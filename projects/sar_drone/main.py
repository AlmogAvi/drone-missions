# main.py
import argparse
import asyncio

# --- כל הייבואים הרלוונטיים ---
from src.utils.logger import TelemetryLogger

# משימות בסיסיות מהפרויקט המקורי
from src.missions import takeoff_land, survey, orbit_rect, square

# משימות חדשות
from src.missions import box_orbit
from src.missions import sar_lawnmower


# -----------------------------------------------------
# CLI ARGUMENTS
# -----------------------------------------------------
def build_parser():
    p = argparse.ArgumentParser(description="PX4 Drone Missions CLI")

    p.add_argument("--mission", required=True,
                   choices=[
                       "takeoff_land",
                       "survey",
                       "orbit_rect",
                       "square",
                       "box_orbit",
                       "sar_lawnmower"
                   ],
                   help="Select which mission to run")
    p.add_argument("--conn", default="udp://:14540",
                   help="PX4 connection URL (default: udp://:14540)")
    p.add_argument("--log", default=None,
                   help="Path for CSV telemetry log (optional). Example: logs/out.csv")

    # --- generic ---
    p.add_argument("--alt", type=float, default=20.0, help="Flight altitude (m)")
    p.add_argument("--speed", type=float, default=6.0, help="Cruise speed (m/s)")

    # --- box_orbit params ---
    p.add_argument("--len", dest="length", type=float, default=80.0, help="[box_orbit] Rectangle length (m)")
    p.add_argument("--wid", dest="width", type=float, default=50.0, help="[box_orbit] Rectangle width (m)")
    p.add_argument("--laps", type=int, default=2, help="[box_orbit] Number of loops")
    p.add_argument("--orbit_radius", type=float, default=20.0, help="[box_orbit] Loiter radius (m)")
    p.add_argument("--orbit_time", type=int, default=45, help="[box_orbit] Loiter time (s)")

    # --- sar_lawnmower params ---
    p.add_argument("--origin_lat", type=float, default=47.397742, help="[sar_lawnmower] Origin latitude")
    p.add_argument("--origin_lon", type=float, default=8.545594, help="[sar_lawnmower] Origin longitude")
    p.add_argument("--sar_alt", type=float, default=20.0, help="[sar_lawnmower] Altitude (m)")
    p.add_argument("--box_w", type=float, default=80.0, help="[sar_lawnmower] Search box width (m)")
    p.add_argument("--box_h", type=float, default=60.0, help="[sar_lawnmower] Search box height (m)")
    p.add_argument("--lane", type=float, default=15.0, help="[sar_lawnmower] Lane spacing (m)")
    p.add_argument("--video_src", type=int, default=0, help="[sar_lawnmower] OpenCV video source index")
    p.add_argument("--detect_n", type=int, default=5, help="[sar_lawnmower] Detect every N frames")
    p.add_argument("--sar_speed", type=float, default=6.0, help="[sar_lawnmower] Cruise speed (m/s)")

    return p


# -----------------------------------------------------
# MAIN FUNCTION
# -----------------------------------------------------
async def main():
    args = build_parser().parse_args()

    logger = None
    if args.log:
        logger = TelemetryLogger(args.conn, args.log, hz=2.0)
        print(f"[LOG] Telemetry -> {args.log}")
        await logger.start()

    try:
        # --- classic missions ---
        if args.mission == "takeoff_land":
            await takeoff_land.run(conn_url=args.conn, alt=args.alt)

        elif args.mission == "survey":
            await survey.run(conn_url=args.conn)

        elif args.mission == "orbit_rect":
            await orbit_rect.run(conn_url=args.conn)

        elif args.mission == "square":
            await square.run(conn_url=args.conn)

        # --- new missions ---
        elif args.mission == "box_orbit":
            await box_orbit.run(
                conn_url=args.conn,
                alt_agl=args.alt,
                length_m=args.length,
                width_m=args.width,
                laps=args.laps,
                orbit_radius_m=args.orbit_radius,
                orbit_time_s=args.orbit_time,
                cruise_speed_ms=args.speed,
            )

        elif args.mission == "sar_lawnmower":
            await sar_lawnmower.run(
                conn_url=args.conn,
                origin_lat=args.origin_lat,
                origin_lon=args.origin_lon,
                alt_m=args.sar_alt,
                box_w_m=args.box_w,
                box_h_m=args.box_h,
                lane_m=args.lane,
                video_src=args.video_src,
                detect_every_n_frames=args.detect_n,
                cruise_speed_ms=args.sar_speed,
            )

        else:
            raise SystemExit(f"Unknown mission: {args.mission}")

    finally:
        if logger:
            print("[LOG] Stopping telemetry logger...")
            await logger.stop()


if __name__ == "__main__":
    asyncio.run(main())
