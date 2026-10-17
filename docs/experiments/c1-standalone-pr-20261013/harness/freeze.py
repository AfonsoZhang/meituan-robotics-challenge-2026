"""Freeze the standalone main-based C1 validation without touching prior evidence."""
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

run = Path(__file__).resolve().parents[1]
project = run.parents[1]
publication = project / 'outputs/c1-cancel-fix-20261013/publication'
source = run / 'source'
base = 'b4185155383541e1a4161587c4049a162f74b36d'
evidence = 'docs/experiments/c1-standalone-pr-20261013'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def git(*args):
    return subprocess.check_output(['git', '-C', str(source), *args], text=True)


commit = git('rev-parse', 'HEAD').strip()
assert not git('status', '--porcelain'), 'commit source before freezing'
assert git('rev-parse', 'HEAD^').strip() == base
tests = json.loads((run / 'meta/test-identities.json').read_text())
assert tests['cases'] == 366 and tests['failed'] == tests['errors'] == tests['skipped'] == 0
assert any(c['name'] == 'DelayedCancelWaitsForChildStopThenAllowsNextTask'
           for c in tests['identities'])
assert json.loads((run / 'meta/build.json').read_text())['exit_code'] == 0
assert 'Summary: 386 tests, 0 errors, 0 failures, 0 skipped' in (run / 'logs/tests.log').read_text()
pr = json.loads((run / 'meta/standalone-pr.json').read_text())
assert pr['headRefOid'] == commit and pr['state'] == 'OPEN' and pr['baseRefName'] == 'main'
stopped = json.loads((run / 'meta/isolation-stopped.json').read_text())[0]
assert not stopped['State']['Running'] and not stopped['State']['OOMKilled']
changed = git('diff', '--name-only', base, commit).splitlines()
assert len(changed) == 9 and all(
    p.startswith(('src/mtc_motion_execution_cpp/', 'src/mtc_ros2_action_cpp/'))
    or p == 'docs/migration/C1_DELAYED_CANCEL_FIX_20261013.md' for p in changed)
dest = publication / evidence
dest.mkdir(parents=True, exist_ok=False)
for directory in ['container', 'harness', 'logs', 'meta']:
    for path in sorted((run / directory).rglob('*')):
        if not path.is_file() or path.is_symlink() or '__pycache__' in path.parts:
            continue
        target = dest / path.relative_to(run)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
for name in changed:
    target = dest / 'source' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / name, target)
(dest / 'source.patch').write_text(git('diff', '--binary', base, commit))
summary = dict(
    source_id='ENV-CANCEL-PR-20261013', status='STANDALONE_C1_MAIN_BASED_REGRESSION_PASSED',
    base_commit=base, fix_commit=commit, pull_request=pr['url'],
    tests={k: v for k, v in tests.items() if k != 'identities'},
    colcon_total_including_wrappers=386, added_cpp_tests=8,
    built_packages=6, tested_packages=5,
    added_parent_regression='700 ms result delivery / 400 ms delayed cancel: CANCELED/0, completed=0; same stack next task SUCCEEDED/0, completed=1',
    original_combination_evidence=dict(
        source_id='ENV-CANCEL-FIX-20261013', commit='062811ed2895eadc8b41efe8a8d7b2acff03fe92',
        cpp_cases=365, independent_process_cases=7,
        relation='same three runtime files and original three regression files, plus PR #8 integration; not represented as runs of the standalone commit'),
    pr8_withdrawal=dict(
        commit='8f11750e0bd2e485826acb904fd31382945ba0b9',
        tree_identical_to='7da43228d602a6b23571bfc599d69529ef7bea23'),
    preserved=['Core validators and freshness threshold', 'FSM/ActionSlot/IDL',
               'missing/unknown/timeout and stale snapshot rejection', 'carrying admission lock'],
    not_verified=['real FJT/MoveIt/NUC/hardware', 'browser or complete FSM integration'],
    formal_pin_unchanged=True, container_stopped=True, ai_assistance='OpenAI Codex')
write(dest / 'summary.json', summary)
write(dest / 'inputs.json', dict(
    source_ids=['USER-HW-20261013-03', 'TEAMMATE-CANCELPR-20261013'],
    base_commit=base, fix_commit=commit, changed_files=changed,
    environment='Ubuntu 24.04.5 x86_64 / ROS 2 Jazzy / C++17; fresh isolated container, 2 CPU / 4 GiB, network=none, no device/mount/port mapping',
    image='mtc-cpp-webui-base:20261012', image_inspect='meta/isolation-start.json',
    source_integrity='meta/source-integrity.json', scope='Standalone C1 software Mock patch; no Bringup/Web UI code'))
(dest / 'protocol.md').write_text('''# C1 独立 PR 的 main 基线复验

来源：USER-HW-20261013-03（用户会话要求单独提交、单独推送 PR），TEAMMATE-CANCELPR-20261013（独立候选），ENV-CANCEL-PR-20261013（本机复验）。

1. 基于 main b418515 新建分支，只迁移 C1 的三个运行源码文件、三个原回归文件和文档。PR #8 使用普通 revert 撤出 C1，其源码树恢复到原 7da4322；没有改写历史。
2. 新增父任务真实 Action 回归：700 ms 结果交付、MOVE_PRE_ALIGN 后等待 400 ms 再取消，检查父任务 CANCELED/0、完成数 0、单次执行/停止；同栈新 Goal 必须 SUCCEEDED/0、完成数 1。
3. 在全新 Jazzy 容器构建六包，测试五个 Core/Mock/Action 包；从 gtest XML 统计 366 个真实用例，与 colcon 386（含 20 包装项）分开。原缺证、未知/超时、过期、错误身份、带载锁定负例保留。
4. 核验容器内编译相关源码与提交一致，保存二进制哈希和完整测试身份。先前 PR #8 组合的 365 项测试及七个独立进程场景作为单独历史证据，不冒充本分支运行。
5. 停止本轮容器，记录 OOM 状态、自有进程和 PR head。冻结本目录，不修改原证据；不合并 PR 或推进正式 pin。

使用 OpenAI Codex 协助定向补丁、验证和文档归档。软件 Mock 观测不代表实机停稳证明。
''')
files = [dict(path=str(p.relative_to(dest)), sha256=sha(p), size=p.stat().st_size)
         for p in sorted(dest.rglob('*')) if p.is_file()]
write(dest / 'index.json', dict(source_id=summary['source_id'],
      created_at=datetime.now(timezone.utc).isoformat(), files=files))
receipt = dict(directory=str(dest), index_sha256=sha(dest / 'index.json'),
               file_count=len(files), fix_commit=commit, pull_request=pr['url'])
write(run / 'freeze-receipt.json', receipt)
assert not (project / evidence).exists()
shutil.copytree(dest, project / evidence)
print(json.dumps(receipt, ensure_ascii=False))
