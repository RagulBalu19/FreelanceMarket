from django.contrib import admin
from .models import Gig


@admin.register(Gig)
class GigAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'seller',
        'price',
        'is_active',
        'created_at'
    )

    list_filter = (
        'is_active',
        'created_at'
    )

    search_fields = (
        'title',
        'description'
    )

    prepopulated_fields = {
        'slug': ('title',)
    }

    ordering = ('-created_at',)
