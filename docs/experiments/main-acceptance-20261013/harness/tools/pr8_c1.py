"""One unchanged PR #8 delayed-cancel repro; no automatic retry or kernel edit.

Codex-assisted external supervisor. A terminal Result is not automatically PASS.
"""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import signal
import subprocess
import time

out = Path('/pr8-review/c1')
out.mkdir(exist_ok=False)
stack_out = out / 'stack'
argv = ['ros2', 'run', 'mtc_cpp_mock_bringup', 'mock_stack', '--namespace', '/cpp_c1',
        '--output-dir', str(stack_out), '--result-delay-ms', '700', '--no-web']
result = {'sha': '7da43228d602a6b23571bfc599d69529ef7bea23',
          'started_at': datetime.now(timezone.utc).isoformat(), 'stack_argv': argv,
          'status': 'NOT_RUN', 'scope': 'Unchanged PR8 CLI C1 reproducer; no new browser acceptance'}
with (out / 'stack.log').open('xb') as log:
    stack = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            if stack.poll() is not None:
                raise RuntimeError('stack exited before ready')
            ready = stack_out / 'ready.json'
            if ready.exists() and json.loads(ready.read_text())['ok']:
                break
            time.sleep(.1)
        else:
            raise TimeoutError('stack readiness')
        goal = {'task_id': 'c1_retest_20261013', 'mode': 1, 'ordered_colors': [1],
                'timeout_ms': 30000, 'placement_stability_sec': 3}
        client_argv = ['ros2', 'run', 'mtc_cpp_mock_bringup', 'mock_task',
                       '--namespace', '/cpp_c1', '--output-dir', str(out / 'client'),
                       '--cancel-at', 'MOVE_PRE_ALIGN', '--cancel-delay-ms', '400',
                       '--goal', json.dumps(goal)]
        result['client_argv'] = client_argv
        with (out / 'client.log').open('xb') as client_log:
            client = subprocess.run(client_argv, stdout=client_log,
                                    stderr=subprocess.STDOUT, timeout=55)
        result['client_exit_code'] = client.returncode
        final = json.loads((out / 'client/result.json').read_text())
        result['actual'] = final
        events = [json.loads(line) for line in (out / 'client/events.jsonl').read_text().splitlines()]
        result['cancel_reply'] = [e for e in events if e['kind'] == 'cancel_reply']
        result['child_statuses'] = [e for e in events if e['kind'] == 'status' and
                                    e['endpoint'].endswith('/manipulation/pick_place')]
        result['status'] = 'PASS_CANCEL_COMPLETED' if final['status'] == 5 and final['result']['error_code'] == 0 else 'FAIL_CANCEL_NOT_COMPLETED'
    except Exception as exc:
        result.update(status='HARNESS_OR_RUNTIME_ERROR', exception=repr(exc))
    finally:
        if stack.poll() is None:
            stack.send_signal(signal.SIGINT)
            try:
                stack.wait(timeout=22)
            except subprocess.TimeoutExpired:
                result['forced_cleanup'] = True
                os.killpg(stack.pid, signal.SIGTERM)
                try:
                    stack.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(stack.pid, signal.SIGKILL)
                    stack.wait(timeout=3)
        result['stack_exit_code'] = stack.returncode
        cleanup = stack_out / 'cleanup.json'
        if cleanup.exists():
            result['cleanup'] = json.loads(cleanup.read_text())
        result['ended_at'] = datetime.now(timezone.utc).isoformat()
        (out / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
raise SystemExit(0 if result['status'] == 'PASS_CANCEL_COMPLETED' and
                 result['stack_exit_code'] == 0 and result.get('cleanup', {}).get('cleanup_ok') else 1)
