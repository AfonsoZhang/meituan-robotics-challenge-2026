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
for label in ['planning-sop']:
 d=raw/'container'/label
 fixedp=next(d.glob('fixed_pose*.yaml'));fixed=yaml.safe_load(fixedp.read_text());assert fixed['result']['ok']
 v=check_trajectory(fixed['trajectory']);v.update({k:fixed['result'][k] for k in ['planning_time_s','final_position_error_m','final_orientation_error_rad']});v['yaml']=fixedp.name;v['child_exit']=exit_code(d/'plan_fixed_pose.log','plan_fixed_pose')
 seq={}
 for typ in ['passive_hook_v1','magnetic_latch_v2']:
  p=next(d.glob('battery_sequence_'+typ+'*.yaml'));data=yaml.safe_load(p.read_text());phases=data['phases'];out=[];allcommands=[];bounds=[]
  assert data['tcp']['status']=='PLACEHOLDER' and data['start']=='SRDF named state home'
  for phase in phases:
   assert phase['simulation_only'] is True
   commands=phase['commands'] or []
   if not phase['ok']:assert not commands and phase['error_code']==200
   else:assert commands and phase['error_code']==0
   ps={x['primitive_name']:x for x in phase['primitives']}
   for c in commands:
    assert c['simulation_only'] is True and c['target_rad']==[]
    b=check_trajectory(c['trajectory']);b['primitive_name']=c['primitive_name'];report=ps[c['primitive_name']]
    assert b['point_count']==report['point_count'] and abs(b['duration_s']-report['duration_s'])<1e-6
    assert b['duration_s']<=report['state_watchdog_s']*.8 and c['timeout_ms']>b['duration_s']*1000
    b.update({k:report[k] for k in ['method','start_assumption','planning_time_s','time_scale_applied','timeout_ms','state_watchdog_s','max_ee_linear_speed_m_s','max_ee_angular_speed_rad_s','contact_intent_only']});bounds.append(b);allcommands.append(c)
   out.append({k:phase[k] for k in ['phase','ok','error_code','message','simulation_only','uncalibrated_inputs','primitives']})
  boundaries=[]
  for a,b in zip(allcommands,allcommands[1:]):
   delta=max(abs(x-y) for x,y in zip(a['trajectory']['points'][-1]['positions_rad'],b['trajectory']['points'][0]['positions_rad']))
   gap=b['primitive_name'] in ['test_lift','retreat']
   if not gap:assert delta<1e-3,(a['primitive_name'],b['primitive_name'],delta)
   boundaries.append({'from':a['primitive_name'],'to':b['primitive_name'],'max_joint_gap_rad':delta,'unemitted_tool_motion_assumption':gap,'scope':'Gap assumed by upstream ToolPort handoff; not executed or validated physically' if gap else 'Matching endpoints'})
  ok=all(x['ok'] for x in phases)
  if ok:assert [c['primitive_name'] for c in allcommands]==['top_insert','test_lift','lift','transport','pre_seat','seat_contact','retreat']
  seq[typ]={'yaml':p.name,'ok':ok,'phases':out,'command_count':len(allcommands),'trajectories':bounds,'boundaries':boundaries,'child_exit':exit_code(d/('plan_battery_sequence_v1.log' if typ.endswith('v1') else 'plan_battery_sequence_v2.log'),'plan_battery_sequence')}
 runs[label]={'fixed_pose':v,'sequences':seq,'move_group_exit':exit_code(d/'move_group_launch.log','move_group'),'control_exit':exit_code(d/'control_launch.log','ros2_control_node'),'script_exit':json.loads((raw/'logs'/(label+'.json')).read_text())['exit_code'],'summary_reports_no_remaining_nodes':'PASS all nodes started by this script exited' in (d/'SUMMARY.txt').read_text()}
result={'at':datetime.now(timezone.utc).isoformat(),'scope':'Unmodified merged-overlay default MoveGroup/Fake planning SOP only; no planner trajectory executed','configuration_change':False,'raw_urdf_command_interface_limits':raw_limits,'planner_numeric_bounds_from_source':limits,'runtime_limit_enforcement':'NOT VERIFIED; expanded command-interface limits may retain expressions, recorded verbatim','runs':runs}
(raw/'planning-analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{'fixed':v['fixed_pose'],'sequences':{t:{'ok':s['ok'],'commands':s['command_count'],'message':s['phases'][0]['message'],'child_exit':s['child_exit']} for t,s in v['sequences'].items()},'move_group_exit':v['move_group_exit'],'control_exit':v['control_exit']} for k,v in runs.items()},ensure_ascii=False,indent=2))
