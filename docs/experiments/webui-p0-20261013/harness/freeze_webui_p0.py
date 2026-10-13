"""Freeze this P0 UI delivery once; prior evidence is never rewritten."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone

root = Path.cwd()
run = Path(json.loads(Path('.agents/webui-p0-current.json').read_text())['run'])
dest = Path('docs/experiments/webui-p0-20261013')
dest.mkdir(parents=True, exist_ok=False)
stamp = datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path, data): path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)

for directory in ['logs', 'container-evidence']:
    for p in (run/directory).rglob('*'):
        if p.is_file(): copy(p, dest/directory/p.relative_to(run/directory))
for pattern in ['browser*.json', 'webui-p0-*.png', 'cleanup*.json']:
    for p in run.glob(pattern): copy(p, dest/p.name)
for name in ['source.patch', 'source-sync.json', 'patch-validation.json', 'upstream-status.json']:
    copy(run/name, dest/name)
copy(run/'qa_relay.py', dest/'harness/qa_relay.py')
copy(Path('.agents/webui_p0_exec.py'), dest/'harness/webui_p0_exec.py')
copy(Path(__file__), dest/'harness/freeze_webui_p0.py')
source_files = {}
for p in Path('webui').rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:
        copy(p, dest/'source-webui'/p.relative_to('webui'))
        source_files[str(p)] = sha(p)

dump(dest/'development-notes.json', dict(
    recorded_at=stamp,
    failures=[
        'Image dependency probe found no cv2. P0 fixture avoids camera generation; installed-package image test is explicitly skipped. No new camera claim.',
        'Initial tar copy attempted chown under cap_drop=ALL and returned 2. Retained source-copy-first-attempt.json; corrected with --no-same-owner without relaxing isolation.',
        'After requiring simulation_mode=false for independent stop, one Python test failed because its synthetic RobotState omitted that field. Explicit non-simulation input and a simulation rejection case added; final 54 pass.',
        'First nested shell version-query command had invalid quoting. p0-runtime.log preserved; structured subprocess argument retry succeeded.',
        'Two browser snapshot HTTP 502 responses occurred while switching fixture sessions; browser-console-switch.log retained. First offline preview navigation raced startup and returned ERR_CONNECTION_REFUSED; retry succeeded.',
        'Documentation updater initially failed to locate the Q19 row. Q19 was then updated explicitly; no stable question IDs removed.'
    ],
    final_browser_delta=[
        'Foreign task display clears the prior local result and elapsed fields; normal fixture paths unaffected.',
        'Quarantine old execution telemetry when a new FJT Status UUID arrives before Feedback; added 12th Node semantic test. Final asset rebuilt and installed bytes verified.',
        'Final static assets reloaded in offline browser. Screenshots from normal sequence/cancel paths precede the last UUID guard; their data paths are unchanged.'
    ],
    cleanup_note='All fixture/UI ROS actors exited before stopping sleep-infinity PID1 (137). Final static packaging restarted only the keeper and build process, then stopped it again. No ROS acceptance was resumed. Offline readonly no-domain preview remains on host port 8772.'
))
dump(dest/'inputs.json', dict(
    date='2026-10-13', raw_run=str(run), personal_start_commit='bda833064c9f24384729285f903e9c730491e6b8',
    baseline_commit='1d940f7c5f12561fed6641457c0b4b630a282b05',
    pr8_commit='7da43228d602a6b23571bfc599d69529ef7bea23',
    phase2c_reference='22b0607948c3e58568870da866287d23c135a9fb',
    upstream_main='b4185155383541e1a4161587c4049a162f74b36d',
    container='mtc-webui-p0-20261013',
    image_snapshot='sha256:78403f2414a89220e3ebba58ad79c2a057e781cf44630feb7984a4d2498d97f8',
    architecture='x86_64', ros='Jazzy', ros_domain_id=94, discovery='LOCALHOST',
    source_files=source_files, formal_pin_sha256=sha(Path('robot/fsm-baseline.repos')),
    hardware_connected=False, upstream_fsm_run=False, c1_revalidated=False,
    runtime_evidence=['logs/p0-runtime-v2.log'],
    package_source_map='source-sync.json', patch_validation='patch-validation.json'
))
dump(dest/'summary.json', dict(
    source_id='ENV-WEBUI-P0-20261013', status='UI_CLIENT_AND_ISOLATED_INTERFACES_PASS; EXECUTOR_PUBLISHER_AND_HARDWARE_PENDING',
    tests=dict(host_python=dict(passed=54,failed=0),node=dict(passed=12,failed=0),
               isolated_ros=dict(passed=5,failed=0),demo=dict(passed=27,failed=0),robot=dict(passed=30,failed=0),
               installed_package=dict(build_passed=True,python_passed=53,python_skipped=1,ros_passed=5,
                                      note='Same tests in installed namespace; not five additional distinct cases. Image test skipped: no cv2.')),
    browser=dict(sequence_success=True,completed_count_separate_from_index=True,
                 injected_cancel_status='ABORTED',injected_cancel_error_code=520,cancel_ack=True,stop_confirmed_after_ack=False,
                 stop_reply_does_not_confirm_stop=True,pause_clears_motion_and_fsm=True,
                 layout_widths=[320,390,768,1440],views=3,horizontal_overflow=False,
                 pageerror_during_success_flow=[],fixture_switch_http_502=2),
    missing_upstream_publisher_fields=['primitive','command_id','trajectory_id','expected_duration_sec','progress'],
    not_verified=['C1 actual delayed-cancel fix','complete Task/PickPlace/Phase2C','NUC or real hardware','new camera acceptance'],
    cleanup='cleanup-final.json', source_patch='source.patch', patch_published=False,
    source_ids=['USER-HW-20261013','TEAMMATE-WEBUI-P0-20261013','ROS2-CONTROLMSGS-20261013'],
    ai_assistance='OpenAI Codex'
))
(dest/'protocol.md').write_text('''# Web UI P0 隔离验证协议

依据 USER-HW-20261013 的任务/FSM、运动与独立安全反馈要求，验证 Web 客户端语义。接口参考 TEAMMATE-WEBUI-P0-20261013、ROS2-CONTROLMSGS-20261013；本轮观测 ENV-WEBUI-P0-20261013。

1. 保持正式 pin 与旧实验目录不变。读取 PR #8 固定 head 和 Phase 2C PR #13 的接口；只变更 Web 模块及安装依赖。
2. 本机 unittest 与 Node 原生测试检查旧/缺失/未来消息、Goal 归属、颜色顺序/完成数分离、FJT 遥测关联及 Stop Request / ACK / Result / 独立证据。
3. 新建独立 Jazzy x86_64 容器：network=none、2 CPU / 4 GiB、cap_drop=ALL、无设备/端口/挂载。固定 domain 94 / LOCALHOST；不启动 FSM/MoveIt/驱动。详见 inputs.json、cleanup.json。
4. `python3 -m webui.p0_integration_check --isolated-fixture` 运行真实 rclpy/DDS/Action 刺激。断言 UI 没有 FJT send_goal/cancel_goal 客户端，验证原生反馈/结果、注入 520、请求后新独立消息与断流。fixture 的 simulation_mode=false 是门禁输入，不是硬件证据。
5. 浏览器经仅用于 QA 的 loopback stdio relay 进入容器 HTTP：选绿—蓝—红（测试口令），观察 1/3 与最终 3/3；另一个 Goal 取消后保留 ACK 和 ABORTED/520、独立停稳未确认。检查暂停和三视图在 320/390/768/1440 宽的布局。消息均来自实际测试发布器，不篡改页面状态。
6. 将同一 UI 以命名空间转换同步到 PR #8 包，colcon 构建并从安装路径运行同一接口检查。source-sync.json 记录映射与哈希，source.patch 限定 Web/依赖；patch-validation.json 记录应用到原 head 后字节一致。安装测试不是新增独立用例数。
7. 停止测试发布器/服务与 relay；确认仅剩 keeper 后停止容器。最终静态资源补打包后再清理，未运行新 ROS actors。离线只读预览无 domain，保留在 host 8772。

通过仅指客户端、包安装与隔离 ROS 接口。执行端真实遥测发布器、C1 修复、完整 Phase 2C、NUC 与硬件均待交付或验收。JSON 示例、测试中的预计时长和进度不是上游已发布字段。旧 33/9、PR #8 的真实 C1 失败与其他冻结运行不改写。

development-notes.json 保留开发失败与截图到最终代码的差异。harness 记录本轮操作，不作为可直接用于实机的部署脚本。source-webui 固定本轮个人源码；index.json 对所有冻结文件计哈希（不自包含）。使用 OpenAI Codex 协助实现、验证和归档。
''')

files = [dict(path=str(p.relative_to(dest)),sha256=sha(p),bytes=p.stat().st_size)
         for p in sorted(dest.rglob('*')) if p.is_file()]
dump(dest/'index.json',dict(schema_version=1,source_id='ENV-WEBUI-P0-20261013',frozen_on=stamp,files=files))
manifest=Path('materials/manifest.json'); data=json.loads(manifest.read_text())
new_ids=['USER-HW-20261013','TEAMMATE-WEBUI-P0-20261013','ROS2-CONTROLMSGS-20261013','ENV-WEBUI-P0-20261013']
assert not any(e['id'] in new_ids for key in ['sources','project_decisions','external_references','local_observations'] for e in data[key])
original='''P0：必须优先实现的功能
1. 任务状态与执行进度

现有的 ExecuteTask 和 PickPlace 接口基本可以满足要求，但希望页面能完整展示：

当前任务 ID、任务模式（基础/序列）。
用户输入的颜色口令及对应顺序。
当前正在处理第几块电池。
当前目标电池 ID、颜色及目标放置工位。
当前 Task FSM 状态。
当前 PickPlace FSM 子状态，例如 MOVE_PRE_ALIGN、ENGAGE、TEST_LIFT、TRANSPORT、SEAT 等。
当前任务完成进度，例如 1/3。
任务最终状态：SUCCEEDED / FAILED / CANCELED / FAULT，以及对应的错误码和原因。
最好有一个直观的 FSM 流程图，能够高亮当前执行阶段，而不是只显示状态字符串。

2. 机械臂运动状态

后续接入 Phase 2C 的 FJT 执行端后，需要显示：

六个关节的实际位置。
六个关节的实际速度。
当前机械臂处于空闲、运动中、取消中、停止确认中还是故障状态。
当前正在执行的 Motion Primitive，例如 side_approach、side_insert、lift、transport 等。
当前 trajectory_id / command_id。
轨迹执行进度、实际执行时间与预计时长。
运动是否成功，以及失败原因。
如果条件允许，可以加入关节目标值和实际值的对比。

这里需要强调：只能显示执行端真实反馈的数据，不能简单根据 FSM 状态推测机械臂是否运动或已经停稳。

3. 安全状态与停止反馈

这个功能比较重要，希望在页面上有一个独立的安全状态区域。

至少显示：

ROS 2 通信是否正常。
各模块是否在线。
机械臂是否 Ready。
Safety Interlock 是否正常。
是否存在 FAULT 锁定。
Stop Request 是否送达。
Stop Confirmed 是否由独立证据确认。
Cancel ACK 和 Cancel Final Result。
特别是：

Cancel ACK ≠ Stop Confirmed

不能把取消请求成功直接显示成机械臂已经安全停止。

目前 PR #8 中正常 Mock 延迟取消出现的 ABORTED/520，也需要保留并正确显示。'''
data['project_decisions'].append(dict(id=new_ids[0],kind='user_message',date='2026-10-13',source='本项目用户会话',original_text=original,
    confirmed=dict(priority='P0：任务状态与执行进度、机械臂运动状态、独立安全状态与停止反馈',
                   motion='只能展示执行端真实反馈，不从 FSM 推测运动或停稳',
                   cancellation='Cancel ACK ≠ Stop Confirmed；保留 PR #8 正常 Mock 延迟取消 ABORTED/520'),
    scope_note='授权本轮 UI 客户端开发及所需隔离接口验证；未确认 NUC/domain/设备上线，不是修复 C1 或接管 FSM/Action/Motion 内核，不恢复已终止的旧完整验收或自动推进正式 pin。',derived_files=[]))
data['external_references'].append(dict(id=new_ids[1],kind='teammate_interface_read_only_snapshot',title='Web UI P0 接口核对：PR #8 与 Phase 2C PR #13',
    url='https://github.com/F1u0rite/meituan_challenge_ws/pull/13',accessed_on='2026-10-13',
    commit='22b0607948c3e58568870da866287d23c135a9fb',pr8_commit='7da43228d602a6b23571bfc599d69529ef7bea23',
    upstream_main='b4185155383541e1a4161587c4049a162f74b36d',pull_requests_status='PR #8 / #13 OPEN at observation; no merge',
    observed=['mtc_interfaces between PR8 and PR13 unchanged','No Web primitive/command_id/trajectory_id/expected duration/progress publisher in reviewed sources','FJT ownership guard counts send_goal service clients; UI passive subscriptions and get_result do not create execution ownership'],
    scope_note='源码与 GitHub 状态核对，不是新 Phase 2C / C1 验收；上游 MIT 及原许可保留。',
    report='docs/web-ui.md',derived_files=[]))
data['external_references'].append(dict(id=new_ids[2],kind='official_ros_interface_reference',title='control_msgs Jazzy controller state and FJT IDL',
    url='https://github.com/ros-controls/control_msgs/tree/jazzy/control_msgs',accessed_on='2026-10-13',
    urls=['https://raw.githubusercontent.com/ros-controls/control_msgs/jazzy/control_msgs/msg/JointTrajectoryControllerState.msg',
          'https://raw.githubusercontent.com/ros-controls/control_msgs/jazzy/control_msgs/action/FollowJointTrajectory.action'],
    version='Official jazzy branch API; installed control_msgs 5.10.0 verified separately',license='BSD-3-Clause',
    use='Jazzy reference/feedback fields, FJT actual.time_from_start and native result; no inferred duration or progress',derived_files=[]))
data['local_observations'].append(dict(id=new_ids[3],kind='isolated_webui_p0_interface_validation',date='2026-10-13',observed_at=stamp,
    triggered_by=[new_ids[0]],upstream_source=new_ids[1],report='docs/web-ui.md',index=str(dest/'index.json'),index_sha256=sha(dest/'index.json'),
    inputs=str(dest/'inputs.json'),summary=str(dest/'summary.json'),raw_output_directories=[str(run.resolve())],
    verification_status='UI_CLIENT_AND_ISOLATED_INTERFACES_PASS; C1_AND_HARDWARE_UNRESOLVED',
    method='Offline Python/Node semantics, actual Jazzy DDS fixture, desktop/mobile browser, installed-package build/import/interface checks, byte-matched PR8 patch and independent stop evidence. No upstream kernel or hardware run.',
    observed=json.loads((dest/'summary.json').read_text()),algorithm_provenance='webui/provenance.json',
    scope_note='54 host Python / 12 Node / 5 unique ROS cases; installed namespace repeats same cases (53 Python pass, 1 camera skip). Injected ABORTED/520 preserves display, does not revalidate actual C1. Missing executor telemetry publisher remains pending.',derived_files=[]))

review_files=[Path(x) for x in ['README.md','docs/web-ui.md','docs/hardware-vision-plan.md','docs/open-questions.md','docs/current-status.md','webui/README.md','webui/telemetry-contract.md','webui/provenance.json']]
review_files += [dest/'protocol.md',dest/'inputs.json',dest/'summary.json']
for key in ['sources','project_decisions','external_references','local_observations']:
    for entry in data[key]:
        found = [str(p) for p in review_files if re.search(r'(?<![A-Z0-9-])'+re.escape(entry['id'])+r'(?![A-Z0-9-])',p.read_text())]
        entry['derived_files']=sorted(set(entry.get('derived_files',[])+found))
dump(manifest,data)
print(json.dumps(dict(frozen_files=len(files),bytes=sum(x['bytes'] for x in files),index_sha256=sha(dest/'index.json')),indent=2))
