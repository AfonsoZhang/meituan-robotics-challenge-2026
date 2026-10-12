"""Collect and stop this event's supplement without changing prior evidence."""
from pathlib import Path
from datetime import datetime, timezone
import json, subprocess

raw = Path(__file__).resolve().parent
container = 'mtc-vision-adapter-review-0e329f1'
original = 'mtc-repro-5c8f61d8af9f-0e329f10e6f6'

def inspect(name):
    return json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]

assert not Path('/proc/18721').exists()
for name in [original, 'mtc-planner-scene-review-30e3c6e', 'mtc-repro-5c8f61d8af9f-30e3c6e64516']:
    assert not inspect(name)['State']['Running'], name
assert inspect(container)['State']['Running']
for label in ['inventory','identity','adapter-unit-original','core-original','ros-replay','ros-replay-wait5','install-offline','install-pep517','install-compatible','core-offline','core-compatible','entrypoints','final-environment']:
    assert (raw / 'logs' / (label + '.json')).is_file(), 'Step has not finished: ' + label
top = subprocess.check_output(['docker', 'top', container, '-eo', 'pid,ppid,args'], text=True)
(raw / 'container-processes-before-stop.txt').write_text(top)
assert len(top.strip().splitlines()) == 2 and top.strip().endswith('sleep infinity'), top
diff = subprocess.check_output(['docker', 'exec', container, 'git', '-C', '/candidate', 'diff', 'HEAD', '--'], text=True)
assert not diff, 'Source changed during supplement'
head = subprocess.check_output(['docker', 'exec', container, 'git', '-C', '/candidate', 'rev-parse', 'HEAD'], text=True).strip()
assert head == '0e329f10e6f607c9c417a54ae60d290b8e2395b5'
(raw / 'source-after.json').write_text(json.dumps({'commit': head, 'tracked_diff': diff, 'source_changed': False,
    'path_aliases': [], 'environment_changes': 'Isolated venv plus copied offline dependency wheels; temporary editable-install metadata only, original installed ROS adapter and tracked source unchanged'}, indent=2) + '\n')
stop = subprocess.run(['docker', 'stop', '-t', '12', container], capture_output=True, text=True, timeout=30)
assert stop.returncode == 0, stop.stderr
(raw / 'container').mkdir()
subprocess.run(['docker', 'cp', container + ':/review-evidence/.', str(raw / 'container')], check=True, timeout=60)
records = []
for name in [original, container]:
    v = inspect(name)
    assert not v['State']['Running'] and not v['State']['OOMKilled']
    (raw / (name + '-final-inspect.json')).write_text(json.dumps(v, indent=2) + '\n')
    records.append({'container': name, 'state': v['State'], 'network': v['HostConfig']['NetworkMode'],
                    'cpus': v['HostConfig']['NanoCpus'], 'memory': v['HostConfig']['Memory'],
                    'mounts': v['Mounts'], 'devices': v['HostConfig']['Devices'], 'ports': v['HostConfig']['PortBindings']})
(raw / 'cleanup.json').write_text(json.dumps({'recorded_at': datetime.now(timezone.utc).isoformat(),
    'original_runner_pid': 18721, 'original_runner_absent': True, 'supplement_before_stop': 'only sleep infinity; no ROS processes or daemons',
    'stop': {'exit_code': stop.returncode, 'stdout': stop.stdout, 'stderr': stop.stderr}, 'containers': records,
    'keeper_exit137_note': 'docker stop terminates keeper; ROS child results checked separately.'}, indent=2) + '\n')
print('CLEANED_AND_COLLECTED', container)
