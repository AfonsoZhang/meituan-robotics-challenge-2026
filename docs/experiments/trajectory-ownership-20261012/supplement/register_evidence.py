"""Register exact-SHA acceptance and reverse source links. Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
raw=Path(__file__).resolve().parent;root=raw.parents[1];base=Path('docs/experiments/trajectory-ownership-20261012')
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=root/'materials/manifest.json';m=read(p);i=read(root/base/'inputs.json');s=read(root/base/'summary.json');a=s['analysis'];sup=a['supplement'];idx=read(root/base/'index.json')
obs='ENV-TRAJECTORY-OWNERSHIP-20261012';ref='TEAMMATE-OWNERSHIP-20261012';groups=['sources','project_decisions','external_references','local_observations']
assert not any(e['id'] in [obs,ref] for g in groups for e in m[g])
m['external_references'].append({'id':ref,'kind':'teammate_fjt_pending_ownership_live_status_contract','title':'Phase2B Goal归属与原生Status门禁更新',
 'url':'https://github.com/F1u0rite/meituan_challenge_ws/commit/'+i['commit'],'accessed_on':'2026-10-12','commit':i['commit'],'previous':i['previous'],'parents':i['parents'],'observed_refs':i['observed_refs'],
 'code_commit':'b8857de49ec5405812f87887b1407092af7335a5','changed_files':i['changed_files'],'verification_method':'读取实际7文件差异、15新增真实DDS时序测试、production pending UUID及Status门禁、Snapshot布局、探针返回码和新身份核验器；上游报告与本机证据分开。',
 'source_review':str(base/'supplement/source-review.json'),'archived_patch':str(base/'event/change.patch'),'source_archive':str(base/'source'),'local_validation':obs,
 'upstream_claim_vs_local_result':'上游报告普通/UBSan478通过。原固定复现FJT套件DuplicateCancel第7项120秒超时，missing_result；本项目未改二进制61项补跑和独立478UBSan通过，不关闭间歇挂起。原生预检零Goal阻断和默认双客户端已独立复现。',
 'license_status':i['licences'],'scope_note':'仅独立Fake端口及受控DDS测试；原生Status初始化/实时证据与独占执行契约阻断，普通补跑/UBSan不是稳定性或完整FSM证明；未改源、合并、推进正式基线或执行上游文档指令。','derived_files':[]})
m['local_observations'].append({'id':obs,'kind':'isolated_fjt_ownership_timeout_retry_ubsan_native_status_acceptance','date':'2026-10-12','observed_at':s['recorded_at'],
 'triggered_by':i['authorization'],'upstream_source':ref,'commit':i['commit'],'report':'docs/trajectory-ownership-acceptance.md','index':str(base/'index.json'),'index_sha256':sha(root/base/'index.json'),
 'inputs':str(base/'inputs.json'),'summary':str(base/'summary.json'),'raw_output_directories':[i['raw_automatic'],i['raw_supplement']],'verification_status':s['verdict'],
 'method':'CLAIMED后读取25步/317文件、完整增量和原CTest日志；runner及旧容器停止后，2CPU/4GiB无网络/设备/挂载/端口新快照中只补跑一次未改61项二进制、独立478UBSan。原新核验器仍检查失败原XML。域155原生Status预检、域156默认MoveIt共存串行运行，只订阅观察，无额外ActionClient、伪造Status或预热Goal。清理后冻结并同步事实链。',
 'observed':{'packages_built':15,'original_cpp_xml_passed':417,'original_fjt_suite_registered':61,'original_fjt_log_only_passes':6,'original_timeout_case':'FjtAction.DuplicateCancelOnlyOneBackendCall',
 'original_fjt_timeout_seconds':120,'original_fjt_xml':'test_fjt_action.gtest.missing_result','original_colcon_aggregate':{'tests':718,'errors':1,'failures':1},
 'ordinary_retry':sup['ordinary_retry'],'ubsan':sup['ubsan'],'python_cases':269,'python_mock_e2e':15,'ros_wiring_cases':6,'old_fixed_audit':a['automatic']['counts']['old_fixed_audit'],
 'new_verifier_original':'FAIL missing_result; no original XML replaced','native_gate':sup['native_gate'],'native_other_modes':sup['native_other_modes'],'native_goals':0,
 'new_package_rosdep':'PASS','installed_identity_files':4,'invalid_probe_arguments':'2 cases exit2 before ROS init',
 'acceptance_harness_failure':'First native observer wrongly expected exit2 for success-mode blocked exception which correctly returns1; assertion and original FAIL summary retained. Control exit0/empty domain. Only unexecuted topology branch rerun in separate domain156.',
 'automatic_moveit':{'planning_execution':'PASS','execute_status':4,'moveit_code':1,'max_joint_error_rad':a['automatic']['moveit']['max_error_rad'],'distinct_joint_stamps':209,'move_group_exit':-11,'control_exit':0},
 'legacy_python_task_error_codes':[220,510,520],'legacy_python_all_aborted_completed_zero':True,'driver_aggregate':a['automatic']['driver_aggregate'],'all_event_containers_stopped':True,
 'queue_attempts':s['main_receipt']['attempts'],'queue_to_ack_seconds':s['main_receipt']['queue_to_ack_seconds']},
 'not_completed':s['not_completed'],'handoff':s['handoff'],'scope':'原挂起尚无线程栈/根因；补跑通过不消除失败。原生Status/独占权、MoveIt第二客户端、异步FSM取消宿主、规划时钟、完整Task/PickPlace/UI/NUC/实机均非本次通过。08:00集成/UI定时任务未提前启动。无内核修复、queue/新监测/外部消息、合并或基线推进。',
 'algorithm_provenance':{'upstream_references':[ref,'TEAMMATE-TRAJECTORYGATE-20261012','TEAMMATE-SDK-20261011'],'bounded_test_runner':str(base/'supplement/run_action_tests.py'),
 'native_observer_with_preserved_failure':str(base/'supplement/probe_native_gate.py'),'topology_only_observer':str(base/'supplement/probe_topology_gate.py'),'analysis':str(base/'supplement/analyze_event.py'),
 'ai_assistance':'OpenAI Codex协助检查源码/日志、原入口复现、编写有界执行/只读观察/分析/归档脚本；修正仅本地观察器错误，不修改上游内核或算法。'},'derived_files':[]})
entries={e['id']:e for g in groups for e in m[g]}
files=[root/f for f in ['README.md','docs/trajectory-ownership-acceptance.md','docs/hardware-vision-plan.md','docs/open-questions.md','docs/upstream-monitor.md','robot/README.md']]
files += [f for f in (root/base).rglob('*') if f.is_file()]
pattern=re.compile(r'(?<![A-Z0-9-])(?:'+'|'.join(re.escape(k) for k in sorted(entries,key=len,reverse=True))+r')(?![A-Z0-9-])')
for f in files:
 try:text=f.read_text()
 except UnicodeDecodeError:continue
 for ident in set(pattern.findall(text)):
  links=entries[ident].setdefault('derived_files',[]);name=str(f.relative_to(root))
  if name not in links:links.append(name)
for e in entries.values():
 if 'derived_files' in e:e['derived_files']=sorted(set(e['derived_files']))
m['updated_on']='2026-10-12';p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print('REGISTERED',ref,obs,len(idx['files']),sha(root/base/'index.json'))
