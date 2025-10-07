import asyncio
import logging
from typing import List, Tuple
from mavsdk import System
from .utils import connect_drone, ensure_armed, get_current_position, meters_to_latlon_offsets, set_speed

log = logging.getLogger(__name__)

async def run_orbit_rect(
    conn_url: str,
    alt: float = 25.0,
    speed: float = 6.0,
    width_m: float = 80.0,
    height_m: float = 50.0,
    laps: int = 2,
):
    """
    "מסלול היקפי" מלבני סביב הבית: טסים את מלבן (width x height) מספר הקפות.
    בפועל זה מעבר בין 4 פינות בעזרת goto_location.
    """
    drone: System = await connect_drone(conn_url)
    await set_speed(drone, speed)
    await ensure_armed(drone)

    await drone.action.set_takeoff_altitude(alt)
    await drone.action.takeoff()
    await asyncio.sleep(5)

    pos = await get_current_position(drone)
    lat0, lon0 = pos.latitude_deg, pos.longitude_deg
    log.info("Home position: %.6f, %.6f", lat0, lon0)

    hw, hh = width_m / 2.0, height_m / 2.0
    # סדר: NE -> NW -> SW -> SE -> (חזרה ל-NE)
    rect_ne: List[Tuple[float, float]] = [
        (+hh, +hw),  # NE (North, East)
        (+hh, -hw),  # NW
        (-hh, -hw),  # SW
        (-hh, +hw),  # SE
    ]

    for lap in range(1, laps + 1):
        log.info("Lap %d/%d", lap, laps)
        for i, (dn, de) in enumerate(rect_ne, 1):
            d_lat, d_lon = meters_to_latlon_offsets(dn, de, lat0)
            lat, lon = lat0 + d_lat, lon0 + d_lon
            log.info("Corner %d: goto lat=%.6f lon=%.6f alt=%.1f", i, lat, lon, alt)
            await drone.action.goto_location(lat, lon, pos.absolute_altitude_m + alt, 0.0)
            # זמן משוער לכל רגל
            leg_m = width_m if i % 2 == 1 else height_m
            await asyncio.sleep(max(6, int(leg_m / max(speed, 0.1))))

    log.info("Orbit-rectangle complete. Landing ...")
    await drone.action.land()
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            break
        await asyncio.sleep(0.5)
    log.info("Done.")
