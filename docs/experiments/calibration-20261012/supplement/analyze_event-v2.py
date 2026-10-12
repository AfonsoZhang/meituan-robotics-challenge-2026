"""Analyze original and supplement evidence without changing upstream. Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,re
raw=Path(__file__).resolve().parent;root=raw.parents[1];auto=root/'outputs/moveit-watch-20261011/runs/sha-06ab689f25e87dcebf9fd04fdd581ec4755206f6'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=read(raw/'source-review.json');counts=read(raw/'automatic-counts.json');off=read(raw/'container/offline/results.json');tf=read(raw/'container/fake-tf/summary.json')
assert off['all_passed'] and off['unittest']['tests_ran']==54 and off['unittest']['skipped']==0
assert len(off['documented_cases'])==6 and len(off['generated_negative_cases'])==5
assert all(x['passed'] for x in off['documented_cases']+off['generated_negative_cases']) and off['format_checks']['passed']
identity=read(raw/'container/offline/source-identity.json');assert identity['cases']==54 and len(set(identity['source_test_identities']))==54 and identity['source_clean']
for n in ['synthetic','unknown_extrinsic','nominal_mount','design_not_real_case','fake_model_audit']:
 assert read(raw/'container/offline'/(n+'.json'))==read(raw/'source/docs/calibration/validation'/(n+'.json')),n
negative_comparison=[]
for current,upstream in zip(read(raw/'container/offline/generated_negative_inputs.json'),read(raw/'source/docs/calibration/validation/generated_negative_inputs.json')):
 assert {k:v for k,v in current.items() if k!='command'}=={k:v for k,v in upstream.items() if k!='command'}
 assert current['command']==upstream['command'].replace('\\','/')
 negative_comparison.append({'name':current['name'],'result_and_noncommand_fields_equal':True,'command_difference':'Windows versus Linux temporary path separator only'})
archived=read(raw/'container/offline/fake_model_audit.json')
assert [v['samples'] for v in archived['logs'].values()]==[5,5,7] and not archived['real_calibration_verified']
assert tf['status']=='PASS_READ_ONLY_FAKE_TF' and tf['action_clients_created']==tf['goals_sent']==tf['tf_publishers_created']==0
assert len(tf['model_receipts'])==4 and all(x['receipt_matches'] for x in tf['model_receipts'])
assert sha(raw/'container/fake-tf/robot-description.urdf')==tf['robot_description_sha256']
rows=tf['transforms'];assert len(rows)==4 and len({x['query_stamp_ns'] for x in rows})==1
assert all(x['returned_stamp_ns']==x['query_stamp_ns'] for x in rows)
assert all(x['max_position_component_error_m']<1e-10 and x['max_rotation_matrix_component_error']<1e-10 for x in rows)
wrist=next(x for x in rows if x['parent']=='wrist3_Link');assert wrist['translation_m']==[0,0,0]
assert max(abs(a-b) for a,b in zip(wrist['rotation_xyzw'],[0,0,math.sqrt(.5),math.sqrt(.5)]))<1e-12
joints=read(raw/'container/fake-tf/joint-states.json');assert len({x['stamp_ns'] for x in joints})==tf['distinct_joint_stamps']==903
assert not read(raw/'container/fake-tf/goal-status.json')
assert all(math.isfinite(v) and abs(v)<1e-12 for x in joints for k in ['positions','velocities'] for v in x[k])
assert 'Action clients: 0' in (raw/'container/fake-tf/fjt-info.log').read_text()
clean=tf['shutdown'];assert clean['exit_code']==0 and not clean['escalated'] and not clean['child_failures'] and tf['empty_after']
for n in ['offline','fake-tf']:assert read(raw/'logs'/(n+'.json'))['exit_code']==0
inventory=read(raw/'source/config/calibration/site_inventory.json')
assert len(inventory['transforms'])==8 and all(x['status']=='UNKNOWN' and x['translation'] is None and x['rotation_xyzw'] is None for x in inventory['transforms'])
assert all(v is None for k,v in inventory['thresholds'].items() if k!='status')
for p in ['handeye_samples.csv','tcp_samples.csv','validation_points.csv']:
 assert len((raw/'source/docs/calibration'/p).read_text().splitlines())==1
mv=read(auto/'container/moveit/result.json');assert mv['planning_execution']=='PASS' and mv['clean_shutdown']=='FAIL'
assert mv['execute']['status']==4 and mv['execute']['result']['error_code']['val']==1 and mv['distinct_joint_stamps']==209
assert mv['max_error_rad']<.001 and abs(max(abs(a-b) for a,b in zip(mv['actual_rad'],mv['target_rad']))-mv['max_error_rad'])<1e-14
assert any('exit code -11' in l for x in mv['shutdown'] for l in x['child_failures']) and all(not x['escalated'] for x in mv['shutdown'])
tasks=read(auto/'container/task-mock/summary.json');assert [x['result']['result']['error_code'] for x in tasks]==[220,510,220]
assert all(x['result']['status']==6 and x['result']['result']['completed_count']==0 for x in tasks)
assert tasks[2]['cancel_response']['return_code']==0
audit_log=(auto/'logs/cpp-audit.log').read_text();assert '16' in audit_log and '20' in audit_log
driver=(auto/'logs/driver-test-results.log').read_text();assert '1104 tests, 0 errors, 279 failures, 259 skipped' in driver
analysis={'recorded_at':datetime.now(timezone.utc).isoformat(),
 'verdict':'PASS_OFFLINE_CALIBRATION_54_AND_READ_ONLY_FAKE_TF; REAL_CALIBRATION_AND_CONSUMER_WIRING_NOT_ACCEPTED; EXISTING_TASK_AND_MOVEIT_SHUTDOWN_FAILURES_RETAINED',
 'source':source,
 'automatic':{'status':'COMPLETED_WITH_FAILURES','summary_steps':25,'original_files_verified':305,
  'build_packages':14,'cpp_cases':387,'cpp_executables':24,'python_cases':269,'e2e':15,'ros_wiring':6,
  'cpp_audit_failure':counts['old_fixed_audit'],'colcon_aggregate_note':'685 includes CTest wrappers and interface lint',
  'legacy_task':[{k:x[k] for k in ['case','accepted','result','child_failure','shutdown_escalated']} for x in tasks],
  'moveit':{k:v for k,v in mv.items() if k not in ['plan','tf']},
  'dependency_gaps':['ament_python rosdep key','driver docker.io','driver ros-jazzy-ros2-controllers-test-nodes'],
  'driver_test_aggregate':{'total':1104,'failures':279,'skipped':259,'scope':'Includes lint and CTest wrappers, not physical functionality'}},
 'supplement':{'delivered_action_verifier':'358 cases/20 executables PASS; planner29/4 checked separately',
  'offline':off,'offline_source_identity':identity,'five_upstream_diagnostic_json_objects_equal':True,'generated_negative_comparison':negative_comparison,
  'archived_model_tf_audit':archived,'fake_tf_runtime':tf,
  'nominal_mount_scope':'ESTIMATED arithmetic of the upstream design fixture; no deployed or measured transform. 17.5mm datum/4.2mm depth offset and camera wrapper conventions are upstream cited assumptions; camera source files/PDF not independently downloaded or checked in this event.',
  'model_receipt_scope':'Four AUBO Git blobs in official-source receipt match pinned local model repo; remaining seven official reference artifacts are not present and not independently re-verified here.',
  'real_inventory':{'unknown_edges':8,'thresholds_null':True,'handeye_tcp_validation_csvs':'header only, zero physical samples','user_decisions_imported':False},
  'cleanup_guard':'First helper assertion rejected a corrupted copied SHA literal; no source change and only keeper remained. Failed helper/process snapshot preserved; corrected comparison and verified actual HEAD before stopping container.'},
 'not_rerun':{'unchanged_runtime':'All existing src tree matches f7eaa2c and its450-file frozen set/report verified; no repeated planner SOP, independent Action scenarios, UBSan/consumer or FjtPort tests (new FjtPort absent). Current automatic runs stay distinct.',
  'separate_branches':'Vision0e329f1, scene30e3c6e, trajectory688d80d/230 outcomes not attributed to this calibration snapshot.'},
 'integration_gaps':['No ROS TF listener/publisher or hand-eye solver delivered; local read-only witness is acceptance harness only',
  'Offline refusal/MEASURED semantics not consumed by runtime perception/planner/FSM adapters; evidence reference is nonempty text, not authenticity or accuracy proof',
  'Planner uses latest TF for Pose6D whose stamp is FSM clock; observation-time dynamic TF and ROS/Core time conversion unresolved',
  'Planner already applies inverse EE-to-TCP compensation; do not feed already-compensated EE pose as TCP/ring',
  'Slot target uses TCP position and current grasp orientation; independent placement orientation is not consumed',
  'Physical design flange F-to-wrist axes, camera/TCP/optical/scene transforms, ring axes and error/age limits UNKNOWN'],
 'not_completed':['Real D435i intrinsics/internal extrinsics/mount, V1 TCP/tool selection/installation, table/T0/P1-P3 and physical accuracy',
  'Moving-camera capture-time TF and time-domain bridge, live perception and failure propagation',
  'Complete FSM/Action/Planner/FJT/tool chain; legacy B03/B05/B06 and cancellation stop confirmation',
  'MoveIt -11 shutdown, Generic statistics context errors, driver dependencies/lint and evaluated joint limits',
  'SDK licence/vendor checksums, TSan, NUC/physical robot and actual collision/contact'],
 'handoff':{'Han_Minghe':'Calibration data/physical frameF/TCP/field measurements and recorded assumptions; no fabricated or promoted MEASURED data',
  'Sun_Haoran':'Device intrinsics/internal TF/optical frame and observation stamps/ring axes',
  'Chang_Jianshuo':'ROS observation-time TF, one TCP compensation, slot semantic/orientation and calibrated planner parameters',
  'Sun_Jiaming':'ROS/Core clock/full Pose6D/failure propagation and FSM/Action/Cancel kernel, old B03/B05/B06; local issue record only',
  'integration':'Retain artifacts and declared-vs-observed boundaries, TF source ownership/bringup/logging and provenance; no kernel repair or external messages'},
 'source_modified':False,'formal_baseline_advanced':False,'local_merge_performed':False}
(raw/'supplement-analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'verdict':analysis['verdict'],'offline_tests':54,'documented_cases':6,'negative_cases':5,'tf':tf['status'],'samples':903,'inventory_unknown_edges':8,'moveit_error_rad':mv['max_error_rad']},indent=2))
