from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

# Create your models here.


def user_profile_picture_path(instance, filename):
    return f'profile_pictures/user_{instance.pk}/{filename}'


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=user_profile_picture_path, blank=True, null=True)

    is_blocked = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # OTP related fields

    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    otp_attempts = models.IntegerField(default=0)

    def generate_otp(self):
        import random
        otp = f"{random.randint(100000, 999999)}"
        self.otp = otp
        self.otp_created_at = timezone.now()
        self.otp_attempts = 0
        self.save()
        return otp

    def verify_otp(self, otp):

        if not self.otp or not self.otp_created_at:
            return False

        if timezone.now() > self.otp_created_at + timedelta(minutes=5):
            self.clear_otp()
            return False

        if self.otp_attempts >= 5:
            self.clear_otp()
            return False

        if self.otp != otp:
            self.otp_attempts += 1
            self.save()
            return False

        self.clear_otp()
        self.is_verified = True
        self.is_active = True
        self.save(update_fields=['is_verified', 'is_active'])
        return True

    def clear_otp(self):
        self.otp = None
        self.otp_created_at = None
        self.otp_attempts = 0
        self.save(update_fields=['otp', 'otp_created_at', 'otp_attempts'])

    def __str__(self):
        return self.email or self.username
