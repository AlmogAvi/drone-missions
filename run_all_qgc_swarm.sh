#!/usr/bin/env bash
# run_all_qgc_swarm.sh
# Usage: ./run_all_qgc_swarm.sh [NUM_INSTANCES] [QGC_PATH_OR_APPIMAGE]
# Example: ./run_all_qgc_swarm.sh 3 ~/Applications/QGroundControl.AppImage

set -euo pipefail
NUM=${1:-3}
QGC_PATH=${2:-""}
PROJECT_DIR="${HOME}/drone-missions"
LAUNCHER="${PROJECT_DIR}/src/swarm/launcher.sh"
FORMATION_MODULE="src/swarm/formation_v.py"

# 1) Check launcher exists
if [ ! -x "${LAUNCHER}" ]; then
  echo "Error: launcher not found or not executable: ${LAUNCHER}"
  echo "Make sure you created src/swarm/launcher.sh and ran: chmod +x src/swarm/launcher.sh"
  exit 1
fi

# 2) Find QGroundControl executable / AppImage
start_qgc() {
  if [ -n "${QGC_PATH}" ] && [ -x "${QGC_PATH}" ]; then
    echo "[+] Launching QGroundControl from: ${QGC_PATH}"
    nohup "${QGC_PATH}" >/tmp/qgc.log 2>&1 &
    return 0
  fi

  # try qgroundcontrol in PATH
  if command -v QGroundControl >/dev/null 2>&1; then
    echo "[+] Launching QGroundControl (command: QGroundControl)"
    nohup QGroundControl >/tmp/qgc.log 2>&1 &
    return 0
  fi
  if command -v qgroundcontrol >/dev/null 2>&1; then
    echo "[+] Launching QGroundControl (command: qgroundcontrol)"
    nohup qgroundcontrol >/tmp/qgc.log 2>&1 &
    return 0
  fi

  # common AppImage location
  if [ -x "${HOME}/Applications/QGroundControl.AppImage" ]; then
    echo "[+] Launching QGroundControl AppImage"
    nohup "${HOME}/Applications/QGroundControl.AppImage" >/tmp/qgc.log 2>&1 &
    return 0
  fi

  echo "Warning: QGroundControl not found in PATH or at ${HOME}/Applications/QGroundControl.AppImage."
  echo "If you want the script to launch QGC automatically, re-run with path to the AppImage or executable:"
  echo "  ./run_all_qgc_swarm.sh ${NUM} /path/to/QGroundControl.AppImage"
  return 1
}

# 3) Start QGC (best-effort)
start_qgc || echo "[!] Continuing without automatically launching QGC. Please open QGroundControl manually."

# small sleep so QGC GUI has time to start
echo "[*] Waiting 5s for QGC to start..."
sleep 5

# 4) Launch SITL instances
echo "[*] Launching ${NUM} PX4 SITL instances..."
"${LAUNCHER}" "${NUM}"

# Wait a bit for SITL instances to initialize and bind ports
echo "[*] Waiting 8s for SITL instances to initialize..."
sleep 8

# 5) Run formation script
if [ ! -f "${PROJECT_DIR}/${FORMATION_MODULE}" ]; then
  echo "Error: formation script not found: ${PROJECT_DIR}/${FORMATION_MODULE}"
  exit 1
fi

echo "[*] Starting formation script (swarm)..."
# run in a new terminal window (if available) or background
if command -v gnome-terminal >/dev/null 2>&1; then
  gnome-terminal -- bash -ic "cd ${PROJECT_DIR} && python3 -u ${FORMATION_MODULE}; echo 'formation_v finished'; exec bash" &
elif command -v xterm >/dev/null 2>&1; then
  xterm -e "cd ${PROJECT_DIR} && python3 -u ${FORMATION_MODULE}" &
else
  # fallback: run in background (logs to file)
  nohup bash -c "cd ${PROJECT_DIR} && python3 -u ${FORMATION_MODULE}" >/tmp/formation.log 2>&1 &
  echo "[*] formation_v running in background. Logs: /tmp/formation.log"
fi

echo "[OK] All started. Open QGC, select multiple vehicles and watch the swarm."
