import asyncio
from mavsdk import System

ALT = 5.0
HOVER_SEC = 5

async def main():
    drone = System(mavsdk_server_address="localhost", port=50051)
    await drone.connect(system_address="udp://:14540")

    print("Waiting for connection...")
    async for s in drone.core.connection_state():
        if s.is_connected:
            print(f"Connected to {s.uuid}")
            break

    print("Arming...")
    await drone.action.arm()

    print(f"Taking off to {ALT} m...")
    await drone.action.set_takeoff_altitude(ALT)
    await drone.action.takeoff()

    await asyncio.sleep(HOVER_SEC)

    print("Landing...")
    await drone.action.land()

    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("Landed.")
            break

if __name__ == "__main__":
    asyncio.run(main())
