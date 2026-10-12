from pathlib import Path
import json,hashlib,shutil,subprocess,datetime,xml.etree.ElementTree as ET
ROOT=Path('/home/afonso/meituan-robotics-challenge-2026')
raw=ROOT/'outputs/phase2a-acceptance-20261011-c0f7017'
watch=ROOT/'outputs/moveit-watch-20261011'
event='sha-c0f70172e4b0271046d5f52813e0730d40ae772a'
auto=watch/'runs'/event
frozen=ROOT/'docs/experiments/cpp-action-20261011'
assert not frozen.exists(), 'Do not overwrite a frozen experiment'
frozen.mkdir(parents=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def copytree(a,b,exclude=()):
 for p in sorted(a.rglob('*')):
  if p.is_file() and not p.is_symlink() and p.relative_to(a).as_posix() not in exclude:
   copy(p,b/p.relative_to(a))
orig=json.loads((auto/'index.json').read_text())
for f in orig['files']:
 p=auto/f['path'];assert sha(p)==f['sha256'],str(p)
copytree(auto,frozen/'automatic',exclude=('source.bundle','index.json'))
copy(auto/'index.json',frozen/'automatic/original-index.json')
copy(watch/'runs'/(event+'.log'),frozen/'automatic/runner.log')
copy(watch/'events'/(event+'.json'),frozen/'event/event.json')
copy(watch/'events'/(event+'.patch'),frozen/'event/change.patch')
# Preserve raw supplemental failures, logs, exact commands, and all collected test artifacts.
for p in sorted(raw.iterdir()):
 if p.is_file() and p.name!='freeze_evidence.py': copy(p,frozen/'supplement'/p.name)
copytree(raw/'logs',frozen/'supplement/logs')
copytree(raw/'container',frozen/'supplement/container')
copy(ROOT/'robot/probe_cpp_actions.py',frozen/'supplement/probe_cpp_actions.py')
copy(raw/'freeze_evidence.py',frozen/'freeze_evidence.py')
for src,dest in [('LICENSE','LICENSE'),('README.md','upstream-README.md'),('docs/migration/PHASE2A_ROS2_ACTION_REPORT.md','PHASE2A_ROS2_ACTION_REPORT.md'),('src/mtc_ros2_action_cpp/README.md','package-README.md'),('src/mtc_ros2_action_cpp/package.xml','package.xml'),('src/mtc_ros2_action_cpp/test/verify_results.py','verify_results.py')]:
 copy(raw/'source'/src,frozen/'source'/dest)
for src,dest in [('config.json','config.json'),('state.json','state-before-complete.json'),('wake/'+event+'/receipt.json','receipt-before-complete.json'),('wake/'+event+'/job.json','job-before-complete.json'),('wake/'+event+'/attempt-1.log','attempt-1.log'),('wake/'+event+'/message.txt','message.txt')]:
 copy(watch/src,frozen/'monitor'/dest)
recorded=datetime.datetime.now(datetime.timezone.utc).isoformat()
state=json.loads((frozen/'monitor/state-before-complete.json').read_text())
assert state['main_review']['event']==event and state['main_review']['status']=='ACKNOWLEDGED' and state['active'] is None
job=json.loads((frozen/'monitor/job-before-complete.json').read_text())
receipt=json.loads((frozen/'monitor/receipt-before-complete.json').read_text())
latency=(datetime.datetime.fromisoformat(receipt['ack_at'])-datetime.datetime.fromisoformat(job['queued_at'])).total_seconds()
evt=json.loads((frozen/'event/event.json').read_text())
inputs={'observation':'ENV-CPP-ACTION-20261011','upstream_source':'TEAMMATE-ACTION-20261011','authorization':['USER-HW-20261011-08','USER-HW-20261011-09'],'commit':evt['commit'],'previous':evt['previous'],'refs':evt['refs'],'changed_paths':evt['paths'],'changed_path_count':len(evt['paths']),'reviewed_file_sha256':{name:sha(raw/'source'/name) for name in evt['paths']},'source_bundle_sha256':sha(auto/'source.bundle'),'source_bundle_frozen':False,'formal_baseline_file':'robot/fsm-baseline.repos','formal_baseline_sha256':sha(ROOT/'robot/fsm-baseline.repos'),'formal_baseline_commit':'1d940f7c5f12561fed6641457c0b4b630a282b05','baseline_advanced':False,'original_run_index_sha256':sha(auto/'index.json'),'automatic_original_files_verified':len(orig['files']),'raw_automatic_directory':str(auto),'raw_supplement_directory':str(raw),'environment':json.loads((auto/'summary.json').read_text())['environment'],'supplement':json.loads((raw/'runtime.json').read_text()),'probe_sha256':sha(ROOT/'robot/probe_cpp_actions.py'),'source_license':'Repository LICENSE MIT; new package.xml Apache-2.0. Difference retained for maintainer clarification.','algorithm_provenance':'OpenAI Codex assisted orchestration and standard ROS Action assertions; no FSM, planning, driver, or cancellation kernel edits. Full change patch and upstream license declarations retained as evidence; no SDK, image, build products or Git bundle in frozen set.'}
write(frozen/'inputs.json',inputs)
standalone=json.loads((raw/'container/standalone-v2/summary.json').read_text())
assert len(standalone)==4 and all(c['status']=='PASS' and all(x['passed'] for x in c['checks']) for c in standalone)
ubsanfiles=list((raw/'container/ubsan').rglob('*.gtest.xml'))
ubsancount=sum(len(ET.parse(p).getroot().findall('.//testcase')) for p in ubsanfiles)
assert (len(ubsanfiles),ubsancount)==(20,358)
for label in ('identity','ubsan','consumer','standalone-v2'):
 assert json.loads((raw/'logs'/(label+'.json')).read_text())['exit_code']==0
summary={'observation':'ENV-CPP-ACTION-20261011','recorded_at':recorded,'verdict':'PASS_PHASE2A_MOCK_WITH_OPEN_INTEGRATION_FAILURES','commit':evt['commit'],'formal_baseline_unchanged':True,'automatic_summary_complete':True,'automatic_original_status':'COMPLETED_WITH_FAILURES','normal':{'packages_built':13,'cpp_gtest_cases':358,'cpp_executables':20,'retained_cpp_cases':318,'new_cpp_cases':40,'cpp_failed':0,'cpp_skipped':0,'python_cases':269,'explicit_pure_python_mock_e2e':15,'optional_ros_wiring_regressions':'NOT_RUN_FILE_ABSENT','old_cpp_audit':'FAIL_FIXED_16_EXECUTABLE_EXPECTATION','delivered_identity_verifier':'PASS'},'supplement':{'new_package_dependencies':'PASS','new_package_xml_schema':'PASS','ubsan_cases':ubsancount,'ubsan_scope':'five project C++ packages instrumented; ROS/DDS system libraries not instrumented','exported_cmake_consumer':'PASS','standalone_scenarios':[{'name':c['case'],'status':c['status'],'checks':len(c['checks']),'goals':len(c['goals']),'servers':c['servers'],'shutdown':c['shutdown'],'nodes_after_shutdown':c['nodes_after_shutdown']} for c in standalone],'standalone_checks':sum(len(c['checks']) for c in standalone),'development_failures_preserved':['standalone-v1 NumPy UUID serialization TypeError; no complete verdict','preparation runtime.json not yet ready; no test started']},'existing_paths':{'legacy_python_mock':'FAIL_B01_B02_STARTUP_NO_GOALS','whole_workspace_rosdep':'FAIL_ament_python_key','driver_rosdep':'FAIL_missing_ros-jazzy-ros2-controllers-test-nodes_and_docker.io','driver_test_aggregate':{'tests':1104,'failures':279,'skipped':259,'scope':'includes wrappers and lint, not independent functionality count'},'independent_moveit':{'planning_execution':'PASS','action_status':4,'moveit_code':1,'joint_target_increment_rad':0.05,'maximum_target_error_rad':9.746883334591985e-05,'distinct_joint_timestamps':212,'clean_shutdown':'FAIL_move_group_-11','integration_with_new_cpp_actions':False}},'cleanup':json.loads((raw/'cleanup.json').read_text()),'monitor_receipt':{'event':event,'thread':receipt['thread'],'ack_at':receipt['ack_at'],'ack_marker':'MOVEIT_WAKE_ACK_'+receipt['token'],'attempts':len(job['attempts']),'queued_at':job['queued_at'],'queued_to_ack_seconds':latency,'state_at_snapshot':state['status'],'gate_at_snapshot':'ACKNOWLEDGED; complete deliberately deferred until cleanup and provenance registration','monitor_pid':state['pid'],'last_successful_poll':state['last_successful_poll']},'not_verified':['Phase 2B MoveIt Planner and complete trajectory execution','Single shared physical motion authority','Public independent PickPlace stop evidence','Task/Robot/Tool state publishers and real Web UI integration','TSan','NUC and physical robot/camera/tool','SDK license/vendor checksum and controller compatibility','Physical perception, placement, tool and collision evidence','Jazzy Gazebo migration'],'handoff':'FSM/Action/Cancel/Motion Execution issues and Phase 2B delivery remain Sun Jiaming responsibility; local report only, no external messages or kernel fixes.'}
write(frozen/'summary.json',summary)
(frozen/'protocol.md').write_text('''# Phase 2A C++ Action 候选复验协议

来源：ENV-CPP-ACTION-20261011；候选 TEAMMATE-ACTION-20261011，固定 SHA 见 inputs.json。USER-HW-20261011-08、USER-HW-20261011-09 授权隔离集成复验；原监测配置沿用 ENV-UPSTREAM-WAKE-20261011。

1. 本事件 ack 必须返回 CLAIMED；确认原 runner 已结束、原容器停止、summary 有结束/采集信息。读取真实 patch 和逐步日志，不能仅据固定 summary 作功能判定。
2. 校验原 index 的 290 个文件，保留原样；原 container 只用于创建独立 snapshot，不重新启动。新的补跑容器保持 network none、无设备/挂载/端口、2 CPU / 4 GiB、512 PID、ALL caps dropped、no-new-privileges。
3. 复用自动构建的正常候选。按新交付入口核验测试身份、新包 rosdep/XML；另在独立目录编译五个 C++ 包及接口的 UBSan 版本并测试，核对实际编译选项；外部 CMake consumer 验证导出接口。所有命令、开始/结束时间及退出码见 supplement/logs/，自动工具原命令见 automatic/summary.json。
4. 独立程序四场景使用 ROS domain 110–113 和本机发现；逐节点确认唯一 Action Server、发送关联 Goal/Cancel、保存实际 Feedback/Result。延迟 7 秒首任务、基础/保序三色、拒绝非法/并发/重复 ID、关联取消、缺失子服务器失败锁定、单点 Motion 及退出均为必查项。ROS 进程正常 SIGINT 退出且无残留节点才计场景通过。Mock 运动/稳定窗使用模拟时间，不作为物理证明。
5. 补跑不改上游源代码；原 verifier 的 16 目标限制不适用于新增包，保留原失败，使用交付新入口验证 20 个目标 / 358 个独立身份。不存在的可选六项 ROS 接线回归是 NOT RUN；不得按退出 0 写成通过。
6. 探针开发失败不覆盖：v1 保存 UUID 字节时 TypeError，未形成完整结论；字节显式转为 int 后 v2 原场景/断言重跑，记录见 supplement/probe-development-note.json。容器准备时的本地编排失败另存 preparation-note.json。
7. 结束前确认六次 Mock 服务器均退出 0，进程表只剩 keeper，再停止补跑容器，保存 inspect 并采集证据。原容器仍停止。故障、NOT RUN、真实/模拟边界分开报告。原始日志不删；原 source.bundle 仅记录 SHA，镜像、SDK、Git bundle、二进制不冻结入库。
8. index.json 以本目录相对路径列出每个常规文件的 SHA-256 / 大小（不含自身），其哈希由 materials/manifest.json 注册。automatic/original-index.json 是原 outputs 索引，含未复制 bundle，不是本冻结目录索引。日志目录的 latest 符号链接不复制，指向的实际日志完整保留。
9. 本冻结集保存主对话 ACK 和 pre-complete 门禁快照。来源登记、文档同步和清理全部结束后才调用 complete；最终回执在 outputs/moveit-watch-20261011/wake/sha-c0f70172e4b0271046d5f52813e0730d40ae772a/receipt.json，避免为写终态而改动已冻结证据。没有调用 queue 或另启监测。

使用 OpenAI Codex 协助编排、探针与分析。TEAMMATE-ACTION-20261011 的根 LICENSE / package.xml 许可差异原样保留；独立驱动/模型沿用 TEAMMATE-SDK-20261011，不重新授权或归档 SDK。
''')
files=[{'path':p.relative_to(frozen).as_posix(),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(frozen.rglob('*')) if p.is_file() and p.name!='index.json']
write(frozen/'index.json',{'schema_version':1,'observation':'ENV-CPP-ACTION-20261011','created_at':recorded,'files':files,'scope':'Self excluded; original raw-run index separately named original-index.json; source bundle and symlinks omitted as documented.'})
# No nested raw index.json files copied: exclude by basename above is only self, verify this property.
assert not [p for p in frozen.rglob('index.json') if p!=frozen/'index.json']
print(json.dumps({'files':len(files),'bytes':sum(x['size_bytes'] for x in files),'index_sha256':sha(frozen/'index.json'),'receipt_latency_seconds':latency},indent=2))
