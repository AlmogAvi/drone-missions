import asyncio
from mavsdk import System
from mavsdk.offboard import OffboardError, VelocityNedYaw

PORTS = [14540 + i for i in range(10)]  # ננסה 14540..14549

async def connect_any():
    for p in PORTS:
        d = System()
        try:
            print(f"Connecting to udp://:{p}")
            await d.connect(system_address=f"udp://:{p}")
            async for s in d.core.connection_state():
                if s.is_connected:
                    print(f"Connected on {p}")
                    return d
        except Exception as e:
            print(f"Port {p} failed: {e}")
    raise RuntimeError("No PX4 found on 14540-14549")

async def wait_until_healthy(d):
    print("Waiting for system health…")
    async for h in d.telemetry.health():
        if (h.is_global_position_ok and h.is_home_position_ok and
            h.is_gyrometer_calibration_ok and h.is_accelerometer_calibration_ok):
            print("Health OK")
            break

async def arm_and_takeoff(d, alt=6.0):
    print("Arming…"); await d.action.arm()
    print(f"Takeoff to ~{alt} m…"); await d.action.takeoff()
    await asyncio.sleep(7)

async def start_offboard(d, yaw_deg=0.0):
    # שליחת סט-פוינט ראשוני (נדרש ע״י PX4)
    await d.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, yaw_deg))
    try:
        await d.offboard.start()
    except OffboardError as e:
        print(f"Offboard start failed: {e._result.result}")
        raise

async def stop_offboard(d):
    try:
        await d.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
        await asyncio.sleep(0.8)
        await d.offboard.stop()
    except OffboardError:
        pass

async def fly_square_legs(d, side_m=8.0, speed_ms=1.8, yaw_each_leg=True):
    seg_t = max(0.1, side_m / max(0.2, speed_ms))
    print(f"Square: side={side_m}m, speed={speed_ms}m/s, ~{seg_t:.1f}s per leg")

    # NED velocities: (north=y, east=x, down=z)
    legs = [
        VelocityNedYaw(0.0,  speed_ms, 0.0,   0.0),   # North
        VelocityNedYaw(speed_ms, 0.0, 0.0,  90.0),   # East
        VelocityNedYaw(0.0, -speed_ms, 0.0, 180.0),  # South
        VelocityNedYaw(-speed_ms, 0.0, 0.0, -90.0)   # West
    ]
    for leg in legs:
        if yaw_each_leg:
            # שומרים על yaw תואם לכיוון התנועה
            await d.offboard.set_velocity_ned(leg)
        else:
            # טסים בלי לשנות yaw (0°)
            await d.offboard.set_velocity_ned(
                VelocityNedYaw(leg.north_m_s, leg.east_m_s, leg.down_m_s, 0.0)
            )
        await asyncio.sleep(seg_t)

async def main():
    d = await connect_any()
    await wait_until_healthy(d)
    await arm_and_takeoff(d, alt=6.0)

    # OFFBOARD
    await start_offboard(d, yaw_deg=0.0)

    # ריבוע: צד 8 מ׳, מהירות 1.8 מ׳/ש׳
    await fly_square_legs(d, side_m=800.0, speed_ms=30, yaw_each_leg=True)

    # עצירה וריחוף קצר
    await d.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
    await asyncio.sleep(2.0)

    await stop_offboard(d)

    print("Landing…")
    await d.action.land()
    await asyncio.sleep(7)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
