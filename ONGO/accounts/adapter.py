from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_username
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q


User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Pre-process the social login.
        """
        user = sociallogin.user

        if user.id:
            # Existing user, nothing to do
            return

        # Extract data from Google
        data = sociallogin.account.extra_data

        email = data.get('email')
        name = data.get('name', '')

        if email:
            user_email(user, email)

        # Generate a unique username
        if not user.username:
            base_username = email.split('@')[0] if email else f"google_user_{sociallogin.account.uid}"
            counter = 1
            username = base_username
            while User.objects.filter(Q(username=username)).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user_username(user, username)

        # Set name fields
        if name:
            name_parts = name.split(' ', 1)
            if len(name_parts) > 0:
                user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]

        # Mark as verified since authenticated via Google
        user.is_verified = True
        user.is_active = True

    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Return True to allow auto-signup.
        """
        return True

    def get_connect_redirect_url(self, request, socialaccount):
        """
        Return the redirect URL after connecting a social account.
        """
        return getattr(settings, 'LOGIN_REDIRECT_URL', '/')

    def save_user(self, request, sociallogin, form=None):
        """
        Save the social user, creating it if it doesn't exist.
        """
        user = sociallogin.user

        if not user.id:  # If user doesn't exist yet
            data = sociallogin.account.extra_data

            email = data.get('email')
            name = data.get('name', '')

            if email:
                user_email(user, email)

            # Set username
            if not user.username:
                base_username = email.split('@')[0] if email else f"google_user_{sociallogin.account.uid}"
                counter = 1
                username = base_username
                while User.objects.filter(Q(username=username)).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                user_username(user, username)

            # Set name fields
            if name:
                name_parts = name.split(' ', 1)
                if len(name_parts) > 0:
                    user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]

            # Mark as verified
            user.is_verified = True
            user.is_active = True

            # Save the user
            user.save()

        # Create the social account
        sociallogin.save(request)
        return user

    def get_login_redirect_url(self, request):
        """
        Return the redirect URL after successful login.
        """
        return getattr(settings, 'LOGIN_REDIRECT_URL', '/')
