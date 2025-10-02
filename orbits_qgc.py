# הוסף לראש הקובץ:
from mavsdk.mission import MissionItem, MissionPlan

# הוסף פונקציה אחרי build_grid_centers:
def centers_to_mission_items(centers, alt_m, speed_ms=8.0, yaw_deg=float('nan')):
    items = []
    for (lat, lon) in centers:
        items.append(MissionItem(
            lat, lon, alt_m,
            speed=speed_ms,
            is_fly_through=True,
            gimbal_pitch_deg=float('nan'),
            gimbal_yaw_deg=yaw_deg,
            camera_action=MissionItem.CameraAction.NONE,
            loiter_time_s=0,
            camera_photo_interval_s=0,
            acceptance_radius_m=2.0
        ))
    return items

# בתוך run(), ממש לפני ההמראה:
    # בניית רשת מרכזי אורביטים
    centers = build_grid_centers(center_lat, center_lon,
                                 RECT_WIDTH_M, RECT_HEIGHT_M, GRID_SPACING_M,
                                 serpentine=True)
    print(f"נוצרו {len(centers)} מרכזי אורביט")

    # === חדש: העלאת "משימת תצוגה" ל-QGC ===
    try:
        await drone.mission.clear_mission()
        display_items = centers_to_mission_items(centers, ALTITUDE_M)
        plan = MissionPlan(display_items)
        await drone.mission.set_return_to_launch_after_mission(False)
        await drone.mission.upload_mission(plan)
        print("הועלתה משימת תצוגה ל-QGC (לא נריץ אותה).")
    except Exception as e:
        print(f"לא הצלחתי להעלות משימת תצוגה: {e}")

# ואז המשך כמו בקוד המקורי: המראה → goto לכל מרכז → Offboard orbit → RTL

