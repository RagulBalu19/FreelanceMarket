# from django import forms
# from .models import Gig

# class GigForm(forms.ModelForm):
#     class Meta:
#         model = Gig
#         fields = ['title', 'description', 'price', 'image']

from django import forms
from .models import Gig


class GigForm(forms.ModelForm):

    class Meta:
        model = Gig

        # NEVER expose seller field
        exclude = ['seller', 'slug', 'is_active', 'created_at', 'updated_at']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')

        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0")

        return price
