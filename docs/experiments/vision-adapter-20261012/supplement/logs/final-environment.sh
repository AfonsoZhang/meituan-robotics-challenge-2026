set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
/review-venv/bin/python - <<'INNER'
import importlib,sys,json,setuptools
from pathlib import Path
from importlib import metadata
v={'python':sys.version,'prefix':sys.prefix,'setuptools':setuptools.__version__,'distribution':{},'modules':{}}
for n in ['mtc-vision-core','mtc_vision_adapter','numpy','scipy','opencv-python','PyYAML','matplotlib','pytest','pip','setuptools','colcon-core']:
 v['distribution'][n]=metadata.version(n)
for n in ['perception','input','cad_geometry','synthetic','evaluation','real_data','config','mtc_vision_adapter','rclpy','mtc_interfaces.msg']:
 m=importlib.import_module(n);v['modules'][n]=m.__file__
Path('/review-evidence/final-environment.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
INNER
python3 - <<'INNER'
from pathlib import Path
import json,subprocess
v={'tracked_diff':subprocess.check_output(['git','-C','/candidate','diff','HEAD','--'],text=True),'generated_untracked':subprocess.check_output(['git','-C','/candidate','status','--short'],text=True),'devices':'No devices passed to container','optional_assets_present':{p:Path('/candidate/vision_core',p).exists() for p in ['assets/cad/电池道具.stp','assets/cad/舌规V1.STEP','outputs/p0_ros2/replay.jsonl','data/rgbd/session_20261011_143230_red_top']}}
assert not v['tracked_diff']
Path('/review-evidence/source-and-assets.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(json.dumps(v,ensure_ascii=False,indent=2))
INNER
ps -eo pid,ppid,stat,args
