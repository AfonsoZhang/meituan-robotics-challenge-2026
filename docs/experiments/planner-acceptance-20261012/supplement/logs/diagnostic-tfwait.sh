set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
export ROS_DOMAIN_ID=117
export AUBO_WS=/driver_ws MTC_WS=/candidate MTC_RMW=rmw_fastrtps_cpp
export ROS_LOG_DIR=/review-evidence/diagnostic-tfwait/ros-logs
mkdir -p /review-evidence/diagnostic-tfwait
python3 - <<'CONFIG'
from pathlib import Path
import yaml
p=Path('/candidate/src/mtc_moveit_planner/config/planner.yaml')
y=yaml.safe_load(p.read_text());y['/**']['ros__parameters']['backend']['tf_timeout_s']=5.0
Path('/review-evidence/diagnostic-tfwait/planner-tfwait.yaml').write_text(yaml.safe_dump(y,sort_keys=False))
CONFIG
timeout --signal=TERM --kill-after=15 360 bash /review-evidence/diagnostic-tfwait-sop.sh /review-evidence/diagnostic-tfwait
