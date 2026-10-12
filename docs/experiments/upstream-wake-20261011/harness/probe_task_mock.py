#!/usr/bin/env python3
"""Actual ROS Mock Goal/Result and Cancel probes, with no synthetic success.

OpenAI Codex assisted, 2026-10-11. The delivered Python Mock launch remains
distinct from any newly delivered C++ wrapper or MoveIt/FSM launch.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def case(root, label, delay, cancel):
    import rclpy
    from rclpy.action import ActionClient, get_action_server_names_and_types_by_node
    from mtc_interfaces.action import ExecuteTask, PickPlace
    from rosidl_runtime_py.convert import message_to_ordereddict
    out = root / label
    out.mkdir()
    os.environ.update(ROS_DOMAIN_ID='98', ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',
                      ROS_LOG_DIR=str(out / 'ros-logs'))
    result = {'case': label, 'delay_before_goal_sec': delay, 'cancel_requested': cancel,
              'feedback': [], 'status': 'FAIL', 'scope': 'Delivered Python Mock launch, dry_run default'}
    log = (out / 'launch.log').open('w')
    launch = subprocess.Popen(['ros2', 'launch', 'mtc_bringup', 'mock_bringup.launch.py', 'backend:=mock'],
                              stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    node = None
    clients = []
    try:
        rclpy.init()
        node = rclpy.create_node('task_acceptance_probe')
        client = ActionClient(node, ExecuteTask, '/mtc/task/execute')
        clients.append(client)
        pick = ActionClient(node, PickPlace, '/mtc/manipulation/pick_place')
        clients.append(pick)
        result['task_server_available'] = client.wait_for_server(timeout_sec=15)
        assert result['task_server_available'], 'Task server unavailable'
        until = time.monotonic() + delay
        while time.monotonic() < until:
            rclpy.spin_once(node, timeout_sec=0.1)
        goal = ExecuteTask.Goal(task_id='acceptance-' + label, mode=1, ordered_colors=[3],
                                timeout_ms=5000, placement_stability_sec=3.0)
        result['goal'] = message_to_ordereddict(goal)
        future = client.send_goal_async(goal, feedback_callback=lambda m:
                                        result['feedback'].append(message_to_ordereddict(m.feedback)))
        rclpy.spin_until_future_complete(node, future, timeout_sec=6)
        assert future.done(), 'Goal response timeout'
        handle = future.result()
        result['accepted'] = handle.accepted
        assert handle.accepted, 'Goal rejected'
        final = handle.get_result_async()
        if cancel:
            response = handle.cancel_goal_async()
            rclpy.spin_until_future_complete(node, response, timeout_sec=5)
            if response.done():
                result['cancel_response'] = message_to_ordereddict(response.result())
        rclpy.spin_until_future_complete(node, final, timeout_sec=15)
        result['result_received'] = final.done()
        if final.done():
            result['result'] = message_to_ordereddict(final.result())
        result['pickplace_server_available'] = pick.wait_for_server(timeout_sec=1)
        result['nodes'] = node.get_node_names_and_namespaces()
        result['action_servers'] = [{'node': n, 'namespace': ns, 'servers':
            get_action_server_names_and_types_by_node(node, n, ns)} for n, ns in result['nodes']]
        assert result['pickplace_server_available'], 'PickPlace server unavailable (B03/B05)'
        assert final.done(), 'No terminal Action result'
        expected = 5 if cancel else 4
        assert final.result().status == expected, f'Unexpected terminal status: {final.result().status}'
        if cancel:
            assert result.get('cancel_response', {}).get('goals_canceling'), 'Cancellation not accepted'
        else:
            assert final.result().result.error_code == 0, 'Nonzero task error'
        result['status'] = 'PASS'
        result['scope_note'] = 'Action terminal state only; independent physical stop evidence NOT VERIFIED'
    except Exception as exc:
        result['exception'] = repr(exc)
    finally:
        for client in clients:
            client.destroy()
        if node:
            node.destroy_node()
        rclpy.try_shutdown()
        result['shutdown_escalated'] = False
        if launch.poll() is None:
            launch.send_signal(signal.SIGINT)
            try:
                launch.wait(timeout=10)
            except subprocess.TimeoutExpired:
                result['shutdown_escalated'] = True
                os.killpg(launch.pid, signal.SIGTERM)
                try:
                    launch.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(launch.pid, signal.SIGKILL)
                    launch.wait(timeout=3)
        log.close()
        result['launch_exit_code'] = launch.returncode
        result['child_failure'] = 'process has died' in (out / 'launch.log').read_text()
        (out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    root = Path(sys.argv[1])
    root.mkdir(parents=True)

    def terminate(_signum, _frame):
        raise SystemExit(124)

    signal.signal(signal.SIGTERM, terminate)
    results = [case(root, *args) for args in [('early-goal', 0.0, False),
                                             ('delayed-goal', 7.0, False),
                                             ('cancel-goal', 0.0, True)]]
    (root / 'summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(r['status'] == 'PASS' and not r['shutdown_escalated']
                    and not r['child_failure'] and r['launch_exit_code'] == 0 for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
