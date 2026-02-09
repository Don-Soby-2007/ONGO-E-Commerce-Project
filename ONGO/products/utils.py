from decimal import Decimal


def calculate_discount(price, offer):
    if offer.discount_type == 'percent':
        discount = price * (offer.value / Decimal('100'))
        if hasattr(offer, 'max_discount_amount') and offer.max_discount_amount:
            discount = min(discount, offer.max_discount_amount)
        return price - discount
    else:  # fixed
        return max(price - offer.value, Decimal('0'))
