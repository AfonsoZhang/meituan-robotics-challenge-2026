"""No-Goal restart/cleanup check after C1; signal the actual supervisor directly."""
from pathlib import Path
import json
import os
import signal
import subprocess
import sys
import time

out = Path('/pr8-review/cleanup-only')
out.mkdir(exist_ok=False)
argv = [sys.executable, '-m', 'mtc_cpp_mock_bringup.bringup', '--namespace', '/cpp_c1',
        '--output-dir', str(out / 'stack'), '--result-delay-ms', '700', '--no-web']
result = {'scope': 'No-Goal same-namespace restart; direct supervisor SIGINT; not a C1 rerun',
          'argv': argv, 'status': 'FAIL'}
with (out / 'supervisor.log').open('xb') as log:
    p = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            assert p.poll() is None, 'supervisor exited before ready'
            ready = out / 'stack/ready.json'
            if ready.exists() and json.loads(ready.read_text())['ok']:
                break
            time.sleep(.1)
        else:
            raise TimeoutError('readiness')
        time.sleep(2)
        p.send_signal(signal.SIGINT)
        p.wait(timeout=20)
        cleanup = json.loads((out / 'stack/cleanup.json').read_text())
        result['cleanup'] = cleanup
        assert p.returncode == 0 and cleanup['cleanup_ok'] and not cleanup.get('forced_cleanup')
        assert all(v == 0 for v in cleanup['returncodes'].values())
        for name in ('task.log', 'pick_place.log'):
            assert 'goal_accepted' not in (out / 'stack' / name).read_text()
        result['status'] = 'PASS'
    except Exception as exc:
        result['exception'] = repr(exc)
    finally:
        if p.poll() is None:
            result['forced_cleanup'] = True
            os.killpg(p.pid, signal.SIGTERM)
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(p.pid, signal.SIGKILL)
                p.wait(timeout=3)
        result['exit_code'] = p.returncode
        (out / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
raise SystemExit(0 if result['status'] == 'PASS' else 1)
