import asyncio
import logging
from math import cos, radians
from typing import Tuple
from mavsdk import System

log = logging.getLogger(__name__)

# קבועי המרה: כ~111,320 מ' לדקת רוחב; לאורך קו רוחב—*קוסינוס* קו רוחב
M_PER_DEG_LAT = 111_320.0

def meters_to_latlon_offsets(d_north_m: float, d_east_m: float, ref_lat: float) -> Tuple[float, float]:
    """המרת היסטים במטרים לדלתא של lat/lon סביב ref_lat (בקירוב טוב ליישומים קטנים)."""
    d_lat = d_north_m / M_PER_DEG_LAT
    d_lon = d_east_m / (M_PER_DEG_LAT * cos(radians(ref_lat)))
    return d_lat, d_lon

async def connect_drone(conn_url: str) -> System:
    drone = System()
    log.info("Connecting to %s ...", conn_url)
    await drone.connect(system_address=conn_url)

    async for state in drone.core.connection_state():
        if state.is_connected:
            log.info("MAVSDK connected.")
            break

    # לחכות לבריאות בסיסית של חיישנים/גלובלי
    log.info("Waiting for global position & home position ...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            log.info("Health OK: GNSS & Home ready.")
            break
        await asyncio.sleep(0.5)
    return drone

async def get_current_position(drone: System):
    """מחזיר דגימת מיקום נוכחי (lat, lon, abs_alt_m)."""
    async for pos in drone.telemetry.position():
        return pos  # יש בו latitude_deg / longitude_deg / absolute_altitude_m

async def ensure_armed(drone: System):
    log.info("Arming ...")
    await drone.action.arm()
    async for in_air in drone.telemetry.armed():
        if in_air.is_armed:
            break
    log.info("Armed.")

async def set_speed(drone: System, speed_m_s: float):
    try:
        await drone.action.set_max_speed(speed_m_s)  # MAVSDK ≥1.6
    except Exception:
        # חלק מהגרסאות: set_maximum_speed
        try:
            await drone.action.set_maximum_speed(speed_m_s)  # גרסאות ישנות
        except Exception:
            log.warning("Could not set speed via MAVSDK API (version mismatch).")
