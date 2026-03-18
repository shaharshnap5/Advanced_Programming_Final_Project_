import math

def calculate_euclidean_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    return math.sqrt((lon2 - lon1) ** 2 + (lat2 - lat1) ** 2)