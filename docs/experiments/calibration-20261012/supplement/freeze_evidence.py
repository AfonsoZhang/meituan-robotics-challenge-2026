"""Freeze source-specific calibration evidence after cleanup. OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
raw=Path(__file__).resolve().parent;root=raw.parents[1];w=root/'outputs/moveit-watch-20261011'
commit='06ab689f25e87dcebf9fd04fdd581ec4755206f6';event='sha-'+commit;auto=w/'runs'/event
base=root/'docs/experiments/calibration-20261012';obs='ENV-CALIBRATION-20261012';ref='TEAMMATE-CALIBRATION-20261012'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def tree(a,b,exclude=()):
 for p in sorted(a.rglob('*')):
  if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in exclude:copy(p,b/p.relative_to(a))
assert not base.exists()
index=read(auto/'index.json');assert len(index['files'])==305
for f in index['files']:assert sha(auto/f['path'])==f['sha256'],f['path']
assert not Path('/proc/32186').exists()
for n in ['mtc-repro-5c8f61d8af9f-06ab689f25e8','mtc-calibration-review-06ab689']:
 v=json.loads(subprocess.check_output(['docker','inspect',n]))[0];h=v['HostConfig']
 assert not v['State']['Running'] and not v['State']['OOMKilled']
 assert h['NetworkMode']=='none' and h['NanoCpus']==2000000000 and h['Memory']==4294967296
 assert not v['Mounts'] and not h['Devices'] and not h['PortBindings'] and not h['Binds'] and not h['Privileged']
 assert h['PidsLimit']==512 and 'ALL' in h['CapDrop'] and 'no-new-privileges' in h['SecurityOpt']
assert not subprocess.check_output(['docker','ps','--filter','name=mtc-','--format','{{.Names}}'],text=True).strip()
s=read(w/'state.json');assert s['active'] is None and s['main_review']['event']==event and s['main_review']['status']=='ACKNOWLEDGED'
review=read(raw/'source-review.json');counts=read(raw/'automatic-counts.json');a=read(raw/'supplement-analysis.json');cleanup=read(raw/'cleanup.json')
assert review['all_existing_sources_identical_to_reviewed_main'] and len(review['incremental_changed_files'])==38
assert counts['cpp_total']==387 and counts['summary_complete'] and counts['original_files_verified']==305
assert a['supplement']['offline']['all_passed'] and a['supplement']['fake_tf_runtime']['status']=='PASS_READ_ONLY_FAKE_TF'
assert sha(root/'robot/fsm-baseline.repos')==read(raw/'project-before.json')['formal_pin_sha256']
tree(auto,base/'automatic',('index.json','source.bundle'));copy(auto/'index.json',base/'automatic/original-index.json')
copy(w/'runs'/(event+'.log'),base/'automatic/runner.log')
for ext in ['json','patch']:copy(w/'events'/(event+'.'+ext),base/'event'/('event.json' if ext=='json' else 'change.patch'))
for p in raw.iterdir():
 if p.is_file():copy(p,base/'supplement'/p.name)
tree(raw/'logs',base/'supplement/logs');tree(raw/'container',base/'supplement/container')
paths=set(review['cumulative_changed_files']+['LICENSE','tests/verify_cpp_audit_results.py'])
for p in sorted(paths):copy(raw/'source'/p,base/'source'/p)
for n in ['config.json','state.json']:copy(w/n,base/'monitor'/('state-before-complete.json' if n=='state.json' else n))
for n in ['job.json','receipt.json','attempt-1.log','message.txt']:
 copy(w/'wake'/event/n,base/'monitor'/(n.replace('.json','-before-complete.json') if n.endswith('.json') else n))
receipt=read(w/'wake'/event/'receipt.json');job=read(w/'wake'/event/'job.json');now=datetime.now(timezone.utc).isoformat()
inputs={'observation':obs,'upstream':ref,'authorization':['USER-HW-20261011-08','USER-HW-20261011-09'],
 'commit':commit,'previous':review['previous'],'review_base':review['review_base'],'parents':review['parents'],'observed_refs':review['observed_refs'],
 'incremental_changed_files':review['incremental_changed_files'],'cumulative_changed_files':review['cumulative_changed_files'],
 'src_tree':review['src_tree'],'previous_src_tree':review['previous_src_tree'],
 'previous_frozen_index_sha256':review['previous_frozen_index_sha256'],'previous_frozen_files_verified':450,
 'previous_signed_report_sha256':review['previous_signed_report_sha256'],
 'raw_automatic':str(auto),'raw_supplement':str(raw),'original_index_sha256':sha(auto/'index.json'),
 'original_files_verified':305,'source_bundle_sha256':sha(auto/'source.bundle'),'source_bundle_frozen':False,
 'formal_baseline_file':'robot/fsm-baseline.repos','formal_baseline_sha256':sha(root/'robot/fsm-baseline.repos'),
 'formal_baseline_commit':'1d940f7c5f12561fed6641457c0b4b630a282b05','project_head_before':read(raw/'project-before.json')['head'],
 'environment':read(auto/'summary.json')['environment'],'supplement_runtime':read(raw/'runtime.json'),
 'ros_domains':{'original_moveit':99,'offline_verifier':137,'readonly_fake_tf':138},
 'harness_sha256':{n:sha(raw/n) for n in ['probe_fake_tf.py','offline.sh','fake-tf.sh','analyze_event.py','cleanup_event.py']},
 'source_modified':False,'licences':'Upstream root/planner/calibration MIT; Action package.xml Apache-2.0 discrepancy retained. AUBO model/SDK licences and vendor checksums unresolved; not re-licensed.',
 'upstream_user_confirmation_not_imported':review['scope_warning']}
write(base/'inputs.json',inputs)
summary={'observation':obs,'recorded_at':now,'commit':commit,'verdict':a['verdict'],
 'formal_baseline_advanced':False,'local_merge_performed':False,'existing_sources_identical_to_reviewed_main':True,
 'automatic_status':'COMPLETED_WITH_FAILURES','automatic_summary_complete':True,
 'build_packages':14,'cpp_cases':387,'cpp_executables':24,'cpp_by_package':counts['cpp_by_package'],
 'python_cases':269,'pure_python_mock_e2e':15,'ros_wiring_cases':6,'new_offline_calibration_tests':54,
 'analysis':a,'cleanup':cleanup,
 'main_receipt':{'thread':receipt['thread'],'ack_at':receipt['ack_at'],'queued_at':job['queued_at'],
  'queue_to_ack_seconds':(datetime.fromisoformat(receipt['ack_at'])-datetime.fromisoformat(job['queued_at'])).total_seconds(),
  'attempts':len(job['attempts']),'marker':'MOVEIT_WAKE_ACK_'+receipt['token'],'complete_at_freeze':False},
 'not_completed':a['not_completed'],'handoff':a['handoff']}
write(base/'summary.json',summary)
(base/'protocol.md').write_text('''# 标定 / TF 离线交付与 Fake 只读验收协议

来源 TEAMMATE-CALIBRATION-20261012；观测 ENV-CALIBRATION-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. 先CLAIMED后审实际差异：06ab689相对正式1d940f7共119路径，相对已验main/f7eaa2c仅新增38个标定源码/测试/夹具/文档；全部既有src树一致。复核ENV-PLANNER-MAIN-20261012的450文件/索引/已签收报告。新轨迹、视觉和新场景分支不在此快照，默认Action仍Mock。
2. 核对25步summary起止/退出、305原始哈希及失败日志。14包、387 C++/24程序、269 Python/15 E2E/6 ROS通过。旧审计源写16、实际日志为20个*_cpp程序，无缺失/重复/失败；规划包不匹配该glob。交付新审计补跑358/20通过，29规划用例另按源码/XML核对，685汇总含包装/lint。
3. 确认原runner32186与旧任务容器停止，从停止原容器独立快照补验。无网络/设备/挂载/端口、2CPU/4GiB/512PID、cap-dropALL/no-new-privileges。源/安装/控制配置不改，无依赖安装。只运行交付run_offline_validation.py，使用已有--out将输出写入/review-evidence/offline，避免覆盖上游原证据。
4. Python3.12.3/Linux实际54测试无跳过，AST测试身份和逐项日志一致；6文档示例+5生成反例均达到预期，42本地链接和4类CSV列宽检查通过。5个独立诊断JSON对象与上游一致，生成反例只在Windows/Linux临时路径分隔符不同。原分析器两次比较断言（平台路径、把源码中的16误要求出现在日志）和版本保留，修正分析未改数据或重跑测试。
5. 合成完整Pose位置[1,1.1,0.05]、姿态[-sqrt(.5),0,0,sqrt(.5)]和stamp10^10ns保留；UNKNOWN外参拒绝，设计/清单不是观测case，超大整数/20万层JSON/mm误填均拒绝；全部motion_authorized=false。名义设计[.0825,0,.0358]m仅为ESTIMATED数学输出；上游引用相机资料未在本轮重新下载或核读，不作物理标定/安装确认。
6. 交付归档模型审计通过：三份旧TF日志5/5/7样本、零关节FK、SRDF和腕部末端固定旋转一致；原3位小数日志最大平移分量差.0002m属于舍入比较，非实测精度。真实清单8边仍UNKNOWN、阈值null，手眼/TCP/误差采样CSV只有表头。上游“用户确认V1/法兰安装”只作为上游交接前提，不新增本项目用户决策或收敛末端候选。
7. 在域138追加一次只读Fake运行：原驱动显式GenericSystem，无RViz、无Goal/ActionClient/TF发布。读取robot_state_publisher实际robot_description及SHA、活动控制器，收903个新JointState戳且六关节位置/速度为0；观察FJT客户端0/服务端1、无Goal状态。以同一约200ms前的时间查world/base、wrist3/ee、base/ee、world/ee，与展开模型零关节FK一致；腕部→ee为零平移/Z+π/2，base→ee约[0,-.2562,.8072]m。
8. 四个AUBO固定Git blob哈希/大小与上游官方资料receipt一致；另7项相机/API参考未独立复核。TF浮点数误差不解释为真实精度。同一过去时刻在静止Fake可查，不证明运动相机时钟/采集同步。camera/optical/工具/台面/工位提案frames均不可达，不发布零TF补缺。
9. 默认规划仍用latest TF，Core stamp为另一时基；TCP已经逆补偿、工位只消费TCP位置/沿用抓取姿态，诊断拒绝未接入实际适配器。标定数据与物理F归韩明赫；相机观测归孙浩然；规划时间/语义归常建烁；FSM/Action/Cancel、完整Pose/时钟/失败传播归孙嘉明，本轮不接管修复或代发消息。
10. 原独立MoveIt执行4/1、误差约.0000937rad/209戳通过，退出move_group-11/control0；旧Python早Goal220、延迟INIT510、Cancel受理后220均ABORTED且完成0。依赖/驱动lint仍失败，全部保留。既有规划SOP/独立Action/UBSan不因纯新增离线代码重复，历史结果不改记为本次复跑。
11. 只读驱动控制器退出0，无升级终止；保留pal_statistics invalid-context线程错误。按域停止daemon、确认空域与仅keeper。清理守卫首次因复制helper的SHA字面量损坏拒绝，原脚本/快照保留；核对真实HEAD修正比较后停止容器，两容器无OOM、原runner不在。没有绕过运行进程守卫。
12. 冻结原始失败、新结果、源码、清理及ACK/pre-complete；index不含自身。bundle/镜像/SDK/构建二进制仅登记身份不入库。同步manifest、正文、README、open-questions与反向索引后complete，最终回执存raw不改冻结集。原60秒轮询/指定主会话/上海08:00截止不变，不调用queue或新启监测。

本轮是离线数学/输入契约与Jazzy零关节Fake坐标核验。没有实物外参/TCP/工位、手眼求解、真实安装、运动相机同步、完整FSM或NUC/实机验收。正式1d940f7锁定未动，没有合并。OpenAI Codex协助实际源/日志核对、复用交付入口、编写只读TF观察及事实登记；未修改上游算法/内核，根MIT与Action Apache-2.0及模型/SDK许可缺口保留。
''')
files=[{'path':str(p.relative_to(base)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(base.rglob('*')) if p.is_file()]
write(base/'index.json',{'schema_version':1,'observation':obs,'created_at':now,'files':files})
print(json.dumps({'files':len(files),'bytes':sum(f['size_bytes'] for f in files),'index_sha256':sha(base/'index.json'),'queue_to_ack_seconds':summary['main_receipt']['queue_to_ack_seconds']},indent=2))
