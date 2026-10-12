#!/usr/bin/env python3
"""Run delivered Phase 2B Fake probe modes with independent read-only observation.
OpenAI Codex assisted integration harness; no planner/FSM/port/driver modification.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,math,os,re,signal,subprocess,sys,time,xml.etree.ElementTree as ET
mode_to_run=sys.argv[2];domain=sys.argv[3]
assert mode_to_run in ['mismatch','cancel'] and domain in ['135','136']
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
os.environ.update(ROS_DOMAIN_ID=domain,ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',ROS_LOG_DIR=str(out/'ros-logs'))
record={'scope':'Delivered standalone FjtMotionPort/GenericSystem only; no MoveIt, complete FSM or physical device',
 'started_at':datetime.now(timezone.utc).isoformat(),'cases':[],'status':'NOT_RUN'}
launch=None;launch_log=None;node=None;initialized=False;live_case=None;live_log=None;samples=[];statuses=[]

def write(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def finite(v):
 if isinstance(v,float) and not math.isfinite(v):return None
 if isinstance(v,dict):return {k:finite(x) for k,x in v.items()}
 if isinstance(v,list):return [finite(x) for x in v]
 return v

def capture(label,argv,timeout=30):
 started=datetime.now(timezone.utc).isoformat();p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
 (out/(label+'.log')).write_text(p.stdout+p.stderr)
 write(label+'-command.json',{'argv':argv,'started_at':started,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':p.returncode})
 assert p.returncode==0,(label,p.returncode)
 return p.stdout

def interrupt(sig,_):raise InterruptedError(str(sig))
signal.signal(signal.SIGTERM,interrupt)
signal.signal(signal.SIGINT,interrupt)
try:
 from ament_index_python.packages import get_package_share_directory,get_package_prefix
 share=Path(get_package_share_directory('aubo_description'))
 assert str(share).startswith('/driver_work/install/') and (share/'urdf/aubo_S3.urdf.xacro').is_file()
 xml=capture('xacro',['xacro',str(share/'urdf/xacro/inc/aubo_ros2.xacro'),'aubo_type:=aubo_S3','use_fake_hardware:=true'])
 plugins=[p.text.strip() for p in ET.fromstring(xml).findall('ros2_control/hardware/plugin')]
 assert plugins==['mock_components/GenericSystem'];record['plugins']=plugins
 assert not capture('empty-domain',['ros2','node','list','--no-daemon','--spin-time','2']).strip()
 record['source']=capture('candidate-head',['git','-C','/candidate','rev-parse','HEAD']).strip()
 assert record['source']=='688d80d63ba2196e3c1753b69d18c1bfa30919b3'
 assert not capture('source-before',['git','-C','/candidate','diff','HEAD','--']).strip()
 import rclpy
 from rclpy.qos import qos_profile_sensor_data,QoSProfile,ReliabilityPolicy,DurabilityPolicy
 from sensor_msgs.msg import JointState
 from action_msgs.msg import GoalStatusArray
 rclpy.init();initialized=True;node=rclpy.create_node('phase2b_readonly_witness')
 def js(m):
  samples.append({'received_monotonic':time.monotonic(),'stamp_ns':m.header.stamp.sec*1000000000+m.header.stamp.nanosec,
   'names':list(m.name),'positions':list(m.position),'velocities':list(m.velocity)})
 def status(m):
  statuses.append({'received_monotonic':time.monotonic(),'goals':[{'uuid':bytes(x.goal_info.goal_id.uuid).hex(),'status':x.status,
   'accepted_stamp_ns':x.goal_info.stamp.sec*1000000000+x.goal_info.stamp.nanosec} for x in m.status_list]})
 node.create_subscription(JointState,'/joint_states',js,qos_profile_sensor_data)
 node.create_subscription(GoalStatusArray,'/joint_trajectory_controller/follow_joint_trajectory/_action/status',status,
   QoSProfile(depth=20,reliability=ReliabilityPolicy.RELIABLE,durability=DurabilityPolicy.TRANSIENT_LOCAL))
 def spin_for(sec):
  until=time.monotonic()+sec
  while time.monotonic()<until:rclpy.spin_once(node,timeout_sec=.05)
 def wait_for(fn,sec):
  until=time.monotonic()+sec
  while not fn() and time.monotonic()<until:rclpy.spin_once(node,timeout_sec=.05)
  assert fn(),'bounded observation wait expired'
 launch_argv=['ros2','launch','aubo_ros2_driver','aubo_control.launch.py','aubo_type:=aubo_S3','use_fake_hardware:=true',
  'initial_joint_controller:=joint_trajectory_controller','launch_rviz:=false']
 launch_log=(out/'control.log').open('w');launch=subprocess.Popen(launch_argv,stdout=launch_log,stderr=subprocess.STDOUT,start_new_session=True)
 record['launch']={'argv':launch_argv,'pid':launch.pid}
 wait_for(lambda:len(samples)>=40 and (out/'control.log').read_text().count('Configured and activated')>=2,50)
 hardware=capture('hardware',['ros2','control','list_hardware_components','-c','/controller_manager','-v'])
 assert hardware.count('mock_components/GenericSystem')==1 and 'active' in hardware
 ctrl=capture('controllers',['ros2','control','list_controllers','-c','/controller_manager'])
 for n in ['joint_trajectory_controller','joint_state_broadcaster']:assert any(n in line and 'active' in line for line in ctrl.splitlines())
 capture('fjt-action',['ros2','action','info','/joint_trajectory_controller/follow_joint_trajectory','-t'])
 record['observer_has_action_client']=False
 prefix=Path(get_package_prefix('mtc_trajectory_execution_cpp'));record['probe_binary']=str(prefix/'lib/mtc_trajectory_execution_cpp/fake_trajectory_probe')
 for mode in [mode_to_run]:
  spin_for(1);assert launch.poll() is None and samples
  sample_index=len(samples);status_index=len(statuses);seen={g['uuid'] for r in statuses for g in r['goals']}
  before=samples[-1];start=time.monotonic()
  argv=['ros2','run','mtc_trajectory_execution_cpp','fake_trajectory_probe','--verify-generic-system',mode]
  live_log=(out/(mode+'.log')).open('w');live_case=subprocess.Popen(argv,stdout=live_log,stderr=subprocess.STDOUT,start_new_session=True)
  until=time.monotonic()+30
  while live_case.poll() is None and time.monotonic()<until:rclpy.spin_once(node,timeout_sec=.025)
  assert live_case.poll() is not None,'delivered probe exceeded 30-second case limit'
  code=live_case.returncode;live_log.close();live_log=None;live_case=None
  probe_finished=time.monotonic();spin_for(.6)
  text=(out/(mode+'.log')).read_text()
  row={'mode':mode,'argv':argv,'start_monotonic':start,'probe_finished_monotonic':probe_finished,
   'observation_end_monotonic':time.monotonic(),'exit_code':code,'before':before,'after':samples[-1],
   'sample_index_range':[sample_index,len(samples)],'status_index_range':[status_index,len(statuses)],
   'new_goal_uuids':sorted({g['uuid'] for r in statuses for g in r['goals']}-seen),'log':mode+'.log'}
  record['cases'].append(row)
  assert code==0 and f'PASS: GenericSystem {mode}' in text,(mode,code,text)
  if mode=='mismatch':
   assert 'goals_sent=0 cancels_sent=0' in text and 'trajectory start differs' in text and not row['new_goal_uuids']
  else:
   match=re.search(r'UUID=([0-9a-f]{32})',text);assert match;row['uuid']=match.group(1)
   assert row['new_goal_uuids']==[row['uuid']],row['new_goal_uuids']
   row['observed_statuses']=sorted({g['status'] for r in statuses[status_index:] for g in r['goals'] if g['uuid']==row['uuid']})
   assert (4 if mode=='success' else 5) in row['observed_statuses'],row
   assert 'stop_confirmed=1' in text and 'status_unknown=0' in text and 'fault_locked=0' in text
   if mode=='cancel':assert 'cancel initial stop_confirmed=0' in text and 'goals_sent=1 cancels_sent=1' in text
  print('CASE_COMPLETED',mode,code,flush=True)
 record['status']='PASS_DELIVERED_REQUESTED_SCENARIO'
except Exception as e:
 record['status']='FAIL';record['exception']=repr(e)
finally:
 if live_case is not None and live_case.poll() is None:
  os.killpg(live_case.pid,signal.SIGTERM)
  try:live_case.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(live_case.pid,signal.SIGKILL);live_case.wait(timeout=3)
  record['case_cleanup_exit']=live_case.returncode
 if live_log is not None:live_log.close()
 write('joint-states.json',finite(samples));write('action-status.json',finite(statuses))
 if node is not None:node.destroy_node()
 if initialized:rclpy.try_shutdown()
 if launch is not None:
  cleanup={'already_exited':launch.poll() is not None,'escalated':False}
  if launch.poll() is None:
   launch.send_signal(signal.SIGINT)
   try:launch.wait(timeout=15)
   except subprocess.TimeoutExpired:
    cleanup['escalated']=True;os.killpg(launch.pid,signal.SIGTERM)
    try:launch.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(launch.pid,signal.SIGKILL);launch.wait(timeout=3)
  if launch_log:launch_log.close()
  cleanup['exit_code']=launch.returncode
  cleanup['child_failures']=re.findall(r'process has died[^\n]*',(out/'control.log').read_text())
  cleanup['pal_statistics_context_errors']=[l for l in (out/'control.log').read_text().splitlines() if 'Exception in publisher thread' in l]
  record['shutdown']=cleanup
 try:
  capture('daemon-stop',['ros2','daemon','stop'],15)
  left=capture('empty-after',['ros2','node','list','--no-daemon','--spin-time','2'])
  record['empty_after']=not left.strip()
 except Exception as e:record['cleanup_exception']=repr(e)
 record['ended_at']=datetime.now(timezone.utc).isoformat();record['samples']=len(samples);record['status_messages']=len(statuses)
 write('summary.json',finite(record));print(json.dumps(finite(record),ensure_ascii=False,indent=2),flush=True)
clean=record.get('shutdown',{});ok=record['status']=='PASS_DELIVERED_REQUESTED_SCENARIO' and record.get('empty_after') and clean.get('exit_code')==0 and not clean.get('escalated') and not clean.get('already_exited') and not clean.get('child_failures')
sys.exit(0 if ok else 1)
