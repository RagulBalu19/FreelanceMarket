from django.db import models
from django.conf import settings
import uuid


# =========================
# Order Model
# =========================
class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        SUBMITTED = "SUBMITTED", "Submitted"
        REVISION = "REVISION", "Revision Requested"
        COMPLETED = "COMPLETED", "Completed"
        DISPUTED = "DISPUTED", "Disputed"
        OVERDUE = "OVERDUE", "Overdue"
        CANCELLED = "CANCELLED", "cancelled"

    order_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    gig = models.ForeignKey(
        'gigs.Gig',
        on_delete=models.CASCADE,
        related_name='orders'
    )

    amount = models.DecimalField(max_digits=8, decimal_places=2)

    requirements = models.TextField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)

    escrow_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_released = models.BooleanField(default=False)

    payment_id = models.CharField(max_length=200, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    revision_count = models.IntegerField(default=0)
    max_revisions = models.IntegerField(default=3)
    revision_reason = models.TextField(blank=True, null=True)
    
    is_overdue = models.BooleanField(default=False)

    penalty_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    system_note = models.TextField(blank=True, null=True)
    
    cancelled_at = models.DateTimeField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_id} - {self.buyer.username}"


# =========================
# Delivery Model
# =========================
class Delivery(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )

    version = models.IntegerField(default=1)

    file = models.FileField(upload_to='deliveries/')
    message = models.TextField(blank=True)
    change_log = models.TextField(blank=True, null=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Delivery v{self.version} - {self.order.order_id}"


# =========================
# Review Model
# =========================
class Review(models.Model):

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='review'
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_received'
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )

    rating = models.IntegerField(
        choices=[
            (1, "1 Star"),
            (2, "2 Stars"),
            (3, "3 Stars"),
            (4, "4 Stars"),
            (5, "5 Stars"),
        ]
    )

    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.seller.username} by {self.buyer.username}"


# =========================
# Message Model
# =========================
class Message(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    content = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender.username}"


# =========================
# Dispute Model
# =========================
class Dispute(models.Model):

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='dispute'
    )

    raised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    reason = models.TextField()

    is_resolved = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    resolution_note = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Dispute for Order {self.order.order_id}"
