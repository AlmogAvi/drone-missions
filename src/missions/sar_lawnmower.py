# src/missions/sar_lawnmower.py
import asyncio
import math
import cv2
from typing import Tuple
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan
from mission import build_lawnmower         # קיים אצלך
from vision import ColorTargetDetector      # קיים אצלך
from utils import save_frame                # קיים אצלך


async def arm_and_takeoff(drone: System, altitude: float):
    print("[*] Arming...")
    await drone.action.arm()
    print("[*] Taking off...")
    await drone.action.takeoff()
    # המתנה קצרה לייצוב טיפוס
    await asyncio.sleep(5)


def make_mission_plan(waypoints, speed_ms: float = 6.0) -> MissionPlan:
    items = []
    for lat, lon, alt in waypoints:
        items.append(MissionItem(
            latitude_deg=lat, longitude_deg=lon, relative_altitude_m=alt,
            speed_m_s=speed_ms, is_fly_through=True,
            gimbal_pitch_deg=float('nan'), gimbal_yaw_deg=float('nan'),
            camera_action=MissionItem.CameraAction.NONE,
            loiter_time_s=0.0, camera_photo_interval_s=1.0,
            acceptance_radius_m=float('nan'),
            yaw_deg=float('nan'), camera_photo_distance_m=float('nan')
        ))
    return MissionPlan(items)


async def upload_and_start_mission(drone: System, plan: MissionPlan, rtl_after=True):
    await drone.mission.clear_mission()
    await drone.mission.set_return_to_launch_after_mission(bool(rtl_after))
    await drone.mission.upload_mission(plan)
    print("[*] Starting mission...")
    await drone.mission.start_mission()


async def _calc_target_location(drone: System, north_m: float, east_m: float, dalt_m: float) -> Tuple[float, float, float, float]:
    async for pos in drone.telemetry.position():
        lat = pos.latitude_deg
        lon = pos.longitude_deg
        alt = pos.relative_altitude_m
        break
    dlat = north_m / 111_320.0
    dlon = east_m / (111_320.0 * max(0.3, abs(math.cos(math.radians(lat)))))
    return (lat + dlat, lon + dlon, alt + dalt_m, 0.0)


async def goto_offset(drone: System, north_m: float, east_m: float, dalt_m: float = 0.0):
    lat, lon, alt, yaw = await _calc_target_location(drone, north_m, east_m, dalt_m)
    await drone.action.goto_location(lat, lon, alt, yaw)


def image_to_body_offsets(bbox, frame_shape, fov_deg=78.0, gain=0.5):
    """המרת מיקום מטרה בתמונה להיסטים בקואורדינטות הגוף (קדימה/ימינה)."""
    x, y, w, h = bbox
    H, W = frame_shape[:2]
    cx, cy = x + w/2, y + h/2
    dx = (cx - W/2) / (W/2)  # [-1,1]
    dy = (cy - H/2) / (H/2)

    rad_per_pix = math.radians(fov_deg) / W
    yaw_rad   = dx * rad_per_pix * W
    pitch_rad = dy * rad_per_pix * W

    forward_m = -pitch_rad * gain * 5.0
    right_m   =  yaw_rad   * gain * 5.0
    return forward_m, right_m


async def run(conn_url: str = "udp://:14540",
              origin_lat: float = 47.397742,
              origin_lon: float = 8.545594,
              alt_m: float = 20.0,
              box_w_m: float = 80.0,
              box_h_m: float = 60.0,
              lane_m: float = 15.0,
              video_src: int = 0,
              detect_every_n_frames: int = 5,
              cruise_speed_ms: float = 6.0):
    """
    משימת SAR:
    1) המראה
    2) טיסת Lawnmower על אזור (origin/box/lane)
    3) זיהוי מטרה מהווידיאו, Pause, גישות קטנות לכיוון המטרה
    4) RTL
    """
    drone = System()
    await drone.connect(system_address=conn_url)
    print(f"[*] Connecting to {conn_url} ...")

    # המתנה לחיבור
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[*] Connected to PX4.")
            break

    # בריאות/GPS/Home
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("[*] Global position OK (home & gps).")
            break
        await asyncio.sleep(0.2)

    # המראה
    await arm_and_takeoff(drone, alt_m)

    # בניית מסלול Lawnmower
    wps  = build_lawnmower(origin_lat, origin_lon, alt_m, box_w_m, box_h_m, lane_m)
    plan = make_mission_plan(wps, speed_ms=cruise_speed_ms)
    await upload_and_start_mission(drone, plan, rtl_after=True)

    # וידאו + דטקטור
    cap = cv2.VideoCapture(video_src)
    detector = ColorTargetDetector()
    frame_count = 0
    target_found = False

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                await asyncio.sleep(0.05)
                continue
            frame_count += 1

            # זיהוי מטרה כל N פריימים
            if frame_count % max(1, int(detect_every_n_frames)) == 0:
                bbox = detector.detect(frame)
                if bbox is not None and not target_found:
                    target_found = True
                    print("[!] Target detected — approach & loiter...")
                    path = save_frame(frame, prefix="target")
                    print(f"[*] Saved frame: {path}")

                    # עצירת המשימה וגישות קטנות לכיוון המטרה
                    await drone.mission.pause_mission()

                    for _ in range(8):
                        # בדיקה חוזרת (Fail-fast אם איבדנו מטרה)
                        bbox = detector.detect(frame)
                        if bbox is None:
                            break
                        fwd, right = image_to_body_offsets(bbox, frame.shape)
                        await goto_offset(drone, north_m=fwd, east_m=right, dalt_m=0.0)
                        await asyncio.sleep(1.0)

                    print("[*] RTL...")
                    await drone.action.return_to_launch()
                    break

            # תצוגה למסך
            cv2.imshow("SAR-Drone feed", frame)
            # ESC
            if cv2.waitKey(1) & 0xFF == 27:
                print("[*] ESC pressed, aborting...")
                await drone.action.return_to_launch()
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
