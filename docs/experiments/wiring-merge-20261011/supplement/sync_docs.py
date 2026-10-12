from pathlib import Path
p=Path('README.md');s=p.read_text();lines=s.splitlines()
for i,line in enumerate(lines):
 if line.startswith('**接线补丁已提交审阅：**'):
  lines[i]='**接线补丁已由上游合并：** USER-HW-20261011-05 授权的 B01/B02/B04 补丁 `1d3dccf…` 已作为 [PR #2](https://github.com/F1u0rite/meituan_challenge_ws/pull/2) 合入 23:35 的 `main@c10f6ed…`（TEAMMATE-MERGE-20261011）。本项目复验 13 包构建、358 C++ / 269 Python / 15 Mock E2E、6 项 ROS 接线及 C++ 独立四场景通过；旧 Python Task 虽可受理 Goal，B03/B05/B06 仍阻断任务。独立 MoveIt 两次规划执行通过、退出失败，其中控制器 -11 出现一次。见[合并后验收](docs/wiring-merge-acceptance.md)（ENV-WIRING-MERGE-20261011）；[原补丁复验](docs/fsm-wiring-fix.md)及失败证据保留（ENV-FSM-FIX-20261011）。本项目未执行此次合并，正式基线仍为 `1d940f7…`。'
s='\n'.join(lines)+'\n'
s=s.replace('下一步复核 B01/B02/B04 修复 PR，并由模块负责人处理 B03/B05/B06 后复跑基础 Goal（ENV-FSM-FIX-20261011）；','B01/B02/B04 已由上游合并且复验通过，旧 Python B03/B05/B06 留存为未解决路径（ENV-FSM-FIX-20261011；ENV-WIRING-MERGE-20261011）；')
s=s.replace('- [C++ Action Mock 候选验收]', '- [PR #2 合并后验收](docs/wiring-merge-acceptance.md)：合并事实、六项 ROS 回归、C++ Mock 复验与两次 MoveIt 退出观测。\n- [C++ Action Mock 候选验收]',1)
p.write_text(s)
p=Path('docs/fsm-wiring-fix.md');s=p.read_text()
s=s.replace('已请求仓库负责人 `F1u0rite` 审阅，尚未合并；正式基线仍为 `1d940f7…`，','原 17:25 提交时已请求仓库负责人 `F1u0rite` 审阅、尚未合并；该状态为历史快照。后续 23:35 上游已合并，见文末追踪；正式基线仍为 `1d940f7…`，',1)
s+='\n## 后续合并追踪（23:35）\n\n监测在上游 `main` 发现合并提交 `c10f6ed59966401684851f917f9137b0a6cf12ae`，双父提交包含本补丁 `1d3dccf…` 与 C++ Action 交付 `c0f7017…`；两个 Python 文件、六项测试和复验说明均与原 PR 相同（TEAMMATE-MERGE-20261011）。合并后的六项 ROS 回归再次通过，但实际旧 Python 尽早/延迟/取消任务分别 ABORTED / 220、510、520，B03/B05/B06 不据合并关闭。新 C++ 独立四场景另行通过，独立 MoveIt 退出仍失败，见[本次验收](wiring-merge-acceptance.md)（ENV-WIRING-MERGE-20261011）。原 ENV-FSM-FIX-20261011 的 OPEN 快照、失败与冻结索引不改写；本项目未代为合并或推进锁定。\n'
p.write_text(s)
p=Path('robot/README.md');s=p.read_text()
s=s.replace('该 PR 尚未合并，下面的正式版本锁定未推进。','后续上游已在 `c10f6ed…` 合并该 PR，六项 ROS 回归再次通过；新 C++ 独立四场景通过，旧 Python 仍失败，见[合并后验收](../docs/wiring-merge-acceptance.md)（TEAMMATE-MERGE-20261011；ENV-WIRING-MERGE-20261011）。本项目未执行合并，下面的正式版本锁定未推进。')
p.write_text(s)
p=Path('docs/hardware-vision-plan.md');s=p.read_text()
s=s.replace('并请求仓库负责人 `F1u0rite` 审阅；尚未合并，正式基线未推进。','原提交时请求仓库负责人 `F1u0rite` 审阅；后续上游已在 `c10f6ed…` 合并（TEAMMATE-MERGE-20261011），本项目正式基线未推进。')
s+='\n### 8. 23:35 合并候选的复验补充\n\nPR #2 已由上游合入 `main@c10f6ed…`，记录于 TEAMMATE-MERGE-20261011；本地锁定继续为 `1d940f7…`。I01 本次 13 包 / 358 C++ / 269 Python / 15 Mock E2E 及 6 项 ROS 回归通过；I02/I04/I05 的现有 C++ 默认程序、唯一 Action 服务器、基础/序列/取消/失败锁定四场景再次通过，仍为 Mock 端口，未新交付统一 Bringup 或 MoveIt/FJT 接线（ENV-WIRING-MERGE-20261011）。UBSan 和外部 consumer 只引用前轮 ENV-CPP-ACTION-20261011，不重复计为本次运行。\n\n旧 Python 任务仍 ABORTED / 220、510、520；独立 MoveIt 两次 Plan → Execute 通过而 move_group 两次 -11，原固定运行的 ros2_control_node 另有一次 -11、补跑未再现。维护者合并说明建议后续关注 C++ Mock Bringup，是上游交接信息，本事件未据此另行启动开发或改变 FSM/Action/Cancel 分工。完整轨迹、状态来源、Web UI、实体停稳与 NUC/实机待验；[合并后报告](wiring-merge-acceptance.md)保存结果和交接，原失败不覆盖。\n'
p.write_text(s)
p=Path('docs/open-questions.md');s=p.read_text();lines=s.splitlines()
for i,line in enumerate(lines):
 if line.startswith('| Q18'):
  line=line.replace('；未合并或推进基线，','；本项目未执行合并或推进基线，')
  line=line.replace('见[候选验收](cpp-action-acceptance.md) |','见[候选验收](cpp-action-acceptance.md)。随后上游 `main@c10f6ed…` 已合入 PR #2，六项 ROS 接线回归与 C++ 四场景再次通过（TEAMMATE-MERGE-20261011；ENV-WIRING-MERGE-20261011） |')
  lines[i]=line
 if line.startswith('| Q17'):
  lines[i]=line[:-1]+'；合并候选复跑还观察到 ros2_control_node 退出 -11，第二轮未再现，尚不能关闭；move_group 两次 -11（ENV-WIRING-MERGE-20261011） |'
s='\n'.join(lines)+'\n'
s+='\nPR #2 合并后复验（TEAMMATE-MERGE-20261011；ENV-WIRING-MERGE-20261011）：上游 23:35 的 `c10f6ed…` 完整保留三项接线补丁，六项 ROS 回归通过；旧 Python 尽早/延迟/取消 Goal 分别 ABORTED / 220、510、520，B03/B05/B06 保留。新 C++ Action 代码未变，独立四场景通过；没有统一 Bringup 或完整 MoveIt/轨迹交付。独立 MoveIt 原运行与补跑均规划执行成功、move_group 退出 -11，控制器原运行另有 -11、补跑为 0，根因和退出修复待验。维护者转向 C++ Bringup 的建议作为上游交接记录，不当作本事件的新增开发授权。清理与冻结证据见[报告](wiring-merge-acceptance.md)，正式锁定未推进。\n'
p.write_text(s)
p=Path('docs/upstream-monitor.md');s=p.read_text()
s+='\n## PR #2 合并事件\n\n后续 `main@c10f6ed…` 合并了原三项 Python 接线补丁（TEAMMATE-MERGE-20261011）。固定入口已实际运行六项 ROS 回归并通过；主对话补跑新 C++ 身份核验、四组独立程序及一次独立 MoveIt 退出复核，见[合并后验收](wiring-merge-acceptance.md)（ENV-WIRING-MERGE-20261011）。普通构建/回归通过，旧 Python Task 三场景仍失败；独立 MoveIt 两次规划执行通过而退出失败，控制器 -11 一次出现、一次未再现。没有改动当前固定监测工具、另启监测或重复 queue；原失败与每次 SHA 的门禁状态分别保存。\n'
p.write_text(s)
print('Seven documents synchronized; original frozen evidence and signed Phase 2A report unchanged')
