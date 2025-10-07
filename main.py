#!/usr/bin/env python3
# main.py
import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# --- הוספת ./src ל-PYTHONPATH כדי לאפשר imports כמו missions.takeoff_land ---
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# --- ייבוא פונקציות המשימות ---
# ודא שיש קבצים תואמים ב-src/missions/: takeoff_land.py, survey.py, orbit_rect.py, square.py
from missions.takeoff_land import run_takeoff_land
from missions.survey import run_survey
from missions.orbit_rect import run_orbit_rect
from missions.square import run_square


def setup_logging():
    """
    קונפיגורציית לוגים אחידה למסך + (אופציונלית) לקובץ.
    שלוט ברמת הלוג דרך משתנה סביבה LOG_LEVEL=DEBUG/INFO/WARNING/ERROR.
    אפשר גם LOG_FILE=drone.log כדי לכתוב לקובץ.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handlers = [logging.StreamHandler()]
    log_file = os.getenv("LOG_FILE")
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )

    # קצת שקט מספריות חיצוניות רועשות (אם תרצה)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="PX4/MAVSDK Missions CLI (takeoff, survey, orbit, square)"
    )
    p.add_argument(
        "--conn",
        default=os.getenv("MAVSDK_CONN", "udp://:14540"),
        help="MAVSDK connection URL (e.g. udp://:14540, tcp://127.0.0.1:5760)",
    )
    p.add_argument(
        "--mission",
        required=True,
        choices=["takeoff_land", "survey", "orbit_rect", "square"],
        help="Which mission to run",
    )
    p.add_argument("--alt", type=float, default=float(os.getenv("DEFAULT_ALT", 20.0)),
                   help="Altitude in meters (default: 20)")
    p.add_argument("--speed", type=float, default=float(os.getenv("DEFAULT_SPEED", 5.0)),
                   help="Speed in m/s where applicable (default: 5)")
    # פרמטרים ייעודיים למשימות מסוימות? תוכל להוסיף כאן דגלים ייחודיים
    return p


async def run_selected_mission(args):
    log = logging.getLogger("main")
    log.info("Selected mission: %s", args.mission)
    log.info("Connection: %s | Alt: %.2f | Speed: %.2f", args.conn, args.alt, args.speed)

    if args.mission == "takeoff_land":
        await run_takeoff_land(args.conn, args.alt)
    elif args.mission == "survey":
        await run_survey(args.conn, args.alt, args.speed)
    elif args.mission == "orbit_rect":
        await run_orbit_rect(args.conn, args.alt, args.speed)
    elif args.mission == "square":
        await run_square(args.conn, args.alt, args.speed)
    else:
        log.error("Unknown mission: %s", args.mission)


async def main_async():
    parser = build_parser()
    args = parser.parse_args()
    await run_selected_mission(args)


def main():
    setup_logging()
    log = logging.getLogger("main")

    try:
        asyncio.run(main_async())
        log.info("Mission finished successfully.")
    except KeyboardInterrupt:
        log.warning("Interrupted by user (Ctrl+C). Landing/cleanup may be required.")
    except Exception as e:
        log.exception("Unhandled error: %s", e)
        # כאן אפשר להוסיף טיפול-שחזור/ניסיון נחיתה אם רלוונטי


if __name__ == "__main__":
    main()

