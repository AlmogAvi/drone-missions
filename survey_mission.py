import asyncio
import math
from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)

# === הגדרות בסיסיות ===
ALT_AGL_M = 30.0               # גובה טיסה במטרים
SURVEY_WIDTH_M = 200.0         # רוחב המלבנים (ממזרח למערב) במטרים
SURVEY_HEIGHT_M = 120.0        # גובה המלבנים (מצפון לדרום) במטרים
LINE_SPACING_M = 20.0          # מרווח בין קווים (ככל שקטן – כיסוי צפוף יותר)
CRUISE_SPEED_MS = 8.0          # מהירות שיוט (מ'/ש')
YAW_DEG = 0.0                  # כיוון אף (0 = מזרחה; 90 = צפונה) – נשמר לכל נקודה
TAKEOFF_ALT_M = ALT_AGL_M      # גובה המראה
USE_HOME_AS_CENTER = True      # אם False – הגדר נקודת מרכז ידנית למטה
CENTER_LAT = None              # לדוגמה: 47.3980
CENTER_LON = None              # לדוגמה: 8.5456

# === פונקציות עזר ===
def meters_to_latlon_offset(d_north_m: float, d_east_m: float, ref_lat_deg: float):
    """ ממיר היסט מקומי במטרים (N,E) להיסט ב- lat/lon מעל קו רוחב ref_lat_deg. """
    dlat = d_north_m / 111320.0
    dlon = d_east_m / (111320.0 * math.cos(math.radians(ref_lat_deg)))
    return dlat, dlon

def build_lawnmower_points(center_lat, center_lon, width_m, height_m, spacing_m, start_east_first=True):
    """
    יוצר רשימת נקודות (lat, lon) בדפוס מדשאה מלבני, מרכז סביב center_lat/lon.
    start_east_first=True אומר שקו ראשון הולך מ"–width/2" ל"+width/2" בציר מזרח-מערב.
    """
    points = []
    half_w = width_m / 2.0
    half_h = height_m / 2.0

    # נתקדם שורה-שורה מצפון לדרום (N -> S):
    y = half_h
    left_e = -half_w
    right_e = half_w
    toggle = start_east_first  # לאיזה צד הולכים בשורה הנוכחית

    while y >= -half_h - 1e-6:
        if toggle:
            # משמאל לימין (מערב->מזרח)
            x1, x2 = left_e, right_e
        else:
            # מימין לשמאל (מזרח->מערב)
            x1, x2 = right_e, left_e

        # נקודת התחלה של השורה
        dlat, dlon = meters_to_latlon_offset(y, x1, center_lat)
        points.append((center_lat + dlat, center_lon + dlon))
        # נקודת סוף של השורה
        dlat, dlon = meters_to_latlon_offset(y, x2, center_lat)
        points.append((center_lat + dlat, center_lon + dlon))

        # לשורה הבאה יורדים דרומה ב-spacing
        y -= spacing_m
        toggle = not toggle

    return points

async def wait_until_connected(drone: System):
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"מחובר לרחפן (UUID: {state.uuid})")
            break

async def wait_for_global_position(drone: System):
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("מצב ניווט (GPS/Home) תקין")
            break

async def get_home(drone: System):
    async for hp in drone.telemetry.home():
        return hp

async def run():
    drone = System()
    # אם מריצים מול הרחפן הראשון ב-SITL, זה בדרך כלל 14540
    # לשני: 14541 וכן הלאה.
    await drone.connect(system_address="udp://:14540")

    print("ממתין לחיבור...")
    await wait_until_connected(drone)
    print("בודק GPS/Home...")
    await wait_for_global_position(drone)

    if USE_HOME_AS_CENTER or CENTER_LAT is None or CENTER_LON is None:
        home = await get_home(drone)
        center_lat = home.latitude_deg
        center_lon = home.longitude_deg
        print(f"מרכז הסריקה (Home): {center_lat:.7f}, {center_lon:.7f}")
    else:
        center_lat = CENTER_LAT
        center_lon = CENTER_LON
        print(f"מרכז הסריקה (Custom): {center_lat:.7f}, {center_lon:.7f}")

    # בניית נקודות דפוס מדשאה
    waypoints = build_lawnmower_points(center_lat, center_lon,
                                       SURVEY_WIDTH_M, SURVEY_HEIGHT_M,
                                       LINE_SPACING_M, start_east_first=True)
    print(f"נוצרו {len(waypoints)} נקודות למסלול הסריקה")

    # הכנת משימה: המראה -> נקודות -> RTL
    mission_items = []

    # המראה (PX4 מתייחס ל-takeoff דרך Action 通常; כאן נשתמש בפריט ראשון עם altitude)
    # בפועל אפשר פשוט להתחיל מ־arm/takeoff ואז להתחיל משימה; כאן נשמור משימה "נקייה".
    # נשים פריט ראשון ליד הבית בגובה היעד (כדי לשמור קונטקסט)
    mission_items.append(MissionItem(
        center_lat, center_lon, TAKEOFF_ALT_M,
        speed=CRUISE_SPEED_MS, is_fly_through=True, gimbal_pitch_deg=float('nan'),
        gimbal_yaw_deg=YAW_DEG, camera_action=MissionItem.CameraAction.NONE,
        loiter_time_s=0, camera_photo_interval_s=0, acceptance_radius_m=2.0
    ))

    for (lat, lon) in waypoints:
        mission_items.append(MissionItem(
            lat, lon, ALT_AGL_M,
            speed=CRUISE_SPEED_MS, is_fly_through=True, gimbal_pitch_deg=float('nan'),
            gimbal_yaw_deg=YAW_DEG, camera_action=MissionItem.CameraAction.NONE,
            loiter_time_s=0, camera_photo_interval_s=0, acceptance_radius_m=2.5
        ))

    plan = MissionPlan(mission_items)

    # העלאת משימה
    await drone.mission.clear_mission()
    await drone.mission.set_return_to_launch_after_mission(True)
    await drone.mission.upload_mission(plan)
    print("המשימה הועלתה")

    # Arm + Takeoff (דרך Action)
    print("חימוש וההמראה...")
    await drone.action.arm()
    await drone.action.takeoff()
    await asyncio.sleep(5)

    # התחלת המשימה
    print("מתחיל משימה...")
    await drone.mission.start_mission()

    # המתן לסיום
    async for mission_prog in drone.mission.mission_progress():
        print(f"משימה: {mission_prog.current}/{mission_prog.total}")
        if mission_prog.current == mission_prog.total:
            print("המשימה הסתיימה (RTL אמור להתחיל).")
            break

    # נמתין מעט ל-RTL
    await asyncio.sleep(10)
    print("סיום סקריפט.")

if __name__ == "__main__":
    asyncio.run(run())
