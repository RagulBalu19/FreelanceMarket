from django import forms
from .models import Order


class OrderForm(forms.ModelForm):

    class Meta:
        model = Order

        # hide sensitive fields
        exclude = [
            'order_id',
            'buyer',
            'total_price',
            'status',
            'payment_id',
            'is_paid',
            'created_at',
            'updated_at'
        ]
