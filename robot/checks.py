"""实机接入检查的纯逻辑（不依赖 ROS，可离线单测）；ROS 部分在 bringup_check.py / jog.py。"""
import math
import socket
from pathlib import Path

# 与 aubo_ros2_driver 的 aubo_controllers.yaml、仿真模型一致
JOINTS = ['shoulder_joint', 'upperArm_joint', 'foreArm_joint', 'wrist1_joint', 'wrist2_joint', 'wrist3_joint']
REALSENSE_VENDOR = '8086'
D435I_PRODUCT = '0b3a'
# 驱动连接控制柜的端口（aubo_hardware_interface.cpp：RPC 30004、RTDE 30010）
ROBOT_PORTS = {'rpc': 30004, 'rtde': 30010}
JOG_MAX_DEG = 5.0      # 单次点动上限
JOG_MIN_S = 5.0        # 单次点动最短时长，约束最大角速度 ≤1°/s
COLOR_ENCODINGS = ('rgb8', 'bgr8')
DEPTH_ENCODINGS = ('16UC1', '32FC1')


def realsense_usb(root='/sys/bus/usb/devices'):
    """列出 RealSense USB 设备及协商速率（Mbps）；D435i 需 USB 3（≥5000）才能跑满深度+彩色。"""
    found = []
    for dev in Path(root).glob('*'):
        try:
            vendor = (dev/'idVendor').read_text().strip()
            product = (dev/'idProduct').read_text().strip()
        except OSError:
            continue
        if vendor != REALSENSE_VENDOR: continue
        speed = (dev/'speed').read_text().strip() if (dev/'speed').exists() else '0'
        name = (dev/'product').read_text().strip() if (dev/'product').exists() else ''
        found.append({'path': dev.name, 'product_id': product, 'name': name,
                      'is_d435i': product == D435I_PRODUCT, 'speed_mbps': float(speed)})
    return found


def tcp_open(host, port, timeout=2.0):
    try:
        with socket.create_connection((host, port), timeout=timeout): return True
    except OSError:
        return False


def joint_state_problems(names, positions, expected=JOINTS):
    """关节名必须恰好是那 6 个、数值有限；返回问题列表，空表示通过。"""
    problems = []
    missing = [j for j in expected if j not in names]
    if missing: problems.append('缺少关节：' + ', '.join(missing))
    extra = [n for n in names if n not in expected]
    if extra: problems.append('多出关节：' + ', '.join(extra))
    if len(names) != len(positions): problems.append('names 与 positions 长度不一致')
    if any(not math.isfinite(p) for p in positions): problems.append('存在非有限值')
    return problems


def jog_target(current, joint, delta_deg, duration_s):
    """单关节点动的目标位形；超出幅度或时长下限直接拒绝。current 为 {关节名: rad}。"""
    if joint not in JOINTS: raise ValueError(f'未知关节 {joint}')
    if set(current) != set(JOINTS): raise ValueError('当前关节状态不完整')
    if not 0 < abs(delta_deg) <= JOG_MAX_DEG: raise ValueError(f'幅度须在 (0, {JOG_MAX_DEG}]° 内')
    if duration_s < JOG_MIN_S: raise ValueError(f'时长须 ≥{JOG_MIN_S} s')
    target = dict(current)
    target[joint] += math.radians(delta_deg)
    return [target[j] for j in JOINTS]


def classify_image_topics(stats):
    """stats: {topic: {'encoding': str, ...}} → (彩色话题, 深度话题, 对齐深度话题)。"""
    # 深度相机的伪彩图也是 rgb8（仿真 /d435i/depth/image_raw），按名字排除
    color = sorted(t for t, s in stats.items() if s.get('encoding') in COLOR_ENCODINGS and 'depth' not in t)
    depth = sorted(t for t, s in stats.items() if s.get('encoding') in DEPTH_ENCODINGS)
    aligned = [t for t in depth if 'aligned_depth_to_color' in t]
    return color, depth, aligned


def dashboard_presets(color_topic=None, depth_topic=None):
    """按实测话题生成监控台只读预设（dashboard.py --presets 使用）。"""
    presets = [
        {'name': '节点列表', 'cmd': 'watch -n 2 ros2 node list', 'kind': 'monitor'},
        {'name': '话题列表', 'cmd': 'watch -n 2 ros2 topic list', 'kind': 'monitor'},
        {'name': '控制器状态', 'cmd': 'watch -n 2 ros2 control list_controllers', 'kind': 'monitor'},
        {'name': '关节角', 'cmd': 'ros2 topic echo /joint_states --field position', 'kind': 'monitor'},
        {'name': '空 shell', 'cmd': '', 'kind': 'shell'},
    ]
    for label, topic in (('彩色帧率', color_topic), ('深度帧率', depth_topic)):
        if topic: presets.append({'name': label, 'cmd': f'ros2 topic hz {topic}', 'kind': 'monitor'})
    return presets
