from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    # Forgot Password
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

    # Authentication URLs
    path('login/', views.LoginView.as_view(), name='login'),
    path('signup/', views.SignupView.as_view(), name='signup'),

    # Otp verification

    path('otp-verify/', views.OtpVerificationView.as_view(), name='otp_verify'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('user-confirmed/', views.userConfirmedView, name='user_confirmed'),

    # Logut
    path('logout/', views.userLogoutView, name='logout'),

    # ---------Profile Section----------

    path('profile/', views.ProfileView, name='profile'),
    path('profile/edit', views.EditProfileView.as_view(), name='edit_profile'),
    path('profile/update-photo/', views.UpdateProfilePhotoView.as_view(), name='update_profile_photo'),

    # Email Change OTP Verification
    path('profile/email-change-verify/', views.EmailChangeOtpVerificationView.as_view(),
         name='email_change_otp_verify'),
    path('profile/cancel-email-change/', views.cancel_email_change, name='cancel_email_change'),
    path('profile/resend-email-otp/', views.resend_email_change_otp, name='resend_email_change_otp'),

    path('manage-address/', views.AddressView.as_view(), name='manage_address'),
    path('manage-address/create', views.AddAddressView.as_view(), name='add_address'),
    path('manage-address/edit/<int:address_id>/', views.EditAddressView.as_view(), name="edit_address"),
    path('manage-address/delete/<int:pk>/', views.DeleteAddressView, name='delete_address'),

    path('manage-password/', views.PasswordView.as_view(), name='manage_password')
]
