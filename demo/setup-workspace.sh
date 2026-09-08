#!/usr/bin/env bash
# Builds only description + project simulation; does not install or run real-hardware drivers.
set -euo pipefail
DEMO_PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DEMO_WORKSPACE="${AUBO_ROS2_WS:-${HOME}/aubo_ros2_ws}"
DEMO_ROS_SETUP="${DEMO_ROS_SETUP:-/opt/ros/humble/setup.bash}"
DEMO_DESCRIPTION_URL="${AUBO_DESCRIPTION_REPOSITORY:-https://github.com/AuboRobot/aubo_description.git}"
DEMO_DESCRIPTION_COMMIT=47fa5e02fa873f27f7e812d31f31e3f4cf5e56b1
if [[ ! -f "$DEMO_ROS_SETUP" ]]; then
  echo "Install ROS 2 Humble first; see demo/SETUP.md." >&2
  exit 1
fi
set +u
source "$DEMO_ROS_SETUP"
set -u
command -v colcon >/dev/null
mkdir -p "$DEMO_WORKSPACE/src"
DEMO_DESCRIPTION_DIR="$DEMO_WORKSPACE/src/aubo_description"
if [[ ! -e "$DEMO_DESCRIPTION_DIR" ]]; then
  git clone --no-checkout "$DEMO_DESCRIPTION_URL" "$DEMO_DESCRIPTION_DIR"
  git -C "$DEMO_DESCRIPTION_DIR" checkout --detach "$DEMO_DESCRIPTION_COMMIT"
fi
if [[ "$(git -C "$DEMO_DESCRIPTION_DIR" rev-parse HEAD)" != "$DEMO_DESCRIPTION_COMMIT" ]]; then
  echo "Existing aubo_description is not at the pinned commit. Use a fresh AUBO_ROS2_WS." >&2
  exit 1
fi
git -C "$DEMO_DESCRIPTION_DIR" diff --quiet HEAD --
cd "$DEMO_WORKSPACE"
# Do not use --symlink-install: upstream contains directory-level mesh symlinks.
colcon build --base-paths "$DEMO_DESCRIPTION_DIR" "$DEMO_PROJECT_DIR/simulation/meituan_sim" "$DEMO_PROJECT_DIR/simulation/meituan_robust_control" \
  --packages-select aubo_description meituan_sim meituan_robust_control \
  --cmake-args -DBUILD_TESTING=OFF -DPython3_EXECUTABLE=/usr/bin/python3
echo "Built workspace: $DEMO_WORKSPACE"
echo "Run: AUBO_ROS2_WS=\"$DEMO_WORKSPACE\" bash \"$DEMO_PROJECT_DIR/demo/run.sh\" --check"
