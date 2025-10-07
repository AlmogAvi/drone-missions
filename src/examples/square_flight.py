import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw

async def arm_and_takeoff(drone, takeoff_alt=5.0):
    print("מחבר ל- PX4…")
    await drone.connect(system_address="udp://:14540")

    print("ממתין לבריאות מערכת…")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok and health.is_gyrometer_calibration_ok:
            break

    print("מקבל מיקום GPS…")
    async for pos in drone.telemetry.position():
        print(f"Home: {pos.latitude_deg:.7f}, {pos.longitude_deg:.7f}")
        break

    print("נשק וממריא…")
    await drone.action.arm()
    await drone.action.takeoff()
    # ממתין להתייצבות בגובה
    await asyncio.sleep(6)

async def fly_square(drone, side_m=5.0, speed_ms=1.0):
    # מתחילים OFFBOARD עם סט-פוינט ראשוני אפס כדי לא לטעות
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print(f"Offboard start failed: {e._result.result}")
        print("מנסה לנתק ולהמשיך…")
        await drone.offboard.stop()
        return

    # כל קטע זמן = מרחק/מהירות
    seg_t = side_m / max(speed_ms, 0.2)

    # צפונה (y+), מזרחה (x+), דרומה (y-), מערבה (x-)
    legs = [
        VelocityNedYaw(0.0,  speed_ms, 0.0, 0.0),   # North
        VelocityNedYaw(speed_ms, 0.0, 0.0, 90.0),   # East
        VelocityNedYaw(0.0, -speed_ms, 0.0, 180.0), # South
        VelocityNedYaw(-speed_ms, 0.0, 0.0, -90.0)  # West
    ]

    for leg in legs:
        await drone.offboard.set_velocity_ned(leg)
        await asyncio.sleep(seg_t)

    # עצירה
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(1.0)
    await drone.offboard.stop()

async def land(drone):
    print("נוחת…")
    await drone.action.land()
    await asyncio.sleep(6)

async def main():
    drone = System()
    await arm_and_takeoff(drone, takeoff_alt=5.0)
    await fly_square(drone, side_m=5.0, speed_ms=1.0)
    await land(drone)

if __name__ == "__main__":
    asyncio.run(main())
