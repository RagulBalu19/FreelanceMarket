from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg
import razorpay
from django.contrib.admin.views.decorators import staff_member_required


from .models import Order, Delivery, Review, Message, Dispute
from gigs.models import Gig
from accounts.models import Notification


# ========================
# Helper: Create Notification
# ========================
def create_notification(user, message, order=None):
    Notification.objects.create(
        user=user,
        message=message,
        order=order
    )



# ========================
# deadline
# ========================
def check_overdue_orders():

    today = timezone.now().date()

    overdue_orders = Order.objects.filter(
        status__in=[
            Order.Status.PAID,
            Order.Status.IN_PROGRESS,
            Order.Status.REVISION,
            Order.Status.SUBMITTED
        ],
        deadline__lt=today,
        is_overdue=False
    )

    for order in overdue_orders:

        order.status = Order.Status.OVERDUE
        order.is_overdue = True

        # 🔥 Optional penalty (5%)
        penalty = order.amount * 0.05
        order.penalty_amount = penalty

        order.system_note = "Deadline crossed. Order marked overdue automatically."
        order.save()

        # 🔔 Notify buyer
        create_notification(
            order.buyer,
            f"Order overdue: {order.gig.title}"
        )

        # 🔔 Notify seller
        create_notification(
            order.gig.seller,
            f"You missed deadline for {order.gig.title}"
        )

# ========================
# Create Order
# ========================
@login_required
def create_order(request, slug):

    if request.user.role != "buyer":
        return redirect("home")

    gig = get_object_or_404(Gig, slug=slug)

    if request.method == "POST":
        requirements = request.POST.get("requirements")
        deadline = request.POST.get("deadline")

        order = Order.objects.create(
            buyer=request.user,
            gig=gig,
            amount=gig.price,
            requirements=requirements,
            deadline=deadline
        )

        create_notification(
            gig.seller,
            f"You received a new order for '{gig.title}'",
            order
        )

        return redirect("pay_order", order_id=order.order_id)

    return render(request, "orders/create_order.html", {"gig": gig})


# ========================
# My Orders
# ========================
@login_required
def my_orders(request):
    orders = Order.objects.filter(buyer=request.user)
    return render(request, "orders/my_orders.html", {"orders": orders})


# ========================
# Seller Orders
# ========================
@login_required
def seller_orders(request):
    orders = Order.objects.filter(gig__seller=request.user)
    return render(request, "orders/seller_orders.html", {"orders": orders})


# ========================
# Razorpay Payment
# ========================
@login_required
def pay_order(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    payment = client.order.create({
        "amount": int(order.amount * 100),
        "currency": "INR",
        "payment_capture": 1
    })

    context = {
        "payment": payment,
        "order": order,
        "key": settings.RAZORPAY_KEY_ID
    }

    return render(request, "orders/payment.html", context)


# ========================
# Payment Success
# ========================
@login_required
def payment_success(request):

    order_id = request.GET.get("order_id")
    payment_id = request.GET.get("payment_id")

    order = get_object_or_404(Order, order_id=order_id)
    
    # order.escrow_amount = order.amount
    order.payment_id = payment_id
    order.status = Order.Status.PAID
    order.save()

    return redirect("my_orders")


# ========================
# Start Order
# ========================
@login_required
def start_order(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.user != order.gig.seller:
        return redirect("home")

    order.status = Order.Status.IN_PROGRESS
    order.started_at = timezone.now()
    order.save()

    return redirect("seller_orders")


# ========================
# Deliver Work
# ========================
@login_required
def deliver_order(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.user != order.gig.seller:
        return redirect("home")

    if request.method == "POST":

        file = request.FILES.get("file")
        message = request.POST.get("message")

        last_delivery = order.deliveries.order_by("-version").first()
        next_version = last_delivery.version + 1 if last_delivery else 1

        Delivery.objects.create(
            order=order,
            version=next_version,
            file=file,
            message=message
        )

        order.status = Order.Status.SUBMITTED
        order.save()

        create_notification(
            order.buyer,
            f"New delivery submitted for {order.gig.title}",
            order
        )

        return redirect("seller_orders")

    return render(request, "orders/deliver.html", {"order": order})


# ========================
# Complete Order
# ========================
@login_required
def complete_order(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.user != order.buyer:
        return redirect("home")

    if order.status != Order.Status.SUBMITTED:
        return redirect("my_orders")

    order.status = Order.Status.COMPLETED
    order.completed_at = timezone.now()

    if not order.is_released:
        seller_profile = order.gig.seller.seller_profile
        seller_profile.total_earnings += order.escrow_amount
        seller_profile.save()

        order.is_released = True
        order.escrow_amount = 0

    order.save()

    return redirect("my_orders")

# ========================
# Add Review
# ========================
@login_required
def add_review(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.user != order.buyer:
        return redirect("home")

    if order.status != Order.Status.COMPLETED:
        return redirect("my_orders")

    if hasattr(order, "review"):
        return redirect("my_orders")

    if request.method == "POST":

        rating = int(request.POST.get("rating"))
        comment = request.POST.get("comment")

        Review.objects.create(
            order=order,
            seller=order.gig.seller,
            buyer=request.user,
            rating=rating,
            comment=comment
        )

        avg_rating = Review.objects.filter(
            seller=order.gig.seller
        ).aggregate(Avg("rating"))["rating__avg"]

        seller_profile = order.gig.seller.seller_profile
        seller_profile.rating = round(avg_rating, 1)
        seller_profile.save()

        return redirect("my_orders")

    return render(request, "orders/add_review.html", {"order": order})


# ========================
# Notifications View
# ========================
@login_required
def notifications_view(request):

    notifications = Notification.objects.filter(user=request.user)
    unread_count = notifications.filter(is_read=False).count()

    return render(request, "accounts/notifications.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })


# ========================
# Chat
# ========================
@login_required
def order_chat(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.user != order.buyer and request.user != order.gig.seller:
        return redirect("home")

    if request.method == "POST":
        content = request.POST.get("content")

        if content:
            Message.objects.create(
                order=order,
                sender=request.user,
                content=content
            )

    messages = order.messages.all().order_by("timestamp")

    return render(request, "orders/chat.html", {
        "order": order,
        "messages": messages
    })


# ========================
# Request Revision
# ========================
@login_required
def request_revision(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.user != order.buyer:
        return redirect("home")

    if order.status != Order.Status.SUBMITTED:
        return redirect("my_orders")

    if order.revision_count >= order.max_revisions:
        return redirect("my_orders")

    if request.method == "POST":
        reason = request.POST.get("reason")

        order.status = Order.Status.REVISION
        order.revision_reason = reason
        order.revision_count += 1
        order.save()

        create_notification(
            order.gig.seller,
            f"Revision requested for {order.gig.title}",
            order
        )

        return redirect("my_orders")

    return render(request, "orders/request_revision.html", {"order": order})


@login_required
def raise_dispute(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.user != order.buyer:
        return redirect('home')

    if order.status != Order.Status.SUBMITTED:
        return redirect('my_orders')

    if hasattr(order, 'dispute'):
        return redirect('my_orders')

    if request.method == "POST":
        reason = request.POST.get("reason")

        Dispute.objects.create(
            order=order,
            raised_by=request.user,
            reason=reason
        )

        order.status = Order.Status.DISPUTED
        order.save()

        return redirect('my_orders')

    return render(request, "orders/raise_dispute.html", {"order": order})


@login_required
def compare_submissions(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    # Only buyer or seller allowed
    if request.user != order.buyer and request.user != order.gig.seller:
        return redirect('home')

    deliveries = order.deliveries.order_by('-version')

    return render(request, "orders/compare.html", {
        "order": order,
        "deliveries": deliveries
    })


@staff_member_required
def resolve_dispute(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)
    dispute = order.dispute

    if request.method == "POST":

        action = request.POST.get("action")

        if action == "refund":
            order.escrow_amount = 0
            order.is_released = False
            order.status = Order.Status.COMPLETED

        elif action == "release":

            seller_profile = order.gig.seller.seller_profile
            seller_profile.total_earnings += order.escrow_amount
            seller_profile.save()

            order.is_released = True
            order.escrow_amount = 0
            order.status = Order.Status.COMPLETED

        dispute.is_resolved = True
        dispute.resolution_note = request.POST.get("note")
        dispute.resolved_at = timezone.now()

        dispute.save()
        order.save()

        return redirect("admin_dashboard")

    return render(request, "orders/resolve_dispute.html", {
        "order": order,
        "dispute": dispute
    })

@login_required
def deliver_order(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.user != order.gig.seller:
        return redirect("home")

    if request.method == "POST":

        file = request.FILES.get("file")
        message = request.POST.get("message")

        if not file:
            return redirect("seller_orders")

        last_delivery = order.deliveries.order_by("-version").first()
        next_version = last_delivery.version + 1 if last_delivery else 1

        Delivery.objects.create(
            order=order,
            version=next_version,
            file=file,
            message=message
        )

        order.status = Order.Status.SUBMITTED
        order.save()

        return redirect("seller_orders")

    return render(request, "orders/deliver.html", {"order": order})


@login_required
def extend_deadline(request, order_id):

    order = get_object_or_404(Order, order_id=order_id)

    if request.user != order.buyer:
        return redirect("home")

    if request.method == "POST":

        new_deadline = request.POST.get("new_deadline")

        order.deadline = new_deadline
        order.status = Order.Status.IN_PROGRESS
        order.is_overdue = False
        order.penalty_amount = 0
        order.save()

        create_notification(
            order.gig.seller,
            f"Deadline extended for {order.gig.title}"
        )

        return redirect("my_orders")

    return render(request, "orders/extend_deadline.html", {"order": order})
