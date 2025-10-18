# src/utils/logger.py
import asyncio
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from mavsdk import System
from mavsdk.telemetry import FlightMode


class TelemetryLogger:
    """
    לוג טלמטריה ל-CSV. מתחבר בנפרד ל-system_address שקיבלת.
    שימוש:
        logger = TelemetryLogger(conn_url, "out.csv")
        await logger.start()
        ...
        await logger.stop()
    """
    def __init__(self, conn_url: str, csv_path: str, hz: float = 2.0):
        self._conn_url = conn_url
        self._csv_path = Path(csv_path)
        self._hz = max(0.2, float(hz))
        self._drone: Optional[System] = None
        self._task: Optional[asyncio.Task] = None
        self._stop_evt = asyncio.Event()

        # header
        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._csv_path.exists():
            with self._csv_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow([
                    "ts_iso", "flight_mode",
                    "lat_deg", "lon_deg", "abs_alt_m", "rel_alt_m",
                    "vx_ms", "vy_ms", "vz_ms",
                    "ground_speed_ms",
                    "battery_percent"
                ])

    async def start(self):
        self._drone = System()
        await self._drone.connect(system_address=self._conn_url)
        # המתנה קצרה להתחברות
        async for _ in self._drone.telemetry.flight_mode():
            break
        self._stop_evt.clear()
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._stop_evt.set()
        if self._task:
            await self._task
        # ניתוק לא חובה; MAVSDK ייסגר כשיתום

    async def _run(self):
        assert self._drone is not None
        # streams
        flight_mode_stream = self._drone.telemetry.flight_mode()
        pos_stream = self._drone.telemetry.position()
        vel_stream = self._drone.telemetry.velocity_ned()
        groundspeed_stream = self._drone.telemetry.ground_speed_ned()
        batt_stream = self._drone.telemetry.battery()

        # ערכים אחרונים
        fm = None
        pos = None
        vel = None
        gs = None
        batt = None

        # קוראים את כל הזרמים בקצב אחיד
        period = 1.0 / self._hz
        while not self._stop_evt.is_set():
            # נסה “לרוקן” כל זרם אם יש דגימה ממתינה
            try:
                fm = await asyncio.wait_for(flight_mode_stream.__anext__(), timeout=0.0)
            except asyncio.TimeoutError:
                pass
            try:
                pos = await asyncio.wait_for(pos_stream.__anext__(), timeout=0.0)
            except asyncio.TimeoutError:
                pass
            try:
                vel = await asyncio.wait_for(vel_stream.__anext__(), timeout=0.0)
            except asyncio.TimeoutError:
                pass
            try:
                gs = await asyncio.wait_for(groundspeed_stream.__anext__(), timeout=0.0)
            except asyncio.TimeoutError:
                pass
            try:
                batt = await asyncio.wait_for(batt_stream.__anext__(), timeout=0.0)
            except asyncio.TimeoutError:
                pass

            # כתיבה לשורה
            with self._csv_path.open("a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                ts = datetime.now(timezone.utc).isoformat()
                mode_name = fm.name if isinstance(fm, FlightMode) else str(fm) if fm else ""
                lat = getattr(pos, "latitude_deg", None) if pos else None
                lon = getattr(pos, "longitude_deg", None) if pos else None
                abs_alt = getattr(pos, "absolute_altitude_m", None) if pos else None
                rel_alt = getattr(pos, "relative_altitude_m", None) if pos else None
                vx = getattr(vel, "north_m_s", None) if vel else None
                vy = getattr(vel, "east_m_s", None) if vel else None
                vz = getattr(vel, "down_m_s", None) if vel else None
                gs_ms = None
                if gs:
                    # ground_speed_ned מחזיר וקטור; אפשר נורמה
                    try:
                        gs_ms = (gs.north_m_s**2 + gs.east_m_s**2 + gs.down_m_s**2) ** 0.5
                    except Exception:
                        gs_ms = None
                batt_pct = getattr(batt, "remaining_percent", None) if batt else None

                w.writerow([ts, mode_name, lat, lon, abs_alt, rel_alt, vx, vy, vz, gs_ms, batt_pct])

            await asyncio.sleep(period)
