from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
import json
from .models import SellerProfile
from django.db.models.functions import TruncMonth

from .forms import RegisterForm
from .models import User, SellerProfile, Notification, CodingProblem, TestCase, FreelancerSkill, Submission, Skill
from gigs.models import Gig
from orders.models import Order, Review
from orders.views import check_overdue_orders
import sys, io, random
from decimal import Decimal

# ---------------- REGISTER ----------------
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


# ---------------- LOGIN ----------------
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        return reverse_lazy('dashboard')


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect('login')


# ---------------- PUBLIC LEADERBOARD ----------------
def public_leaderboard(request):

    top_sellers = SellerProfile.objects.filter(
        user__role="seller"
    ).select_related("user").annotate(

        total_earnings_calc=Sum(
            "user__gigs__orders__amount",
            filter=Q(user__gigs__orders__status=Order.Status.COMPLETED)
        ),

        completed_orders_count=Count(
            "user__gigs__orders",
            filter=Q(user__gigs__orders__status=Order.Status.COMPLETED)
        )

    ).order_by(
        "-total_earnings_calc",
        "-rating",
        "-completed_orders_count"
    )

    return render(request, "accounts/leaderboard.html", {
        "top_sellers": top_sellers
    })
# ---------------- CREATE NOTIFICATION ----------------
def create_notification(user, message, order=None):
    Notification.objects.create(
        user=user,
        message=message,
        order=order
    )


# ---------------- DASHBOARD (ROLE BASED REDIRECT) ----------------
@login_required
def dashboard(request):

    user = request.user

    # Check overdue orders
    check_overdue_orders()

    # ================= SELLER DASHBOARD =================
    if user.role == "seller":

        seller_orders = Order.objects.filter(
            gig__seller=user
        )

        total_orders = seller_orders.count()

        completed_orders = seller_orders.filter(
            status=Order.Status.COMPLETED
        ).count()

        active_orders = seller_orders.exclude(
            status=Order.Status.COMPLETED
        ).count()

        total_earnings = seller_orders.filter(
            status=Order.Status.COMPLETED
        ).aggregate(
            total=Sum("amount")
        )["total"] or 0


        # Chart data
        earnings_data = seller_orders.filter(
            status=Order.Status.COMPLETED
        ).annotate(
            month=TruncMonth("completed_at")
        ).values("month").annotate(
            total=Sum("amount")
        ).order_by("month")


        months = []
        earnings = []

        for item in earnings_data:
            if item["month"]:
                months.append(item["month"].strftime("%b %Y"))
                earnings.append(float(item["total"]))


        context = {

            "orders": seller_orders,

            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "active_orders": active_orders,
            "total_earnings": total_earnings,

            "months": json.dumps(months),
            "earnings": json.dumps(earnings),

        }

        return render(
            request,
            "accounts/dashboard.html",
            context
        )


    # ================= BUYER DASHBOARD =================
    else:

        buyer_orders = Order.objects.filter(
            buyer=user
        )

        total_orders = buyer_orders.count()

        completed_orders = buyer_orders.filter(
            status=Order.Status.COMPLETED
        ).count()

        active_orders = buyer_orders.exclude(
            status=Order.Status.COMPLETED
        ).count()


        context = {

            "orders": buyer_orders,

            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "active_orders": active_orders,

        }

        return render(
            request,
            "accounts/dashboard.html",
            context
        )

# ---------------- PROFILE ----------------
@login_required
def profile_view(request):
    user = request.user
    
    if user.role == "buyer":

        total_orders = Order.objects.filter(buyer=user).count()

        completed_orders = Order.objects.filter(
            buyer=user,
            status=Order.Status.COMPLETED
        ).count()

        active_orders = Order.objects.filter(
            buyer=user,
            status__in=[
                Order.Status.PAID,
                Order.Status.IN_PROGRESS,
                Order.Status.SUBMITTED,
                Order.Status.REVISION
            ]
        ).count()

        total_spent = Order.objects.filter(
            buyer=user,
            status=Order.Status.COMPLETED
        ).aggregate(total=Sum("amount"))["total"] or 0

        reviews_given = Review.objects.filter(
            buyer=user
        ).count()

        context = {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "active_orders": active_orders,
            "total_spent": total_spent,
            "reviews_given": reviews_given,
        }

        return render(request, "accounts/profile.html", context)
    # Safe SellerProfile access
    seller_profile = getattr(user, "profile", None)

    # Completed Orders
    # completed_orders = user.orders.filter(status="COMPLETED").count()
    
    completed_orders = Order.objects.filter(gig__seller=user,status=Order.Status.COMPLETED).count()
    

    total_earnings = Order.objects.filter(
        gig__seller=request.user,
        status=Order.Status.COMPLETED
    ).aggregate(total=Sum("amount"))["total"] or 0

    # Profile Completion Logic
    fields_filled = 0
    total_fields = 4

    if user.profile_pic:
        fields_filled += 1

    if user.bio:
        fields_filled += 1

    # if seller_profile and seller_profile.skills:
    #     skills_list = [skill.strip() for skill in seller_profile.skills.split(",")]


    if hasattr(user,"location") and user.location:
        fields_filled += 1

    completion_percentage = int((fields_filled / total_fields) * 100)
    
    verified_skills = FreelancerSkill.objects.filter(user=user,is_verified=True).values_list("skill", flat=True)
    # Level Logic
    if total_earnings > 5000:
        level = "Gold"
    elif total_earnings > 1000:
        level = "Silver"
    else:
        level = "Bronze"
    # Get skills properly (ManyToMany)
    if seller_profile:
        skills_list = seller_profile.skills.all()
    else:
        skills_list = []
    context = {
        "seller": seller_profile,
        "completed_orders": completed_orders,
        "total_earnings": total_earnings,
        "completion_percentage": completion_percentage,
        "level": level,
        "skills_list":skills_list,
        "verified_skills": verified_skills
    }

    return render(request, "accounts/profile.html", context)
# ---------------- EDIT SELLER PROFILE ----------------
@login_required
def edit_seller_profile(request):

    if request.user.role != "seller":
        return redirect('home')
    
    profile = request.user.seller_profile
    all_skills = Skill.objects.all()
    
    if request.method == "POST":
        profile.skills.set(request.POST.getlist("skills"))
        experience = request.POST.get("experience")
        profile.experience = request.POST.get("experience")
        profile.portfolio_link = request.POST.get("portfolio_link")
        profile.save()
        return redirect('profile')

    return render(request, "accounts/edit_seller_profile.html", {
        "profile": profile,"all_skills": all_skills
    })


# ---------------- ADMIN DASHBOARD ----------------
@staff_member_required
def admin_dashboard(request):

    total_users = User.objects.count()
    total_sellers = User.objects.filter(role='seller').count()
    total_buyers = User.objects.filter(role='buyer').count()

    total_gigs = Gig.objects.count()
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(
        status=Order.Status.COMPLETED
    ).count()

    total_revenue = Order.objects.filter(
        status=Order.Status.COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or Decimal("0")

    platform_commission = total_revenue * Decimal(0.10)

    # ---------------- Monthly Revenue ----------------
    monthly_data = (
        Order.objects.filter(status=Order.Status.COMPLETED)
        .annotate(month=TruncMonth('completed_at'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    months = []
    revenues = []

    for entry in monthly_data:
        months.append(entry['month'].strftime("%b %Y"))
        revenues.append(float(entry['total']))

    # ---------------- Growth Calculation ----------------
    today = timezone.now()

    current_month_start = today.replace(day=1)

    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)

    current_month_revenue = Order.objects.filter(
        status=Order.Status.COMPLETED,
        completed_at__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0

    previous_month_revenue = Order.objects.filter(
        status=Order.Status.COMPLETED,
        completed_at__gte=previous_month_start,
        completed_at__lt=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0

    if previous_month_revenue > 0:
        growth_percentage = (
            (current_month_revenue - previous_month_revenue)
            / previous_month_revenue
        ) * 100
    else:
        growth_percentage = 100 if current_month_revenue > 0 else 0

    # ---------------- Top Sellers ----------------
    top_sellers = SellerProfile.objects.select_related('user') \
        .filter(user__role="seller")\
        .order_by('-total_earnings')[:5]

    context = {
        'total_users': total_users,
        'total_sellers': total_sellers,
        'total_buyers': total_buyers,
        'total_gigs': total_gigs,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'platform_commission': platform_commission,
        'months': json.dumps(months),
        'revenues': json.dumps(revenues),
        'current_month_revenue': current_month_revenue,
        'previous_month_revenue': previous_month_revenue,
        'growth_percentage': round(growth_percentage, 1),
        'top_sellers': top_sellers,
    }

    return render(request, "accounts/admin_dashboard.html", context)

# =========================
# FRONTEND VALIDATORS
# =========================

def validate_html(code):
    required_tags = ["<table>", "<tr>", "<td>", "</table>", "</tr>", "</td>"]
    matched = sum(1 for tag in required_tags if tag in code)
    return (matched / len(required_tags)) * 100


def validate_css(code):
    required_patterns = ["{", "}", "color", "font", "margin"]
    matched = sum(1 for item in required_patterns if item in code)
    return (matched / len(required_patterns)) * 100


def validate_js(code):
    required_patterns = ["function", "console.log", "var", "let", "const"]
    matched = sum(1 for item in required_patterns if item in code)
    return (matched / len(required_patterns)) * 100

# ---------------verification badge---------------
def submit_code(request, problem_id):
    problem = get_object_or_404(CodingProblem, id=problem_id)

    
    skill_name = problem.skill.name.lower()

    if skill_name in ["html", "css", "js"]:

        if request.method == "POST":
            code = request.POST.get("code", "").lower()

            if skill_name == "html":
                percentage = validate_html(code)

            elif skill_name == "css":
                percentage = validate_css(code)

            elif skill_name == "js":
                percentage = validate_js(code)

            passed = percentage >= problem.min_score

            Submission.objects.create(
                user=request.user,
                problem=problem,
                code=code,
                score=percentage,
                passed=passed
            )

            # Auto verify
            if passed:
                fs, created = FreelancerSkill.objects.get_or_create(
                    user=request.user,
                    skill=problem.skill
                )
                fs.is_verified = True
                fs.save()

            return render(request, "result.html", {
                "score": percentage,
                "passed": passed,
                "results": []
            })

        return render(request, "problem_detail.html", {"problem": problem})
    
    # 🔒 Attempt Limit Check
    attempts = Submission.objects.filter(
        user=request.user,
        problem=problem
    ).count()

    if attempts >= problem.max_attempts:
        return render(request, "accounts/attempt_limit.html")

    if request.method == "POST":
        code = request.POST.get("code")
        test_cases = TestCase.objects.filter(problem=problem)

        passed_count = 0
        total = test_cases.count()

        results = []

        for test in test_cases:
            old_stdout = sys.stdout
            old_stdin = sys.stdin
            
            sys.stdout = io.StringIO()
            sys.stdin = io.StringIO(test.input_data)

            try:
                exec(code)
                output = sys.stdout.getvalue().strip()
            except Exception:
                output = "Error"

            sys.stdout = old_stdout
            sys.stdin = old_stdin

            is_passed = output == test.expected_output.strip()

            if is_passed:
                passed_count += 1

            # Only show non-hidden test cases
            if not test.is_hidden:
                results.append({
                    "input": test.input_data,
                    "expected": test.expected_output,
                    "output": output,
                    "passed": is_passed
                })

        percentage = (passed_count / total) * 100
        passed = percentage >= problem.min_score

        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            code=code,
            score=percentage,
            passed=passed
        )

        # 🎯 AUTO VERIFY LOGIC
        if passed:
            fs, created = FreelancerSkill.objects.get_or_create(
                user=request.user,
                skill=problem.skill
            )
            fs.is_verified = True
            fs.save()

        return render(request, "result.html", {
            "score": percentage,
            "passed": passed,
            "results": results
        })

    return render(request, "problem_detail.html", {"problem": problem})

@login_required
def my_skill_tests(request):
    seller_profile = getattr(request.user, "seller_profile", None)

    if not seller_profile:
        return redirect("dashboard")

    skills = seller_profile.skills.all()

    # 🔹 Get already verified skills
    verified_skills = FreelancerSkill.objects.filter(
        user=request.user,
        is_verified=True
    ).values_list("skill", flat=True)

    # 🔹 Show only problems for unverified skills
    problems = CodingProblem.objects.filter(
        skill__in=skills
    ).exclude(
        skill__in=verified_skills
    )

    return render(request, "accounts/my_skill_tests.html", {
        "problems": problems
    })
    
@login_required
def start_test(request, skill_id):

    problems = CodingProblem.objects.filter(skill_id=skill_id)

    problem = random.choice(problems)

    return redirect("coding_test", problem.id)

def generate_problem_view(request):

    data = generate_problem()

    problem = CodingProblem.objects.create(
        skill_id=1,  # example Python skill
        title=data["title"],
        description=data["description"],
        sample_input=data["sample_input"],
        sample_output=data["sample_output"]
    )

    for tc in data["testcases"]:
        TestCase.objects.create(
            problem=problem,
            input_data=tc["input"],
            expected_output=tc["output"]
        )

    return redirect("admin_dashboard")