from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.core.mail import send_mail

from django.db import DatabaseError

from .models import User

import re
import logging


# Create your views here.

logger = logging.getLogger(__name__)


def admin_login_view(request):
    return render(request, 'accounts/admin-login.html')


def admin_dashboard_view(request):
    return render(request, 'accounts/admin-dashboard.html')


def user_login_view(request):
    return render(request, 'accounts/user-login.html')


class SignupView(View):
    template_name = 'accounts/user-signup.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):

        username = request.POST.get('username').strip()
        email = request.POST.get('email').strip().lower()
        phone = request.POST.get('phone').strip()
        password = request.POST.get('password').strip()
        confirm_password = request.POST.get('confirm_password').strip()

        if re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password) is False:
            messages.error(request, "Password must be at least 8 characters long "
                           "and include uppercase,lowercase, number, and special character.")
            return render(request, self.template_name)

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, self.template_name)

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, self.template_name)

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken.")
            return render(request, self.template_name)

        user = User.objects.create_user(
            username=username,
            email=email,
            phone_number=phone,
        )
        user.set_password(password)
        user.is_verified = False
        user.is_active = False
        user.save()

        otp = user.generate_otp()
        logger.info(f"OTP for user {user.email}: {otp}")

        send_mail(
            'Your OTP Verification Code',
            f'Your OTP code is: {otp}. It is valid for 5 minutes.',
            None,
            [user.email],
            fail_silently=False,
        )

        request.session['pending_user_id'] = user.id
        return redirect("otp_verify")


class OtpVerificationView(View):
    template_name = 'accounts/otp-verification.html'

    def get(self, request):
        if not request.session.get('pending_user_id'):
            return redirect("signup")
        return render(request, self.template_name)

    def post(self, request):
        user_id = request.session.get('pending_user_id')
        otp_input = request.POST.get('otp')

        if not user_id:
            messages.error(request, "No pending OTP verification found.")
            return redirect("signup")

        if not otp_input or not otp_input.isdigit() or len(otp_input) != 6:
            messages.error(request, "Please enter a valid 6-digit OTP.")
            return render(request, self.template_name)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            logger.warning(f"OTP verification attempted for non-existent user ID: {user_id}")
            messages.error(request, "User not found. Please sign up again.")
            return redirect("signup")

        except DatabaseError as e:
            logger.error(f"Database error during OTP verification for user {user_id}: {e}")
            messages.error(request, "A database error occurred. Please try again later.")
            return render(request, self.template_name)

        if user.verify_otp(otp_input):
            request.session.pop('pending_user_id', None)
            messages.success(request, "OTP verified successfully. Your account is now active.")
            return redirect("login")
        else:
            messages.error(request, "Invalid or expired OTP. Please try again.")
            return render(request, self.template_name)
