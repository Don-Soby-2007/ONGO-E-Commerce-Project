from allauth.socialaccount.signals import social_account_added, social_account_updated
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


def update_user_from_google(extra_data, user):
    """
    Extract Google profile picture and update user model.
    """
    picture_url = extra_data.get("picture")

    # Google gives high-resolution photo with "s96-c", convert to bigger size if needed
    if picture_url:
        picture_url = picture_url.replace("s96-c", "s400-c")

    # Save profile picture URL directly in your custom field
    if picture_url and user.profile_picture != picture_url:
        user.profile_picture = picture_url
        user.save(update_fields=["profile_picture"])


@receiver(social_account_added)
def social_account_added_callback(request, sociallogin, **kwargs):
    extra_data = sociallogin.account.extra_data
    user = sociallogin.user
    update_user_from_google(extra_data, user)


@receiver(social_account_updated)
def social_account_updated_callback(request, sociallogin, **kwargs):
    extra_data = sociallogin.account.extra_data
    user = sociallogin.user
    update_user_from_google(extra_data, user)
