import asyncio
import logging
from typing import List, Tuple
from mavsdk import System
from .utils import connect_drone, ensure_armed, get_current_position, meters_to_latlon_offsets, set_speed

log = logging.getLogger(__name__)

async def run_square(conn_url: str, alt: float = 20.0, speed: float = 5.0, size_m: float = 40.0):
    """
    טיסה בריבוע סביב נקודת ההמראה (home) בגודל size_m.
    משתמש ב-goto_location בכל פינה.
    """
    drone: System = await connect_drone(conn_url)
    await set_speed(drone, speed)
    await ensure_armed(drone)

    log.info("Setting takeoff altitude: %.1f m", alt)
    await drone.action.set_takeoff_altitude(alt)
    await drone.action.takeoff()
    await asyncio.sleep(5)

    pos = await get_current_position(drone)
    lat0, lon0 = pos.latitude_deg, pos.longitude_deg
    log.info("Home position: %.6f, %.6f", lat0, lon0)

    # נקודות הריבוע (N,E) במטרים סביב הבית
    half = size_m / 2.0
    corners_ne: List[Tuple[float, float]] = [
        ( half,  half),  # NE
        ( half, -half),  # NW
        (-half, -half),  # SW
        (-half,  half),  # SE
    ]

    for i, (dn, de) in enumerate(corners_ne, 1):
        d_lat, d_lon = meters_to_latlon_offsets(dn, de, lat0)
        lat, lon = lat0 + d_lat, lon0 + d_lon
        log.info("Leg %d: goto lat=%.6f lon=%.6f alt=%.1f (speed=%.1f)", i, lat, lon, alt, speed)
        await drone.action.goto_location(lat, lon, pos.absolute_altitude_m + alt, 0.0)
        await asyncio.sleep(max(6, int(size_m / max(speed, 0.1))))  # זמן משוער לקטע

    log.info("Square complete. Landing ...")
    await drone.action.land()
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            break
        await asyncio.sleep(0.5)
    log.info("Done.")
