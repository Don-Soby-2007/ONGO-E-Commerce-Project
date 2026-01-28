from django.db import models

from order.models import Order
from accounts.models import User

# Create your models here.


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
    return_reason = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the return was processed by admin"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Return'
        verbose_name_plural = 'Returns'
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"Return #{self.id} - {self.get_status_display()} ({self.order})"
