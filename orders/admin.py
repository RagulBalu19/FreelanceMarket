from django.contrib import admin
from .models import Order,  Dispute


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'order_id',
        'gig',
        'buyer',
        # 'total_price',
        'amount',
        'status',
        # 'is_paid',
        'created_at'
    )

    list_filter = (
        'status',
        # 'is_paid'
    )

    search_fields = (
        'order_id',
        'buyer__username',
        'gig__title',
        'amount'
    )

    ordering = ('-created_at',)

@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ('order', 'raised_by', 'is_resolved', 'created_at')
    list_filter = ('is_resolved',)