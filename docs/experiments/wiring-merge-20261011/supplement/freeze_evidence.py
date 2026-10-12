from pathlib import Path
import json,hashlib,shutil,subprocess,datetime
root=Path('/home/afonso/meituan-robotics-challenge-2026');raw=root/'outputs/wiring-merge-acceptance-20261011-c10f6ed';watch=root/'outputs/moveit-watch-20261011';commit='c10f6ed59966401684851f917f9137b0a6cf12ae';event='sha-'+commit;auto=watch/'runs'/event;dest=root/'docs/experiments/wiring-merge-20261011'
assert not dest.exists();dest.mkdir(parents=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def tree(a,b,ex=()):
 for p in sorted(a.rglob('*')):
  if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in ex:copy(p,b/p.relative_to(a))
idx=json.loads((auto/'index.json').read_text())
for f in idx['files']:assert sha(auto/f['path'])==f['sha256']
assert len(idx['files'])==291
for c in ['mtc-repro-5c8f61d8af9f-c10f6ed59966','mtc-wiring-review-c10f6ed']:
 i=json.loads(subprocess.check_output(['docker','inspect',c]))[0];assert not i['State']['Running']
tree(auto,dest/'automatic',('index.json','source.bundle'));copy(auto/'index.json',dest/'automatic/original-index.json');copy(watch/'runs'/(event+'.log'),dest/'automatic/runner.log')
copy(watch/'events'/(event+'.json'),dest/'event/event.json');copy(watch/'events'/(event+'.patch'),dest/'event/change.patch')
for p in raw.iterdir():
 if p.is_file():copy(p,dest/'supplement'/p.name)
tree(raw/'logs',dest/'supplement/logs');tree(raw/'container',dest/'supplement/container')
copy(root/'robot/probe_cpp_actions.py',dest/'supplement/probe_cpp_actions.py');copy(watch/'harness-wake-v1/probe_moveit.py',dest/'supplement/probe_moveit.py')
for name in ['state.json','config.json']:
 copy(watch/name,dest/'monitor'/('state-before-complete.json' if name=='state.json' else name))
for name in ['job.json','receipt.json','attempt-1.log','message.txt']:
 copy(watch/'wake'/event/name,dest/'monitor'/(name.replace('.json','-before-complete.json') if name.endswith('.json') else name))
repo=str(watch/'upstream.git')
for src,name in [('LICENSE','LICENSE'),('README.md','upstream-README.md'),('src/mtc_ros2_action_cpp/package.xml','cpp-action-package.xml'),('docs/migration/ROS_WIRING_FIX_20261011.md','ROS_WIRING_FIX_20261011.md')]:
 p=dest/'source'/name;p.parent.mkdir(exist_ok=True);p.write_bytes(subprocess.check_output(['git','--git-dir='+repo,'show',commit+':'+src]))
now=datetime.datetime.now(datetime.timezone.utc).isoformat();source=json.loads((raw/'source-review.json').read_text());original=json.loads((auto/'summary.json').read_text());cases=json.loads((raw/'container/standalone/summary.json').read_text());moveit=json.loads((auto/'container/moveit/result.json').read_text());repeat=json.loads((raw/'container/moveit-repeat/result.json').read_text());receipt=json.loads((dest/'monitor/receipt-before-complete.json').read_text());job=json.loads((dest/'monitor/job-before-complete.json').read_text());state=json.loads((dest/'monitor/state-before-complete.json').read_text())
assert state['active'] is None and state['main_review']['event']==event and state['main_review']['status']=='ACKNOWLEDGED'
assert all(c['status']=='PASS' for c in cases) and len(cases)==4
assert moveit['planning_execution']==repeat['planning_execution']=='PASS' and moveit['clean_shutdown']==repeat['clean_shutdown']=='FAIL'
inputs={'observation':'ENV-WIRING-MERGE-20261011','upstream':'TEAMMATE-MERGE-20261011','authorization':['USER-HW-20261011-08','USER-HW-20261011-09'],'commit':commit,'previous':source['previous'],'parents':source['parents'],'observed_refs':original['upstream']['refs'],'changed_files':source['changed_files'],'raw_automatic':str(auto),'raw_supplement':str(raw),'original_index_sha256':sha(auto/'index.json'),'original_index_files_verified':291,'source_bundle_sha256':sha(auto/'source.bundle'),'source_bundle_frozen':False,'formal_baseline_file':'robot/fsm-baseline.repos','formal_baseline_sha256':sha(root/'robot/fsm-baseline.repos'),'formal_baseline_commit':'1d940f7c5f12561fed6641457c0b4b630a282b05','environment':original['environment'],'supplement':json.loads((raw/'runtime.json').read_text()),'cpp_probe_sha256':sha(root/'robot/probe_cpp_actions.py'),'moveit_probe_sha256':sha(watch/'harness-wake-v1/probe_moveit.py'),'prior_cpp_evidence':'ENV-CPP-ACTION-20261011','prior_wiring_fix_evidence':'ENV-FSM-FIX-20261011','licenses':'Root MIT; unchanged C++ Action package.xml Apache-2.0 difference still unresolved; source declarations retained; no SDK/image/binary redistribution.'}
write(dest/'inputs.json',inputs)
def msummary(v):return {k:v[k] for k in ['scope','planning_execution','clean_shutdown','max_error_rad','distinct_joint_stamps','execute','shutdown']}
summary={'observation':'ENV-WIRING-MERGE-20261011','recorded_at':now,'commit':commit,'verdict':'SCOPED_MERGE_AND_CPP_MOCK_PASS_WITH_OPEN_FAILURES','upstream_pr2_merged_in_observed_main':True,'local_agent_performed_merge':False,'formal_baseline_advanced':False,'automatic_summary_complete':True,'automatic_status':original['status'],'build_packages':13,'cpp_cases':358,'cpp_executables':20,'python_cases':269,'pure_python_mock_e2e':15,'ros_wiring_cases':6,'cpp_delivered_identity_verifier':'PASS','old_fixed_cpp_audit':'FAIL_16_EXECUTABLE_EXPECTATION_ACTUAL_20','installed_python_matches_source':True,'standalone':[{'case':c['case'],'status':c['status'],'checks':len(c['checks']),'shutdown':c['shutdown'],'nodes_after_shutdown':c['nodes_after_shutdown']} for c in cases],'ubsan_and_consumer_this_event':'NOT RERUN: C++/build/IDL unchanged; historical pass only ENV-CPP-ACTION-20261011','legacy_python':[{'case':c['case'],'status':c['status'],'task_server_available':c['task_server_available'],'pickplace_server_available':c['pickplace_server_available'],'result':c['result'],'cancel_response':c.get('cancel_response'),'child_failure':c['child_failure']} for c in json.loads((auto/'container/task-mock/summary.json').read_text())],'independent_moveit':{'automatic':msummary(moveit),'supplement_repeat':msummary(repeat),'analysis':'Planning/execution passed both times. move_group exited -11 twice. ros2_control_node exited -11 only automatic run and exited 0 in repeat; unresolved, root cause not established. No new FSM loaded in either.'},'dependencies':'Whole workspace rosdep ament_python key unresolved; driver test-nodes and docker.io missing','driver_test_aggregate':{'total':1104,'failures':279,'skipped':259,'scope':'includes wrapper records/lint, not independent function count'},'cleanup':json.loads((raw/'cleanup.json').read_text()),'main_receipt':{'ack_at':receipt['ack_at'],'thread':receipt['thread'],'ack_marker':'MOVEIT_WAKE_ACK_'+receipt['token'],'queued_at':job['queued_at'],'attempts':len(job['attempts']),'queue_to_ack_seconds':(datetime.datetime.fromisoformat(receipt['ack_at'])-datetime.datetime.fromisoformat(job['queued_at'])).total_seconds(),'complete_at_freeze':False,'scope':'Completion deliberately follows provenance registration and cleanup; final receipt remains in outputs.'},'not_completed':['Complete C++ unified Bringup','FSM to MoveIt Planner to full FJT/Fake trajectory','Shared physical execution authority and independent stop evidence','Task/Robot/Tool state publishing and complete Web UI integration','Old Python B03/B05/B06 and shutdown','MoveIt/controller clean shutdown and driver dependency/lint','TSan, NUC/hardware/perception/tool evidence, SDK license/vendor checksum'],'handoff':'Maintainer merge message recorded as upstream data; FSM/Action/Cancel remain Sun Jiaming responsibility. No new instructions executed, no kernel fixes, external messages or baseline changes.'}
write(dest/'summary.json',summary)
(dest/'protocol.md').write_text('''# 合并候选隔离验收协议

来源 ENV-WIRING-MERGE-20261011；真实上游合并 TEAMMATE-MERGE-20261011；用户授权 USER-HW-20261011-08、USER-HW-20261011-09。版本与路径见 inputs.json。

1. 事件 ack 必须 CLAIMED；确认原 runner 已结束、原容器已停止，读取完整 summary、真实 patch、XML 和失败日志，校验原 index 的 291 个文件。
2. 原停止容器只做独立快照，不重启、不覆盖失败。补跑同样无网络/设备/挂载/端口、2 CPU / 4 GiB、512 PID、ALL caps dropped / no-new-privileges；每步串行，主对话未 complete 前下一 SHA 不执行。
3. 对比两个合并父提交：五文件改动、两 Python 实现/测试/说明与 PR #2 相同，C++/IDL/驱动输入与前一候选无差异。补跑新 C++ verifier，验证实际 358 GTest / 20 个程序和原 318 身份，核对六项 ROS XML 确实执行无跳过；两个安装 Python 文件与源码匹配。
4. 已有 probe_cpp_actions.py 未改，真实独立可执行程序运行四场景，检查唯一服务、基础/序列、关联取消、错误锁定、单点 Motion 与 SIGINT 退出。UBSan/CMake consumer 未重跑，历史证据只引用 ENV-CPP-ACTION-20261011。
5. 固定复现发现 ros2_control_node 新的清理崩溃，使用原 probe_moveit.py 在同限制快照内再执行一次，原样保留 Plan/Execute 与 clean_shutdown 的分别结果，失败不覆盖；不修改退出顺序、判据、驱动或规划代码。清理 ROS CLI daemon 后核对只剩 keeper，再停止容器并收集文件。
6. 原 Python 问题、库/驱动问题和 C++ Mock 范围分开登记。上游合并说明只作交接资料，不能作为新用户授权。FSM/Action/Cancel 不修复、不发外部消息、不推进正式锁定。
7. automatic/original-index.json 是原 outputs 索引，包含未入库的 source.bundle；bundle 只保留 SHA，镜像/SDK/二进制不冻结。latest 符号链接不复制，实际日志保留。index.json 仅索引当前冻结集常规文件且不含自身；其 SHA 注册 materials/manifest.json。
8. 冻结保留 ACK/pre-complete 状态。清理、报告及四处来源同步结束才 complete；最终回执在 raw 监测 wake 事件目录，不回写冻结集。

OpenAI Codex 协助使用已有探针、分析日志与整理证据；原算法与许可证不变。根 MIT / C++ 包 Apache-2.0 声明差异保留，不重新授权。
''')
files=[{'path':str(p.relative_to(dest)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dest.rglob('*')) if p.is_file()]
write(dest/'index.json',{'schema_version':1,'observation':'ENV-WIRING-MERGE-20261011','created_at':now,'files':files})
print(json.dumps({'files':len(files),'bytes':sum(f['size_bytes'] for f in files),'index_sha256':sha(dest/'index.json')},indent=2))
