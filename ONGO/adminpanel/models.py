from django.db import models
from django.utils import timezone

# Create your models here.


class Banner(models.Model):

    LOCATION_CHOICES = [
        ("home_hero", "Home Hero"),
        ("home_secondary", "Home Secondary"),
    ]

    title = models.CharField(max_length=200)

    desktop_image = models.URLField()
    desktop_public_id = models.CharField(max_length=200, blank=True, null=True)

    mobile_image = models.URLField(blank=True, null=True)
    mobile_public_id = models.CharField(max_length=200, blank=True, null=True)

    redirect_link = models.URLField(blank=True)

    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)

    priority = models.IntegerField(default=1)

    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'banners'

    def __str__(self):
        return f"banner for {self.title} in {self.location}"
