"""Register standalone delivery while retaining original C1 and concurrent UI facts."""
import copy
import json
from pathlib import Path

run = Path(__file__).resolve().parents[1]
project = run.parents[1]
publication = project / 'outputs/c1-cancel-fix-20261013/publication'
receipt = json.loads((run / 'freeze-receipt.json').read_text())
pr = json.loads((run / 'meta/standalone-pr.json').read_text())
sha = receipt['fix_commit']
number, url = pr['number'], pr['url']
evidence = 'docs/experiments/c1-standalone-pr-20261013'
report = 'docs/c1-cancel-fix.md'
env, source_id, user = 'ENV-CANCEL-PR-20261013', 'TEAMMATE-CANCELPR-20261013', 'USER-HW-20261013-03'
paths = ['README.md', 'docs/current-status.md', 'docs/open-questions.md',
         'docs/hardware-vision-plan.md', 'docs/cpp-mock-webui-acceptance.md', report,
         evidence + '/protocol.md', evidence + '/inputs.json', evidence + '/summary.json']
intro = (f'**C1 独立修复（2026-10-13）：** 已单独提交并推送 [PR #{number}]({url})（`{sha[:7]}`，基于 main）；'
         '独立分支 366 项 C++ 用例通过，700/400 ms 延迟取消后同栈新任务成功。'
         '此前 PR #8 组合另有 365 项测试及七个独立进程场景通过。C1 补丁已从 PR #8 撤出，原内容保留。'
         '修复限软件 Mock，未合并、未推进正式 pin；旧失败证据保留。'
         f'见 [修复报告](c1-cancel-fix.md)（{env}；{user}）。')
text = (publication / report).read_text()
old_intro = next(line for line in text.splitlines() if line.startswith('**C1 已在'))
text = text.replace('# PR #8 C1 延迟取消修复与复验', '# C1 延迟取消的独立修复 PR 与复验', 1)
text = text.replace(old_intro,
    f'**C1 已单独提交并推送 [PR #{number}]({url})。** 候选提交 `{sha}` 基于 main '
    '`b4185155383541e1a4161587c4049a162f74b36d`，仍待审、未合并。正常软件 Mock 的延迟取消返回 '
    '`CANCELED/0`，同栈再次受理的新任务成功；独立分支 366 项 C++ 用例通过。用户后续明确“单独提交”“单独推送PR”，'
    '因此先前组合提交 `062811e` 已通过普通 revert `8f11750` 从 PR #8 撤出，PR #8 源码树与原 `7da4322` 相同。'
    f'来源：{user}（用户会话）、{source_id}（2026-10-13 查询）、{env}（本机独立复验）；'
    '原组合记录继续使用 TEAMMATE-CANCELFIX-20261013 / ENV-CANCEL-FIX-20261013。正式 pin 保持不变，完整 FSM/FJT、NUC 和实体设备仍未验收。', 1)
standalone = f'''## 独立分支的 main 基线复验

在新的隔离 Jazzy 容器中，从 main 构建六包并测试五个相关 C++ 包：**366 项实际用例通过**（322 Core/Mock + 44 Action，新增 8 项），无失败、错误或跳过。colcon 含 20 个包装项显示 386。源文件与容器字节核验、二进制哈希和完整测试身份见 [独立复验摘要](experiments/c1-standalone-pr-20261013/summary.json)。

独立分支额外加入 `TaskAction.DelayedCancelWaitsForChildStopThenAllowsNextTask`：真实父子 Action 在结果交付延迟 700 ms、移动 Feedback 后等 400 ms 取消，父任务最终 CANCELED/0、完成数 0、执行/停止各一次；同栈下一任务 SUCCEEDED/0、完成数 1。该测试不依赖 PR #8 的 Bringup 或 Web UI。三个运行源码文件及原三个回归文件与先前组合补丁逐字相同；本分支再增加父任务回归。

本次独立 PR 只有三个运行源码文件、四个测试文件、包 README 和修复说明；无 Bringup/Web UI 改动。容器已停止，OOMKilled=false。冻结目录含 **{receipt['file_count']} 个索引成员**；[index.json](experiments/c1-standalone-pr-20261013/index.json) SHA-256：`{receipt['index_sha256']}`。

## 原 PR #8 组合复验（单独保留）

下列 365 项测试及七个独立进程场景运行于 `062811ed2895eadc8b41efe8a8d7b2acff03fe92`（C1 + 原 PR #8），不是独立 PR 提交的运行结果。原冻结目录和索引哈希保持不变。
'''
text = text.replace('## 实际验证\n', standalone, 1)
old_repro = '采用 [修复提交内 SOP](https://github.com/F1u0rite/meituan_challenge_ws/blob/062811ed2895eadc8b41efe8a8d7b2acff03fe92/docs/migration/C1_DELAYED_CANCEL_FIX_20261013.md)，构建并加载 Jazzy 工作空间。在两个终端使用同一 ROS domain 和全新输出目录：'
text = text.replace(old_repro, f'''独立分支按 [提交内 SOP](https://github.com/F1u0rite/meituan_challenge_ws/blob/{sha}/docs/migration/C1_DELAYED_CANCEL_FIX_20261013.md) 构建和运行回归：

```bash
colcon build --packages-up-to mtc_ros2_action_cpp --executor sequential \\
  --cmake-args -DBUILD_TESTING=ON -DCMAKE_CXX_STANDARD=17
source install/setup.bash
colcon test --packages-select mtc_motion_execution_cpp mtc_ros2_action_cpp \\
  --executor sequential --event-handlers console_direct+
colcon test-result --verbose
```

以下 CLI 需要组合原 PR #8 与本补丁，或使用已冻结组合提交 `062811e`；独立 PR 本身不提供 Bringup CLI。加载对应 Jazzy 工作空间后，在两个终端使用同一 ROS domain 和全新输出目录：''', 1)
text = text.replace('本次范围止于 PR #8 软件 Mock C1；', '本次范围止于原 PR #8 发现的软件 Mock C1；')
text = text.replace('既有 Web UI P0 暂存改动保留，未并入本次 PR。', '既有 Web UI P0 暂存内容和 P1 工作保留，未并入本次独立 PR。')

new_reference = dict(id=source_id, kind='github_standalone_c1_fix_candidate',
    title='C1 延迟取消独立修复 PR', url=url, accessed_on='2026-10-13', commit=sha,
    base_commit='b4185155383541e1a4161587c4049a162f74b36d',
    branch=pr['headRefName'], state=pr['state'],
    scope_note='独立 main 基线的单提交 C1 候选；PR #8 已用 revert 撤出旧组合补丁。未合并，非实机停稳证明。',
    derived_files=paths)
new_observation = dict(id=env, kind='isolated_standalone_c1_regression', date='2026-10-13',
    triggered_by=[user], upstream_source=source_id, commit=sha, report=report,
    index=evidence + '/index.json', index_sha256=receipt['index_sha256'],
    inputs=evidence + '/inputs.json', summary=evidence + '/summary.json',
    verification_status='STANDALONE_C1_MAIN_BASED_REGRESSION_PASSED',
    observed=dict(cpp_cases=366, added_cases=8, failures=0, errors=0, skipped=0,
        built_packages=6, tested_packages=5,
        delayed_parent_cancel='700/400 ms: CANCELED/0/completed=0',
        same_stack_followup='SUCCEEDED/0/completed=1',
        container_stopped=True, formal_pin_unchanged=True),
    method='Fresh main-based six-package build; five-package gtest XML identities; additional actual parent/child delayed cancel and next-task regression; byte-verified source and isolated cleanup.',
    scope_note='Software Mock only. The original 365-test/seven-process PR8-combination run stays under ENV-CANCEL-FIX-20261013; it is not relabeled as a run of this commit. No hardware/full FSM/FJT validation.',
    algorithm_provenance=dict(upstream=source_id, license='Upstream MIT root; existing package/SDK license differences retained',
        ai_assistance='OpenAI Codex; explicit Mock sampler, bridge call, eight regressions and traceable documentation'),
    derived_files=paths)
for root in [publication, project]:
    (root / report).write_text(text)
    for name in paths[:5]:
        path = root / name
        old = path.read_text()
        note = intro.replace('(c1-cancel-fix.md)', '(docs/c1-cancel-fix.md)') if name == 'README.md' else intro
        if name.endswith('cpp-mock-webui-acceptance.md'):
            note = (f'后续更新：软件 Mock C1 已单独修复并推送 [PR #{number}]({url})，见 [新报告](c1-cancel-fix.md)（{env}；ENV-CANCEL-FIX-20261013）。'
                    'PR #8 源码树已恢复原内容；下文保留 2026-10-12 的原始失败和交付记录。')
        lines = old.splitlines(keepends=True)
        found = 0
        for i, line in enumerate(lines):
            if line.startswith(('**C1 修复（', '后续更新：2026-10-13 已完成软件 Mock C1')):
                lines[i] = note + '\n'; found += 1
            elif line.startswith(user + ' 明确授权定向解决 C1。'):
                lines[i] = (f'{user} 授权定向解决 C1 并要求单独提交、单独推送 PR。{source_id} / {env} 记录 main 基线独立补丁及 366 项 C++ 通过；'
                    'TEAMMATE-CANCELFIX-20261013 / ENV-CANCEL-FIX-20261013 保留先前组合的 365 项测试、五档正常延迟取消、两项故障反例及同栈后续成功。'
                    'PR #8 的旧 520 和冻结证据保留；修复在独立候选分支通过，未放宽 Core 门禁。Q18/Q19 仍部分确认，完整 FSM/FJT、独立真实停稳、故障恢复及 NUC/实机待验，其他 M1/旧 Python/MoveIt 问题未关闭。\n')
        assert found == 1, (path, found)
        path.write_text(''.join(lines))
    path = root / 'materials/manifest.json'
    data = json.loads(path.read_text())
    decision = next(e for e in data['project_decisions'] if e['id'] == user)
    decision.setdefault('subsequent_resolutions', []).extend([
        dict(date='2026-10-13', source='本项目用户会话', original_text='单独提交',
             confirmed='C1 使用单独代码提交，不混入 Web UI P0/P1 工作。'),
        dict(date='2026-10-13', source='本项目用户会话', original_text='单独推送PR',
             confirmed=f'从 main 建立独立 C1 PR #{number}；旧 PR #8 通过普通 revert 撤出 C1，保留原内容。')])
    old_reference = next(e for e in data['external_references'] if e['id'] == 'TEAMMATE-CANCELFIX-20261013')
    old_reference['scope_note'] = ('062811e 是先前 C1 + PR #8 组合验证提交，已由 8f11750 从 PR #8 撤出；'
                                 f'运行证据不变。当前独立候选见 {source_id}。未合并，不是实体停稳证明。')
    old_reference['subsequent_resolutions'] = [dict(date='2026-10-13',
        withdrawal_commit='8f11750e0bd2e485826acb904fd31382945ba0b9', standalone_source=source_id)]
    for entry in [decision, old_reference,
                  next(e for e in data['local_observations'] if e['id'] == 'ENV-CANCEL-FIX-20261013')]:
        entry['derived_files'] = list(dict.fromkeys(entry['derived_files'] + paths))
    for section, entry in [('external_references', new_reference), ('local_observations', new_observation)]:
        assert not any(e['id'] == entry['id'] for e in data[section]), entry['id']
        data[section].append(copy.deepcopy(entry))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
print(url, sha, receipt['index_sha256'])
