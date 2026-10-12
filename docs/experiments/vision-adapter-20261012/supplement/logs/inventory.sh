set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
python3 - <<'INNER'
import json,importlib,sys
from pathlib import Path
v={'python':sys.version,'imports':{}}
for name in ['numpy','scipy','cv2','yaml','matplotlib','pytest','pip','venv','setuptools','rclpy','mtc_interfaces.msg','mtc_vision_adapter']:
 try:
  m=importlib.import_module(name);v['imports'][name]={'file':getattr(m,'__file__',None),'version':getattr(m,'__version__',None)}
 except Exception as e:v['imports'][name]={'error':repr(e)}
Path('/review-evidence/base-environment.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
INNER
python3 src/mtc_ros2_action_cpp/test/verify_results.py /candidate-build
