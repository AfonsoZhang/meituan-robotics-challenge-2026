"""Correlate actual XML, logs and read-only observations; no kernel changes. Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import json,math,re,xml.etree.ElementTree as ET
raw=Path(__file__).resolve().parent;root=raw.parents[1];w=root/'outputs/moveit-watch-20261011'
event='sha-688d80d63ba2196e3c1753b69d18c1bfa30919b3';auto=w/'runs'/event
read=lambda p:json.loads(p.read_text())
counts=read(raw/'automatic-counts.json');source=read(raw/'source-review.json')
assert counts['cpp_total']==424 and counts['original_files_verified']==303 and counts['summary_complete']
ub=[]
for p in sorted((raw/'container/ubsan').rglob('*.gtest.xml')):
 x=ET.parse(p).getroot();cs=x.findall('.//testcase')
 assert cs and not x.findall('.//failure') and not x.findall('.//error') and not x.findall('.//skipped'),str(p)
 ub += [(str(p.relative_to(raw/'container/ubsan')),c.attrib['classname']+'.'+c.attrib['name']) for c in cs]
assert len(ub)==424 and len(set(p for p,c in ub))==22 and len(set(c for p,c in ub))==424
expected={c for x in counts['cpp_xml'] for c in x['cases']};assert {c for p,c in ub}==expected
instrumentation={}
for p in sorted((raw/'container/ubsan').glob('mtc_*_cpp/compile_commands.json')):
 cmds=read(p);assert cmds and all('-fsanitize=undefined' in x['command'] and '-fno-sanitize-recover=all' in x['command'] for x in cmds)
 instrumentation[p.parent.name]=len(cmds)
assert len(instrumentation)==6
for label in ['identity','consumer','ubsan','mismatch','cancel']:
 assert read(raw/'logs'/f'{label}.json')['exit_code']==0,label
assert read(raw/'logs/generic.json')['exit_code']==1
assert 'runtime error:' not in (raw/'logs/ubsan.log').read_text()

def generic(label):
 p=raw/'container'/label;s=read(p/'summary.json');assert s['empty_after'] and len(s['cases'])==1
 clean=s['shutdown'];assert clean['exit_code']==0 and not clean['escalated'] and not clean['already_exited'] and not clean['child_failures']
 c=s['cases'][0];mode=c['mode'];text=(p/(mode+'.log')).read_text()
 states=read(p/'joint-states.json');statuses=read(p/'action-status.json');a,b=c['sample_index_range'];samples=states[a:b]
 assert len(samples)>2 and len(set(x['stamp_ns'] for x in samples))==len(samples)
 assert all(y['stamp_ns']>x['stamp_ns'] for x,y in zip(samples,samples[1:]))
 for x in samples:
  assert len(x['names'])==len(x['positions'])==len(x['velocities'])==6 and len(set(x['names']))==6
  assert all(math.isfinite(v) for k in ['positions','velocities'] for v in x[k])
 values={k:int(v) for k,v in re.findall(r'\b(goals_sent|cancels_sent|feedback_samples|success|arrived|stop_confirmed|timed_out|status_unknown|fault_locked|error)=([0-9]+)',text)}
 uuid=re.search(r'UUID=([0-9a-f]{32})',text);uuid=uuid.group(1) if uuid else None
 observed=sorted({g['status'] for r in statuses for g in r['goals'] if g['uuid']==uuid})
 before=dict(zip(c['before']['names'],c['before']['positions']));after=dict(zip(c['after']['names'],c['after']['positions']))
 assert set(before)==set(after)
 delta={k:after[k]-before[k] for k in before}
 result={'mode':mode,'exit_code':c['exit_code'],'probe':values,'uuid':uuid,'observed_statuses':observed,
  'new_goal_uuids':c['new_goal_uuids'],'observation_has_action_client':s['observer_has_action_client'],
  'case_samples':len(samples),'total_run_samples':len(states),'distinct_case_stamps':len(set(x['stamp_ns'] for x in samples)),
  'max_stamp_gap_sec':max((y['stamp_ns']-x['stamp_ns'])/1e9 for x,y in zip(samples,samples[1:])),
  'max_receive_gap_sec':max(y['received_monotonic']-x['received_monotonic'] for x,y in zip(samples,samples[1:])),
  'final_named_delta_rad':delta,'observed_final_velocities':c['after']['velocities'],
  'source':s['source'],'shutdown':clean,'empty_after':s['empty_after'],'probe_log':str(p/(mode+'.log'))}
 assert not result['observation_has_action_client']
 if mode=='success':
  assert c['exit_code']==1 and values['error']==230 and values['goals_sent']==values['cancels_sent']==1
  assert values['status_unknown']==values['fault_locked']==1 and values['stop_confirmed']==values['success']==0
  assert 'runtime Fake/controller/state/graph proof lost' in text and observed==[2,4]
  result['observed_max_final_error_rad']=max(abs(v-.02) for v in delta.values());assert result['observed_max_final_error_rad']<.005
  result['verdict']='FAIL_PORT_RUNTIME_PROOF_LOST_DESPITE_OBSERVED_CONTROLLER_SUCCESS'
 elif mode=='mismatch':
  assert c['exit_code']==0 and values['goals_sent']==values['cancels_sent']==0 and not c['new_goal_uuids']
  assert 'trajectory start differs' in text and max(abs(v) for v in delta.values())==0
  result['verdict']='PASS_START_MISMATCH_REJECTED_WITHOUT_GOAL'
 else:
  assert c['exit_code']==0 and values['goals_sent']==values['cancels_sent']==1 and 5 in observed
  assert values['success']==values['status_unknown']==values['fault_locked']==0 and values['stop_confirmed']==1
  assert 'cancel initial stop_confirmed=0' in text
  result['verdict']='PASS_OWNED_CANCEL_TERMINAL_AND_STATIONARY'
 if uuid:
  assert c['new_goal_uuids']==[uuid]
  terminal=next(r['received_monotonic'] for r in statuses if any(g['uuid']==uuid and g['status'] in [4,5,6] for g in r['goals']))
  after_terminal=[x for x in samples if terminal<=x['received_monotonic']<=c['probe_finished_monotonic']]
  result['terminal_status_observed_monotonic']=terminal
  result['post_terminal_samples_before_probe_exit']=len(after_terminal)
  result['post_terminal_span_before_probe_exit_sec']=(after_terminal[-1]['received_monotonic']-after_terminal[0]['received_monotonic']) if len(after_terminal)>1 else 0
  result['post_terminal_stationary_evidence_is_external']='Independent subscription only; not proof of which callbacks/proofs the port processed.'
 return result

cases=[generic(x) for x in ['generic','mismatch','cancel']]
mv=read(auto/'container/moveit/result.json');assert mv['planning_execution']=='PASS' and mv['clean_shutdown']=='FAIL'
assert mv['execute']['status']==4 and mv['execute']['result']['error_code']['val']==1 and mv['max_error_rad']<.001
assert abs(max(abs(a-b) for a,b in zip(mv['actual_rad'],mv['target_rad']))-mv['max_error_rad'])<1e-14
assert any('exit code -11' in line for x in mv['shutdown'] for line in x['child_failures'])
assert all(not x['escalated'] for x in mv['shutdown'])
tasks=read(auto/'container/task-mock/summary.json');assert [x['result']['result']['error_code'] for x in tasks]==[220,510,220]
assert all(x['result']['status']==6 and x['result']['result']['completed_count']==0 for x in tasks)
assert tasks[2]['cancel_response']['return_code']==0
analysis={'recorded_at':datetime.now(timezone.utc).isoformat(),
 'verdict':'PARTIAL_PASS_TRAJECTORY_TESTS_UBSAN_CONSUMER; GENERIC_SUCCESS_FAILED_PROOF_LOST; MISMATCH_AND_CANCEL_PASS; FULL_FSM_NOT_ACCEPTED',
 'source':source,
 'automatic':{'status':'COMPLETED_WITH_FAILURES','summary_steps':25,'original_files_verified':303,
  'build_packages':14,'cpp_cases':424,'cpp_executables':22,'new_trajectory_cases':66,'python_cases':269,'e2e':15,'ros_wiring':6,
  'cpp_audit_failure':counts['old_fixed_audit'],'colcon_aggregate_note':'720 includes CTest wrappers and interface lint; not independent cases',
  'legacy_task':[{k:x[k] for k in ['case','accepted','result','child_failure','shutdown_escalated']} for x in tasks],
  'moveit':{k:v for k,v in mv.items() if k not in ['plan','tf']},
  'dependency_gaps':['ament_python rosdep key','driver docker.io','driver ros-jazzy-ros2-controllers-test-nodes'],
  'driver_test_aggregate':{'total':1104,'failures':279,'skipped':259,'scope':'lint/CTest wrappers, not independent physical-function cases'}},
 'supplement':{'installed_identity_files':4,'new_package_rosdep':'PASS','compiled_registration_verifier':'424 cases /22 executables PASS',
  'external_cmake_consumer':'PASS only exported package target, valid trajectory but disabled default, ready=false goals=0 cancels=0',
  'invalid_probe_arguments':'No-argument and invalid mode each return 2 before ROS init',
  'ubsan':{'cases':424,'executables':22,'compile_commands_instrumented':instrumentation,'all_case_identities_match_automatic':True,
   'colcon_aggregate':446,'scope':'Six C++ packages rebuilt; ROS/DDS/system libraries not instrumented; no TSan'},
  'generic_cases':cases,'generic_runs':3,'success_retries':0,
  'execution_sequence':'Initial combined harness stops after success failure; unexecuted mismatch and cancel run once each in fresh sequential driver domains 135 and 136. Domain 134 failure unchanged. No package/limits/timers modifications.',
  'failure_analysis':'One Goal reached controller SUCCEEDED/4 and all six independently observed joints reached +0.02 rad. Port returned STOP_UNKNOWN/230 with runtime Fake/controller/state/graph proof lost, auto-cancel count1, fault lock, no stop confirmation. Independent observer fresh stamps do not prove internal callbacks or health proofs; aggregate message does not identify failed predicate. No proven root cause or kernel repair.',
  'shutdown_note':'Each GenericSystem control child exits 0 without escalation; pal_statistics invalid-context publisher-thread errors still present in shutdown logs.',
  'joint_order_limit':'Delivered probe reverses names but all joints use identical increments; asymmetric reorder is covered by validator unit test, not independently proved by this GenericSystem motion.'},
 'not_completed':['Stable GenericSystem success path and diagnostic attribution of lost runtime proof',
  'Complete PickPlace/Task FSM runtime host and asynchronous cancel/stop bridge; direct existing FSM remains FAULT/520',
  'Default ROS Action servers still MockPlanner/AsyncMockMotion; no new FjtMotionPort runtime binding',
  'MoveItPlanner-to-FjtPort unified one-owner execution chain, contact/Cartesian primitives and real tool transitions',
  'Legacy B03/B05/B06 and Python Cancel stop confirmation; Safety repeated shutdown',
  'MoveIt -11 shutdown; driver dependency/lint and symbolic disabled limits; GenericSystem statistics shutdown errors',
  'Planner/scene/perception independent branch integration, calibrated TCP/TF/limits and physical inputs',
  'TSan, SDK licence/vendor checksums, NUC/physical hardware and real collision/contact validation'],
 'handoff':{'Sun_Jiaming':'Runtime proof loss/230 in Generic success and FSM asynchronous stop integration/520, default Action bindings and old B03/B05/B06; record locally, no kernel fix or external message',
  'Chang_Jianshuo':'Planner output contracts, calibrated scene/TF/tool coordinates; this branch has no planner dependency',
  'integration':'Preserve first failure and source boundaries, compare internal health diagnostics with external status and fresh JointState, track cleanup/limits/dependency evidence'},
 'source_modified':False,'formal_baseline_advanced':False,'local_merge_performed':False}
(raw/'supplement-analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'verdict':analysis['verdict'],'generic_cases':cases,'ubsan':analysis['supplement']['ubsan']},ensure_ascii=False,indent=2))
