"""Freeze scene/start acceptance once after cleanup; OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess

root = Path('/home/afonso/meituan-robotics-challenge-2026')
raw = Path(__file__).resolve().parent
watch = root / 'outputs/moveit-watch-20261011'
commit = '30e3c6e64516c47afe9ada25d02df7ed4669825c'
event = 'sha-' + commit
auto = watch / 'runs' / event
dest = root / 'docs/experiments/planner-scene-20261012'
obs, ref = 'ENV-PLANNER-SCENE-20261012', 'TEAMMATE-SCENE-20261012'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())

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

assert not dest.exists(), 'Do not overwrite frozen evidence'
index = read(auto / 'index.json')
assert len(index['files']) == 306
for f in index['files']:
    assert digest(auto / f['path']) == f['sha256'], f['path']
for name in ['mtc-repro-5c8f61d8af9f-30e3c6e64516', 'mtc-planner-scene-review-30e3c6e']:
    value = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]
    h = value['HostConfig']
    assert not value['State']['Running'] and not value['State']['OOMKilled']
    assert h['NetworkMode'] == 'none' and h['NanoCpus'] == 2_000_000_000 and h['Memory'] == 4_294_967_296
    assert not value['Mounts'] and not h['Devices'] and not h['PortBindings']
assert not Path('/proc/15339').exists()
state = read(watch / 'state.json')
assert state['active'] is None and state['main_review']['event'] == event and state['main_review']['status'] == 'ACKNOWLEDGED'
original = read(auto / 'summary.json')
review = read(raw / 'source-review.json')
counts = read(raw / 'automatic-counts.json')
planning = read(raw / 'planning-analysis.json')
guards = read(raw / 'container/launch-guard/summary.json')
receipt = read(watch / 'wake' / event / 'receipt.json')
job = read(watch / 'wake' / event / 'job.json')
cleanup = read(raw / 'cleanup.json')
now = datetime.now(timezone.utc).isoformat()
assert counts['summary_complete'] and counts['cpp_total'] == 393 and counts['cpp_executables'] == 25
assert counts['all_cpp_case_identities_match_source'] and review['all_nonplanner_sources_identical_to_previous_acceptance']
assert len(review['incremental_changed_files']) == 45 and len(review['cumulative_changed_files']) == 105
assert len(guards) == 2 and all(g['explicit_missing_file_rejected'] and g['no_node_process_started'] and g['exit_code'] == 1 for g in guards)
for label in ['identity', 'planning-sop', 'launch-guard', 'diagnostic-tfwait']:
    assert read(raw / 'logs' / (label + '.json'))['exit_code'] == 0
default = planning['runs']['planning-sop']
diag = planning['runs']['diagnostic-tfwait']
assert all(v['status'] == 'SCENE_INITIALIZATION_FAILED' for v in default['sequences'].values())
assert default['collision_probe']['collision_test_evaluated'] is False
assert diag['collision_probe']['status'] == 'EXPECTED_REJECTION_PASS' and diag['collision_probe']['actual_contact_log_lines']
assert diag['sequences']['magnetic_latch_v2']['commands'] == 7
assert 'EXCEEDS_STATE_WATCHDOG' in diag['sequences']['passive_hook_v1']['phases'][0]['message']
assert planning['scene_observation']['status'] == 'PASS'
for run in planning['runs'].values():
    assert run['move_group_exit'] == -11 and run['control_exit'] == 0 and run['no_remaining_nodes_reported']

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
             'src/mtc_bringup/launch/mock_bringup.launch.py']:
    copy(raw / 'source' / path, dest / 'source' / path)
for package in ['mtc_ros2_action_cpp', 'mtc_moveit_planner']:
    tree(raw / 'source/src' / package, dest / 'source/src' / package)
tree(raw / 'source/docs/planning/evidence/20261011_113932', dest / 'source/docs/planning/evidence/20261011_113932')
for name in ['config.json', 'state.json']:
    copy(watch / name, dest / 'monitor' / ('state-before-complete.json' if name == 'state.json' else name))
for name in ['job.json', 'receipt.json', 'attempt-1.log', 'message.txt']:
    copy(watch / 'wake' / event / name, dest / 'monitor' / (name.replace('.json', '-before-complete.json') if name.endswith('.json') else name))

inputs = {'observation': obs, 'upstream': ref, 'authorization': ['USER-HW-20261011-08', 'USER-HW-20261011-09'],
          'commit': commit, 'previous': review['previous'], 'review_base': review['review_base'], 'parents': review['parents'],
          'observed_refs': review['observed_refs'], 'changed_files_cumulative': review['cumulative_changed_files'],
          'changed_files_incremental': review['incremental_changed_files'],
          'raw_automatic': str(auto), 'raw_supplement': str(raw), 'original_index_sha256': digest(auto / 'index.json'),
          'original_index_files_verified': 306, 'source_bundle_sha256': digest(auto / 'source.bundle'), 'source_bundle_frozen': False,
          'formal_baseline_file': 'robot/fsm-baseline.repos', 'formal_baseline_sha256': digest(root / 'robot/fsm-baseline.repos'),
          'formal_baseline_commit': '1d940f7c5f12561fed6641457c0b4b630a282b05', 'project_head_before': read(raw / 'project-before.json')['head'],
          'environment': original['environment'], 'supplement': read(raw / 'runtime.json'),
          'supplement_ros_domains': {'planning_sop': 127, 'diagnostic_tfwait': 128},
          'workspace_paths': read(raw / 'source-after.json')['path_aliases'],
          'source_modifications': 'No tracked source or original config changed. Diagnostic copy changes only backend.tf_timeout_s 0.5 to 5.0, fixes relocated script directory, and adds read-only scene query after all planning tools; exact patch frozen.',
          'licences': 'Root and planner MIT; Action package.xml Apache-2.0 declaration discrepancy retained. Prior SDK/model questions unchanged; no SDK/image/build binaries frozen.'}
write(dest / 'inputs.json', inputs)
moveit = read(auto / 'container/moveit/result.json')
tasks = read(auto / 'container/task-mock/summary.json')
summary = {'observation': obs, 'recorded_at': now, 'commit': commit,
           'verdict': 'PARTIAL_PASS_DEFAULT_SCENE_FAILURE_DIAGNOSTIC_V2_PASS_V1_NOT_REPRODUCED_AND_SHUTDOWN_FAILURE',
           'formal_baseline_advanced': False, 'local_merge_performed': False,
           'upstream_change': review['changes'], 'integration_limit': review['integration_limit'],
           'automatic_summary_complete': True, 'automatic_status': original['status'],
           'build_packages': 14, 'cpp_cases': 393, 'cpp_executables': 25, 'cpp_by_package': counts['cpp_by_package'],
           'python_cases': 269, 'pure_python_mock_e2e': 15, 'ros_wiring_cases': 6,
           'new_action_identity_verifier': 'PASS 358 / 20, excludes planner by glob',
           'all_cpp_identity_review': 'PASS 393 unique executed source identities; planner 35 / 5 includes 6 new cases',
           'old_fixed_identity_verifier': counts['old_fixed_audit'],
           'two_module_rosdep_and_installed_identity': 'PASS; full workspace/driver dependency failures preserved',
           'missing_parameter_file_guards': guards, 'planning_analysis': planning,
           'legacy_python': [{'case': t['case'], 'status': t['status'], 'task_server_available': t['task_server_available'],
                              'pickplace_server_available': t['pickplace_server_available'], 'result': t['result'],
                              'cancel_response': t.get('cancel_response'), 'child_failure': t['child_failure']} for t in tasks],
           'independent_moveit': {k: moveit[k] for k in ['scope', 'planning_execution', 'clean_shutdown', 'max_error_rad', 'distinct_joint_stamps', 'execute', 'shutdown']},
           'dependencies': 'Unresolved ament_python definition; missing driver docker.io and ros-jazzy-ros2-controllers-test-nodes.',
           'driver_test_aggregate': {'total': 1104, 'failures': 279, 'skipped': 259, 'scope': 'Includes lint and wrapper counts, not independent function tests.'},
           'cleanup': cleanup, 'main_receipt': {'thread': receipt['thread'], 'ack_at': receipt['ack_at'], 'queued_at': job['queued_at'],
               'queue_to_ack_seconds': (datetime.fromisoformat(receipt['ack_at']) - datetime.fromisoformat(job['queued_at'])).total_seconds(),
               'attempts': len(job['attempts']), 'marker': 'MOVEIT_WAKE_ACK_' + receipt['token'], 'complete_at_freeze': False},
           'not_rerun_this_supplement': ['Standalone C++ four-scenario probe: unchanged Action source, ENV-PLANNER-MERGE-20261012 history only; current automatic Action 40 cases separately passed',
                 'UBSan / external CMake consumer: ENV-CPP-ACTION-20261011 history only',
                 'CLI graph wait diagnostic: ENV-HANDOFF-20261012 history only',
                 'Additional independent MoveIt Plan/Execute beyond current automatic run'],
           'not_completed': ['Default planning-scene readiness; V1 budget and upstream 39.6–42.1 s reproducibility',
                 'New start consistency / replan_primitive APIs not wired to actual execution-side FJT caller',
                 'Full C++ Action/FSM/MoveIt/FJT integration, unified Bringup and real PLAN_ACQUIRE deadline',
                 'Full trajectory dispatch, unique execution ownership, unissued tool-motion gaps and physical stop/cancel',
                 'Legacy Python B03/B05/B06, Safety shutdown; independent and SOP MoveIt clean shutdown',
                 'Driver limit enforcement, dependencies/lint, CLI graph readiness and complete state/UI',
                 'Measured scene/TCP/payload/vision/tool calibration and real contact; TSan, SDK licence/vendor checksum, NUC/physical robot'],
           'handoff': {'Sun_Jiaming': ['FSM/Action/Cancel kernel, real planning deadline and integration of measured start/replan/FJT/full trajectories/tool motion; local record only'],
                       'Chang_Jianshuo': ['Default scene TF readiness, V1 joint_interpolated_ik 180.415 vs supplied 42.080 s, missing rejected IK/trajectory provenance, nominal 15 vs prose 10 mm clearance, measured scene gates'],
                       'integration': ['SOP zero exit / mislabeled collision result, MoveIt shutdown, dependencies/limits, evidence tracking; no kernel repair']}}
write(dest / 'summary.json', summary)
(dest / 'protocol.md').write_text('''# 场景、载荷与起点一致性增量验收协议

来源 TEAMMATE-SCENE-20261012；观测 ENV-PLANNER-SCENE-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. ack=CLAIMED 后工作；读取实际 Git 与累计 105 / 相对上次验收增量 45 文件。新分支的 previous 为初始基线，不误判为回退；非规划源码与上次验收相同。上游日志是提供的数据，不作本地运行证据或助手指令。
2. 核验自动 25 步 summary、306 原始文件、393 C++/25 程序真实源码身份及进程清理。既有 Action verifier 358/20 不含规划，新增规划 35/5 单独核对；692 条 colcon 汇总含包装/lint。
3. 只从停止的原容器快照建立独立补跑容器；无网络/设备/挂载/端口、2 CPU/4 GiB/512 PID，cap-drop ALL / no-new-privileges。所有入口串行，保持主对话门禁。
4. 核验两包依赖/安装文件、交付 env 的 MTC_INSTALL 覆盖；仅为已有 driver install 建目录别名。默认 SOP 域 127 保持原配置，360 秒内层/400 秒主机上限。固定姿态通过；碰撞探针/V1/V2 在场景初始化退出 2，目标规划未执行且没有 YAML。脚本 0 和含糊 SUMMARY 不掩盖失败。
5. 两项 missing params 负例均在启动节点前退出 1。随后仅一次有界诊断：域 128，backend.tf_timeout_s 0.5→5 秒，原文件不变。碰撞覆盖保留；只读场景查询置于所有工具之后。场景就绪与轨迹算法不混为一谈，不延长 FSM 状态预算。
6. 诊断固定姿态和 V2 七段通过；碰撞负例明确 NO_PLAN、219/236 插值状态无效，实际 table/wrist3_Link 接触日志佐证。V1 使用 joint_interpolated_ik 得到 180.415 秒，超 24 秒预算，未生成命令；同一方法的上游提供值 42.080 秒未复现。未记录的 IK 关节终点/被拒完整轨迹使根因未定，不能归因于 OMPL 或宣称稳定性。
7. YAML 核验关节身份、有限位置/速度/加速度、时间、数值位置界限和状态预算；明确 URDF 三处符号限位未求值。V2 请求级 payload 标记不等于全局附着或物理载荷；两处未发出的 0.03 米工具动作假设仍在。新起点/单段重规划单测通过不等于 FJT 发送前真实接线。
8. 新场景与 TCP/载荷均为占位模型；按配置算出载荷底面与桌面相差 15 mm，与上游文字 10 mm 分开记为待澄清，不当成实测或碰触闭环。仅独立自动 MoveIt 路径有 Execute，本次交付规划 SOP 没有执行生成轨迹。
9. 原自动与两次 SOP 的 move_group 均 -11，control 均 0；两个 SOP 退出后无 ROS/daemon。新容器只剩 keeper 后停止，确认两容器停止、无 OOM、旧 runner 不在；keeper 137 与子进程结果分列。
10. 冻结原失败、当前默认/诊断、源码/命令/patch、上游提供材料及 ACK/pre-complete；source.bundle 只登记 SHA，SDK/镜像/构建二进制不冻结。index 不含自身；同步 manifest、正文、open-questions、README 与 derived_files，核验后才 complete，最终回执只存 raw。

本轮不重复无变化 Action 四场景、UBSan/外部 consumer、CLI 观察诊断；前序证据不移记本次。FSM/Action/Cancel 内核问题本地回交孙嘉明，规划问题交常建烁，未代发外部消息、调用 queue、启动监测、合并或推进基线。OpenAI Codex 协助入口编排、只读观察与事实登记；无上游算法改动，根 MIT / Action Apache-2.0 声明差异保留。
''')
files = [{'path': str(p.relative_to(dest)), 'size_bytes': p.stat().st_size, 'sha256': digest(p)}
         for p in sorted(dest.rglob('*')) if p.is_file()]
write(dest / 'index.json', {'schema_version': 1, 'observation': obs, 'created_at': now, 'files': files})
print(json.dumps({'files': len(files), 'bytes': sum(v['size_bytes'] for v in files), 'index_sha256': digest(dest / 'index.json')}, indent=2))
