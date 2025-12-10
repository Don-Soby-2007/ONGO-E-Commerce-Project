from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
from .models import User


class SocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        # Optional: block users before login
        email = sociallogin.account.extra_data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                if user.is_blocked:
                    messages.error(request, "Your account has been blocked.")
                    raise ImmediateHttpResponse(redirect('/'))
            except User.DoesNotExist:
                pass

    def save_user(self, request, sociallogin, form=None):
        # Bypass form — create user directly from Google data
        user = sociallogin.user
        extra_data = sociallogin.account.extra_data

        # Populate fields from Google profile
        user.email = extra_data.get('email', '').lower()
        user.username = extra_data.get('name', '') or extra_data.get('given_name', '') + ' ' + extra_data.get('family_name', '')[:1]
        user.is_verified = True  # Google emails are verified
        user.is_active = True

        # Handle picture: save Cloudinary public_id later (or upload on first login)
        # We'll do that in a signal or override here if needed

        user.save()
        sociallogin.save(request)
        return user
