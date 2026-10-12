"""Isolated DDS replay acceptance, no action goals or devices. Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, math, os, signal, subprocess, time
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from mtc_interfaces.msg import BatteryDetectionArray
from mtc_task.task_executor import TaskExecutorNode
from rosidl_runtime_py.convert import message_to_ordereddict

out = Path('/review-evidence/replay-default'); out.mkdir(parents=True, exist_ok=True)
example = Path('/candidate/src/mtc_vision_adapter/examples/synthetic.jsonl')
records = [json.loads(x) for x in example.read_text().splitlines() if x]
summary = {'started_at': datetime.now(timezone.utc).isoformat(), 'scope': 'Actual installed replay publisher to isolated native Jazzy DDS subscriber; no task goal, camera or motion',
           'example_sha256': hashlib.sha256(example.read_bytes()).hexdigest(), 'domain': os.environ['ROS_DOMAIN_ID'],
           'checks': [], 'negative_inputs': [], 'shutdown': [], 'consumer_scope': 'Existing Python static candidate predicate only; no actual FSM topic subscription is delivered'}
received = []; endpoints = []; failures = []; proc = None; stream = None

def check(name, value, details=None):
    summary['checks'].append({'check': name, 'passed': bool(value), 'details': details})

def clean(value):
    if isinstance(value, float) and not math.isfinite(value):
        return 'NaN' if math.isnan(value) else str(value)
    if isinstance(value, dict): return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    return value

def save(name, obj):
    (out / name).write_text(json.dumps(clean(obj), ensure_ascii=False, indent=2, allow_nan=False) + '\n')

def stop(p, name):
    rec = {'name': name, 'pid': p.pid, 'escalated': False, 'already_exited': p.poll() is not None}
    if p.poll() is None:
        os.killpg(p.pid, signal.SIGINT)
        try: p.wait(timeout=6)
        except subprocess.TimeoutExpired:
            rec['escalated'] = True; os.killpg(p.pid, signal.SIGTERM)
            try: p.wait(timeout=4)
            except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL); p.wait(timeout=4)
    rec['exit_code'] = p.returncode
    summary['shutdown'].append(rec)

def native_match(msg, expected):
    h = msg.header
    if {'sec': h.stamp.sec, 'nanosec': h.stamp.nanosec} != expected['header']['stamp'] or h.frame_id != expected['header']['frame_id']:
        return False
    if len(msg.detections) != len(expected['detections']): return False
    for d, v in zip(msg.detections, expected['detections']):
        if d.object_id != v['object_id'] or d.color != v['color'] or not math.isclose(d.confidence, v['confidence'], abs_tol=1e-6) or d.ring_pose_valid:
            return False
        for name in ['body_pose', 'ring_pose']:
            pose = getattr(d, name)
            if pose.header != h: return False
            for group in ['position', 'orientation']:
                for key, val in v[name]['pose'][group].items():
                    actual = getattr(getattr(pose.pose, group), key)
                    if val is None and not math.isnan(actual): return False
                    if val is not None and actual != val: return False
    return True

rclpy.init()
node = Node('vision_acceptance_observer')
qos = QoSProfile(depth=5, reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, durability=DurabilityPolicy.VOLATILE)
topic = '/mtc/perception/batteries'
sub = node.create_subscription(BatteryDetectionArray, topic, lambda msg: received.append(msg), qos)
try:
    argv = ['ros2', 'run', 'mtc_vision_adapter', 'replay_publisher', '--ros-args', '-p', 'input_jsonl:=' + str(example), '-p', 'period_s:=1.0']
    summary['argv'] = argv
    stream = (out / 'publisher.log').open('w')
    proc = subprocess.Popen(argv, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline and len(received) < len(records) and proc.poll() is None:
        rclpy.spin_once(node, timeout_sec=.1)
        info = node.get_publishers_info_by_topic(topic)
        if info:
            endpoints = [{'node_name': e.node_name, 'namespace': e.node_namespace, 'type': e.topic_type,
                          'reliability': e.qos_profile.reliability.name, 'history': e.qos_profile.history.name,
                          'depth': e.qos_profile.depth, 'durability': e.qos_profile.durability.name} for e in info]
    check('four_records_received_in_order', len(received) == len(records), {'expected': len(records), 'actual': len(received)})
    check('unique_native_publisher_type_reliability_durability', len(endpoints) == 1 and endpoints[0]['type'] == 'mtc_interfaces/msg/BatteryDetectionArray'
          and endpoints[0]['reliability'] == 'RELIABLE' and endpoints[0]['durability'] == 'VOLATILE', endpoints)
    check('timestamp_frame_ids_colors_and_null_to_native_nan', len(received) == len(records) and all(native_match(a, b['message']) for a, b in zip(received, records)))
    colors = sorted({d.color for msg in received for d in msg.detections})
    check('all_four_color_enums', colors == [1, 2, 3, 4], colors)
    check('ring_invalid_and_existing_python_predicate_rejects_actual_candidates', bool(colors) and all(not TaskExecutorNode._is_usable_candidate(d) for msg in received for d in msg.detections))
    # Observe a known local predicate limitation without creating a task node/Goal.
    if any(m.detections for m in received):
        invalid = copy.deepcopy(next(m.detections[0] for m in received if m.detections))
        invalid.ring_pose_valid = True
        summary['existing_python_predicate_counterexample'] = {
            'ring_pose_valid_forced_true': True, 'body_x_is_nan': math.isnan(invalid.body_pose.pose.position.x),
            'ring_x_is_nan': math.isnan(invalid.ring_pose.pose.position.x),
            'old_stamp_sec': invalid.body_pose.header.stamp.sec,
            'predicate_accepts': TaskExecutorNode._is_usable_candidate(invalid),
            'scope': 'Static predicate only: validates ring flag/confidence, not finite pose/age. Artificial counterexample never published or sent to a task.'}
    # Actual IDL cannot carry these JSON provenance flags.
    summary['native_array_fields'] = BatteryDetectionArray.get_fields_and_field_types()
    if any(m.detections for m in received):
        summary['native_detection_fields'] = next(m.detections[0] for m in received if m.detections).get_fields_and_field_types()
    before = len(received); late_received = []
    late = node.create_subscription(BatteryDetectionArray, topic, lambda msg: late_received.append(msg), qos)
    until = time.monotonic() + 1.5
    while time.monotonic() < until: rclpy.spin_once(node, timeout_sec=.1)
    check('replay_completes_without_loop_and_volatile_late_subscriber_has_no_history', len(received) == before and not late_received,
          {'late_messages': len(late_received), 'publisher_remains_idle': proc.poll() is None})
    summary['completion_log_seen'] = 'replay complete' in (out / 'publisher.log').read_text()
    stop(proc, 'valid-replay')
    check('valid_replay_SIGINT_clean', proc.returncode == 0 and not summary['shutdown'][-1]['escalated'])
    proc = None
    stream.close(); stream = None
    # Declared fail-closed input mode gate, tested as separate processes.
    for label, content, phrase in [('empty', '', 'explicit replay/synthetic records required'),
                                    ('live-mode', json.dumps(dict(records[0], mode='live')) + '\n', 'explicit replay/synthetic records required')]:
        fixture = out / (label + '.jsonl'); fixture.write_text(content)
        argv = ['ros2', 'run', 'mtc_vision_adapter', 'replay_publisher', '--ros-args', '-p', 'input_jsonl:=' + str(fixture)]
        with (out / (label + '.log')).open('w') as log:
            proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            timed_out = False
            try: proc.wait(timeout=8)
            except subprocess.TimeoutExpired: timed_out = True; stop(proc, label)
            code = proc.returncode; proc = None
        text = (out / (label + '.log')).read_text()
        result = {'case': label, 'exit_code': code, 'timed_out': timed_out, 'explicit_rejection': phrase in text}
        summary['negative_inputs'].append(result)
        check('reject_' + label, code != 0 and not timed_out and phrase in text, result)
except Exception as e:
    failures.append(repr(e))
finally:
    if proc is not None: stop(proc, 'exception-cleanup')
    if stream is not None: stream.close()
    node.destroy_node()
    if rclpy.ok(): rclpy.shutdown()
    summary['ended_at'] = datetime.now(timezone.utc).isoformat()
    summary['exceptions'] = failures
    summary['endpoints'] = endpoints
    summary['status'] = 'PASS_MESSAGE_CONTRACT' if not failures and all(x['passed'] for x in summary['checks']) else 'FAIL'
    summary['received_count'] = len(received)
    save('received.json', [message_to_ordereddict(m) for m in received])
    save('summary.json', summary)
    print(json.dumps(clean(summary), ensure_ascii=False, indent=2))
raise SystemExit(0 if summary['status'] == 'PASS_MESSAGE_CONTRACT' else 1)
