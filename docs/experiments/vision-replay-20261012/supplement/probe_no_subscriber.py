"""Observe installed replay without a subscriber; no publisher mocks. Codex assisted."""
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from datetime import datetime, timezone
import rclpy
from rclpy.node import Node

out = Path('/review-evidence/no-subscriber')
out.mkdir(parents=True, exist_ok=False)
executable = '/candidate-install/mtc_vision_adapter/lib/mtc_vision_adapter/replay_publisher'
fixture = '/candidate/src/mtc_vision_adapter/examples/synthetic.jsonl'
rclpy.init()
node = Node('replay_no_subscriber_observer')
results = []
try:
    for name, extra, expected in [
        ('default-natural', [], 0),
        ('bounded-discovery-timeout', ['-p', 'wait_for_subscriber_s:=2.0', '-p', 'period_s:=0.25'], 1),
    ]:
        argv = [executable, '--ros-args', '-p', 'input_jsonl:=' + fixture] + extra
        started = datetime.now(timezone.utc).isoformat()
        start = time.monotonic()
        log_path = out / (name + '.log')
        code = None
        signals = []
        with log_path.open('w') as stream:
            proc = subprocess.Popen(argv, stdout=stream, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, start_new_session=True)
            try:
                while proc.poll() is None and time.monotonic() - start < 20:
                    rclpy.spin_once(node, timeout_sec=.1)
                code = proc.poll()
            finally:
                if proc.poll() is None:
                    signals.append('SIGINT')
                    os.killpg(proc.pid, signal.SIGINT)
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        signals.append('SIGKILL')
                        os.killpg(proc.pid, signal.SIGKILL)
                        proc.wait()
        text = log_path.read_text()
        deadline = time.monotonic() + 10
        while any(n == 'vision_offline_replay' for n, _ in node.get_node_names_and_namespaces()) and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=.1)
        remaining = [n for n, _ in node.get_node_names_and_namespaces() if n == 'vision_offline_replay']
        frames = [line for line in text.splitlines() if 'frame=' in line]
        checks = {
            'exit_expected': code == expected,
            'no_cleanup_signals': not signals,
            'node_gone': not remaining,
            'no_duplicate_shutdown': 'already called' not in text and 'already shutdown' not in text,
            'created_qos': 'created QoS: RELIABLE KEEP_LAST(5) VOLATILE' in text,
        }
        if name == 'default-natural':
            checks.update(four_publishes=len(frames) == 4,
                          natural_completion='replay complete' in text,
                          no_traceback='Traceback' not in text)
        else:
            checks.update(zero_publishes=not frames,
                          explicit_discovery_timeout='TimeoutError: no matched replay subscriber' in text,
                          no_false_completion='replay complete' not in text)
        results.append({'case': name, 'argv': argv, 'pid': proc.pid, 'started_at': started,
                        'ended_at': datetime.now(timezone.utc).isoformat(),
                        'elapsed_seconds': time.monotonic() - start, 'exit_code': code,
                        'signals': signals, 'published_log_count': len(frames),
                        'remaining_nodes': remaining, 'checks': checks,
                        'passed': all(checks.values()),
                        'scope': 'No subscription created, no frame delivery claimed; graph observer only.'})
        (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
finally:
    node.destroy_node()
    rclpy.try_shutdown()
print(json.dumps(results, indent=2))
assert len(results) == 2 and all(r['passed'] for r in results)
