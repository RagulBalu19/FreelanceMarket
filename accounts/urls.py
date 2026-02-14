# from django.urls import path
# from .views import register_view
# from django.contrib.auth import views as auth_views

# urlpatterns = [
#     path('register/', register_view,name='register'),
#     path('login/',auth_views.LoginView.as_view(template_name='accounts/login.html'),name='login'),

#     path('logout/',auth_views.LogoutView.as_view(),name='logout'),
# ]

from django.urls import path
from .views import register_view, logout_view, profile_view, CustomLoginView, dashboard, edit_seller_profile, admin_dashboard, public_leaderboard

urlpatterns = [
    path('register/', register_view, name='register'),
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('seller-profile/edit/', edit_seller_profile, name='edit_seller_profile'),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('leaderboard/', public_leaderboard, name='leaderboard'),


]
