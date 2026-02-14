# from django.urls import path
# from . import views

# urlpatterns = [
#     path('', views.gig_list, name='gig_list'),
#     path('', views.home, name='home'),
#     # path('gig/<int:pk>/', views.gig_detail, name='gig_detail'),
#     path('create/', views.create_gig, name='create_gig'),
# ]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('gigs/', views.gig_list, name='gig_list'),

    path('gigs/create/', views.create_gig, name='create_gig'),

    path('gigs/<slug:slug>/', views.gig_detail, name='gig_detail'),
]
