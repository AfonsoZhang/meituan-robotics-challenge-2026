#!/usr/bin/env python3
"""单关节小幅点动：验证实机方向、单位与急停。幅度 ≤5°、时长 ≥5 s（≤1°/s），执行前人工确认。

只经 /joint_trajectory_controller/follow_joint_trajectory 发一个目标点，由 JTC 从当前位置插值；
其余关节保持当前值。执行前请确认急停在手边、工作空间无人无物，第一次先用末端关节（wrist3_joint）。
"""
import argparse, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import JOG_MAX_DEG, JOG_MIN_S, JOINTS, jog_target


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--joint', required=True, choices=JOINTS)
    ap.add_argument('--delta-deg', type=float, required=True, help=f'带符号，绝对值 ≤{JOG_MAX_DEG}')
    ap.add_argument('--duration', type=float, default=6.0, help=f'秒，≥{JOG_MIN_S}')
    a = ap.parse_args()

    import rclpy
    from rclpy.action import ActionClient
    from builtin_interfaces.msg import Duration
    from control_msgs.action import FollowJointTrajectory
    from sensor_msgs.msg import JointState
    from trajectory_msgs.msg import JointTrajectoryPoint

    rclpy.init()
    node = rclpy.create_node('meituan_jog')
    latest = {}
    node.create_subscription(JointState, '/joint_states', lambda m: latest.update(msg=m, t=time.monotonic()), 10)
    end = time.monotonic() + 5
    while time.monotonic() < end and 'msg' not in latest: rclpy.spin_once(node, timeout_sec=0.05)
    if 'msg' not in latest: sys.exit('5 s 内没有 /joint_states，驱动未启动？')
    current = dict(zip(latest['msg'].name, latest['msg'].position))
    current = {j: current[j] for j in JOINTS if j in current}
    try:
        target = jog_target(current, a.joint, a.delta_deg, a.duration)
    except ValueError as e:
        sys.exit(f'拒绝执行：{e}')
    i = JOINTS.index(a.joint)
    print(f'{a.joint}: {current[a.joint]*57.2958:.2f}° → {target[i]*57.2958:.2f}°（{a.delta_deg:+g}°，{a.duration:g} s）')
    if input('急停在手边、工作空间已清空？输入 yes 执行：').strip() != 'yes': sys.exit('已取消')

    client = ActionClient(node, FollowJointTrajectory, '/joint_trajectory_controller/follow_joint_trajectory')
    if not client.wait_for_server(timeout_sec=5): sys.exit('轨迹控制器 action 不可用')
    goal = FollowJointTrajectory.Goal()
    goal.trajectory.joint_names = JOINTS
    sec = int(a.duration)
    goal.trajectory.points = [JointTrajectoryPoint(positions=target, velocities=[0.0]*6,
                                                   time_from_start=Duration(sec=sec, nanosec=int((a.duration-sec)*1e9)))]
    fut = client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, fut, timeout_sec=5)
    handle = fut.result()
    if handle is None or not handle.accepted: sys.exit('目标被拒绝')
    res = handle.get_result_async()
    rclpy.spin_until_future_complete(node, res, timeout_sec=a.duration + 10)
    end = time.monotonic() + 1
    while time.monotonic() < end: rclpy.spin_once(node, timeout_sec=0.05)
    final = dict(zip(latest['msg'].name, latest['msg'].position))
    err = [abs(final[j]-t)*57.2958 for j, t in zip(JOINTS, target)]
    code = res.result().result.error_code if res.done() else '超时'
    print(f'结果码 {code}；各关节终点误差（°）：' + ' '.join(f'{e:.2f}' for e in err))
    print('请目视确认：实际转动的是所选关节，方向与符号一致。反向回位：--delta-deg %+g' % -a.delta_deg)
    node.destroy_node(); rclpy.shutdown()


if __name__ == '__main__':
    main()
