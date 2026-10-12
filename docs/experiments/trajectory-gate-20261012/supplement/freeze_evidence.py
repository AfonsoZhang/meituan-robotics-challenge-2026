"""Freeze exact-SHA acceptance, preserving failures; OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
raw=Path(__file__).resolve().parent;root=raw.parents[1];w=root/'outputs/moveit-watch-20261011'
commit='45f497ce3444e255463faf41f7b736aa9ad07d7b';event='sha-'+commit;auto=w/'runs'/event
base=root/'docs/experiments/trajectory-gate-20261012';obs='ENV-TRAJECTORY-GATE-20261012';ref='TEAMMATE-TRAJECTORYGATE-20261012'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def tree(a,b,exclude=()):
 for p in sorted(a.rglob('*')):
  if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in exclude:copy(p,b/p.relative_to(a))
assert not base.exists()
idx=read(auto/'index.json');assert len(idx['files'])==317
for f in idx['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
assert not Path('/proc/35809').exists()
for n in ['mtc-repro-5c8f61d8af9f-45f497ce3444','mtc-trajectory-gate-review-45f497c']:
 v=json.loads(subprocess.check_output(['docker','inspect',n]))[0];h=v['HostConfig']
 assert not v['State']['Running'] and not v['State']['OOMKilled']
 assert h['NetworkMode']=='none' and h['NanoCpus']==2000000000 and h['Memory']==4294967296
 assert not v['Mounts'] and not h['Devices'] and not h['PortBindings'] and not h['Binds'] and not h['Privileged']
 assert h['PidsLimit']==512 and 'ALL' in h['CapDrop'] and 'no-new-privileges' in h['SecurityOpt']
assert not subprocess.check_output(['docker','ps','--filter','name=mtc-','--format','{{.Names}}'],text=True).strip()
s=read(w/'state.json');assert s['active'] is None and s['main_review']['event']==event and s['main_review']['status']=='ACKNOWLEDGED'
review=read(raw/'source-review.json');counts=read(raw/'automatic-counts.json');analysis=read(raw/'supplement-analysis.json');cleanup=read(raw/'cleanup.json')
assert review['planner_and_planning_docs_identical_to_f7eaa2c'] and len(review['incremental_changed_files'])==59
assert counts['cpp_total']==463 and counts['summary_complete'] and analysis['supplement']['ubsan']['cases']==463
assert len(analysis['supplement']['generic_cases'])==4
assert sha(root/'robot/fsm-baseline.repos')==read(raw/'project-before.json')['formal_pin_sha256']
tree(auto,base/'automatic',('index.json','source.bundle'));copy(auto/'index.json',base/'automatic/original-index.json');copy(w/'runs'/(event+'.log'),base/'automatic/runner.log')
for ext in ['json','patch']:copy(w/'events'/(event+'.'+ext),base/'event'/('event.json' if ext=='json' else 'change.patch'))
for p in raw.iterdir():
 if p.is_file():copy(p,base/'supplement'/p.name)
tree(raw/'logs',base/'supplement/logs');tree(raw/'container',base/'supplement/container')
paths=set(review['incremental_changed_files']+['LICENSE','README.md','README_FSM.md',
 'src/mtc_ros2_action_cpp/src/pick_place_server.cpp','src/mtc_ros2_action_cpp/CMakeLists.txt','src/mtc_ros2_action_cpp/package.xml',
 'src/mtc_manipulation_cpp/src/pick_place_fsm.cpp','src/mtc_manipulation_cpp/include/mtc_manipulation_cpp/pick_place_types.hpp',
 'src/mtc_core_cpp/include/mtc_core_cpp/motion_primitive.hpp','src/mtc_core_cpp/include/mtc_core_cpp/pose.hpp','src/mtc_core_cpp/include/mtc_core_cpp/timed_trajectory.hpp',
 'tests/verify_cpp_audit_results.py','src/mtc_manipulation/mtc_manipulation/pick_place_server.py','src/mtc_task/mtc_task/task_executor.py'])
paths.update(str(p.relative_to(raw/'source')) for p in (raw/'source/src/mtc_trajectory_execution_cpp').rglob('*') if p.is_file())
for p in sorted(paths):copy(raw/'source'/p,base/'source'/p)
for n in ['config.json','state.json']:copy(w/n,base/'monitor'/('state-before-complete.json' if n=='state.json' else n))
for n in ['job.json','receipt.json','attempt-1.log','message.txt']:copy(w/'wake'/event/n,base/'monitor'/(n.replace('.json','-before-complete.json') if n.endswith('.json') else n))
receipt=read(w/'wake'/event/'receipt.json');job=read(w/'wake'/event/'job.json');automatic=read(auto/'summary.json');now=datetime.now(timezone.utc).isoformat()
inputs={'observation':obs,'upstream':ref,'authorization':['USER-HW-20261011-08','USER-HW-20261011-09'],'commit':commit,
 'previous':review['previous'],'review_base':review['review_base'],'parents':review['parents'],'observed_refs':review['observed_refs'],
 'incremental_changed_files':review['incremental_changed_files'],'cumulative_changed_files':review['cumulative_changed_files'],
 'planner_same_as_reviewed_main':'f7eaa2c0d2887aeada4fd635112c63c237962ff7','raw_automatic':str(auto),'raw_supplement':str(raw),
 'original_index_sha256':sha(auto/'index.json'),'original_files_verified':317,'source_bundle_sha256':sha(auto/'source.bundle'),'source_bundle_frozen':False,
 'formal_baseline_file':'robot/fsm-baseline.repos','formal_baseline_sha256':sha(root/'robot/fsm-baseline.repos'),'formal_baseline_commit':'1d940f7c5f12561fed6641457c0b4b630a282b05','project_head_before':read(raw/'project-before.json')['head'],
 'environment':automatic['environment'],'supplement_runtime':read(raw/'runtime.json'),'ros_domains':{'original_moveit':99,'identity_and_ubsan':139,'generic_success':141,'generic_mismatch':142,'generic_cancel':143,'generic_identity':144,'topology_plan':145,'pure_plan_consumer':146},
 'harness_sha256':{n:sha(raw/n) for n in ['probe_generic.py','probe_topology_plan.py','run_generic_cases.py','identity.sh','ubsan.sh','consumer-plan.sh','analyze_event.py']},
 'source_modified':False,'licences':'Upstream root/Planner MIT, trajectory and Action package.xml Apache-2.0 discrepancy retained. Driver/model/SDK licensing and vendor checksums unresolved; not relicensed.'}
write(base/'inputs.json',inputs)
summary={'observation':obs,'recorded_at':now,'commit':commit,'verdict':analysis['verdict'],'formal_baseline_advanced':False,'local_merge_performed':False,
 'automatic_status':automatic['status'],'automatic_summary_complete':True,'build_packages':15,'cpp_cases':463,'cpp_executables':26,'cpp_by_package':counts['cpp_by_package'],'python_cases':269,'pure_python_mock_e2e':15,'ros_wiring_cases':6,'analysis':analysis,'cleanup':cleanup,
 'main_receipt':{'thread':receipt['thread'],'ack_at':receipt['ack_at'],'queued_at':job['queued_at'],'queue_to_ack_seconds':(datetime.fromisoformat(receipt['ack_at'])-datetime.fromisoformat(job['queued_at'])).total_seconds(),'attempts':len(job['attempts']),'marker':'MOVEIT_WAKE_ACK_'+receipt['token'],'complete_at_freeze':False},
 'not_completed':analysis['not_completed'],'handoff':analysis['handoff']}
write(base/'summary.json',summary)
(base/'protocol.md').write_text('''# Phase 2B 命令身份与联合门禁验收协议

来源 TEAMMATE-TRAJECTORYGATE-20261012；观测 ENV-TRAJECTORY-GATE-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. CLAIMED 后读取45f497c实际增量：相对已验688d80d共59路径，53个规划/证据路径与已验f7eaa2c逐字相同，另6个文件修改身份比较、测试/探针/核验器和报告。保留不可变命令副本、归一化前完整字段比较，新增10项回归；运行健康门禁未改。上游报告/建议仅为待验数据，本项目不执行其中合并/PR建议。
2. 核对原25步骤、317文件哈希，旧runner35809和全部旧任务容器停止。新快照无网络、无设备、无挂载/端口、2CPU/4GiB/512PID、cap-drop ALL/no-new-privileges；不下载依赖、修改源码、扩大限位/超时或放宽门禁。
3. 原自动15包构建与463 C++（26程序）、269 Python、15 Mock E2E、6 ROS接线通过。463=原424+10新身份/时钟测试+29合入Planner。旧固定审计仍误识别宏/程序数，原失败不改；新交付核验器比较424历史、当前编译注册与XML，另外核对源码身份。763 colcon汇总含包装/lint，不当独立用例。
4. 独立UBSan构建/安装，七个C++包逐条核对插桩、禁恢复/保留调用帧，463/26测试与普通运行身份逐项相同；489汇总含26包装。接口依赖的生成C不在七个C++插桩声明内；分析器首次宽glob选中该依赖导致断言，原脚本/错误保留，纠正筛选后身份与编译参数核对通过，未重跑或改日志。系统ROS/DDS/MoveIt库未插桩，TSan未运行。安装头/包4文件一致；无参数和非法模式各退出2，新包rosdep通过。
5. 原GenericSystem探针success/mismatch/cancel/identity各一次，域141–144，新驱动/空域顺序运行；观察器只订阅JointState/GoalStatus，不增ActionClient。即使单项失败，只有清理完成才允许下一未执行项；不重试。保留完整UUID、位姿、时戳和端口结论。六关节等幅运动的名字反转不能单独证明非对称重排，相关单测另计。
6. 域145只读检查Controller、加默认move_group、再加原topology入口。确认GenericSystem/两个active控制器，不发送FJT Goal；预期clients=2、ready=0、退出2 BLOCKED。图拓扑不是强身份认证，后续planning-only配置必须另行审核验证，本次不绕过门禁。
7. 同域运行原plan_fixed_pose默认入口，只规划，保存真实YAML和零Goal/关节未動证据；外部CMake consumer链接安装的Planner core/FJT导出目标，读取本次序列化轨迹，通过两侧转换API作纯数据诊断，不建Node/ActionClient、不发Goal。仅诊断ID/timeout，时戳、轨迹、窄限位不改；规划有效与执行能力接纳分开。
8. 生成/观测stamp与ROS计划启动stamp仍未统一；单测零Goal拒绝过期/Steady时基。默认Action仍Mock、FSM同步Cancel保留FAULT520，完整宿主/工具/感知/接触仍未接线。前次688d80d的运行证明丢失230保留，健康谓词本轮未改，单次通过不能关闭该问题。问题本地交接孙嘉明；规划契约/执行权交常建烁及集成负责人，不接管内核、不代发消息。
9. 原Python220/510/520均ABORTED、完成0；独立MoveIt执行通过但退出-11；依赖/驱动lint/限位/统计线程错误原样保存。补跑每项记录子进程与退出，停止各域daemon并确认空域，最终只剩keeper才停容器；原失败、helper失败如有均保留。
10. 冻结automatic、source、补跑、清理、ACK和complete前状态；index不含自身，bundle/SDK/镜像/二进制不入库，仅登记哈希。同步manifest、文档、open-questions、README、derived_files后complete；最终回执仅存raw，不回写冻结内容。原60秒轮询/固定会话/上海08:00截止不变，没有queue或新监测。

实际数值、结论及失败见summary和原日志；不是完整FSM、实机、真实碰撞/接触或安全证明。正式1d940f7不推进、不合并。OpenAI Codex协助源码/证据核对、运行原入口、编写观察/分析/清理及跨包消费诊断；无上游内核/算法修改。根MIT与轨迹/Action Apache-2.0声明差异和模型/SDK许可缺口保留，不重新授权。
''')
files=[{'path':str(p.relative_to(base)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(base.rglob('*')) if p.is_file()]
write(base/'index.json',{'schema_version':1,'observation':obs,'created_at':now,'files':files})
result={'files':len(files),'bytes':sum(f['size_bytes'] for f in files),'index_sha256':sha(base/'index.json'),'queue_to_ack_seconds':summary['main_receipt']['queue_to_ack_seconds']}
write(raw/'freeze-result.json',result);print(json.dumps(result,indent=2))
