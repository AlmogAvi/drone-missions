import asyncio
import logging
from mavsdk import System
from .utils import connect_drone, ensure_armed

log = logging.getLogger(__name__)

async def run_takeoff_land(conn_url: str, alt: float = 20.0):
    """
    המראה לגובה alt, השהיה קצרה, נחיתה.
    """
    drone: System = await connect_drone(conn_url)

    log.info("Setting takeoff altitude: %.1f m", alt)
    await drone.action.set_takeoff_altitude(alt)

    await ensure_armed(drone)

    log.info("Taking off ...")
    await drone.action.takeoff()

    # מחכים להגיע קרוב לגובה
    await asyncio.sleep(6)

    log.info("Landing ...")
    await drone.action.land()

    # ממתין עד שהרחפן לא באוויר
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            break
        await asyncio.sleep(0.5)

    log.info("Mission complete: landed.")

