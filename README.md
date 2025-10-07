# 🛩️ Drone Missions – PX4 + MAVSDK Automation

This project provides ready-to-run mission scripts and utilities for autonomous drone control using **PX4 SITL** and **MAVSDK**.  
It allows quick testing, simulation, and extension of flight behaviors such as takeoff, landing, survey patterns, orbits, and square missions – all directly from Python.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/AlmogAvi/drone-missions.git
cd drone-missions

2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt


If requirements.txt doesn’t exist yet, create it manually with:

mavsdk==2.9.0
pandas>=2.2

4. Launch PX4 SITL and QGroundControl

Start PX4 SITL in a terminal (Gazebo or JMAVSim).

Open QGroundControl and confirm connection on port 14540.

🧭 Running Missions

Each mission is defined as an async Python script under src/missions/
You can execute any mission via the unified CLI:

python main.py --mission takeoff_land --conn udp://:14540 --alt 20

Supported missions:
Mission	Description
takeoff_land	Simple takeoff and landing sequence
survey	Grid flight pattern for area scanning
orbit_rect	Orbit path within rectangular area
square	Square flight path demonstration

Example:

python main.py --mission survey --conn udp://:14540 --alt 25 --speed 6

⚙️ Configuration

You can optionally create a .env file (based on .env.example) to store connection defaults:

MAVSDK_CONN=udp://:14540
DEFAULT_ALT=20
DEFAULT_SPEED=5

📁 Project Structure
drone-missions/
│
├── src/
│   └── missions/
│       ├── takeoff_land.py
│       ├── survey.py
│       ├── orbit_rect.py
│       └── square.py
│
├── examples/           # Optional demo scripts
├── scripts/            # Helper scripts (e.g. SITL setup)
├── requirements.txt
├── main.py
├── .env.example
└── README.md

🧩 Example Code Snippet
from mavsdk import System
import asyncio

async def run_takeoff_land(conn_url="udp://:14540", alt=20.0):
    drone = System()
    await drone.connect(system_address=conn_url)
    print(f"Connecting to {conn_url}...")
    await drone.action.arm()
    await drone.action.set_takeoff_altitude(alt)
    await drone.action.takeoff()
    await asyncio.sleep(5)
    await drone.action.land()
    print("Mission complete.")

🧪 Testing
pytest -q


Add your simulation logic tests under tests/.

📸 Optional: Demo in QGroundControl

Open QGroundControl

Run the mission script

Observe telemetry, waypoints, and flight path in real time.

🛠️ Development
Linting & Formatting
pip install ruff black
ruff check .
black src/

Run in Docker (optional)
docker build -t drone-missions .
docker run --rm -it drone-missions

🧑‍💻 Contributing

Pull requests are welcome!
For major changes, please open an issue first to discuss what you would like to change.

Fork the project

Create your feature branch (git checkout -b feature/awesome)

Commit your changes (git commit -m 'Add awesome feature')

Push to the branch (git push origin feature/awesome)

Open a Pull Request

📄 License

This project is licensed under the MIT License — see the LICENSE
 file for details.

Author

Almog Avi
GitHub: @AlmogAvi

✈️ Notes

Works with PX4 SITL (udp://:14540)

Requires Python ≥ 3.10

Tested on Ubuntu 22.04

Designed for learning, testing and mission automation research.
