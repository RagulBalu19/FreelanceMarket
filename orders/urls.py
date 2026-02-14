from django.urls import path
from . import views

urlpatterns = [
    path('create/<slug:slug>/', views.create_order, name='create_order'),
    path('my/', views.my_orders, name='my_orders'),
    path('seller/', views.seller_orders, name='seller_orders'),
    path('pay/<uuid:order_id>/', views.pay_order, name='pay_order'),
    path('success/', views.payment_success, name='payment_success'),
    path('start/<uuid:order_id>/', views.start_order, name='start_order'),
    path('deliver/<uuid:order_id>/', views.deliver_order, name='deliver_order'),
    path('complete/<uuid:order_id>/', views.complete_order, name='complete_order'),
    path('review/<uuid:order_id>/', views.add_review, name='add_review'),
    path('chat/<uuid:order_id>/', views.order_chat, name='order_chat'),
    path('dispute/<uuid:order_id>/', views.raise_dispute, name='raise_dispute'),
    path('compare/<uuid:order_id>/', views.compare_submissions, name='compare_submissions'),
    path('resolve/<uuid:order_id>/', views.resolve_dispute, name='resolve_dispute'),
    path('revision/<uuid:order_id>/', views.request_revision, name='request_revision'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('extend/<uuid:order_id>/', views.extend_deadline, name='extend_deadline'),

]
