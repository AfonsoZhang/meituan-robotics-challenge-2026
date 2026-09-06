"""Record an isolated Gazebo-only yellow-to-P1 demo with traceable measurements.

No hardware interfaces; no object attachment; no GUI automation. The video follows
sensor simulation timestamps (CFR, holding frames across gaps), not wall time.
"""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

import cv2
import numpy as np
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from ament_index_python.packages import get_package_share_directory
from control_msgs.action import FollowJointTrajectory
from control_msgs.msg import JointTrajectoryControllerState
from gazebo_msgs.msg import ModelStates
from gazebo_msgs.srv import GetLinkProperties, SetLinkProperties
from sensor_msgs.msg import Image
from trajectory_msgs.msg import JointTrajectoryPoint

from metrics import JOINTS, MODELS, Kinematics, schedule, evaluate

ROOT = Path(__file__).resolve().parent


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def prepare(out):
    sim = Path(get_package_share_directory('meituan_sim'))
    desc = Path(get_package_share_directory('aubo_description'))
    world = ET.parse(sim/'worlds/task_p2.world')
    w = world.getroot().find('world')
    scene = ET.SubElement(w,'scene')
    ET.SubElement(scene,'ambient').text = '0.45 0.45 0.45 1'
    ET.SubElement(scene,'background').text = '0.92 0.94 0.96 1'
    ET.SubElement(scene,'shadows').text = 'false'
    plugin = ET.SubElement(w, 'plugin', name='demo_states', filename='libgazebo_ros_state.so')
    ET.SubElement(ET.SubElement(plugin, 'ros'), 'namespace').text = '/gazebo'
    ET.SubElement(plugin, 'update_rate').text = '30'
    props = ET.SubElement(w, 'plugin', name='demo_properties', filename='libgazebo_ros_properties.so')
    ET.SubElement(ET.SubElement(props,'ros'),'namespace').text = '/gazebo'
    # Presentation-only spectator camera; it does not enter the control loop.
    model = ET.SubElement(w, 'model', name='demo_overview')
    ET.SubElement(model, 'static').text = 'true'
    ET.SubElement(model, 'pose').text = '0.85 0.75 0.85 0 0.55 -2.5673'
    sensor = ET.SubElement(ET.SubElement(model, 'link', name='link'), 'sensor', type='camera', name='overview')
    ET.SubElement(sensor, 'update_rate').text = '15'
    ET.SubElement(sensor, 'always_on').text = 'true'
    camera = ET.SubElement(sensor, 'camera', name='overview')
    ET.SubElement(camera, 'horizontal_fov').text = '1.20'
    image = ET.SubElement(camera, 'image')
    for k,v in {'width':'1280','height':'720','format':'R8G8B8'}.items(): ET.SubElement(image,k).text=v
    clip = ET.SubElement(camera, 'clip')
    ET.SubElement(clip,'near').text = '0.03'
    ET.SubElement(clip,'far').text = '20'
    cp = ET.SubElement(sensor,'plugin',name='demo_camera',filename='libgazebo_ros_camera.so')
    ET.SubElement(ET.SubElement(cp,'ros'),'namespace').text = '/demo'
    ET.SubElement(cp,'frame_name').text = 'demo_overview'
    world.write(out/'world.sdf', encoding='unicode')
    full = json.loads((ROOT/'data/sequence-v1.json').read_text())
    plan = []
    for p in full:
        if not p['name'].startswith('yellow:'): break
        plan.append(p)
    assert plan and all(p['col'] <= 1 and len(p['q']) == 6 for p in plan)
    save(out/'plan.json', plan)
    files = [ROOT/'data/sequence-v1.json', ROOT/'record.py', ROOT/'metrics.py', ROOT/'simulation.launch.py',
             sim/'urdf/aubo_S3_gazebo.urdf.xacro', sim/'urdf/hook.urdf.xacro', sim/'urdf/d435i.urdf.xacro',
             sim/'config/aubo_S3_controllers.yaml', desc/'urdf/aubo_S3.urdf']
    save(out/'inputs.json', {'ai_assistance':'OpenAI Codex; historical trajectory: Claude Code',
         'trajectory_provenance':json.loads((ROOT/'data/provenance.json').read_text()),
         'files':[{'path':str(p), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
         'mode':'simulation only; open-loop yellow to P1; example task',
         'planned_seconds':schedule(plan)[-1], 'waypoints':len(plan),
         'video_clock':'simulation sensor time, 15 fps; frames held across delivery gaps',
         'initialization':'Robot link gravity disabled only during controller startup; restored and verified before recording. Battery gravity unchanged.',
         'limitations':['No formal safety proof or full competition score', 'No contact-pair monitor',
                        'Nominal model, ideal camera; no real hardware validation']})
    return sim, desc, plan


class Recorder(Node):
    def __init__(self, out, desc, plan):
        super().__init__('demo_recorder', parameter_overrides=[Parameter('use_sim_time', value=True)])
        self.out, self.plan, self.times = out, plan, schedule(plan)
        self.kin = Kinematics(desc/'urdf/aubo_S3.urdf')
        self.poses, self.joints, self.wrist, self.overview = {}, None, None, None
        self.models_wall, self.joints_wall = 0., 0.
        self.start_sim, self.first_frame, self.frames = None, None, 0
        self.received_frames, self.held_frames, self.max_camera_gap, self.last_camera_stamp = 0, 0, 0., None
        self.wall_start = time.monotonic()
        self.samples, self.errors, self.prev_frame, self.video = [], [], None, None
        self.last_sample, self.last_tracking = -1., -1.
        self.video_log = None
        self.track_file = (out/'tracking.csv').open('w', newline='')
        self.track = csv.writer(self.track_file)
        self.track.writerow(['sim_s','elapsed_s','desired_tcp_x','desired_tcp_y','desired_tcp_z',
                             'actual_tcp_x','actual_tcp_y','actual_tcp_z','tcp_tracking_error_mm','max_joint_error_rad'])
        self.state_file = (out/'model_states.jsonl').open('w')
        self.create_subscription(ModelStates, '/gazebo/model_states', self.models, 10)
        self.create_subscription(JointTrajectoryControllerState, '/joint_trajectory_controller/controller_state', self.controller, 10)
        self.create_subscription(Image, '/d435i/color/image_raw', self.wrist_image, qos_profile_sensor_data)
        self.create_subscription(Image, '/demo/overview/image_raw', self.frame, qos_profile_sensor_data)
        self.action = ActionClient(self, FollowJointTrajectory, '/joint_trajectory_controller/follow_joint_trajectory')

    def now(self):
        return self.get_clock().now().nanoseconds/1e9

    @staticmethod
    def bgr(msg):
        if msg.encoding not in ('rgb8', 'bgr8'): raise RuntimeError('Unexpected image encoding: '+msg.encoding)
        rows = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)
        a = rows[:, :msg.width*3].reshape(msg.height,msg.width,3)
        return (a[:,:,::-1] if msg.encoding == 'rgb8' else a).copy()

    def wrist_image(self, msg):
        self.wrist = self.bgr(msg)

    def models(self, msg):
        table = dict(zip(msg.name,msg.pose))
        if not all(n in table for n in MODELS): return
        self.models_wall = time.monotonic()
        self.poses = {n:[p.position.x,p.position.y,p.position.z,p.orientation.x,p.orientation.y,p.orientation.z,p.orientation.w]
                      for n in MODELS for p in [table[n]]}
        if self.start_sim is not None:
            t = self.now()-self.start_sim
            if t-self.last_sample >= .025:
                sample = {'t':t,'poses':self.poses}
                self.samples.append(sample)
                self.state_file.write(json.dumps(sample)+'\n')
                self.last_sample = t

    def controller(self, msg):
        if len(msg.actual.positions) != 6 or len(msg.desired.positions) != 6: return
        self.joints_wall = time.monotonic()
        idx = [msg.joint_names.index(n) for n in JOINTS]
        actual = np.array(msg.actual.positions)[idx]
        desired = np.array(msg.desired.positions)[idx]
        self.joints = actual
        if self.start_sim is None: return
        stamp = msg.header.stamp.sec+msg.header.stamp.nanosec/1e9
        if stamp-self.last_tracking < .045: return
        self.last_tracking = stamp
        a, d = self.kin.tcp(actual), self.kin.tcp(desired)
        error = float(np.linalg.norm(a-d)*1000)
        self.errors.append(error)
        self.track.writerow([stamp,stamp-self.start_sim,*d,*a,error,float(np.max(np.abs(actual-desired)))])

    def start_video(self):
        self.video_log = (self.out/'ffmpeg.log').open('w')
        self.video = subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','warning','-y',
            '-f','rawvideo','-pixel_format','bgr24','-video_size','1600x880','-framerate','15','-i','pipe:0',
            '-an','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',
            str(self.out/'demo.mp4')], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self.video_log)

    def frame(self, msg):
        self.overview = self.bgr(msg)
        if self.video is None: return
        stamp = msg.header.stamp.sec+msg.header.stamp.nanosec/1e9
        if self.first_frame is None: self.first_frame = stamp
        if self.last_camera_stamp is not None:
            self.max_camera_gap = max(self.max_camera_gap,stamp-self.last_camera_stamp)
        self.last_camera_stamp = stamp
        self.received_frames += 1
        frame_number = int(round((stamp-self.first_frame)*15))
        if frame_number < self.frames: return
        canvas = np.full((880,1600,3), 22, dtype=np.uint8)
        canvas[:720,:1280] = self.overview
        if self.wrist is not None: canvas[50:290,1280:1600] = cv2.resize(self.wrist,(320,240))
        elapsed = self.now()-self.start_sim if self.start_sim is not None else 0.
        phase = 'settling'
        if self.start_sim is not None:
            i = int(np.searchsorted(self.times, elapsed))
            if i >= len(self.plan): phase = 'post-motion observation'
            else:
                stage = self.plan[i]['name'].split(':')[-1]
                phases = {'transit':'approach','1_':'ready','2_':'insert','3_':'lift','4_':'transfer',
                          '5_':'lower','6_':'unload','7_':'clear tip','8_':'withdraw','9_':'retreat'}
                phase = next((v for k,v in phases.items() if stage.startswith(k)), 'transition')
        lines = [('SIMULATION | AUBO S3 + passive hook | yellow -> P1', (20,758)),
                 (f'Sim elapsed {elapsed:6.2f} s | wall elapsed {time.monotonic()-self.wall_start:6.1f} s | planned stage: {phase}', (20,795)),
                 ('Open-loop trajectory. Ideal RGB-D shown separately. Outcome evaluated after release.', (20,835)),
                 ('Wrist RGB', (1300,32)), ('44 mm tongue', (1295,330)), ('5 mm thickness', (1295,365)),
                 ('5 mm raised tip', (1295,400)), ('No object attachment', (1295,450)),
                 ('Sensor-time video', (1295,495)), ('15 fps', (1295,530))]
        for txt,xy in lines: cv2.putText(canvas,txt,xy,cv2.FONT_HERSHEY_SIMPLEX,.60,(225,225,225),1,cv2.LINE_AA)
        if self.prev_frame is not None:
            missing = max(0,frame_number-self.frames)
            self.held_frames += missing
            for _ in range(missing):
                self.video.stdin.write(self.prev_frame.tobytes()); self.frames += 1
        self.video.stdin.write(canvas.tobytes()); self.frames += 1
        if self.prev_frame is None: cv2.imwrite(str(self.out/'first-frame.png'),canvas)
        self.prev_frame = canvas

    def close(self):
        self.track_file.close(); self.state_file.close()
        if self.video is not None:
            self.video.stdin.close()
            if self.video.wait(timeout=30) != 0: raise RuntimeError('ffmpeg failed; see ffmpeg.log')
            self.video_log.close()
        if self.prev_frame is not None: cv2.imwrite(str(self.out/'last-frame.png'),self.prev_frame)


def spin_until(node, condition, seconds, label):
    deadline = time.monotonic()+seconds
    while not condition():
        if time.monotonic() > deadline: raise TimeoutError(label)
        rclpy.spin_once(node, timeout_sec=.05)


def recover_start(node, target):
    actual = node.joints.copy()
    error = float(np.max(np.abs(actual-target)))
    if error <= .02: return {'required':False,'initial_max_error_rad':error}
    if error > .25: raise RuntimeError(f'Startup displacement too large for local recovery: {error:.4f} rad')
    bridge = [actual+(target-actual)*u for u in np.linspace(0,1,51)]
    if not all(node.kin.startup_clear(q,node.poses) for q in bridge):
        raise RuntimeError('Startup recovery rejected by discrete capsule/height check')
    initial = node.poses
    goal = FollowJointTrajectory.Goal(); goal.trajectory.joint_names = JOINTS
    for q,t in [(actual,.2),(target,3.)]:
        p = JointTrajectoryPoint(); p.positions = q.tolist()
        p.time_from_start.sec = int(t); p.time_from_start.nanosec = int((t-int(t))*1e9)
        goal.trajectory.points.append(p)
    future = node.action.send_goal_async(goal)
    spin_until(node,future.done,15,'Startup recovery goal response timed out')
    handle = future.result()
    if not handle.accepted: raise RuntimeError('Startup recovery rejected by controller')
    result = handle.get_result_async()
    spin_until(node,result.done,60,'Startup recovery timed out')
    if result.result().status != 4 or result.result().result.error_code != 0:
        raise RuntimeError('Startup recovery controller failure')
    settle = node.now()
    spin_until(node,lambda:node.now()-settle>=2.,45,'Startup recovery settling timed out')
    final_error = float(np.max(np.abs(node.joints-target)))
    moved = max(float(np.linalg.norm(np.array(node.poses[n][:3])-initial[n][:3])) for n in MODELS)
    if final_error > .02 or moved > .002:
        raise RuntimeError(f'Startup recovery failed verification: {final_error:.4f} rad, battery displacement {moved:.5f} m')
    return {'required':True,'initial_max_error_rad':error,'final_max_error_rad':final_error,
            'max_battery_endpoint_displacement_m':moved,'checked_bridge_samples':51,
            'note':'Small high-workspace recovery before recording; gravity unchanged; no object repositioning.'}


def enable_robot_gravity(node):
    get = node.create_client(GetLinkProperties,'/gazebo/get_link_properties')
    set_ = node.create_client(SetLinkProperties,'/gazebo/set_link_properties')
    spin_until(node,lambda:get.service_is_ready() and set_.service_is_ready(),20,'Link property services unavailable')
    verified = []
    for link in ('shoulder_Link','upperArm_Link','foreArm_Link','wrist1_Link','wrist2_Link','wrist3_Link'):
        name = 'aubo_S3::'+link
        request = GetLinkProperties.Request(); request.link_name = name
        future = get.call_async(request)
        spin_until(node,future.done,10,'Read initial link properties timeout')
        before = future.result()
        if not before.success: raise RuntimeError(before.status_message)
        req = SetLinkProperties.Request(); req.link_name = name; req.gravity_mode = True
        for field in ('com','mass','ixx','ixy','ixz','iyy','iyz','izz'): setattr(req,field,getattr(before,field))
        future = set_.call_async(req)
        spin_until(node,future.done,10,'Restore robot link gravity timeout')
        if not future.result().success: raise RuntimeError(future.result().status_message)
        future = get.call_async(request)
        spin_until(node,future.done,10,'Verify restored gravity timeout')
        after = future.result()
        if not after.success or not after.gravity_mode: raise RuntimeError('Gravity restoration not verified: '+name)
        for field in ('mass','ixx','ixy','ixz','iyy','iyz','izz'):
            if abs(getattr(after,field)-getattr(before,field)) > 1e-9: raise RuntimeError('Inertial property changed: '+name)
        verified.append({'link':name,'gravity_enabled':after.gravity_mode,'mass':after.mass})
    node.destroy_client(get); node.destroy_client(set_)
    save(node.out/'startup-gravity.json',verified)
    return verified


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true', help='Recover the start posture, then record five stationary simulated seconds')
    parser.add_argument('--check', action='store_true', help='Prepare inputs without starting Gazebo')
    parser.add_argument('--timeout', type=float, default=900, help='Wall-clock timeout for motion/recording')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    out = (args.output or ROOT.parent/'outputs'/('demo-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    out.mkdir(parents=True, exist_ok=False)
    sim, desc, plan = prepare(out)
    if args.check:
        print(f'Prepared {len(plan)} yellow waypoints, {schedule(plan)[-1]:.3f} planned seconds: {out}')
        return 0
    os.environ.update(ROS_DOMAIN_ID='67', GAZEBO_MASTER_URI='http://127.0.0.1:11365',
                      GAZEBO_IP='127.0.0.1', GAZEBO_MODEL_DATABASE_URI='', DEMO_WORLD=str(out/'world.sdf'),
                      ROS_LOG_DIR=str(out/'ros-logs'))
    os.environ['GAZEBO_MODEL_PATH'] = os.pathsep.join(['/usr/share/gazebo-11/models',str(desc.parent),str(sim/'models'),os.environ.get('GAZEBO_MODEL_PATH','')])
    os.environ['GAZEBO_RESOURCE_PATH'] = os.pathsep.join(['/usr/share/gazebo-11',os.environ.get('GAZEBO_RESOURCE_PATH','')])
    server = node = log = None
    report, code = {'passed':False,'mode':'smoke' if args.smoke else 'yellow_to_P1'}, 1
    try:
        log = (out/'launch.log').open('w')
        server = subprocess.Popen(['ros2','launch',str(ROOT/'simulation.launch.py')],
                                  stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        rclpy.init()
        node = Recorder(out,desc,plan)
        spin_until(node, lambda: bool(node.poses) and node.joints is not None and node.overview is not None
                   and node.action.server_is_ready(), 100, 'Simulation, cameras or controller did not become ready')
        report['gravity_restored_before_recording'] = enable_robot_gravity(node)
        ready_time = node.now()
        spin_until(node, lambda: node.now()-ready_time >= 3., 60, 'Controller startup settling timed out')
        if time.monotonic()-min(node.models_wall,node.joints_wall) > 2: raise RuntimeError('Stale startup state')
        report['startup_recovery'] = recover_start(node,np.array(plan[0]['q']))
        initial = node.poses
        node.start_video()
        settle = node.now()
        spin_until(node,lambda:node.now()-settle>=2.,60,'Pre-record settling timed out')
        initial = node.poses
        node.start_sim = node.now()
        if args.smoke:
            spin_until(node,lambda:node.now()-node.start_sim>=5.,args.timeout,'Smoke recording timed out')
            report.update(passed=node.frames>0, simulated_seconds=node.now()-node.start_sim,
                          note='Stationary camera test only; no grasp executed')
        else:
            goal = FollowJointTrajectory.Goal()
            goal.trajectory.joint_names = JOINTS
            for point,t in zip(plan,node.times):
                p = JointTrajectoryPoint(); p.positions = point['q']
                p.time_from_start.sec = int(t); p.time_from_start.nanosec = int((t-int(t))*1e9)
                goal.trajectory.points.append(p)
            future = node.action.send_goal_async(goal)
            spin_until(node,future.done,15,'Goal response timeout')
            handle = future.result()
            if not handle.accepted: raise RuntimeError('Controller rejected trajectory')
            result = handle.get_result_async()
            print(f'Recording yellow -> P1, {node.times[-1]:.2f} planned seconds. Output: {out}',flush=True)
            spin_until(node,lambda:result.done() and node.now()-node.start_sim>=node.times[-1]+5.,
                       args.timeout,'Trajectory/observation timeout')
            action_result = result.result()
            checks = evaluate(node.samples,initial,node.times[-1])
            report.update(checks, action_status=action_result.status,
                          controller_error_code=action_result.result.error_code,
                          controller_error_string=action_result.result.error_string)
            report['passed'] = bool(checks['passed'] and action_result.status == 4 and action_result.result.error_code == 0)
        report.update(frames=node.frames, camera_frames_received=node.received_frames,
                      held_frames=node.held_frames,max_camera_timestamp_gap_s=node.max_camera_gap,
                      video_seconds=node.frames/15., wall_elapsed_s=time.monotonic()-node.wall_start,
                      tracking_samples=len(node.errors),
                      tcp_tracking_error_mm={'rms':float(np.sqrt(np.mean(np.square(node.errors)))),
                                             'max':max(node.errors)} if node.errors else None)
        code = 0 if report['passed'] else 2
    except Exception as exc:
        report.update(passed=False,error=f'{type(exc).__name__}: {exc}')
        print(report['error'],flush=True)
    finally:
        if node is not None:
            try: node.close()
            except Exception as exc: report.update(passed=False,video_error=str(exc)); code=1
            node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()
        if server is not None:
            try:
                os.killpg(server.pid,signal.SIGINT); server.wait(timeout=15)
            except (ProcessLookupError,subprocess.TimeoutExpired):
                try: os.killpg(server.pid,signal.SIGKILL)
                except ProcessLookupError: pass
        if log: log.close()
        save(out/'summary.json',report)
        print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
        print(f'Artifacts: {out}',flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
