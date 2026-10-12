set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
source /driver_work/install/setup.bash
python3 /candidate/src/mtc_ros2_action_cpp/test/verify_results.py --build-base /candidate-build
rosdep check --from-paths /candidate/src/mtc_moveit_planner /candidate/src/mtc_ros2_action_cpp --ignore-src
python3 - <<'INNER'
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
import hashlib,json,subprocess
root=Path('/candidate'); rows=[]
for pkg,files in [('mtc_moveit_planner',['package.xml','config/planner.yaml','config/sequence_v2_override.yaml','launch/plan_tool.launch.py']),('mtc_ros2_action_cpp',['package.xml'])]:
 for rel in files:
  a=root/'src'/pkg/rel;b=Path(get_package_share_directory(pkg))/rel
  assert a.read_bytes()==b.read_bytes(),str(a)
  rows.append({'source':str(a),'installed':str(b),'sha256':hashlib.sha256(a.read_bytes()).hexdigest()})
assert subprocess.check_output(['git','-C','/candidate','rev-parse','HEAD'],text=True).strip()=='f7eaa2c0d2887aeada4fd635112c63c237962ff7'
assert not subprocess.check_output(['git','-C','/candidate','diff','HEAD','--'],text=True)
Path('/review-evidence/installed-identity.json').write_text(json.dumps(rows,indent=2)+'\n')
print('INSTALLED_IDENTITY_PASS',len(rows))
INNER
