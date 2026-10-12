python3 src/mtc_ros2_action_cpp/test/verify_results.py --build-base /candidate-build
rosdep check --from-paths src/mtc_ros2_action_cpp src/mtc_moveit_planner --ignore-src
python3 - <<'PY'
from pathlib import Path
import hashlib, json
from ament_index_python.packages import get_package_prefix, get_package_share_directory
result = {}
for package in ['mtc_ros2_action_cpp', 'mtc_moveit_planner']:
    prefix = Path(get_package_prefix(package))
    share = Path(get_package_share_directory(package))
    paths = ['package.xml']
    if package == 'mtc_moveit_planner':
        paths += ['config/planner.yaml', 'config/sequence_v2_override.yaml', 'config/collision_probe_override.yaml', 'launch/plan_tool.launch.py']
    records = []
    for name in paths:
        source = Path('/candidate/src') / package / name
        installed = share / name
        assert source.read_bytes() == installed.read_bytes(), name
        records.append({'path': name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'installed_equals_source': True})
    result[package] = {'prefix': str(prefix), 'files': records,
        'executables': sorted(p.name for p in (prefix / 'lib' / package).iterdir() if p.is_file())}
Path('/review-evidence/installed-identities.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
PY
