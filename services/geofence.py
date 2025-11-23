import math
from core.config import settings


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on Earth in kilometers
    """
    R = 6371  # Earth radius in km

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def is_in_basel_area(latitude: float, longitude: float) -> bool:
    """
    Check if coordinates are within Art Basel Miami area
    """
    distance = haversine_distance(
        settings.BASEL_LAT,
        settings.BASEL_LON,
        latitude,
        longitude
    )
    return distance <= settings.BASEL_RADIUS_KM
