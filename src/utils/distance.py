import math


def euclidean_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute Euclidean distance between two (lat, lon) points."""
    return math.hypot(lat1 - lat2, lon1 - lon2)
