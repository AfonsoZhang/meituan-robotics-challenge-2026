"""Correlate original failure and isolated supplement without hiding either. Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,re,xml.etree.ElementTree as ET
raw=Path(__file__).resolve().parent;root=raw.parents[1];event='sha-681bb64bfb8cd482d1e78950cef4cfe395b21bff';auto=root/'outputs/moveit-watch-20261011/runs'/event
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
counts=read(raw/'automatic-counts.json');source=read(raw/'source-review.json')
def identities(p):
 rt=ET.parse(p).getroot();cases=list(rt.iter('testcase'))
 assert cases and all(not list(c) and c.get('status')=='run' and c.get('result')=='completed' for c in cases),p
 return [c.get('classname').split('.')[-1]+'.'+c.get('name') for c in cases]
regular=identities(raw/'container/ordinary-full/full.xml');expected={'FjtAction.'+n for n in source['fjt_registered_source']}
assert len(regular)==61 and set(regular)==expected
registered=(raw/'container/ordinary-full/registration.txt').read_text();assert {'FjtAction.'+x.strip() for x in registered.splitlines() if x.startswith('  ')}==expected
repeat=read(raw/'container/ordinary-full/full.json');assert repeat['exit_code']==0 and not repeat['timed_out'] and repeat['process_reaped']
original_ids={v for f in counts['cpp_xml'] for v in f['passed_cases']};assert len(original_ids)==417 and not original_ids & expected
ubsan=[];instrumentation={}
for p in sorted((raw/'container/ubsan').rglob('*.gtest.xml')):ubsan.extend(identities(p))
assert len(ubsan)==478 and set(ubsan)==original_ids|expected
for p in sorted((raw/'container/ubsan').glob('*/compile_commands.json')):
 if p.parent.name=='mtc_interfaces':continue
 cmds=read(p);assert cmds and all('-fsanitize=undefined' in c['command'] and '-fno-sanitize-recover=all' in c['command'] for c in cmds),p
 instrumentation[p.parent.name]=len(cmds)
assert len(instrumentation)==7 and 'runtime error:' not in (raw/'logs/ubsan.log').read_text()
assert read(raw/'logs/ubsan.json')['exit_code']==0
first=read(raw/'container/native-gate/summary.json');native=read(raw/'container/topology-gate/summary.json')
assert first['status']=='FAIL' and first['exception']=='AssertionError()' and first['native_success']['exit_code']==1
assert first['empty_after'] and len(first['shutdown'])==1 and first['shutdown'][0]['exit_code']==0 and not first['shutdown'][0]['child_failures'] and not first['shutdown'][0]['escalated']
nt=(raw/'container/native-gate/native-success.log').read_text()
assert 'FJT servers=1 clients=1 direct_trajectory_publishers=0 foreign_active_goals=0 status_received=0 status_fresh=0 unknown_active_goals=0 ready=0' in nt
assert 'BLOCKED: GenericSystem/active controller/fresh state/exclusive graph proof unavailable' in nt
nj=read(raw/'container/native-gate/joint-states.json');ns=read(raw/'container/native-gate/action-status.json')
assert len(nj)>2 and not ns and all(abs(x)<1e-10 for v in nj for x in v['positions'])
assert native['status']=='PASS_COEXISTENCE_BLOCKED' and native['empty_after'] and native['all_joints_zero']
assert native['topology']['exit_code']==2 and native['status_messages']==0 and not native['fjt_goal_uuids']
assert len(native['controller_only_graph']['clients'])==0 and len(native['moveit_graph']['clients'])==1
assert len(native['topology']['coexistence_graph'][0]['clients'])==2
assert first['driver_files_unchanged'] and native['driver_files_unchanged'] and first['driver_files_count']==native['driver_files_count']
# Derived combination of two serial runs; neither original summary is changed.
native['native_success']=first['native_success'];native['native_domain155']=first
native['native_distinct_joint_stamps']=len({x['stamp_ns'] for x in nj})
native['combined_distinct_joint_stamps']=len({x['stamp_ns'] for x in nj}|{x['stamp_ns'] for x in read(raw/'container/topology-gate/joint-states.json')})
native['derived_interpretation']='PASS_NATIVE_AND_COEXISTENCE_BLOCKED; first observer assertion FAIL retained separately'
native['observer_error']='First observer expected2 instead of delivered success-preflight exception exit1; exited and cleaned before MoveIt. A separate topology-only run covers the unexecuted branch; native probe not repeated.'
qos=(raw/'container/native-gate/status-qos.log').read_text();assert 'RELIABLE' in qos and 'TRANSIENT_LOCAL' in qos
assert read(raw/'logs/original-verifier.json')['exit_code']==1
assert 'test_fjt_action.gtest.missing_result' in (raw/'logs/original-verifier.log').read_text()
mv=read(auto/'container/moveit/result.json');tasks=read(auto/'container/task-mock/summary.json')
assert mv['planning_execution']=='PASS' and mv['clean_shutdown']=='FAIL' and mv['execute']['status']==4
assert [t['result']['result']['error_code'] for t in tasks]==[220,510,520]
assert all(t['result']['status']==6 and t['result']['result']['completed_count']==0 for t in tasks)
analysis={'recorded_at':datetime.now(timezone.utc).isoformat(),
 'verdict':'PARTIAL: ORIGINAL_FJT_SUITE_TIMEOUT_UNRESOLVED; UNCHANGED_61_CASE_RETRY_PASS; UBSAN_478_PASS; NATIVE_GENERIC_AND_MOVEIT_COEXISTENCE_BLOCKED; FULL_FSM_NOT_ACCEPTED',
 'source':source,'automatic':{'counts':counts,'legacy_python_task':tasks,'moveit':{k:v for k,v in mv.items() if k not in ['plan','tf']},
 'dependency_gaps':['ament_python rosdep key','driver docker.io','driver ros-jazzy-ros2-controllers-test-nodes'],
 'driver_aggregate':{'total':1104,'failures':279,'skipped':259,'scope':'Lint/wrappers, not functional or physical tests'},
 'new_delivered_verifier_on_original':'FAIL missing_result; preserves original XML, not substituted with retry'},
 'supplement':{'ordinary_retry':{'cases':61,'elapsed_seconds':repeat['elapsed_seconds'],'all_case_names':regular,'new_cases':source['new_tests'],'source_and_binary_unchanged':True,
 'interpretation':'Retry passes; original 6 textual passes followed by DuplicateCancelOnlyOneBackendCall120s timeout remains FAIL. Combined417 original XML+61retry represents coverage, NOT a passing original478-run.'},
 'ubsan':{'cases':478,'executables':26,'compile_commands_instrumented':instrumentation,'source_registration_xml_verified':True,
 'scope':'All seven C++ packages rebuilt; ROS/DDS/MoveIt system libraries not instrumented. TSan NOT RUN. Passing run does not rule out deadlock/race.'},
 'native_gate':native,'native_status_qos':'One publisher RELIABLE/TRANSIENT_LOCAL; zero messages observed; new Port subscriber RELIABLE/VOLATILE from source',
 'native_goal_count':0,'native_other_modes':'NOT_RUN prerequisite status contract missing; not prewarmed, heartbeat injected, gate weakened or old four-mode PASS reused',
 'installed_identity_files':4,'new_package_rosdep':'PASS','invalid_arguments':'Two argument-negative invocations each exit2 before ROS initialization'},
 'not_completed':['Intermittent 120s DuplicateCancelOnlyOneBackendCall timeout root cause and bounded lifecycle behavior','Native GenericSystem initial live Status and ongoing trusted evidence contract / exclusive owner','Native mismatch/cancel/identity execution and complete Task/PickPlace/FJT chain','Default MoveIt second execution client; planning timebase vs FJT start time; async FSM cancel/stop host','Old Python220/510/520, MoveIt shutdown-11, driver dependencies/lint, SDK licensing/vendor checksums, TSan, NUC and real robot'],
 'handoff':{'Sun_Jiaming':'Original LastTest120s timeout, missing-result XML, unchanged61-case retry and478UBSan contradiction; diagnose test fixture versus FjtMotionPort lifecycle/locking with bounded repro. Own native Status/exclusive execution contract and asynchronous cancellation; do not infer cancellation complete from ACK.',
 'integration':'Freeze evidence, preserve original failure, no source/kernel edits or merge. 08:00 C++ Mock/UI work remains deferred.',
 'planning_coordination':'DefaultMoveIt second FJT client and generated-versus-scheduled stamp contract remain open; no Planner modifications or relaxed limits.'},
 'source_modified':False,'formal_baseline_advanced':False,'local_merge_performed':False}
(raw/'supplement-analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'verdict':analysis['verdict'],'ordinary_retry':len(regular),'ubsan':len(ubsan),'native':native['derived_interpretation'],'native_cleanup':native['clean_shutdown']},ensure_ascii=False))
