"""Summarize actual immutable outputs; no ROS execution or source modification."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

raw = Path(__file__).resolve().parent
runtime = raw / 'runtime'
load = lambda path: json.loads(path.read_text())
def xml_counts(base, pattern):
    cases = [case for p in base.rglob(pattern) for case in ET.parse(p).getroot().iter('testcase')]
    return {'cases': len(cases), 'failed': sum(c.find('failure') is not None for c in cases),
            'errors': sum(c.find('error') is not None for c in cases),
            'skipped': sum(c.find('skipped') is not None for c in cases)}

cpp = []
for directory in ['cpp-mock-v2', 'cpp-mock']:
    for row in load(runtime / directory / 'summary.json'):
        if row['status'] != 'PASS':
            continue
        goals = []
        for g in row['goals']:
            item = {'goal': g['goal'], 'accepted': g['accepted'], 'uuid': bytes(g['goal_uuid']).hex(),
                    'feedback_count': len(g['feedback']), 'terminal': g.get('terminal'),
                    'cancel_response': g.get('cancel_response'),
                    'times': {k: v for k, v in g.items() if k.endswith('_monotonic')}, 'children': []}
            for child in g.get('child_terminal_results', []):
                item['children'].append({'uuid': bytes(child['uuid']).hex(), 'terminal': child['response'],
                                        'received_monotonic': child['received_monotonic']})
            goals.append(item)
        cpp.append({'case': row['case'], 'status': row['status'], 'goals': goals,
                    'shutdown': row['shutdown'], 'nodes_after_shutdown': row['nodes_after_shutdown'],
                    'pickplace_send_goal_clients': row.get('pickplace_send_goal_clients'),
                    'topic_qos': row.get('topic_qos'),
                    'evidence': f'runtime/{directory}/{row["case"]}/result.json'})

repeat = load(runtime / 'repeat-fjt/summary.json')
extra_log = (raw / 'logs/python-extra.log').read_text()
assert 'E2E RESULT: PASS 15 / FAIL 0 / SKIP 0' in extra_log
assert '6 passed' in extra_log and 'Ran 54 tests' in extra_log and extra_log.rstrip().endswith('OK')
steps = []
for p in sorted((raw / 'meta').glob('*.json')):
    d = load(p)
    if isinstance(d, dict) and 'argv' in d and 'name' in d:
        steps.append({k: d.get(k) for k in ['name', 'started_at', 'ended_at', 'exit_code', 'timeout_seconds']})
data = {'status': 'PARTIAL_NOT_ACCEPTED_AS_COMPLETE_SYSTEM',
        'main_sha': 'b4185155383541e1a4161587c4049a162f74b36d',
        'pr8_sha': '7da43228d602a6b23571bfc599d69529ef7bea23',
        'formal_pin': '1d940f7c5f12561fed6641457c0b4b630a282b05',
        'ordinary_cpp': xml_counts(runtime / 'artifacts/main-build', '*.gtest.xml'),
        'ordinary_python': xml_counts(runtime / 'artifacts/main-build', 'pytest.xml'),
        'ubsan_cpp': xml_counts(runtime / 'artifacts/main-ubsan-build', '*.gtest.xml'),
        'extra_python': {'offline_e2e': 15, 'ros_wiring': 6, 'calibration': 54,
                         'evidence': 'host-logs/python-extra.log'},
        'repeat': {'planned_processes': 40, 'completed_processes': len(repeat['processes']),
                   'identities': 10, **xml_counts(runtime / 'repeat-fjt', '*.xml'),
                   'status': repeat['status'], 'stop_on_first_failure': True,
                   'failed_case': 'FjtAction.LateGoalResponseAfterFaultRetainsOriginalSession'},
        'cpp_process_cases': cpp,
        'harness_failures': {'initial_cpp_observer': [
            {k: x.get(k) for k in ['case', 'exception', 'status', 'shutdown']}
            for x in load(runtime / 'cpp-mock/summary.json') if x['status'] != 'PASS'],
            'explanation': 'Before any Task Goal in the two affected cases, Action graph counted feedback/status-only observer as a client. Corrected external observer verifies actual send_goal service endpoints and reruns only those two unexecuted cases; original results retained.',
            'fresh_source_setup': 'Git dubious ownership exit128 before build; per-process safe.directory used only for /main-source, no permission/capability/global-config change.'},
        'python_mock': [{k: x.get(k) for k in ['case', 'status', 'exception', 'result',
                          'cancel_response', 'launch_exit_code', 'shutdown_escalated', 'child_failure']}
                        for x in load(runtime / 'python-mock/summary.json')],
        'native_gate': load(runtime / 'native-gate/summary.json'),
        'moveit': {k: v for k, v in load(runtime / 'moveit/result.json').items() if k not in ['plan', 'tf']},
        'pr8_c1': load(raw / 'pr8-runtime/c1/summary.json'),
        'pr8_postcheck': load(raw / 'pr8-runtime/postcheck.json'),
        'pr8_direct_cleanup': load(raw / 'pr8-runtime/cleanup-only/summary.json'),
        'steps': steps,
        'source_comparisons': load(raw / 'meta/source-comparisons.json'),
        'handoff': load(raw / 'meta/M1-handoff.json'),
        'main_cleanup': load(raw / 'meta/main-stopped.json'),
        'pr8_cleanup': load(raw / 'meta/pr8-stopped.json'),
        'container_ownership': load(raw / 'meta/final-containers.json'),
        'not_run': ['new Phase2C/planning/perception/Gazebo candidates',
                    'new browser UI acceptance (PR8 code unchanged)',
                    'new driver lint suite (old failures retained)', 'TSan', 'complete FSM', 'NUC', 'physical hardware']}
(raw / 'summary.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: data[k] for k in ['ordinary_cpp', 'ordinary_python', 'ubsan_cpp', 'repeat']}, indent=2))
