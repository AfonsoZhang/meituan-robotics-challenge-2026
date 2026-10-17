uname -a
cat /etc/os-release
dpkg-query -W
git rev-parse HEAD
git status --porcelain
git -C /driver_ws/src/aubo_ros2_driver rev-parse HEAD
git -C /driver_ws/src/aubo_ros2_driver/aubo_description rev-parse HEAD
env | sort | grep -E '^(ROS|RMW|AMENT|COLCON|CMAKE_PREFIX_PATH|PYTHONPATH)='
python3 - <<'PY'
from pathlib import Path
import hashlib,json
root=Path('/main-source')
files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
Path('/review/source-files-before.json').write_text(json.dumps(files,indent=2)+'\n')
PY
