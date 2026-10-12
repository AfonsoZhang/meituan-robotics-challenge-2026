"""Freeze SHA-specific acceptance with original failures intact. OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
raw=Path(__file__).resolve().parent;root=raw.parents[1];w=root/'outputs/moveit-watch-20261011'
commit='688d80d63ba2196e3c1753b69d18c1bfa30919b3';event='sha-'+commit;auto=w/'runs'/event
base=root/'docs/experiments/trajectory-execution-20261012';obs='ENV-TRAJECTORY-20261012';ref='TEAMMATE-TRAJECTORY-20261012'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def tree(a,b,exclude=()):
 for p in sorted(a.rglob('*')):
  if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in exclude:copy(p,b/p.relative_to(a))
assert not base.exists()
idx=read(auto/'index.json');assert len(idx['files'])==303
for f in idx['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
assert not Path('/proc/28269').exists()
for n in ['mtc-repro-5c8f61d8af9f-688d80d63ba2','mtc-trajectory-review-688d80d']:
 v=json.loads(subprocess.check_output(['docker','inspect',n]))[0];h=v['HostConfig']
 assert not v['State']['Running'] and not v['State']['OOMKilled']
 assert h['NetworkMode']=='none' and h['NanoCpus']==2000000000 and h['Memory']==4294967296
 assert not v['Mounts'] and not h['Devices'] and not h['PortBindings'] and not h['Binds'] and not h['Privileged']
 assert h['PidsLimit']==512 and 'ALL' in h['CapDrop'] and 'no-new-privileges' in h['SecurityOpt']
assert not subprocess.check_output(['docker','ps','--filter','name=mtc-','--format','{{.Names}}'],text=True).strip()
s=read(w/'state.json');assert s['active'] is None and s['main_review']['event']==event and s['main_review']['status']=='ACKNOWLEDGED'
review=read(raw/'source-review.json');counts=read(raw/'automatic-counts.json');analysis=read(raw/'supplement-analysis.json');cleanup=read(raw/'cleanup.json')
assert review['all_existing_sources_identical_to_reviewed_main'] and len(review['incremental_changed_files'])==13
assert counts['cpp_total']==424 and counts['summary_complete'] and counts['original_files_verified']==303
assert analysis['supplement']['ubsan']['cases']==424
assert [c['exit_code'] for c in analysis['supplement']['generic_cases']]==[1,0,0]
assert sha(root/'robot/fsm-baseline.repos')==read(raw/'project-before.json')['formal_pin_sha256']
tree(auto,base/'automatic',('index.json','source.bundle'))
copy(auto/'index.json',base/'automatic/original-index.json');copy(w/'runs'/(event+'.log'),base/'automatic/runner.log')
for ext in ['json','patch']:copy(w/'events'/(event+'.'+ext),base/'event'/('event.json' if ext=='json' else 'change.patch'))
for p in raw.iterdir():
 if p.is_file():copy(p,base/'supplement'/p.name)
tree(raw/'logs',base/'supplement/logs');tree(raw/'container',base/'supplement/container')
paths=review['incremental_changed_files']+['LICENSE','README.md','README_FSM.md',
 'src/mtc_ros2_action_cpp/src/pick_place_server.cpp','src/mtc_ros2_action_cpp/CMakeLists.txt',
 'src/mtc_ros2_action_cpp/package.xml','src/mtc_ros2_action_cpp/test/verify_results.py',
 'tests/verify_cpp_audit_results.py','src/mtc_manipulation/mtc_manipulation/pick_place_server.py',
 'src/mtc_task/mtc_task/task_executor.py','src/mtc_manipulation_cpp/src/pick_place_fsm.cpp',
 'src/mtc_manipulation_cpp/include/mtc_manipulation_cpp/pick_place_types.hpp',
 'src/mtc_manipulation_cpp/include/mtc_manipulation_cpp/pick_place_fsm.hpp',
 'src/mtc_core_cpp/include/mtc_core_cpp/motion_primitive.hpp']
for p in paths:copy(raw/'source'/p,base/'source'/p)
for n in ['config.json','state.json']:copy(w/n,base/'monitor'/('state-before-complete.json' if n=='state.json' else n))
for n in ['job.json','receipt.json','attempt-1.log','message.txt']:
 copy(w/'wake'/event/n,base/'monitor'/(n.replace('.json','-before-complete.json') if n.endswith('.json') else n))
receipt=read(w/'wake'/event/'receipt.json');job=read(w/'wake'/event/'job.json');auto_summary=read(auto/'summary.json');now=datetime.now(timezone.utc).isoformat()
inputs={'observation':obs,'upstream':ref,'authorization':['USER-HW-20261011-08','USER-HW-20261011-09'],
 'commit':commit,'previous':review['previous'],'review_base':review['review_base'],'parents':review['parents'],'observed_refs':review['observed_refs'],
 'incremental_changed_files':review['incremental_changed_files'],'cumulative_changed_files':review['cumulative_changed_files'],
 'raw_automatic':str(auto),'raw_supplement':str(raw),'original_index_sha256':sha(auto/'index.json'),
 'original_files_verified':303,'source_bundle_sha256':sha(auto/'source.bundle'),'source_bundle_frozen':False,
 'formal_baseline_file':'robot/fsm-baseline.repos','formal_baseline_sha256':sha(root/'robot/fsm-baseline.repos'),
 'formal_baseline_commit':'1d940f7c5f12561fed6641457c0b4b630a282b05','project_head_before':read(raw/'project-before.json')['head'],
 'environment':auto_summary['environment'],'supplement_runtime':read(raw/'runtime.json'),
 'ros_domains':{'original_moveit':99,'identity':132,'consumer':133,'ubsan':106,'generic_success':134,'generic_mismatch':135,'generic_cancel':136},
 'harness_sha256':{n:sha(raw/n) for n in ['probe_generic.py','probe_generic_remaining.py','ubsan.sh','consumer.sh','identity.sh','analyze_event.py']},
 'source_modified':False,'licences':'Upstream root MIT; Action and trajectory package.xml Apache-2.0 discrepancy retained. Driver/model/SDK licences and vendor checksums unresolved; no re-licensing.'}
write(base/'inputs.json',inputs)
summary={'observation':obs,'recorded_at':now,'commit':commit,'verdict':analysis['verdict'],
 'formal_baseline_advanced':False,'local_merge_performed':False,'existing_sources_identical_to_reviewed_main':True,
 'automatic_status':auto_summary['status'],'automatic_summary_complete':True,
 'build_packages':14,'cpp_cases':424,'cpp_executables':22,'cpp_by_package':counts['cpp_by_package'],
 'python_cases':269,'pure_python_mock_e2e':15,'ros_wiring_cases':6,
 'analysis':analysis,'cleanup':cleanup,
 'main_receipt':{'thread':receipt['thread'],'ack_at':receipt['ack_at'],'queued_at':job['queued_at'],
  'queue_to_ack_seconds':(datetime.fromisoformat(receipt['ack_at'])-datetime.fromisoformat(job['queued_at'])).total_seconds(),
  'attempts':len(job['attempts']),'marker':'MOVEIT_WAKE_ACK_'+receipt['token'],'complete_at_freeze':False},
 'not_completed':analysis['not_completed'],'handoff':analysis['handoff']}
write(base/'summary.json',summary)
(base/'protocol.md').write_text('''# Phase 2B 独立轨迹端口验收协议

来源 TEAMMATE-TRAJECTORY-20261012；观测 ENV-TRAJECTORY-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. CLAIMED 后审阅固定 SHA 688d80d 的全部实际增量。相对正式 1d940f7 共 41 路径，相对已验 a04ac68 仅新增 13 文件：新轨迹包及报告；其余源码逐字相同。父提交 b47b5fe 提供实现。当前分支不含 Planner/视觉包，默认 Action 仍 MockPlanner/AsyncMockMotion。
2. 固定复现 25 步有起止/退出，303 原始文件哈希匹配；原 runner 28269 及全部旧任务容器已停止。在停止原容器的独立快照补验，无网络/设备/挂载/端口，2 CPU/4 GiB/512 PID，cap-drop ALL/no-new-privileges。没有改安装源码、参数/预算/容差，也没有安装依赖。
3. 自动构建 14 包，424 C++ /22 程序、269 Python、15 显式 Mock E2E、6 ROS 接线回归通过。424 为 318 核心+40 Action+66 新轨迹（30 验证器+36 ROS Fake Action）；720 colcon 汇总含包装和 lint。旧审计预期16而实际22程序，且误识别宏模板 TrajectoryValidator.Name、漏22个 INVALID_TEST 展开；核对源码、XML 和交付编译注册审计，424 身份完整且无重复/漏跑/跳过。
4. 补跑新包 rosdep、四份安装文件逐字身份；无参数/非法模式分别在 ROS init 前退出2。外部 CMake consumer 仅 find 新包并链接导出目标，合法轨迹在默认关闭状态被拒绝，ready=false、Goal/Cancel计数0。
5. 独立 build/install 重新构建六个 C++ 包及接口依赖，启用 UBSan、不可恢复、保留调用帧，逐条核对编译参数。424/22 全通过，446汇总含22包装。ROS/DDS系统库未插桩，没有TSan。分析器首次未去掉 colcon 的包名前缀导致身份比较断言，原脚本/错误单独保留；修正分析归一化后与自动424身份完全一致，未重跑测试或改XML。
6. 按交付原 fake_trajectory_probe 三场景进行。只读观察器订阅 JointState/GoalStatus、不建ActionClient，保留唯一执行客户端；每次验证明确GenericSystem、active控制器及空隔离域。原组合入口在 success 首项失败后停止并清理，后两项各自用新域/新驱动依次运行一次，未重跑success。所有配置和测试输入沿用交付代码。
7. success（域134）控制器报告SUCCEEDED/4、六关节实际到+0.02rad，但端口返回STOP_UNKNOWN/230、runtime Fake/controller/state/graph proof lost，1 Goal/1取消尝试、36反馈、stop_confirmed=0/fault_locked=1。独立876个递增时间戳、最大源/接收间隔约9.40/9.55ms；这些外部证据不证明端口内部回调或健康证明可用。聚合错误没有指明具体失败谓词，保留未知原因回交孙嘉明，不修内核、不放宽时限、不用上游成功覆盖。
8. mismatch（域135）起点偏差拒绝，返回210、0 Goal/Cancel、无新UUID且关节未动。cancel（域136）初次stop_confirmed=0，最终CANCELED/5并独立新反馈停稳，1 Goal/Cancel、stop_confirmed=1、无unknown/fault；六关节约+0.004906rad。两场景通过不能覆盖success失败。原探针反转关节名但六关节等幅运动；不同数值重排由单测覆盖，本次Generic运动不能单独证明该项。
9. 三次控制器/驱动均正常退出0、无升级终止，各自停止ROS daemon并确认空域；pal_statistics退出时仍打印invalid-context线程错误，原样保存。核对容器仅keeper后停止，原/补跑均无OOM。固定独立MoveIt本次Plan→Execute通过、最大误差约0.0000765rad/206新戳，move_group仍-11、control0；不计为新端口或完整FSM链。
10. 旧Python早Goal220/延迟INIT510/Cancel受理后220均ABORTED且完成0；B05/create_client、B03被遮挡、B06/Safety退出仍在。新测试仅证明FSM首段运动可注入端口、placement_verified=false；直接FSM Cancel保留FAULT/520，尚无异步停稳桥/runtime host。FSM/Action/Cancel回交孙嘉明；规划契约和标定输入交常建烁，本轮只本地记录，不代发消息。
11. 全部原失败、补跑、独立反馈与清理、ACK/pre-complete状态冻结，index不含自身；bundle/镜像/SDK/构建二进制不入库，仅记录身份。同步manifest、对应文档、README、open-questions及反向引用后complete。最终回执只存raw，原60秒轮询/固定主会话/上海08:00截止不变；没有queue或新监测。

这是Ubuntu 24.04/Jazzy/C++17的独立Mock/Fake软件验收。稳定成功执行、实际Planner/Action/FSM/工具感知接线、异步停稳桥、碰撞接触、TSan、SDK许可/厂商校验值、符号限位、NUC与实机未验收。正式1d940f7基线不动，未合并。根MIT与轨迹/Action Apache-2.0声明差异保留，不重新授权。OpenAI Codex协助审阅实际差异、复用交付入口、编写独立观察/分析/清理脚本并登记事实链，没有上游算法或内核修改。
''')
files=[{'path':str(p.relative_to(base)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(base.rglob('*')) if p.is_file()]
write(base/'index.json',{'schema_version':1,'observation':obs,'created_at':now,'files':files})
print(json.dumps({'files':len(files),'bytes':sum(f['size_bytes'] for f in files),'index_sha256':sha(base/'index.json'),'queue_to_ack_seconds':summary['main_receipt']['queue_to_ack_seconds']},indent=2))
