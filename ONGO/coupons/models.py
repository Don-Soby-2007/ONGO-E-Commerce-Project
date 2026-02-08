from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from accounts.models import User
from order.models import Order

# Create your models here.


class Coupon(models.Model):
    DISCOUNT_CHOICES = [
        ('percent', 'Percentage off cart'),
        ('fixed',   'Fixed amount off cart'),
        ('free_shipping', 'Free shipping'),
    ]

    coupon_code = models.CharField(max_length=180, unique=True, db_index=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICES, default='percent')
    value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    max_discount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )
    min_order_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    usage_limit = models.PositiveSmallIntegerField(default=100)
    per_user_limit = models.PositiveSmallIntegerField(default=1)

    active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_active(self):
        now = timezone.now()
        return (
            self.active
            and self.max_limit > 0
            and self.start_date <= now
            and (self.end_date is None or self.end_date >= now)
        )

    def clean(self):
        if self.discount_type == 'percent' and self.value > 100:
            raise ValidationError("Percentage discount cannot exceed 100%")

        if self.discount_type == 'free_shipping' and self.value > 0:
            raise ValidationError("Free shipping coupon should not have a value")

    def __str__(self):
        return f"{self.code}, {self.max_limit}"


class CouponUsage(models.Model):

    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name='usage'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='used_coupon'
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='used_coupon'
    )

    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('coupon', 'order')
        indexes = [
            models.Index(fields=['coupon', 'user']),
        ]
