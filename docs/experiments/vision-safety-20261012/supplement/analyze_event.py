"""Analyze actual vision safety acceptance evidence; OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import json, xml.etree.ElementTree as ET

raw = Path(__file__).resolve().parent
root = raw.parents[1]
c = raw / 'container'
source = raw / 'source'
auto = root / 'outputs/moveit-watch-20261011/runs/sha-e53c09fba0ac6082d97d53676413d6e285140dc1'
read = lambda p: json.loads(p.read_text())

def xml(name):
    cases = list(ET.parse(c / name).getroot().iter('testcase'))
    result = [{'class': v.get('classname'), 'name': v.get('name'),
               'result': 'FAIL' if v.find('failure') is not None else 'ERROR' if v.find('error') is not None
               else 'SKIP' if v.find('skipped') is not None else 'PASS',
               'details': [dict(tag=t.tag, attributes=t.attrib, text=t.text) for t in v]} for v in cases]
    return {'file': name, 'counts': dict(Counter(v['result'] for v in result)),
            'by_class': dict(Counter(v['class'] for v in result)), 'cases': result}

unit = xml('adapter-tests.xml')
public = xml('public-vision-tests.xml')
assert unit['counts'] == {'PASS': 53}
assert public['counts'] == {'PASS': 62, 'SKIP': 1}
default = read(c / 'replay-default/summary.json')
assert default['received_count'] == 4 and default['status'] == 'PASS_MESSAGE_CONTRACT'
assert default['completion_log_seen'] and default['existing_python_predicate_counterexample']['predicate_accepts']
assert default['shutdown'][0]['exit_code'] == 0 and not default['shutdown'][0]['escalated']
assert all(v['passed'] for v in default['checks']) and len(default['negative_inputs']) == 2
controlled = {}
records = [json.loads(v) for v in (source / 'src/mtc_vision_adapter/examples/synthetic.jsonl').read_text().splitlines() if v]
relabelled = [json.loads(v) for v in (c / 'replay-labelled.jsonl').read_text().splitlines() if v]
assert all(dict(a, mode='replay') == b for a, b in zip(records, relabelled)) and len(records) == len(relabelled) == 4
for name in ['replay-synthetic', 'replay-labelled']:
    result = read(c / name / 'ros_results.json')
    assert result['received_frames'] == 4 and result['array_lengths'] == [0, 4, 4, 4]
    assert all(result['exact_fixture_matches']) and result['subscriber_cleanup_complete']
    assert result['publisher_exit'] == 0 and not result['replay_nodes_remaining']
    assert result['publisher_created_qos'] == [dict(reliability='RELIABLE', history='KEEP_LAST', depth=5, durability='VOLATILE')]
    assert all(v['compatibility'] == 'OK' and v['history'] == 'UNKNOWN' and v['depth'] == 0 for v in result['qos'])
    assert [v['live'] for v in result['motion_rejections']] == ['EMPTY', 'RING_INVALID', 'RING_INVALID', 'RING_INVALID']
    assert all(v['offline'] == 'REPLAY_NOT_MOTION_INPUT' for v in result['motion_rejections'])
    log = (c / name / 'ros_publisher.log').read_text()
    assert 'replay complete' in log and 'Traceback' not in log and 'already called' not in log
    controlled[name] = result
assert 'already called' not in (c / 'replay-default/publisher.log').read_text()
install = (raw / 'logs/install-offline.log').read_text()
assert 'No broken requirements found.' in install and 'setuptools==80.9.0' not in (raw / 'requirements-review.txt').read_text()
assert 'setuptools==68.1.2' in (c / 'vision-python-freeze.txt').read_text()
task_cpp = (source / 'src/mtc_ros2_action_cpp/src/task_server.cpp').read_text()
task_py = (source / 'src/mtc_task/mtc_task/task_executor.py').read_text()
assert 'MockPerception scene' in task_cpp and 'create_subscription' not in task_cpp and 'create_subscription' not in task_py
assert 'motion_rejection' not in task_cpp and 'motion_rejection' not in task_py
process = (source / 'src/mtc_vision_adapter/test/ros_replay_validation.py').read_text()
publisher = (source / 'src/mtc_vision_adapter/mtc_vision_adapter/publisher.py').read_text()
assert 'Node.create_publisher=observed' in process and 'get_subscription_count' in process
assert 'get_subscription_count' not in publisher and 'rclpy.try_shutdown()' in publisher
command = next((auto / 'container/test-log').glob('test_*/mtc_vision_adapter/command.log')).read_text()
assert '/usr/bin/python3 -m unittest -v' in command
task = read(auto / 'container/task-mock/summary.json')
assert [t['result']['result']['error_code'] for t in task] == [220, 510, 520]
assert all(t['result']['status'] == 6 and t['result']['result']['completed_count'] == 0 for t in task)
moveit = read(auto / 'container/moveit/result.json')
assert moveit['planning_execution'] == 'PASS' and moveit['clean_shutdown'] == 'FAIL'
assert moveit['execute']['status'] == 4 and moveit['execute']['result']['error_code']['val'] == 1
assert moveit['distinct_joint_stamps'] == 206 and any('exit code -11' in x for x in moveit['shutdown'][0]['child_failures'])
assert '1104 tests, 0 errors, 279 failures, 259 skipped' in (auto / 'logs/driver-test-results.log').read_text()
steps = {p.stem: read(p) for p in (raw / 'logs').glob('*.json') if 'label' in read(p)}
assert len(steps) == 7 and all(v['exit_code'] == 0 for v in steps.values())
cleanup = read(raw / 'cleanup.json')
assert all(not v['state']['Running'] and not v['state']['OOMKilled'] for v in cleanup['containers'])
result = {
    'at': datetime.now(timezone.utc).isoformat(),
    'verdict': 'PARTIAL_PASS_VISION_SAFETY_AND_CLEANUP; BLOCKED_FULL_FSM_AND_DEFAULT_TEST_COLLECTION',
    'automatic': {'counts': read(raw / 'automatic-counts.json'),
        'failed_steps': [v['name'] for v in read(auto / 'summary.json')['steps'] if v['exit_code']],
        'adapter_test_collection': 'FAIL exit 5: colcon actually invokes unittest -v, zero tests. setup.py has no pytest tests_require; XML aggregate 652 excludes this empty package.',
        'old_cpp_audit': 'FAIL expected 16 executables, actual 20; no missing, unexpected, duplicate or bad cases. Delivered Action verifier PASS 358/20.',
        'dependency_gaps': ['rosdep ament_python definition', 'docker.io', 'ros-jazzy-ros2-controllers-test-nodes'],
        'driver_test_aggregate': {'tests': 1104, 'errors': 0, 'failures': 279, 'skipped': 259, 'includes_wrappers_and_lint': True},
        'legacy_python': task, 'moveit': moveit},
    'supplement': {'new_adapter_tests': unit, 'public_vision_tests': public,
        'default_replay': default, 'controlled_replay': controlled, 'step_results': steps,
        'offline_environment': read(c / 'vision-python-versions.json'),
        'dependencies': 'Previously verified cached wheels only; no downloads. Separate system-site-packages venv, base setuptools 68.1.2, editable installs and pip check PASS.',
        'count_scope': '53 new adapter tests and 62 public vision cases, with one private evidence skip. Earlier 27 adapter tests are included in those 62, not additional.',
        'instrumentation_scope': 'Delivered validator monkeypatches publisher creation to wait up to 20 s for subscriber, before starting a 2 s timer, and reads the created publisher QoS. This barrier is absent from production publisher. Only layout symlink added, no tracked source edits.',
        'input_scope': 'Original four synthetic records plus the same synthetic records relabelled replay only; messages/capture timestamps unchanged. Neither run is real camera data.',
        'startup_limit': 'Default 1 s invocation passed once with 4/4; no subscriber-barrier change in production. Prior default 1/4 failure is preserved and not closed by one success.',
        'shutdown': 'Default plus both instrumented runs observed replay complete then SIGINT exit 0, without escalation. Completion cancels timer but publisher stays spinning until SIGINT; not natural process exit.',
        'tf_scope': 'Local tf2 Buffer only: missing TF and latest-only transform reject; transform at capture time permits. No live TF listener or calibrated transform; callback supplied by caller, helper trusts exact True and does not itself transform poses.',
        'consumer_boundary': 'Helper not integrated into FSM. C++ still MockPerception; no real topic consumer in Python. Artificial true-ring/NaN/old-stamp static predicate counterexample still accepted, never published or sent as Goal. IDL lacks offline/live provenance mode.',
        'new_supplement_action_goals': 0, 'cameras_opened': False, 'source_changed': False},
    'not_completed': ['Default colcon pytest registration', 'Reliable default replay startup across discovery timings',
        'Real perception topic consumer and fail-closed provenance/time/TF/finite-pose gates in FSM',
        'Trusted runtime TF validator/pose transformation and ROS/Core time contract',
        'Live camera, private 22-frame evidence/CAD assets, physical color/ID/XYZ/Yaw/ring/calibration validation',
        'Complete FSM/Planner/FJT/tool/Cancel loop, old Python B03/B05/B06 and shutdown defects',
        'Driver dependencies/lint/limits, MoveIt clean shutdown, SDK licence/vendor checksum, NUC/physical robot'],
    'handoff': {'孙浩然': 'pytest registration and default replay readiness; live adapter/provenance delivery',
        '孙嘉明': 'Actual perception consumer, provenance/time/finite/TF gate and existing FSM/Action/Cancel failures; no kernel repairs performed',
        '韩明赫': 'Trusted measured TF and capture clock contract',
        '系统集成': 'Local evidence and regression/cleanup tracking; no external messages, merge, baseline advancement or extra monitor'},
    'cleanup': cleanup}
(raw / 'supplement-analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'adapter': unit['counts'], 'by_class': unit['by_class'], 'public': public['counts'],
    'default_received': default['received_count'], 'controlled': list(controlled), 'status': result['verdict']}, ensure_ascii=False, indent=2))
