"""Read-only Phase 2B change, registered test identity and evidence audit. Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET
raw=Path(__file__).resolve().parent;root=raw.parents[1];source=raw/'source';w=root/'outputs/moveit-watch-20261011'
commit='688d80d63ba2196e3c1753b69d18c1bfa30919b3';reviewed='a04ac6831dd3963e6b1ec4b9e27214eb564f9f24';previous='1d940f7c5f12561fed6641457c0b4b630a282b05';auto=w/'runs'/('sha-'+commit)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(source),*a],text=True).strip()
def write(n,v):(raw/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert git('rev-parse','HEAD')==commit and not git('status','--short')
paths=git('diff','--name-only',reviewed,commit).splitlines();cumulative=git('diff','--name-only',previous,commit).splitlines()
assert len(paths)==13 and len(cumulative)==41
assert all(v.startswith('src/mtc_trajectory_execution_cpp/') or v=='docs/migration/PHASE2B_TRAJECTORY_EXECUTION_REPORT.md' for v in paths)
assert not git('diff','--name-only',reviewed,commit,'--','.',':!src/mtc_trajectory_execution_cpp',':!docs/migration/PHASE2B_TRAJECTORY_EXECUTION_REPORT.md')
assert all(v.startswith('A\t') for v in git('diff','--name-status',reviewed,commit).splitlines())
for label,base in [('incremental',reviewed),('cumulative',previous)]: (raw/(label+'.patch')).write_text(git('diff','--binary',base,commit)+'\n')
binding=(source/'src/mtc_ros2_action_cpp/src/pick_place_server.cpp').read_text()
assert 'std::make_shared<MockPlanner>' in binding and 'std::make_shared<AsyncMockMotion>' in binding
assert not (source/'src/mtc_moveit_planner').exists() and not (source/'src/mtc_vision_adapter').exists()
review={'at':datetime.now(timezone.utc).isoformat(),'commit':commit,'previous':previous,'review_base':reviewed,
 'parents':git('show','-s','--format=%P',commit).split(),'commit_metadata':git('show','-s','--format=fuller',commit),
 'incremental_commits':git('log','--format=%H %P %s',reviewed+'..'+commit).splitlines(),
 'incremental_changed_files':paths,'cumulative_changed_files':cumulative,
 'changed_file_inventory':[{'path':p,'size_bytes':(source/p).stat().st_size,'sha256':sha(source/p)} for p in paths],
 'all_existing_sources_identical_to_reviewed_main':True,'planner_and_vision_packages_present':False,
 'binding':{'planner':'MockPlanner','motion':'AsyncMockMotion','new_fjt_port_in_default_servers':False},
 'changes':'New standalone Fake-only asynchronous FjtMotionPort, full trajectory validation/conversion, 30+36 tests, compiled-registration verifier and explicit three-mode GenericSystem probe; new report only, no existing file changes.',
 'integration_limit':'Real transport tests inject only first PickPlace motion; direct FSM cancellation deliberately remains FAULT/520 while asynchronous stop is pending. No runtime host or stop bridge, no Planner dependency, no contact/Cartesian execution.',
 'source_modified':False,'formal_baseline_advanced':False,'local_merge_performed':False,
 'observed_refs':json.loads((auto/'summary.json').read_text())['upstream']['refs']}
write('source-review.json',review)
index=json.loads((auto/'index.json').read_text())
for f in index['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
counts=Counter();actual=Counter();expected=Counter();xmls=[]
rx=re.compile(r'\bTEST(?:_F)?\s*\(\s*(\w+)\s*,\s*(\w+)\s*\)')
for p in sorted((auto/'container/test-results').rglob('*.gtest.xml')):
 rt=ET.parse(p).getroot();cases=list(rt.iter('testcase'));pkg=p.relative_to(auto/'container/test-results').parts[0]
 assert len(cases)==int(rt.attrib['tests']) and all(c.get('status')=='run' and c.get('result')=='completed' and not list(c) for c in cases)
 identities=[c.get('classname').split('.')[-1]+'.'+c.get('name') for c in cases]
 cpp=source/'src'/pkg/'test'/(p.name.removesuffix('.gtest.xml')+'.cpp');text=cpp.read_text()
 declared=[a+'.'+b for a,b in rx.findall(text)]
 if pkg=='mtc_trajectory_execution_cpp' and cpp.name=='test_trajectory_validator.cpp':
  assert declared.count('TrajectoryValidator.Name')==1
  declared.remove('TrajectoryValidator.Name')
  macro_names=re.findall(r'^INVALID_TEST\((\w+),',text,re.M);assert len(macro_names)==22
  declared += ['TrajectoryValidator.'+n for n in macro_names]
 assert Counter(identities)==Counter(declared),(cpp,identities,declared)
 actual.update((pkg,n) for n in identities);expected.update((pkg,n) for n in declared);counts[pkg]+=len(cases)
 xmls.append({'path':str(p.relative_to(auto)),'package':pkg,'cases':identities,'source':str(cpp.relative_to(source)),'source_sha256':sha(cpp)})
assert actual==expected and all(n==1 for n in actual.values())
assert dict(counts)=={'mtc_core_cpp':23,'mtc_manipulation_cpp':120,'mtc_motion_execution_cpp':88,'mtc_ros2_action_cpp':40,'mtc_task_cpp':87,'mtc_trajectory_execution_cpp':66}
assert sum(counts.values())==424 and len(xmls)==22
py=[]
for p in sorted((auto/'container/test-results').rglob('*pytest*.xml')):
 cases=list(ET.parse(p).getroot().iter('testcase'));assert all(not list(c) for c in cases);py.extend(cases)
assert len(py)==269
ros=list(ET.parse(auto/'container/ros-wiring.xml').getroot().iter('testcase'));assert len(ros)==6 and all(not list(c) for c in ros)
summary=json.loads((auto/'summary.json').read_text());assert len(summary['steps'])==25 and summary['ended_at'] and summary['status']=='COMPLETED_WITH_FAILURES'
assert all(v['started_at'] and v['ended_at'] and isinstance(v['exit_code'],int) for v in summary['steps'])
for n in ['build','colcon-test','test-results','stop','collect']:assert next(v for v in summary['steps'] if v['name']==n)['exit_code']==0
assert 'E2E RESULT: PASS 15 / FAIL 0 / SKIP 0' in (auto/'logs/python-mock-e2e.log').read_text()
assert 'Summary: 14 packages finished' in (auto/'logs/build.log').read_text()
write('automatic-counts.json',{'at':datetime.now(timezone.utc).isoformat(),'original_files_verified':len(index['files']),
 'original_index_sha256':sha(auto/'index.json'),'source_bundle_sha256':sha(auto/'source.bundle'),'summary_complete':True,
 'summary_steps':25,'build_packages':14,'cpp_total':424,'cpp_executables':22,'cpp_by_package':dict(counts),
 'cpp_xml':xmls,'all_cpp_case_identities_match_source':True,'macro_expansion':'22 INVALID_TEST calls replace definition placeholder TrajectoryValidator.Name; also checked against compiled registrations by upstream verifier',
 'python_cases':269,'python_mock_e2e':15,'ros_wiring_cases':6,'colcon_aggregate':{'total':720,'note':'Includes CTest wrappers and interface lint; not 720 independent functional cases'},
 'old_fixed_audit':'FAIL: expects 16 versus 22 *_cpp executables; parses macro placeholder TrajectoryValidator.Name and misses 22 actual INVALID_TEST expansions. No duplicate or failed cases.',
 'new_verifier_scope':'All six C++ packages, 424/22; baseline 358 retained, +66 new; compiled registrations compared with XML'})
print(json.dumps({'incremental_files':len(paths),'cumulative_files':len(cumulative),'original_files':len(index['files']),'cpp':dict(counts),'cpp_total':424,'python':269,'e2e':15,'ros':6}))
