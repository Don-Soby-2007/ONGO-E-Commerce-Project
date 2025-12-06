from django.urls import path
from . import views

urlpatterns = [
    path('admin/login/', views.admin_login_view, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),

    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),

    path('otp-verify/', views.OtpVerificationView.as_view(), name='otp_verify'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('user-confirmed/', views.userConfirmedView, name='user_confirmed'),

    path('', views.homeView, name='home'),
    path('logout/', views.userLogoutView, name='logout')

]
