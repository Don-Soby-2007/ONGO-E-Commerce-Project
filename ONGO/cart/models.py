from django.db import models
from accounts.models import User
from products.models import ProductVariant

from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


class Cart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    product_variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product_variant')
