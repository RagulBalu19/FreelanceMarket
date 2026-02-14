from datetime import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from gigs.models import Gig
from orders.models import Order
from django.urls import reverse_lazy
from accounts.models import SellerProfile
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from orders.models import Order
from .models import User, SellerProfile
from django.db.models.functions import TruncMonth
import json
from accounts.models import Notification
from django.utils import timezone
from datetime import timedelta
from .models import Notification
from orders.views import check_overdue_orders

# check_overdue_orders()

# ---------------- REGISTER ----------------
def register_view(request):
    if request.method == 'POST':        
        form = RegisterForm(request.POST, request.FILES)
    
        if form.is_valid():
            user = form.save()
            login(request, user)
    
            # ALWAYS go to dashboard
            return redirect('dashboard')
        else:
            print(form.errors)
    else:
        form = RegisterForm()
        
    return render(request, 'accounts/register.html', {'form': form})


# ---------------- LOGIN ----------------
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    # ALWAYS go to dashboard
    def get_success_url(self):
        return reverse_lazy('dashboard')


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect('login')

def public_leaderboard(request):

    top_sellers = SellerProfile.objects.select_related('user') \
        .order_by('-total_earnings')

    return render(request, "accounts/leaderboard.html", {
        "top_sellers": top_sellers
    })

def create_notification(user, message, order=None):
    Notification.objects.create(
        user=user,
        message=message,
        order=order
    )

# ---------------- DASHBOARD (role logic here) ----------------

@login_required
def dashboard(request):
    check_overdue_orders()

    if request.user.role == "seller":
        gigs = Gig.objects.filter(seller=request.user)
        completed_orders = Order.objects.filter(
            gig__seller=request.user,
            status=Order.Status.COMPLETED
        ).count()

        return render(request, 'accounts/seller_dashboard.html', {
            'gigs': gigs,
            'completed_orders': completed_orders
        })

    return render(request, 'accounts/buyer_dashboard.html')

@login_required
def profile_view(request):

    user = request.user

    if request.method == "POST":
        user.bio = request.POST.get("bio")

        if request.FILES.get("profile_pic"):
            user.profile_pic = request.FILES.get("profile_pic")

        user.save()
        return redirect('profile')

    return render(request, 'accounts/profile.html')

@login_required
def edit_seller_profile(request):

    if request.user.role != "seller":
        return redirect('home')

    profile = request.user.seller_profile

    if request.method == "POST":
        profile.skills = request.POST.get("skills")
        profile.experience = request.POST.get("experience")
        profile.portfolio_link = request.POST.get("portfolio_link")
        profile.save()
        return redirect('dashboard')

    return render(request, "accounts/edit_seller_profile.html", {"profile": profile})

@login_required
def complete_order(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    # Only buyer can complete
    if request.user != order.buyer:
        return redirect('home')

    # Prevent double earning
    if order.status == Order.Status.COMPLETED:
        return redirect('my_orders')

    order.status = Order.Status.COMPLETED
    order.completed_at = timezone.now()
    order.save()

    # 🔥 AUTO EARNINGS CALCULATION
    seller_profile = order.gig.seller.seller_profile
    seller_profile.total_earnings += order.amount
    seller_profile.save()

    return redirect('my_orders')

@staff_member_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_sellers = User.objects.filter(role='seller').count()
    total_buyers = User.objects.filter(role='buyer').count()

    total_gigs = Gig.objects.count()
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status=Order.Status.COMPLETED).count()

    total_revenue = Order.objects.filter(
        status=Order.Status.COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Optional: Platform commission (example 10%)
    platform_commission = total_revenue * 0.10
    
    today = timezone.now()

    # First day of current month
    current_month_start = today.replace(day=1)
    
    # First day of previous month
    previous_month_end = current_month_start - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)
    
    # Current month revenue
    current_month_revenue = Order.objects.filter(
        status=Order.Status.COMPLETED,
        completed_at__gte=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Previous month revenue
    previous_month_revenue = Order.objects.filter(
        status=Order.Status.COMPLETED,
        completed_at__gte=previous_month_start,
        completed_at__lt=current_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Growth percentage
    if previous_month_revenue > 0:
        growth_percentage = (
            (current_month_revenue - previous_month_revenue)
            / previous_month_revenue
        ) * 100
    else:
        growth_percentage = 100 if current_month_revenue > 0 else 0
    
    top_sellers = SellerProfile.objects.select_related('user') \
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
    
    # Monthly revenue data
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


    return render(request, "accounts/admin_dashboard.html", context)

