"""Freeze this planning event after process cleanup; OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,subprocess,difflib
root=Path('/home/afonso/meituan-robotics-challenge-2026');raw=root/'outputs/planner-acceptance-20261011-fcdd8ea';w=root/'outputs/moveit-watch-20261011';commit='fcdd8eae897cbc37c539d4bad57b712f08124938';event='sha-'+commit;auto=w/'runs'/event;dest=root/'docs/experiments/planner-acceptance-20261012';obs='ENV-PLANNER-20261012'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def tree(a,b,ex=()):
 for p in sorted(a.rglob('*')):
  if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in ex:copy(p,b/p.relative_to(a))
assert not dest.exists()
idx=json.loads((auto/'index.json').read_text());assert len(idx['files'])==290
for f in idx['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
for c in ['mtc-repro-5c8f61d8af9f-fcdd8eae897c','mtc-planner-review-fcdd8ea']:
 v=json.loads(subprocess.check_output(['docker','inspect',c]))[0];assert not v['State']['Running'] and not v['State']['OOMKilled']
assert not Path('/proc/94194').exists()
state=json.loads((w/'state.json').read_text());assert state['active'] is None and state['main_review']['event']==event and state['main_review']['status']=='ACKNOWLEDGED'
original=json.loads((auto/'summary.json').read_text());review=json.loads((raw/'source-review.json').read_text());counts=json.loads((raw/'automatic-counts.json').read_text());analysis=json.loads((raw/'planning-analysis.json').read_text());receipt=json.loads((w/'wake'/event/'receipt.json').read_text());job=json.loads((w/'wake'/event/'job.json').read_text());cleanup=json.loads((raw/'cleanup.json').read_text());now=datetime.now(timezone.utc).isoformat()
assert len(original['steps'])==25 and counts['summary_complete']
assert json.loads((raw/'logs/dependency-identity.json').read_text())['exit_code']==0
sop=raw/'source/src/mtc_moveit_planner/scripts/run_planning_evidence.sh';diagnostic=raw/'diagnostic-tfwait-sop.sh'
(raw/'diagnostic-sop.patch').write_text(''.join(difflib.unified_diff(sop.read_text().splitlines(keepends=True),diagnostic.read_text().splitlines(keepends=True),fromfile='upstream/run_planning_evidence.sh',tofile='local/diagnostic-tfwait-sop.sh')))
tree(auto,dest/'automatic',('index.json','source.bundle'));copy(auto/'index.json',dest/'automatic/original-index.json');copy(w/'runs'/(event+'.log'),dest/'automatic/runner.log')
copy(w/'events'/(event+'.json'),dest/'event/event.json');copy(w/'events'/(event+'.patch'),dest/'event/change.patch')
for p in raw.iterdir():
 if p.is_file():copy(p,dest/'supplement'/p.name)
tree(raw/'logs',dest/'supplement/logs');tree(raw/'container',dest/'supplement/container')
for p in ['LICENSE','docs/planning/PLANNING_HANDOFF.md','docs/planning/README.md']:
 copy(raw/'source'/p,dest/'source'/p)
tree(raw/'source/src/mtc_moveit_planner',dest/'source/src/mtc_moveit_planner')
for name in ['config.json','state.json']:copy(w/name,dest/'monitor'/('state-before-complete.json' if name=='state.json' else name))
for name in ['job.json','receipt.json','attempt-1.log','message.txt']:
 copy(w/'wake'/event/name,dest/'monitor'/(name.replace('.json','-before-complete.json') if name.endswith('.json') else name))
inputs={'observation':obs,'upstream':'TEAMMATE-PLANNER-20261011','authorization':['USER-HW-20261011-08','USER-HW-20261011-09'],'commit':commit,'previous':review['previous'],'parents':review['parents'],'observed_refs':original['upstream']['refs'],'changed_files':review['changed_files'],'raw_automatic':str(auto),'raw_supplement':str(raw),'original_index_sha256':sha(auto/'index.json'),'original_index_files_verified':290,'source_bundle_sha256':sha(auto/'source.bundle'),'source_bundle_frozen':False,'formal_baseline_file':'robot/fsm-baseline.repos','formal_baseline_sha256':sha(root/'robot/fsm-baseline.repos'),'formal_baseline_commit':review['previous'],'environment':original['environment'],'supplement':json.loads((raw/'runtime.json').read_text()),'supplement_ros_domains':[116,117],'workspace_aliases':{'/driver_ws/install_no_symlink':'/driver_work/install','/candidate/install/planner':'/candidate-install'},'delivered_sop_sha256':sha(sop),'only_diagnostic_parameter_difference':analysis['only_diagnostic_parameter_difference'],'source_modifications':'None. Internal workspace aliases only; separate diagnostic SOP copy injects tf_timeout_s=5.0 without modifying delivered sources/installed config.','licences':'Root LICENSE and planner package.xml MIT. Previously recorded SDK/model licence questions unchanged; no SDK/images/binaries frozen.'}
write(dest/'inputs.json',inputs)
moveit=json.loads((auto/'container/moveit/result.json').read_text());task=json.loads((auto/'container/task-mock/summary.json').read_text())
summary={'observation':obs,'recorded_at':now,'trigger_local_date':'2026-10-11','supplement_finished_local_date':'2026-10-12','commit':commit,'verdict':'PLANNER_PARTIAL_PASS_WITH_DEFAULT_TF_WATCHDOG_AND_SHUTDOWN_FAILURES','formal_baseline_advanced':False,'merge_performed':False,'automatic_summary_complete':True,'automatic_status':original['status'],'build_packages':13,'cpp_cases':347,'cpp_by_package':counts['cpp_by_package'],'cpp_executables':20,'python_cases':269,'pure_python_mock_e2e':15,'new_planner_source_test_identity':'PASS 29 cases / 4 executables','ros_wiring':'NOT RUN: no optional regression on this branch','cpp_action':'NOT PRESENT on this separate branch; no claim of 358 Action tests','new_planner_rosdep':'PASS with installed workspace/driver overlays','installed_package_config_launch_identity':'PASS','planner_runs':analysis['runs'],'only_diagnostic_parameter_difference':analysis['only_diagnostic_parameter_difference'],'tf_analysis':analysis['analysis'],'raw_urdf_command_interface_limits':analysis['raw_urdf_command_interface_limits'],'runtime_limit_enforcement':analysis['runtime_limit_enforcement'],'legacy_python':task,'independent_moveit':{k:moveit[k] for k in ['scope','planning_execution','clean_shutdown','max_error_rad','distinct_joint_stamps','execute','shutdown']},'dependencies':'Whole workspace unresolved ament_python key; driver test-nodes/docker.io missing. New planner per-package check passes.','driver_test_aggregate':{'total':1104,'failures':279,'skipped':259,'scope':'includes lint and wrapper records, not independent function count'},'cleanup':cleanup,'main_receipt':{'thread':receipt['thread'],'ack_at':receipt['ack_at'],'queued_at':job['queued_at'],'queue_to_ack_seconds':(datetime.fromisoformat(receipt['ack_at'])-datetime.fromisoformat(job['queued_at'])).total_seconds(),'attempts':len(job['attempts']),'marker':'MOVEIT_WAKE_ACK_'+receipt['token'],'complete_at_freeze':False,'note':'Complete only after frozen evidence, report and fact-chain registration; final raw receipt is not backfilled into frozen files.'},'not_completed':['Default V1/V2 TF startup robustness','V1 136.515 s trajectory versus 24 s state budget; no timeout relaxation applied','New planner full trajectories into real C++ Action/FSM/FJT including unique execution ownership/cancel/stop','Actual 2 s PLAN_ACQUIRE deadline with real async backend','Tool insertion/withdrawal execution and actual start-state matching','Calibrated TCP/stations/dynamic TF timing, camera/tool/battery/environment collision scene and attached battery','MoveIt clean shutdown; driver limits enforcement, dependencies/lint','TSan, SDK licence/vendor checksum, NUC and physical robot, full Web UI/state topics'],'handoff':{'Chang_Jianshuo':['default TF readiness','planning scene / calibration gates / numeric limit declaration','V1 planning/profile coordination'],'Sun_Jiaming':['FSM state deadlines / Action integration / tool gaps / cancel & stop / unique executor; no kernel fix taken over'],'integration':['driver and MoveIt shutdown','raw model symbolic command limits verification','dependency and evidence tracking']}}
write(dest/'summary.json',summary)
(dest/'protocol.md').write_text('''# MoveIt 规划分支隔离验收协议

来源 ENV-PLANNER-20261012；提交 TEAMMATE-PLANNER-20261011；授权 USER-HW-20261011-08、USER-HW-20261011-09。事件 10 月 11 日收到，补跑与证据整理跨到 10 月 12 日，均按上海日期标注。

1. ack 为 CLAIMED 后才工作；确认原 PID 和容器停止，核对完整 25 步 summary、完整 53 文件 diff 与原 290 个文件 SHA。
2. 只对停止原容器做独立文件系统快照；无网络/设备/挂载/发布端口，2 CPU / 4 GiB / 512 PID、cap-drop ALL、no-new-privileges。未重启或改写原失败容器；下一 SHA 保持主对话门禁。
3. 单独核验正常 XML：原四核心 318 + 新规划 29 = 347；新 29 个测试身份和源码 TEST 全部对应。此分支没有 C++ Action 包或 PR #2 回归，不套用另一分支的 358/6 数字。FakeBackend/spy Motion 的 FSM 用例不能替代真实 MoveIt 执行。
4. 保持代码与默认参数不变，只在容器内用目录别名适配既有 workspace/install 布局；ROS domain 116 运行交付 run_planning_evidence.sh。固定姿态 PASS、V1/V2 均 TF_UNAVAILABLE；所有原文件保留。脚本 0 不等于各工具或退出通过。
5. 外部 TF 文本和图有 world/base_link，故执行一次有界诊断：domain 117，唯一参数变化 backend.tf_timeout_s 0.5→5.0（其余数值、帧、RMW、几何、状态时限不变）。独立 SOP 副本与 patch 留档，未修改上游源文件或安装配置；固定姿态 PASS，V1 超看门狗拒绝，V2 七段规划 PASS。上限 360 秒、host 400 秒；本轮均未超时。不继续重跑直到通过。
6. 离线独立校验完整 YAML 的关节顺序、时间递增、有限位置/速度/加速度、规划器数值位置限位、时长与状态预算、simulation_only、空 target_rad；对未输出的工具插入/退出明确保留起点假设。此阶段不执行新轨迹。初版解析器在 URDF 的 {-2*pi}/{2*pi} 字面量失败，保留脚本/错误；修订只按已阅 planner_config.cpp 数值审计，不能据此声称 ros2_control 已强制限位。
7. 单独检查新包 rosdep 与安装 config/launch/package.xml 源码身份；旧全空间依赖/旧 Python/驱动 lint 失败不覆盖。控制器与 move_group 子进程退出逐条判定，不按 launch/SOP 0 或图清空认定干净退出。
8. 两次 SOP 后进程表仅剩 sleep keeper，再停止补跑容器；原容器亦停止、无 OOM、原 runner 不存在。记录两容器 inspect 与清理。keeper 137 不作 ROS 崩溃计数。
9. automatic/original-index.json 是原始 outputs 索引，含未入库 source.bundle；只登记 bundle SHA。镜像、SDK 和构建二进制不入库；符号链接不复制。index.json 对冻结集全部常规文件计 SHA，不包含自身；其 SHA 登记 manifest。
10. 冻结 ACK/pre-complete 快照；报告及 README、open-questions、manifest/derived_files 同步后才 complete。FSM/Action/Cancel 交孙嘉明；规划事项交常建烁。仅本地交接，不修内核、不发外部消息、不合并或推进基线。

OpenAI Codex 协助编排已有 SOP、独立核验与事实登记；原上游 MIT 声明保留，无算法修改。新规划器成功范围仅为模拟规划，工具候选未由本轮收敛。
''')
files=[{'path':str(p.relative_to(dest)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dest.rglob('*')) if p.is_file()]
write(dest/'index.json',{'schema_version':1,'observation':obs,'created_at':now,'files':files})
print(json.dumps({'files':len(files),'bytes':sum(v['size_bytes'] for v in files),'index_sha256':sha(dest/'index.json')},indent=2))
