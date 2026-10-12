"""Source/evidence-based failure analysis; no upstream algorithm changes. Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,re
raw=Path(__file__).resolve().parent;root=raw.parents[1];watch=root/'outputs/moveit-watch-20261011'
event='sha-f7eaa2c0d2887aeada4fd635112c63c237962ff7';auto=watch/'runs'/event
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=read(auto/'container/moveit/result.json');diagnostic=read(raw/'container/moveit-wait5/result.json')
assert original['planning_execution']=='FAIL' and original['plan']['error_code']['val']==1
assert original['accepted'] and original['execute']['status']==6 and original['execute']['result']['error_code']['val']==-4
assert 'max_error_rad' not in original
assert diagnostic['planning_execution']=='PASS' and diagnostic['plan']['error_code']['val']==1
assert diagnostic['accepted'] and diagnostic['execute']['status']==4 and diagnostic['execute']['result']['error_code']['val']==1
assert diagnostic['diagnostic_settle']['elapsed_seconds']>=5
assert diagnostic['max_error_rad']<=0.001 and diagnostic['distinct_joint_stamps']>2
assert abs(max(abs(a-b) for a,b in zip(diagnostic['actual_rad'],diagnostic['target_rad']))-diagnostic['max_error_rad'])<1e-14
for r in [original,diagnostic]:
 assert r['plugins']==['mock_components/GenericSystem'] and r['clean_shutdown']=='FAIL'
 assert len(r['controller_action_servers'])==1
 assert len(r['shutdown'])==2
 assert all(not a['escalated'] and a['exit_code']==0 and not a['already_exited'] for a in r['shutdown'])
 mg=next(a for a in r['shutdown'] if a['launch']=='move-group');ctrl=next(a for a in r['shutdown'] if a['launch']=='control')
 assert len(mg['child_failures'])==1 and 'exit code -11' in mg['child_failures'][0] and not ctrl['child_failures']
 trajectories=r['plan']['trajectory']['joint_trajectory'];assert trajectories['joint_names']==r['joint_names']
 pts=trajectories['points'];times=[a['time_from_start']['sec']+1e-9*a['time_from_start']['nanosec'] for a in pts]
 assert len(pts)>1 and all(b>a for a,b in zip(times,times[1:]))
 assert all(len(a[k])==6 and all(math.isfinite(x) for x in a[k]) for a in pts for k in ['positions','velocities','accelerations'])

def log_result(base):
 mg=(base/'move-group.log').read_text();control=(base/'control.log').read_text()
 def timestamp(needle):
  line=next((l for l in mg.splitlines() if needle in l),None)
  return {'line':line,'time':float(re.search(r'\[(\d+\.\d+)\]',line).group(1))} if line else None
 added=timestamp('Added FollowJointTrajectory controller')
 failed=timestamp('Action client not connected to action server')
 received=timestamp('Execution request received')
 assert 'process has finished cleanly' in control
 assert not re.search(r'process has died',control)
 return {'controller_added':added,'internal_client_not_connected':failed,
         'controller_added_to_failure_seconds':failed['time']-added['time'] if failed and added else None,
         'execute_received':received,'control_child_exit':0,'move_group_child_exit':-11,
         'control_received_goal':any('Received new action goal' in l for l in control.splitlines())}
orig_logs=log_result(auto/'container/moveit');diag_logs=log_result(raw/'container/moveit-wait5')
assert orig_logs['internal_client_not_connected'] and not orig_logs['control_received_goal']
assert not diag_logs['internal_client_not_connected'] and diag_logs['control_received_goal']
tasks=read(auto/'container/task-mock/summary.json');assert [v['result']['result']['error_code'] for v in tasks]==[220,510,520]
assert all(v['result']['status']==6 and v['result']['result']['completed_count']==0 for v in tasks)
assert tasks[2]['cancel_response']['return_code']==0
for case in ['early-goal','delayed-goal','cancel-goal']:
 all_logs='\n'.join(p.read_text(errors='replace') for p in (auto/'container/task-mock'/case).rglob('*.log'))
 assert 'create_client' in all_logs
assert read(raw/'logs/identity.json')['exit_code']==0
assert read(raw/'logs/moveit-wait5.json')['exit_code']==1
assert read(raw/'logs/stop-daemon.json')['exit_code']==0
assert sha(raw/'probe_moveit_original.py')==read(auto/'summary.json')['environment']['harness_sha256']['probe_moveit.py']
counts=read(raw/'automatic-counts.json'); source=read(raw/'source-review.json')
analysis={'recorded_at':datetime.now(timezone.utc).isoformat(),
 'verdict':'PARTIAL_PASS_IDENTICAL_MAIN_MERGE_DEFAULT_MOVEIT_EXECUTION_FAIL_WAIT5_PASS_SHUTDOWN_FAIL',
 'source':{'entire_tree_identical_to_prior_acceptance':source['whole_tree_identical_to_reviewed_commit'],
  'reference':'ENV-PLANNER-MERGE-20261012','tree':source['tree'],'new_source_or_entrypoints':False,
  'current_automatic_results_independent_of_history':True},
 'automatic':{'summary_steps':25,'original_files_verified':counts['original_files_verified'],
  'build_packages':14,'cpp':387,'cpp_executables':24,'python':269,'e2e':15,'ros':6,
  'old_cpp_audit':'Count-only mismatch: expected 16 versus 20 *_cpp executables; planner excluded',
  'legacy_task':[{k:a[k] for k in ['case','status','accepted','result','child_failure','shutdown_escalated']} for a in tasks],
  'moveit':{k:v for k,v in original.items() if k not in ['tf','plan']},'moveit_log_review':orig_logs,
  'no_final_joint_error_measurement':'Original probe exits on execute ABORTED/-4 before final position check; cannot claim target reached',
  'dependency_gaps':['ament_python rosdep key','driver docker.io','driver ros-jazzy-ros2-controllers-test-nodes'],
  'driver_test_aggregate':{'total':1104,'failures':279,'skipped':259,'scope':'Includes lint and wrappers, not physical function tests'}},
 'supplement':{'installed_identity_and_two_module_rosdep':'PASS','delivered_action_audit':'358 / 20 PASS; excludes planner; 29 / 4 independently audited',
  'moveit_diagnostic':{k:v for k,v in diagnostic.items() if k not in ['tf','plan']},'moveit_log_review':diag_logs,
  'changes':'Only local copied probe uses isolated domain 131 and an extra monotonic 5-second discovery settle; no driver/planner/config/tolerance/deadline modifications',
  'repeat_count':1,'causal_limit':'One fresh run supports a discovery-readiness hypothesis, not a proven race root cause, reliable fixed wait or production repair',
  'startup_contract_limit':'External active controller, graph discovery and MoveIt action availability do not prove internal MoveIt FJT ActionClient connected',
  'cleanup_guard':'Detected remaining domain 131 CLI daemon after launch exit; stopped that daemon, then rechecked only keeper and stopped supplement. First assertion and process snapshot retained.'},
 'history_not_rerun':{'ENV-PLANNER-MERGE-20261012':'Same exact Git tree/environment: standalone C++ four scenarios 40 checks; default planning fixed pose passed; V1 42.0717s >24s, V2 TF_UNAVAILABLE. These are prior outcomes, not current reruns.',
  'ENV-CPP-ACTION-20261011':'UBSan and external CMake consumer unchanged; historical evidence only',
  'ENV-HANDOFF-20261012':'Short CLI graph observation failures still open',
  'separate_branch_results':'Scene 30e3c6e and perception 0e329f1 not in this main tree, cannot attribute their tests/features to f7eaa2c.'},
 'not_completed':['Production MoveIt internal controller readiness and clean shutdown',
  'Default planner sequence TF/V1 watchdog failures; no new planner code in this merge',
  'Full FSM/Action/Planner/FJT wiring, unique execution ownership, full trajectory and tool transitions',
  'Legacy Python B03/B05/B06 and cancel stop confirmation; Safety repeated shutdown',
  'Scene/payload/vision branch integration, calibrated TCP/TF/tools, live perception, collision validity',
  'SDK licence/vendor checksum, symbolic controller limits, driver dependency/lint, TSan, NUC/physical robot'],
 'handoff':{'Sun_Jiaming':'FSM/Action/Cancel kernel, actual trajectory/stop integration and old B03/B05/B06/520; record locally, no repair or external message',
  'Chang_Jianshuo':'Planner default TF/state budget and calibrated scene/input contracts',
  'integration':'Replace availability-only acceptance assumptions with verifiable readiness contract; track observed default failure and bounded diagnosis separately, retain -11 and cleanup evidence'},
 'source_modified':False,'formal_baseline_advanced':False,'local_merge_performed':False}
(raw/'supplement-analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'default':original['planning_execution'],'execute_default':original['execute'],'wait5':diagnostic['planning_execution'],
 'wait_elapsed':diagnostic['diagnostic_settle']['elapsed_seconds'],'max_error_rad':diagnostic['max_error_rad'],'distinct_stamps':diagnostic['distinct_joint_stamps'],
 'shutdown':[orig_logs['move_group_child_exit'],diag_logs['move_group_child_exit']],
 'added_to_failure_seconds':orig_logs['controller_added_to_failure_seconds']},ensure_ascii=False,indent=2))
