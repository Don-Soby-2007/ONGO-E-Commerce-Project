import uuid
from django.db import models
from django.utils import timezone
from accounts.models import User, Address
from django.core.validators import MinValueValidator
from products.models import ProductVariant


class Order(models.Model):

    order_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text="Public unique identifier for the order"
    )

    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]

    PAYMENT_METHOD_CHOICE = [
        ('cod', 'COD'),
        ('online', 'Online'),
        ('wallet', 'Wallet'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICE,
        default='COD',
    )
    shipping = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.user.email}"

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):

    ITEM_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
        ('refunded', 'Refunded'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)

    product_name = models.CharField(max_length=255)
    variant_options = models.JSONField()
    image_url = models.URLField()
    price_at_time_of_order = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=ITEM_STATUS_CHOICES,
        default='pending'
    )

    cancel_reason = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.price_at_time_of_order
        super().save(*args, **kwargs)


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='invoices/')

    def __str__(self):
        return f"Invoice {self.invoice_number} for Order {self.order.order_id}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last_invoice = Invoice.objects.order_by('-created_at').first()
            if last_invoice:
                try:
                    last_number = int(last_invoice.invoice_number.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            self.invoice_number = f"INV-{timezone.now().year}-{new_number:05d}"
        super().save(*args, **kwargs)
