import asyncio, math
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

PORTS = [14540 + i for i in range(10)]  # ננסה 14540..14549

def add_meters(lat_deg, lon_deg, north_m, east_m):
    """המרת היסטים במטרים ל-lat/lon יחסית לנקודת הבית."""
    dlat = north_m / 111_111.0
    dlon = east_m / (111_111.0 * math.cos(math.radians(lat_deg)))
    return lat_deg + dlat, lon_deg + dlon

async def connect_any():
    for p in PORTS:
        d = System()
        try:
            print(f"Connecting to udpin://:{p} (udp:// גם יעבוד)")
            # חלק מהגרסאות מדפיסות אזהרה על udp://; שתי הכתובות תקינות ב-SITL
            await d.connect(system_address=f"udpin://:{p}")
            async for s in d.core.connection_state():
                if s.is_connected:
                    print(f"Connected on {p}")
                    return d
        except Exception as e:
            print(f"Port {p} failed: {e}")
    raise RuntimeError("No PX4 found on 14540-14549")

async def wait_until_ready(drone):
    print("Waiting for health and home position…")
    home = None
    async for h in drone.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            async for pos in drone.telemetry.home():
                home = pos
                break
            if home:
                print("Health OK, home acquired.")
                break
    return home

async def build_and_upload_mission(drone, home_lat, home_lon, rel_alt=10.0, speed=3.0):
    # נקודות יחסיות במטרים (North, East)
    waypoints_ne = [
        (  0,   0),   # נקודת התחלה
        ( 20,   0),   # צפונה 20 מ'
        ( 20,  20),   # מזרחה 20 מ'
        (  0,  20),   # דרומה 20 מ'
    ]

    items = []
    for (n, e) in waypoints_ne:
        lat, lon = add_meters(home_lat, home_lon, n, e)
        items.append(
            MissionItem(
                latitude_deg=lat,
                longitude_deg=lon,
                relative_altitude_m=rel_alt,
                speed_m_s=speed,
                is_fly_through=True,
                gimbal_pitch_deg=0.0,
                gimbal_yaw_deg=0.0,
                camera_action=MissionItem.CameraAction.NONE,
                # השדות הנוספים שגרסתך דורשת:
                loiter_time_s=0.0,
                camera_photo_interval_s=0.0,
                acceptance_radius_m=2.0,
                yaw_deg=float("nan"),          # אין יאו ספציפי (NaN = השאר כיוון)
                camera_photo_distance_m=0.0,
                vehicle_action=MissionItem.VehicleAction.NONE
            )
        )

    plan = MissionPlan(items)
    await drone.mission.clear_mission()
    await drone.mission.set_return_to_launch_after_mission(True)
    await drone.mission.upload_mission(plan)
    print("Mission uploaded.")

async def run_mission(drone):
    await drone.action.arm()
    await drone.mission.start_mission()
    print("Mission started.")
    async for progress in drone.mission.mission_progress():
        print(f"Progress: {progress.current}/{progress.total}")
        if progress.current == progress.total:
            break
    print("Mission finished. RTL should engage.")

async def main():
    drone = await connect_any()
    home = await wait_until_ready(drone)
    if not home:
        raise RuntimeError("Home position not available.")
    await build_and_upload_mission(
        drone,
        home_lat=home.latitude_deg,
        home_lon=home.longitude_deg,
        rel_alt=10.0,
        speed=3.0,
    )
    await run_mission(drone)

if __name__ == "__main__":
    asyncio.run(main())
import asyncio, math
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

PORTS = [14540 + i for i in range(10)]  # ננסה 14540..14549

def add_meters(lat_deg, lon_deg, north_m, east_m):
    """המרת היסטים במטרים ל-lat/lon יחסית לנקודת הבית."""
    dlat = north_m / 111_111.0
    dlon = east_m / (111_111.0 * math.cos(math.radians(lat_deg)))
    return lat_deg + dlat, lon_deg + dlon

async def connect_any():
    for p in PORTS:
        d = System()
        try:
            print(f"Connecting to udpin://:{p} (udp:// גם יעבוד)")
            # חלק מהגרסאות מדפיסות אזהרה על udp://; שתי הכתובות תקינות ב-SITL
            await d.connect(system_address=f"udp://:{p}")
            async for s in d.core.connection_state():
                if s.is_connected:
                    print(f"Connected on {p}")
                    return d
        except Exception as e:
            print(f"Port {p} failed: {e}")
    raise RuntimeError("No PX4 found on 14540-14549")

async def wait_until_ready(drone):
    print("Waiting for health and home position…")
    home = None
    async for h in drone.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            async for pos in drone.telemetry.home():
                home = pos
                break
            if home:
                print("Health OK, home acquired.")
                break
    return home

async def build_and_upload_mission(drone, home_lat, home_lon, rel_alt=10.0, speed=3.0):
    # נקודות יחסיות במטרים (North, East)
    waypoints_ne = [
        (  0,   0),   # נקודת התחלה
        ( 20,   0),   # צפונה 20 מ'
        ( 20,  20),   # מזרחה 20 מ'
        (  0,  20),   # דרומה 20 מ'
    ]

    items = []
    for (n, e) in waypoints_ne:
        lat, lon = add_meters(home_lat, home_lon, n, e)
        items.append(
            MissionItem(
                latitude_deg=lat,
                longitude_deg=lon,
                relative_altitude_m=rel_alt,
                speed_m_s=speed,
                is_fly_through=True,
                gimbal_pitch_deg=0.0,
                gimbal_yaw_deg=0.0,
                camera_action=MissionItem.CameraAction.NONE,
                # השדות הנוספים שגרסתך דורשת:
                loiter_time_s=0.0,
                camera_photo_interval_s=0.0,
                acceptance_radius_m=2.0,
                yaw_deg=float("nan"),          # אין יאו ספציפי (NaN = השאר כיוון)
                camera_photo_distance_m=0.0,
                vehicle_action=MissionItem.VehicleAction.NONE
            )
        )

    plan = MissionPlan(items)
    await drone.mission.clear_mission()
    await drone.mission.set_return_to_launch_after_mission(True)
    await drone.mission.upload_mission(plan)
    print("Mission uploaded.")

async def run_mission(drone):
    await drone.action.arm()
    await drone.mission.start_mission()
    print("Mission started.")
    async for progress in drone.mission.mission_progress():
        print(f"Progress: {progress.current}/{progress.total}")
        if progress.current == progress.total:
            break
    print("Mission finished. RTL should engage.")

async def main():
    drone = await connect_any()
    home = await wait_until_ready(drone)
    if not home:
        raise RuntimeError("Home position not available.")
    await build_and_upload_mission(
        drone,
        home_lat=home.latitude_deg,
        home_lon=home.longitude_deg,
        rel_alt=10.0,
        speed=3.0,
    )
    await run_mission(drone)

if __name__ == "__main__":
    asyncio.run(main())
