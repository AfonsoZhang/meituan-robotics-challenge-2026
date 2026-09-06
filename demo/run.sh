#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
set +u
source /opt/ros/humble/setup.bash
source /home/afonso/aubo_ros2_ws/install/setup.bash
set -u
exec /usr/bin/python3 "$SCRIPT_DIR/record.py" "$@"
