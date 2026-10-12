#!/usr/bin/env python3
"""Headless Plan -> Execute -> observed joints; isolated S3 GenericSystem only.

OpenAI Codex assisted, 2026-10-11. Uses the installed moveit_msgs interfaces;
does not implement planning, modify driver code, or bypass MoveIt execution.
"""
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


def finite_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: finite_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [finite_json(item) for item in value]
    return value


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True)
    os.environ.update(ROS_DOMAIN_ID='99', ROS_AUTOMATIC_DISCOVERY_RANGE='LOCALHOST',
                      ROS_LOG_DIR=str(out / 'ros-logs'))
    result = {'scope': 'Independent S3 MoveIt / GenericSystem; no FSM or physical robot',
              'planning_execution': 'NOT RUN', 'clean_shutdown': 'NOT RUN'}
    launches = []
    node = None
    initialized = False

    def capture(label, argv):
        p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, timeout=25)
        (out / (label + '.log')).write_text(p.stdout)
        if p.returncode:
            raise RuntimeError(f'{label}: exit {p.returncode}')
        return re.sub(r'\x1b\[[0-9;]*m', '', p.stdout)

    def launch(label, argv):
        log = (out / (label + '.log')).open('w')
        p = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        launches.append((label, p, log))

    def interrupted(signum, _frame):
        raise InterruptedError(f'signal {signum}')

    signal.signal(signal.SIGTERM, interrupted)
    try:
        from ament_index_python.packages import get_package_share_directory
        share = Path(get_package_share_directory('aubo_description'))
        xml = capture('xacro', ['xacro', str(share / 'urdf/xacro/inc/aubo_ros2.xacro'),
                                'aubo_type:=aubo_S3', 'use_fake_hardware:=true'])
        result['plugins'] = [p.text.strip() for p in ET.fromstring(xml).findall('ros2_control/hardware/plugin')]
        assert result['plugins'] == ['mock_components/GenericSystem'], result['plugins']
        assert not capture('empty-domain', ['ros2', 'node', 'list', '--no-daemon', '--spin-time', '2']).strip()
        launch('control', ['ros2', 'launch', 'aubo_ros2_driver', 'aubo_control.launch.py',
                           'aubo_type:=aubo_S3', 'use_fake_hardware:=true',
                           'initial_joint_controller:=joint_trajectory_controller', 'launch_rviz:=false'])
        import rclpy
        from rclpy.action import ActionClient, get_action_server_names_and_types_by_node
        from sensor_msgs.msg import JointState
        from moveit_msgs.srv import GetMotionPlan
        from moveit_msgs.msg import Constraints, JointConstraint
        from moveit_msgs.action import ExecuteTrajectory
        from rosidl_runtime_py.convert import message_to_ordereddict
        from tf2_ros import Buffer, TransformListener
        rclpy.init()
        initialized = True
        node = rclpy.create_node('moveit_acceptance_probe')
        samples = []
        node.create_subscription(JointState, '/joint_states', lambda m: samples.append((time.monotonic(), m)), 10)
        buffer = Buffer()
        listener = TransformListener(buffer, node)

        def spin_until(condition, timeout):
            deadline = time.monotonic() + timeout
            while not condition() and time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=0.1)
            assert condition(), 'Timed out waiting for state / response'

        spin_until(lambda: len(samples) >= 20, 45)
        hardware = capture('hardware', ['ros2', 'control', 'list_hardware_components', '-c', '/controller_manager', '-v'])
        assert hardware.count('mock_components/GenericSystem') == 1 and 'active' in hardware
        controllers = capture('controllers', ['ros2', 'control', 'list_controllers', '-c', '/controller_manager'])
        for name in ('joint_state_broadcaster', 'joint_trajectory_controller'):
            assert any(name in line and 'active' in line for line in controllers.splitlines())
        result['tf'] = {f'{parent}->{child}': message_to_ordereddict(buffer.lookup_transform(parent, child, rclpy.time.Time()))
                        for parent, child in [('world', 'base_link'), ('base_link', 'ee_link')]}
        launch('move-group', ['ros2', 'launch', 'aubo_moveit_config', 'aubo_moveit.launch.py',
                              'aubo_type:=aubo_S3', 'launch_rviz:=false'])
        planner = node.create_client(GetMotionPlan, '/plan_kinematic_path')
        assert planner.wait_for_service(timeout_sec=45), 'MoveIt planning service unavailable'
        executor = ActionClient(node, ExecuteTrajectory, '/execute_trajectory')
        assert executor.wait_for_server(timeout_sec=15), 'MoveIt execution Action unavailable'
        for _ in range(20):
            rclpy.spin_once(node, timeout_sec=0.1)
        servers = []
        for name, namespace in node.get_node_names_and_namespaces():
            for action, types in get_action_server_names_and_types_by_node(node, name, namespace):
                if action == '/joint_trajectory_controller/follow_joint_trajectory':
                    servers.append({'node': name, 'namespace': namespace, 'types': types})
        result['controller_action_servers'] = servers
        assert len(servers) == 1, servers
        names = ['shoulder_joint', 'upperArm_joint', 'foreArm_joint', 'wrist1_joint', 'wrist2_joint', 'wrist3_joint']

        def positions():
            assert time.monotonic() - samples[-1][0] < 1.0, 'Stale JointState'
            lookup = dict(zip(samples[-1][1].name, samples[-1][1].position))
            values = [lookup[name] for name in names]
            assert all(math.isfinite(x) for x in values)
            return values

        initial = positions()
        target = initial.copy()
        target[0] += 0.05
        result.update(initial_rad=initial, target_rad=target, joint_names=names)
        request = GetMotionPlan.Request()
        req = request.motion_plan_request
        req.group_name = 'manipulator'
        req.pipeline_id = 'ompl'
        req.num_planning_attempts = 5
        req.allowed_planning_time = 5.0
        req.max_velocity_scaling_factor = 0.1
        req.max_acceleration_scaling_factor = 0.1
        req.start_state.joint_state = samples[-1][1]
        req.start_state.joint_state.effort = []  # GenericSystem has no effort interface
        req.goal_constraints = [Constraints(joint_constraints=[
            JointConstraint(joint_name=name, position=value, tolerance_above=0.0001,
                            tolerance_below=0.0001, weight=1.0)
            for name, value in zip(names, target)])]
        future = planner.call_async(request)
        spin_until(future.done, 20)
        response = future.result().motion_plan_response
        result['plan'] = message_to_ordereddict(response)
        assert response.error_code.val == 1, response.error_code
        trajectory = response.trajectory.joint_trajectory
        assert set(trajectory.joint_names) == set(names) and len(trajectory.points) >= 2
        times = [p.time_from_start.sec + p.time_from_start.nanosec * 1e-9 for p in trajectory.points]
        assert all(b > a for a, b in zip(times, times[1:])), times
        assert max(abs(a - b) for a, b in zip(positions(), initial)) < 0.001, 'Start state changed; must re-plan'
        future = executor.send_goal_async(ExecuteTrajectory.Goal(trajectory=response.trajectory))
        spin_until(future.done, 8)
        handle = future.result()
        result['accepted'] = handle.accepted
        assert handle.accepted
        final = handle.get_result_async()
        spin_until(final.done, 45)
        result['execute'] = message_to_ordereddict(final.result())
        assert final.result().status == 4 and final.result().result.error_code.val == 1
        for _ in range(10):
            rclpy.spin_once(node, timeout_sec=0.1)
        actual = positions()
        result['actual_rad'] = actual
        result['max_error_rad'] = max(abs(a - b) for a, b in zip(actual, target))
        assert result['max_error_rad'] <= 0.001
        result['distinct_joint_stamps'] = len({(m.header.stamp.sec, m.header.stamp.nanosec) for _, m in samples})
        assert result['distinct_joint_stamps'] > 2
        result['planning_execution'] = 'PASS'
        executor.destroy()
    except Exception as exc:
        result['planning_execution'] = 'FAIL'
        result['exception'] = repr(exc)
    finally:
        if node is not None:
            node.destroy_node()
        if initialized:
            rclpy.try_shutdown()
        cleanup = []
        for label, p, log in reversed(launches):
            row = {'launch': label, 'escalated': False, 'already_exited': p.poll() is not None}
            if p.poll() is None:
                p.send_signal(signal.SIGINT)
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    row['escalated'] = True
                    os.killpg(p.pid, signal.SIGTERM)
                    try:
                        p.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(p.pid, signal.SIGKILL)
                        p.wait(timeout=3)
            log.close()
            row['exit_code'] = p.returncode
            row['child_failures'] = re.findall(r'process has died[^\n]*', (out / (label + '.log')).read_text())
            cleanup.append(row)
        result['shutdown'] = cleanup
        result['clean_shutdown'] = ('PASS' if len(cleanup) == 2 and all(
            not r['already_exited'] and not r['escalated'] and not r['child_failures'] and r['exit_code'] == 0
            for r in cleanup) else 'FAIL')
        result['json_note'] = 'Any non-finite optional ROS fields are null; original representation retained in result.raw.txt'
        (out / 'result.raw.txt').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        (out / 'result.json').write_text(json.dumps(finite_json(result), ensure_ascii=False, indent=2, allow_nan=False) + '\n')
        print(json.dumps(finite_json(result), ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if result['planning_execution'] == result['clean_shutdown'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
