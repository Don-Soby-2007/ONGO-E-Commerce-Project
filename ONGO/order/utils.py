import weasyprint
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from .models import Invoice
from coupons.models import Coupon, CouponUsage
from decimal import Decimal


from django.contrib.staticfiles import finders


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


def validate_and_apply_coupon(user, coupon_code, base_total):
    """
    Validate coupon against current cart state and calculate discount.
    Returns: (is_valid: bool, discount: Decimal, free_shipping: bool, error_msg: str)
    """
    try:
        coupon = Coupon.objects.get(coupon_code__iexact=coupon_code.strip())
    except Coupon.DoesNotExist:
        return False, Decimal('0.00'), False, "Invalid coupon code"

    # Check coupon active status (time, total usage, active flag)
    if not coupon.is_active():
        return False, Decimal('0.00'), False, "Coupon is expired or inactive"

    # Check user-specific usage limit
    user_usage = CouponUsage.objects.filter(user=user, coupon=coupon).count()
    if user_usage >= coupon.per_user_limit:
        return (False, Decimal('0.00'), False,
                f"You've used this coupon {user_usage} times (limit: {coupon.per_user_limit})")

    # Check min order amount against BASE TOTAL (after other discounts)
    if coupon.min_order_amount and base_total < coupon.min_order_amount:
        return False, Decimal('0.00'), False, (
            f"Minimum order amount ₹{coupon.min_order_amount} not met. "
            f"Your eligible cart total is ₹{base_total}"
        )

    # Calculate discount
    discount = Decimal('0.00')
    free_shipping = False

    if coupon.discount_type == 'percent':
        discount = base_total * (coupon.value / Decimal('100'))
        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)
    elif coupon.discount_type == 'fixed':
        discount = min(coupon.value, base_total)
    elif coupon.discount_type == 'free_shipping':
        free_shipping = True

    return True, discount, free_shipping, ""
