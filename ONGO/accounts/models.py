from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import cloudinary.uploader
import cloudinary.utils
import uuid

# Create your models here.


class User(AbstractUser):

    """Custom User model with email login, OTP verification, and Cloudinary profile pictures."""

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    profile_picture = models.CharField(max_length=500, blank=True, null=True,  help_text="Cloudinary public_id")

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

    def upload_profile_picture(self, image_file):
        """
        Upload image to Cloudinary and save public_id
        :param image_file: File object (e.g., from request.FILES['profile_picture'])
        """
        if not image_file:
            return False

        if self.profile_picture:
            try:
                cloudinary.uploader.destroy(self.profile_picture)
            except Exception as e:
                print(f"Failed to delete old image {self.profile_picture}: {e}")

        if not image_file.content_type.startswith('image/'):
            raise ValueError("Only image files are allowed.")

        if image_file.size > 10 * 1024 * 1024:
            raise ValueError("Image too large. Max 10MB.")

        try:
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder="profile_pics",           # organizes in Media Library
                public_id=f"user_{self.id}_{uuid.uuid4().hex[:8]}",
                overwrite=True,
                resource_type="image",
                # Optional: transformations on upload
                # width=500, height=500, crop="limit", quality="auto:good"
            )

            # Save the public_id (e.g., "profile_pics/user_1_1734567890")
            self.profile_picture = upload_result['public_id']
            self.save(update_fields=['profile_picture'])
            return True

        except Exception as e:
            print(f"Cloudinary upload failed: {e}")
            return False

    def get_profile_picture_url(self, width=200, height=200):
        """
        Returns optimized, resized profile picture URL
        """
        if not self.profile_picture:
            # Return default avatar (optional)
            name = self.username.replace(' ', '+')
            return f"https://ui-avatars.com/api/?name={name}&background=FF9999&color=fff"

        # Build optimized Cloudinary URL
        return cloudinary.utils.cloudinary_url(
            self.profile_picture,
            transformation=[
                {'width': width, 'height': height, 'crop': 'thumb', 'gravity': 'face'},
                {'quality': 'auto', 'fetch_format': 'auto'},
            ]
        )[0]  # [0] = URL, [1] = options

    def __str__(self):
        return self.email or self.username


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')

    name = models.CharField(max_length=150)
    street_address = models.CharField("Street Address", max_length=500)

    city = models.CharField(max_length=150)
    state = models.CharField(max_length=150)
    country = models.CharField(max_length=150)
    postel_code = models.CharField(max_length=20)

    phone = models.PositiveIntegerField(blank=False)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_default']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(is_default=True),
                name='one_default_address_per_user'
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.city}, {self.country}"
