from decimal import Decimal, ROUND_HALF_UP
from cart.models import Cart
from offers.models import GlobalOffer
from products.utils import calculate_discount


def _to_decimal(value, default='0'):

    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _round_currency(value):

    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def get_cart_items_for_user(request, user):
    cart = Cart.objects.filter(user=user).select_related(
        'product_variant',
        'product_variant__product',
        'product_variant__product__category'  # Critical: avoid N+1 on category
    ).prefetch_related(
        'product_variant__images'
    )

    cart_items = []
    items_subtotal_exact = Decimal('0')
    total_payable_exact = Decimal('0')

    for cart_item in cart:
        variant = cart_item.product_variant
        product = variant.product

        original_price = _to_decimal(variant.final_price, '0')
        offer_price = original_price
        offer_type = None
        offer_value = None
        offer_scope = None
        has_offer = False
        print('Debug: offer_price: ', offer_price)

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

            discounted = calculate_discount(original_price, product_offer)
            print('Debug discounted:', discounted)

            offer_price = max(Decimal('0'), discounted)

            print('DEBUG offer_price: ', offer_price)

        # CATEGORY OFFER
        category_offer = None
        if product.category and hasattr(product.category, 'offer') and product.category.offer:
            category_offer = (
                product.category.offer
                .filter(active=True)
                .order_by('-priority')
                .first()
            )

        if category_offer and category_offer.is_active_now():
            cat_value = _to_decimal(category_offer.value)
            cat_type = category_offer.discount_type
            cat_price = calculate_discount(original_price, category_offer)

            if cat_price < offer_price:
                offer_price = cat_price
                offer_type = cat_type
                offer_value = cat_value
                has_offer = True
                offer_scope = 'category'

            print('Debug: offer_price: ', offer_price, offer_type, offer_value, offer_scope, cat_price)

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

        print('DEBUG cart_items: ', cart_items)

    shipping = Decimal('100')
    applied_global_offers = []
    applicable_global_offers = []

    global_offers = GlobalOffer.objects.filter(
        min_cart_value__lte=total_payable_exact,
        active=True
    ).order_by('-priority')

    for offer in global_offers:
        if (
            not offer.is_active_now() or offer.discount_type not in ['percent', 'fixed']
            or offer.name == 'First_Ord_Referral_Off'
        ):
            continue

        disc_amt = 0
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
    print("Debug befor applying the shipping: ", applied_global_offers)

    for offer in global_offers:
        if (
            offer.name == 'First_Ord_Referral_Off' and offer.discount_type == 'percent' and offer.is_active_now()
            and _to_decimal(offer.min_cart_value) <= total_payable_exact
        ):
            if (
                request.user.orders.count() == 0 and not request.user.has_claimed_referral_discount
                and request.user.referred_by
            ):
                disc_amt = 0
                offer_val = _to_decimal(offer.value)
                disc_amt = total_payable_exact * (offer_val / Decimal('100'))
                if offer.max_discount:
                    disc_amt = min(disc_amt, _to_decimal(offer.max_discount))

                total_payable_exact = _round_currency(total_payable_exact - disc_amt)
                applied_global_offers.append({
                    "id": offer.id,
                    "name": offer.name,
                    "type": offer.discount_type,
                    "value": float(_round_currency(offer.value)),
                    "discount_amount": float(_round_currency(disc_amt)),
                })

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

    print("Debug after applying the shipping: ", applied_global_offers)

    if 'applied_coupon' in request.session:
        applied_coupon = request.session.get('applied_coupon')
        coupon_discount_exact = Decimal('0.00')

        if applied_coupon:

            discount_str = applied_coupon.get('discount_amount', '0.00')
            coupon_discount_exact = _to_decimal(discount_str)

            if applied_coupon.get('free_shipping'):
                shipping = Decimal('0.00')

            coupon_discount_exact = min(coupon_discount_exact, total_payable_exact)
            total_payable_exact -= coupon_discount_exact
            total_payable_exact = max(total_payable_exact, Decimal('0.00'))

    summary = {
        "items_subtotal": float(_round_currency(items_subtotal_exact)),
        "cart_discount": float(_round_currency(cart_discount_exact)),
        "shipping": float(_round_currency(shipping)),
        "tax": 0.0,
        "total_payable": float(_round_currency(total_payable_exact + shipping)),
        "applied_global_offers": applied_global_offers,
        "applied_coupon": request.session.get('applied_coupon', {})
    }

    return cart_items, summary
