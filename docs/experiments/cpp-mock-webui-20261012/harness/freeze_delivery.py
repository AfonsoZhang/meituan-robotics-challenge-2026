"""Freeze new evidence only. Never rewrite prior signed reports or indices."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

raw = Path(__file__).resolve().parent
root = raw.parents[1]
candidate = raw / 'candidate'
dest = root / 'docs/experiments/cpp-mock-webui-20261012'
dest.mkdir(exist_ok=False)
base = 'f7eaa2c0d2887aeada4fd635112c63c237962ff7'
code = '7da43228d602a6b23571bfc599d69529ef7bea23'
observation = 'ENV-CPP-MOCK-WEBUI-20261012'
sha = lambda b: hashlib.sha256(b).hexdigest()

def write_json(name, obj):
    (dest / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def git(*args):
    return subprocess.check_output(['git', '-C', str(candidate), *args])

excluded = []
for srcname, dstname in [('evidence', 'host'), ('logs', 'host-logs'), ('container-evidence', 'runtime')]:
    for path in sorted((raw / srcname).rglob('*')):
        if not path.is_file():
            continue
        rel = path.relative_to(raw / srcname)
        if path.is_symlink() or path.name == 'watch-config.json' or '__pycache__' in rel.parts or path.suffix == '.pyc':
            excluded.append(str(path.relative_to(raw)))
            continue
        target = dest / dstname / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

changed = git('diff', '--name-only', base, code).decode().splitlines()
extra = git('ls-tree', '-r', '--name-only', code, '--',
            'src/mtc_ros2_action_cpp', 'src/mtc_interfaces', 'src/mtc_task_cpp',
            'src/mtc_manipulation_cpp', 'src/mtc_motion_execution_cpp', 'src/mtc_core_cpp',
            'LICENSE').decode().splitlines()
paths = sorted(set(changed + extra))
source_hashes = {}
for name in paths:
    content = git('show', f'{code}:{name}')
    target = dest / 'source' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    source_hashes[name] = sha(content)
(dest / 'source.patch').write_bytes(git('diff', '--binary', base, code))
write_json('source-files.json', {'commit': code, 'base': base, 'changed_paths': changed, 'files': source_hashes})

for name in ['run_step.py', 'qa_relay.py', 'verify_prior.py', 'freeze_delivery.py']:
    target = dest / 'harness' / name
    target.parent.mkdir(exist_ok=True)
    shutil.copy2(raw / name, target)

write_json('inputs.json', {
    'observation': observation,
    'authority': ['USER-HW-20261012', 'USER-HW-20261012-02'],
    'source': 'TEAMMATE-CPPUI-20261012',
    'cutoff': '2026-10-12T08:00:00+08:00',
    'cutoff_main': base, 'candidate_commit': code,
    'candidate_branch': 'fix/cpp-mock-webui-integration-20261012',
    'pull_request': 'https://github.com/F1u0rite/meituan_challenge_ws/pull/8',
    'own_head_before': '96b76245da4c9ffe856d26d156bbd72f7f956a84',
    'formal_pin_unchanged': '1d940f7c5f12561fed6641457c0b4b630a282b05',
    'base_snapshot_image': 'sha256:2f0a27c475acb9ec056cb1741777bd83a08b919e0d9b4ab6bfcc95f3e7af6da9',
    'original_image': 'sha256:8c442d3be3d5c2671d149d320da09388350d261fa452e23bb848aa5978b8a5f1',
    'environment': {'os': 'Ubuntu 24.04.5', 'ros': 'Jazzy', 'cpp': '17', 'python': '3.12.3',
                    'rclcpp': '28.1.22', 'rclcpp_action': '28.1.22', 'rclpy': '7.1.12',
                    'std_msgs': '5.3.8', 'rmw_fastrtps_cpp': '8.4.4', 'g++': '13.3.0'},
    'isolation': {'network': 'none', 'devices': [], 'mounts': [], 'docker_port_bindings': {},
                  'cpus': 2, 'memory_bytes': 4294967296, 'cap_drop': ['ALL'], 'pids_limit': 512,
                  'domain': 161, 'discovery': 'LOCALHOST'},
    'browser_transport': 'Owned host loopback QA relay 127.0.0.1:8769 -> docker exec stdio -> container loopback:8767; no Docker port mapping or external requests; relay stopped.',
    'scope': 'Actual C++ Task/PickPlace ROS Actions with software Mock ports; Web UI integration. No MoveIt, driver, physical robot or complete hardware FSM.',
    'excluded_from_freeze': excluded,
})
cases = json.loads((raw / 'container-evidence/acceptance-final/summary.json').read_text())
checks = json.loads((raw / 'container-evidence/source-integrity.json').read_text())
write_json('summary.json', {
    'observation': observation,
    'status': 'PARTIAL_C1_CANCEL_COMPLETION_UNRESOLVED',
    'code_commit': code,
    'cpp_action_cases_passed': sum(x['tests'] for x in checks['cpp_action_xml']),
    'ui_offline_cases_passed': 39,
    'real_http_cpp_chain_cases': [{k: v for k, v in c.items() if k != 'cleanup'} for c in cases],
    'case_cleanup': {c['case']: c['cleanup']['cleanup_ok'] for c in cases},
    'browser': {'success': True, 'actual_feedback_and_result': True, 'duplicate_server_denied': True,
                'same_namespace_restart_without_replay': True, 'delayed_cancel_completed': False,
                'delayed_cancel_actual_status': 'ABORTED', 'delayed_cancel_actual_error': 520,
                'mobile_no_horizontal_overflow': True, 'stopped_ui_blocks_submission': True},
    'C1': {'owner': '孙嘉明', 'profile': 'success (no stop-evidence fault injection)',
           'browser_parent': '07750616e1bd41eaba003cdfff9ba0bc',
           'browser_child': 'b82da195d639f268b9f47da27b2dec08',
           'cli_parent': '3587bc1fe5b64da7a99405eded248d69',
           'cli_child': 'c861a09931ce7ecf74f2261aca0a6f74',
           'cancel_ack': True, 'parent_and_child_terminal_status': 6, 'error_code': 520,
           'candidate_cause': 'Static evidence-freshness analysis only; exact failing kernel predicate not instrumented/proved.'},
    'watcher': {'status': 'EXPIRED', 'ended_at': '2026-10-12T00:00:00.267972+00:00',
                'completed_signed_events_verified': 14, 'pending': []},
    'cleanup': {'all_cpp_web_processes_exit_zero': True, 'namespace_graphs_empty': True,
                'qa_relay_stopped': True, 'container_stopped': True,
                'container_pid1_exit_code': 137,
                'container_exit_note': 'docker stop terminates remaining sleep infinity PID1 after all ROS/UI processes exited and graphs emptied; no OOM.'},
    'not_accepted': ['C1 delayed cancellation completion', 'fault recovery kernel', 'complete vision/tool/Motion/FJT/MoveIt FSM chain', 'NUC deployment', 'physical robot'],
    'prior_failure_bytes_preserved': 'host/prior-integrity.json; 22 index digests, 20 flat member sets, 2 legacy run schemas index-only, 14 signed report digests',
})
(dest / 'protocol.md').write_text('''# C++ Mock 与 Web UI 冻结协议

来源 ENV-CPP-MOCK-WEBUI-20261012、TEAMMATE-CPPUI-20261012；用户会话授权 USER-HW-20261012 / USER-HW-20261012-02。本集只新增，不改此前签收报告和冻结集。

先确认北京时间 08:00 后 watcher EXPIRED、pending/active/main_review 为空、14 个实际事件签名仍匹配，旧 runner/容器均已停止；再在截止 main 的隔离副本实现。候选提交与完整差异见 inputs.json、source-files.json、source.patch；冻结源码取自实际推送的 Git 提交。未拼接未合并分支，不推进正式 pin。

单容器无外部网络、设备映射、宿主挂载或 Docker 端口映射，2 CPU / 4 GiB。复用已验依赖，源码 docker cp。先构建并运行 40 个 C++ Action 与 39 个 UI 离线回归，再六个串行 HTTP→真实 ROS→C++ Task→C++ PickPlace 场景；记录实际父子 UUID、状态/Feedback/Result/Cancel、唯一服务器/类型/QoS及退出图。浏览器通过本机仅环回的 QA stdio 中转访问，测试后停止中转。

runtime/ 保留全部初次失败和修正后运行、C++ 日志与 Web 会话，host-logs/ 是宿主有界命令记录，host/ 是命令元数据、浏览器回执/截图、环境隔离/清理和既有证据完整性。harness/ 为本轮执行/归档工具。原始 outputs 仍留本机，不整目录上传；不归档实时配置 watch-config.json、缓存或 Git 私有配置。已存在的旧冻结集按自身 index 原样保留。

六项程序断言通过不代表全部取消边界通过：正常 Mock 700 ms Future 延时，浏览器及独立 CLI 延迟取消均 ACK 后实际 ABORTED/520，C1 未关闭。仅静态证据新鲜度分析；内核根因与契约交孙嘉明。正常及时取消 CANCELED/0 不能覆盖此失败。旧 Python/独立 MoveIt/轨迹分支失败同样不被本轮关闭。

完整报告在 docs/cpp-mock-webui-acceptance.md；SOP 与本轮源码在上游独立 PR #8。PR 保持待审、不自动合并。使用 OpenAI Codex 协助启动/观测/UI/诊断与归档；具体导入代码、版本、许可边界见 source/src/mtc_cpp_mock_bringup/provenance.json。未替第三方代码重新授权。
''')
files = []
for path in sorted(dest.rglob('*')):
    if path.is_file():
        data = path.read_bytes()
        files.append({'path': str(path.relative_to(dest)), 'size_bytes': len(data), 'sha256': sha(data)})
write_json('index.json', {'schema_version': 1, 'observation': observation,
                          'created_at': datetime.now(timezone.utc).isoformat(), 'files': files})
print(json.dumps({'path': str(dest), 'files': len(files), 'index_sha256': sha((dest / 'index.json').read_bytes()), 'bytes': sum(x['size_bytes'] for x in files)}))
