import asyncio
import logging
from typing import List, Tuple
from mavsdk import System
from .utils import connect_drone, ensure_armed, get_current_position, meters_to_latlon_offsets, set_speed

log = logging.getLogger(__name__)

async def run_survey(
    conn_url: str,
    alt: float = 30.0,
    speed: float = 7.0,
    width_m: float = 120.0,
    height_m: float = 90.0,
    lane_spacing_m: float = 20.0,
    sweep_east_first: bool = True,
):
    """
    "Survey" בסגנון lawnmower: טסים קווים מקבילים במלבנים סביב הבית.
    משתמש ב-goto_location לנקודות פינה של כל קו סריקה.
    """
    drone: System = await connect_drone(conn_url)
    await set_speed(drone, speed)
    await ensure_armed(drone)

    await drone.action.set_takeoff_altitude(alt)
    await drone.action.takeoff()
    await asyncio.sleep(5)

    pos = await get_current_position(drone)
    lat0, lon0 = pos.latitude_deg, pos.longitude_deg
    base_abs_alt = pos.absolute_altitude_m + alt
    log.info("Home position: %.6f, %.6f | Survey %.0fx%.0f m | lane=%.0f m",
             lat0, lon0, width_m, height_m, lane_spacing_m)

    hh = height_m / 2.0
    hw = width_m / 2.0

    # נבנה קווי סריקה לאורך ציר ה-"גובה" (North-South), ומתקדמים במרווחים לאורך ה-"רוחב" (East-West)
    lanes: List[Tuple[float, float]] = []
    x = -hw
    direction = 1  # 1=North first, -1=South first
    if not sweep_east_first:
        x = hw
        step = -lane_spacing_m
    else:
        step = lane_spacing_m

    while (x <= hw + 1e-6) if step > 0 else (x >= -hw - 1e-6):
        # שתי נקודות קצה של כל קו (דרום->צפון או להפך)
        start_dn = -hh if direction == 1 else +hh
        end_dn   = +hh if direction == 1 else -hh

        # תחילה לקצה הראשון
        d_lat1, d_lon1 = meters_to_latlon_offsets(start_dn, x, lat0)
        lat1, lon1 = lat0 + d_lat1, lon0 + d_lon1
        lanes.append((lat1, lon1))

        # ואז לקצה השני
        d_lat2, d_lon2 = meters_to_latlon_offsets(end_dn, x, lat0)
        lat2, lon2 = lat0 + d_lat2, lon0 + d_lon2
        lanes.append((lat2, lon2))

        # קו הבא
        x += step
        direction *= -1

    # ביצוע המסלול
    est_leg = max(height_m, lane_spacing_m) / max(speed, 0.1)
    for i, (lat, lon) in enumerate(lanes, 1):
        log.info("Lane pt %d/%d -> lat=%.6f lon=%.6f alt=%.1f", i, len(lanes), lat, lon, alt)
        await drone.action.goto_location(lat, lon, base_abs_alt, 0.0)
        await asyncio.sleep(max(4, int(est_leg)))

    log.info("Survey complete. Landing ...")
    await drone.action.land()
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            break
        await asyncio.sleep(0.5)
    log.info("Done.")
