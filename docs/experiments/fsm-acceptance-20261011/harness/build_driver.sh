#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
export CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS=-j2 PYTHONDONTWRITEBYTECODE=1
cd /driver_ws
test "$(git -C src/aubo_ros2_driver rev-parse HEAD)" = 53aab83735236f0c262ecb11e04ef2600241d9d9
test "$(git -C src/aubo_ros2_driver/aubo_description rev-parse HEAD)" = 47fa5e02fa873f27f7e812d31f31e3f4cf5e56b1
cmp src/aubo_ros2_driver/aubo_description/urdf/xacro/inc/aubo.ros2_control.xacro /ws/docs/migration/patches/aubo.ros2_control.xacro.locally_fixed
colcon --log-base /evidence/driver-build build --build-base /driver_work/build --install-base /driver_work/install --executor sequential --packages-select aubo_description aubo_dashboard_msgs aubo_msgs aubo_ros2_driver aubo_moveit_config
