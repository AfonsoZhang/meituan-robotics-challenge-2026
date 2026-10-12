"""Prepare only this event's isolated supplement; OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess

root = Path('/home/afonso/meituan-robotics-challenge-2026')
raw = Path(__file__).resolve().parent
watch = root / 'outputs/moveit-watch-20261011'
commit = 'dc76a0bf0a43f9110f3d24cfa38a2b3478f48dcd'
original = 'mtc-repro-5c8f61d8af9f-dc76a0bf0a43'
container = 'mtc-vision-replay-review-dc76a0b'
raw.joinpath('logs').mkdir(exist_ok=True)

def write(name, data):
    (raw / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def run(label, args, timeout=120):
    start = datetime.now(timezone.utc).isoformat()
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    (raw / 'logs' / (label + '.log')).write_text(p.stdout + p.stderr)
    write('logs/' + label + '.json', {'argv': args, 'started_at': start,
          'ended_at': datetime.now(timezone.utc).isoformat(), 'exit_code': p.returncode})
    assert p.returncode == 0, (label, p.stderr)
    return p.stdout

assert not Path('/proc/56334').exists(), 'original runner still exists'
state = json.loads((watch / 'state.json').read_text())
assert state['active'] is None and state['main_review']['event'] == 'sha-' + commit
assert state['main_review']['status'] == 'ACKNOWLEDGED'
prior = subprocess.check_output(['docker', 'ps', '-a', '--format', '{{.Names}}'], text=True).splitlines()
assert container not in prior, 'Do not overwrite a previous supplement'
snapshots = []
for name in prior:
    if name.startswith('mtc-'):
        v = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]
        assert not v['State']['Running'], name
        snapshots.append({'name': name, 'state': v['State']})
write('prior-stopped.json', {'original_runner_pid': 56334, 'runner_absent': True,
                           'at': datetime.now(timezone.utc).isoformat(), 'containers': snapshots})
write('project-before.json', {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
      'formal_pin_sha256': hashlib.sha256((root / 'robot/fsm-baseline.repos').read_bytes()).hexdigest(),
      'status': subprocess.check_output(['git', 'status', '--short'], cwd=root, text=True)})
run('clone', ['git', 'clone', '--no-hardlinks', str(watch / 'upstream.git'), str(raw / 'source')])
run('checkout', ['git', '-C', str(raw / 'source'), 'checkout', '--detach', commit])
original_inspect = json.loads(subprocess.check_output(['docker', 'inspect', original]))[0]
write('original-inspect-before.json', original_inspect)
image = run('commit-image', ['docker', 'commit', original, 'mtc-vision-replay-review:dc76a0b'], 240).strip()
argv = ['docker', 'run', '-d', '--name', container, '--network', 'none', '--cpus', '2',
        '--memory', '4g', '--pids-limit', '512', '--cap-drop', 'ALL', '--security-opt',
        'no-new-privileges', '--label', 'mtc.purpose=vision-replay-acceptance', '--label',
        'mtc.event=sha-' + commit, image, 'sleep', 'infinity']
run('create-supplement', argv)
v = json.loads(subprocess.check_output(['docker', 'inspect', container]))[0]
h = v['HostConfig']
assert v['State']['Running'] and h['NetworkMode'] == 'none'
assert h['NanoCpus'] == 2_000_000_000 and h['Memory'] == 4_294_967_296
assert not v['Mounts'] and not h['Devices'] and not h['PortBindings']
assert h['PidsLimit'] == 512 and 'ALL' in h['CapDrop'] and 'no-new-privileges' in h['SecurityOpt']
write('supplement-isolation.json', v)
write('runtime.json', {'container': container, 'image': image, 'argv': argv,
                      'source_container': original, 'commit': commit,
                      'ready_at': datetime.now(timezone.utc).isoformat()})
shutil.copyfile(root / 'outputs/handoff-acceptance-20261012-a04ac68/run_step.py', raw / 'run_step.py')
run('review-tools-directory', ['docker', 'exec', container, 'mkdir', '-p', '/review-tools', '/review-evidence'])
print('READY', container, flush=True)
