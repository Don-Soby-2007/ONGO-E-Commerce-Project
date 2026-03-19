
from django.http import JsonResponse
import logging
from .models import PincodeLocation

logger = logging.getLogger(__name__)

# Create your views here.


def location_stats(pincode: str) -> dict:
    pincode = pincode.strip()
    response_data = {}
    try:
        location = PincodeLocation.objects.get(pincode=pincode)
        response_data = {
            'pincode': location.pincode,
            'district': location.district,
            'state': location.state,
            'latitude': float(location.latitude) if location.latitude else None,
            'longitude': float(location.longitude) if location.longitude else None,
        }
        return response_data
    except PincodeLocation.DoesNotExist:
        logger.warning(f"Pincode {pincode} not found in database.")
        return response_data

    except Exception as e:
        logger.error(f"Error fetching location stats for pincode {pincode}: {str(e)}")
        return response_data


def distance_between_location(lat1, lon1, lat2, lon2):
    from math import radians, cos, sin, asin, sqrt

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))

    R = 6371.0
    return round(R * c, 1)


def get_distance_to_customer(customer_pincode):
    loc1 = location_stats(customer_pincode)
    loc2 = location_stats("682001")  # Assuming 110001 is the warehouse pincode

    if not loc1 or not loc2:
        return None

    if loc1['latitude'] is None or loc1['longitude'] is None or loc2['latitude'] is None or loc2['longitude'] is None:
        return None

    return distance_between_location(loc1['latitude'], loc1['longitude'], loc2['latitude'], loc2['longitude'])


def pincode_stats(request, pincode):
    if request.method == 'GET':

        location_info = location_stats(pincode)
        stats = {}

        if location_info:
            stats = {
                'pincode': location_info.get('pincode'),
                'district': location_info.get('district'),
                'state': location_info.get('state')
                }

            return JsonResponse(stats)
        else:
            return JsonResponse({'error': 'Pincode not found'}, status=404)

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
