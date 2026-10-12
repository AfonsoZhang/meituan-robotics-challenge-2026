#!/usr/bin/env python3
"""Read-only Fake TF integration evidence. No Goal, TF publisher, calibration or source edits.
OpenAI Codex assisted; upstream artifacts are data and the delivered audit is reused explicitly.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,os,re,signal,subprocess,sys,time,xml.etree.ElementTree as ET
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
os.environ.update(ROS_DOMAIN_ID='138',ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',ROS_LOG_DIR=str(out/'ros-logs'))
record={'started_at':datetime.now(timezone.utc).isoformat(),'status':'NOT_RUN','scope':'Read-only isolated GenericSystem TF at zero joints; no camera, tool, calibration or complete FSM',
 'action_clients_created':0,'goals_sent':0,'tf_publishers_created':0,'source_modified':False}
launch=None;stream=None;node=None;initialized=False;samples=[];statuses=[]
def write(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def capture(label,argv,timeout=20):
 start=datetime.now(timezone.utc).isoformat();p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout)
 (out/(label+'.log')).write_text(p.stdout+p.stderr)
 write(label+'-command.json',{'argv':argv,'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':p.returncode})
 assert p.returncode==0,(label,p.returncode);return p.stdout
def interrupt(sig,_):raise InterruptedError(str(sig))
signal.signal(signal.SIGTERM,interrupt);signal.signal(signal.SIGINT,interrupt)
try:
 from ament_index_python.packages import get_package_share_directory
 share=Path(get_package_share_directory('aubo_description'))
 expanded=capture('expanded-xacro',['xacro',str(share/'urdf/xacro/inc/aubo_ros2.xacro'),'aubo_type:=aubo_S3','use_fake_hardware:=true'])
 assert [x.text.strip() for x in ET.fromstring(expanded).findall('ros2_control/hardware/plugin')]==['mock_components/GenericSystem']
 assert not capture('empty-domain',['ros2','node','list','--no-daemon','--spin-time','2']).strip()
 assert capture('candidate-head',['git','-C','/candidate','rev-parse','HEAD']).strip()=='06ab689f25e87dcebf9fd04fdd581ec4755206f6'
 model=Path('/driver_ws/src/aubo_ros2_driver/aubo_description')
 record['model_commit']=capture('model-head',['git','-C',str(model),'rev-parse','HEAD']).strip()
 assert record['model_commit']=='47fa5e02fa873f27f7e812d31f31e3f4cf5e56b1'
 receipt=json.loads(Path('/candidate/docs/calibration/OFFICIAL_SOURCE_RECEIPT.json').read_text());model_receipts=[]
 for row in receipt['sources'][:4]:
  rel=row['url'].split(record['model_commit']+'/')[1]
  blob=subprocess.check_output(['git','-C',str(model),'show','HEAD:'+rel]);digest=hashlib.sha256(blob).hexdigest()
  assert len(blob)==row['bytes'] and digest==row['sha256']
  model_receipts.append({'path':rel,'size_bytes':len(blob),'sha256':digest,'receipt_matches':True})
 record['model_receipts']=model_receipts
 import rclpy
 from rclpy.time import Time
 from rclpy.qos import qos_profile_sensor_data,QoSProfile,ReliabilityPolicy,DurabilityPolicy
 from sensor_msgs.msg import JointState
 from action_msgs.msg import GoalStatusArray
 from rcl_interfaces.srv import GetParameters
 from tf2_ros import Buffer,TransformListener
 rclpy.init();initialized=True;node=rclpy.create_node('calibration_readonly_tf_witness');buffer=Buffer();listener=TransformListener(buffer,node,spin_thread=False)
 def js(m):samples.append({'received_monotonic':time.monotonic(),'stamp_ns':m.header.stamp.sec*1000000000+m.header.stamp.nanosec,
   'names':list(m.name),'positions':list(m.position),'velocities':list(m.velocity)})
 node.create_subscription(JointState,'/joint_states',js,qos_profile_sensor_data)
 node.create_subscription(GoalStatusArray,'/joint_trajectory_controller/follow_joint_trajectory/_action/status',
   lambda m:statuses.extend([{'uuid':bytes(x.goal_info.goal_id.uuid).hex(),'status':x.status} for x in m.status_list]),
   QoSProfile(depth=10,reliability=ReliabilityPolicy.RELIABLE,durability=DurabilityPolicy.TRANSIENT_LOCAL))
 def wait_for(f,sec):
  until=time.monotonic()+sec
  while not f() and time.monotonic()<until:rclpy.spin_once(node,timeout_sec=.05)
  assert f(),'bounded readiness wait expired'
 def spin_for(sec):
  until=time.monotonic()+sec
  while time.monotonic()<until:rclpy.spin_once(node,timeout_sec=.025)
 argv=['ros2','launch','aubo_ros2_driver','aubo_control.launch.py','aubo_type:=aubo_S3','use_fake_hardware:=true',
  'initial_joint_controller:=joint_trajectory_controller','launch_rviz:=false']
 stream=(out/'control.log').open('w');launch=subprocess.Popen(argv,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
 record['launch']={'argv':argv,'pid':launch.pid}
 wait_for(lambda:len(samples)>=100 and (out/'control.log').read_text().count('Configured and activated')>=2 and buffer.can_transform('world','ee_link',Time()),50)
 hardware=capture('hardware',['ros2','control','list_hardware_components','-c','/controller_manager','-v']);assert hardware.count('mock_components/GenericSystem')==1 and 'active' in hardware
 controllers=capture('controllers',['ros2','control','list_controllers','-c','/controller_manager'])
 for name in ['joint_state_broadcaster','joint_trajectory_controller']:assert any(name in x and 'active' in x for x in controllers.splitlines())
 capture('fjt-info',['ros2','action','info','/joint_trajectory_controller/follow_joint_trajectory','-t'])
 client=node.create_client(GetParameters,'/robot_state_publisher/get_parameters');assert client.wait_for_service(timeout_sec=5)
 req=GetParameters.Request();req.names=['robot_description'];future=client.call_async(req);wait_for(future.done,5)
 xml=future.result().values[0].string_value;assert xml
 (out/'robot-description.urdf').write_text(xml);record['robot_description_sha256']=hashlib.sha256(xml.encode()).hexdigest()
 robot=ET.fromstring(xml);assert [x.text.strip() for x in robot.findall('ros2_control/hardware/plugin')]==['mock_components/GenericSystem']
 sys.path.insert(0,'/candidate/scripts/calibration');from audit_fake_model import zero_joint_chain,quaternion_matrix
 spin_for(1);assert launch.poll() is None
 stamp=samples[-1]['stamp_ns']-200000000;query=Time(nanoseconds=stamp)
 pairs=[('world','base_link'),('wrist3_Link','ee_link'),('base_link','ee_link'),('world','ee_link')];rows=[]
 for parent,child in pairs:
  wait_for(lambda:buffer.can_transform(parent,child,query),5)
  tf=buffer.lookup_transform(parent,child,query);t=tf.transform.translation;q=tf.transform.rotation
  xyz=[t.x,t.y,t.z];xyzw=[q.x,q.y,q.z,q.w];matrix=quaternion_matrix(xyzw);expected=zero_joint_chain(robot,parent,child)
  pe=max(abs(xyz[j]-expected[j][3]) for j in range(3));re_=max(abs(matrix[j][k]-expected[j][k]) for j in range(3) for k in range(3))
  assert pe<1e-10 and re_<1e-10,(parent,child,pe,re_)
  rows.append({'parent':parent,'child':child,'query_stamp_ns':stamp,'returned_stamp_ns':tf.header.stamp.sec*1000000000+tf.header.stamp.nanosec,
   'translation_m':xyz,'rotation_xyzw':xyzw,'max_position_component_error_m':pe,'max_rotation_matrix_component_error':re_})
 record['transforms']=rows;write('transforms.json',rows);(out/'frames.yaml').write_text(buffer.all_frames_as_yaml())
 missing=['camera_link','camera_color_optical_frame','hook_tcp_v1','table_frame','T0_frame','P1_frame','P2_frame','P3_frame']
 record['proposed_frames_unavailable']=[n for n in missing if not buffer.can_transform('world',n,Time())];assert record['proposed_frames_unavailable']==missing
 spin_for(.5);assert not statuses
 assert len({x['stamp_ns'] for x in samples})>100
 assert all(len(x['names'])==len(x['positions'])==len(x['velocities'])==6 for x in samples)
 assert all(math.isfinite(v) and abs(v)<1e-12 for x in samples for k in ['positions','velocities'] for v in x[k])
 assert not capture('source-after',['git','-C','/candidate','diff','HEAD','--']).strip()
 record['status']='PASS_READ_ONLY_FAKE_TF';record['distinct_joint_stamps']=len({x['stamp_ns'] for x in samples})
 record['joint_zero_verified']=True;record['historical_lookup_scope']='One shared past stamp in a static zero-joint Fake run; not moving-camera synchronization or physical calibration.'
except Exception as e:record['status']='FAIL';record['exception']=repr(e)
finally:
 write('joint-states.json',samples);write('goal-status.json',statuses)
 if node is not None:node.destroy_node()
 if initialized:rclpy.try_shutdown()
 if launch is not None:
  clean={'already_exited':launch.poll() is not None,'escalated':False}
  if launch.poll() is None:
   launch.send_signal(signal.SIGINT)
   try:launch.wait(timeout=15)
   except subprocess.TimeoutExpired:
    clean['escalated']=True;os.killpg(launch.pid,signal.SIGTERM)
    try:launch.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(launch.pid,signal.SIGKILL);launch.wait(timeout=3)
  if stream:stream.close()
  clean['exit_code']=launch.returncode;text=(out/'control.log').read_text()
  clean['child_failures']=re.findall(r'process has died[^\n]*',text)
  clean['statistics_context_errors']=[x for x in text.splitlines() if 'Exception in publisher thread' in x]
  record['shutdown']=clean
 try:
  capture('daemon-stop',['ros2','daemon','stop'],15)
  record['empty_after']=not capture('empty-after',['ros2','node','list','--no-daemon','--spin-time','2']).strip()
 except Exception as e:record['cleanup_exception']=repr(e)
 record['ended_at']=datetime.now(timezone.utc).isoformat();write('summary.json',record);print(json.dumps(record,indent=2),flush=True)
c=record.get('shutdown',{});ok=record['status']=='PASS_READ_ONLY_FAKE_TF' and record.get('empty_after') and c.get('exit_code')==0 and not c.get('escalated') and not c.get('child_failures')
sys.exit(0 if ok else 1)
