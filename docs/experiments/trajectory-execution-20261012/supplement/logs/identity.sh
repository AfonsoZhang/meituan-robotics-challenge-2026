set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
export ROS_DOMAIN_ID=132
python3 src/mtc_trajectory_execution_cpp/test/verify_results.py --build-base /candidate-build
rosdep check --from-paths src/mtc_trajectory_execution_cpp --ignore-src
python3 - <<'INNER'
from pathlib import Path
from ament_index_python.packages import get_package_share_directory,get_package_prefix
import hashlib,json,subprocess
pkg='mtc_trajectory_execution_cpp';root=Path('/candidate/src')/pkg
prefix=Path(get_package_prefix(pkg));pairs=[(root/'package.xml',Path(get_package_share_directory(pkg))/'package.xml')]
for p in (root/'include').rglob('*.hpp'):pairs.append((p,prefix/'include'/p.relative_to(root/'include')))
rows=[]
for a,b in pairs:
 assert a.read_bytes()==b.read_bytes(),str(b)
 rows.append({'source':str(a),'installed':str(b),'sha256':hashlib.sha256(a.read_bytes()).hexdigest()})
Path('/review-evidence/installed-identity.json').write_text(json.dumps(rows,indent=2)+'\n')
probe=prefix/'lib'/pkg/'fake_trajectory_probe';negative=[]
for args in [[],['--verify-generic-system','invalid-mode']]:
 p=subprocess.run([str(probe),*args],capture_output=True,text=True,timeout=10)
 negative.append({'argv':[str(probe),*args],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 assert p.returncode==2
Path('/review-evidence/argument-negatives.json').write_text(json.dumps(negative,ensure_ascii=False,indent=2)+'\n')
print('INSTALLED_IDENTITY_PASS',len(rows),'ARGUMENT_NEGATIVES_PASS',len(negative))
INNER
