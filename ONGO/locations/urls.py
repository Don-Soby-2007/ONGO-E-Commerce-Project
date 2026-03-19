from django.urls import path
from . import views

urlpatterns = [
    path('pincode-stats/<str:pincode>/', views.pincode_stats, name='pincode_stats'),
]
