import weasyprint
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.conf import settings
from .models import Invoice
from cart.models import Cart


def get_cart_items_for_user(user):
    cart_items = []
    cart = Cart.objects.filter(user=user).select_related(
        'product_variant__product'
    ).prefetch_related('product_variant__images')

    for item in cart:
        variant = item.product_variant
        product = variant.product
        image_obj = variant.images.filter(is_primary=True).first() or variant.images.first()
        image_url = image_obj.image_url if image_obj else "https://via.placeholder.com/150?text=No+Image"
        cart_items.append({
            'id': item.id,
            'product_name': product.name,
            'price': float(variant.final_price),
            'quantity': item.quantity,
            'image_url': image_url,
            'size': variant.size,
            'color': variant.color,
            'in_stock': variant.is_in_stock,
        })
    return cart_items


def generate_invoice_pdf(order):
    """
    Generates a PDF invoice for the given order and saves it to the Invoice model.
    """
    # 1. Create Invoice object FIRST to generate invoice_number and created_at
    invoice, created = Invoice.objects.get_or_create(order=order)

    # 2. Prepare context with the invoice object
    context = {
        'order': order,
        'invoice': invoice, # Explicitly pass invoice
        'user': order.user,
        'items': order.items.all(),
    }

    # 3. Render HTML
    html_string = render_to_string('order/invoice.html', context)

    # 4. Generate PDF
    if settings.DEBUG:
        pass

    pdf_file = weasyprint.HTML(string=html_string, base_url=str(settings.BASE_DIR)).write_pdf()

    # 5. Save PDF to the existing invoice object
    filename = f"Invoice_{invoice.invoice_number}.pdf"
    invoice.pdf_file.save(filename, ContentFile(pdf_file), save=True)

    return invoice
