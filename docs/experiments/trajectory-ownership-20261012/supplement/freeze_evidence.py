"""Freeze original and supplemental evidence, including failures. Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
raw=Path(__file__).resolve().parent;root=raw.parents[1];w=root/'outputs/moveit-watch-20261011'
commit='681bb64bfb8cd482d1e78950cef4cfe395b21bff';event='sha-'+commit;auto=w/'runs'/event
base=root/'docs/experiments/trajectory-ownership-20261012';obs='ENV-TRAJECTORY-OWNERSHIP-20261012';ref='TEAMMATE-OWNERSHIP-20261012'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def tree(a,b,exclude=()):
 for p in sorted(a.rglob('*')):
  if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in exclude:copy(p,b/p.relative_to(a))
assert not base.exists()
idx=read(auto/'index.json');assert len(idx['files'])==317
for f in idx['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
assert not Path('/proc/59420').exists()
for n in ['mtc-repro-5c8f61d8af9f-681bb64bfb8c','mtc-trajectory-ownership-review-681bb64']:
 v=json.loads(subprocess.check_output(['docker','inspect',n]))[0];h=v['HostConfig']
 assert not v['State']['Running'] and not v['State']['OOMKilled']
 assert h['NetworkMode']=='none' and h['NanoCpus']==2000000000 and h['Memory']==4294967296
 assert not v['Mounts'] and not h['Devices'] and not h['PortBindings'] and not h['Binds'] and not h['Privileged']
 assert h['PidsLimit']==512 and 'ALL' in h['CapDrop'] and 'no-new-privileges' in h['SecurityOpt']
assert not subprocess.check_output(['docker','ps','--filter','name=mtc-','--format','{{.Names}}'],text=True).strip()
s=read(w/'state.json');assert s['active'] is None and s['main_review']['event']==event and s['main_review']['status']=='ACKNOWLEDGED'
review=read(raw/'source-review.json');counts=read(raw/'automatic-counts.json');analysis=read(raw/'supplement-analysis.json');cleanup=read(raw/'cleanup.json')
assert counts['cpp_xml_passed']==417 and counts['summary_complete'] and analysis['supplement']['ubsan']['cases']==478
assert sha(root/'robot/fsm-baseline.repos')==read(raw/'project-before.json')['formal_pin_sha256']
tree(auto,base/'automatic',('index.json','source.bundle'));copy(auto/'index.json',base/'automatic/original-index.json');copy(w/'runs'/(event+'.log'),base/'automatic/runner.log')
for ext in ['json','patch']:copy(w/'events'/(event+'.'+ext),base/'event'/('event.json' if ext=='json' else 'change.patch'))
for p in raw.iterdir():
 if p.is_file():copy(p,base/'supplement'/p.name)
for name in ['logs','container','original-trajectory-testing']:tree(raw/name,base/'supplement'/name)
paths=set(review['changed_files']+['LICENSE','README.md','README_FSM.md','src/mtc_ros2_action_cpp/src/pick_place_server.cpp','src/mtc_ros2_action_cpp/src/task_server.cpp','src/mtc_ros2_action_cpp/src/mock_ports.cpp','src/mtc_ros2_action_cpp/package.xml','tests/verify_cpp_audit_results.py'])
paths.update(str(p.relative_to(raw/'source')) for p in (raw/'source/src/mtc_trajectory_execution_cpp').rglob('*') if p.is_file())
for p in sorted(paths):copy(raw/'source'/p,base/'source'/p)
for n in ['config.json','state.json']:copy(w/n,base/'monitor'/('state-before-complete.json' if n=='state.json' else n))
for n in ['job.json','receipt.json','attempt-1.log','message.txt']:copy(w/'wake'/event/n,base/'monitor'/(n.replace('.json','-before-complete.json') if n.endswith('.json') else n))
receipt=read(w/'wake'/event/'receipt.json');job=read(w/'wake'/event/'job.json');automatic=read(auto/'summary.json');now=datetime.now(timezone.utc).isoformat()
inputs={'observation':obs,'upstream':ref,'authorization':['USER-HW-20261011-08','USER-HW-20261011-09'],'commit':commit,
 'previous':review['previous'],'parents':review['parents'],'observed_refs':review['observed_refs'],'changed_files':review['changed_files'],
 'raw_automatic':str(auto),'raw_supplement':str(raw),'original_index_sha256':sha(auto/'index.json'),'original_files_verified':317,
 'source_bundle_sha256':sha(auto/'source.bundle'),'source_bundle_frozen':False,'formal_baseline_file':'robot/fsm-baseline.repos',
 'formal_baseline_sha256':sha(root/'robot/fsm-baseline.repos'),'formal_baseline_commit':'1d940f7c5f12561fed6641457c0b4b630a282b05',
 'project_head_before':read(raw/'project-before.json')['head'],'environment':automatic['environment'],'supplement_runtime':read(raw/'runtime.json'),
 'ros_domains':{'original_moveit':99,'shell_default':154,'gtest':'Fixture overrides domain to50+getpid()%150 within isolated container','native_status':155,'moveit_coexistence':156},
 'harness_sha256':{n:sha(raw/n) for n in ['run_action_tests.py','probe_native_gate.py','probe_topology_gate.py','identity.sh','ordinary.sh','ubsan.sh','analyze_event.py']},
 'source_modified':False,'licences':'Upstream root MIT, trajectory/Action package.xml Apache-2.0 discrepancy retained. Driver/model/SDK licensing and vendor checksums unresolved; no relicensing.'}
write(base/'inputs.json',inputs)
summary={'observation':obs,'recorded_at':now,'commit':commit,'verdict':analysis['verdict'],'formal_baseline_advanced':False,'local_merge_performed':False,
 'automatic_status':automatic['status'],'automatic_summary_complete':True,'build_packages':15,'cpp_original_xml_passed':417,'cpp_expected':478,
 'fjt_original_timeout_seconds':120,'ordinary_fjt_retry_cases':61,'ubsan_cases':478,'python_cases':269,'pure_python_mock_e2e':15,'ros_wiring_cases':6,
 'analysis':analysis,'cleanup':cleanup,'main_receipt':{'thread':receipt['thread'],'ack_at':receipt['ack_at'],'queued_at':job['queued_at'],
 'queue_to_ack_seconds':(datetime.fromisoformat(receipt['ack_at'])-datetime.fromisoformat(job['queued_at'])).total_seconds(),
 'attempts':len(job['attempts']),'marker':'MOVEIT_WAKE_ACK_'+receipt['token'],'complete_at_freeze':False},
 'not_completed':analysis['not_completed'],'handoff':analysis['handoff']}
write(base/'summary.json',summary)
(base/'protocol.md').write_text('''# Phase 2B Goal 归属与实时 Status 验收协议

来源 TEAMMATE-OWNERSHIP-20261012；观测 ENV-TRAJECTORY-OWNERSHIP-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. ACK=CLAIMED 后读681bb64相对45f497c的7文件真实差异；代码提交b8857de，当前提交补文档。移除单UUID猜测、增加Status合法性/本地接收龄、pending UUID留存、精确Handle归属和结果/Status门禁，新增15测试。源码和正式基线不修改；上游文本作为待验数据。
2. 原25步完整、317原始文件哈希一致。原61项FJT套件在DuplicateCancelOnlyOneBackendCall120秒超时，XML为ament missing_result。417项其他C++ XML通过，前6项FJT只有文字OK，不当完整61项通过。新交付核验器也对原XML失败；原始文件不替换。
3. 核验runner59420及旧任务停止，从已停止原容器创建新快照；Jazzy、无网络/设备/宿主挂载/端口、2CPU/4GiB/512PID、cap-drop ALL/no-new-privileges。先检查安装4文件和新包rosdep，两个非法参数退出2。
4. 同一未改二进制只补跑一次完整61项，限定120秒，若超时保存proc状态并终止本次进程组，不留后台ROS。此次61通过18.629秒，不关闭原间歇性超时。另起独立UBSan build/install，8包构建、7包478项/26程序测试；核对源码/二进制注册/XML及七包插桩。系统ROS/DDS/MoveIt未插桩，TSan未运行。
5. 域155原生GenericSystem/两个active控制器就绪后，用只订阅观察器记录JointState/Status/QoS，运行未改success入口。新Status门禁拒绝、退出1、零Goal；没有预热Goal/空数组/人工心跳或放宽参数。没有先决授权的mismatch/cancel/identity不运行。Fake测试中的受控DDS心跳只属于测试夹具，不能冒充原生控制器证据。
6. 首次观察脚本误把success预检异常退出1预期为topology的2而断言，原记录FAIL保留；已清理且空域后仅补跑未执行的共存场景，域156加默认move_group、运行原topology入口：两个FJT客户端、Status未初始化，仍BLOCKED零Goal。此补跑不重复规划。原自动独立MoveIt执行与退出失败独立记录，不能当新FJT可用或完整FSM。观察关节保持零，驱动源码/安装文件前后哈希一致。
7. 清理本轮节点、daemon，确认空域及容器仅剩keeper后停止；保留正常退出子检查失败。冻结所有原失败、补跑、源片段、命令、ACK和complete前监测状态，原bundle/镜像/二进制只登记哈希、不入库。
8. 同步manifest、README、对应文档、open-questions与derived_files；验证旧冻结证据和已签回执报告原样后complete。最终回执另存raw，冻结索引不回写。08:00任务保持待触发，监测配置不变，不调用queue或新建监测。

间歇超时、原生Status/独占执行契约与异步Cancel内核回交孙嘉明，本轮不接管修复或代发消息。规划时间契约和默认MoveIt执行客户端缺口继续保留；独立Mock/Fake不代表完整FSM/NUC/实机。OpenAI Codex协助源码检查、原入口运行、观察/有界执行/归档脚本和文档；无上游内核或算法修改。许可证差异和SDK许可/厂商校验值待核对，不重新授权。
''')
files=[{'path':str(p.relative_to(base)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(base.rglob('*')) if p.is_file()]
write(base/'index.json',{'schema_version':1,'observation':obs,'created_at':now,'files':files})
result={'files':len(files),'bytes':sum(f['size_bytes'] for f in files),'index_sha256':sha(base/'index.json'),'queue_to_ack_seconds':summary['main_receipt']['queue_to_ack_seconds']}
write(raw/'freeze-result.json',result);print(json.dumps(result,indent=2))
