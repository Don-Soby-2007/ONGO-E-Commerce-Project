import weasyprint
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from .models import Invoice
from coupons.models import Coupon, CouponUsage
from decimal import Decimal, ROUND_HALF_UP

import razorpay
from django.conf import settings


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
        print(type(coupon.value))
        discount = base_total * (coupon.value / Decimal('100'))
        if coupon.max_discount:
            discount = min(discount, coupon.max_discount)
    elif coupon.discount_type == 'fixed':
        discount = min(coupon.value, base_total)
    elif coupon.discount_type == 'free_shipping':
        free_shipping = True

    return True, discount, free_shipping, ""


razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def create_razorpay_order(amount_inr: Decimal) -> dict:
    """
    Create Razorpay order (amount in INR, converted to paisa)
    Returns: {'id': 'order_xxx', 'amount': 50000, 'currency': 'INR', ...}
    """
    print('razorpay order creation called')
    return razorpay_client.order.create({
        'amount': int(amount_inr * 100),
        'currency': 'INR',
    })


def verify_razorpay_signature(params_dict: dict) -> bool:
    """
    Verify Razorpay payment signature
    params_dict should contain: razorpay_order_id, razorpay_payment_id, razorpay_signature
    """
    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
        return True
    except Exception:
        return False


def calculate_item_refund_amount(item, order) -> Decimal:

    zero = Decimal('0.00')
    quant = Decimal('0.01')

    if not item or not order:
        return zero

    if not item.quantity or item.quantity <= 0:
        return zero

    # Stable order denominator: sum of all order-item net values before order-level discounts.
    order_net_total = zero
    for line in order.items.all().only('price_at_purchase', 'quantity', 'line_discount'):
        line_gross = Decimal(str(line.price_at_purchase)) * Decimal(line.quantity)
        line_disc = Decimal(str(line.line_discount or zero))
        line_net = max(line_gross - line_disc, zero)
        order_net_total += line_net

    if order_net_total <= 0:
        return zero

    item_gross_total = Decimal(str(item.price_at_purchase)) * Decimal(item.quantity)
    item_line_disc_total = Decimal(str(item.line_discount or zero))
    item_net_total = max(item_gross_total - item_line_disc_total, zero)

    if item_net_total <= 0:
        return zero

    # `line_discount` is already reflected at item level, so only prorate
    # true order-level discount here to avoid double-discounting.
    order_level_disc_total = Decimal(str(order.coupon_discount or zero))

    # Item's share of order-level discounts for full line refund.
    item_total_ratio = item_net_total / order_net_total
    item_total_prorated_disc = order_level_disc_total * item_total_ratio
    item_max_refundable = max(item_net_total - item_total_prorated_disc, zero)

    already_refunded = Decimal(str(getattr(item, 'refunded_amount', zero) or zero))
    remaining_refundable = max(item_max_refundable - already_refunded, zero)

    final_refund = min(item_max_refundable, remaining_refundable)
    return final_refund.quantize(quant, rounding=ROUND_HALF_UP)
