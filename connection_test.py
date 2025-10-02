import asyncio
from mavsdk import System

async def run():
    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("ממתין לחיבור...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("מחובר לרחפן ✅")
            break

asyncio.run(run())
