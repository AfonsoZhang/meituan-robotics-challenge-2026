#!/usr/bin/env bash
# 与 run.sh 相同的环境：ROS Humble + 仿真工作空间（缺工作空间时只 source ROS，终端里 ros2 control 等命令可能不全）
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEMO_ROS_SETUP="${DEMO_ROS_SETUP:-/opt/ros/humble/setup.bash}"
DEMO_WS_SETUP="${AUBO_ROS2_WS:-${HOME}/aubo_ros2_ws}/install/setup.bash"
set +u
[[ -f "$DEMO_ROS_SETUP" ]] && source "$DEMO_ROS_SETUP" || echo "未找到 $DEMO_ROS_SETUP：实时画面不可用" >&2
[[ -f "$DEMO_WS_SETUP" ]] && source "$DEMO_WS_SETUP" || echo "未找到 $DEMO_WS_SETUP" >&2
set -u
exec /usr/bin/python3 "$SCRIPT_DIR/dashboard.py" "$@"
