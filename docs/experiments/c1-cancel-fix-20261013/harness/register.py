"""Append C1 evidence without replacing either workspace's existing facts or UI work."""
import hashlib,json,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
run=Path(__file__).resolve().parents[1]; project=run.parents[1];publication=run/'publication'
receipt=json.loads((run/'freeze-receipt.json').read_text());sha=receipt['fix_commit'];short=sha[:7]
evidence='docs/experiments/c1-cancel-fix-20261013';report='docs/c1-cancel-fix.md'
summary=json.loads((publication/evidence/'summary.json').read_text())
rows=json.loads((run/'container/fixed/summary.json').read_text())
pr=json.loads((run/'meta/pr8-after-push.json').read_text());assert pr['headRefOid']==sha and pr['state']=='OPEN'
user='USER-HW-20261013-03';source_id='TEAMMATE-CANCELFIX-20261013';env='ENV-CANCEL-FIX-20261013'
report_text=f'''# PR #8 C1 延迟取消修复与复验

**C1 已在软件 Mock 范围修复并复验通过。** 修复提交 `{sha}` 已更新到 [PR #8](https://github.com/F1u0rite/meituan_challenge_ws/pull/8)，仍待审、未合并。正常 Mock 的延迟取消现为父子 `CANCELED/0`、完成数 0；400 ms 档在同一栈取消后，新任务 `SUCCEEDED/0`、完成数 1。正式 pin 保持不变，完整 FSM/FJT、NUC 和实体设备仍未验收。来源：{user}（用户会话）、{source_id}（2026-10-13 查询）、{env}（本机隔离复验）。

## 根因与修改

原 PR head 为 `7da43228d602a6b23571bfc599d69529ef7bea23`。底层 Mock 运动即时完成，停稳证据仅保存一次；上层 Future 延迟 700 ms 交付时，PickPlace 的 10 ms 定时器每次仍推进 ManualClock 20 ms。400 ms 后证据龄期约 0.8 s，超过 Core 的 0.3 s 门限。新增确定性回归记录旧反馈 1.7 s、当前时间 2.5 s，原代码返回 520；真实父子 Action 同样复现，完成数 0，下一 Goal 被拒。

修复只增加 `MockMotionAdapter::sample_stationary_feedback(command_id)` 及 AsyncMockMotion 的调用。在适配器锁内读取当前虚拟关节状态，要求同一已知停稳命令、没有在途命令或队列、关节状态未变、采样时间有限且不倒退。保留命令身份和原停稳区间；取得新的虚拟观测后，仍由原 Core 判定。`stop_evidence()` 本身继续返回可能过期的快照。

MotionExecutorCore、0.3 s 新鲜度门限、FSM/ActionSlot/IDL 均未修改。缺失、未知、超时、错误 ID、带载取消与原过期快照负例继续保留。**这是 Mock 内部完整已知状态的显式采样，不是机械臂传感反馈，不能作为实机/FJT“刷新旧时间戳”的实现。** Cancel ACK 与停止完成继续分别判断。

## 实际验证

环境：Ubuntu 24.04.5 x86_64 / ROS 2 Jazzy / C++17，独立容器 2 CPU / 4 GiB，network=none，无设备、宿主挂载或端口映射，cap-drop ALL。首次从固定源构建 7 包，修改的两个包清理重编；[源码字节核验](experiments/c1-cancel-fix-20261013/meta/source-integrity.json)覆盖 225 个编译相关文件。新采样符号和编译前后二进制哈希均保存。

- 旧代码反证：2 个延迟取消正例失败、1 个缺证反例通过；独立父子 Action 重现 ACK 后 `ABORTED/520` 并拒绝下一任务。
- 修复版：**365 项实际 C++ 测试通过**，无失败、错误或跳过；包括原有 358 项和新增 7 项。322 项 Core/Mock、43 项 Action；colcon 加入 20 个包装项显示 385，不重复计为功能用例。
- 原 `StaleFeedbackCannotConfirmStop` 仍通过拒绝断言；新增错误 ID、启动/在途无证据、未知/超时、倒退和非有限时钟测试通过。

以下全部经实际安装的 C++ Task → PickPlace，保存父子 UUID、真实 Feedback/Result、ACK、只读就绪图、日志和清理；没有注入或修改 Result：

| 配置 | 取消延迟 | 结果交付延迟 | 父子终态 | 后续任务 |
| --- | ---: | ---: | --- | --- |
'''
for row in rows:
    delay='不取消' if row['delay_ms'] is None else str(row['delay_ms'])+' ms'
    terminal={5:'CANCELED',6:'ABORTED'}[row['task']['final']['status']]
    follow=row.get('followup',{}).get('final')
    next_task='未另发' if follow is None else ('拒绝' if follow['status']=='REJECTED' else '同栈 SUCCEEDED/0，完成 1')
    report_text+=f"| {row['profile']} | {delay} | {row['result_delay_ms']} ms | {terminal}/{row['task']['final']['result']['error_code']}，完成 0 | {next_task} |\n"
normal=next(r for r in rows if r['delay_ms']==400 and r['profile']=='success')
report_text+=f'''
400 ms 正例父 UUID `{normal['task']['final']['goal_id']}`，子 `{normal['child']['goal_id']}`；同栈新 Goal `{normal['followup']['final']['goal_id']}`。完整结果见 [summary.json](experiments/c1-cancel-fix-20261013/summary.json)，逐场景结果见 `container/fixed/`。所有七个修复场景的 supervisor、Task、PickPlace 均退出 0，图排空。

## 复现

采用 [修复提交内 SOP](https://github.com/F1u0rite/meituan_challenge_ws/blob/{sha}/docs/migration/C1_DELAYED_CANCEL_FIX_20261013.md)，构建并加载 Jazzy 工作空间。在两个终端使用同一 ROS domain 和全新输出目录：

```bash
ros2 run mtc_cpp_mock_bringup mock_stack --namespace /c1_repro \\
  --output-dir /tmp/c1-stack-001 --result-delay-ms 700 --no-web
```

```bash
ros2 run mtc_cpp_mock_bringup mock_task --namespace /c1_repro \\
  --output-dir /tmp/c1-client-001 --cancel-at MOVE_PRE_ALIGN \\
  --cancel-delay-ms 400 \\
  --goal '{{"task_id":"c1_repro_001","mode":1,"ordered_colors":[1],"timeout_ms":30000,"placement_stability_sec":3}}'
```

应分别检查 ACK 与最终父子 `CANCELED/0`，CLI exit 0 本身只代表取得终态。自动化宿主直接启动安装的 mock_stack 可准确向 supervisor 发送信号；不要只给 `ros2 run` 外层进程发 SIGINT。

## 失败保留与清理

初次基线外部测试给 ros2 CLI 包装进程发 SIGINT 未转发，随后限时终止 wrapper，原 summary 为 CLEANUP_FAIL；真实 C++ 子节点随后退出 0、supervisor 生成 cleanup_ok。该尝试原样留存。改为直接启动安装的 supervisor 后，另存 baseline-clean，再做修复对照；没有修改 Bringup 的清理代码。

首次补丁增量构建因为复制保留的 mtime 早于旧对象而跳过编译。它不计入修复验证；之后以 `--cmake-clean-first` 重编并核验符号、二进制及源文件。两个过程日志都保留。

所有场景结束后，本轮容器已停止、OOMKilled=false。PID1 为 sleep infinity，容器最终 exit 137 单独记录，不计作 C++ 崩溃；初次 wrapper 留下的僵尸随本轮容器停止清理。没有恢复旧监测或操作其他容器。原 [C1 失败报告](cpp-mock-webui-acceptance.md) 与全部冻结证据保持原记录。

冻结目录含 **{receipt['file_count']} 个索引成员**；[index.json](experiments/c1-cancel-fix-20261013/index.json) SHA-256：`{receipt['index_sha256']}`。源码补丁、7 项新增测试、原失败、完整测试身份和构建记录均在冻结目录。

本次范围止于 PR #8 软件 Mock C1；未验证新浏览器交互，不关闭 M1/FJT 并发、旧 Python 220/510/520、MoveIt 退出、NUC/实机或完整 FSM 问题。既有 Web UI P0 暂存改动保留，未并入本次 PR。

使用 OpenAI Codex 协助根因定位、最小 Mock 补丁、正负回归、日志与文档归档。补丁基于队友仓库根 MIT 代码，原 package.xml/SDK 许可证与厂商校验边界不变；没有重新授权第三方内容。
'''
intro=f'**C1 修复（2026-10-13）：** PR #8 已更新 `{short}`；365 项 C++ 与七个真实父子 Action 正负场景通过，五档正常延迟取消均 `CANCELED/0`，400 ms 后同栈下一任务成功。缺证据/未知状态仍保持 520/230 和锁定。仅关闭软件 Mock C1，旧失败证据保留；未合并、未推进正式 pin、未验收实机。见 [修复报告](c1-cancel-fix.md)（{env}；{user}）。'
paths=['README.md','docs/current-status.md','docs/open-questions.md','docs/hardware-vision-plan.md','docs/cpp-mock-webui-acceptance.md',report,evidence+'/protocol.md',evidence+'/inputs.json',evidence+'/summary.json']
for root in [publication,project]:
    (root/report).write_text(report_text)
    for name in paths[:5]:
        p=root/name;s=p.read_text();assert env not in s,(p,'already updated')
        note=intro.replace('(c1-cancel-fix.md)','(docs/c1-cancel-fix.md)') if name=='README.md' else intro
        if name.endswith('cpp-mock-webui-acceptance.md'):
            note=f'后续更新：2026-10-13 已完成软件 Mock C1 修复与复验，见 [新报告](c1-cancel-fix.md)（{env}）。下文是 2026-10-12 的原始失败和交付记录，保留原结论与证据。'
        first,rest=s.split('\n',1);s=first+'\n\n'+note+'\n'+rest
        if name=='README.md':s=s.replace('后续需关闭C1取消完成边界、验证完整MoveIt/FJT链路','软件 Mock C1 已修复复验，后续需验证完整 MoveIt/FJT 链路')
        if name=='docs/open-questions.md':s+=f'\n## 2026-10-13 C1 修复后的实验缺口\n\n{user} 明确授权定向解决 C1。{source_id} / {env} 记录新补丁和 365 项 C++、五档真实延迟取消、两项故障反例及同栈后续成功。C1 在 PR #8 软件 Mock 范围关闭，旧 520 保留为原版本失败；独立新采样没有放宽 Core 门禁。Q18/Q19 仍部分确认，完整 FSM/FJT、独立真实停稳、故障恢复及 NUC/实机待验，其他 M1/旧 Python/MoveIt 问题未关闭。\n'
        p.write_text(s)
    p=root/'materials/manifest.json';data=json.loads(p.read_text());assert not any(x['id']==user for x in data['project_decisions'])
    data['project_decisions'].append(dict(id=user,kind='user_message',date='2026-10-13',source='本项目用户会话',original_text='解决：PR #8 的 C1 延迟取消再次受理后返回 ABORTED/520',confirmed={'scope':'授权解决 PR #8 C1：必要的定向代码修复、回归验证和事实链更新'},scope_note='仅限 C1 软件 Mock 问题，不授权自动合并/推进正式 pin/实机运动，也不变更既有其他内核问题的负责人。新授权区别于先前 UI 显示 520 的范围。',derived_files=paths))
    data['external_references'].append(dict(id=source_id,kind='github_pr8_c1_fix_candidate',title='PR #8 软件 Mock C1 定向修复',url=pr['url'],accessed_on='2026-10-13',commit=sha,base_commit=summary['base_commit'],branch=pr['headRefName'],state=pr['state'],scope_note='本项目提交并复验的候选补丁；尚未合并，不是维护者批准或实体停稳证明。',derived_files=paths))
    data['local_observations'].append(dict(id=env,kind='isolated_mock_c1_fix_regression',date='2026-10-13',triggered_by=[user],upstream_source=source_id,commit=sha,report=report,index=evidence+'/index.json',index_sha256=receipt['index_sha256'],inputs=evidence+'/inputs.json',summary=evidence+'/summary.json',verification_status=summary['status'],observed={'cpp_cases':365,'added_cases':7,'failures':0,'positive_delays_ms':[0,200,400,600,1000],'positive_parent_child':'CANCELED/0/completed=0','same_stack_followup':'SUCCEEDED/0/completed=1','negative_cases':['ABORTED/520 + next rejected','ABORTED/230 + next rejected'],'container_stopped':True,'formal_pin_unchanged':True},method='Baseline failing regression and real 700/400ms parent-child counterexample; clean two-package rebuild, 225 source file hash matches, all five related C++ packages, seven independent-process actual Action scenarios and owned cleanup.',scope_note='Software Mock only. No new browser, actual FJT, hardware, M1 or old Python verification. Original failures unchanged, no PR merge or formal pin advance.',algorithm_provenance={'upstream':source_id,'license':'Upstream MIT root; existing package/SDK license differences retained','ai_assistance':'OpenAI Codex; explicit Mock sampler, asynchronous bridge call, seven tests, bounded external regression and traceable documentation'},derived_files=paths))
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
# Make local report links work without adding or changing the pre-existing index.
shutil.copytree(publication/evidence,project/evidence)
print(report,sha,receipt['index_sha256'])
