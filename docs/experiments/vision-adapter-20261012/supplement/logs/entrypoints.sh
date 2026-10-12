set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
export MPLBACKEND=Agg MPLCONFIGDIR=/review-evidence/matplotlib
mkdir -p /review-evidence/entrypoints
cd /candidate/vision_core
timeout 30 /review-venv/bin/python scripts/live_rgbd_preview.py --help > /review-evidence/entrypoints/rgbd-help.txt
timeout 30 /review-venv/bin/python scripts/live_realsense_handheld.py --help > /review-evidence/entrypoints/handheld-help.txt
timeout --signal=TERM --kill-after=10 120 /review-venv/bin/python scripts/replay_ros2_p0.py --output /review-evidence/synthetic --session /review-evidence/no-private-session
