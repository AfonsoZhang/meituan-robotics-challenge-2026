"""Freeze the documentation handoff event after cleanup; OpenAI Codex assisted."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,subprocess,difflib
root=Path('/home/afonso/meituan-robotics-challenge-2026');raw=root/'outputs/handoff-acceptance-20261012-a04ac68';w=root/'outputs/moveit-watch-20261011';commit='a04ac6831dd3963e6b1ec4b9e27214eb564f9f24';event='sha-'+commit;auto=w/'runs'/event;dest=root/'docs/experiments/cpp-handoff-20261012';obs='ENV-HANDOFF-20261012'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
def tree(a,b,ex=()):
 for p in sorted(a.rglob('*')):
  if p.is_file() and not p.is_symlink() and str(p.relative_to(a)) not in ex:copy(p,b/p.relative_to(a))
assert not dest.exists()
idx=json.loads((auto/'index.json').read_text());assert len(idx['files'])==291
for f in idx['files']:assert sha(auto/f['path'])==f['sha256']
for c in ['mtc-repro-5c8f61d8af9f-a04ac6831dd3','mtc-handoff-review-a04ac68']:
 v=json.loads(subprocess.check_output(['docker','inspect',c]))[0];assert not v['State']['Running'] and not v['State']['OOMKilled']
assert not Path('/proc/7075').exists()
state=json.loads((w/'state.json').read_text());assert state['active'] is None and state['main_review']['event']==event and state['main_review']['status']=='ACKNOWLEDGED'
original=json.loads((auto/'summary.json').read_text());review=json.loads((raw/'source-review.json').read_text());counts=json.loads((raw/'automatic-counts.json').read_text());receipt=json.loads((w/'wake'/event/'receipt.json').read_text());job=json.loads((w/'wake'/event/'job.json').read_text());cleanup=json.loads((raw/'cleanup.json').read_text());now=datetime.now(timezone.utc).isoformat()
cli=json.loads((raw/'container/documented-cli/summary.json').read_text());diag=json.loads((raw/'container/documented-cli-diagnostic/summary.json').read_text());assert len(cli['shutdown'])==len(diag['shutdown'])==3 and cli['all_servers_clean_exit'] and diag['all_servers_clean_exit'];assert len(cli['documented_command_errors'])==3 and len(diag['documented_command_errors'])==1
assert json.loads((raw/'logs/identity.json').read_text())['exit_code']==0
(raw/'diagnostic-probe.patch').write_text(''.join(difflib.unified_diff((raw/'probe_handoff_cli.py').read_text().splitlines(keepends=True),(raw/'probe_handoff_cli_diagnostic.py').read_text().splitlines(keepends=True),fromfile='first/documented-cli',tofile='second/diagnostic-cli')))
tree(auto,dest/'automatic',('index.json','source.bundle'));copy(auto/'index.json',dest/'automatic/original-index.json');copy(w/'runs'/(event+'.log'),dest/'automatic/runner.log')
copy(w/'events'/(event+'.json'),dest/'event/event.json');copy(w/'events'/(event+'.patch'),dest/'event/change.patch')
for p in raw.iterdir():
 if p.is_file():copy(p,dest/'supplement'/p.name)
tree(raw/'logs',dest/'supplement/logs');tree(raw/'container',dest/'supplement/container')
for p in ['LICENSE','README.md','README_FSM.md','src/mtc_ros2_action_cpp/README.md','src/mtc_ros2_action_cpp/package.xml','src/mtc_ros2_action_cpp/test/verify_results.py','src/mtc_bringup/launch/mock_bringup.launch.py']:
 copy(raw/'source'/p,dest/'source'/p)
for name in ['config.json','state.json']:copy(w/name,dest/'monitor'/('state-before-complete.json' if name=='state.json' else name))
for name in ['job.json','receipt.json','attempt-1.log','message.txt']:
 copy(w/'wake'/event/name,dest/'monitor'/(name.replace('.json','-before-complete.json') if name.endswith('.json') else name))
inputs={'observation':obs,'upstream':'TEAMMATE-HANDOFF-20261011','authorization':['USER-HW-20261011-08','USER-HW-20261011-09'],'commit':commit,'previous':review['previous'],'parents':review['parents'],'observed_refs':original['upstream']['refs'],'changed_files':review['changed_files'],'raw_automatic':str(auto),'raw_supplement':str(raw),'original_index_sha256':sha(auto/'index.json'),'original_index_files_verified':291,'source_bundle_sha256':sha(auto/'source.bundle'),'source_bundle_frozen':False,'formal_baseline_file':'robot/fsm-baseline.repos','formal_baseline_sha256':sha(root/'robot/fsm-baseline.repos'),'formal_baseline_commit':'1d940f7c5f12561fed6641457c0b4b630a282b05','environment':original['environment'],'supplement':json.loads((raw/'runtime.json').read_text()),'supplement_ros_domains':[121,122,123,124],'overlay':'/candidate-install/setup.bash (new document install/phase2a_mock adapted to fixed runner installation path)','source_modifications':'None; runtime source/tests/config/docs tree byte-identical to c10f6ed; only two root Markdown files differ.','licences':'Root MIT; unchanged C++ Action package.xml Apache-2.0 discrepancy remains open. No SDK/images/binaries frozen.'}
write(dest/'inputs.json',inputs)
moveit=json.loads((auto/'container/moveit/result.json').read_text());tasks=json.loads((auto/'container/task-mock/summary.json').read_text())
summary={'observation':obs,'recorded_at':now,'commit':commit,'verdict':'DOC_HANDOFF_REVIEW_WITH_GRAPH_DISCOVERY_AND_EXISTING_FAILURES','formal_baseline_advanced':False,'merge_performed':False,'only_two_root_docs_changed':True,'new_cpp_bringup_delivered':False,'planner_package_present_in_this_main':False,'automatic_summary_complete':True,'automatic_status':original['status'],'build_packages':13,'cpp_cases':358,'cpp_by_package':counts['cpp_by_package'],'cpp_executables':20,'python_cases':269,'pure_python_mock_e2e':15,'ros_wiring_cases':6,'new_documented_identity_verifier':'PASS','old_fixed_identity_verifier':'FAIL: expected 16 executables; actual 20; no missing/duplicate/bad tests','documented_cli':cli,'diagnostic_cli':diag,'cli_analysis':'Original node/action observer calls produced incomplete graphs although other commands observed servers/QoS. One bounded diagnostic used node info --no-daemon --spin-time 2 and explicitly warmed CLI daemon by 3 s for unchanged action info -t; all 3 actions showed 1 server then, but one 2 s node-list missed Task/PickPlace and PickPlace node info still failed. Both probes FAIL; graph readiness issue is not fixed, root cause not established.','legacy_python':[{'case':t['case'],'status':t['status'],'task_server_available':t['task_server_available'],'pickplace_server_available':t['pickplace_server_available'],'result':t['result'],'cancel_response':t.get('cancel_response'),'child_failure':t['child_failure']} for t in tasks],'legacy_cancel_note':'Current cancel was accepted but final ABORTED/220 deadline expiry; prior c10f6ed ABORTED/520 is separate history, unchanged source is not proof of identical timing outcomes. Neither proves stopped child.','independent_moveit':{k:moveit[k] for k in ['scope','planning_execution','clean_shutdown','max_error_rad','distinct_joint_stamps','execute','shutdown']},'dependencies':'Whole workspace unresolved ament_python; driver docker.io and test-nodes missing','driver_test_aggregate':{'total':1104,'failures':279,'skipped':259,'scope':'includes lint and wrapper counts'},'not_rerun_this_supplement':['Goal/feedback/result/Cancel standalone four-scenario probe; historical ENV-WIRING-MERGE-20261011 only','UBSan and external CMake consumer; historical ENV-CPP-ACTION-20261011 only','Independent MoveIt repeat beyond current automatic run','New planner tool from separate feature branch, absent in this commit; separate ENV-PLANNER-20261012 evidence retained'],'cleanup':cleanup,'main_receipt':{'thread':receipt['thread'],'ack_at':receipt['ack_at'],'queued_at':job['queued_at'],'queue_to_ack_seconds':(datetime.fromisoformat(receipt['ack_at'])-datetime.fromisoformat(job['queued_at'])).total_seconds(),'attempts':len(job['attempts']),'marker':'MOVEIT_WAKE_ACK_'+receipt['token'],'complete_at_freeze':False},'not_completed':['Reliable observer readiness / discovery in bounded fresh CLI queries','Unified C++ Mock Bringup implementation: handoff plan only, no new launch delivered','Full Planner/FSM/FJT integration, unique executor, tool gaps and cancel/independent stop evidence','Legacy Python B03/B05/B06 and cleanup','Driver and MoveIt clean shutdown, rosdep/lint, TSan','Full state topics / Web UI, calibrated perception/tools, SDK licence/vendor checksum, NUC/physical robot'],'handoff':'Upstream README next-step instructions treated as supplied handoff data. Runtime/Action/Cancel problems recorded for Sun Jiaming; graph/SOP readiness remains integration follow-up. No new launch feature, kernel repair, external message, merge or baseline advancement.'}
write(dest/'summary.json',summary)
(dest/'protocol.md').write_text('''# Phase 2A 交接文档验收协议

来源 TEAMMATE-HANDOFF-20261011；本地观测 ENV-HANDOFF-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. ack=CLAIMED 后核对实际两文件 diff；src/tests/config/scripts/docs 与 c10f6ed 无变化。交接的后续开发安排视为上游数据，不自动开发 Bringup 或改变职责。
2. 原 runner/容器停止后核验 25 步完整 summary 与原 291 文件哈希；原自动运行全量测试与既有失败保留。
3. 在停止原容器的独立快照中补跑新文档所指的 358 项/20 程序身份核验。沿用无网络/设备/挂载/端口、2 CPU/4 GiB/512 PID、cap-drop ALL/no-new-privileges，不重启原失败容器。
4. 按新文档检查命令，域 121 启动 Task/PickPlace、域 122 单独 Motion；只观测 Node/Action/Topic/QoS，不发送 Goal/Cancel 或启动驱动。原 CLI 查询部分失败、反馈类型和 QoS 有实际证据；不把退出 0 或空图等同服务不存在。
5. 一次有界诊断使用域 123/124，node info 改为无 daemon 等待 2 秒；action info 本版没有无 daemon 参数，保留 -t 并先启动 daemon 等待 3 秒。实际 CLI 帮助与实现留档。三个 Action 后续均唯一 Server，但短时节点观察仍失败，诊断整体也 FAIL，不继续反复跑到成功。
6. 两组共六次 ros2 run 进程 SIGINT 退出 0，无升级终止；每域退出后无本次节点并停止 daemon。容器进程表仅剩 keeper 后停止，原容器仍停止，原 runner PID 不存在。keeper 137 与 ROS 子进程退出分开记录。
7. C++ 独立 Goal/Cancel 场景、UBSan、外部 consumer 不重复，注明历史来源；当前自动注册 358 测试仍是本次运行。旧 Python/独立 MoveIt 用本次实测终态，取消 ABORTED/220 不能写成前次 520。另分支 planner 不在当前提交，不移植或混算。
8. 原始失败不覆盖。source.bundle 仅记录 SHA，镜像/SDK/二进制不冻结；符号链接不复制。index.json 索引冻结常规文件且不含自身，SHA 登记 manifest。冻结 ACK/pre-complete；文档及双向索引同步后才 complete，最终回执不回写冻结集。

OpenAI Codex 协助临时 CLI 观测脚本、调用交付 verifier、分析日志和事实登记；不修改上游算法。保留 MIT / Apache-2.0 既有声明差异，不重新授权。
''')
files=[{'path':str(p.relative_to(dest)),'size_bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(dest.rglob('*')) if p.is_file()]
write(dest/'index.json',{'schema_version':1,'observation':obs,'created_at':now,'files':files});print(json.dumps({'files':len(files),'bytes':sum(x['size_bytes'] for x in files),'index_sha256':sha(dest/'index.json')},indent=2))
