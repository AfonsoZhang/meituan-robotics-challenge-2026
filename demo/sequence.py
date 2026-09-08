"""Three observed picks in one Gazebo world; stop and retain evidence on failure."""
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from record import (Recorder, spin_until, observe_yellow, save, FollowJointTrajectory,
                    JointTrajectoryPoint, JOINTS, MODELS, ROOT)
from metrics import schedule, evaluate, footprint
from gazebo_msgs.msg import ContactsState
from vision import OBSERVER, SIDE_OBSERVER, translated_plan

TASKS = [('yellow',MODELS[1],[.0416,.3639]),
         ('green',MODELS[2],[.2166,.3639]),('blue',MODELS[3],[.2166,.1889])]


def execute_sequence(out, desc, timeout):
    full=json.loads((ROOT/'data/sequence-v1.json').read_text())
    report=dict(mode='three_observed_picks',passed=False,stages=[],
                limitation='Example order; pre-grasp RGB-D updates only. No continuous visual servo or complete collision audit.')
    wall_start=time.monotonic();first_sim=None;final_poses=None
    save(out/'sequence-inputs.json',{'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()
         for p in [ROOT/'sequence.py',ROOT/'record.py',ROOT/'vision.py',ROOT/'metrics.py',ROOT/'detector.py']},
         'tasks':TASKS,'ai_assistance':'OpenAI Codex; historical detector and trajectory: Claude Code'})
    for color,model,target in TASKS:
        stage=out/color;stage.mkdir()
        plan=[p for p in full if p['name'].startswith(color+':')]
        save(stage/'nominal-plan.json',plan)
        node=Recorder(stage,desc,plan,node_name="sequence_"+color);node.task_label=f'{color} -> P{len(report["stages"])+1}'
        node.vision_mode='correct'
        result=dict(color=color,model=model,target=target,passed=False)
        contacts=[]
        def contact_message(msg):
            if msg.states:
                contacts.append({'sim_s':msg.header.stamp.sec+msg.header.stamp.nanosec/1e9,
                    'elapsed_s':node.now()-node.start_sim if node.start_sim is not None else None,
                    'pairs':sorted(set(tuple(sorted((s.collision1_name,s.collision2_name))) for s in msg.states))})
        node.create_subscription(ContactsState,'/demo/blue_contacts',contact_message,10)
        try:
            spin_until(node,lambda: bool(node.poses) and node.joints is not None and node.overview is not None
                       and node.action.server_is_ready(),30,'Stage state unavailable')
            if first_sim is None:first_sim=node.now()
            if np.max(np.abs(node.joints-np.array(plan[0]['q'])))>.02:
                raise RuntimeError('Stage start does not match previous retreat')
            result['vision']=observe_yellow(node,color,OBSERVER if color=='yellow' else SIDE_OBSERVER)
            plan,residual=translated_plan(node.kin,plan,np.array(result['vision']['delta_xy_m']),transition_points=4)
            result['vision']['ik_max_weighted_residual']=residual
            node.plan,node.times=plan,schedule(plan)
            save(stage/'corrected-plan.json',plan)
            node.start_video();settle=node.now()
            spin_until(node,lambda:node.now()-settle>=2.,30,'Stage pre-record settling timed out')
            initial=node.poses;node.start_sim=node.now()
            goal=FollowJointTrajectory.Goal();goal.trajectory.joint_names=JOINTS
            for point,t in zip(plan,node.times):
                p=JointTrajectoryPoint();p.positions=point['q']
                p.time_from_start.sec=int(t);p.time_from_start.nanosec=int((t-int(t))*1e9)
                goal.trajectory.points.append(p)
            f=node.action.send_goal_async(goal)
            spin_until(node,f.done,15,'Stage goal response timeout');handle=f.result()
            if not handle.accepted:raise RuntimeError('Stage goal rejected')
            f=handle.get_result_async()
            print(f'SEQUENCE {color}: {node.times[-1]:.2f} planned seconds',flush=True)
            spin_until(node,lambda:f.done() and node.now()-node.start_sim>=node.times[-1]+5.,timeout,'Stage motion timeout')
            action=f.result()
            result.update(evaluate(node.samples,initial,node.times[-1],model=model,target=np.array(target)),
                          action_status=action.status,controller_error_code=action.result.error_code)
            result['passed']=bool(result['passed'] and action.status==4 and action.result.error_code==0)
            result.update(video_seconds=node.frames/15.,tracking_samples=len(node.errors),
                          tcp_tracking_error_mm={'rms':float(np.sqrt(np.mean(np.square(node.errors)))), 'max':max(node.errors)})
            final_poses=node.poses
            report['simulated_elapsed_s']=node.now()-first_sim
        except Exception as exc:
            result.update(passed=False,error=f'{type(exc).__name__}: {exc}')
        finally:
            try:node.close()
            except Exception as exc:result.update(passed=False,close_error=str(exc))
            node.destroy_node();save(stage/'blue-contacts.json',contacts)
            result['blue_contact_samples']=len(contacts)
            save(stage/'summary.json',result)
        report['stages'].append(result)
        save(out/'sequence-progress.json',report)
        print(json.dumps({'color':color,'passed':result['passed'],'error':result.get('error'),
                          'center_error_mm':result.get('center_error_mm')},ensure_ascii=False),flush=True)
        if not result['passed']:break
    if len(report['stages'])==3 and all(s['passed'] for s in report['stages']):
        report['final_placements']={color:footprint(final_poses[model],np.array(target)) for color,model,target in TASKS}
        report['passed']=all(p['upright'] and p['coverage']>=.7 and p['inside_outer'] for p in report['final_placements'].values())
    report['wall_elapsed_s']=time.monotonic()-wall_start
    report['not_executed']=[t[0] for t in TASKS[len(report['stages']):]]
    return report
