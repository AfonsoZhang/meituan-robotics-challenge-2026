"""Freeze only this P1 UI delivery; preserve P0 and concurrent C1 work."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,shutil,subprocess

root=Path.cwd();run=Path(json.loads(Path('.agents/webui-p1-current.json').read_text())['run'])
dest=Path('docs/experiments/webui-p1-20261013');dest.mkdir(parents=True,exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b)
stamp=datetime.now(timezone.utc).isoformat()
for directory in ['logs','qa','sources']:
    for p in (run/directory).rglob('*'):
        if p.is_file():copy(p,dest/directory/p.relative_to(run/directory))
for p in (run/'container-final/p1-evidence').rglob('*'):
    if p.is_file():copy(p,dest/'container-evidence'/p.relative_to(run/'container-final/p1-evidence'))
for name in ['source.patch','source-sync.json','patch-validation.json','installed-source-check.json','container-isolation.json','cleanup.json']:
    copy(run/name,dest/name)
for name in ['qa_relay.py','qa_relay-v1.py']:copy(run/name,dest/'harness'/name)
for name in ['webui_p1_exec.py','sync_webui_p1.py','freeze_webui_p1.py']:copy(Path('.agents')/name,dest/'harness'/name)
source_files={}
for p in Path('webui').rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:
        copy(p,dest/'source-webui'/p.relative_to('webui'));source_files[str(p)]=sha(p)
sources=['USER-HW-20261013-02','TEAMMATE-WEBUI-P1-20261013']
inputs=dict(source_ids=sources,observed_at=stamp,personal_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            personal_working_tree_sha256=source_files,upstream_initial='7da43228d602a6b23571bfc599d69529ef7bea23',
            upstream_final='8f11750e0bd2e485826acb904fd31382945ba0b9',upstream_same_tree=True,
            formal_baseline='1d940f7c5f12561fed6641457c0b4b630a282b05',
            container='mtc-webui-p1-20261013',image='sha256:760cddbee52045a83ef71726e141b5dd34b193502b60786db9d6c72211287702',
            network='none',devices=[],mounts=[],ports=[],ros_domain=94,cpus=2,memory='4 GiB',
            runtime=dict(python='3.12.3',rclpy='7.1.12',opencv='4.6.0',numpy='1.26.4',control_msgs='5.10.0'),
            source_sync='source-sync.json',patch='source.patch',native_interface_prefix='/work/install/mtc_interfaces',
            image_origin='Read-only snapshot of stopped mtc-webui-20261011; previous source/evidence not changed or rerun')
dump(dest/'inputs.json',inputs)
summary=dict(source_id='ENV-WEBUI-P1-20261013',source_ids=sources,status='UI_CLIENT_AND_ISOLATED_INTERFACES_PASS; REAL_PRODUCERS_AND_HARDWARE_PENDING',
             tests=dict(host_python_passed=62,jazzy_python_passed=62,node_passed=20,p1_ros_passed=6,p0_ros_regression_passed=5,demo_passed=27,robot_passed=30,
                        installed_package=dict(build=True,python_passed=62,python_skipped=0,p1_ros_passed=6,entry_help=True,byte_match_files=28,
                                               note='Repeats the same tests in installed namespace; not additional unique cases')),
             browser=dict(native_detection_rows=3,rgb_and_depth=True,target_id_highlight='fixture-battery-1 (RGB screenshot)',
                          attached_with_command_only='not independently confirmed',test_lift='verified',seated='not provided',
                          raw_planner_error='EXCEEDS_STATE_WATCHDOG',cancel_ack='accepted',cancel_final='ABORTED/520',independent_stop='unconfirmed',
                          pause_clears_image_target_proof=True,widths=[320,390,768,1440],views=3,document_overflow=False,
                          caveat='Hidden Chrome: DOM clicks and Pause/Resume used for live refresh; foreground pointer/keyboard not covered. Relay 502 and timeouts retained.',
                          positive_observations='qa/p1-browser-observations.json',screenshots=['qa/webui-p1-rgb.png','qa/webui-p1-depth.png','qa/webui-p1-planner.png','qa/webui-p1-mobile.png']),
             missing_upstream=['Planner live observation publisher','test-lift/seated independent proof publisher','2D boxes and image frame association'],
             not_verified=['physical D435i','real tool attachment/lift/seating','Planner/FSM/MoveIt/FJT complete chain','NUC','RViz/3D','C1 actual kernel fix'],
             failures_retained=['apt build timeout','wheel download timeout','fixture shared-Time construction error','WSL source-copy failure and repeat with old fixture',
                                'browser relay 502 and undefined module until reload','hidden Chrome action/rAF timeouts','first mobile camera overflow'],
             patch_scope='Cumulative P0+P1 on original PR8, tree-identical to completion PR8; Web module and package metadata only',patch_published=False,
             cleanup='cleanup.json',ai_assistance='OpenAI Codex')
dump(dest/'summary.json',summary)
(dest/'protocol.md').write_text('''# Web UI P1 独立接口验证协议

范围：USER-HW-20261013-02；源码核对 TEAMMATE-WEBUI-P1-20261013；结果登记 ENV-WEBUI-P1-20261013。正式 pin 不变。此轮不恢复旧自动监测或 C1/完整 FSM 验收；工作区另有独立 C1 修复不并入本补丁。

1. 读取原生 BatteryDetectionArray/ToolState 与固定 Planner/视觉源码，确认没有二维框、实时 Planner 话题或试提/落座 IDL。对可选 JSON 消费约定显式固定发布者。
2. 离线测试非有限位姿、旧 PoseStamped、重复 ID、未知检查、命令证据不得独立确认、验证身份、同一锁内 JPEG+时间戳。Node 检查当前目标/其他任务/过期/暂停等展示边界。
3. 全新 network=none、无设备/挂载/暴露端口、2 CPU/4 GiB 容器，固定 domain 94。原生 ROS 图像、BatteryDetectionArray、ToolState、String 由明确合成夹具发布；没有实体相机、FSM、Planner、Motion/SDK 驱动运行。
4. 六项 P1 检查涵盖 RGB/16UC1 深度 JPEG、三块检测、NaN/旧位姿/零检测、watchdog 原因与新 plan 不继承检查、工具估计与非法独立证据、重复发布源和断流。另跑五项原有 P0 ROS 回归，保留 ACK≠Stop Confirmed 与注入 ABORTED/520。
5. Windows 浏览器通过临时 loopback Docker-exec 转发读取实际 HTTP/ROS 快照。截图均合成输入，明确标注不代表实机。document hidden 引起 rAF/鼠标等待超时；最终使用原生 DOM 按钮与暂停/恢复取得新快照，没有替换前端状态。前台鼠标/键盘覆盖不在本轮声明中，详见 qa/browser-validation-notes.md。
6. 同步到 mtc_webui 命名空间，colcon 构建安装包并重复相同 Python/P1 ROS 检查；28 个安装文件逐字节匹配，Node 文件不作为 package_data 安装。累计补丁在原始 PR8 应用后逐字节相同；结束时 PR8 head 变化但整树相同。
7. 停止测试 ROS、转发和专用容器，保留无 ROS domain 的只读 localhost:8772 预览。keeper 的 137 与 ROS 进程正常关闭分开；失败、重试、旧 P0 冻结不删除或覆盖。

原始运行目录见 inputs/manifest；依赖下载失败后使用旧相机验证容器的只读快照创建新环境，没重启原容器。复现命令、源码哈希、安装映射和实际日志均在本目录。索引覆盖除 index.json 自身以外的全部文件，manifest 登记索引 SHA-256。

使用 OpenAI Codex 协助实现、测试、浏览器核验和文档登记。上游 MIT 许可见 sources/upstream-LICENSE；运行依赖许可与边界见 source-webui/provenance.json。原始下载未用于测试，未把历史 C1 注入显示回归记为实际内核修复。
''')
entries=[dict(path=str(p.relative_to(dest)),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(dest.rglob('*')) if p.is_file()]
dump(dest/'index.json',dict(schema_version=1,generated_at=stamp,files=entries,file_count=len(entries),total_bytes=sum(e['bytes'] for e in entries)))
p=Path('materials/manifest.json');manifest=json.loads(p.read_text())
assert not any(e['id']=='ENV-WEBUI-P1-20261013' for e in manifest['local_observations'])
links=['README.md','docs/current-status.md','docs/hardware-vision-plan.md','docs/open-questions.md','docs/web-ui.md','webui/README.md','webui/p1-contract.md','webui/provenance.json',str(dest/'protocol.md'),str(dest/'summary.json')]
manifest['local_observations'].append(dict(id='ENV-WEBUI-P1-20261013',kind='isolated_webui_p1_interface_validation',date='2026-10-13',observed_at=stamp,
    triggered_by=['USER-HW-20261013-02'],upstream_source='TEAMMATE-WEBUI-P1-20261013',report='docs/web-ui.md',index=str(dest/'index.json'),index_sha256=sha(dest/'index.json'),
    inputs=str(dest/'inputs.json'),summary=str(dest/'summary.json'),raw_output_directories=[str(run)],verification_status=summary['status'],observed=summary,
    method='Native Jazzy DDS synthetic fixture, offline/Node semantics, scoped browser DOM verification, installed-package repeat and byte identity; no hardware or kernel acceptance',
    algorithm_provenance='webui/provenance.json',scope_note='6 unique P1 ROS cases plus 5 P0 regressions; installed tests repeat the same cases. Real Planner/tool evidence publishers and physical RGB-D pending. Browser hidden/relay failures retained.',derived_files=links))
dump(p,manifest)
print(json.dumps(dict(directory=str(dest),files=len(entries),bytes=sum(e['bytes'] for e in entries),index_sha256=sha(dest/'index.json')),indent=2))
