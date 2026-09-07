#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEMO_ROS_SETUP="${DEMO_ROS_SETUP:-/opt/ros/humble/setup.bash}"
DEMO_WS_SETUP="${AUBO_ROS2_WS:-${HOME}/aubo_ros2_ws}/install/setup.bash"
if [[ ! -f "$DEMO_ROS_SETUP" || ! -f "$DEMO_WS_SETUP" ]]; then
  echo "Missing ROS or workspace setup: $DEMO_ROS_SETUP / $DEMO_WS_SETUP" >&2
  echo "See demo/SETUP.md; set AUBO_ROS2_WS to the built workspace." >&2
  exit 1
fi
set +u
source "$DEMO_ROS_SETUP"
source "$DEMO_WS_SETUP"
set -u
exec /usr/bin/python3 "$SCRIPT_DIR/record.py" "$@"
