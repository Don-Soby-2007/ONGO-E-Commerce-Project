from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from products.models import Product, Category


class TimedModel(models.Model):

    name = models.CharField(max_length=180)
    active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(default=10)   # higher = wins in conflicts

    class Meta:
        abstract = True
        ordering = ['-priority', '-start_date']

    def is_active_now(self):
        now = timezone.now()
        return self.active and self.start_date <= now and (self.end_date is None or now <= self.end_date)


class ProductOffer(TimedModel):
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='active_offer'
    )
    discount_type = models.CharField(
        max_length=20,
        choices=[('percent', 'Percentage'), ('fixed', 'Fixed amount')],
        default='percent'
    )
    value = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    max_discount_amount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="Cap for percentage discounts"
    )

    def __str__(self):
        return f"{self.name} → {self.product}"


class CategoryOffer(TimedModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='active_offer'
    )
    discount_type = models.CharField(
        max_length=20,
        choices=[('percent', 'Percentage'), ('fixed_per_item', 'Fixed per item')],
        default='percent'
    )
    value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    min_items = models.PositiveSmallIntegerField(default=1, help_text="Minimum quantity in cart to qualify")

    def __str__(self):
        return f"{self.name} → {self.category.name}"


class GlobalOffer(TimedModel):
    DISCOUNT_CHOICES = [
        ('percent', 'Percentage off cart'),
        ('fixed',   'Fixed amount off cart'),
        ('free_shipping', 'Free shipping'),
    ]
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICES, default='percent')
    value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    min_cart_value = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Minimum subtotal to qualify"
    )
    max_discount = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return self.name
