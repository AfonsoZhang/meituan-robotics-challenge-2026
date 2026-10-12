"""Audit saved planner outputs, never execute trajectories; Codex assisted 2026-10-12."""
from pathlib import Path
from datetime import datetime,timezone
import json,math,re,xml.etree.ElementTree as ET
import yaml
raw=Path(__file__).resolve().parent
names=['shoulder_joint','upperArm_joint','foreArm_joint','wrist1_joint','wrist2_joint','wrist3_joint']
model=ET.parse(raw/'container/planning-sop/aubo_S3_fake_expanded.urdf').getroot()
raw_limits={j.get('name'):{p.get('name'):p.text for p in j.findall('command_interface[@name="position"]/param')} for j in model.findall('ros2_control/joint')}
# Source-reviewed numeric values from planner_config.cpp. Do not evaluate upstream strings.
limits={n:{'min':-m,'max':m} for n,m in zip(names,[2*math.pi,2*math.pi,2.41,2.66,2*math.pi,2.23])}
for n,values in raw_limits.items():
 for k,v in values.items():
  if v not in ('{-2*pi}','{2*pi}'):assert float(v)==limits[n][k]

assert list(limits)==names

def check_trajectory(t):
 assert t['shape_is_valid'] is True and t['joint_names']==names
 pts=t['points'];assert len(pts)==t['point_count'] and len(pts)>1
 times=[p['time_from_start_s'] for p in pts]
 assert all(math.isfinite(x) and x>=0 for x in times) and all(b>a for a,b in zip(times,times[1:]))
 assert abs(times[-1]-t['duration_s'])<1e-6
 extremes={n:[math.inf,-math.inf] for n in names}
 for p in pts:
  for k in ['positions_rad','velocities_rad_s','accelerations_rad_s2']:
   v=p[k];assert len(v)==6 and all(math.isfinite(x) for x in v)
  for n,x in zip(names,p['positions_rad']):
   assert limits[n]['min']-1e-8<=x<=limits[n]['max']+1e-8,(n,x,limits[n])
   extremes[n]=[min(extremes[n][0],x),max(extremes[n][1],x)]
 return {'point_count':len(pts),'duration_s':times[-1],'time_monotonic':True,'finite_positions_velocities_accelerations':True,'planner_declared_position_bounds':'PASS','joint_order':names,'extremes_rad':extremes}

def exit_code(log,node):
 t=log.read_text()
 m=re.search(r'\['+re.escape(node)+r'-\d+\]: process has died \[pid \d+, exit code (-?\d+)',t)
 if m:return int(m.group(1))
 assert re.search(r'\['+re.escape(node)+r'-\d+\]: process has finished cleanly',t),(log,node)
 return 0
runs={}
for label in ['planning-sop','diagnostic-tfwait']:
 d=raw/'container'/label
 fixedp=next(d.glob('fixed_pose*.yaml'));fixed=yaml.safe_load(fixedp.read_text());assert fixed['result']['ok']
 fixed_result=check_trajectory(fixed['trajectory'])
 fixed_result.update({k:fixed['result'][k] for k in ['planning_time_s','final_position_error_m','final_orientation_error_rad']})
 fixed_result.update({'yaml':fixedp.name,'child_exit':exit_code(d/'plan_fixed_pose.log','plan_fixed_pose')})
 sequences={}
 for typ,suffix in [('passive_hook_v1','v1'),('magnetic_latch_v2','v2')]:
  paths=list(d.glob('battery_sequence_'+typ+'*.yaml'))
  log=d/('plan_battery_sequence_'+suffix+'.log')
  child=exit_code(log,'plan_battery_sequence')
  if not paths:
   assert 'failed to apply planning scene obstacles' in log.read_text() and child==2
   sequences[typ]={'status':'SCENE_INITIALIZATION_FAILED','ok':False,'planning_reached':False,'yaml':None,'commands':0,'child_exit':child,'message':'failed to apply planning scene obstacles'}
   continue
  assert len(paths)==1
  p=paths[0];data=yaml.safe_load(p.read_text());phases=data['phases'];commands=[];trajectories=[]
  assert data['tcp']['status']=='PLACEHOLDER' and data['start']=='SRDF named state home'
  for phase in phases:
   assert phase['simulation_only'] is True
   values=phase['commands'] or []
   if not phase['ok']:assert not values and phase['error_code']==200
   else:assert values and phase['error_code']==0
   reports={v['primitive_name']:v for v in phase['primitives']}
   for command in values:
    assert command['simulation_only'] and command['target_rad']==[]
    info=check_trajectory(command['trajectory']);pr=reports[command['primitive_name']]
    assert info['point_count']==pr['point_count'] and abs(info['duration_s']-pr['duration_s'])<1e-6
    assert info['duration_s']<=pr['state_watchdog_s']*.8 and command['timeout_ms']>info['duration_s']*1000
    info.update({k:pr[k] for k in ['primitive_name','method','payload_attached','backend_message','state_watchdog_s','timeout_ms','start_assumption','contact_intent_only']})
    trajectories.append(info);commands.append(command)
  boundaries=[]
  for a,b in zip(commands,commands[1:]):
   delta=max(abs(x-y) for x,y in zip(a['trajectory']['points'][-1]['positions_rad'],b['trajectory']['points'][0]['positions_rad']))
   gap=b['primitive_name'] in ['test_lift','retreat']
   if not gap:assert delta<1e-3
   boundaries.append({'from':a['primitive_name'],'to':b['primitive_name'],'max_joint_gap_rad':delta,'unemitted_tool_motion_assumption':gap})
  ok=all(v['ok'] for v in phases)
  if ok:
   assert [v['primitive_name'] for v in commands]==['top_insert','test_lift','lift','transport','pre_seat','seat_contact','retreat']
   assert [v['payload_attached'] for v in trajectories]==[False,True,True,True,True,True,False]
  sequences[typ]={'status':'PASS' if ok else 'PLANNING_REJECTED','ok':ok,'planning_reached':True,'yaml':p.name,
     'commands':len(commands),'child_exit':child,'phases':phases,'trajectories':trajectories,'boundaries':boundaries}
 collision_paths=list((d/'collision_probe').glob('fixed_pose*.yaml'))
 collision_log=d/'collision_probe.log';collision_child=exit_code(collision_log,'plan_fixed_pose')
 if not collision_paths:
  assert 'failed to apply planning scene obstacles' in collision_log.read_text() and collision_child==2
  collision={'status':'SCENE_INITIALIZATION_FAILED','collision_test_evaluated':False,'child_exit':2,'yaml':None,
    'sop_label_note':'goal inside table was NOT rejected is misleading here: target planning was not reached.'}
 else:
  assert len(collision_paths)==1
  data=yaml.safe_load(collision_paths[0].read_text());result=data['result']
  assert not result['ok'] and result['reason']=='NO_PLAN' and 'contact(s)' in result['message'] and 'trajectory' not in data
  contacts=[line for line in (d/'move_group_launch.log').read_text().splitlines() if "Found a contact between 'table'" in line]
  assert contacts and any('wrist3_Link' in line for line in contacts)
  collision={'status':'EXPECTED_REJECTION_PASS','collision_test_evaluated':True,'child_exit':collision_child,
    'yaml':str(collision_paths[0].relative_to(d)),'result':result,'actual_contact_log_lines':contacts,
    'scope':'One sampled-path collision counterexample; not continuous or physical collision safety.'}
 runs[label]={'fixed_pose':fixed_result,'sequences':sequences,'collision_probe':collision,
    'move_group_exit':exit_code(d/'move_group_launch.log','move_group'),
    'control_exit':exit_code(d/'control_launch.log','ros2_control_node'),
    'script_exit':json.loads((raw/'logs'/(label+'.json')).read_text())['exit_code'],
    'no_remaining_nodes_reported':'PASS all nodes started by this script exited' in (d/'SUMMARY.txt').read_text()}

default=runs['planning-sop'];diagnostic=runs['diagnostic-tfwait']
assert diagnostic['sequences']['magnetic_latch_v2']['ok'] and diagnostic['sequences']['magnetic_latch_v2']['commands']==7
local_path=raw/'container/diagnostic-tfwait'/diagnostic['sequences']['passive_hook_v1']['yaml']
local=yaml.safe_load(local_path.read_text())
provided_path=next((raw/'source/docs/planning/evidence/20261011_113932').glob('battery_sequence_passive_hook_v1*.yaml'))
provided=yaml.safe_load(provided_path.read_text())
same=['tool_type','slot','start','ring_pose','tcp']
assert all(local[k]==provided[k] for k in same)
assert local['phases'][0]['start_state']==provided['phases'][0]['start_state']
lp=local['phases'][0]['primitives'][0];up=provided['phases'][0]['primitives'][0]
assert lp['method']==up['method']=='joint_interpolated_ik' and lp['ee_goal']==up['ee_goal']
assert lp['reason']==up['reason']=='EXCEEDS_STATE_WATCHDOG' and not local['phases'][0]['commands']
comparison={'upstream_report':str(provided_path.relative_to(raw)),'upstream_is_supplied_data_not_local_execution':True,
 'equal_fields':same+['phases[0].start_state','ee_goal','method'],
 'upstream':{k:up[k] for k in ['duration_s','point_count','time_scale_applied','max_ee_linear_speed_m_s','max_ee_angular_speed_rad_s','method','backend_message']},
 'local':{k:lp[k] for k in ['duration_s','point_count','time_scale_applied','max_ee_linear_speed_m_s','max_ee_angular_speed_rad_s','method','backend_message']},
 'analysis':'Local joint_interpolated_ik was 180.415 s vs provided 42.080 s despite identical reported named start/ring/TCP/EE goal. This does not reproduce the upstream stable 39.6–42.1 s claim. It is not an observed OMPL fallback. Actual IK joint goal and rejected full trajectory are not serialized by the tool; solver/model/runtime cause not established.'}
scene=json.loads((raw/'container/diagnostic-tfwait/scene-reader/summary.json').read_text())
assert scene['status']=='PASS' and scene['object_ids']==['table'] and not scene['global_attached_objects'] and scene['current_state_valid']
a=yaml.safe_load((raw/'source/src/mtc_moveit_planner/config/planner.yaml').read_text())
b=yaml.safe_load((raw/'container/diagnostic-tfwait/planner-tfwait.yaml').read_text())
assert a['/**']['ros__parameters']['backend']['tf_timeout_s']==.5 and b['/**']['ros__parameters']['backend']['tf_timeout_s']==5
b['/**']['ros__parameters']['backend']['tf_timeout_s']=.5;assert a==b
config=a['/**']['ros__parameters'];table=config['scene']['boxes']['table']
top=table['xyz'][2]+table['size_m'][2]/2
bottom=config['slots']['T0']['xyz'][2]-config['payload']['hang_below_tcp_m']-config['payload']['size_m'][2]/2
result={'at':datetime.now(timezone.utc).isoformat(),'scope':'New planner SOP and one bounded scene-readiness diagnostic; no generated trajectory executed',
 'only_parameter_difference':{'backend.tf_timeout_s':{'default':.5,'diagnostic':5}},
 'diagnostic_observer':'Read-only scene/state query after all planning tools; no scene mutation or timing change before tool results',
 'raw_urdf_command_interface_limits':raw_limits,'planner_numeric_bounds_from_source':limits,'runtime_limit_enforcement':'NOT VERIFIED; three expanded command limits retain symbolic expressions',
 'runs':runs,'v1_upstream_comparison':comparison,
 'scene_observation':{k:scene[k] for k in ['status','object_ids','table_frame','global_attached_objects','current_state_valid']},
 'nominal_clearance_calculation':{'source':'default PLACEHOLDER config, static arithmetic only','table_top_z_m':top,'payload_bottom_z_m':bottom,'clearance_m':bottom-top,
 'note':'Nominal 15 mm above table, not 10 mm as upstream prose says; no physical measurement or actual contact closing.'},
 'public_api_scope':'New start consistency and replan_primitive covered by delivered 35-case unit suite; real execution-side caller/FJT wiring absent, not accepted by these SOPs.'}
(raw/'planning-analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'runs':{k:{'fixed':v['fixed_pose'],'collision':v['collision_probe']['status'],
 'sequences':{t:{'status':z['status'],'commands':z['commands'],'child_exit':z['child_exit']} for t,z in v['sequences'].items()},
 'move_group_exit':v['move_group_exit'],'control_exit':v['control_exit']} for k,v in runs.items()},'v1_comparison':comparison,'clearance':result['nominal_clearance_calculation']},ensure_ascii=False,indent=2))
