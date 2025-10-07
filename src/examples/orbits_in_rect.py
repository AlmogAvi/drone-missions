# orbits_in_rect.py
# דרישות: pip install mavsdk
import asyncio, math
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw

# ========= פרמטרים כלליים =========
ALTITUDE_M = 30.0            # גובה טיסה AGL
TAKEOFF_WAIT_S = 5

# תא שטח מלבני (מטרים) סביב מרכז (ברירת מחדל: Home)
RECT_WIDTH_M  = 200.0        # מזרח-מערב (X)
RECT_HEIGHT_M = 140.0        # צפון-דרום (Y)
GRID_SPACING_M = 80.0        # מרחק בין מרכזי האורביטים

# אורביט
ORBIT_RADIUS_M = 25.0
ORBIT_SPEED_MS = 6.0         # מהירות משיקית
ORBIT_TURNS    = 1.5         # כמה סיבובים בכל נקודה
YAW_FACES_TANGENT = False    # אם True – האף ינוע עם המעגל; אם False – כיוון קבוע

# חיבור לסימולציה
SYSTEM_ADDRESS = "udp://:14540"  # נסה גם "udp://:14540" אם צריך

# ========== עזר גיאו ==========

def meters_to_latlon_offset(d_north_m: float, d_east_m: float, ref_lat_deg: float):
    dlat = d_north_m / 111320.0
    dlon = d_east_m / (111320.0 * math.cos(math.radians(ref_lat_deg)))
    return dlat, dlon

def build_grid_centers(center_lat, center_lon, width_m, height_m, spacing_m, serpentine=True):
    """יוצר רשימת מרכזי אורביט בתוך מלבן, מסודר בשורות (צפון->דרום).
       serpentine=True ימזער טיסות סרק בין נקודות."""
    half_w, half_h = width_m/2.0, height_m/2.0
    ys = []
    y = half_h
    while y >= -half_h - 1e-6:
        ys.append(y)
        y -= spacing_m
    xs = []
    x = -half_w
    while x <= half_w + 1e-6:
        xs.append(x)
        x += spacing_m

    points = []
    left_to_right = True
    for idx, y in enumerate(ys):
        row_xs = xs if (left_to_right or not serpentine) else list(reversed(xs))
        for x in row_xs:
            dlat, dlon = meters_to_latlon_offset(y, x, center_lat)
            points.append((center_lat + dlat, center_lon + dlon))
        left_to_right = not left_to_right
    return points

# ========== תפעול רחפן ==========

async def wait_connected(drone: System):
    async for st in drone.core.connection_state():
        if st.is_connected:
            print("✅ מחובר לרחפן")
            break

async def wait_gps(drone: System):
    async for h in drone.telemetry.health():
        if h.is_global_position_ok and h.is_home_position_ok:
            print("✅ GPS/Home תקין")
            break

async def get_home(drone: System):
    async for hp in drone.telemetry.home():
        return hp

async def goto(drone: System, lat, lon, alt, yaw_deg=math.nan):
    await drone.action.goto_location(lat, lon, alt, yaw_deg)

async def arm_and_takeoff(drone: System, alt):
    await drone.action.set_takeoff_altitude(alt)
    print("חימוש...")
    await drone.action.arm()
    print("המראה...")
    await drone.action.takeoff()
    await asyncio.sleep(TAKEOFF_WAIT_S)

async def do_orbit_offboard(drone: System, radius_m, speed_ms, turns=1.0,
                            yaw_faces_tangent=False, loop_dt=0.05):
    """
    מבצע אורביט ע"י שליחת מהירויות NED ב-Offboard.
    """
    # התחלת Offboard מחייבת סט-פוינט ראשון
    try:
        await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
        await drone.offboard.start()
    except OffboardError as e:
        print(f"❌ Offboard start failed: {e._result.result}")
        return

    try:
        omega = speed_ms / radius_m  # rad/s
        total_time = (2 * math.pi * turns) / omega
        t = 0.0
        while t < total_time:
            vx = -speed_ms * math.sin(omega * t)
            vy =  speed_ms * math.cos(omega * t)
            if yaw_faces_tangent:
                yaw_deg = (math.degrees(omega * t) + 90.0) % 360.0
            else:
                yaw_deg = 0.0
            await drone.offboard.set_velocity_ned(VelocityNedYaw(vx, vy, 0.0, yaw_deg))
            await asyncio.sleep(loop_dt)
            t += loop_dt
    finally:
        try:
            await drone.offboard.stop()
        except OffboardError:
            pass

async def run():
    drone = System()
    await drone.connect(system_address=SYSTEM_ADDRESS)
    print("ממתין לחיבור...")
    await wait_connected(drone)
    print("בודק GPS/Home...")
    await wait_gps(drone)

    home = await get_home(drone)
    center_lat, center_lon = home.latitude_deg, home.longitude_deg
    print(f"מרכז המלבני (Home): {center_lat:.7f}, {center_lon:.7f}")

    # בניית רשת מרכזי אורביטים
    centers = build_grid_centers(center_lat, center_lon,
                                 RECT_WIDTH_M, RECT_HEIGHT_M, GRID_SPACING_M,
                                 serpentine=True)
    print(f"נוצרו {len(centers)} מרכזי אורביט")

    # המראה
    await arm_and_takeoff(drone, ALTITUDE_M)

    # מעבר בין מרכזים וביצוע אורביט
    for i, (lat, lon) in enumerate(centers, 1):
        print(f"→ נקודה {i}/{len(centers)}")
        await goto(drone, lat, lon, ALTITUDE_M, math.nan)
        # זמן הגעה משוער (שקט): תן שניות ספורות (תלוי מרחק)
        await asyncio.sleep(3)
        print("   מבצע Orbit...")
        await do_orbit_offboard(drone,
                                radius_m=ORBIT_RADIUS_M,
                                speed_ms=ORBIT_SPEED_MS,
                                turns=ORBIT_TURNS,
                                yaw_faces_tangent=YAW_FACES_TANGENT)

    print("חוזר לנקודת הבית (RTL)...")
    await drone.action.return_to_launch()
    await asyncio.sleep(5)
    print("סיום.")

if __name__ == "__main__":
    asyncio.run(run())
