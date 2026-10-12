"""Audit executed evidence, not real-camera accuracy; OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
import json, math, xml.etree.ElementTree as ET
raw = Path(__file__).resolve().parent
c = raw / 'container'
read = lambda p: json.loads(p.read_text())

def xml(name):
    cases = list(ET.parse(c / name).getroot().iter('testcase'))
    records = [{'class': a.get('classname'), 'name': a.get('name'), 'time_s': a.get('time'),
                'result': 'ERROR' if a.find('error') is not None else 'FAIL' if a.find('failure') is not None else 'SKIP' if a.find('skipped') is not None else 'PASS',
                'details': [dict(tag=x.tag, attributes=x.attrib, text=x.text) for x in a]} for a in cases]
    return {'path': name, 'collected': len(records), **{status.lower(): sum(v['result'] == status for v in records) for status in ['PASS', 'SKIP', 'FAIL', 'ERROR']}, 'cases': records}

tests = {name: xml(name) for name in ['adapter-original.xml', 'core-original.xml', 'vision-suite.xml', 'vision-suite-compatible.xml']}
assert tests['adapter-original.xml']['pass'] == 27 and tests['adapter-original.xml']['skip'] == 1
for name in ['vision-suite.xml', 'vision-suite-compatible.xml']:
    assert tests[name]['pass'] == 62 and tests[name]['skip'] == 1 and tests[name]['error'] == tests[name]['fail'] == 0
assert tests['core-original.xml']['error'] == 1
default = read(c / 'ros-replay/summary.json')
diag = read(c / 'ros-replay-wait5/summary.json')
assert default['status'] == 'FAIL' and default['received_count'] == 1
assert diag['status'] == 'PASS_MESSAGE_CONTRACT' and diag['received_count'] == 4
assert all(v['passed'] for v in diag['checks'])
assert len(default['negative_inputs']) == 2 and all(v['explicit_rejection'] and not v['timed_out'] for v in default['negative_inputs'])
for result in [default, diag]:
    assert result['existing_python_predicate_counterexample']['predicate_accepts']
    assert result['endpoints'][0]['history'] == 'UNKNOWN' and result['endpoints'][0]['depth'] == 0
    assert result['shutdown'][0]['exit_code'] == 1 and not result['shutdown'][0]['escalated']
for folder in ['ros-replay', 'ros-replay-wait5']:
    text = (c / folder / 'publisher.log').read_text()
    assert all('frame=' + str(i) + ' ' in text for i in range(4)) and 'replay complete' in text
    assert 'rcl_shutdown already called' in text
records = [json.loads(x) for x in (c / 'synthetic/synthetic.jsonl').read_text().splitlines() if x]
assert len(records) == 16
colors = set(); total = 0; ids = set()
for record in records:
    assert record['mode'] == 'synthetic' and record['body_pose_valid'] is False and record['ring_pose_valid'] is False
    assert record['candidate_only'] and record['motion_rejection'] == 'REPLAY_NOT_MOTION_INPUT'
    detections = record['message']['detections']; stamp = record['message']['header']
    assert len({v['object_id'] for v in detections}) == len(detections)
    for d in detections:
        total += 1; colors.add(d['color']); ids.add(d['object_id'])
        assert d['ring_pose_valid'] is False
        for name in ['body_pose', 'ring_pose']:
            assert d[name]['header'] == stamp
            assert all(v is None for group in d[name]['pose'].values() for v in group.values())
assert colors == {1,2,3,4} and total == 50 and len(ids) == 5
synthetic = read(c / 'synthetic/summary.json')
assert synthetic['replay']['frames'] == 0 and synthetic['synthetic']['rejected_for_motion'] == 16
assets = read(c / 'source-and-assets.json'); assert not assets['tracked_diff'] and not any(assets['optional_assets_present'].values())
versions = read(c / 'final-environment.json')
assert versions['setuptools'] == '68.1.2' and versions['distribution']['mtc-vision-core'] == '0.4.0'
assert 'No broken requirements found.' in (raw / 'logs/install-compatible.log').read_text()
for name in ['rgbd-help.txt', 'handheld-help.txt']:
    assert 'usage:' in (c / 'entrypoints' / name).read_text().lower()
source = raw / 'source'
task_cpp = (source / 'src/mtc_ros2_action_cpp/src/task_server.cpp').read_text()
task_py = (source / 'src/mtc_task/mtc_task/task_executor.py').read_text()
assert 'MockPerception scene' in task_cpp and 'create_subscription' not in task_cpp and 'create_subscription' not in task_py
received = read(c / 'ros-replay/received.json')
summary = {
    'at': datetime.now(timezone.utc).isoformat(), 'tests': tests,
    'test_count_scope': '62 public cases includes the earlier 27 adapter cases; one private 22-frame evidence case skipped. Two environment passes are not cumulative and not the original private 215-test suite.',
    'default_ros': default, 'diagnostic_ros': diag,
    'default_received_stamps': [r['header']['stamp'] for r in received],
    'diagnostic_only_change': 'period_s 1 to 5 seconds and independent ROS domain 129 to 130; input bytes, capture timestamps, installed publisher and subscriber logic unchanged; no algorithm change',
    'qos_scope': 'Native discovery confirms RELIABLE and VOLATILE; KEEP_LAST(5) is source configuration only, graph reports UNKNOWN history/depth 0. No claim of runtime depth confirmation.',
    'startup_analysis': 'Original publisher logged all four frames, receiver got one late record. Longer cadence received all four. Consistent with discovery/readiness timing in this environment; no matching barrier in publisher. Exact cause not established; reliable/volatile does not recover pre-match data.',
    'shutdown_analysis': 'Both publisher runs complete replay but remain spinning; controlled SIGINT leads to KeyboardInterrupt then rcl_shutdown already called, exit 1, without escalation.',
    'consumer_boundary': 'Native false-ring/NaN candidates are rejected by existing Python static predicate. Artificial true-ring/NaN/stale candidate accepted by that predicate; never published and no Goal. No current C++ or Python topic consumer delivered; local motion_rejection helper is not an integrated gate. IDL carries no mode/body_pose_valid provenance fields.',
    'synthetic': {'frames': 16, 'detections': total, 'color_enums': sorted(colors), 'unique_ids': sorted(ids), 'motion_rejected_frames': 16, 'summary': synthetic,
                  'real_replay_frames': 0, 'physical_accuracy': 'NOT MEASURED; strict JSON nulls, all ring invalid, uncalibrated replay frame'},
    'entrypoints': {'live_rgbd_preview_help': 'PASS', 'live_realsense_handheld_help': 'PASS', 'devices_opened': False},
    'dependency_setup': {'base_core_test': 'ERROR missing cv2; base pytest 7.4.4 below new >=8 declaration',
        'first_venv': 'Pinned setuptools 80.9.0 conflicts with colcon-core <80 and legacy editable adapter script_dir option; preserved. This toolchain selection belongs to acceptance harness.',
        'pep517_diagnostic': 'Adapter editable installation succeeds; pip check still fails on setuptools/colcon conflict',
        'final': 'Reuse existing Ubuntu setuptools 68.1.2, both README editable paths and pip check PASS; other primary dependencies pinned in offline requirements',
        'final_environment': versions, 'source_and_assets': assets,
        'offline_wheels': '23 binaries downloaded on host from PyPI and copied in; SHA/metadata recorded; no container network, no wheels frozen'},
    'configuration_provenance_limit': 'competition.yaml explicit_official/map_calibrated are upstream labels only; not newly verified rules/physical calibration. Private CAD source and third-party migration lineage/licensing need owner confirmation. Root MIT / adapter Apache-2.0 declarations retained.',
    'not_completed': ['Default replay reliable startup delivery and clean shutdown', 'ROS package test registration (colcon exits 5 with zero tests)',
        'Live camera ROS publisher, actual FSM consumer, replay/age/finite-pose/frame gates and calibrated TF',
        'True four-color accuracy/physical identity/XYZ/Yaw/ring pose, private 22-frame replay and CAD preview/Python3.12 backend',
        'Complete vision to FSM/MoveIt/FJT/tool/cancel pipeline, NUC and physical robot'],
    'no_action_goal_or_camera_or_algorithm_change': True}
(raw / 'supplement-analysis.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'vision_tests': '62 PASS / 1 SKIP', 'default_ros': default['status'], 'diagnostic_ros': diag['status'],
    'synthetic': summary['synthetic'], 'source_unchanged': True}, ensure_ascii=False, indent=2))
