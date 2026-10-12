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
git status --porcelain
git diff --exit-code c0f70172e4b0271046d5f52813e0730d40ae772a HEAD -- src/mtc_core_cpp src/mtc_task_cpp src/mtc_manipulation_cpp src/mtc_motion_execution_cpp src/mtc_ros2_action_cpp src/mtc_interfaces docs/setup docs/migration/patches
git diff --exit-code 1d3dccf23c53d299d457564daeb6438190ea2d77 HEAD -- src/mtc_task/mtc_task/task_executor.py src/mtc_manipulation/mtc_manipulation/pick_place_server.py tests/test_ros_wiring.py docs/migration/ROS_WIRING_FIX_20261011.md
python3 src/mtc_ros2_action_cpp/test/verify_results.py --build-base /candidate-build
python3 - <<'PY'
import importlib.util,subprocess,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
items=[]
for module in ['mtc_task.task_executor','mtc_manipulation.pick_place_server']:
 path=Path(importlib.util.find_spec(module).origin)
 source=Path('/candidate/src')/module.split('.')[0]/Path(*module.split('.')).with_suffix('.py')
 assert path.read_bytes()==source.read_bytes(),(path,source)
 items.append({'module':module,'installed':str(path),'source':str(source),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
xml=ET.parse('/candidate-evidence/ros-wiring.xml').getroot();cases=list(xml.iter('testcase'))
assert len(cases)==6 and all(not list(c) for c in cases),[(c.attrib,list(c)) for c in cases]
print('PASS: two installed Python wrappers match source; six actual ROS XML cases with no failures or skips')
Path('/review-evidence/installed-python-identity.json').write_text(json.dumps(items,indent=2)+'\n')
PY
