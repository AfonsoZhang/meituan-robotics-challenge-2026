"""Read-only calibration increment and original test/evidence audit. Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET
raw=Path(__file__).resolve().parent;root=raw.parents[1];source=raw/'source';watch=root/'outputs/moveit-watch-20261011'
commit='06ab689f25e87dcebf9fd04fdd581ec4755206f6';reviewed='f7eaa2c0d2887aeada4fd635112c63c237962ff7';previous='1d940f7c5f12561fed6641457c0b4b630a282b05';auto=watch/'runs'/('sha-'+commit)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(source),*a],text=True).strip()
def write(n,v):(raw/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert git('rev-parse','HEAD')==commit and not git('status','--short')
paths=git('diff','--name-only',reviewed,commit).splitlines();cumulative=git('diff','--name-only',previous,commit).splitlines()
assert len(paths)==38 and len(cumulative)==119
assert all(x.startswith('A\t') for x in git('diff','--name-status',reviewed,commit).splitlines())
assert all(p=='TF_AND_CALIBRATION_HANDOFF.md' or p.startswith(('config/calibration/','docs/calibration/','examples/calibration/','scripts/calibration/','tests/calibration/')) for p in paths)
assert not git('diff','--name-only',reviewed,commit,'--','src','docs/planning','README.md','README_FSM.md')
for name,base in [('incremental',reviewed),('cumulative',previous)]: (raw/(name+'.patch')).write_text(git('diff','--binary',base,commit)+'\n')
prior=root/'docs/experiments/planner-main-20261012';pidx=json.loads((prior/'index.json').read_text())
assert sha(prior/'index.json')=='a6641cd712b8538b6dbc5a848359aa483e295e5e76a1c04ccd5453406d35ac9e'
for f in pidx['files']:assert sha(prior/f['path'])==f['sha256'],f['path']
receipt=json.loads((watch/'wake'/('sha-'+reviewed)/'receipt.json').read_text());assert sha(Path(receipt['report']))==receipt['report_sha256']
summary=json.loads((auto/'summary.json').read_text());assert summary['environment']==json.loads((prior/'automatic/summary.json').read_text())['environment']
binding=(source/'src/mtc_ros2_action_cpp/src/pick_place_server.cpp').read_text()
assert 'std::make_shared<MockPlanner>' in binding and 'std::make_shared<AsyncMockMotion>' in binding
assert not (source/'src/mtc_trajectory_execution_cpp').exists() and not (source/'src/mtc_vision_adapter').exists()
index=json.loads((auto/'index.json').read_text());assert len(index['files'])==305
for f in index['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
review={'at':datetime.now(timezone.utc).isoformat(),'commit':commit,'previous':previous,'review_base':reviewed,
 'parents':git('show','-s','--format=%P',commit).split(),'commit_metadata':git('show','-s','--format=fuller',commit),
 'incremental_commits':git('log','--format=%H %P %s',reviewed+'..'+commit).splitlines(),
 'incremental_changed_files':paths,'cumulative_changed_files':cumulative,
 'changed_file_inventory':[{'path':p,'size_bytes':(source/p).stat().st_size,'sha256':sha(source/p)} for p in paths],
 'all_existing_sources_identical_to_reviewed_main':True,'src_tree':git('rev-parse',commit+':src'),
 'previous_src_tree':git('rev-parse',reviewed+':src'),'previous_frozen_files_verified':len(pidx['files']),
 'previous_frozen_index_sha256':sha(prior/'index.json'),'previous_signed_report_sha256':receipt['report_sha256'],
 'automatic_environment_and_harness_identical_to_previous':True,'observed_refs':summary['upstream']['refs'],
 'binding':{'planner':'MockPlanner','motion':'AsyncMockMotion','calibration_contract_consumed':False},
 'other_branches_present':{'new_trajectory':False,'new_vision':False,'new_planning_scene':False},
 'changes':'38 added offline calibration/TF/TCP geometry, input contract, mount estimate, model-log audit, examples, 54 tests, documentation and upstream generated evidence. No existing runtime source/config changes.',
 'scope_warning':'Upstream claimed V1 and flange camera installation confirmations are upstream handoff premises, not new user decisions in this project. Real calibration stays UNKNOWN; no end-effector selection recorded.',
 'integration_limit':'No ROS TF listener, hand-eye solver, TF publisher or planner/FSM consumer; diagnostic JSON motion_authorized=false. Existing planner uses latest TF and slot position without independently specified placement orientation.',
 'source_modified':False,'formal_baseline_advanced':False,'local_merge_performed':False}
assert review['src_tree']==review['previous_src_tree'];write('source-review.json',review)
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
                        'mtc_moveit_planner': 29, 'mtc_ros2_action_cpp': 40, 'mtc_task_cpp': 87}, counts
assert sum(counts.values()) == 387 and len(xmls) == 24
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
      'summary_complete': True, 'summary_steps': 25, 'build_packages': 14, 'cpp_total': 387, 'cpp_executables': 24,
      'cpp_by_package': dict(counts), 'all_cpp_case_identities_match_source': True, 'cpp_xml': xmls,
      'python_cases': 269, 'python_mock_e2e': 15, 'ros_wiring_cases': 6,
      'ros_wiring_identities': [{k: c.get(k) for k in ['classname', 'name']} for c in ros],
      'colcon_aggregate': {'total': 685, 'note': 'Includes CTest wrappers and interface lint; not 685 independent source cases.'},
      'old_fixed_audit': 'FAIL: expects 16, sees 20 *_cpp executables. No missing/unexpected/duplicate/bad case. Planner package excluded by that glob.',
      'new_action_audit_scope': '358 cases / 20 *_cpp executables, excludes mtc_moveit_planner; 29 planner identities checked independently.'})
print('PASS source increment38/cumulative119; original305; CPP387/24; Python269/E2E15/ROS6')
