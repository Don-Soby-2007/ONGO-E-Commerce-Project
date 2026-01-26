from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Order
from .utils import generate_invoice_pdf


@receiver(post_save, sender=Order)
def invoice_generation_signal(sender, instance, created, **kwargs):
    """
    Triggers invoice generation when order status changes to 'delivered'.
    """
    if instance.status == 'delivered' and not hasattr(instance, 'invoice'):
        generate_invoice_pdf(instance)
