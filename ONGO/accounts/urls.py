from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html'
        ),
        name='password_reset'
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),

    path('otp-verify/', views.OtpVerificationView.as_view(), name='otp_verify'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('user-confirmed/', views.userConfirmedView, name='user_confirmed'),

    path('logout/', views.userLogoutView, name='logout'),

]
