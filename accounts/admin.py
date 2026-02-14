from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import SellerProfile

@admin.register(User)
class CustomUserAdmin(UserAdmin):

    model = User

    list_display = (
        'username',
        'email',
        'role',
        'is_staff',
        'created_at'
    )

    list_filter = (
        'role',
        'is_staff',
        'is_superuser'
    )

    search_fields = (
        'username',
        'email'
    )

    ordering = ('-created_at',)

    fieldsets = UserAdmin.fieldsets + (
        ("Extra Info", {
            'fields': ('role', 'bio', 'profile_pic')
        }),
    )

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'skills', 'experience', 'rating', 'total_earnings')