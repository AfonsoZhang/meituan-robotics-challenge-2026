from pathlib import Path
import hashlib,json,shutil
root=Path.cwd();run=Path(json.loads(Path('.agents/webui-p2-current.json').read_text())['run']);dest=Path('docs/experiments/webui-p2-20261013');dest.mkdir(exist_ok=False)
def copy(source,target):
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
for folder in ('logs','qa','sources'):
 for p in sorted((run/folder).rglob('*')):
  if p.is_file():copy(p,dest/folder/p.relative_to(run/folder))
for p in sorted((run/'container-output/p2-evidence').rglob('*')):
 if p.is_file():copy(p,dest/'container-evidence'/p.relative_to(run/'container-output/p2-evidence'))
for p in sorted(Path('webui').rglob('*')):
 if p.is_file() and '__pycache__' not in p.parts:copy(p,dest/'source-webui'/p.relative_to('webui'))
for name in ('source.patch','source-sync.json','patch-validation.json','installed-source-check.json','journal-integrity.json','cleanup.json'):
 copy(run/name,dest/name)
for p in [Path('.agents/webui_p2_exec.py'),Path('.agents/sync_webui_p2.py'),Path('.agents/freeze_webui_p2.py'),run/'qa_relay.py']:
 copy(p,dest/'harness'/p.name)
inputs={'user_source':'USER-HW-20261013-04','source_reference':'TEAMMATE-WEBUI-P2-20261013','personal_head_before':'bda833064c9f24384729285f903e9c730491e6b8','upstream_base':'8f11750e0bd2e485826acb904fd31382945ba0b9','upstream_main_observed':'b4185155383541e1a4161587c4049a162f74b36d','formal_pin_unchanged':'1d940f7c5f12561fed6641457c0b4b630a282b05','runtime':'Ubuntu 24.04 / ROS 2 Jazzy / Python 3.12; host Python 3.10','container':'mtc-webui-p2-20261013','image':'mtc-webui-p1-camera-base:20261013','image_id':'sha256:760cddbee52045a83ef71726e141b5dd34b193502b60786db9d6c72211287702','isolation':{'network':'none','domain':94,'discovery':'LOCALHOST','devices':[],'host_mounts':[],'port_exposure':[]},'raw_run':str(run),'source_map':'source-sync.json','installed_hashes':'installed-source-check.json'}
summary={'source_id':'ENV-WEBUI-P2-20261013','status':'PASS_SCOPED_UI_CONSUMERS','tests':{'python':73,'node':30,'p2_native_ros':6,'p1_native_ros_regression':6,'p0_native_ros_regression':5,'demo':27,'robot':30},'installed_repeats':{'python':73,'p2_native_ros':6,'do_not_count_as_additional_unique_cases':True,'matching_installed_files':33},'browser':{'native_task_trace':True,'three_actual_fixture_uuids':True,'goal_module_transition_filter':True,'pause_eight_unknown':True,'offline_no_fake_states_submit_disabled':True,'viewport_widths':[320,390,768,1440],'document_overflow':False,'http_export':{'status':200,'matching_events':23,'total':23,'attachment':True},'chrome_download_save_verified':False,'visibility':'hidden','interaction':'DOM form/button actions and actual HTTP; no snapshot/application-state injection','final_css':'query buttons corrected; final 390px offline screenshot verified'},'journal_integrity':json.loads((run/'journal-integrity.json').read_text()),'package_patch':{'base':inputs['upstream_base'],'changed_files':32,'applies_to_clean_checkout':True,'tree_match':True,'published':False},'cleanup':'cleanup.json','scope':'原生 ROS 消息/Action 测试夹具，无实机、实际 FSM/Planner/Phase 2C 内核验收；原始高频传感器并非 ROS bag','pending':['真实 Calibration 有效性与跨层 FJT trace 发布器','现场 TF 坐标链与标定有效性实测','NUC / 实体设备与整轮 FSM 闭环'],'ai_assistance':'OpenAI Codex implementation, testing, review and evidence preparation'}
notes={'initial_offline':'Four existing FJT tests used short fake UUID labels. Updated fixtures to valid UUID strings; final 73 passed without weakening native UUID contract.','initial_ros':'First P2 run omitted placement_stability_sec in the fixture HTTP goal; 2 tests rejected input. Fixed fixture input, native 6 passed.','browser':'Hidden Chrome prevented download event confirmation and element stable screenshot; direct clip also failed. Full-page screenshots / actual HTTP export retained. Service restarts caused 502 polls.','installed_inventory':'First inventory mistakenly included run.sh, not installed by package_data. Verification now checks 33 actual installed files; console_scripts is the installed entrypoint.','older_frozen_evidence':'P0/P1 and concurrent C1 directories unchanged; no earlier failure is removed.'}
for name,data in [('inputs.json',inputs),('summary.json',summary),('development-notes.json',notes)]:
 (dest/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(dest/'protocol.md').write_text('''# Web UI P2 scoped verification — 2026-10-13

USER-HW-20261013-04 / TEAMMATE-WEBUI-P2-20261013 / ENV-WEBUI-P2-20261013. OpenAI Codex assisted implementation, review, testing and evidence preparation.

## Scope and invariants

Eight-module tri-state health, read-only PickPlace/TF observation, optional calibration/trace consumers, complete recorded event query/export. No FSM/Cancel/Motion kernel changes, physical device, production RobotState/ToolState fabrication, baseline promotion or publishing. Preserve Cancel ACK != Stop Confirmed and raw ABORTED/520. Empty/expired/unwired remains unknown. Explicit Goal links only; conflicts quarantine derived ownership.

## Procedure

1. Read fixed PR8/main calibration/Phase2C source. Register new consumer contracts where no producer exists.
2. Run Python offline/HTTP and Node evidence-model tests, including 650-event pagination/export and late/conflicting UUID relationships.
3. Run native ROS fixtures in a new network=none, no-device/no-mount Jazzy container on domain 94 / LOCALHOST. Synthetic RobotState, TF and calibration valid=true are test stimuli, not physical measurements.
4. Build only mtc_cpp_mock_bringup. Repeat the same Python and P2 native checks under the installed namespace, verify installed bytes, and apply the cumulative UI patch to a clean checkout. No full FSM/MoveIt acceptance.
5. Use the configured Windows Playwright browser with an isolated HTTP relay. Native Task → PickPlace → FJT UUIDs, logs and HTTP records come from the actual fixture server. Verify filters, three-view widths and pause/offline behavior. Hidden-tab automation limitations are recorded in qa/browser-validation-notes.md.
6. Preserve complete JSONL/SQLite session files; check SQLite integrity and exact JSONL equality. Stop fixture, relay and container; leave only a no-domain readonly preview.

## Reproduce code checks

```bash
python3 -m unittest discover -s webui -p 'test_*.py'
node --test webui/test_p0.cjs webui/test_p1.cjs webui/test_p2.cjs
# Only in a network-isolated ROS fixture environment, never a robot domain:
python3 -m webui.p2_integration_check --isolated-fixture
python3 -m webui.p1_integration_check --isolated-fixture
python3 -m webui.p0_integration_check --isolated-fixture
```

Actual commands and return codes are in logs/*.command.json. Installed repeats are not extra unique cases. source-sync.json documents namespace conversion; source.patch changes only the Web module and package installation metadata. Full record means all received/recorded session events, not ROS bag or pre-session/unreceived data.

## Results and limitations

See summary.json and development-notes.json. Missing production publishers, hardware/NUC and real calibration remain pending. Browser HTTP export is verified; native Chrome download-to-file was not confirmed. No merge, push, hardware action or formal pin change.
''')
rows=[]
for p in sorted(dest.rglob('*')):
 if p.is_file():rows.append({'path':str(p.relative_to(dest)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
index={'schema_version':1,'source_id':'ENV-WEBUI-P2-20261013','files':rows,'file_count':len(rows),'total_bytes':sum(r['bytes'] for r in rows)}
(dest/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n')
sha=hashlib.sha256((dest/'index.json').read_bytes()).hexdigest()
p=Path('materials/manifest.json');m=json.loads(p.read_text());assert not any(e['id']=='ENV-WEBUI-P2-20261013' for e in m['local_observations'])
m['local_observations'].append({'id':'ENV-WEBUI-P2-20261013','kind':'local_isolated_ui_interface_validation','date':'2026-10-13','scope':'P2 消费与诊断功能；隔离 ROS 夹具，不代表生产发布器/NUC/实机验收','method':'73 Python / 30 Node / 6 P2 + 6 P1 + 5 P0 native ROS checks; installed 73/6 repeats; browser real HTTP/UUID checks; 33 installed hashes and clean patch application','report':'docs/web-ui.md','index':str(dest/'index.json'),'index_sha256':sha,'file_count':len(rows),'total_bytes':index['total_bytes'],'tests':summary['tests'],'limitations':summary['pending']+['Chrome 下载落盘未确认；使用 hidden 页 DOM 动作和实际 HTTP','完整记录指本会话已接收事件，不是 ROS bag'],'derived_files':['README.md','docs/current-status.md','docs/hardware-vision-plan.md','docs/open-questions.md','docs/web-ui.md','webui/README.md','webui/provenance.json','webui/p2-contract.md',str(dest/'protocol.md'),str(dest/'summary.json')]})
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files':len(rows),'bytes':index['total_bytes'],'index_sha256':sha},indent=2))
