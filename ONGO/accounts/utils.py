import re
from .models import Address

import logging

logger = logging.getLogger(__name__)


def create_address_from_request(request, redirect_on_success=True):
    """
    Handles address creation from POST data.
    Returns (success: bool, message: str, redirect_url: str or None)
    """
    full_name = request.POST.get('fullName', '').strip()
    street_address = request.POST.get('streetAddress', '').strip()
    phone_number = request.POST.get('phoneNumber', '').strip()
    city = request.POST.get('city', '').strip()
    state = request.POST.get('state', '').strip()
    postal_code = request.POST.get('postalCode', '').strip()
    country = request.POST.get('country', '').strip()
    is_default = request.POST.get('defaultAddress') == 'on'

    user = request.user

    # Validation
    if not re.match(r'^[a-zA-Z\s]{3,}$', full_name):
        return False, "Name must contain only letters and spaces (min 3 chars).", None

    if not re.match(r'^[a-zA-Z0-9\s,.\-/#]{5,}$', street_address):
        return False, "Address seems invalid. Use letters, numbers, and common symbols.", None

    if not re.match(r'^\+?[0-9]{10,15}$', phone_number):
        return False, "Enter a valid phone number (10-15 digits).", None

    if not re.match(r'^[a-zA-Z\s]+$', city):
        return False, "City must contain only letters.", None

    if not re.match(r'^[a-zA-Z\s]+$', state):
        return False, "State must contain only letters.", None

    if not re.match(r'^[0-9]{5,6}$', postal_code):
        return False, "Postal code must be 5-6 digits.", None

    if not country:
        return False, "Please select a country.", None

    try:
        # Enforce default logic
        if is_default:
            Address.objects.filter(user=user, is_default=True).update(is_default=False)
        elif not Address.objects.filter(user=user).exists():
            is_default = True

        Address.objects.create(
            user=user,
            name=full_name,
            street_address=street_address,
            phone=phone_number,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            is_default=is_default
        )
        return True, "Address added successfully!", 'manage_address'

    except Exception as e:
        logger.error(f"Error saving address for user {request.user}: {e}")
        return False, "Something went wrong while saving the address.", None
