# src/missions/box_orbit.py
import asyncio, math
from typing import Tuple, List
from mavsdk import System, mission
from mavsdk.telemetry import FlightMode

def meters_to_latlon(lat_deg: float, lon_deg: float, north_m: float, east_m: float) -> Tuple[float, float]:
    R = 6378137.0
    dlat = north_m / R
    dlon = east_m / (R * math.cos(math.radians(lat_deg)))
    return lat_deg + math.degrees(dlat), lon_deg + math.degrees(dlon)

async def _wait_ready(drone: System, min_sats=6):
    # Home + Global position
    async for h in drone.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            break
        await asyncio.sleep(0.2)
    # GPS sats (ב־SITL זה מהיר)
    async for g in drone.telemetry.gps_info():
        if g.num_satellites >= min_sats:
            break
        await asyncio.sleep(0.2)

async def run(conn_url: str = "udp://:14540",
              alt_agl: float = 30.0,
              length_m: float = 80.0,
              width_m: float = 50.0,
              laps: int = 2,
              orbit_radius_m: float = 20.0,
              orbit_time_s: int = 45,
              cruise_speed_ms: float = 7.0):
    drone = System()
    await drone.connect(system_address=conn_url)
    print(f"[BOX-ORBIT] Connecting to {conn_url} ...")
    await _wait_ready(drone)

    # קבל HOME
    async for hp in drone.telemetry.home():
        home_lat, home_lon, _ = hp.latitude_deg, hp.longitude_deg, hp.absolute_altitude_m
        break

    # משימת המראה לנ.צ. HOME בגובה alt_agl
    items: List[mission.MissionItem] = []
    items.append(mission.MissionItem(
        home_lat, home_lon, alt_agl,
        speed_m_s=cruise_speed_ms, is_fly_through=False,
        gimbal_pitch_deg=float("nan"), gimbal_yaw_deg=float("nan"),
        camera_action=mission.MissionItem.CameraAction.NONE,
        loiter_time_s=0, camera_photo_interval_s=0, acceptance_radius_m=2.0,
        yaw_deg=float("nan")
    ))

    half_len, half_wid = length_m/2.0, width_m/2.0
    corners_ne = [(+half_len, -half_wid), (+half_len, +half_wid), (-half_len, +half_wid), (-half_len, -half_wid)]

    def add_box_once():
        for n,e in corners_ne:
            lat, lon = meters_to_latlon(home_lat, home_lon, n, e)
            items.append(mission.MissionItem(
                lat, lon, alt_agl, speed_m_s=cruise_speed_ms, is_fly_through=True,
                gimbal_pitch_deg=float("nan"), gimbal_yaw_deg=float("nan"),
                camera_action=mission.MissionItem.CameraAction.NONE,
                loiter_time_s=0, camera_photo_interval_s=0, acceptance_radius_m=2.0,
                yaw_deg=float("nan")
            ))

    for _ in range(max(1, int(laps))):
        add_box_once()

    # מרכז המלבן לאורביט
    center_lat, center_lon = meters_to_latlon(home_lat, home_lon, 0, 0)
    items.append(mission.MissionItem(
        center_lat, center_lon, alt_agl,
        speed_m_s=cruise_speed_ms, is_fly_through=False,
        gimbal_pitch_deg=float("nan"), gimbal_yaw_deg=float("nan"),
        camera_action=mission.MissionItem.CameraAction.NONE,
        loiter_time_s=int(orbit_time_s), # זמן השהייה (Loiter)
        camera_photo_interval_s=0, acceptance_radius_m=orbit_radius_m,
        yaw_deg=float("nan")
    ))

    plan = mission.MissionPlan(items)
    await drone.action.set_maximum_speed(cruise_speed_ms)
    await drone.mission.clear_mission()
    await drone.mission.set_return_to_launch_after_mission(True)
    await drone.mission.upload_mission(plan)

    print("[BOX-ORBIT] Arming + starting mission")
    await drone.action.arm()
    await drone.mission.start_mission()

    # המתן לסיום
    async for st in drone.mission.mission_progress():
        print(f"[MISSION] wp {st.current}/{st.total}")
        # RTL אוטומטי לאחר סיום (set_return_to_launch_after_mission=True)
        if st.current == st.total and st.total > 0:
            break
        await asyncio.sleep(0.2)

    # המתן לנחיתה
    while True:
        async for fm in drone.telemetry.flight_mode():
            if fm in (FlightMode.LAND, FlightMode.HOLD):
                return
            break
        await asyncio.sleep(1.0)
