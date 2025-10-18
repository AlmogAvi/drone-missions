from typing import List, Tuple
import math

def build_lawnmower(origin_lat: float, origin_lon: float, altitude_m: float,
                    width_m: float, height_m: float, lane_spacing_m: float) -> List[Tuple[float, float, float]]:
    """
    יוצר רשימת waypoints לסריקה מלבנית בגובה קבוע.
    ההמרות מ' למעלות מקורבות ומתאימות לשטחים קטנים (דמו).
    """
    def meters_to_deg_lat(m: float) -> float:
        return m / 111_320.0

    def meters_to_deg_lon(m: float, lat_deg: float) -> float:
        k = 111_320.0 * max(0.3, abs(math.cos(math.radians(lat_deg))))
        return m / k

    waypoints: List[Tuple[float,float,float]] = []
    lanes = int(height_m // lane_spacing_m) + 1
    left_lon  = origin_lon - meters_to_deg_lon(width_m/2, origin_lat)
    right_lon = origin_lon + meters_to_deg_lon(width_m/2, origin_lat)
    start_lat = origin_lat - meters_to_deg_lat(height_m/2)

    for i in range(lanes):
        lat_i = start_lat + meters_to_deg_lat(i * lane_spacing_m)
        if i % 2 == 0:
            waypoints += [(lat_i, left_lon, altitude_m), (lat_i, right_lon, altitude_m)]
        else:
            waypoints += [(lat_i, right_lon, altitude_m), (lat_i, left_lon, altitude_m)]
    return waypoints
