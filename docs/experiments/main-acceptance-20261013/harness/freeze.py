"""Create one new evidence set; never edit existing evidence or signed reports."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess

raw = Path(__file__).resolve().parent
root = raw / 'publication'
target = root / 'docs/experiments/main-acceptance-20261013'
target.mkdir(parents=True, exist_ok=False)
def copy(a, b):
    b.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(a, b)

excluded = []
for source, dest in [('runtime', 'runtime'), ('pr8-runtime', 'pr8-runtime'),
                     ('logs', 'host-logs'), ('meta', 'host'), ('tools', 'harness/tools')]:
    for p in sorted((raw / source).rglob('*')):
        if not p.is_file():
            continue
        if (p.is_symlink() or '__pycache__' in p.parts or '.pytest_cache' in p.parts or
            p.suffix == '.pyc' or p.name in ['CMakeCache.txt', 'prior-jobs.json']):
            excluded.append(str(p.relative_to(raw)))
            continue
        copy(p, target / dest / p.relative_to(raw / source))
for p in ['step.py', 'step-pr8.py', 'analyze.py', 'freeze.py']:
    copy(raw / p, target / 'harness' / p)
for p in ['summary.json', 'inputs.json', 'protocol.md']:
    copy(raw / p, target / p)

# Small source witnesses + actual Git patches; no .git, outputs, caches or SDK blobs.
selected = ['LICENSE', 'src/mtc_trajectory_execution_cpp/src/fjt_motion_port.cpp',
            'src/mtc_trajectory_execution_cpp/test/test_fjt_action.cpp',
            'src/mtc_trajectory_execution_cpp/test/verify_results.py',
            'src/mtc_trajectory_execution_cpp/include/mtc_trajectory_execution_cpp/execution_state.hpp',
            'src/mtc_ros2_action_cpp/src/task_server.cpp',
            'src/mtc_ros2_action_cpp/src/pick_place_server.cpp',
            'src/mtc_ros2_action_cpp/src/mock_ports.cpp',
            'src/mtc_ros2_action_cpp/include/mtc_ros2_action_cpp/mock_ports.hpp',
            'src/mtc_interfaces/action/ExecuteTask.action', 'src/mtc_interfaces/action/PickPlace.action',
            'docs/migration/PHASE2B_ACTION_MUTEX_BACKPORT_GATE.md']
for name in selected:
    copy(raw / 'source' / name, target / 'source' / name)
(target / 'archive-selection.json').write_text(json.dumps({'excluded_from_freeze': excluded,
    'source_files': selected, 'note': 'Original bytes remain in local outputs; cached dependencies/binaries/full Git/private job state excluded.'}, indent=2) + '\n')
entries = [{'path': str(p.relative_to(target)), 'size_bytes': p.stat().st_size,
            'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
           for p in sorted(target.rglob('*')) if p.is_file()]
index = {'schema_version': 1, 'observation': 'ENV-MAIN-ACCEPTANCE-20261013',
         'created_at': datetime.now(timezone.utc).isoformat(), 'files': entries}
(target / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
receipt = {'index': str((target / 'index.json').relative_to(root)),
           'files': len(entries), 'size_bytes': sum(e['size_bytes'] for e in entries),
           'index_sha256': hashlib.sha256((target / 'index.json').read_bytes()).hexdigest()}
(raw / 'freeze-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt, indent=2))
