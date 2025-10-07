#!/usr/bin/env bash
# מפעיל N מופעי PX4 SITL עם פורטים מופרדים, תואם MAVSDK/QGC
# שימוש: ./src/swarm/launcher.sh 3
set -e
N=${1:-3}
PX4_DIR="${HOME}/PX4-Autopilot"   # שנה אם צריך
WORLD="jmavsim"                   # או gazebo-classic / gz sim

for i in $(seq 0 $((N-1))); do
  SITL_TCP=$((4560 + i))
  MAVLINK_IN=$((14540 + i))   # MAVSDK יתחבר לכאן
  MAVLINK_OUT=$((14560 + i))  # QGC בד"כ על 14550, נעדכן אם צריך
  echo "[*] Spawning instance $i (tcp:$SITL_TCP, mavsdk:$MAVLINK_IN)"
  (cd "$PX4_DIR" && PX4_SYS_AUTOSTART=4001 PX4_GZ_WORLD=empty \
    make px4_sitl_default $WORLD \
    MAVLINK_URI="udp://127.0.0.1:$MAVLINK_OUT@127.0.0.1:$MAVLINK_IN" \
    HEADLESS=1) &> /tmp/px4_$i.log &
  sleep 2
done

echo "[OK] Spawned $N instances. Open QGC before/after לפי הצורך."
