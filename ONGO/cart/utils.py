from decimal import Decimal, ROUND_HALF_UP
from coupons.models import Coupon, CouponUsage
from cart.models import Cart
from offers.models import GlobalOffer
from collections import defaultdict


def _to_decimal(value, default='0'):

    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _round_currency(value):

    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def get_cart_items_for_user(user):
    cart = Cart.objects.filter(user=user).select_related(
        'product_variant',
        'product_variant__product',
        'product_variant__product__category'  # Critical: avoid N+1 on category
    ).prefetch_related(
        'product_variant__images'
    )

    cart_items = []
    category_quantities = defaultdict(int)
    items_subtotal_exact = Decimal('0')
    total_payable_exact = Decimal('0')

    for cart_item in cart:
        if cart_item.product_variant.product.category:
            cat_id = cart_item.product_variant.product.category.id
            category_quantities[cat_id] += cart_item.quantity

    for cart_item in cart:
        variant = cart_item.product_variant
        product = variant.product

        original_price = _to_decimal(variant.final_price, '0')
        offer_price = original_price
        offer_type = None
        offer_value = None
        offer_scope = None
        has_offer = False

        # PRODUCT OFFER
        product_offer = None
        if hasattr(product, 'offer') and product.offer:
            product_offer = (
                product.offer
                .filter(active=True)
                .order_by('-priority')
                .first()
            )

        if product_offer and product_offer.is_active_now():
            offer_type = product_offer.discount_type
            offer_value = _to_decimal(product_offer.value)
            has_offer = True
            offer_scope = 'product'

            if offer_type == 'percent':
                discounted = original_price * (Decimal('1') - offer_value / Decimal('100'))
                if product_offer.max_discount_amount:
                    max_disc = _to_decimal(product_offer.max_discount_amount)
                    discounted = min(discounted, max_disc)
                offer_price = max(Decimal('0'), discounted)
            elif offer_type == 'fixed':
                offer_price = max(Decimal('0'), original_price - offer_value)

        # CATEGORY OFFER
        category_offer = None
        category_eligible = False
        if product.category and hasattr(product.category, 'offer') and product.category.offer:
            category_offer = (
                product.category.offer
                .filter(active=True)
                .order_by('-priority')
                .first()
            )

        if category_offer and category_offer.is_active_now():
            required_min = category_offer.min_items or 0
            actual_in_cart = category_quantities.get(product.category.id, 0)
            category_eligible = actual_in_cart >= required_min

        if category_eligible and category_offer:
            cat_value = _to_decimal(category_offer.value)
            cat_type = category_offer.discount_type

            if cat_type == 'percent':
                cat_price = original_price * (Decimal('1') - cat_value / Decimal('100'))
            elif cat_type == 'fixed_per_item':
                cat_price = max(Decimal('0'), original_price - cat_value)
            else:
                cat_price = original_price

            if cat_price < offer_price:
                offer_price = cat_price
                offer_type = cat_type
                offer_value = cat_value
                has_offer = True
                offer_scope = 'category'

        # IMAGE HANDLING
        image_obj = variant.images.filter(is_primary=True).first() or variant.images.first()
        image_url = image_obj.image_url if image_obj else "https://via.placeholder.com/150?text=No+Image"

        line_subtotal_exact = original_price * cart_item.quantity
        line_total_exact = offer_price * cart_item.quantity
        items_subtotal_exact += line_subtotal_exact
        total_payable_exact += line_total_exact

        cart_items.append({
            # Identity
            "cart_item_id": cart_item.id,
            "product_id": product.id,
            "variant_id": variant.id,
            # Display
            "product_name": product.name,
            "image_url": image_url,
            "color": variant.color,
            "size": variant.size,
            # Quantity & stock
            "quantity": cart_item.quantity,
            "max_qty_allowed": 5,
            "in_stock": variant.is_in_stock,
            "stock": variant.stock,
            # Pricing (unit-level) - ROUNDED FOR DISPLAY
            "unit_price": float(_round_currency(original_price)),
            "offer_price": float(_round_currency(offer_price)),
            "discount_per_unit": float(_round_currency(original_price - offer_price)),
            # Pricing (line-level) - ROUNDED FOR DISPLAY
            "line_subtotal": float(_round_currency(line_subtotal_exact)),
            "total_discount": float(_round_currency(line_subtotal_exact - line_total_exact)),
            "line_total": float(_round_currency(line_total_exact)),
            # Applied offer
            "has_offer": has_offer,
            "applied_offer_scope": offer_scope,
            "applied_offer_type": offer_type,
            "applied_offer_value": float(_round_currency(offer_value)) if offer_value is not None else None,
        })

    shipping = Decimal('100')
    applied_global_offers = []
    applicable_global_offers = []

    global_offers = GlobalOffer.objects.filter(
        min_cart_value__lte=total_payable_exact,
        active=True
    ).order_by('-priority')

    for offer in global_offers:
        if not offer.is_active_now() or offer.discount_type not in ['percent', 'fixed']:
            continue

        offer_val = _to_decimal(offer.value)
        if offer.discount_type == 'percent':
            disc_amt = total_payable_exact * (offer_val / Decimal('100'))
            if offer.max_discount:
                disc_amt = min(disc_amt, _to_decimal(offer.max_discount))
        else:
            disc_amt = min(offer_val, total_payable_exact)

        disc_amt = _round_currency(disc_amt)
        if disc_amt <= Decimal('0'):
            continue

        applicable_global_offers.append({
            "id": offer.id,
            "name": f"Cart {float(_round_currency(offer_val))}% OFF" if offer.discount_type == 'percent'
                    else f"Cart ₹{float(_round_currency(offer_val))} OFF",
            "type": offer.discount_type,
            "value": float(_round_currency(offer_val)),
            "discount_amount": float(_round_currency(disc_amt))
        })

    if applicable_global_offers:

        top_offer = max(applicable_global_offers, key=lambda x: x['discount_amount'])
        discount_amt_dec = _to_decimal(top_offer['discount_amount'])
        total_payable_exact = _round_currency(total_payable_exact - discount_amt_dec)
        applied_global_offers.append(top_offer)
    else:
        total_payable_exact = _round_currency(total_payable_exact)

    for offer in global_offers:
        if (
            offer.discount_type == 'free_shipping' and offer.is_active_now()
            and _to_decimal(offer.min_cart_value) <= total_payable_exact
        ):
            shipping = Decimal('0')
            applied_global_offers.append({
                "id": offer.id,
                "name": "Free Shipping",
                "type": "free_shipping",
                "value": 0.0,
                "discount_amount": 100.0
            })
            break

    cart_discount_exact = items_subtotal_exact - total_payable_exact
    summary = {
        "items_subtotal": float(_round_currency(items_subtotal_exact)),
        "cart_discount": float(_round_currency(cart_discount_exact)),
        "shipping": float(_round_currency(shipping)),
        "tax": 0.0,
        "total_payable": float(_round_currency(total_payable_exact)),
        "applied_global_offers": applied_global_offers,
    }

    return cart_items, summary


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
