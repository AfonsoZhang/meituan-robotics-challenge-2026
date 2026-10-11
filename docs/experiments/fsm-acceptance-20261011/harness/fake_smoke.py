#!/usr/bin/env python3
"""Independent GenericSystem acceptance; never select the real AUBO plugin.

OpenAI Codex assisted, 2026-10-11. Private container with no device mounts.
"""
from pathlib import Path
import json
import math
import os
import re
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

E=Path('/evidence/fake-smoke')
E.mkdir(parents=True)
os.environ.update(ROS_DOMAIN_ID='94', ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',
                  ROS_LOG_DIR=str(E/'ros-logs'), PYTHONDONTWRITEBYTECODE='1')
from ament_index_python.packages import get_package_share_directory
share=Path(get_package_share_directory('aubo_description'))
model=share/'urdf/aubo_S3.urdf.xacro'
assert model.is_file(), 'Missing generated S3 model'
cmd=['xacro',str(share/'urdf/xacro/inc/aubo_ros2.xacro'),
     'aubo_type:=aubo_S3','use_fake_hardware:=true']
xml=subprocess.check_output(cmd,text=True)
(E/'fake.urdf').write_text(xml)
plugins=[p.text.strip() for p in ET.fromstring(xml).findall('ros2_control/hardware/plugin')]
assert plugins==['mock_components/GenericSystem'], plugins
result={'plugins':plugins,'xacro_command':cmd,'trajectories':[]}
commands=[]
def capture(name,argv,timeout=15):
    try:
        p=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
        text=p.stdout;code=p.returncode
    except subprocess.TimeoutExpired as exc:
        text=exc.stdout or b''
        if isinstance(text,bytes):text=text.decode(errors='replace')
        code=124
    (E/(name+'.log')).write_text(text)
    commands.append({'name':name,'argv':argv,'exit_code':code})
    return text

assert not capture('preflight-nodes',['ros2','node','list','--no-daemon','--spin-time','2']).strip()
launch_cmd=['ros2','launch','aubo_ros2_driver','aubo_control.launch.py',
 'aubo_type:=aubo_S3','use_fake_hardware:=true',
 'initial_joint_controller:=joint_trajectory_controller','launch_rviz:=false']
log=(E/'launch.log').open('w')
launch=subprocess.Popen(launch_cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
try:
    import rclpy
    from rclpy.action import ActionClient
    from sensor_msgs.msg import JointState
    from trajectory_msgs.msg import JointTrajectoryPoint
    from control_msgs.action import FollowJointTrajectory
    from builtin_interfaces.msg import Duration
    from tf2_ros import Buffer, TransformListener
    from rosidl_runtime_py.convert import message_to_ordereddict
    rclpy.init()
    node=rclpy.create_node('acceptance_fake_driver_probe')
    samples=[]
    node.create_subscription(JointState,'/joint_states',lambda msg:samples.append(msg),10)
    buffer=Buffer(); listener=TransformListener(buffer,node)
    client=ActionClient(node,FollowJointTrajectory,'/joint_trajectory_controller/follow_joint_trajectory')
    assert client.wait_for_server(timeout_sec=45),'FJT server missing'
    deadline=time.monotonic()+8
    while time.monotonic()<deadline:
        rclpy.spin_once(node,timeout_sec=0.1)
    assert samples, 'JointState missing'
    names=['shoulder_joint','upperArm_joint','foreArm_joint','wrist1_joint','wrist2_joint','wrist3_joint']
    def positions():
        m=samples[-1];lookup=dict(zip(m.name,m.position))
        out=[lookup[n] for n in names]
        assert all(math.isfinite(x) for x in out)
        return out
    assert set(samples[-1].name)==set(names) and len(samples[-1].position)==6
    initial=positions()
    result['initial_joint_state']=message_to_ordereddict(samples[-1])
    stamps={(m.header.stamp.sec,m.header.stamp.nanosec) for m in samples}
    result['joint_state_samples']=len(samples)
    result['distinct_timestamps']=len(stamps)
    assert len(stamps)>2
    result['tf']={f'{parent}->{child}':message_to_ordereddict(
       buffer.lookup_transform(parent,child,rclpy.time.Time()))
       for parent,child in [('world','base_link'),('base_link','ee_link')]}
    hardware=capture('hardware',['ros2','control','list_hardware_components','-c','/controller_manager','-v'])
    assert hardware.count('mock_components/GenericSystem')==1 and 'active' in hardware,hardware
    controllers=capture('controllers',['ros2','control','list_controllers','-c','/controller_manager'])
    capture('interfaces',['ros2','control','list_hardware_interfaces','-c','/controller_manager'])
    capture('update-rate',['ros2','param','get','/controller_manager','update_rate'])
    capture('topics',['ros2','topic','list','-t'])
    capture('actions',['ros2','action','list','-t'])
    assert 'joint_state_broadcaster' in controllers and 'joint_trajectory_controller' in controllers
    plain=re.sub(r'\x1b\[[0-9;]*m','',controllers)
    states={parts[0]:parts[-1] for line in plain.splitlines() if (parts:=line.split()) and parts[0] in ('joint_state_broadcaster','joint_trajectory_controller')}
    assert states=={'joint_state_broadcaster':'active','joint_trajectory_controller':'active'},controllers
    result['controller_states']=states
    for label,waypoints in [('single',[(0.03,3)]),('multi',[(0.015,2),(0.0,4)])]:
        goal=FollowJointTrajectory.Goal()
        goal.trajectory.joint_names=names
        for offset,seconds in waypoints:
            p=initial.copy();p[-1]+=offset
            goal.trajectory.points.append(JointTrajectoryPoint(positions=p,time_from_start=Duration(sec=seconds)))
        future=client.send_goal_async(goal)
        rclpy.spin_until_future_complete(node,future,timeout_sec=8)
        assert future.done()
        handle=future.result();assert handle.accepted
        end=handle.get_result_async()
        rclpy.spin_until_future_complete(node,end,timeout_sec=15)
        assert end.done()
        for _ in range(10):rclpy.spin_once(node,timeout_sec=0.1)
        actual=positions();target=list(goal.trajectory.points[-1].positions)
        error=max(abs(a-b) for a,b in zip(actual,target))
        row={'case':label,'goal_uuid':bytes(handle.goal_id.uuid).hex(),
             'goal':message_to_ordereddict(goal),'result':message_to_ordereddict(end.result()),
             'actual_position_rad':actual,'max_error_rad':error}
        result['trajectories'].append(row)
        assert end.result().status==4 and end.result().result.error_code==0
        assert error<=0.001
    result['status']='PASS'
    client.destroy();node.destroy_node();rclpy.shutdown()
except Exception as exc:
    result['status']='FAIL';result['exception']=repr(exc)
    raise
finally:
    if launch.poll() is None:
        launch.send_signal(signal.SIGINT)
        try:launch.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(launch.pid,signal.SIGTERM);launch.wait(timeout=5)
    log.close()
    result['launch']=launch_cmd;result['launch_exit_code']=launch.returncode
    (E/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (E/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
