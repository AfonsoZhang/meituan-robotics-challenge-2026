#!/usr/bin/env bash
# NUC 实机环境：装 realsense-ros、MoveIt、ros2_control，克隆锁定提交的 aubo_ros2_driver 并构建驱动与 MoveIt 配置。
# 前提：原生 Ubuntu 22.04，已按 ROS 官方文档装好 ros-humble-desktop（本脚本不改 apt 源）。
# 需要 sudo（apt）和外网：aubo_ros2_driver 构建时从 download.aubo-robotics.cn 下载二进制 aubo_sdk。
# 工作空间已存在且提交不符时停止，不 reset、不删除。
set -euo pipefail
ROBOT_WS="${AUBO_ROS2_WS:-${HOME}/aubo_ros2_ws}"
ROBOT_ROS_SETUP="${ROBOT_ROS_SETUP:-/opt/ros/humble/setup.bash}"
DRIVER_URL="${AUBO_DRIVER_REPOSITORY:-https://github.com/AuboRobot/aubo_ros2_driver.git}"
DRIVER_COMMIT=85684075d6ff06c5385e39611208e99ebf0f94c6       # 仿真工作空间用的同一提交
DESCRIPTION_COMMIT=47fa5e02fa873f27f7e812d31f31e3f4cf5e56b1  # 其 submodule aubo_description

. /etc/os-release
[[ "$VERSION_ID" == "22.04" ]] || { echo "需要 Ubuntu 22.04，当前 $VERSION_ID" >&2; exit 1; }
if grep -qi microsoft /proc/version; then echo "这是 WSL；实机环境应在 NUC 原生 Ubuntu 上" >&2; exit 1; fi
[[ -f "$ROBOT_ROS_SETUP" ]] || { echo "未找到 $ROBOT_ROS_SETUP：先按 ROS 官方文档安装 ros-humble-desktop" >&2; exit 1; }

sudo apt-get update
sudo apt-get install -y python3-colcon-common-extensions python3-rosdep git \
  ros-humble-realsense2-camera ros-humble-moveit ros-humble-ros2-control ros-humble-ros2-controllers \
  ros-humble-controller-manager-msgs ros-humble-control-msgs
[[ -f /etc/ros/rosdep/sources.list.d/20-default.list ]] || sudo rosdep init
rosdep update

set +u; source "$ROBOT_ROS_SETUP"; set -u
mkdir -p "$ROBOT_WS/src"
DRIVER_DIR="$ROBOT_WS/src/aubo_ros2_driver"
if [[ ! -e "$DRIVER_DIR" ]]; then
  git clone --no-checkout "$DRIVER_URL" "$DRIVER_DIR"
  git -C "$DRIVER_DIR" checkout --detach "$DRIVER_COMMIT"
  git -C "$DRIVER_DIR" submodule update --init --recursive
fi
[[ "$(git -C "$DRIVER_DIR" rev-parse HEAD)" == "$DRIVER_COMMIT" ]] || { echo "现有 aubo_ros2_driver 不在锁定提交；换一个新的 AUBO_ROS2_WS" >&2; exit 1; }
[[ "$(git -C "$DRIVER_DIR/aubo_description" rev-parse HEAD)" == "$DESCRIPTION_COMMIT" ]] || { echo "aubo_description submodule 提交不符" >&2; exit 1; }
# 仿真工作空间曾给驱动包加 COLCON_IGNORE；实机要构建它，发现就停下让人确认
if [[ -e "$DRIVER_DIR/aubo_ros2_driver/COLCON_IGNORE" ]]; then
  echo "$DRIVER_DIR/aubo_ros2_driver/COLCON_IGNORE 存在（仿真工作空间的做法）。实机请用新的 AUBO_ROS2_WS。" >&2; exit 1
fi

PKGS=(aubo_description aubo_msgs aubo_dashboard_msgs aubo_ros2_driver aubo_moveit_config)
rosdep install -y --rosdistro humble --ignore-src --from-paths "${PKGS[@]/#/$DRIVER_DIR/}" \
  --skip-keys "docker.io warehouse_ros_mongo"
cd "$ROBOT_WS"
# ros_joints_plan 依赖 ROS 1、aubo_gazebo 依赖 Gazebo，实机不需要，只构建所需包
colcon build --packages-up-to aubo_ros2_driver aubo_moveit_config --cmake-args -DCMAKE_BUILD_TYPE=Release
echo "构建完成：$ROBOT_WS"
echo "下一步：source $ROBOT_WS/install/setup.bash && python3 $(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/bringup_check.py env --robot-ip <控制柜 IP>"
