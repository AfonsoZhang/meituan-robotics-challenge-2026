"""Analyze collected immutable runtime evidence; OpenAI Codex assisted."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import xml.etree.ElementTree as ET

raw = Path(__file__).resolve().parent
root = raw.parents[1]
source = raw / 'source'
c = raw / 'container'
commit = 'dc76a0bf0a43f9110f3d24cfa38a2b3478f48dcd'
auto = root / 'outputs/moveit-watch-20261011/runs' / ('sha-' + commit)
read = lambda p: json.loads(p.read_text())

def xml(name):
    cases = []
    for v in ET.parse(c / name).getroot().iter('testcase'):
        status = 'ERROR' if v.find('error') is not None else 'FAIL' if v.find('failure') is not None else 'SKIP' if v.find('skipped') is not None else 'PASS'
        cases.append({'class': v.get('classname'), 'name': v.get('name'), 'status': status,
                      'details': [{'tag': t.tag, 'attributes': t.attrib, 'text': t.text} for t in v]})
    return {'file': name, 'counts': dict(Counter(x['status'] for x in cases)),
            'by_class': dict(Counter(x['class'] for x in cases)), 'cases': cases}

adapter = xml('adapter-tests.xml')
public = xml('public-vision-tests.xml')
assert adapter['counts'] == {'PASS': 57}, adapter['counts']
assert public['counts'] == {'PASS': 80, 'SKIP': 1}, public['counts']
processes = {}
for mode in ['synthetic', 'replay']:
    for exit_mode in ['natural', 'sigint']:
        name = mode + '-' + exit_mode
        result = read(c / 'installed-processes' / name / 'ros_results.json')
        expected = 4 if exit_mode == 'natural' else 2
        assert result['passed'] and result['publisher_exit'] == 0
        assert result['received_frames'] == expected and result['array_lengths'] == [0, 4, 4, 4][:expected]
        assert result['signal_sent'] == (exit_mode == 'sigint')
        assert all(result['exact_fixture_matches']) and result['subscriber_cleanup_complete']
        assert not result['replay_nodes_remaining']
        assert result['created_qos'] == 'RELIABLE KEEP_LAST(5) VOLATILE'
        assert result['discovered_qos'] and all(q['compatibility'] == 'OK' and q['reliability'] == 'RELIABLE' and q['durability'] == 'VOLATILE' for q in result['discovered_qos'])
        log = (c / 'installed-processes' / name / 'ros_publisher.log').read_text()
        assert ('replay complete' in log) == (exit_mode == 'natural')
        assert 'Traceback' not in log and 'already called' not in log
        result['publisher_log_frame_lines'] = [x for x in log.splitlines() if 'frame=' in x]
        processes[name] = result

no_subscriber = read(c / 'no-subscriber/results.json')
assert len(no_subscriber) == 2 and all(r['passed'] for r in no_subscriber)
assert [r['exit_code'] for r in no_subscriber] == [0, 1]
assert [r['published_log_count'] for r in no_subscriber] == [4, 0]
assert all(not r['signals'] and not r['remaining_nodes'] for r in no_subscriber)
inputs = read(c / 'private-entrypoint-inputs.json')
assert all(not r['exists'] for r in inputs['required_private_inputs'])
for name in ['private-v41', 'private-v42']:
    assert read(raw / 'logs' / (name + '.json'))['exit_code'] == 1
    assert 'FileNotFoundError' in (raw / 'logs' / (name + '.log')).read_text()
    assert 'outputs/live_rgbd_integration/v4' in (raw / 'logs' / (name + '.log')).read_text()
steps = {p.stem: read(p) for p in (raw / 'logs').glob('*.json') if 'label' in read(p)}
assert len(steps) == 8
assert all(v['exit_code'] == (1 if k in ('private-v41', 'private-v42') else 0) for k, v in steps.items())
assert 'No broken requirements found.' in (raw / 'logs/install-offline.log').read_text()
assert 'setuptools==68.1.2' in (c / 'vision-python-freeze.txt').read_text()

publisher = (source / 'src/mtc_vision_adapter/mtc_vision_adapter/publisher.py').read_text()
validator = (source / 'src/mtc_vision_adapter/test/ros_replay_validation.py').read_text()
assert 'Node.create_publisher=' not in validator and 'wait_for_subscriber_s:=15.0' in validator
assert "declare_parameter('wait_for_subscriber_s',0.0)" in publisher
assert 'wait_for_all_acked(Duration(seconds=2.0))' in publisher
assert 'while rclpy.ok() and not complete' in publisher
task_cpp = (source / 'src/mtc_ros2_action_cpp/src/task_server.cpp').read_text()
task_py = (source / 'src/mtc_task/mtc_task/task_executor.py').read_text()
assert 'MockPerception scene' in task_cpp
assert all('create_subscription' not in s and 'motion_rejection' not in s for s in (task_cpp, task_py))
collection = next((auto / 'container/test-log').glob('test_*/mtc_vision_adapter/command.log')).read_text()
assert '/usr/bin/python3 -m unittest -v' in collection
task = read(auto / 'container/task-mock/summary.json')
assert [t['result']['result']['error_code'] for t in task] == [220, 510, 520]
assert all(t['result']['status'] == 6 and t['result']['result']['completed_count'] == 0 for t in task)
moveit = read(auto / 'container/moveit/result.json')
assert moveit['planning_execution'] == 'PASS' and moveit['clean_shutdown'] == 'FAIL'
assert moveit['execute']['status'] == 4 and moveit['execute']['result']['error_code']['val'] == 1
assert any('exit code -11' in t for t in moveit['shutdown'][0]['child_failures'])
assert '1104 tests, 0 errors, 279 failures, 259 skipped' in (auto / 'logs/driver-test-results.log').read_text()
cleanup = read(raw / 'cleanup.json')
assert all(not v['state']['Running'] and not v['state']['OOMKilled'] for v in cleanup['containers'])

result = {
    'at': datetime.now(timezone.utc).isoformat(), 'commit': commit,
    'verdict': 'PARTIAL_PASS_INSTALLED_REPLAY_NATURAL_EXIT_AND_SIGINT; PRIVATE_BENCHMARK_AND_FULL_FSM_NOT_VERIFIED',
    'automatic': {'counts': read(raw / 'automatic-counts.json'),
        'failed_steps': [s['name'] for s in read(auto / 'summary.json')['steps'] if s['exit_code']],
        'adapter_test_collection': 'FAIL exit 5: unittest -v collects zero; setup.py has no pytest tests_require; aggregate 652 does not cover the adapter.',
        'old_cpp_audit': 'FAIL expects 16 executables, sees 20; individual source identities match 358 tests; delivered Action verifier passed.',
        'dependency_gaps': ['ament_python rosdep definition', 'docker.io', 'ros-jazzy-ros2-controllers-test-nodes'],
        'driver_test_aggregate': {'tests': 1104, 'errors': 0, 'failures': 279, 'skipped': 259, 'includes_wrappers_and_lint': True},
        'legacy_python': task, 'moveit': moveit},
    'supplement': {'adapter_suite': adapter, 'public_vision_suite': public,
        'installed_processes': processes, 'no_subscriber': no_subscriber,
        'private_input_inventory': inputs, 'step_results': steps,
        'offline_environment': read(c / 'vision-python-versions.json'),
        'test_count_scope': '57 = earlier 53 adapter tests plus four installed-process cases; 80 public passes = earlier 62 plus 18 new cases. One private 22-frame evidence test skipped. Earlier 27 adapter-core cases already part of public suite.',
        'process_scope': 'Direct installed replay_publisher, no monkeypatch. Exact upstream test uses period 0.5 s and optional subscriber wait 15 s, domains 191-194. Natural cases receive 4/4 and exit without signal; SIGINT cases receive 2/4 and do not claim complete delivery.',
        'input_scope': 'Same four synthetic frames; replay case changes mode and timestamp_source metadata only; original messages and capture stamps retained. No actual recording or camera.',
        'default_scope': 'Default wait=0/period=1 with zero subscribers exits 0 after four publishes; no delivery claim. Positive wait=2/period=0.25 with zero subscribers exits 1 with explicit TimeoutError before any frame and leaves no node.',
        'ack_limit': 'Successful RELIABLE middleware acknowledgment does not establish application/FSM acceptance. Actual final-ack timeout branch was not fault-injected.',
        'graph_identity_limit': 'All four first discovered endpoint snapshots report _NODE_NAME_UNKNOWN_, history UNKNOWN and depth 0. Topic type/QoS compatibility are observed; named graph identity is not established by these snapshots. Executable/source identity and process exit are independently verified; final docker top contains only keeper.',
        'startup_limit': 'Optional wait now exists in publisher and is exercised by four installed-process cases; default remains zero and does not guarantee a subscriber or close previous default 1/4 loss/reliability gap.',
        'private_entrypoints': 'Both delivered V4.1 benchmark and V4.2 audit attempted exactly; exit 1 creating missing parent output directory, before data/frame processing. Private recordings, prior audit/paired/before results and CAD assets absent; BLOCKED, no performance or real accuracy claims.',
        'vision_algorithm_scope': 'New separable/ray plane-height equivalence tests, visual confirmation candidates, stale CAD clearing and diagnostic aliases pass on synthetic inputs. CONFIRMED_OBJECT is visual hypothesis; body/ring validity remains false; ROS clock not mapped.',
        'safety_integration': 'No changed FSM/IDL/Action sources; C++ Task still MockPerception and neither Task consumes topic/helper. Prior static predicate counterexample remains in earlier signed evidence, not re-executed or promoted to a real Goal.',
        'source_changed': False, 'new_supplement_action_goals': 0, 'cameras_opened': False},
    'not_completed': ['Default colcon pytest collection', 'Default zero-wait subscriber delivery guarantee and broader replay reliability', 'Real final-ack timeout failure injection', 'Private V4.1 paired benchmark and V4.2 saved-recording audit', 'Real D435i/USB/cross-host transport and actual measured XYZ/Yaw/ring accuracy', 'Actual FSM perception consumption and trusted capture-time TF/clock checks', 'Old Python B03/B05/B06 and Safety cleanup', 'MoveIt shutdown, dependencies/driver lint, SDK license/vendor checksum, NUC and real hardware', 'Deferred 08:00 C++ Bringup/Web UI task remains scheduled, not executed in this event'],
    'handoff': {'孙浩然': 'colcon pytest registration, optional discovery wait SOP/default reliability, private benchmark inputs and live perception delivery', '孙嘉明': 'FSM perception consumer/source-time-finite-TF rejection, old Action/Cancel/kernel blockers; no kernel repair here', '韩明赫': 'Measured trusted TF/calibration and ROS/Core capture-time contracts', '系统集成与验收': 'Preserve original failures, exact source boundaries and isolated clean shutdown; execute later authorized integration only after deadline and monitor drain'},
    'cleanup': cleanup,
}
(raw / 'supplement-analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verdict': result['verdict'], 'adapter': adapter['counts'], 'public': public['counts'],
                  'processes': {k: {'frames': v['received_frames'], 'signal': v['signal_sent'], 'exit': v['publisher_exit']} for k, v in processes.items()}},
                 ensure_ascii=False, indent=2))
