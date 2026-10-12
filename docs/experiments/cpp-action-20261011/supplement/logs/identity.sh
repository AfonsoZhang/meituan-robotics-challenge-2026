set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
git rev-parse HEAD
git diff --exit-code 1d940f7c5f12561fed6641457c0b4b630a282b05 HEAD -- src/mtc_core_cpp src/mtc_task_cpp src/mtc_manipulation_cpp src/mtc_motion_execution_cpp src/mtc_interfaces src/mtc_task src/mtc_manipulation
git status --short
python3 src/mtc_ros2_action_cpp/test/verify_results.py --build-base /candidate-build
ament_xmllint src/mtc_ros2_action_cpp/package.xml
rosdep check --from-paths src/mtc_ros2_action_cpp --ignore-src
