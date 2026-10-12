"""Freeze perception event after cleanup; no source/algorithm edits. Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess
root = Path('/home/afonso/meituan-robotics-challenge-2026')
raw = Path(__file__).resolve().parent
w = root / 'outputs/moveit-watch-20261011'
commit = '0e329f10e6f607c9c417a54ae60d290b8e2395b5'; event = 'sha-' + commit
auto = w / 'runs' / event
dest = root / 'docs/experiments/vision-adapter-20261012'
obs, ref = 'ENV-VISION-ADAPTER-20261012', 'TEAMMATE-PERCEPTION-20261012'
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, v):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')
def copy(a, b):
    b.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(a, b)
def tree(a, b, exclude=()):
    for p in sorted(a.rglob('*')):
        if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in exclude: copy(p, b / p.relative_to(a))
assert not dest.exists()
idx = read(auto / 'index.json'); assert len(idx['files']) == 301
for f in idx['files']: assert sha(auto / f['path']) == f['sha256'], f['path']
for name in ['mtc-repro-5c8f61d8af9f-0e329f10e6f6', 'mtc-vision-adapter-review-0e329f1']:
    v = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]; h = v['HostConfig']
    assert not v['State']['Running'] and not v['State']['OOMKilled']
    assert h['NetworkMode'] == 'none' and h['NanoCpus'] == 2_000_000_000 and h['Memory'] == 4_294_967_296
    assert not v['Mounts'] and not h['Devices'] and not h['PortBindings']
assert not Path('/proc/18721').exists()
state = read(w / 'state.json')
assert state['active'] is None and state['main_review']['event'] == event and state['main_review']['status'] == 'ACKNOWLEDGED'
original = read(auto / 'summary.json'); review = read(raw / 'source-review.json'); counts = read(raw / 'automatic-counts.json')
analysis = read(raw / 'supplement-analysis.json'); cleanup = read(raw / 'cleanup.json')
receipt = read(w / 'wake' / event / 'receipt.json'); job = read(w / 'wake' / event / 'job.json')
assert counts['cpp_total'] == 358 and counts['cpp_executables'] == 20 and counts['summary_complete']
assert len(review['incremental_changed_files']) == 111 and review['all_nonvision_sources_identical_to_main_acceptance']
assert analysis['tests']['vision-suite-compatible.xml']['pass'] == 62
assert analysis['diagnostic_ros']['status'] == 'PASS_MESSAGE_CONTRACT' and analysis['default_ros']['status'] == 'FAIL'
assert read(raw / 'logs/install-compatible.json')['exit_code'] == 0 and read(raw / 'logs/entrypoints.json')['exit_code'] == 0
tree(auto, dest / 'automatic', ('index.json', 'source.bundle'))
copy(auto / 'index.json', dest / 'automatic/original-index.json')
copy(w / 'runs' / (event + '.log'), dest / 'automatic/runner.log')
for ext in ['json', 'patch']: copy(w / 'events' / (event + '.' + ext), dest / 'event' / ('event.json' if ext == 'json' else 'change.patch'))
for p in raw.iterdir():
    if p.is_file(): copy(p, dest / 'supplement' / p.name)
tree(raw / 'logs', dest / 'supplement/logs')
tree(raw / 'container', dest / 'supplement/container')
for path in review['incremental_changed_files'] + ['LICENSE', 'README.md', 'README_FSM.md',
        'src/mtc_interfaces/msg/BatteryDetection.msg', 'src/mtc_interfaces/msg/BatteryDetectionArray.msg',
        'src/mtc_task/mtc_task/task_executor.py', 'src/mtc_ros2_action_cpp/src/task_server.cpp',
        'src/mtc_ros2_action_cpp/package.xml', 'src/mtc_ros2_action_cpp/test/verify_results.py']:
    copy(raw / 'source' / path, dest / 'source' / path)
for name in ['config.json', 'state.json']:
    copy(w / name, dest / 'monitor' / ('state-before-complete.json' if name == 'state.json' else name))
for name in ['job.json', 'receipt.json', 'attempt-1.log', 'message.txt']:
    copy(w / 'wake' / event / name, dest / 'monitor' / (name.replace('.json', '-before-complete.json') if name.endswith('.json') else name))
now = datetime.now(timezone.utc).isoformat()
inputs = {'observation': obs, 'upstream': ref, 'authorization': ['USER-HW-20261011-08', 'USER-HW-20261011-09'],
    'commit': commit, 'previous': review['previous'], 'parents': review['parents'], 'observed_refs': review['observed_refs'],
    'changed_files': review['incremental_changed_files'], 'raw_automatic': str(auto), 'raw_supplement': str(raw),
    'original_index_sha256': sha(auto / 'index.json'), 'original_files_verified': 301,
    'source_bundle_sha256': sha(auto / 'source.bundle'), 'source_bundle_frozen': False,
    'formal_baseline_file': 'robot/fsm-baseline.repos', 'formal_baseline_sha256': sha(root / 'robot/fsm-baseline.repos'),
    'formal_baseline_commit': '1d940f7c5f12561fed6641457c0b4b630a282b05', 'project_head_before': read(raw / 'project-before.json')['head'],
    'environment': original['environment'], 'supplement_runtime': read(raw / 'runtime.json'),
    'ros_domains': {'original_replay': 129, 'one_wait_diagnostic': 130},
    'dependency_provenance': 'supplement/offline-dependencies.json and final requirements/environment; host PyPI binary download, offline copy/install in no-network container',
    'source_modified': False, 'private_assets_present': False,
    'licences': 'Root MIT and adapter package Apache-2.0 declarations preserved; vision migration lineage and private CAD permissions unverified. Dependency metadata retained, no binaries or private assets frozen.'}
write(dest / 'inputs.json', inputs)
moveit = read(auto / 'container/moveit/result.json'); tasks = read(auto / 'container/task-mock/summary.json')
summary = {'observation': obs, 'recorded_at': now, 'commit': commit,
    'verdict': 'PARTIAL_PASS_VISION_62_PLUS_SKIP_ROS_WAIT5_PASS_DEFAULT_DELIVERY_AND_SHUTDOWN_FAIL_NO_FSM_CONSUMER',
    'formal_baseline_advanced': False, 'local_merge_performed': False,
    'upstream_change': review['changes'], 'integration_limit': review['integration_limit'],
    'automatic_summary_complete': True, 'automatic_status': original['status'],
    'build_packages': 14, 'cpp_cases': 358, 'cpp_executables': 20, 'cpp_by_package': counts['cpp_by_package'],
    'python_cases': 269, 'pure_python_mock_e2e': 15, 'ros_wiring_cases': 6,
    'cpp_audit': {'old_fixed': counts['old_fixed_audit'], 'new_verifier': 'PASS 358 / 20'},
    'colcon_test_exit': 5, 'colcon_test_failure': 'mtc_vision_adapter collects zero tests, no tests ran; 652 successful XML aggregate excludes missing adapter tests and includes wrappers/lint',
    'supplement_analysis': analysis,
    'legacy_python': [{k: a[k] for k in ['case', 'status', 'result', 'child_failure']} for a in tasks],
    'independent_moveit': {k: moveit[k] for k in ['scope', 'planning_execution', 'clean_shutdown', 'max_error_rad', 'distinct_joint_stamps', 'execute', 'shutdown']},
    'dependencies': 'Base rosdep unresolved ament_python; driver docker.io/ros-jazzy-ros2-controllers-test-nodes absent',
    'driver_test_aggregate': {'total': 1104, 'failures': 279, 'skipped': 259, 'scope': 'Includes lint and wrapper counts'},
    'cleanup': cleanup,
    'main_receipt': {'thread': receipt['thread'], 'ack_at': receipt['ack_at'], 'queued_at': job['queued_at'],
        'queue_to_ack_seconds': (datetime.fromisoformat(receipt['ack_at']) - datetime.fromisoformat(job['queued_at'])).total_seconds(),
        'attempts': len(job['attempts']), 'marker': 'MOVEIT_WAKE_ACK_' + receipt['token'], 'complete_at_freeze': False},
    'not_rerun_this_supplement': ['Unchanged standalone Action scenarios, UBSan and external consumer; previous acceptance only',
        'Planner branch SOP/scene/payload: source package not present in this main-derived branch', 'Independent MoveIt beyond current automatic run'],
    'not_completed': analysis['not_completed'] + ['Old Python B03/B05/B06/Safety cleanup, independent MoveIt clean exit, driver lint/dependencies and SDK licence/vendor checksum'],
    'handoff': {'Sun_Haoran': ['Perception test registration, default replay readiness, publisher shutdown, dependency/install guidance, live/validity provenance and source/asset licensing'],
        'Sun_Jiaming': ['FSM actual perception subscription, replay/staleness/finite-pose/frame input gates; static predicate counterexample only, no kernel repair; old B03/B05/B06'],
        'Han_Minghe': ['Clock/TF/frame identity, calibration and actual XYZ/Yaw/ring validation'],
        'integration': ['Preserve failed default/conditional diagnostics, dependency compatibility and cleanup evidence; local handoff only']}}
write(dest / 'summary.json', summary)
(dest / 'protocol.md').write_text('''# 视觉源码迁移与 ROS 回放适配器验收协议

来源 TEAMMATE-PERCEPTION-20261012；观测 ENV-VISION-ADAPTER-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. CLAIMED 后审阅实际 111 文件增量：9 个适配器文件、102 个视觉核心文件。其余源码/IDL 与 main 父版本一致；本分支没有规划包，不把前次场景版本结果移记此分支。
2. 核验自动 25 步、301 原始哈希与已停止原 runner/容器。14 包构建及 358 C++/269 Python/15 E2E/6 ROS 成功；colcon-test 的适配器零测试退出 5 保留，不能用成功 XML 掩盖。
3. 补跑使用停止原容器的独立快照，保持无网络/设备/挂载/端口、2 CPU/4 GiB/512 PID、cap-drop ALL/no-new-privileges；所有入口串行。无相机/Task Goal/运动命令，原安装 ROS 发布器保持不变。
4. 源码新增测试 test_ros2_p0 单独 27 通过、1 私有数据跳过；全视觉测试原环境缺 cv2，保留 collection error。主机下载锁定二进制轮子并记录哈希/许可元数据，再复制至无网络容器。隔离 venv 中初选 setuptools 80.9 与现有 colcon <80 冲突，原 editable 安装失败；PEP517 只解除安装错误，版本冲突仍留。恢复自带 68.1.2 后两条 editable 入口和 pip check 均通过，无上游修改。
5. 公开视觉 62 通过、1 私有 22 帧证据跳过；初始/最终环境两次通过不累加，27 个 adapter 测试包含在 62 内，不等于私有 215 套件。两相机脚本只 --help；生成器产生 16 帧/50 候选严格 JSON，均不可用于运动，真实 replay 0 帧单列。
6. 实际 Jazzy 生成消息/安装发布器/DDS 订阅：域 129 默认 period_s=1，发布 4 帧但只收到最后 1 帧；不得改写为默认通过。一次域 130、period_s=5 的有界诊断收齐 4 帧，逐字段验证颜色/ID/旧时间戳/帧/null→原生 NaN，未改输入、算法或时间戳。匹配就绪的具体根因未定。
7. 图发现实际确认唯一消息类型、RELIABLE、VOLATILE；history UNKNOWN/depth 0，KEEP_LAST(5) 仅记源码配置。默认已看到 replay complete 后仍 spin；诊断末帧后只观察 1.5 秒，尚未到下一 5 秒完成 tick，其原探针 no-loop 标签只能覆盖该窗口。两次 SIGINT 均 shutdown 重复退出 1，无升级杀进程。
8. 默认实测两个负例（空记录/live mode）明确拒绝。收到的 ring=false NaN 候选被现有 Python 静态谓词拒绝；将 flag 人为改 true 的 NaN/旧时间候选被该谓词接纳，只作函数级反例、不发布、不建 Task Goal。C++ 仍 MockPerception、Python 只有注入 provider，无真实 topic 消费链；JSON mode/body_valid 也不在 IDL 中，不能声称完整输入门禁通过。
9. 私有 CAD/真实数据、物理四色/位姿/ID 精度、标定、实际接触/运动均未运行。上游配置 explicit_official/map_calibrated 标签不升级为项目规则/实测事实。根 MIT 与新适配器 Apache-2.0 声明、移植来源/私有许可待核对。
10. 所有进程结束仅剩 keeper 后停止容器，确认原/补跑停止、无 OOM、原 PID 不在。冻结原失败、脚本、初始/最终环境、数据/源码及 ACK/pre-complete；wheel/SDK/镜像/bundle 不冻结，保存版本与哈希。index 不含自身。同步文档四处和 derived_files、核验后 complete，最终回执仅存 raw。

OpenAI Codex 协助验收探针、有限环境诊断、数据核验与事实登记；自身调用参数、wheel 元数据与分析假设错误保留在 harness notes/原日志，未归咎上游算法。视觉问题本地交孙浩然，FSM/Action/Cancel 内核与消费门禁交孙嘉明，标定交韩明赫；未代发消息、queue、新监测、合并或推进基线。
''')
files = [{'path': str(p.relative_to(dest)), 'size_bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(dest.rglob('*')) if p.is_file()]
write(dest / 'index.json', {'schema_version': 1, 'observation': obs, 'created_at': now, 'files': files})
print(json.dumps({'files': len(files), 'bytes': sum(f['size_bytes'] for f in files), 'index_sha256': sha(dest / 'index.json'), 'queue_to_ack_seconds': summary['main_receipt']['queue_to_ack_seconds']}, indent=2))
