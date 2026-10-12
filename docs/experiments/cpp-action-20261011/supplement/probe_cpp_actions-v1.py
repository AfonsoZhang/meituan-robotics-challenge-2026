#!/usr/bin/env python3
"""Acceptance of delivered standalone C++ Mock Action executables.

OpenAI Codex assisted, 2026-10-11. Run only in the documented networkless
Jazzy acceptance container. No driver, MoveIt, hardware or FSM modifications.
"""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


class Session:
    def __init__(self, root, label, domain, executables, install):
        import rclpy
        from rclpy.context import Context
        from rclpy.executors import SingleThreadedExecutor
        self.rclpy = rclpy
        self.out = root / label
        self.out.mkdir()
        self.result = {'case': label, 'scope': 'Standalone C++ Mock processes and ROS Action only',
                       'domain': domain, 'checks': [], 'goals': [], 'status': 'FAIL'}
        self.children = []
        self.clients = []
        self.context = Context()
        self.node = None
        self.executor = None
        env = dict(os.environ, ROS_DOMAIN_ID=str(domain), ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',
                   RMW_IMPLEMENTATION='rmw_fastrtps_cpp', ROS_LOG_DIR=str(self.out / 'ros-logs'))
        for key in ('ROS_STATIC_PEERS', 'ROS_LOCALHOST_ONLY', 'FASTRTPS_DEFAULT_PROFILES_FILE',
                    'FASTDDS_DEFAULT_PROFILES_FILE', 'CYCLONEDDS_URI'):
            env.pop(key, None)
        try:
            rclpy.init(context=self.context, domain_id=domain)
            self.node = rclpy.create_node('cpp_action_acceptance', context=self.context)
            self.executor = SingleThreadedExecutor(context=self.context)
            self.executor.add_node(self.node)
            for exe in executables:
                binary = install / 'mtc_ros2_action_cpp' / 'lib' / 'mtc_ros2_action_cpp' / exe
                assert binary.is_file(), str(binary)
                log = (self.out / (exe + '.log')).open('w')
                child = subprocess.Popen([str(binary)], env=env, stdout=log,
                                         stderr=subprocess.STDOUT, start_new_session=True)
                self.children.append((exe, child, log))
        except Exception:
            self.close()
            raise

    def spin(self, seconds):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            self.executor.spin_once(timeout_sec=max(0.0, min(0.02, until - time.monotonic())))

    def wait(self, future, timeout=10):
        self.executor.spin_until_future_complete(future, timeout_sec=timeout)
        assert future.done(), 'Future timeout'
        return future.result()

    def check(self, name, condition):
        self.result['checks'].append({'name': name, 'passed': bool(condition)})
        assert condition, name

    def client(self, action, name, expected_node):
        from rclpy.action import ActionClient, get_action_server_names_and_types_by_node
        client = ActionClient(self.node, action, name)
        self.clients.append(client)
        self.check(name + ' server available', client.wait_for_server(timeout_sec=8))
        self.spin(0.2)
        servers = []
        for node, ns in self.node.get_node_names_and_namespaces():
            for topic, types in get_action_server_names_and_types_by_node(self.node, node, ns):
                if topic == name:
                    servers.append({'node': node, 'namespace': ns, 'types': types})
        self.result.setdefault('servers', {})[name] = servers
        self.check(name + ' unique delivered server', len(servers) == 1 and servers[0]['node'] == expected_node)
        return client

    def send(self, client, goal):
        from rosidl_runtime_py.convert import message_to_ordereddict as convert
        record = {'goal': convert(goal), 'feedback': []}
        self.result['goals'].append(record)
        handle = self.wait(client.send_goal_async(goal, feedback_callback=lambda m:
                           record['feedback'].append(convert(m.feedback))))
        record['accepted'] = handle.accepted
        record['goal_uuid'] = list(handle.goal_id.uuid)
        return handle, record

    def terminal(self, handle, record, timeout=30):
        from rosidl_runtime_py.convert import message_to_ordereddict as convert
        result = self.wait(handle.get_result_async(), timeout)
        record['terminal'] = convert(result)
        return result

    def cancel(self, handle, record):
        from rosidl_runtime_py.convert import message_to_ordereddict as convert
        response = self.wait(handle.cancel_goal_async())
        record['cancel_response'] = convert(response)
        self.check('associated Cancel accepted', response.return_code == 0 and
                   any(list(g.goal_id.uuid) == list(handle.goal_id.uuid) for g in response.goals_canceling))

    def close(self):
        shutdown = []
        for exe, child, log in reversed(self.children):
            escalated = False
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGINT)
            try:
                child.wait(timeout=6)
            except subprocess.TimeoutExpired:
                escalated = True
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=3)
            log.close()
            shutdown.append({'executable': exe, 'exit_code': child.returncode, 'escalated': escalated})
        self.result['shutdown'] = shutdown
        if any(x['exit_code'] != 0 or x['escalated'] for x in shutdown):
            self.result['status'] = 'FAIL'
        if self.node:
            until = time.monotonic() + 3
            while any(n.startswith('mtc_mock_') for n, _ in self.node.get_node_names_and_namespaces()) and time.monotonic() < until:
                self.spin(0.1)
            self.result['nodes_after_shutdown'] = self.node.get_node_names_and_namespaces()
            if any(n.startswith('mtc_mock_') for n, _ in self.result['nodes_after_shutdown']):
                self.result['status'] = 'FAIL'
            for client in self.clients:
                client.destroy()
            self.executor.remove_node(self.node)
            self.executor.shutdown(timeout_sec=2)
            self.node.destroy_node()
        if self.context.ok():
            self.context.shutdown()
        save(self.out / 'result.json', self.result)


def task_goal(identity, colors=None, timeout_ms=20000, stability=3.0):
    from mtc_interfaces.action import ExecuteTask
    colors = colors or [1]
    return ExecuteTask.Goal(task_id=identity, mode=1 if len(colors) == 1 else 2,
                            ordered_colors=colors, timeout_ms=timeout_ms,
                            placement_stability_sec=stability)


def task_workflow(s):
    from mtc_interfaces.action import ExecuteTask, PickPlace
    client = s.client(ExecuteTask, '/mtc/task/execute', 'mtc_mock_task')
    s.client(PickPlace, '/mtc/manipulation/pick_place', 'mtc_mock_pick_place')
    s.spin(7)  # Explicitly check an idle startup longer than the historical INIT timeout.
    for g in (task_goal('bad-color', [0]), task_goal('bad-sequence', [1, 1, 3]),
              task_goal('bad-stability', stability=0.0)):
        h, record = s.send(client, g)
        s.check('invalid task rejected: ' + g.task_id, not h.accepted)
    goal = task_goal('standalone-basic')
    h, record = s.send(client, goal)
    s.check('basic accepted after idle', h.accepted)
    other, _ = s.send(client, task_goal('concurrent-task'))
    s.check('concurrent task rejected', not other.accepted)
    result = s.terminal(h, record)
    s.check('basic real child result and T0', result.status == 4 and result.result.success and
            result.result.error_code == 0 and result.result.completed_count == 1 and
            list(result.result.completed_slots) == ['T0'])
    s.check('task and child feedback populated', any(f['substate'] and f['current_object_id']
            and f['current_slot'] == 'T0' for f in record['feedback']))
    repeated, _ = s.send(client, goal)
    s.check('completed business ID rejected', not repeated.accepted)
    sequence, record = s.send(client, task_goal('standalone-sequence', [3, 1, 2], timeout_ms=45000))
    s.check('sequence accepted after normal finish', sequence.accepted)
    result = s.terminal(sequence, record, 50)
    s.check('ordered sequence completed', result.status == 4 and result.result.success and
            result.result.completed_count == 3 and list(result.result.completed_slots) == ['P1', 'P2', 'P3'])
    seen = {(f['current_slot'], f['current_object_id']) for f in record['feedback']}
    s.check('ordered colors preserved in actual feedback', all(x in seen for x in
            [('P1', 'mock_battery_color_3'), ('P2', 'mock_battery_color_1'), ('P3', 'mock_battery_color_2')]))


def task_cancel(s):
    from mtc_interfaces.action import ExecuteTask, PickPlace
    client = s.client(ExecuteTask, '/mtc/task/execute', 'mtc_mock_task')
    s.client(PickPlace, '/mtc/manipulation/pick_place', 'mtc_mock_pick_place')
    h, record = s.send(client, task_goal('standalone-cancel'))
    s.check('cancel scenario accepted', h.accepted)
    until = time.monotonic() + 6
    while time.monotonic() < until and sum(f['substate'] == 'MOVE_PRE_ALIGN' for f in record['feedback']) < 3:
        s.spin(0.01)
    s.check('child motion state observed repeatedly', sum(f['substate'] == 'MOVE_PRE_ALIGN' for f in record['feedback']) >= 3)
    s.cancel(h, record)
    result = s.terminal(h, record)
    s.check('trusted child final cancel propagated', result.status == 5 and not result.result.success
            and result.result.error_code == 0 and result.result.completed_count == 0)
    s.result['stop_scope'] = 'Only this delivered trusted Mock contract; public PickPlace result has no independent stop_confirmed field.'


def missing_child(s):
    from mtc_interfaces.action import ExecuteTask
    client = s.client(ExecuteTask, '/mtc/task/execute', 'mtc_mock_task')
    h, record = s.send(client, task_goal('missing-child', timeout_ms=150))
    s.check('missing-child request accepted', h.accepted)
    result = s.terminal(h, record)
    s.check('missing child cannot fabricate success', result.status == 6 and not result.result.success
            and result.result.error_code == 220 and result.result.completed_count == 0)
    other, _ = s.send(client, task_goal('after-fault'))
    s.check('fault admission lock retained', not other.accepted)


def motion_goal(identity):
    from mtc_interfaces.action import ExecuteJointMove
    return ExecuteJointMove.Goal(command_id=identity,
        joint_names=['shoulder_joint', 'upperArm_joint', 'foreArm_joint', 'wrist1_joint', 'wrist2_joint', 'wrist3_joint'],
        target_rad=[0.05, -0.02, 0.01, 0.03, -0.04, 0.02], velocity_scaling=0.2,
        acceleration_scaling=0.2, timeout_ms=2000)


def motion_workflow(s):
    from mtc_interfaces.action import ExecuteJointMove
    client = s.client(ExecuteJointMove, '/mtc/motion/execute_joint_move', 'mtc_mock_joint_move')
    bad = motion_goal('invalid-motion')
    bad.acceleration_scaling = 1.0
    rejected, _ = s.send(client, bad)
    s.check('motion scaling over limit rejected', not rejected.accepted)
    goal = motion_goal('standalone-motion')
    h, record = s.send(client, goal)
    s.check('0.2 float32 boundary accepted', h.accepted)
    other, _ = s.send(client, motion_goal('concurrent-motion'))
    s.check('motion concurrent goal rejected', not other.accepted)
    result = s.terminal(h, record)
    s.check('nonzero single point result exact', result.status == 4 and result.result.success and
            result.result.stop_confirmed and list(result.result.final_position_rad) == list(goal.target_rad))
    s.check('finite backend feedback present', bool(record['feedback']) and all(
        math.isfinite(x) for f in record['feedback'] for x in f['actual_position_rad']))
    repeated, _ = s.send(client, goal)
    s.check('motion completed ID rejected', not repeated.accepted)
    h, record = s.send(client, motion_goal('standalone-motion-cancel'))
    s.check('new motion accepted', h.accepted)
    until = time.monotonic() + 2
    while not record['feedback'] and time.monotonic() < until:
        s.spin(0.01)
    s.check('motion dispatched before cancellation', bool(record['feedback']))
    s.cancel(h, record)
    result = s.terminal(h, record)
    s.check('motion cancel has terminal stop confirmation', result.status == 5 and not result.result.success
            and result.result.stop_confirmed and result.result.error_code == 0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--install', type=Path, default=Path('/candidate-install'))
    args = parser.parse_args()
    assert os.environ.get('ROS_DISTRO') == 'jazzy', 'Use isolated Jazzy environment'
    assert os.environ.get('ROS_AUTOMATIC_DISCOVERY_RANGE') == 'LOCALHOST'
    args.output.mkdir(parents=True)
    cases = []
    both = ['mock_pick_place_server', 'mock_task_server']
    for offset, (label, executables, check) in enumerate([
        ('task-basic-sequence-after-idle', both, task_workflow),
        ('task-associated-cancel', both, task_cancel),
        ('task-missing-child-fault', ['mock_task_server'], missing_child),
        ('motion-single-point-cancel', ['mock_motion_server'], motion_workflow),
    ]):
        session = Session(args.output, label, 110 + offset, executables, args.install)
        try:
            check(session)
            session.result['status'] = 'PASS'
        except Exception as exc:
            session.result['exception'] = repr(exc)
        finally:
            session.close()
        cases.append(session.result)
        print(label, session.result['status'], flush=True)
    save(args.output / 'summary.json', cases)
    return 0 if all(x['status'] == 'PASS' for x in cases) else 1


if __name__ == '__main__':
    raise SystemExit(main())
