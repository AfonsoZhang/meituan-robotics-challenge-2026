"""Freeze this event after cleanup; preserve original failure evidence. Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
raw=Path(__file__).resolve().parent;root=raw.parents[1];w=root/'outputs/moveit-watch-20261011'
commit='f7eaa2c0d2887aeada4fd635112c63c237962ff7';event='sha-'+commit;auto=w/'runs'/event
base=root/'docs/experiments/planner-main-20261012';obs='ENV-PLANNER-MAIN-20261012';ref='TEAMMATE-PLANNERMAIN-20261012'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def tree(a,b,exclude=()):
 for p in sorted(a.rglob('*')):
  if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in exclude:copy(p,b/p.relative_to(a))
assert not base.exists()
idx=read(auto/'index.json');assert len(idx['files'])==305
for f in idx['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
assert not Path('/proc/24525').exists()
for n in ['mtc-repro-5c8f61d8af9f-f7eaa2c0d288','mtc-planner-main-review-f7eaa2c']:
 v=json.loads(subprocess.check_output(['docker','inspect',n]))[0];h=v['HostConfig']
 assert not v['State']['Running'] and not v['State']['OOMKilled']
 assert h['NetworkMode']=='none' and h['NanoCpus']==2000000000 and h['Memory']==4294967296
 assert not v['Mounts'] and not h['Devices'] and not h['PortBindings'] and not h['Binds'] and not h['Privileged']
s=read(w/'state.json');assert s['active'] is None and s['main_review']['event']==event and s['main_review']['status']=='ACKNOWLEDGED'
review=read(raw/'source-review.json');counts=read(raw/'automatic-counts.json');analysis=read(raw/'supplement-analysis.json');cleanup=read(raw/'cleanup.json')
assert review['whole_tree_identical_to_reviewed_commit'] and len(review['changed_files_from_main'])==53
assert counts['cpp_total']==387 and counts['summary_complete'] and counts['original_files_verified']==305
assert analysis['automatic']['moveit']['planning_execution']=='FAIL'
assert analysis['supplement']['moveit_diagnostic']['planning_execution']=='PASS'
assert sha(root/'robot/fsm-baseline.repos')==read(raw/'project-before.json')['formal_pin_sha256']
tree(auto,base/'automatic',('index.json','source.bundle'))
copy(auto/'index.json',base/'automatic/original-index.json')
copy(w/'runs'/(event+'.log'),base/'automatic/runner.log')
for ext in ['json','patch']:copy(w/'events'/(event+'.'+ext),base/'event'/('event.json' if ext=='json' else 'change.patch'))
for p in raw.iterdir():
 if p.is_file():copy(p,base/'supplement'/p.name)
tree(raw/'logs',base/'supplement/logs');tree(raw/'container',base/'supplement/container')
paths=review['changed_files_from_main']+['LICENSE','README.md','README_FSM.md',
 'src/mtc_ros2_action_cpp/src/pick_place_server.cpp','src/mtc_ros2_action_cpp/CMakeLists.txt',
 'src/mtc_ros2_action_cpp/package.xml','src/mtc_ros2_action_cpp/test/verify_results.py',
 'tests/verify_cpp_audit_results.py','src/mtc_manipulation/mtc_manipulation/pick_place_server.py',
 'src/mtc_task/mtc_task/task_executor.py']
for p in paths:copy(raw/'source'/p,base/'source'/p)
for n in ['config.json','state.json']:copy(w/n,base/'monitor'/('state-before-complete.json' if n=='state.json' else n))
for n in ['job.json','receipt.json','attempt-1.log','message.txt']:
 copy(w/'wake'/event/n,base/'monitor'/(n.replace('.json','-before-complete.json') if n.endswith('.json') else n))
receipt=read(w/'wake'/event/'receipt.json');job=read(w/'wake'/event/'job.json');auto_summary=read(auto/'summary.json');now=datetime.now(timezone.utc).isoformat()
inputs={'observation':obs,'upstream':ref,'authorization':['USER-HW-20261011-08','USER-HW-20261011-09'],
 'commit':commit,'previous':review['previous'],'parents':review['parents'],'observed_refs':review['observed_refs'],
 'changed_files_from_main':review['changed_files_from_main'],'tree':review['tree'],
 'identical_reviewed_commit':review['previous_review_commit'],'identical_reviewed_tree':review['previous_review_tree'],
 'previous_frozen_index':review['previous_frozen_index'],'previous_frozen_index_sha256':review['previous_frozen_index_sha256'],
 'previous_frozen_files_verified':review['previous_frozen_files_verified'],'previous_signed_report_sha256':review['previous_signed_report_sha256'],
 'raw_automatic':str(auto),'raw_supplement':str(raw),'original_index_sha256':sha(auto/'index.json'),
 'original_files_verified':305,'source_bundle_sha256':sha(auto/'source.bundle'),'source_bundle_frozen':False,
 'formal_baseline_file':'robot/fsm-baseline.repos','formal_baseline_sha256':sha(root/'robot/fsm-baseline.repos'),
 'formal_baseline_commit':'1d940f7c5f12561fed6641457c0b4b630a282b05','project_head_before':read(raw/'project-before.json')['head'],
 'environment':auto_summary['environment'],'supplement_runtime':read(raw/'runtime.json'),
 'ros_domains':{'original_moveit':99,'one_wait5_diagnostic':131},
 'probe_original_sha256':sha(raw/'probe_moveit_original.py'),'probe_diagnostic_sha256':sha(raw/'probe_moveit_wait5.py'),
 'diagnostic_patch':'supplement/probe-diagnostic.patch','source_modified':False,
 'licences':'Upstream root/planner MIT; Action package.xml Apache-2.0 discrepancy retained. Driver/model/SDK licences and vendor checksums unchanged/unresolved; not re-licensed.'}
write(base/'inputs.json',inputs)
summary={'observation':obs,'recorded_at':now,'commit':commit,'verdict':analysis['verdict'],
 'formal_baseline_advanced':False,'local_merge_performed':False,'source_tree_equal_to_prior':True,
 'automatic_status':auto_summary['status'],'automatic_summary_complete':True,
 'build_packages':14,'cpp_cases':387,'cpp_executables':24,'cpp_by_package':counts['cpp_by_package'],
 'python_cases':269,'pure_python_mock_e2e':15,'ros_wiring_cases':6,
 'analysis':analysis,'cleanup':cleanup,
 'main_receipt':{'thread':receipt['thread'],'ack_at':receipt['ack_at'],'queued_at':job['queued_at'],
  'queue_to_ack_seconds':(datetime.fromisoformat(receipt['ack_at'])-datetime.fromisoformat(job['queued_at'])).total_seconds(),
  'attempts':len(job['attempts']),'marker':'MOVEIT_WAKE_ACK_'+receipt['token'],'complete_at_freeze':False},
 'not_completed':analysis['not_completed'],'handoff':analysis['handoff']}
write(base/'summary.json',summary)
(base/'protocol.md').write_text('''# 规划 PR #3 主线合并事件验收协议

来源 TEAMMATE-PLANNERMAIN-20261012；观测 ENV-PLANNER-MAIN-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. 先 CLAIMED，再比较实际提交、父版本、文件内容及模式。f7eaa2c 的双父为 a04ac68 / 4a1a816，较主线增加 53 个原规划文件；整棵 Git tree 与前次验收 4a1a816 完全相同。复核 ENV-PLANNER-MERGE-20261012 的 486 文件索引和已签收报告；前次结果不改记为本次运行。
2. 审阅源码/交付 SOP 及固定运行真实日志。25 步起止/退出完整、305 原始文件哈希匹配、原 runner/容器已停止。14 包 / 387 C++ / 269 Python / 15 E2E / 6 ROS 通过；387 的每个测试身份与源码一致，分 318 核心、40 Action、29 Planner；colcon 685 含包装与 lint，不作独立功能计数。
3. 旧 C++ 审计要求 16 个程序而实际 20；在停止原容器的独立快照中补跑交付的新审计入口：358/20 通过，规划 29/4 另核对。两个包 rosdep 与五份安装文件逐字节身份通过。源码/默认配置/预算不变，无依赖安装或网络访问。
4. 原独立 MoveIt 规划成功，但 ExecuteTrajectory ABORTED / -4，日志明确内部 FJT ActionClient 尚未连接；此时外部探针可见唯一 FJT server。原控制器未收到 goal，未有最终误差测量。日志中加入 FJT 控制器至连接错误约 0.342 秒；外部服务可见不证明内部客户端就绪。
5. 仅做一次有界诊断：原探针复制到容器临时目录，隔离域 131，保留原 20 次 spin 后再用单调时钟 spin 5 秒。不修改任何上游代码、容差/控制/规划配置、状态预算或超时，不做自动重试。外层上限 210 秒、工具上限 180 秒，实际无超时。Plan→Execute / 关节反馈通过，MoveIt 仍 -11；单次成功只支持就绪时序假设，不证明固定等待可靠或缺陷已修复。
6. 两轮均无升级终止、move_group -11、control 进程 0；诊断结束检查发现域 131 ROS CLI daemon，守卫拒绝直接清理完成。保留首次进程快照，按该域停止 daemon，再核对仅剩 keeper，停止补跑容器。两个容器均停止、无 OOM、2 CPU/4 GiB/512 PID、无网络/设备/挂载/端口，cap-drop ALL/no-new-privileges。
7. 旧 Python 本次早 Goal 为 220、延迟 INIT 为 510、Cancel 受理后为 520 且完成 0；PickPlace create_client 与 Safety 清理失败保留。FSM/Action/Cancel/停稳内核记录回交孙嘉明。规划默认 TF/预算交常建烁，系统集成跟踪内部客户端就绪和退出；未代发外部消息或修复内核。
8. 没有新入口或运行代码，故不重复前次默认规划 SOP、C++ 独立四场景、UBSan/外部 consumer。前次默认 V1 42.0717 秒超过 24 秒、V2 TF_UNAVAILABLE 仍为历史未解除问题。新场景 30e3c6e、视觉 0e329f1 分支尚不在此快照，不将其新功能/测试记到此主线。
9. 冻结全部原失败、诊断、清理及 ACK/pre-complete 数据，index 不含自身；源 bundle/镜像/SDK/构建二进制不入库，版本与哈希留存。同步 manifest、正文、README、open-questions 与 derived_files 后才 complete；最终回执存 raw，不回写冻结集。原 60 秒轮询、固定主会话与上海 08:00 截止不变。

本轮仅独立 Jazzy Mock/Fake 软件验收，未推进正式 1d940f7 基线；完整 FSM、实际感知/工具/碰撞场景与 NUC/实机未验收。源声明 MIT/Apache-2.0 差异和 SDK 许可/厂商校验值保留。OpenAI Codex 协助只读源/测试身份核验、一次等待诊断、清理和事实登记；没有上游规划、FSM、Action 或驱动算法修改。
''')
files=[{'path':str(p.relative_to(base)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(base.rglob('*')) if p.is_file()]
write(base/'index.json',{'schema_version':1,'observation':obs,'created_at':now,'files':files})
print(json.dumps({'files':len(files),'bytes':sum(f['size_bytes'] for f in files),'index_sha256':sha(base/'index.json'),'queue_to_ack_seconds':summary['main_receipt']['queue_to_ack_seconds']},indent=2))
