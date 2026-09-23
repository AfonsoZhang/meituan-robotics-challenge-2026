#!/usr/bin/env python3
"""NUC 实机接入逐项检查，每项给出通过/不通过与依据，报告写入 outputs/claude_bringup_<阶段>_<时间>/。

  env     环境：Ubuntu 22.04、ROS 2 Humble、所需包、D435i USB 3、控制柜端口（给 --robot-ip 时）
  driver  驱动已启动（假硬件或实机）：控制器激活、/joint_states 6 个关节、频率，打印关节角供对照示教器
  camera  realsense-ros 已启动：图像话题、编码、分辨率、帧率；生成监控台预设

本脚本只读：不发运动指令，不改参数。但 driver 阶段检查的是**已经启动的驱动**，驱动一旦连上实机就进入
伺服保持当前位置，那一步的安全措施见 robot/README.md。
"""
import argparse, json, os, platform, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import (JOINTS, ROBOT_PORTS, classify_image_topics, dashboard_presets,
                    joint_state_problems, realsense_usb, tcp_open)

REPO = Path(__file__).resolve().parent.parent
PACKAGES = ['aubo_ros2_driver', 'aubo_description', 'aubo_moveit_config', 'realsense2_camera', 'moveit_ros_move_group']


class Report:
    def __init__(self, stage):
        self.stage, self.items = stage, []

    def add(self, name, ok, detail):
        self.items.append({'check': name, 'pass': bool(ok), 'detail': detail})
        print(f"[{'通过' if ok else '不通过'}] {name}：{detail}")

    def save(self, extra=None):
        out = REPO/'outputs'/f"claude_bringup_{self.stage}_{time.strftime('%Y%m%d-%H%M%S')}"
        out.mkdir(parents=True, exist_ok=True)
        data = {'stage': self.stage, 'host': platform.node(), 'time': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
                'ros_domain_id': os.environ.get('ROS_DOMAIN_ID', '0'), 'items': self.items, **(extra or {})}
        (out/'report.json').write_text(json.dumps(data, ensure_ascii=False, indent=2))
        failed = [i['check'] for i in self.items if not i['pass']]
        print(f"\n报告：{out/'report.json'}\n" + ('全部通过' if not failed else '未通过：' + '、'.join(failed)))
        return out, not failed


def stage_env(args):
    r = Report('env')
    os_release = dict(l.split('=', 1) for l in Path('/etc/os-release').read_text().split('\n') if '=' in l)
    ver = os_release.get('VERSION_ID', '').strip('"')
    r.add('Ubuntu 22.04', ver == '22.04', f"VERSION_ID={ver}")
    r.add('非 WSL', 'microsoft' not in platform.release().lower(), platform.release())
    distro = os.environ.get('ROS_DISTRO')
    r.add('ROS 2 Humble 已 source', distro == 'humble', f'ROS_DISTRO={distro}')
    for pkg in PACKAGES:
        p = subprocess.run(['ros2', 'pkg', 'prefix', pkg], capture_output=True, text=True) if distro else None
        r.add(f'包 {pkg}', p is not None and p.returncode == 0, (p.stdout or p.stderr).strip() if p else '未 source ROS')
    cams = realsense_usb()
    d435i = [c for c in cams if c['is_d435i']]
    r.add('D435i 已枚举', bool(d435i), json.dumps(cams, ensure_ascii=False) if cams else '未发现 RealSense USB 设备')
    if d435i:
        s = d435i[0]['speed_mbps']
        r.add('D435i 走 USB 3', s >= 5000, f'{s:g} Mbps（USB 2 为 480，深度+彩色高分辨率会掉帧）')
    if args.robot_ip:
        for name, port in ROBOT_PORTS.items():
            r.add(f'控制柜 {name} 端口 {port}', tcp_open(args.robot_ip, port), args.robot_ip)
    else:
        r.add('控制柜端口', False, '未给 --robot-ip，未检查')
    return r.save()


def ros_node():
    import rclpy
    rclpy.init()
    return rclpy, rclpy.create_node('meituan_bringup_check')


def spin_for(rclpy, node, seconds, until=lambda: False):
    end = time.monotonic() + seconds
    while time.monotonic() < end and not until():
        rclpy.spin_once(node, timeout_sec=0.05)


def stage_driver(args):
    from controller_manager_msgs.srv import ListControllers
    from sensor_msgs.msg import JointState
    rclpy, node = ros_node()
    r = Report('driver')
    cli = node.create_client(ListControllers, '/controller_manager/list_controllers')
    states = {}
    if cli.wait_for_service(timeout_sec=5.0):
        fut = cli.call_async(ListControllers.Request())
        spin_for(rclpy, node, 5.0, fut.done)
        states = {c.name: c.state for c in fut.result().controller} if fut.done() and fut.result() else {}
    r.add('controller_manager 可用', bool(states), json.dumps(states, ensure_ascii=False) if states else '5 s 内无响应')
    for c in ('joint_state_broadcaster', 'joint_trajectory_controller'):
        r.add(f'{c} 激活', states.get(c) == 'active', states.get(c, '不存在'))
    msgs = []
    node.create_subscription(JointState, '/joint_states', msgs.append, 10)
    t0 = time.monotonic(); spin_for(rclpy, node, 3.0); dt = time.monotonic() - t0
    r.add('/joint_states 有数据', bool(msgs), f'{len(msgs)} 条 / {dt:.1f} s ≈ {len(msgs)/dt:.0f} Hz')
    extra = {}
    if msgs:
        m = msgs[-1]
        problems = joint_state_problems(list(m.name), list(m.position))
        r.add('关节名与数值', not problems, '；'.join(problems) or '6 个关节齐全')
        pos = dict(zip(m.name, m.position))
        deg = {j: round(pos[j]*57.29577951308232, 2) for j in JOINTS if j in pos}
        extra['joint_positions_deg'] = deg
        print('\n当前关节角（°），请与示教器逐个对照：')
        for j, v in deg.items(): print(f'  {j:16s} {v:9.2f}')
        r.add('与示教器一致（需人工确认）', False, '脚本无法读示教器；对照后在报告里记下结论')
    node.destroy_node(); rclpy.shutdown()
    return r.save(extra)


def stage_camera(args):
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image
    rclpy, node = ros_node()
    r = Report('camera')
    spin_for(rclpy, node, 2.0)   # 等话题发现
    topics = sorted(n for n, t in node.get_topic_names_and_types() if 'sensor_msgs/msg/Image' in t)
    r.add('发现图像话题', bool(topics), ', '.join(topics) or '无')
    stats = {t: {'count': 0} for t in topics}
    def cb(msg, t):
        s = stats[t]; s['count'] += 1
        s.update(encoding=msg.encoding, width=msg.width, height=msg.height, frame_id=msg.header.frame_id)
    for t in topics:
        node.create_subscription(Image, t, lambda m, t=t: cb(m, t), qos_profile_sensor_data)
    spin_for(rclpy, node, 1.0)
    for s in stats.values(): s['count'] = 0
    t0 = time.monotonic(); spin_for(rclpy, node, args.seconds); dt = time.monotonic() - t0
    for t, s in stats.items():
        s['hz'] = round(s.pop('count')/dt, 1)
        print(f"  {t}: {s.get('encoding')} {s.get('width')}x{s.get('height')} {s['hz']} Hz frame={s.get('frame_id')}")
    color, depth, aligned = classify_image_topics(stats)
    r.add('彩色话题有数据', any(stats[t]['hz'] > 0 for t in color), ', '.join(color) or '无 rgb8/bgr8 话题')
    r.add('深度话题有数据', any(stats[t]['hz'] > 0 for t in depth), ', '.join(depth) or '无 16UC1/32FC1 话题')
    r.add('深度已对齐到彩色', bool(aligned), ', '.join(aligned) or '未见 aligned_depth_to_color；启动 realsense 时加 align_depth.enable:=true')
    node.destroy_node(); rclpy.shutdown()
    presets = dashboard_presets(color[0] if color else None, (aligned or depth or [None])[0])
    out, ok = r.save({'image_topics': stats})
    (out/'dashboard-presets.json').write_text(json.dumps(presets, ensure_ascii=False, indent=2))
    print(f"监控台预设：bash demo/dashboard.sh --readonly --presets {out/'dashboard-presets.json'}")
    return out, ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('stage', choices=['env', 'driver', 'camera'])
    ap.add_argument('--robot-ip', help='控制柜 IP（env 阶段检查 RPC/RTDE 端口）')
    ap.add_argument('--seconds', type=float, default=3.0, help='camera 阶段测帧率的时长')
    a = ap.parse_args()
    _, ok = {'env': stage_env, 'driver': stage_driver, 'camera': stage_camera}[a.stage](a)
    sys.exit(0 if ok else 2)


if __name__ == '__main__':
    main()
