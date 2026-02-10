# cart/utils.py
from decimal import Decimal
from coupons.models import Coupon, CouponUsage
from cart.models import Cart
from offers.models import GlobalOffer


def get_cart_base_total(user):
    """
    Calculate cart total AFTER product/category offers and global offers,
    BEFORE shipping and coupons. Matches CartView logic.
    Returns: (base_total: Decimal, shipping: Decimal, applied_global_offers: list)
    """
    cart_items = Cart.objects.filter(user=user).select_related(
        'product_variant__product'
    ).prefetch_related(
        'product_variant__images'
    )

    if not cart_items.exists():
        return Decimal('0.00'), Decimal('100.00'), []

    # Calculate after product/category offers (line discounts)
    total_after_line_discounts = Decimal('0.00')
    for item in cart_items:
        variant = item.product_variant
        price = variant.final_price if variant.final_price else Decimal('0.00')
        total_after_line_discounts += price * item.quantity

    # Apply global offers (cart-level discounts)
    base_total = total_after_line_discounts
    shipping = Decimal('100.00')
    applied_global_offers = []

    global_offers = GlobalOffer.objects.filter(
        min_cart_value__lte=base_total,
        active=True
    ).order_by('-priority')

    for offer in global_offers:
        if not offer.is_active_now():
            continue

        if offer.discount_type == 'percent':
            discount = base_total * (Decimal(offer.value) / Decimal('100'))
            if offer.max_discount:
                discount = min(discount, Decimal(offer.max_discount))
            base_total -= discount
            applied_global_offers.append({'type': 'percent', 'amount': discount})

        elif offer.discount_type == 'fixed':
            discount = min(Decimal(offer.value), base_total)
            base_total -= discount
            applied_global_offers.append({'type': 'fixed', 'amount': discount})

        elif offer.discount_type == 'free_shipping' and offer.is_active_now():
            shipping = Decimal('0.00')
            applied_global_offers.append({'type': 'free_shipping'})
            break  # Only one free shipping offer applies

    return base_total, shipping, applied_global_offers


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
        return False, Decimal('0.00'), False, f"You've used this coupon {user_usage} times (limit: {coupon.per_user_limit})"

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
