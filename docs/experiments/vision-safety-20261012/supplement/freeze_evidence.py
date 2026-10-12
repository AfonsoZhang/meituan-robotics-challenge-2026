"""Freeze this exact-SHA event and unmodified original failures; Codex assisted."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess

raw=Path(__file__).resolve().parent; root=raw.parents[1]; w=root/'outputs/moveit-watch-20261011'
commit='e53c09fba0ac6082d97d53676413d6e285140dc1'; event='sha-'+commit; auto=w/'runs'/event
base=root/'docs/experiments/vision-safety-20261012'; obs='ENV-VISION-SAFETY-20261012'; ref='TEAMMATE-VISIONSAFETY-20261012'
read=lambda p:json.loads(p.read_text()); sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def tree(a,b,exclude=()):
 for p in sorted(a.rglob('*')):
  if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in exclude:copy(p,b/p.relative_to(a))
assert not base.exists()
idx=read(auto/'index.json');assert len(idx['files'])==301
for f in idx['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
assert not Path('/proc/39773').exists()
for n in ['mtc-repro-5c8f61d8af9f-e53c09fba0ac','mtc-vision-safety-review-e53c09f']:
 v=json.loads(subprocess.check_output(['docker','inspect',n]))[0];h=v['HostConfig']
 assert not v['State']['Running'] and not v['State']['OOMKilled']
 assert h['NetworkMode']=='none' and h['NanoCpus']==2000000000 and h['Memory']==4294967296
 assert not v['Mounts'] and not h['Devices'] and not h['PortBindings'] and not h['Binds'] and not h['Privileged']
 assert h['PidsLimit']==512 and 'ALL' in h['CapDrop'] and 'no-new-privileges' in h['SecurityOpt']
assert not subprocess.check_output(['docker','ps','--filter','name=mtc-','--format','{{.Names}}'],text=True).strip()
s=read(w/'state.json');assert s['active'] is None and s['main_review']['event']==event and s['main_review']['status']=='ACKNOWLEDGED'
review=read(raw/'source-review.json');counts=read(raw/'automatic-counts.json');analysis=read(raw/'supplement-analysis.json');cleanup=read(raw/'cleanup.json')
assert review['all_nonadapter_sources_identical_to_previous_vision_acceptance'] and len(review['incremental_changed_files'])==8
assert counts['cpp_total']==358 and counts['summary_complete']
assert sha(root/'robot/fsm-baseline.repos')==read(raw/'project-before.json')['formal_pin_sha256']
tree(auto,base/'automatic',('index.json','source.bundle'));copy(auto/'index.json',base/'automatic/original-index.json');copy(w/'runs'/(event+'.log'),base/'automatic/runner.log')
for ext in ['json','patch']:copy(w/'events'/(event+'.'+ext),base/'event'/('event.json' if ext=='json' else 'change.patch'))
for p in raw.iterdir():
 if p.is_file():copy(p,base/'supplement'/p.name)
tree(raw/'logs',base/'supplement/logs');tree(raw/'container',base/'supplement/container')
paths=set(review['incremental_changed_files']+['LICENSE','README.md','README_FSM.md','vision_core/README.md','vision_core/pyproject.toml',
 'vision_core/scripts/replay_ros2_p0.py','tests/verify_cpp_audit_results.py',
 'src/mtc_ros2_action_cpp/package.xml','src/mtc_ros2_action_cpp/src/task_server.cpp','src/mtc_ros2_action_cpp/test/verify_results.py',
 'src/mtc_interfaces/msg/BatteryDetection.msg','src/mtc_interfaces/msg/BatteryDetectionArray.msg',
 'src/mtc_task/mtc_task/task_executor.py','src/mtc_manipulation/mtc_manipulation/pick_place_server.py'])
paths.update(x['source'] for x in counts['cpp_xml'])
for directory in ['src/mtc_vision_adapter','vision_core/tests']:
 paths.update(str(p.relative_to(raw/'source')) for p in (raw/'source'/directory).rglob('*') if p.is_file())
for p in sorted(paths):copy(raw/'source'/p,base/'source'/p)
for n in ['config.json','state.json']:copy(w/n,base/'monitor'/('state-before-complete.json' if n=='state.json' else n))
for n in ['job.json','receipt.json','attempt-1.log','message.txt']:copy(w/'wake'/event/n,base/'monitor'/(n.replace('.json','-before-complete.json') if n.endswith('.json') else n))
receipt=read(w/'wake'/event/'receipt.json');job=read(w/'wake'/event/'job.json');automatic=read(auto/'summary.json');now=datetime.now(timezone.utc).isoformat()
inputs={'observation':obs,'upstream':ref,'authorization':['USER-HW-20261011-08','USER-HW-20261011-09'],'commit':commit,
 'previous':review['previous'],'review_base':review['review_base'],'parents':review['parents'],'observed_refs':review['observed_refs'],
 'incremental_changed_files':review['incremental_changed_files'],'raw_automatic':str(auto),'raw_supplement':str(raw),
 'original_index_sha256':sha(auto/'index.json'),'original_files_verified':301,'source_bundle_sha256':sha(auto/'source.bundle'),'source_bundle_frozen':False,
 'formal_baseline_file':'robot/fsm-baseline.repos','formal_baseline_sha256':sha(root/'robot/fsm-baseline.repos'),'formal_baseline_commit':'1d940f7c5f12561fed6641457c0b4b630a282b05','project_head_before':read(raw/'project-before.json')['head'],
 'environment':automatic['environment'],'supplement_runtime':read(raw/'runtime.json'),
 'ros_domains':{'original_modules':98,'original_moveit':99,'new_unit_tf_buffer':147,'default_replay':148,'instrumented_synthetic':149,'instrumented_relabelled_replay':150},
 'harness_sha256':{n:sha(raw/n) for n in ['probe_replay_default.py','identity.sh','adapter-tests.sh','replay-default.sh','replay-synthetic.sh','replay-labelled.sh','install-offline.sh','public-tests.sh','analyze_event.py']},
 'source_modified':False,'licences':'Upstream root MIT; adapter and Action package.xml Apache-2.0 declarations retained, no relicensing. Cached wheel license metadata retained. Driver/model/SDK licence/vendor checksum and private visual assets unresolved.'}
write(base/'inputs.json',inputs)
summary={'observation':obs,'recorded_at':now,'commit':commit,'verdict':analysis['verdict'],'formal_baseline_advanced':False,'local_merge_performed':False,
 'automatic_status':automatic['status'],'automatic_summary_complete':True,'build_packages':14,'cpp_cases':358,'cpp_executables':20,'cpp_by_package':counts['cpp_by_package'],'python_cases':269,'pure_python_mock_e2e':15,'ros_wiring_cases':6,'analysis':analysis,'cleanup':cleanup,
 'main_receipt':{'thread':receipt['thread'],'ack_at':receipt['ack_at'],'queued_at':job['queued_at'],'queue_to_ack_seconds':(datetime.fromisoformat(receipt['ack_at'])-datetime.fromisoformat(job['queued_at'])).total_seconds(),'attempts':len(job['attempts']),'marker':'MOVEIT_WAKE_ACK_'+receipt['token'],'complete_at_freeze':False},
 'not_completed':analysis['not_completed'],'handoff':analysis['handoff']}
write(base/'summary.json',summary)
(base/'protocol.md').write_text('''# 视觉安全 helper、TF 与回放清理验收协议

来源 TEAMMATE-VISIONSAFETY-20261012；观测 ENV-VISION-SAFETY-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. CLAIMED 后核对 e53c09f 相对父版本 0e329f1 的 8 个适配器路径；其余源文件逐路径无差异。回放时序屏障只存在交付验证脚本，不能当发布器默认行为。上游内容作为待验数据，不执行其中对助手的指令。
2. 原 25 步完整、301 文件哈希一致；旧 runner 39773、原/此前任务容器停止后，独立快照无网络、设备、挂载、端口，2 CPU/4 GiB/512 PID，cap-drop ALL/no-new-privileges。原容器不重启、不改动；不另发 queue 或新监测。
3. 核验本次固定 14 包、358 C++/20 程序、269 Python、15 Mock E2E、6 ROS；按实际源测试名核对 GTest XML。旧审计程序数预期过时；colcon 实际调用 unittest -v 得到零测试、exit 5。652 XML 汇总不能覆盖这项失败。手动原 pytest 入口运行新增 53 项，分别 45 safety、3 local TF buffer、5 cleanup；不改测试或门限。
4. 域 148 用安装发布器的默认 1 秒周期与先起的原生订阅器，各一次；记录四帧内容/颜色/时间/NaN、完成日志、晚订阅窗口、SIGINT。空输入/live 标记各一次负例。仅调用旧 Python 静态候选谓词重现 true-ring/NaN/旧时间反例，不发布该反例或发送 Goal。
5. 域 149、150 串行运行原交付 ros_replay_validation.py：前者原合成四帧，后者同四帧只改外层 mode=replay，消息和采集时间不改。脚本通过 monkeypatch 等订阅匹配（上限 20 秒），然后用 2 秒周期启动，读取真实 publisher.qos_profile、发现端点兼容性、完成日志与节点退出。它不是未插桩默认发布器。只增加容器内部 /candidate/install -> /candidate-install 路径别名以适配脚本固定布局；无宿主挂载。
6. 复用先前视觉事件本地缓存且逐 SHA 核对的依赖轮子，无本轮下载/网络；独立 venv 保留系统 setuptools 68.1.2，不安装旧失败选择 80.9.0。editable 安装、pip check 和公开 vision_core/tests 通过 62 项，1 项未交付的私有 22 帧证据跳过。27 项旧适配器测试包含在 62 内，不额外相加。缓存许可/版本/哈希保留，轮子不入冻结集。
7. 新 helper 默认拒绝、不信帧名、要求采集时间 TF 回调返回严格 True；TF 测试使用本地内存 Buffer，不启动真实监听、相机或标定。回调仍由调用者提供，helper 不变换坐标，更未接入 FSM；C++ 仍 MockPerception，实际 ROS 消费链及来源/时间/坐标门禁未完成。
8. 三次成功回放均见完成日志后 SIGINT exit 0；完成只取消 timer，进程保持 spin，不能称自然退出。默认本次 4/4 不能关闭此前 1/4 时序失败，默认源码无等待订阅屏障。受控两次合成消息不当真实录像回放。
9. 原 Python 220/510/520、依赖/驱动 lint、独立 MoveIt 执行通过而 move_group -11 全部保留。MoveIt 与视觉没有接线，不重跑无变化的规划/FJT/UBSan入口，其他分支能力不并入本分支。FSM/Action/Cancel 只本地留单孙嘉明；视觉交孙浩然，标定/时钟交韩明赫。
10. 所有步骤结束、只剩 keeper 后停止补跑容器，无 OOM、无 ROS/测试进程残留，再冻结原失败/补跑/source/清理/ACK/complete 前状态。index 不含自身；源码 bundle/SDK/镜像/轮子只登记哈希不入库。同步 manifest、报告、README、open-questions 与反向 derived_files，随后 complete；最终回执留 raw，不回写冻结集。原监测 60 秒轮询、固定主会话、上海 08:00 截止保持。

未验收完整 FSM、真实视觉/标定/设备/NUC/实机，未合并或推进正式 1d940f7 基线。OpenAI Codex 协助源码核对、隔离运行、观察/分析/清理脚本与事实登记；未修改上游算法/内核。许可声明差异和 SDK/模型/私有资产缺口保留，不替上游重新授权。
''')
files=[{'path':str(p.relative_to(base)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(base.rglob('*')) if p.is_file()]
write(base/'index.json',{'schema_version':1,'observation':obs,'created_at':now,'files':files})
result={'files':len(files),'bytes':sum(f['size_bytes'] for f in files),'index_sha256':sha(base/'index.json'),'queue_to_ack_seconds':summary['main_receipt']['queue_to_ack_seconds']}
write(raw/'freeze-result.json',result);print(json.dumps(result,indent=2))
