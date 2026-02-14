from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from orders.models import Order

# from accounts.models import SellerProfile
class User(AbstractUser):

    class Roles(models.TextChoices):
        BUYER = "buyer", "Buyer"
        SELLER = "seller", "Seller"

    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.BUYER,
        db_index=True
    )

    bio = models.TextField(null=True)  # null not needed for TextField
    
    profile_pic = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.role})"

class SellerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seller_profile'
    )

    skills = models.CharField(max_length=300, blank=True)
    experience = models.IntegerField(blank=True, null=True)
    portfolio_link = models.URLField(blank=True)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rating = models.FloatField(default=0)

    def __str__(self):
        return f"{self.user.username} Profile"
    
class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    message = models.TextField()
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.message}"

    
@receiver(post_save, sender=User)
def create_seller_profile(sender, instance, created, **kwargs):
    if created and instance.role == "seller":
        SellerProfile.objects.create(user=instance)
