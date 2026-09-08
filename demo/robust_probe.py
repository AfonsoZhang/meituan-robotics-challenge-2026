"""Fixed high-workspace effort-control experiment; external force is not feedback."""
import math
import json
from pathlib import Path
import numpy as np


def reference(q0, kin):
    out=[];amp=np.array([.03,.025,-.03,.03,-.025,.03])
    for t in np.arange(.1,24.0001,.1):
        u=(t-2)/12
        f=df=ddf=0.
        if 0<u<1:
            f=.5*math.sin(2*math.pi*u)-.25*math.sin(4*math.pi*u)
            df=(math.pi*math.cos(2*math.pi*u)-math.pi*math.cos(4*math.pi*u))/12
            ddf=(-2*math.pi**2*math.sin(2*math.pi*u)+4*math.pi**2*math.sin(4*math.pi*u))/144
        q=np.array(q0)+amp*f
        if not kin.startup_clear(q,{}):raise ValueError('Probe leaves high-workspace clearance envelope')
        out.append(dict(name='probe:reference',q=q.tolist(),dq=(amp*df).tolist(),ddq=(amp*ddf).tolist(),
                        t=float(t),tcp=kin.tcp(q).tolist()))
    return out


def enable_compensation(node):
    from rcl_interfaces.srv import SetParameters
    from rclpy.parameter import Parameter
    from record import spin_until
    client=node.create_client(SetParameters,'/joint_trajectory_controller/set_parameters')
    spin_until(node,client.service_is_ready,15,'Effort-controller parameter service unavailable')
    request=SetParameters.Request()
    request.parameters=[Parameter('robust.gravity_enabled',value=True).to_parameter_msg()]
    f=client.call_async(request);spin_until(node,f.done,10,'Gravity compensation enable timeout')
    if not all(r.successful for r in f.result().results):raise RuntimeError('Gravity compensation not enabled')
    node.destroy_client(client)


def disturb(node, magnitude):
    from gazebo_msgs.srv import ApplyJointEffort
    from record import spin_until, save
    client=node.create_client(ApplyJointEffort,'/apply_joint_effort')
    spin_until(node,client.service_is_ready,15,'Gazebo force-system service unavailable')
    requests=[]
    if magnitude:
        for start,effort in [(8.,magnitude),(16.,-magnitude)]:
            r=ApplyJointEffort.Request();r.joint_name='aubo_S3::upperArm_joint';r.effort=effort
            t=node.start_sim+start;r.start_time.sec=int(t);r.start_time.nanosec=int((t-int(t))*1e9)
            r.duration.sec=2
            f=client.call_async(r);spin_until(node,f.done,10,'Disturbance request timeout')
            if not f.result().success:raise RuntimeError(f.result().status_message)
            requests.append(dict(joint=r.joint_name,effort_nm=effort,start_elapsed_s=start,duration_s=2.,accepted=True))
    save(node.out/'disturbances.json',requests);node.destroy_client(client)
    return requests


def evaluate_probe(node,initial):
    node.track_file.flush();node.audit_file.flush()
    a=np.genfromtxt(node.out/'tracking.csv',delimiter=',',names=True)
    effort=np.genfromtxt(node.out/'effort-audit.csv',delimiter=',',names=True)
    if len(effort)<100:raise RuntimeError('Insufficient effort audit samples')
    stamps=effort['sim_s']-node.start_sim
    desired=np.column_stack([effort['desired_'+str(i)] for i in range(6)])
    actual=np.column_stack([effort['actual_'+str(i)] for i in range(6)])
    tcp=np.array([np.linalg.norm(node.kin.tcp(q)-node.kin.tcp(qd))*1000 for q,qd in zip(actual,desired)])
    windows={}
    for name,start,end in [('motion',2,14),('moving_disturbance',8,10),('holding_disturbance',16,18),('recovered',20,24)]:
        mask=(stamps>=start)&(stamps<=end)
        if np.count_nonzero(mask)<100:raise RuntimeError('Insufficient probe samples: '+name)
        if np.max(np.diff(stamps[mask]))>.1:raise RuntimeError('Probe audit gaps: '+name)
        error=(actual[:,1]-desired[:,1])[mask]
        windows[name]=dict(samples=int(np.count_nonzero(mask)),tcp_rms_mm=float(np.sqrt(np.mean(tcp[mask]**2))),
                           tcp_max_mm=float(np.max(tcp[mask])),
                           upper_arm_rms_rad=float(np.sqrt(np.mean(error**2))))
    moved=max(float(np.linalg.norm(np.array(s['poses'][n][:3])-initial[n][:3])) for s in node.samples for n in initial)
    saturation=sum(int(np.count_nonzero(np.abs(effort['raw_'+str(i)]-effort['applied_'+str(i)])>1e-8)) for i in range(6))
    return dict(passed=bool(windows['recovered']['tcp_max_mm']<10 and moved<.002),
                scope='High-workspace arm tracking under external joint torques; no grasp attempted',windows=windows,
                saturated_joint_samples=saturation,audit_samples=len(effort),max_battery_displacement_m=moved,
                max_sliding_term_nm=[float(np.max(abs(effort['robust_'+str(i)]))) for i in range(6)])
