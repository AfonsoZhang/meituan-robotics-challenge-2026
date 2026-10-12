"""Correlate recorded results, retaining negative outcomes. OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,re,xml.etree.ElementTree as ET
raw=Path(__file__).resolve().parent;root=raw.parents[1];w=root/'outputs/moveit-watch-20261011';event='sha-45f497ce3444e255463faf41f7b736aa9ad07d7b';auto=w/'runs'/event
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
counts=read(raw/'automatic-counts.json');source=read(raw/'source-review.json')
assert counts['cpp_total']==463 and counts['original_files_verified']==317 and counts['summary_complete']
ub=[];instrumentation={}
for p in sorted((raw/'container/ubsan').rglob('*.gtest.xml')):
 x=ET.parse(p).getroot();cs=x.findall('.//testcase');assert cs and not x.findall('.//failure') and not x.findall('.//error') and not x.findall('.//skipped')
 rel=p.relative_to(raw/'container/ubsan');pkg=rel.parts[0]
 assert all(c.attrib['classname'].startswith(pkg+'.') and c.attrib['status']=='run' and c.attrib['result']=='completed' for c in cs)
 ub += [(str(rel),c.attrib['classname'][len(pkg)+1:]+'.'+c.attrib['name']) for c in cs]
assert len(ub)==463 and len({p for p,c in ub})==26 and len({c for p,c in ub})==463
assert {c for p,c in ub}=={c for x in counts['cpp_xml'] for c in x['cases']}
for p in sorted((raw/'container/ubsan').glob('*/compile_commands.json')):
 if p.parent.name=='mtc_interfaces':continue
 cmds=read(p);assert cmds and all('-fsanitize=undefined' in x['command'] and '-fno-sanitize-recover=all' in x['command'] for x in cmds)
 instrumentation[p.parent.name]=len(cmds)
assert len(instrumentation)==7
for label in ['identity','ubsan','consumer-plan']:assert read(raw/'logs'/f'{label}.json')['exit_code']==0,label
assert 'runtime error:' not in (raw/'logs/ubsan.log').read_text()
def generic(mode):
 p=raw/'container'/('generic-'+mode);s=read(p/'summary.json');assert s['empty_after'] and len(s['cases'])==1
 clean=s['shutdown'];assert clean['exit_code']==0 and not clean['escalated'] and not clean['already_exited'] and not clean['child_failures']
 c=s['cases'][0];text=(p/(mode+'.log')).read_text();states=read(p/'joint-states.json');statuses=read(p/'action-status.json');lo,hi=c['sample_index_range'];samples=states[lo:hi]
 assert len(samples)>2 and all(y['stamp_ns']>x['stamp_ns'] for x,y in zip(samples,samples[1:]))
 assert all(len(x['names'])==len(set(x['names']))==len(x['positions'])==len(x['velocities'])==6 and all(math.isfinite(v) for k in ['positions','velocities'] for v in x[k]) for x in samples)
 values={k:int(v) for k,v in re.findall(r'\b(goals_sent|cancels_sent|feedback_samples|success|arrived|stop_confirmed|timed_out|status_unknown|fault_locked|error)=([0-9]+)',text)}
 match=re.search(r'UUID=([0-9a-f]{32})',text);uuid=match.group(1) if match else None
 observed=sorted({g['status'] for r in statuses for g in r['goals'] if g['uuid']==uuid})
 before=dict(zip(c['before']['names'],c['before']['positions']));after=dict(zip(c['after']['names'],c['after']['positions']));delta={k:after[k]-before[k] for k in before}
 row={'mode':mode,'exit_code':c['exit_code'],'verdict':s['status'],'probe':values,'uuid':uuid,'observed_statuses':observed,'new_goal_uuids':c['new_goal_uuids'],'observer_has_action_client':s['observer_has_action_client'],'distinct_case_stamps':len({x['stamp_ns'] for x in samples}),'total_run_samples':len(states),'final_named_delta_rad':delta,'observed_final_velocities':c['after']['velocities'],'max_stamp_gap_sec':max((y['stamp_ns']-x['stamp_ns'])/1e9 for x,y in zip(samples,samples[1:])),'max_receive_gap_sec':max(y['received_monotonic']-x['received_monotonic'] for x,y in zip(samples,samples[1:])),'shutdown':clean,'empty_after':True}
 assert not row['observer_has_action_client']
 if c['exit_code']==0:
  assert f'PASS: GenericSystem {mode}' in text
  if mode=='mismatch':assert values['goals_sent']==values['cancels_sent']==0 and not c['new_goal_uuids'] and 'trajectory start differs' in text and all(v==0 for v in delta.values())
  else:
   assert values['goals_sent']==1 and values['stop_confirmed']==1 and values['status_unknown']==values['fault_locked']==0
   assert c['new_goal_uuids']==[uuid] and (5 if mode=='cancel' else 4) in observed
   if mode=='cancel':assert values['cancels_sent']==1 and 'cancel initial stop_confirmed=0' in text
   else:
    assert values['cancels_sent']==0 and values['success']==1
    row['max_observed_target_error_rad']=max(abs(v-.02) for v in delta.values());assert row['max_observed_target_error_rad']<.005
   if mode=='identity':
    assert 'identity reread + 3 changed-content refusals; goals_sent=1 cancels_sent=0' in text
    row['cached_read_and_three_changed_content_refusals']=True
 else:row['failure_log']=text
 if uuid:
  terms=[r['received_monotonic'] for r in statuses if any(g['uuid']==uuid and g['status'] in [4,5,6] for g in r['goals'])]
  if terms:
   settled=[x for x in samples if terms[0]<=x['received_monotonic']<=c['probe_finished_monotonic']]
   row['post_terminal_samples_before_exit']=len(settled)
   row['post_terminal_span_sec']=settled[-1]['received_monotonic']-settled[0]['received_monotonic'] if len(settled)>1 else 0
   row['post_terminal_max_velocity']=max((abs(v) for x in settled for v in x['velocities']),default=None)
   row['external_observer_scope']='Subscription evidence only; does not establish port-internal health predicates.'
 return row
cases=[generic(m) for m in ['success','mismatch','cancel','identity']]
top=read(raw/'container/topology-plan/summary.json');assert top['empty_after'];assert top['status']=='PASS_BLOCKED_TOPOLOGY_AND_PLAN_ONLY'
assert top['topology']['exit_code']==2 and len(top['topology']['coexistence_graph'][0]['clients'])==2
assert not top['fjt_goal_uuids'] and top['observer_action_clients']==0 and top['all_joints_zero']
consumer=read(raw/'container/plan-consumer/input.json');ct=(raw/'logs/consumer-plan.log').read_text()
assert 'Before diagnostic IDs: accepted=0' in ct and 'No Node, Action Client, Goal, stamp substitution or capability widening.' in ct
consumer['before_id_rejected']=True;consumer['after_id_accepted']=bool(re.search('After diagnostic IDs: accepted=1',ct));consumer['after_id_error']=re.search(r'After diagnostic IDs: accepted=[01] error=(.*?) timeout_ms=',ct).group(1)
mv=read(auto/'container/moveit/result.json');assert mv['planning_execution']=='PASS' and mv['execute']['status']==4 and mv['execute']['result']['error_code']['val']==1 and mv['clean_shutdown']=='FAIL'
assert mv['max_error_rad']<.001 and any('exit code -11' in line for r in mv['shutdown'] for line in r['child_failures'])
tasks=read(auto/'container/task-mock/summary.json');assert [x['result']['result']['error_code'] for x in tasks]==[220,510,520]
assert all(x['result']['status']==6 and x['result']['result']['completed_count']==0 for x in tasks) and tasks[2]['cancel_response']['return_code']==0
all_generic=all(x['exit_code']==0 for x in cases)
analysis={'recorded_at':datetime.now(timezone.utc).isoformat(),'verdict':('PASS_COMMAND_IDENTITY_463_UBSAN_AND_FOUR_GENERIC_CASES' if all_generic else 'PARTIAL_PASS_IDENTITY_463_UBSAN_WITH_GENERIC_FAILURE')+'; DEFAULT_MOVEIT_FJT_TOPOLOGY_BLOCKED; FULL_FSM_NOT_ACCEPTED; SHUTDOWN_FAILURES_RETAINED',
 'source':source,'automatic':{'status':'COMPLETED_WITH_FAILURES','summary_steps':25,'original_files_verified':317,'build_packages':15,'cpp_cases':463,'cpp_executables':26,'python_cases':269,'e2e':15,'ros_wiring':6,'cpp_audit_failure':counts['old_fixed_audit'],'colcon_aggregate':763,'colcon_aggregate_note':'Includes wrappers/lint, not independent cases','legacy_task':[{k:x[k] for k in ['case','accepted','result','child_failure','shutdown_escalated']} for x in tasks],'moveit':{k:v for k,v in mv.items() if k not in ['plan','tf']},'dependency_gaps':['ament_python rosdep key','driver docker.io','driver ros-jazzy-ros2-controllers-test-nodes'],'driver_test_aggregate':{'total':1104,'failures':279,'skipped':259,'scope':'lint/wrappers, not physical-function tests'}},
 'supplement':{'installed_identity_files':4,'new_package_rosdep':'PASS','compiled_registration_verifier':'463/26 PASS; original424 retained plus10 new and29 merged','invalid_probe_arguments':'No argument and invalid mode each return2 before ROS init','ubsan':{'cases':463,'executables':26,'compile_commands_instrumented':instrumentation,'all_case_identities_match_automatic':True,'scope':'Seven C++ packages including Planner rebuilt; ROS/DDS/MoveIt system libraries not instrumented; TSan NOT RUN'},'generic_cases':cases,'generic_runs':4,'retries':0,'execution_sequence':'Each delivered mode run once in its own fresh driver/domain, serial and unchanged. Independent read-only witness; no source/config/limits/timers adjustments.','topology_and_plan':top,'plan_consumer':consumer,'previous_230':'688d80d original success failure preserved. Current source changes command identity only, not health predicates; a new passing sample cannot establish a fix or reliability.','scope_note':'Equal joint increments do not independently validate asymmetric name reordering. Command cache is historical; no current stop proof or complete FSM.'},
 'not_completed':['Default MoveIt/FJT one-owner execution: default move_group adds an executable FJT client; no planning-only launch delivered','Planner generation/observation stamp vs ROS scheduled-start contract; cannot silently set stamp0','FSM asynchronous cancel/stop host and default real planner/motion bindings; direct FSM cancellation retains FAULT520','Attribution and reliable exclusion of previous688d80d runtime proof loss230','Full PickPlace/Task, tool/contact/Cartesian execution, placement evidence and real perception','MoveIt shutdown -11, Generic statistics context errors, driver dependencies/lint and symbolic/unforced limits','Planning-scene branch, calibration and perception integration; SDK licence/vendor checksums, TSan, NUC/physical robot'],
 'handoff':{'Sun_Jiaming':'Command-identity kernel acceptance results; preserve previous230, current oldPython220/510/520 and default runtime/async cancel host gaps. Local handoff only, no kernel repair or messages.','Chang_Jianshuo':'Planning-only ownership configuration proposal, generated-vs-scheduled timestamps, reviewed trajectory limits/spline/start contracts and physical TF/tool semantics. No bypass or limits widening.','integration':'Retain source/branch/test identity, UUID/feedback, blocked graph and clean shutdown evidence; no merge/baseline advance.'},'source_modified':False,'formal_baseline_advanced':False,'local_merge_performed':False}
(raw/'supplement-analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'verdict':analysis['verdict'],'cases':[{'mode':c['mode'],'exit_code':c['exit_code'],'probe':c['probe']} for c in cases],'topology':top['status'],'plan_consumer':consumer},ensure_ascii=False,indent=2))
