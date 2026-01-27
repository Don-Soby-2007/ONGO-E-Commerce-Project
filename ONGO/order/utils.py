import weasyprint
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from .models import Invoice
from cart.models import Cart

from django.contrib.staticfiles import finders


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
    invoice, created = Invoice.objects.get_or_create(order=order)

    css_path = finders.find('css/order/invoice.css')
    css_content = ""
    if css_path:
        try:
            with open(css_path, 'r') as f:
                css_content = f.read()
        except Exception as e:
            print(f"⚠️ CSS load error: {e}")
    else:
        print("⚠️ CSS file not found by staticfiles finders!")

    context = {
        'order': order,
        'invoice': invoice,
        'user': order.user,
        'items': order.items.all(),
        'for_pdf': True,
        'css_content': css_content
    }

    html_string = render_to_string('order/invoice.html', context)

    pdf_file = weasyprint.HTML(
        string=html_string,
        base_url=None,
    ).write_pdf()

    filename = f"Invoice_{invoice.invoice_number}.pdf"
    invoice.pdf_file.save(filename, ContentFile(pdf_file), save=True)

    return invoice
