#!/usr/bin/env python3
"""本地仿真监控台：多个 ROS 终端 + 相机实时画面 + 已录视频，一个浏览器页面。

只监听 127.0.0.1（终端就是本机 shell，不要暴露到网络）；远程查看走 SSH 隧道。
--readonly 时不开交互 shell，只能运行白名单里的监控命令，且不接受键盘输入。
ROS 部分可选：没有 rclpy 时终端和录像仍可用，实时画面与节点状态显示为不可用。
用 demo/dashboard.sh 启动，它和 run.sh 一样先 source ROS 与工作空间。
"""
import argparse, asyncio, fcntl, json, os, pty, signal, struct, subprocess, termios, threading, time
from pathlib import Path

import cv2
import numpy as np
from aiohttp import web, WSMsgType

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
OUTPUTS = REPO/'outputs'
# 默认与 record.py 写死的仿真实例一致；看实机时用 --ros-domain-id 改成实机所用值
SIM_ENV = {'ROS_DOMAIN_ID': '67', 'GAZEBO_MASTER_URI': 'http://127.0.0.1:11365'}
# kind：shell 键入并回车；type 只键入不回车，留给人确认；monitor 只读监控，--readonly 下唯一允许的一类
PRESETS = [
    {'name': '空 shell', 'cmd': '', 'kind': 'shell'},
    {'name': '运行 demo（待确认）', 'cmd': 'bash demo/run.sh --smoke', 'kind': 'type'},
    {'name': '节点列表', 'cmd': 'watch -n 2 ros2 node list', 'kind': 'monitor'},
    {'name': '话题列表', 'cmd': 'watch -n 2 ros2 topic list', 'kind': 'monitor'},
    {'name': '控制器状态', 'cmd': 'watch -n 2 ros2 control list_controllers', 'kind': 'monitor'},
    {'name': '关节跟踪误差', 'cmd': 'ros2 topic echo /joint_trajectory_controller/controller_state --field error.positions', 'kind': 'monitor'},
    {'name': '腕部相机帧率', 'cmd': 'ros2 topic hz /d435i/color/image_raw', 'kind': 'monitor'},
    {'name': '俯视相机帧率', 'cmd': 'ros2 topic hz /demo/overview/image_raw', 'kind': 'monitor'},
]
WATCHED = ('gzserver', 'gzclient', 'record.py', 'robot_state_publisher', 'ros2')
STREAM_FPS = 15


def to_bgr(encoding, height, width, step, data):
    """sensor_msgs/Image 原始字段 → 可显示的 BGR uint8；深度按本帧 2–98 分位拉伸着色（近亮远暗），无效值为黑。"""
    buf = np.frombuffer(data, dtype=np.uint8)
    if encoding in ('rgb8', 'bgr8'):
        a = buf.reshape(height, step)[:, :width*3].reshape(height, width, 3)
        return (a[:, :, ::-1] if encoding == 'rgb8' else a).copy()
    if encoding == 'mono8':
        return cv2.cvtColor(buf.reshape(height, step)[:, :width], cv2.COLOR_GRAY2BGR)
    if encoding == '32FC1':
        d = buf.view(np.float32).reshape(height, step//4)[:, :width]
    elif encoding == '16UC1':
        d = buf.view(np.uint16).reshape(height, step//2)[:, :width].astype(np.float32)/1000.  # mm → m
    else:
        raise ValueError('unsupported encoding: '+encoding)
    valid = np.isfinite(d) & (d > 0)
    scaled = np.zeros(d.shape, np.uint8)
    if valid.any():
        lo, hi = np.percentile(d[valid], (2, 98))
        scaled[valid] = np.clip((hi - d[valid])/max(hi - lo, 1e-3)*255, 0, 255).astype(np.uint8)
    out = cv2.applyColorMap(scaled, cv2.COLORMAP_TURBO)
    out[~valid] = 0
    return out


def terminal_spec(preset, readonly):
    """预设编号 → (argv, 开头键入的字节, 是否接受键盘输入)；只读模式拒绝非 monitor 预设。"""
    p = PRESETS[int(preset)]
    if readonly:
        if p['kind'] != 'monitor': raise PermissionError('只读模式只允许监控预设')
        return ['bash', '-c', p['cmd']], b'', False
    typed = p['cmd'].encode() + (b'\n' if p['cmd'] and p['kind'] != 'type' else b'')
    return ['bash', '-i'], typed, True


def same_origin(request):
    """浏览器跨站也能连 ws://127.0.0.1，必须校验 Origin，否则任意网页都能借终端执行命令。"""
    origin = request.headers.get('Origin')
    if origin is None: return True   # 非浏览器客户端（curl、测试脚本）
    return origin.split('://', 1)[-1] == request.host


def processes():
    """扫 /proc 找仿真相关进程，返回 {名字: [pid...]}；不依赖 ROS。"""
    found = {k: [] for k in WATCHED}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit(): continue
        try: argv = (p/'cmdline').read_bytes().split(b'\0')
        except OSError: continue
        names = [Path(a.decode(errors='replace')).name for a in argv[:3] if a]
        for k in WATCHED:
            if k in names: found[k].append(int(p.name))
    return found


def recordings(limit=200):
    if not OUTPUTS.is_dir(): return []
    files = sorted(OUTPUTS.glob('**/*.mp4'), key=lambda f: f.stat().st_mtime, reverse=True)[:limit]
    return [{'path': str(f.relative_to(OUTPUTS)), 'mb': round(f.stat().st_size/1e6, 1),
             'mtime': time.strftime('%Y-%m-%d %H:%M', time.localtime(f.stat().st_mtime))} for f in files]


class RosBridge:
    """后台线程跑 rclpy；按需订阅图像话题，只保留最新一帧 JPEG。"""
    def __init__(self):
        self.error, self.frames, self.lock = None, {}, threading.Lock()
        try:
            import rclpy
            from rclpy.executors import MultiThreadedExecutor
            from rclpy.qos import qos_profile_sensor_data
            from sensor_msgs.msg import Image
        except ImportError as e:
            self.error = f'rclpy 不可用（先 source ROS）：{e}'
            return
        self.Image, self.qos = Image, qos_profile_sensor_data
        rclpy.init()
        self.node = rclpy.create_node('meituan_dashboard')
        self.executor = MultiThreadedExecutor()
        self.executor.add_node(self.node)
        threading.Thread(target=self.executor.spin, daemon=True).start()

    def image_topics(self):
        if self.error: return []
        return sorted(n for n, types in self.node.get_topic_names_and_types() if 'sensor_msgs/msg/Image' in types)

    def graph(self):
        if self.error: return None
        return {'nodes': sorted(ns.rstrip('/')+'/'+n if ns != '/' else '/'+n
                                for n, ns in self.node.get_node_names_and_namespaces() if n != 'meituan_dashboard'),
                'topics': len(self.node.get_topic_names_and_types())}

    def subscribe(self, topic):
        with self.lock:
            if topic in self.frames: return
            self.frames[topic] = {'jpeg': None, 'seq': 0, 'wall': None, 'times': [], 'size': None, 'error': None, 'last_enc': 0.}
        self.node.create_subscription(self.Image, topic, lambda m, t=topic: self.on_image(t, m), self.qos)

    def on_image(self, topic, msg):
        f, now = self.frames[topic], time.monotonic()
        f['times'] = [t for t in f['times'] if now-t < 2.] + [now]
        f['wall'], f['size'] = now, [msg.width, msg.height, msg.encoding]
        if now-f['last_enc'] < 1/STREAM_FPS: return   # 限帧，省 CPU
        try:
            ok, jpg = cv2.imencode('.jpg', to_bgr(msg.encoding, msg.height, msg.width, msg.step, msg.data),
                                   [cv2.IMWRITE_JPEG_QUALITY, 80])
            f['jpeg'], f['error'] = jpg.tobytes(), None
        except ValueError as e:
            f['error'] = str(e)
        f['seq'] += 1
        f['last_enc'] = now

    def stream_stats(self):
        now = time.monotonic()
        return {t: {'fps': round(len([x for x in f['times'] if now-x < 2.])/2., 1),
                    'age_s': None if f['wall'] is None else round(now-f['wall'], 1),
                    'size': f['size'], 'error': f['error']} for t, f in list(self.frames.items())}


async def index(request):
    return web.FileResponse(ROOT/'dashboard.html')


async def status(request):
    ros = request.app['ros']
    graph = await asyncio.to_thread(ros.graph) if not ros.error else None
    return web.json_response({'env': request.app['env'], 'ros_error': ros.error, 'graph': graph,
                              'processes': await asyncio.to_thread(processes),
                              'streams': ros.stream_stats() if not ros.error else {}})


async def config(request):
    ro = request.app['readonly']
    return web.json_response({'readonly': ro, 'presets': [{'id': i, 'name': p['name'], 'cmd': p['cmd'], 'kind': p['kind']}
                              for i, p in enumerate(PRESETS) if not ro or p['kind'] == 'monitor']})


async def topics(request):
    ros = request.app['ros']
    return web.json_response(await asyncio.to_thread(ros.image_topics))


async def list_recordings(request):
    return web.json_response(await asyncio.to_thread(recordings))


async def output_file(request):
    path = (OUTPUTS/request.match_info['path']).resolve()
    if OUTPUTS.resolve() not in path.parents or not path.is_file(): raise web.HTTPNotFound()
    return web.FileResponse(path)   # 支持 Range，浏览器可拖动进度


async def mjpeg(request):
    ros = request.app['ros']
    if ros.error: raise web.HTTPServiceUnavailable(text=ros.error)
    topic = '/'+request.match_info['topic']
    ros.subscribe(topic)
    resp = web.StreamResponse(headers={'Content-Type': 'multipart/x-mixed-replace; boundary=frame',
                                       'Cache-Control': 'no-cache'})
    await resp.prepare(request)
    seq = -1
    try:
        while True:
            f = ros.frames[topic]
            if f['seq'] != seq and f['jpeg'] is not None:
                seq, jpg = f['seq'], f['jpeg']
                await resp.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: %d\r\n\r\n' % len(jpg) + jpg + b'\r\n')
            await asyncio.sleep(1/STREAM_FPS/2)
    except (ConnectionResetError, asyncio.CancelledError):
        pass
    return resp


async def terminal(request):
    """一个 WebSocket 对应一个 PTY；普通模式是交互 bash（预设命令先键入，Ctrl-C 后仍是可用 shell），只读模式直接跑监控命令。"""
    if not same_origin(request): raise web.HTTPForbidden(text='cross-origin terminal refused')
    try: argv, typed, accept_input = terminal_spec(request.query.get('preset', '0'), request.app['readonly'])
    except (IndexError, ValueError): raise web.HTTPBadRequest(text='unknown preset')
    except PermissionError as e: raise web.HTTPForbidden(text=str(e))
    ws = web.WebSocketResponse(max_msg_size=1 << 20)
    await ws.prepare(request)
    master, slave = pty.openpty()
    env = {**os.environ, **request.app['env'], 'TERM': 'xterm-256color'}
    proc = subprocess.Popen(argv, stdin=slave, stdout=slave, stderr=slave, cwd=REPO, env=env,
                            start_new_session=True, close_fds=True)
    os.close(slave)
    os.set_blocking(master, False)
    loop = asyncio.get_running_loop()

    def readable():
        try: data = os.read(master, 65536)
        except (BlockingIOError, InterruptedError): return
        except OSError: data = b''
        if not data:
            loop.remove_reader(master)
            asyncio.ensure_future(ws.close())
            return
        asyncio.ensure_future(ws.send_bytes(data))

    loop.add_reader(master, readable)
    if typed: os.write(master, typed)
    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT: continue
            m = json.loads(msg.data)
            if m['type'] == 'input' and accept_input:
                os.write(master, m['data'].encode())
            elif m['type'] == 'resize':
                fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', int(m['rows']), int(m['cols']), 0, 0))
    finally:
        loop.remove_reader(master)
        try: os.killpg(proc.pid, signal.SIGHUP)
        except ProcessLookupError: pass
        os.close(master)
        await asyncio.to_thread(proc.wait)
    return ws


def make_app(ros, env=SIM_ENV, readonly=False):
    app = web.Application()
    app['ros'], app['env'], app['readonly'] = ros, env, readonly
    app.add_routes([web.get('/', index), web.get('/api/status', status), web.get('/api/config', config), web.get('/api/topics', topics),
                    web.get('/api/recordings', list_recordings), web.get('/outputs/{path:.+}', output_file),
                    web.get('/video/{topic:.+}', mjpeg), web.get('/ws/term', terminal)])
    return app


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--host', default='127.0.0.1', help='终端即本机 shell，非回环地址等于开放远程执行；远程查看请用 SSH 隧道')
    ap.add_argument('--readonly', action='store_true', help='不开交互 shell，只允许监控预设、不接受键盘输入')
    ap.add_argument('--ros-domain-id', default=SIM_ENV['ROS_DOMAIN_ID'], help='默认 67 对应仿真；看实机时填实机所用值')
    a = ap.parse_args()
    env = {**SIM_ENV, 'ROS_DOMAIN_ID': str(a.ros_domain_id)}
    os.environ.update(env)   # rclpy 在 init 时读 ROS_DOMAIN_ID
    ros = RosBridge()
    if ros.error: print(ros.error)
    print(f'监控台：http://{a.host}:{a.port}/' + ('（只读）' if a.readonly else ''))
    web.run_app(make_app(ros, env, a.readonly), host=a.host, port=a.port, print=None)


if __name__ == '__main__':
    main()
