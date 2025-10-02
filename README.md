# Drone Missions (PX4 SITL + MAVSDK + QGC)
![CI](https://github.com/AlmogAvi/drone-missions/actions/workflows/python-ci.yml/badge.svg)


Minimal Python missions for drones (PX4 SITL or real hardware) using **MAVSDK**.
Includes: arm/takeoff/land, rectangular survey (“lawnmower”), square flights, and orbit patterns.
Tested with **QGroundControl** (UDP).

## Quick Start
```bash
# Python deps
pip install -r requirements.txt

# (Optional) GeographicLib datasets for PX4 estimators, if needed:
bash install_geographiclib_datasets.sh
Run examples
bash
Copy code
# 1) Simple takeoff & land
python takeoff_land.py

# 2) Survey mission (lawnmower pattern)
python survey_mission.py

# 3) Orbits along rectangle corners (QGC shows the path)
python orbits_in_rect.py
Default connection is typically udp://:14540 for MAVSDK and udp://:14550 for QGC.
Open QGroundControl first, then start PX4 SITL (JMAVSim/Gazebo), then run a script.

Repo Structure
takeoff_land.py – arm → takeoff → land

survey_mission.py – rectangular survey using waypoint mission

orbits_in_rect.py / orbits.py – orbit patterns

square_flight.py / fly_square.py – square paths

connection_test.py – sanity check connection

install_geographiclib_datasets.sh – helper for GeographicLib data

Safety
SITL only unless you know what you’re doing. Verify geofence, GPS, and failsafes.

License
MIT (add a LICENSE file if you wish)

yaml
Copy code

---

## 3) requirements.txt
```txt
mavsdk==2.9.0
pandas>=2.2
