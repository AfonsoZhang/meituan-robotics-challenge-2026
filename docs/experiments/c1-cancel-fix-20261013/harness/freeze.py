"""Freeze this C1 change only; retain old failure evidence byte-for-byte."""
import hashlib,json,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
run=Path(__file__).resolve().parents[1]
source=run/'source'; publication=run/'publication'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
commit=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
assert not subprocess.check_output(['git','-C',str(source),'status','--porcelain']), 'source not committed'
tests=json.loads((run/'meta/tests.json').read_text())
rows=json.loads((run/'container/fixed/summary.json').read_text())
assert len(rows)==7 and all(x['status']=='PASS' for x in rows)
dest=publication/'docs/experiments/c1-cancel-fix-20261013';dest.mkdir(parents=True,exist_ok=False)
for directory in ['container','harness','logs','meta']:
    for p in sorted((run/directory).rglob('*')):
        if not p.is_file() or p.is_symlink() or '__pycache__' in p.parts or p.name=='preexisting-index.patch':continue
        target=dest/p.relative_to(run);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
changed=subprocess.check_output(['git','-C',str(source),'diff','--name-only','7da4322',commit],text=True).splitlines()
for name in changed:
    target=dest/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,target)
(dest/'source.patch').write_bytes(subprocess.check_output(['git','-C',str(source),'diff','--binary','7da4322',commit]))
summary=dict(source_id='ENV-CANCEL-FIX-20261013',status='C1_SOFTWARE_MOCK_FIXED_AND_VERIFIED',base_commit='7da43228d602a6b23571bfc599d69529ef7bea23',fix_commit=commit,
    tests={k:v for k,v in tests.items() if k!='identities'},colcon_total_including_wrappers=385,added_cpp_tests=7,
    baseline={'regression_positive_failed':2,'regression_negative_passed':1,'parent_status':6,'child_status':6,'error_code':520,'next_goal':'REJECTED'},
    integration=[dict(case=x['profile']+'_delay_'+str(x['delay_ms']),profile=x['profile'],delay_ms=x['delay_ms'],result_delay_ms=x['result_delay_ms'],status=x['status'],parent=x['task']['final'],child=x['child'],followup=x.get('followup',{}).get('final'),cleanup=x['cleanup']) for x in rows],
    preserved_gates=['stale unsampled evidence','identity mismatch','unknown/timeout lock','unsupported cancellation','missing stop evidence','carrying/unknown-load admission'],
    not_verified=['real robot/NUC','complete FSM/MoveIt/FJT','browser end-to-end in this run','M1 FJT concurrency','old Python failures'],
    development_issues=['First ROS CLI wrapper did not forward SIGINT; cleanup recorded separately, bounded harness corrected to launch the installed supervisor directly. C++ nodes later exited zero and the original wrapper failure is retained.', 'Initial incremental build skipped older-mtime replacement source; clean-first rebuild and symbol/binary/source verification performed before any fixed test.'],
    ai_assistance='OpenAI Codex')
write(dest/'summary.json',summary)
write(dest/'inputs.json',dict(source_ids=['USER-HW-20261013-03','TEAMMATE-CANCELFIX-20261013'],base_commit=summary['base_commit'],fix_commit=commit,
  changed_files=changed,environment='Ubuntu 24.04.5 x86_64 / ROS 2 Jazzy / C++17; isolated network=none, 2CPU/4GiB, no mounts/ports/devices, cap-drop ALL',
  image='mtc-cpp-webui-base:20261012',image_inspect='meta/isolation-start.json',source_integrity='meta/source-integrity.json',
  scope='C1 offline Mock observation only; production Core/thresholds, FSM, ActionSlot and IDL unchanged',formal_pin=json.loads((run/'meta/initial-state.json').read_text())['formal_pin_sha256']))
(dest/'protocol.md').write_text('''# PR #8 C1 修复验证协议

来源：USER-HW-20261013-03（用户会话）、TEAMMATE-CANCELFIX-20261013（固定 PR 候选），本机证据 ENV-CANCEL-FIX-20261013。

1. 从 PR #8 的 7da4322 建立独立工作树和 Jazzy 容器；保存原暂存区哈希与正式 pin，保持原冻结证据。
2. 原运行代码仅加入回归测试：确定性桥接和真实 PickPlace 延迟取消正例必须失败为 520，缺失证据反例通过。实际父子 Action 700/400 ms 重现 6/520，下一任务被拒。首次 supervisor CLI 包装退出问题保留；改为直接调用安装的 supervisor 后单列 baseline-clean。
3. 只新增 Mock 显式采样方法及 AsyncMockMotion 调用；保留 Core 和旧 StaleFeedbackCannotConfirmStop 负例。新增匹配 ID、缺证、未知/超时、倒退/非法时钟和真实 PickPlace 回归。
4. 按 logs/fixed-clean-build.log 完全重编两个受影响包；检查导出符号、二进制哈希和全部编译相关源码字节，再运行五包 C++ 测试。colcon 包装数与实际 gtest 身份分开统计。
5. 独立进程串行验证五档取消延迟 0/200/400/600/1000 ms（结果交付 700 ms，最后一档 1500 ms）。所有父子实际终态须 5/0、完成数 0；400 ms 后同栈新任务 4/0/1。缺证 6/520、未知状态 6/230，均拒绝下一 Goal。只根据实际 Result 判断，不由 ACK 推断。
6. 每个场景核验关联 UUID、唯一就绪图、自有进程退出与图排空；停止本轮容器。冻结失败、通过、源码补丁和测试身份；不修改旧证据。

使用 OpenAI Codex 协助分析、补丁、回归与冻结。Mock 采样不是实机停稳证据；未合并 PR 或推进正式 pin。
''')
files=[dict(path=str(p.relative_to(dest)),sha256=sha(p),size=p.stat().st_size) for p in sorted(dest.rglob('*')) if p.is_file()]
write(dest/'index.json',dict(source_id=summary['source_id'],created_at=datetime.now(timezone.utc).isoformat(),files=files))
receipt=dict(directory=str(dest),index_sha256=sha(dest/'index.json'),file_count=len(files),fix_commit=commit)
write(run/'freeze-receipt.json',receipt)
print(json.dumps(receipt,ensure_ascii=False))
