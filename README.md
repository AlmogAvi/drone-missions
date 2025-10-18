🛰️ Drone Missions – PX4 + MAVSDK

A collection of autonomous flight missions for PX4, powered by Python + MAVSDK,
with built-in telemetry logging and optional video-based target detection (OpenCV).

This repository includes both classic and advanced missions such as
Box Orbit, Lawnmower Search (SAR), Survey, Orbit Rectangle, and more.

⚙️ Requirements
Software

Python 3.10+

PX4 SITL or a real PX4-based drone

QGroundControl (to visualize and monitor the mission)

Gazebo / JMAVSim (for SITL simulation)

Python Packages

Install manually:

pip install mavsdk opencv-python


or via requirements.txt:

pip install -r requirements.txt

📁 Project Structure
drone-missions/
│
├── main.py                     # Main CLI entry point for all missions
│
├── src/
│   ├── missions/
│   │   ├── takeoff_land.py     # Simple takeoff and land
│   │   ├── survey.py           # Grid/survey flight
│   │   ├── orbit_rect.py       # Rectangle-orbit pattern
│   │   ├── square.py           # Simple square pattern
│   │   ├── box_orbit.py        # Box + Loiter mission
│   │   ├── sar_lawnmower.py    # Search-and-Rescue (lawnmower + vision)
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   ├── logger.py           # Telemetry logger (CSV)
│   │   └── __init__.py
│
└── logs/                       # Generated telemetry logs

🚀 How to Run
1️⃣ Start PX4 SITL
cd ~/PX4-Autopilot
make px4_sitl gz_x500

2️⃣ Launch QGroundControl

It will automatically detect the PX4 SITL connection.

3️⃣ Run missions from this repo
Takeoff + Land
python main.py --mission takeoff_land --conn udp://:14540

Survey
python main.py --mission survey --conn udp://:14540

Orbit Rectangle
python main.py --mission orbit_rect --conn udp://:14540

Square
python main.py --mission square --conn udp://:14540

Box Orbit
python main.py --mission box_orbit --conn udp://:14540 `
  --alt 30 --len 80 --wid 50 --laps 2 --orbit_radius 20 --orbit_time 45 --speed 7 `
  --log "logs/box_orbit.csv"

SAR Lawnmower (Search & Rescue with camera)
python main.py --mission sar_lawnmower --conn udp://:14540 `
  --origin_lat 47.397742 --origin_lon 8.545594 --sar_alt 20 `
  --box_w 80 --box_h 60 --lane 15 --video_src 0 --detect_n 5 --sar_speed 6 `
  --log "logs/sar_lawnmower.csv"

📊 Telemetry Logging

You can record full flight telemetry by adding:

--log logs/telemetry.csv


The generated CSV includes:

timestamp | flight_mode | lat | lon | abs_alt | rel_alt | vx | vy | vz | groundspeed | battery%

🧠 Mission Overview
Mission	Description
takeoff_land	Simple autonomous takeoff and safe landing
survey	Grid-style area scanning
orbit_rect	Rectangular orbit around a central point
square	Simple square pattern
box_orbit	Rectangle flight pattern + Loiter (orbit) at center
sar_lawnmower	Search-and-Rescue: lawnmower pattern with camera-based target detection
📡 SAR Lawnmower Flow

Workflow:

Connect to PX4

Arm and take off to target altitude

Fly a lawnmower search pattern (width × height × lane spacing)

Use OpenCV to detect colored targets in the video feed

Pause the mission and perform small offset maneuvers toward the target

Automatically execute Return-To-Launch (RTL)

Save the detected frame (target_*.jpg)

🪪 License

Open-source under the MIT License.
Developed by AlmogAvi
.

💡 Tips (Windows)

Activate your virtual environment before running:

.\.venv\Scripts\Activate.ps1


Create a logs folder (if missing):

New-Item -ItemType Directory -Force -Path .\logs | Out-Null