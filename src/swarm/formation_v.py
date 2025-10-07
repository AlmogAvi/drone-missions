import asyncio, math
from dataclasses import dataclass
from typing import List, Tuple
from mavsdk import System
import numpy as np

@dataclass
class AgentCfg:
    conn: str
    offset_ned: Tuple[float, float, float]  # (N,E,D) יחסית למנהיג

TAKEOFF_ALT = 20.0
CRUISE_SPEED = 8.0
STEP_HZ = 10.0

async def connect(conn: str) -> System:
    d = System()
    await d.connect(system_address=conn)
    async for s in d.core.connection_state():
        if s.is_connected:
            print(f"[+] Connected {conn}")
            break
    return d

async def arm_takeoff(drone: System, alt=TAKEOFF_ALT):
    print("[ACTION] arm & takeoff")
    await drone.action.arm()
    await drone.action.set_maximum_speed(CRUISE_SPEED)
    await drone.action.takeoff()
    await asyncio.sleep(5)

async def goto_rel(drone: System, n: float, e: float, d_alt: float):
    # שליחת setpoint מהירות לכיוון היעד (פשטני אך יעיל בסימולציה)
    # אפשר לשדרג ל-offboard position בפועל.
    await drone.action.goto_location_relative(n, e, d_alt, 0.0)

async def leader_patrol(drone: System, radius_m=60.0):
    # מסלול מעגלי איטי – המנהיג "מסייר"
    t = 0.0
    while True:
        n = radius_m * math.sin(t)
        e = radius_m * math.cos(t)
        await goto_rel(drone, n, e, TAKEOFF_ALT)
        await asyncio.sleep(1.0/STEP_HZ)
        t += 0.03

async def follower_track(drone: System, leader: System, offset_ned: Tuple[float,float,float]):
    # עוקב אחרי המנהיג עם היסט NED קבועה (Virtual Structure פשוט)
    on, oe, od = offset_ned
    async for lp in leader.telemetry.position_velocity_ned():
        # NED של המנהיג יחסית ל-home (בקירוב)
        n = -lp.velocity.down_m_s * 0.0  # לא מדויק – נעדכן למצב אמיתי אם נרצה
        # במקום לזה, ניקח את מיקום ה-GPS היחסי (פשטני בסיממס):
        # לשם הדוגמה, נחשב מיקום יחסי מעגלי כמו בפונקציית leader.
        # בפועל: קרא position() של המנהיג ושמור origin להמרה ל-NED.
        # כאן נשמור קירוב: נעביר את היסט ה-offset כפקודת goto יחסית.
        await goto_rel(drone, on, oe, TAKEOFF_ALT)  # "דבוק" למנהיג
        await asyncio.sleep(1.0/STEP_HZ)

async def main():
    # שלושה כלים: מנהיג + שני עוקבים בצורת V
    cfgs = [
        AgentCfg("udp://:14540", (0.0,   0.0,   0.0)),   # leader
        AgentCfg("udp://:14541", (-15.0, -10.0, 0.0)),   # left wing
        AgentCfg("udp://:14542", (-15.0, +10.0, 0.0)),   # right wing
    ]
    drones: List[System] = [await connect(c.conn) for c in cfgs]

    # המראה לכולם (אפשר בטור כדי להימנע מעומס)
    for d in drones:
        await arm_takeoff(d, TAKEOFF_ALT)

    leader = drones[0]
    tasks = [asyncio.create_task(leader_patrol(leader))]
    for d, c in zip(drones[1:], cfgs[1:]):
        tasks.append(asyncio.create_task(follower_track(d, leader, c.offset_ned)))

    # לרוץ עד Ctrl+C
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass
    finally:
        for d in drones:
            try:
                await d.action.return_to_launch()
            except: pass

if __name__ == "__main__":
    asyncio.run(main())
