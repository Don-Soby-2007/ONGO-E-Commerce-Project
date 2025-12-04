from django.urls import path
from . import views

urlpatterns = [
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),

    path('', views.user_login_view, name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('otp-verify/', views.OtpVerificationView.as_view(), name='otp_verify'),
    path('user-confirmed/', views.userConfirmedView, name='user_confirmed'),
]
