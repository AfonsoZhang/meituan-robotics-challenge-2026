"""Freeze this merge event once, after cleanup; OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess

root = Path('/home/afonso/meituan-robotics-challenge-2026')
raw = Path(__file__).resolve().parent
watch = root / 'outputs/moveit-watch-20261011'
commit = '4a1a81652fca39efe2916a19ad49187d29789697'
event = 'sha-' + commit
auto = watch / 'runs' / event
dest = root / 'docs/experiments/planner-merge-20261012'
obs = 'ENV-PLANNER-MERGE-20261012'
ref = 'TEAMMATE-INTEGRATION-20261012'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text())

def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def copy(a, b):
    b.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(a, b)

def tree(a, b, exclude=()):
    for p in sorted(a.rglob('*')):
        if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in exclude:
            copy(p, b / p.relative_to(a))

assert not dest.exists(), 'Frozen evidence must not be overwritten'
index = read(auto / 'index.json')
assert len(index['files']) == 305
for f in index['files']:
    assert digest(auto / f['path']) == f['sha256'], f['path']
for name in ['mtc-repro-5c8f61d8af9f-4a1a81652fca', 'mtc-planner-merge-review-4a1a816']:
    value = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]
    h = value['HostConfig']
    assert not value['State']['Running'] and not value['State']['OOMKilled']
    assert h['NetworkMode'] == 'none' and h['NanoCpus'] == 2_000_000_000 and h['Memory'] == 4_294_967_296
    assert not value['Mounts'] and not h['Devices'] and not h['PortBindings']
assert not Path('/proc/12886').exists()
state = read(watch / 'state.json')
assert state['active'] is None and state['main_review']['event'] == event and state['main_review']['status'] == 'ACKNOWLEDGED'
original = read(auto / 'summary.json')
review = read(raw / 'source-review.json')
counts = read(raw / 'automatic-counts.json')
planning = read(raw / 'planning-analysis.json')
actions = read(raw / 'container/standalone/summary.json')
receipt = read(watch / 'wake' / event / 'receipt.json')
job = read(watch / 'wake' / event / 'job.json')
cleanup = read(raw / 'cleanup.json')
now = datetime.now(timezone.utc).isoformat()
assert counts['summary_complete'] and counts['cpp_total'] == 387
assert all(v['status'] == 'PASS' for v in actions)
assert sum(len(v['checks']) for v in actions) == 40
assert all(v['passed'] for a in actions for v in a['checks'])
assert len([v for a in actions for v in a['shutdown']]) == 6
assert all(v['exit_code'] == 0 and not v['escalated'] for a in actions for v in a['shutdown'])
for label in ['identity', 'standalone', 'planning-sop']:
    assert read(raw / 'logs' / (label + '.json'))['exit_code'] == 0
plan = planning['runs']['planning-sop']
assert 'EXCEEDS_STATE_WATCHDOG' in plan['sequences']['passive_hook_v1']['phases'][0]['message']
assert 'TF_UNAVAILABLE' in plan['sequences']['magnetic_latch_v2']['phases'][0]['message']
assert plan['move_group_exit'] == -11 and plan['control_exit'] == 0

tree(auto, dest / 'automatic', ('index.json', 'source.bundle'))
copy(auto / 'index.json', dest / 'automatic/original-index.json')
copy(watch / 'runs' / (event + '.log'), dest / 'automatic/runner.log')
copy(watch / 'events' / (event + '.json'), dest / 'event/event.json')
copy(watch / 'events' / (event + '.patch'), dest / 'event/change.patch')
for p in raw.iterdir():
    if p.is_file():
        copy(p, dest / 'supplement' / p.name)
tree(raw / 'logs', dest / 'supplement/logs')
tree(raw / 'container', dest / 'supplement/container')
for path in ['LICENSE', 'README.md', 'README_FSM.md', 'docs/planning/README.md', 'docs/planning/PLANNING_HANDOFF.md',
             'docs/migration/PHASE2A_ROS2_ACTION_REPORT.md', 'docs/migration/ROS_WIRING_FIX_20261011.md',
             'src/mtc_bringup/launch/mock_bringup.launch.py']:
    copy(raw / 'source' / path, dest / 'source' / path)
for package in ['mtc_ros2_action_cpp', 'mtc_moveit_planner']:
    tree(raw / 'source/src' / package, dest / 'source/src' / package)
for name in ['config.json', 'state.json']:
    copy(watch / name, dest / 'monitor' / ('state-before-complete.json' if name == 'state.json' else name))
for name in ['job.json', 'receipt.json', 'attempt-1.log', 'message.txt']:
    copy(watch / 'wake' / event / name, dest / 'monitor' / (name.replace('.json', '-before-complete.json') if name.endswith('.json') else name))

inputs = {'observation': obs, 'upstream': ref, 'authorization': ['USER-HW-20261011-08', 'USER-HW-20261011-09'],
          'commit': commit, 'previous': review['previous'], 'parents': review['parents'],
          'observed_refs': original['upstream']['refs'], 'changed_files': review['changed_files_from_planner'],
          'raw_automatic': str(auto), 'raw_supplement': str(raw), 'original_index_sha256': digest(auto / 'index.json'),
          'original_index_files_verified': 305, 'source_bundle_sha256': digest(auto / 'source.bundle'), 'source_bundle_frozen': False,
          'formal_baseline_file': 'robot/fsm-baseline.repos', 'formal_baseline_sha256': digest(root / 'robot/fsm-baseline.repos'),
          'formal_baseline_commit': '1d940f7c5f12561fed6641457c0b4b630a282b05', 'project_head_before': read(raw / 'project-before.json')['head'],
          'environment': original['environment'], 'supplement': read(raw / 'runtime.json'),
          'supplement_ros_domains': {'standalone': [110, 111, 112, 113], 'planning_sop': 126},
          'workspace_aliases': {'/driver_ws/install_no_symlink': '/driver_work/install', '/candidate/install/planner': '/candidate-install'},
          'source_modifications': 'None; original SOP, defaults and algorithms retained. Only workspace directory aliases inside new container.',
          'licences': 'Root and planner MIT; Action package.xml Apache-2.0 declaration discrepancy retained. Prior SDK/model questions unchanged; no SDK/image/build binaries frozen.'}
write(dest / 'inputs.json', inputs)
moveit = read(auto / 'container/moveit/result.json')
tasks = read(auto / 'container/task-mock/summary.json')
summary = {'observation': obs, 'recorded_at': now, 'commit': commit,
           'verdict': 'MERGED_MODULES_PARTIAL_PASS_WITH_PLANNING_WATCHDOG_TF_AND_SHUTDOWN_FAILURES',
           'formal_baseline_advanced': False, 'local_merge_performed': False,
           'upstream_change': 'Merge main a04ac68 into planner fcdd8ea, exact union; both module trees unchanged, no production wiring.',
           'automatic_summary_complete': True, 'automatic_status': original['status'],
           'build_packages': 14, 'cpp_cases': 387, 'cpp_executables': 24, 'cpp_by_package': counts['cpp_by_package'],
           'python_cases': 269, 'pure_python_mock_e2e': 15, 'ros_wiring_cases': 6,
           'new_action_identity_verifier': 'PASS 358 / 20, excludes planner by glob',
           'all_cpp_identity_review': 'PASS 387 unique executed source identities, includes planner 29 / 4',
           'old_fixed_identity_verifier': counts['old_fixed_audit'],
           'two_module_rosdep_and_installed_identity': 'PASS; full workspace/driver dependency failures preserved',
           'standalone_cpp_actions': {'scenarios': 4, 'checks': 40, 'status': 'PASS', 'process_invocations_exit_zero': 6,
                'cases': [{k: a[k] for k in ['case', 'scope', 'domain', 'status', 'checks', 'shutdown', 'nodes_after_shutdown']} for a in actions],
                'stop_scope': 'Trusted Mock Action contract only; PickPlace public result has no independent stop_confirmed field. No actual planner, FJT, tool or physical stop.'},
           'planner_runs': planning['runs'], 'planner_configuration_changed': False,
           'planner_analysis': 'Default V1 reached planning this time but side_insert 42.0717 s exceeded 24 s budget; V2 still TF_UNAVAILABLE. Same planner/source/config as previous fcdd8ea default where both were TF_UNAVAILABLE. This is variable observed failure stage, not a fix or performance improvement. No TF-wait diagnostic repeated; previous 5 s / V2 7-command result remains historical ENV-PLANNER-20261012.',
           'raw_urdf_command_interface_limits': planning['raw_urdf_command_interface_limits'],
           'runtime_limit_enforcement': planning['runtime_limit_enforcement'],
           'legacy_python': [{'case': t['case'], 'status': t['status'], 'task_server_available': t['task_server_available'],
                              'pickplace_server_available': t['pickplace_server_available'], 'result': t['result'],
                              'cancel_response': t.get('cancel_response'), 'child_failure': t['child_failure']} for t in tasks],
           'independent_moveit': {k: moveit[k] for k in ['scope', 'planning_execution', 'clean_shutdown', 'max_error_rad', 'distinct_joint_stamps', 'execute', 'shutdown']},
           'dependencies': 'Unresolved ament_python definition; missing driver docker.io and ros-jazzy-ros2-controllers-test-nodes.',
           'driver_test_aggregate': {'total': 1104, 'failures': 279, 'skipped': 259, 'scope': 'Includes lint and wrapper counts, not function tests.'},
           'cleanup': cleanup, 'main_receipt': {'thread': receipt['thread'], 'ack_at': receipt['ack_at'], 'queued_at': job['queued_at'],
               'queue_to_ack_seconds': (datetime.fromisoformat(receipt['ack_at']) - datetime.fromisoformat(job['queued_at'])).total_seconds(),
               'attempts': len(job['attempts']), 'marker': 'MOVEIT_WAKE_ACK_' + receipt['token'], 'complete_at_freeze': False},
           'not_rerun_this_supplement': ['UBSan / external CMake consumer: ENV-CPP-ACTION-20261011 history only',
                 'Graph CLI wait diagnostic: ENV-HANDOFF-20261012 history only; successful bounded Action client wait does not close CLI gap',
                 'Planner TF wait 5 s diagnostic and V2 seven trajectories: ENV-PLANNER-20261012 history only',
                 'Independent MoveIt Plan/Execute beyond current automatic run'],
           'not_completed': ['Default sequence readiness and V1 motion budget', 'Full C++ Action/FSM/MoveIt/FJT wiring and unified Bringup',
                 'Real PLAN_ACQUIRE deadline, unique execution ownership, full trajectory dispatch, tool-motion gaps and actual start state',
                 'Independent physical stop/cancel evidence, complete state topics and Web UI',
                 'Legacy Python B03/B05/B06 and Safety shutdown', 'MoveIt clean shutdown, driver limit enforcement, dependencies/lint',
                 'Calibrated TCP/vision/tools, environment and attached object collision scene, TSan, SDK licence/vendor checksum, NUC/physical robot'],
           'handoff': {'Sun_Jiaming': ['FSM/Action/Cancel kernel, real async deadline, unique execution and full trajectory/tool integration; local issue handoff only'],
                       'Chang_Jianshuo': ['Default TF readiness, V1 planning profile and state budget coordination, calibrated scene/input gates'],
                       'integration': ['Observer readiness, driver/MoveIt cleanup, dependency declarations, symbolic URDF limits and evidence tracking']}}
write(dest / 'summary.json', summary)
(dest / 'protocol.md').write_text('''# 规划与 Action 合并版本验收协议

来源 TEAMMATE-INTEGRATION-20261012；观测 ENV-PLANNER-MERGE-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. ack=CLAIMED 后才工作。核对双父提交与逐路径身份：相对规划父提交改 28 文件，相对 main 父提交仅增加原有 53 个规划文件；原模块均字节不变。合并事实不视为已完成模块接线。
2. 核验自动 25 步 summary、305 原始文件哈希、原 PID/容器与旧事件容器停止。只快照原容器文件系统至新容器，不重启或覆盖原始运行。
3. 补跑沿用无网络/设备/挂载/端口、2 CPU / 4 GiB / 512 PID、cap-drop ALL / no-new-privileges。整个事件受原主对话门禁保护，独立场景与规划 SOP 串行。
4. 14 包/387 C++/269 Python/15 E2E/6 ROS 是本次自动实测。XML 对应 24 个真实 GTest 程序且逐项对应源码身份；新 Action verifier 只覆盖 358/20，再单独计规划 29/4。不把 colcon 的 685 条包装/lint 汇总当独立用例。
5. 补跑未修改的 Action verifier、两包 rosdep、安装文件身份和既有四场景独立程序探针。Mock Task/PickPlace 与独立 Motion 分域运行，40 项检查通过；六次服务器均正常退出，容器仅剩 keeper 后才进入下一步。Mock Cancel 不证明物理停稳。
6. 容器内仅建两处工作空间路径别名，保持交付 SOP 和默认配置原样，域 126 上限 360 秒/host 400 秒。固定姿态通过；V1 超 24 秒状态预算、V2 TF 不可用，两序列均无命令输出。SOP 返回 0 不能覆盖工具子进程 1 或 move_group -11。
7. 核验固定姿态 YAML 的关节顺序、时间单调、有限数值、规划器数值位置界限；记录 URDF 未求值限位字面量，运行时强制限位未验。此 SOP 只规划，不发送规划器轨迹。原自动独立 MoveIt Plan/Execute 另列。
8. 前次默认/5 秒 TF 诊断与本次原样结果分开。相同代码出现不同失败阶段不等于修复；无新证据需要时不重复旧诊断或循环重跑。UBSan、外部 consumer、CLI 图观察诊断只引用历史，不算本次运行。
9. 清理前确认无本轮 ROS 进程/daemon、tracked source diff 为空，仅剩 keeper。停止新容器、收集证据，核实两容器均停止且无 OOM、旧 runner 不在；keeper 137 与 ROS 子进程结果分开。
10. 冻结原始失败、源码/补跑命令、数据、清理与 ACK/pre-complete。source.bundle 只登记 SHA；SDK、镜像、构建二进制不冻结。index 索引常规文件且不含自身，SHA 登记 manifest。文档四处及 derived_files 同步后才 complete；最终回执保存在原始目录，不回写冻结集。

FSM/Action/Cancel 内核问题仅本地回交孙嘉明；规划问题交常建烁，集成侧保留清理/依赖/就绪验证。未接管内核、发外部消息、调用 queue、启动监测、合并或推进基线。OpenAI Codex 协助既有入口编排、只读身份/结果核验和事实登记；无上游算法修改，根 MIT / Action Apache-2.0 声明差异保留。
''')
files = [{'path': str(p.relative_to(dest)), 'size_bytes': p.stat().st_size, 'sha256': digest(p)}
         for p in sorted(dest.rglob('*')) if p.is_file()]
write(dest / 'index.json', {'schema_version': 1, 'observation': obs, 'created_at': now, 'files': files})
print(json.dumps({'files': len(files), 'bytes': sum(v['size_bytes'] for v in files), 'index_sha256': digest(dest / 'index.json')}, indent=2))
