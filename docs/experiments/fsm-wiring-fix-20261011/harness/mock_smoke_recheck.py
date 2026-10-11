#!/usr/bin/env python3
"""Record actual Mock graph and a bounded Goal after B01/B02/B04 wiring fixes.

OpenAI Codex assisted acceptance harness. Run only in an isolated container
with the locked source, backend=mock, and no AUBO hardware launch.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import time

E = Path('/fix-evidence/mock-smoke-recheck')
E.mkdir(parents=True)
env = os.environ.copy()
env.update(ROS_DOMAIN_ID='95', ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',
           ROS_LOG_DIR=str(E/'ros-logs'), PYTHONDONTWRITEBYTECODE='1')
os.environ.update(env)
commands=[]

def capture(name, argv, timeout=12):
    try:
        p=subprocess.run(argv,env=env,text=True,stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,timeout=timeout)
        output=p.stdout; code=p.returncode
    except subprocess.TimeoutExpired as exc:
        output=exc.stdout or b''
        if isinstance(output,bytes): output=output.decode(errors='replace')
        code=124
    (E/(name+'.log')).write_text(output)
    commands.append(dict(name=name,argv=argv,exit_code=code))
    return output

capture('preflight-nodes',['ros2','node','list','--no-daemon','--spin-time','2'])
launch_cmd=['ros2','launch','mtc_bringup','mock_bringup.launch.py','backend:=mock']
log=(E/'launch.log').open('w')
launch=subprocess.Popen(launch_cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
result={'launch':launch_cmd,'task_id':'wiring-fix-20261011-basic-yellow',
        'runtime':'ROS DDS Mock; yellow is an acceptance example, not a competition command',
        'feedback':[]}
try:
    time.sleep(6)
    capture('nodes',['ros2','node','list','--no-daemon','--spin-time','2'])
    capture('topics',['ros2','topic','list','-t','--no-daemon','--spin-time','2'])
    capture('actions',['ros2','action','list','-t'])
    capture('services',['ros2','service','list','-t'])
    import rclpy
    from rclpy.action import ActionClient
    from mtc_interfaces.action import ExecuteTask, PickPlace
    from rosidl_runtime_py.convert import message_to_ordereddict
    result['generated_PickPlace_has_Server']=hasattr(PickPlace,'Server')
    rclpy.init()
    node=rclpy.create_node('acceptance_basic_goal_probe')
    for _ in range(30):
        rclpy.spin_once(node,timeout_sec=0.1)
    from rclpy.action import get_action_names_and_types, get_action_server_names_and_types_by_node
    result['runtime_graph']={
        'nodes':node.get_node_names_and_namespaces(),
        'actions':get_action_names_and_types(node),
        'services':node.get_service_names_and_types(),
        'topics':node.get_topic_names_and_types()}
    result['runtime_action_servers']=[{'node': name, 'namespace': ns, 'servers': get_action_server_names_and_types_by_node(node,name,ns)} for name,ns in node.get_node_names_and_namespaces()]
    pickplace=ActionClient(node,PickPlace,'/mtc/manipulation/pick_place')
    result['pickplace_server_available']=pickplace.wait_for_server(timeout_sec=1.0)
    pickplace.destroy()
    result['planned_goal']={'task_id':result['task_id'],'mode':1,'ordered_colors':[3],
                            'timeout_ms':5000,'placement_stability_sec':3.0}
    capture('processes',['ps','-eo','pid,ppid,args'])
    client=ActionClient(node,ExecuteTask,'/mtc/task/execute')
    result['task_server_available']=client.wait_for_server(timeout_sec=5)
    if result['task_server_available']:
        goal=ExecuteTask.Goal(task_id=result['task_id'],mode=1,ordered_colors=[3],
                              timeout_ms=5000,placement_stability_sec=3.0)
        result['goal']=message_to_ordereddict(goal)
        future=client.send_goal_async(goal,feedback_callback=lambda msg:
            result['feedback'].append(message_to_ordereddict(msg.feedback)))
        rclpy.spin_until_future_complete(node,future,timeout_sec=6)
        result['goal_response_received']=future.done()
        if future.done() and future.exception() is None:
            handle=future.result()
            result['accepted']=handle.accepted
            result['goal_uuid']=bytes(handle.goal_id.uuid).hex()
            if handle.accepted:
                final=handle.get_result_async()
                rclpy.spin_until_future_complete(node,final,timeout_sec=12)
                result['result_received']=final.done()
                if final.done() and final.exception() is None:
                    result['result']=message_to_ordereddict(final.result())
    client.destroy()
    node.destroy_node()
    rclpy.shutdown()
finally:
    if launch.poll() is None:
        launch.send_signal(signal.SIGINT)
        try: launch.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(launch.pid,signal.SIGTERM)
            launch.wait(timeout=5)
    log.close()
    result['launch_exit_code']=launch.returncode
    (E/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (E/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
