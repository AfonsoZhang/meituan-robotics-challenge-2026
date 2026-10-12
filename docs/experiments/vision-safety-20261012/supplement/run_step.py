"""Local acceptance command recorder, OpenAI Codex assisted, 2026-10-11."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
label, timeout, script = sys.argv[1:]
assert label.replace('-', '').replace('_', '').isalnum()
name = json.loads((root / 'runtime.json').read_text())['container']
prefix = '''set -e
source /opt/ros/jazzy/setup.bash
source /candidate-install/setup.bash
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
export ROS_DOMAIN_ID=106 PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review-evidence/ros-logs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
mkdir -p /review-evidence
cd /candidate
'''
cmd = prefix + Path(script).read_text()
(root / 'logs' / (label + '.sh')).write_text(cmd)
start = datetime.now(timezone.utc).isoformat()
argv = ['/usr/bin/docker', 'exec', name, 'bash', '-c', cmd]
with (root / 'logs' / (label + '.log')).open('wb') as stream:
    try:
        code = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT,
                              timeout=float(timeout)).returncode
    except subprocess.TimeoutExpired:
        code = 124
        subprocess.run(['/usr/bin/docker', 'stop', '-t', '12', name], timeout=30,
                       stdout=stream, stderr=subprocess.STDOUT)
record = {'label': label, 'started_at': start,
          'ended_at': datetime.now(timezone.utc).isoformat(),
          'container': name, 'script': str(root / 'logs' / (label + '.sh')),
          'timeout_seconds': float(timeout), 'exit_code': code}
(root / 'logs' / (label + '.json')).write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record), flush=True)
sys.exit(code)
