"""Freeze exact event, original failures and isolated supplement; Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess

raw = Path(__file__).resolve().parent
root = raw.parents[1]
w = root / 'outputs/moveit-watch-20261011'
commit = 'dc76a0bf0a43f9110f3d24cfa38a2b3478f48dcd'
event = 'sha-' + commit
auto = w / 'runs' / event
base = root / 'docs/experiments/vision-replay-20261012'
obs = 'ENV-VISION-REPLAY-20261012'
ref = 'TEAMMATE-VISIONREPLAY-20261012'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def copy(a, b):
    b.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(a, b)

def tree(a, b, exclude=()):
    for p in sorted(a.rglob('*')):
        if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in exclude:
            copy(p, b / p.relative_to(a))

assert not base.exists(), 'Frozen evidence is append-only'
index = read(auto / 'index.json')
assert len(index['files']) == 301
for f in index['files']:
    assert sha(auto / f['path']) == f['sha256'], f['path']
assert not Path('/proc/56334').exists()
assert not subprocess.check_output(['docker', 'ps', '--filter', 'name=mtc-', '--format', '{{.Names}}'], text=True).strip()
for name in ['mtc-repro-5c8f61d8af9f-dc76a0bf0a43', 'mtc-vision-replay-review-dc76a0b']:
    v = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]
    h = v['HostConfig']
    assert not v['State']['Running'] and not v['State']['OOMKilled']
    assert h['NetworkMode'] == 'none' and h['NanoCpus'] == 2_000_000_000 and h['Memory'] == 4_294_967_296
    assert not v['Mounts'] and not h['Devices'] and not h['PortBindings'] and not h['Binds'] and not h['Privileged']
    assert h['PidsLimit'] == 512 and 'ALL' in h['CapDrop'] and 'no-new-privileges' in h['SecurityOpt']
state = read(w / 'state.json')
assert state['active'] is None and state['main_review']['event'] == event and state['main_review']['status'] == 'ACKNOWLEDGED'
review = read(raw / 'source-review.json')
counts = read(raw / 'automatic-counts.json')
analysis = read(raw / 'supplement-analysis.json')
cleanup = read(raw / 'cleanup.json')
assert review['all_outside_adapter_and_vision_unchanged'] and len(review['incremental_changed_files']) == 6 and len(review['cumulative_changed_files']) == 18
assert sha(root / 'robot/fsm-baseline.repos') == read(raw / 'project-before.json')['formal_pin_sha256']
tree(auto, base / 'automatic', ('index.json', 'source.bundle'))
copy(auto / 'index.json', base / 'automatic/original-index.json')
copy(w / 'runs' / (event + '.log'), base / 'automatic/runner.log')
for ext in ['json', 'patch']:
    copy(w / 'events' / (event + '.' + ext), base / 'event' / ('event.json' if ext == 'json' else 'change.patch'))
copy(w / 'events' / ('sha-' + review['previous'] + '.json'), base / 'event/previous-filtered-event.json')
for p in raw.iterdir():
    if p.is_file():
        copy(p, base / 'supplement' / p.name)
tree(raw / 'logs', base / 'supplement/logs')
tree(raw / 'container', base / 'supplement/container')
paths = set(review['cumulative_changed_files'] + [
    'LICENSE', 'README.md', 'README_FSM.md', 'vision_core/README.md', 'vision_core/pyproject.toml',
    'vision_core/scripts/replay_ros2_p0.py', 'tests/verify_cpp_audit_results.py',
    'src/mtc_ros2_action_cpp/package.xml', 'src/mtc_ros2_action_cpp/src/task_server.cpp',
    'src/mtc_ros2_action_cpp/test/verify_results.py', 'src/mtc_interfaces/msg/BatteryDetection.msg',
    'src/mtc_interfaces/msg/BatteryDetectionArray.msg', 'src/mtc_task/mtc_task/task_executor.py',
    'src/mtc_manipulation/mtc_manipulation/pick_place_server.py'])
paths.update(v['source'] for v in counts['cpp_xml'])
for directory in ['src/mtc_vision_adapter', 'vision_core/tests']:
    paths.update(str(p.relative_to(raw / 'source')) for p in (raw / 'source' / directory).rglob('*') if p.is_file())
for name in sorted(paths):
    copy(raw / 'source' / name, base / 'source' / name)
for name in ['config.json', 'state.json']:
    copy(w / name, base / 'monitor' / ('state-before-complete.json' if name == 'state.json' else name))
for name in ['job.json', 'receipt.json', 'attempt-1.log', 'message.txt']:
    copy(w / 'wake' / event / name, base / 'monitor' / (name.replace('.json', '-before-complete.json') if name.endswith('.json') else name))
timer_root = root / 'outputs/cpp-mock-after-watch-20261012'
timer_state = read(timer_root / 'state.json')
timer_registration = read(timer_root / 'scheduler-registration.json')
assert timer_state['status'] == 'SCHEDULED' and not timer_state['attempts']
assert Path('/proc', str(timer_state['timer_pid'])).exists()
assert all(sha(timer_root / name) == value for name, value in timer_registration['files_sha256'].items())
write(base / 'monitor/deferred-integration-status.json', {
    'checked_at': datetime.now(timezone.utc).isoformat(), 'not_before': timer_state['not_before'],
    'status': timer_state['status'], 'attempts': len(timer_state['attempts']),
    'registered_files_unchanged': True, 'integration_started': False,
    'authorization': ['USER-HW-20261012', 'USER-HW-20261012-02'],
    'scope': 'Only status recorded; this event does not start or reschedule the later integration task.'})
receipt = read(w / 'wake' / event / 'receipt.json')
job = read(w / 'wake' / event / 'job.json')
automatic = read(auto / 'summary.json')
now = datetime.now(timezone.utc).isoformat()
inputs = {
    'observation': obs, 'upstream': ref, 'authorization': ['USER-HW-20261011-08', 'USER-HW-20261011-09'],
    'commit': commit, 'previous': review['previous'], 'review_base': review['review_base'], 'parents': review['parents'],
    'observed_refs': review['observed_refs'], 'incremental_changed_files': review['incremental_changed_files'],
    'cumulative_changed_files': review['cumulative_changed_files'], 'raw_automatic': str(auto), 'raw_supplement': str(raw),
    'original_index_sha256': sha(auto / 'index.json'), 'original_files_verified': len(index['files']),
    'source_bundle_sha256': sha(auto / 'source.bundle'), 'source_bundle_frozen': False,
    'formal_baseline_file': 'robot/fsm-baseline.repos', 'formal_baseline_sha256': sha(root / 'robot/fsm-baseline.repos'),
    'formal_baseline_commit': '1d940f7c5f12561fed6641457c0b4b630a282b05', 'project_head_before': read(raw / 'project-before.json')['head'],
    'environment': automatic['environment'], 'supplement_runtime': read(raw / 'runtime.json'),
    'ros_domains': {'original_modules': 98, 'original_moveit': 99, 'adapter_outer_tf_buffer': 151,
                    'synthetic_natural': 191, 'replay_natural': 192, 'synthetic_sigint': 193, 'replay_sigint': 194, 'no_subscriber': 152},
    'harness_sha256': {p.name: sha(p) for p in raw.iterdir() if p.suffix in ('.py', '.sh')},
    'source_modified': False,
    'licences': 'Root MIT, adapter/Action Apache-2.0 package declarations retained; no relicensing. Cached wheel versions/licenses/hashes retained; wheels not frozen. Driver/model/SDK license/vendor checksum and private visual assets unresolved.'}
write(base / 'inputs.json', inputs)
summary = {
    'observation': obs, 'recorded_at': now, 'commit': commit, 'verdict': analysis['verdict'],
    'formal_baseline_advanced': False, 'local_merge_performed': False,
    'automatic_status': automatic['status'], 'automatic_summary_complete': True,
    'build_packages': 14, 'cpp_cases': 358, 'cpp_executables': 20, 'cpp_by_package': counts['cpp_by_package'],
    'python_cases': 269, 'pure_python_mock_e2e': 15, 'ros_wiring_cases': 6, 'analysis': analysis, 'cleanup': cleanup,
    'main_receipt': {'thread': receipt['thread'], 'ack_at': receipt['ack_at'], 'queued_at': job['queued_at'],
                     'queue_to_ack_seconds': (datetime.fromisoformat(receipt['ack_at']) - datetime.fromisoformat(job['queued_at'])).total_seconds(),
                     'attempts': len(job['attempts']), 'marker': 'MOVEIT_WAKE_ACK_' + receipt['token'], 'complete_at_freeze': False},
    'not_completed': analysis['not_completed'], 'handoff': analysis['handoff']}
write(base / 'summary.json', summary)
(base / 'protocol.md').write_text('''# 视觉回放自然退出与 V4.2 增量验收协议

来源 TEAMMATE-VISIONREPLAY-20261012；观测 ENV-VISION-REPLAY-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. CLAIMED 后读取 dc76a0b 相对 e09d00e 的 6 路径；同时核对自前次已验 e53c09f 起的 18 路径。e09d00e 曾按既有监测过滤规则 relevant=false；其视觉增量在本次累计版本补验。上游资料只作为待验数据。
2. 原 summary 25 步完整、301 原索引文件逐 SHA 一致；确认 runner 56334 及原/旧容器停止，从停止容器建立新补跑快照，无网络/设备/挂载/端口，2 CPU/4 GiB/512 PID，cap-drop ALL/no-new-privileges，不重启原容器。
3. 原 14 包、358 C++/20 程序、269 Python、15 Mock E2E、6 ROS 回归核对源码/XML身份。原 cpp-audit 预期程序数过时；colcon 对 adapter 调 unittest 收集零测试/exit 5，652 汇总不替代该失败。原 Action verifier 与安装代码逐字节身份核对通过。
4. 保持交付源码/门限，仅用容器内部 install 路径别名适配既有安装布局。交付 pytest 57 项（45 safety、3 TF Buffer、5 mock cleanup、4 真实安装进程）全部运行。四进程域 191–194，直接安装入口，period=0.5、wait_for_subscriber=15；两次自然退出必须完整 4 帧且不发信号，两次中途 SIGINT 收 2 帧、不能记为完整送达。replay 仅重标同四帧合成数据外层元数据，无真实录制或采集。
5. 图快照均显示节点名 UNKNOWN、history UNKNOWN/depth 0，只用于消息类型和 RELIABLE/VOLATILE 兼容性；实际 publisher 日志报告 RELIABLE KEEP_LAST(5) VOLATILE。进程/源码身份与最终 keeper-only 清理由独立检查证明，不据图占位字段认定唯一命名节点。RELIABLE acknowledgment 不证明 FSM 接受；未注入真实最终 ACK 超时。
6. 域 152 不建订阅器：默认 wait=0/period=1 发布四帧后自然 exit 0，不声称任何接收；开启 wait=2/period=0.25 后在首帧前明确超时 exit 1，零帧、无虚假完成日志，两例均无升级终止/残留。默认未启用屏障，历史漏帧与广泛可靠性不因此关闭。
7. 23 个既有缓存轮子逐 SHA 核对，无网络下载；独立 system-site-packages venv 保留 setuptools 68.1.2，editable/pip check 通过。公开视觉 80 PASS/1 私有证据 SKIP；此前 62 PASS 加 18 新测试，旧 27 adapter-core 项已含其中。新增平面高度数值等价、视觉假设确认/过期 CAD 清除与诊断字段只证明合成软件契约，不证明实测姿态或性能提升。
8. 两个新增私有 V4.1/V4.2 入口原样尝试，各 exit 1，缺输出父目录、私有记录/先前分析/CAD资料，均在处理帧前失败；保存完整 traceback，BLOCKED。不给目录补造数据，不将未执行基准记为通过。
9. FSM/IDL/Action 与前验相同，Task 仍 MockPerception，未调用视觉 helper；零补跑 Action Goal、零相机。旧 Python 220/510/520、依赖/驱动 lint、独立 MoveIt 通过但 move_group -11 保留。FSM/Action/Cancel 本地回交孙嘉明，视觉入口与数据缺口交孙浩然，可信标定/时钟交韩明赫；不代发消息或修内核。
10. 确认补跑只剩 keeper 后停止并收集，原/补跑均停止、无 OOM，再冻结和生成不含自身的 index；源码 bundle/SDK/镜像/轮子仅登记哈希，原始失败不覆盖。manifest/报告/README/open-questions/derived_files 同步后 complete，最终回执保存在 raw，不回写冻结集。原 60 秒监测及 08:00 截止不变；后续 C++/Web UI 工作继续等待指定时刻和尾部排空。

未合并或推进正式 1d940f7 基线；未验收完整 FSM/实时感知/NUC/实机。OpenAI Codex 协助源码与证据核验、原入口隔离运行、观察/分析/清理和事实登记；未修改上游视觉算法或 FSM/Action/Cancel 内核，许可差异仍保留。
''')
files = [{'path': str(p.relative_to(base)), 'size_bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(base.rglob('*')) if p.is_file()]
write(base / 'index.json', {'schema_version': 1, 'observation': obs, 'created_at': now, 'files': files})
result = {'files': len(files), 'bytes': sum(f['size_bytes'] for f in files), 'index_sha256': sha(base / 'index.json'),
          'queue_to_ack_seconds': summary['main_receipt']['queue_to_ack_seconds']}
write(raw / 'freeze-result.json', result)
print(json.dumps(result, indent=2))
