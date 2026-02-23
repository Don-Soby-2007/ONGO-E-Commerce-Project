from django.db import models
from django.utils.translation import gettext_lazy as _

from order.models import Order, OrderItem
from accounts.models import User


class Return(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='returns'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='returns'
    )

    RETURN_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    status = models.CharField(
        max_length=20,
        choices=RETURN_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    return_reason = models.TextField(
        help_text=_("Overall reason for the return request")
    )
    admin_notes = models.TextField(
        blank=True,
        help_text=_("Notes from admin regarding acceptance/rejection")
    )

    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refunded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When the return was processed by admin")
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Return Request'
        verbose_name_plural = 'Return Requests'
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Return #{self.id} - {self.get_status_display()} ({self.order})"

    @property
    def total_items(self):
        """Total number of items being returned in this request"""
        return self.return_items.aggregate(
            total=models.Sum('quantity')
        )['total'] or 0


class ReturnItem(models.Model):
    """Individual items being returned"""

    return_request = models.ForeignKey(
        Return,
        on_delete=models.CASCADE,
        related_name='return_items'
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='return_items'
    )

    quantity = models.PositiveIntegerField(
        help_text=_("Number of units being returned")
    )
    item_reason = models.TextField(
        blank=True,
        help_text=_("Specific reason for returning this item")
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Return Item'
        verbose_name_plural = 'Return Items'
        constraints = [
            models.UniqueConstraint(
                fields=['return_request', 'order_item'],
                name='unique_order_item_per_return'
            )
        ]

    def __str__(self):
        return f"{self.quantity}x {self.order_item.product.name} from Return #{self.return_request.id}"
