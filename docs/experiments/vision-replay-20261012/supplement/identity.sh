python3 src/mtc_ros2_action_cpp/test/verify_results.py --build-base /candidate-build
python3 - <<'PY'
from pathlib import Path
import hashlib, json
from ament_index_python.packages import get_package_prefix, get_package_share_directory
result = {}
for package in ['mtc_ros2_action_cpp', 'mtc_vision_adapter']:
    prefix = Path(get_package_prefix(package))
    share = Path(get_package_share_directory(package))
    paths = ['package.xml']
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
python3 - <<'INNER'
from pathlib import Path
import hashlib,json,mtc_vision_adapter
base=Path(mtc_vision_adapter.__file__).parent
v=[]
for n in ['__init__.py','core.py','publisher.py']:
 a=Path('/candidate/src/mtc_vision_adapter/mtc_vision_adapter')/n;b=base/n
 assert a.read_bytes()==b.read_bytes()
 v.append({'path':n,'sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'installed':str(b)})
Path('/review-evidence/adapter-code-identity.json').write_text(json.dumps(v,indent=2)+'\n')
INNER
