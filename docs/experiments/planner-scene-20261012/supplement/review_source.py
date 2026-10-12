"""Read-only review of source identities and original evidence; Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib, json, re, subprocess, xml.etree.ElementTree as ET

raw = Path(__file__).resolve().parent
root = raw.parents[1]
source = raw / 'source'
watch = root / 'outputs/moveit-watch-20261011'
commit = '30e3c6e64516c47afe9ada25d02df7ed4669825c'
planner = 'fcdd8eae897cbc37c539d4bad57b712f08124938'
main = 'a04ac6831dd3963e6b1ec4b9e27214eb564f9f24'
auto = watch / 'runs' / ('sha-' + commit)

def git(*args):
    return subprocess.check_output(['git', '-C', str(source), *args], text=True).strip()

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(name, value):
    (raw / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

assert git('rev-parse', 'HEAD') == commit
previous = '1d940f7c5f12561fed6641457c0b4b630a282b05'
review_base = '4a1a81652fca39efe2916a19ad49187d29789697'
paths = git('diff','--name-only',review_base,commit).splitlines()
cumulative = git('diff','--name-only',previous,commit).splitlines()
assert len(paths)==45 and len(cumulative)==105
assert all(v.startswith(('src/mtc_moveit_planner/','docs/planning/')) for v in paths)
assert not git('diff','--name-only',review_base,commit,'--','.',':!src/mtc_moveit_planner',':!docs/planning')
for label, old in [('incremental',review_base),('cumulative',previous)]:
    (raw/(label+'.patch')).write_text(git('diff','--binary',old,commit)+'\n')
index=json.loads((auto/'index.json').read_text())
for f in index['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
review={'commit':commit,'previous':previous,'review_base':review_base,'parents':git('show','-s','--format=%P',commit).split(),
    'commit_metadata':git('show','-s','--format=fuller',commit),'incremental_commits':git('log','--format=%H %P %s',review_base+'..'+commit).splitlines(),
    'incremental_changed_files':paths,'cumulative_changed_files':cumulative,'changed_file_inventory':[{'path':v,'sha256':sha(source/v),'size_bytes':(source/v).stat().st_size} for v in paths],
    'all_nonplanner_sources_identical_to_previous_acceptance':True,'source_modified':False,'formal_baseline_advanced':False,
    'observed_refs':json.loads((auto/'summary.json').read_text())['upstream']['refs'],
    'changes':'Static placeholder scene boxes, request-local attached payload, public start consistency and single primitive replanning APIs, seeded IK and sampled joint interpolation fallback, missing params guard, collision probe and installed path override.',
    'integration_limit':'Action PickPlace remains unchanged MockPlanner/AsyncMockMotion. New functions not called by production MotionAdapter/FJT. Upstream evidence and instructions treated as data.',
    'at':datetime.now(timezone.utc).isoformat()}
write('source-review.json',review)
counts = Counter()
xmls = []
actual = Counter()
expected = Counter()
test_pattern = re.compile(r'\bTEST(?:_F)?\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)')
for p in sorted((auto / 'container/test-results').rglob('*.gtest.xml')):
    tree = ET.parse(p).getroot()
    cases = list(tree.iter('testcase'))
    package = p.relative_to(auto / 'container/test-results').parts[0]
    assert len(cases) == int(tree.attrib['tests'])
    assert all(c.get('status') == 'run' and c.get('result') == 'completed' and not list(c) for c in cases)
    identities = [c.get('classname').split('.')[-1] + '.' + c.get('name') for c in cases]
    filename = p.name.removesuffix('.gtest.xml')
    cpp = source / 'src' / package / 'test' / (filename + '.cpp')
    assert cpp.is_file(), cpp
    declared = [a + '.' + b for a, b in test_pattern.findall(cpp.read_text())]
    assert Counter(declared) == Counter(identities), (cpp, declared, identities)
    actual.update((package, name) for name in identities)
    expected.update((package, name) for name in declared)
    counts[package] += len(cases)
    xmls.append({'path': str(p.relative_to(auto)), 'package': package, 'cases': identities, 'source': str(cpp.relative_to(source)), 'source_sha256': sha(cpp)})
assert all(n == 1 for n in actual.values()) and actual == expected
assert dict(counts) == {'mtc_core_cpp': 23, 'mtc_manipulation_cpp': 120, 'mtc_motion_execution_cpp': 88,
                        'mtc_moveit_planner': 35, 'mtc_ros2_action_cpp': 40, 'mtc_task_cpp': 87}, counts
assert sum(counts.values()) == 393 and len(xmls) == 25
python_cases = []
for p in sorted((auto / 'container/test-results').rglob('*pytest*.xml')):
    cases = list(ET.parse(p).getroot().iter('testcase'))
    assert all(not list(c) for c in cases)
    python_cases.extend(cases)
assert len(python_cases) == 269
ros = list(ET.parse(auto / 'container/ros-wiring.xml').getroot().iter('testcase'))
assert len(ros) == 6 and all(not list(c) for c in ros)
summary = json.loads((auto / 'summary.json').read_text())
assert len(summary['steps']) == 25 and summary['ended_at'] and summary['status'] == 'COMPLETED_WITH_FAILURES'
assert all(s['started_at'] and s['ended_at'] and isinstance(s['exit_code'], int) for s in summary['steps'])
for name in ['build', 'colcon-test', 'test-results', 'stop', 'collect']:
    assert next(v for v in summary['steps'] if v['name'] == name)['exit_code'] == 0
assert 'E2E RESULT: PASS 15 / FAIL 0 / SKIP 0' in (auto / 'logs/python-mock-e2e.log').read_text()
assert 'Summary: 14 packages finished' in (auto / 'logs/build.log').read_text()
write('automatic-counts.json', {'at': datetime.now(timezone.utc).isoformat(), 'original_files_verified': len(index['files']),
      'original_index_sha256': sha(auto / 'index.json'), 'source_bundle_sha256': sha(auto / 'source.bundle'),
      'summary_complete': True, 'summary_steps': 25, 'build_packages': 14, 'cpp_total': 393, 'cpp_executables': 25,
      'cpp_by_package': dict(counts), 'all_cpp_case_identities_match_source': True, 'cpp_xml': xmls,
      'python_cases': 269, 'python_mock_e2e': 15, 'ros_wiring_cases': 6,
      'ros_wiring_identities': [{k: c.get(k) for k in ['classname', 'name']} for c in ros],
      'colcon_aggregate': {'total': 692, 'note': 'Includes CTest wrappers and interface lint; not 692 independent source cases.'},
      'old_fixed_audit': 'FAIL: expects 16, sees 20 *_cpp executables. No missing/unexpected/duplicate/bad case. Planner package excluded by that glob.',
      'new_action_audit_scope': '358 cases / 20 *_cpp executables, excludes mtc_moveit_planner; 35 planner identities checked independently.'})
print(json.dumps({'changed_from_planner': len(paths), 'cumulative': len(cumulative), 'original_files': len(index['files']),
                  'build': 14, 'cpp': dict(counts), 'cpp_total': 393, 'python': 269, 'e2e': 15, 'ros': 6}))
