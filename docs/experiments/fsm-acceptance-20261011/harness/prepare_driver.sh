#!/usr/bin/env bash
set -eo pipefail
export DEBIAN_FRONTEND=noninteractive
# Minimal independent Fake driver scope; MoveIt planning is a later gate.
apt-get install -y --no-install-recommends libboost-dev socat ros-jazzy-ros2-control ros-jazzy-ros2-controllers ros-jazzy-xacro ros-jazzy-robot-state-publisher ros-jazzy-rviz2 ros-jazzy-joint-state-publisher ros-jazzy-tf2-geometry-msgs ros-jazzy-urdf
