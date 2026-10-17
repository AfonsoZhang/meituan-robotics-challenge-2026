#!/usr/bin/env python3
"""Codex-assisted isolated default native Status/topology witness. Never sends FJT goals."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, os, re, signal, subprocess, sys, time, xml.etree.ElementTree as ET
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
os.environ.update(ROS_DOMAIN_ID='176',ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',ROS_LOG_DIR=str(out/'ros-logs'))
result={'started_at':datetime.now(timezone.utc).isoformat(),'scope':'Default GenericSystem+MoveIt+FjtMotionPort ownership gate with native Status evidence; no FJT Goal, no complete FSM/physical robot','observer_action_clients':0,'status':'NOT_RUN'}
launches=[];node=None;initialized=False;samples=[];statuses=[];live=None;live_log=None
def finite(v):
 if isinstance(v,float) and not math.isfinite(v):return None
 if isinstance(v,dict):return {k:finite(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)):return [finite(x) for x in v]
 return v
def write(name,v):(out/name).write_text(json.dumps(finite(v),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def capture(label,argv,timeout=25):
 start=datetime.now(timezone.utc).isoformat();p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
 (out/(label+'.log')).write_text(p.stdout+p.stderr);write(label+'-command.json',{'argv':argv,'started_at':start,'exit_code':p.returncode})
 assert p.returncode==0,(label,p.returncode);return p.stdout
def launch(label,argv):
 log=(out/(label+'.log')).open('w');p=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 launches.append((label,p,log));return p
def interrupt(sig,_):raise InterruptedError(str(sig))
signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
def fingerprint():
 rows={}
 for base in [Path('/driver_ws/src/aubo_ros2_driver'),Path('/driver_work/install')]:
  for p in sorted(base.rglob('*')):
   if p.is_file() and not any(x in p.parts for x in ['.git','__pycache__']):rows[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 return rows
driver_before=fingerprint();write('driver-files-before.json',driver_before)
try:
 from ament_index_python.packages import get_package_share_directory
 share=Path(get_package_share_directory('aubo_description'));assert str(share).startswith('/driver_work/install/')
 xml=capture('xacro',['xacro',str(share/'urdf/xacro/inc/aubo_ros2.xacro'),'aubo_type:=aubo_S3','use_fake_hardware:=true'])
 result['plugins']=[p.text.strip() for p in ET.fromstring(xml).findall('ros2_control/hardware/plugin')];assert result['plugins']==['mock_components/GenericSystem']
 assert not capture('empty-domain',['ros2','node','list','--no-daemon','--spin-time','2']).strip()
 assert capture('candidate-head',['git','-C','/main-source','rev-parse','HEAD']).strip()=='b4185155383541e1a4161587c4049a162f74b36d'
 assert not capture('source-before',['git','-C','/main-source','diff','HEAD','--']).strip()
 import rclpy
 from rclpy.action import get_action_client_names_and_types_by_node,get_action_server_names_and_types_by_node
 from rclpy.qos import qos_profile_sensor_data,QoSProfile,ReliabilityPolicy,DurabilityPolicy
 from sensor_msgs.msg import JointState
 from action_msgs.msg import GoalStatusArray
 from moveit_msgs.srv import GetMotionPlan
 rclpy.init();initialized=True;node=rclpy.create_node('ownership_readonly_witness')
 def js(m):samples.append({'received_monotonic':time.monotonic(),'stamp_ns':m.header.stamp.sec*1000000000+m.header.stamp.nanosec,'names':list(m.name),'positions':list(m.position),'velocities':list(m.velocity)})
 def status(m):statuses.append({'received_monotonic':time.monotonic(),'goals':[{'uuid':bytes(x.goal_info.goal_id.uuid).hex(),'status':x.status} for x in m.status_list]})
 node.create_subscription(JointState,'/joint_states',js,qos_profile_sensor_data)
 node.create_subscription(GoalStatusArray,'/joint_trajectory_controller/follow_joint_trajectory/_action/status',status,QoSProfile(depth=20,reliability=ReliabilityPolicy.RELIABLE,durability=DurabilityPolicy.TRANSIENT_LOCAL))
 def spin_for(seconds):
  until=time.monotonic()+seconds
  while time.monotonic()<until:rclpy.spin_once(node,timeout_sec=.025)
 def wait_for(fn,seconds):
  until=time.monotonic()+seconds
  while not fn() and time.monotonic()<until:rclpy.spin_once(node,timeout_sec=.05)
  assert fn(),'bounded readiness wait expired'
 def graph():
  data={'clients':[],'servers':[],'direct_publishers':node.count_publishers('/joint_trajectory_controller/joint_trajectory')}
  for n,ns in node.get_node_names_and_namespaces():
   for key,fn in [('clients',get_action_client_names_and_types_by_node),('servers',get_action_server_names_and_types_by_node)]:
    for action,types in fn(node,n,ns):
     if action=='/joint_trajectory_controller/follow_joint_trajectory':data[key].append({'node':n,'namespace':ns,'types':types})
  return data
 def run_tool(label,argv,limit,during=False):
  global live,live_log
  live_log=(out/(label+'.log')).open('w');live=subprocess.Popen(argv,stdout=live_log,stderr=subprocess.STDOUT,start_new_session=True)
  start=time.monotonic();seen=[]
  while live.poll() is None and time.monotonic()-start<limit:
   rclpy.spin_once(node,timeout_sec=.025)
   if during and time.monotonic()-start>2 and not seen:
    snap=graph()
    if len(snap['clients'])>=2:seen.append(snap)
  assert live.poll() is not None,(label,'timeout')
  code=live.returncode;live_log.close();live_log=None;live=None
  record={'argv':argv,'exit_code':code,'elapsed_seconds':time.monotonic()-start,'coexistence_graph':seen}
  write(label+'-command.json',record);return code,record
 control=launch('control',['ros2','launch','aubo_ros2_driver','aubo_control.launch.py','aubo_type:=aubo_S3','use_fake_hardware:=true','initial_joint_controller:=joint_trajectory_controller','launch_rviz:=false'])
 wait_for(lambda:len(samples)>40 and (out/'control.log').read_text().count('Configured and activated')>=2,50)
 hw=capture('hardware',['ros2','control','list_hardware_components','-c','/controller_manager','-v']);assert hw.count('mock_components/GenericSystem')==1 and 'active' in hw
 ctrl=capture('controllers',['ros2','control','list_controllers','-c','/controller_manager'])
 for n in ['joint_trajectory_controller','joint_state_broadcaster']:assert any(n in line and 'active' in line for line in ctrl.splitlines())
 spin_for(1);result['controller_only_graph']=graph();assert len(result['controller_only_graph']['clients'])==0 and len(result['controller_only_graph']['servers'])==1
 capture('status-qos',['ros2','topic','info','/joint_trajectory_controller/follow_joint_trajectory/_action/status','--verbose'])
 code,rec=run_tool('native-success',['ros2','run','mtc_trajectory_execution_cpp','fake_trajectory_probe','--verify-generic-system','success'],25)
 result['native_success']=rec;text=(out/'native-success.log').read_text()
 assert code==1 and 'FJT servers=1 clients=1 direct_trajectory_publishers=0 foreign_active_goals=0 status_received=0 status_fresh=0 unknown_active_goals=0 ready=0' in text
 assert 'BLOCKED: GenericSystem/active controller/fresh state/exclusive graph proof unavailable' in text
 assert not statuses,'Unexpected native Status before any Goal'
 result['native_execution']='BLOCKED_ZERO_GOAL';result['native_other_modes']='NOT_RUN: required live Status evidence absent; no fake heartbeat, prewarming Goal or relaxed gate'
 spin_for(1)
 mg=launch('move-group',['ros2','launch','aubo_moveit_config','aubo_moveit.launch.py','aubo_type:=aubo_S3','launch_rviz:=false'])
 planner=node.create_client(GetMotionPlan,'/plan_kinematic_path');assert planner.wait_for_service(timeout_sec=45)
 wait_for(lambda:len(graph()['clients'])==1,15)
 result['moveit_graph']=graph();assert result['moveit_graph']['clients'][0]['node']=='moveit_simple_controller_manager'
 capture('moveit-actions',['ros2','action','list','-t'])
 result['allow_execution_parameter']=capture('allow-execution',['ros2','param','get','/move_group','allow_trajectory_execution'])
 code,rec=run_tool('topology',['ros2','run','mtc_trajectory_execution_cpp','fake_trajectory_probe','--verify-generic-system','topology'],25,True)
 result['topology']=rec;text=(out/'topology.log').read_text()
 assert code==2 and 'FJT servers=1 clients=2 direct_trajectory_publishers=0 foreign_active_goals=0 status_received=0 status_fresh=0 unknown_active_goals=0 ready=0' in text and 'BLOCKED: Fake execution ownership gate; no Goal sent' in text and rec['coexistence_graph']
 assert not any(s['goals'] for s in statuses),'unexpected FJT goal during topology'
 spin_for(1);result['after_port_graph']=graph();assert len(result['after_port_graph']['clients'])==1
 spin_for(.5);result['fjt_goal_uuids']=sorted({g['uuid'] for row in statuses for g in row['goals']});assert not result['fjt_goal_uuids']
 result['distinct_joint_stamps']=len({s['stamp_ns'] for s in samples});assert all(abs(x)<1e-10 for s in samples for x in s['positions'])
 result['all_joints_zero']=True;result['status_messages']=len(statuses);result['status']='PASS_NATIVE_AND_COEXISTENCE_BLOCKED'
except Exception as exc:result['status']='FAIL';result['exception']=repr(exc)
finally:
 if live is not None and live.poll() is None:
  os.killpg(live.pid,signal.SIGTERM)
  try:live.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(live.pid,signal.SIGKILL);live.wait(timeout=3)
  result['tool_cleanup_exit']=live.returncode
 if live_log:live_log.close()
 write('joint-states.json',samples);write('action-status.json',statuses)
 if node is not None:node.destroy_node()
 if initialized:rclpy.try_shutdown()
 cleanup=[]
 for label,p,log in reversed(launches):
  row={'launch':label,'already_exited':p.poll() is not None,'escalated':False}
  if p.poll() is None:
   p.send_signal(signal.SIGINT)
   try:p.wait(timeout=12)
   except subprocess.TimeoutExpired:
    row['escalated']=True;os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait(timeout=3)
  log.close();row['exit_code']=p.returncode
  text=(out/(label+'.log')).read_text();row['child_failures']=re.findall(r'process has died[^\n]*',text)
  row['statistics_context_errors']=[l for l in text.splitlines() if 'Exception in publisher thread' in l];cleanup.append(row)
 result['shutdown']=cleanup
 try:
  capture('daemon-stop',['ros2','daemon','stop'],15);result['empty_after']=not capture('empty-after',['ros2','node','list','--no-daemon','--spin-time','2']).strip()
 except Exception as exc:result['cleanup_exception']=repr(exc)
 result['clean_shutdown']='PASS' if len(cleanup)==2 and all(r['exit_code']==0 and not r['escalated'] and not r['child_failures'] and not r['already_exited'] for r in cleanup) else 'FAIL'
 driver_after=fingerprint();write('driver-files-after.json',driver_after);result['driver_files_unchanged']=driver_after==driver_before;result['driver_files_count']=len(driver_before)
 result['ended_at']=datetime.now(timezone.utc).isoformat();write('summary.json',result)
 print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
sys.exit(0 if result['status']=='PASS_NATIVE_AND_COEXISTENCE_BLOCKED' and result['empty_after'] and result['clean_shutdown']=='PASS' else 1)
