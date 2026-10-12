export ROS_DOMAIN_ID=118
source /driver_work/install/setup.bash
rosdep check --from-paths /candidate/src/mtc_moveit_planner --ignore-src --rosdistro jazzy
python3 - <<'VERIFY'
import json,hashlib
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
p=Path(get_package_share_directory('mtc_moveit_planner'))
files=['config/planner.yaml','config/sequence_v2_override.yaml','launch/plan_tool.launch.py','package.xml']
rows=[]
for s in files:
 a=Path('/candidate/src/mtc_moveit_planner')/s;b=p/s
 assert a.read_bytes()==b.read_bytes(),s
 rows.append({'path':s,'installed':str(b),'sha256':hashlib.sha256(a.read_bytes()).hexdigest()})
Path('/review-evidence/installed-identity.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps({'installed_configuration_source_identity':'PASS','files':rows},indent=2))
VERIFY
git status --short
