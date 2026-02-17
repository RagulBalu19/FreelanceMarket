from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
import json

from .forms import RegisterForm
from .models import User, SellerProfile, Notification
from gigs.models import Gig
from orders.models import Order
from orders.views import check_overdue_orders


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
    top_sellers = SellerProfile.objects.select_related('user') \
        .order_by('-total_earnings')

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
    check_overdue_orders()

    if request.user.role == "buyer":
        return redirect('my_orders')

    elif request.user.role == "seller":
        return redirect('seller_orders')

    return redirect('home')


# ---------------- PROFILE ----------------
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


# ---------------- EDIT SELLER PROFILE ----------------
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

    return render(request, "accounts/edit_seller_profile.html", {
        "profile": profile
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
    ).aggregate(total=Sum('amount'))['total'] or 0

    platform_commission = total_revenue * 0.10

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
