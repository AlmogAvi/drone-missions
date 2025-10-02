import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw

PORTS = [14540 + i for i in range(10)]  # נסה 14540..14549 אם היו לך מופעים קודמים

async def connect_any():
    for p in PORTS:
        drone = System()
        try:
            print(f"Connecting to udp://:{p} ...")
            await drone.connect(system_address=f"udp://:{p}")
            async for state in drone.core.connection_state():
                if state.is_connected:
                    print(f"Connected on udp://:{p}")
                    return drone
        except Exception as e:
            print(f"Port {p} failed: {e}")
    raise RuntimeError("Could not connect to any PX4 port 14540-14549")

async def wait_until_healthy(drone):
    print("Waiting for system health...")
    async for h in drone.telemetry.health():
        if (h.is_global_position_ok and h.is_home_position_ok and
            h.is_gyrometer_calibration_ok and h.is_accelerometer_calibration_ok):
            print("Health OK")
            break

async def arm_and_takeoff(drone, alt=5.0):
    print("Arming...")
    await drone.action.arm()
    print(f"Takeoff to ~{alt} m...")
    await drone.action.takeoff()
    await asyncio.sleep(6)

async def fly_forward_and_land(drone, distance_m=10.0, speed_ms=1.5, yaw_deg=0.0):
    # התחלת OFFBOARD עם סט-פוינט אפס
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, yaw_deg))
    try:
        await drone.offboard.start()
    except OffboardError as e:
        print(f"Offboard start failed: {e._result.result}; trying to stop")
        try:
            await drone.offboard.stop()
        except:
            pass
        return

    seg_t = max(0.1, distance_m / max(0.2, speed_ms))
    print(f"Forward {distance_m} m at {speed_ms} m/s (~{seg_t:.1f}s)")
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, speed_ms, 0.0, yaw_deg))  # NED: y+=North
    await asyncio.sleep(seg_t)

    # עצירה ונחיתה
    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, yaw_deg))
    await asyncio.sleep(1.0)
    try:
        await drone.offboard.stop()
    except OffboardError:
        pass

    print("Landing...")
    await drone.action.land()
    await asyncio.sleep(6)
    print("Done.")

async def main():
    drone = await connect_any()
    await wait_until_healthy(drone)
    await arm_and_takeoff(drone, alt=5.0)
    await fly_forward_and_land(drone, distance_m=10.0, speed_ms=1.5, yaw_deg=0.0)

if __name__ == "__main__":
    asyncio.run(main())
