# cart/utils.py
from decimal import Decimal
from coupons.models import Coupon, CouponUsage
from cart.models import Cart
from offers.models import GlobalOffer


def get_cart_details(user):

    cart = Cart.objects.filter(user=user).select_related(
            'product_variant',
            'product_variant__product'
        ).prefetch_related(
            'product_variant__images'
        )

    cart_items = []

    summary = {}

    items_subtotal = 0
    total_payable = 0
    shipping = 100
    applied_global_offers = []
    applicable_global_offers = []

    from collections import defaultdict
    category_quantities = defaultdict(int)

    for cart_item in cart:
        cat_id = cart_item.product_variant.product.category.id
        category_quantities[cat_id] += cart_item.quantity

    for cart_item in cart:
        variant = cart_item.product_variant
        product = variant.product

        # for offer calculation
        variant_price = float(variant.final_price) if variant.final_price else None
        offer_price = variant_price
        offer_type = None
        offer_value = None
        offer_scope = None
        has_offer = False
        original_price = variant_price

        product_offer = (
            product.offer
            .filter(active=True)
            .order_by('-priority')
            .first()
        )
        category_offer = (
                product.category.offer
                .filter(active=True)
                .order_by('-priority')
                .first()
            )

        category_eligible = False
        if category_offer and category_offer.is_active_now():
            required_min = category_offer.min_items
            actual_in_cart = category_quantities.get(product.category.id, 0)
            if actual_in_cart >= required_min:
                category_eligible = True

        if product_offer and product_offer.is_active_now():
            offer_type = product_offer.discount_type
            offer_value = float(product_offer.value)
            has_offer = True
            offer_scope = 'product'

            if offer_type == 'percent':
                offer_price = variant_price * (1 - offer_value / 100)
                offer_price = min(offer_price, product_offer.max_discount_amount)
            elif offer_type == 'fixed':
                offer_price = max(0, variant_price - offer_value)

        if category_offer and category_offer.is_active_now():

            if category_eligible:
                category_offer_type = category_offer.discount_type
                if category_offer_type == 'percent':
                    category_offer_price = variant_price * (1 - float(category_offer.value) / 100)
                elif category_offer_type == 'fixed_per_item':
                    category_offer_price = max(0, variant_price - float(category_offer.value))

                if category_offer_price < offer_price:
                    offer_price = category_offer_price

                    offer_type = category_offer_type
                    offer_value = float(category_offer.value)
                    has_offer = True
                    offer_scope = 'category'

        image_obj = variant.images.filter(is_primary=True).first()
        if not image_obj:
            image_obj = variant.images.first()
        image_url = image_obj.image_url if image_obj else "https://via.placeholder.com/150?text=No+Image"

        items_subtotal += round(original_price * cart_item.quantity, 2)
        total_payable += round(offer_price * cart_item.quantity, 2)

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

            # Pricing (unit-level)
            "unit_price": round(original_price, 2),
            "offer_price": round(offer_price, 2),
            "discount_per_unit": round(original_price - offer_price, 2),

            # Pricing (line-level)
            "line_subtotal": round(original_price * cart_item.quantity, 2),
            "total_discount": round(
                (original_price - offer_price) * cart_item.quantity, 2
            ),
            "line_total": round(offer_price * cart_item.quantity, 2),

            # Applied offer
            "has_offer": has_offer,
            "applied_offer_scope": offer_scope,  # product / category
            "applied_offer_type": offer_type,  # percent / fixed
            "applied_offer_value": offer_value,
        })

    global_offers = GlobalOffer.objects.filter(min_cart_value__lte=total_payable, active=True).order_by('-priority')

    for offer in global_offers:
        if not offer.is_active_now():
            continue

        offer_value = float(offer.value)

        if offer.discount_type == 'percent':
            discount_amount = round(
                total_payable * (offer_value / 100), 2
            )

            if offer.max_discount:
                discount_amount = min(discount_amount, offer.max_discount)

            applicable_global_offers.append({
                "id": offer.id,
                "name": f"Cart {offer_value}% OFF",
                "type": "percent",
                "value": offer_value,
                "discount_amount": discount_amount
            })

        elif offer.discount_type == 'fixed':
            discount_amount = min(offer_value, total_payable)

            applicable_global_offers.append({
                "id": offer.id,
                "name": f"Cart ₹{offer_value} OFF",
                "type": "fixed",
                "value": offer_value,
                "discount_amount": discount_amount
            })

    top_global_offer = max(applicable_global_offers, key=lambda x: x['discount_amount'])
    total_payable -= top_global_offer['discount_amount']
    applied_global_offers.append(top_global_offer)

    for offer in global_offers:
        if offer.discount_type == 'free_shipping' and offer.is_active_now() and offer.min_cart_value <= total_payable:
            shipping = 0
            applied_global_offers.append({
                "id": offer.id,
                "name": "Free Shipping",
                "type": "free_shipping",
                "value": 0,
                "discount_amount": shipping
            })
            break

    summary = {
        "items_subtotal": round(items_subtotal, 2),
        "cart_discount": round(items_subtotal-total_payable, 2),
        "shipping": shipping,
        "tax": 0,
        "total_payable": total_payable,
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
