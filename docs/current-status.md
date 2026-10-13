# 双仓库当前进度与验收边界

**C1 独立修复（2026-10-13）：** 已单独提交并推送 [PR #15](https://github.com/F1u0rite/meituan_challenge_ws/pull/15)（`8603e18`，基于 main）；独立分支 366 项 C++ 用例通过，700/400 ms 延迟取消后同栈新任务成功。此前 PR #8 组合另有 365 项测试及七个独立进程场景通过。C1 补丁已从 PR #8 撤出，原内容保留。修复限软件 Mock，未合并、未推进正式 pin；旧失败证据保留。见 [修复报告](c1-cancel-fix.md)（ENV-CANCEL-PR-20261013；USER-HW-20261013-03）。

**当前 Web UI 边界（2026-10-13）：** USER-HW-20261013-05 明确保留 HTTP API、只发送顶层 ExecuteTask Goal，其他模块只读接入，缺发布器预留未知值并等待负责人正式接口。联合验证只在 C++ Mock / GenericSystem Fake Hardware 中进行，不涉及真实机械臂控制。已有任务取消/软件停止保留，导出兼容字段补回；76 项本地 Python 检查通过（ENV-WEBUI-API-20261013）。见 [集中约定](../webui/README.md#接口边界与当前联调范围)及 [记录](web-ui.md)。

**Web UI P2（2026-10-13）：** 已实现八模块正常/异常/未知状态、TF/标定分开显示、Task/PickPlace/FJT 显式 UUID 追踪，以及按任务/Goal/模块查询、转换时间线、最近失败与完整已记录事件导出。未接入不显示绿色。73 Python / 30 Node / 6 P2 ROS、6 P1 ROS 与 5 P0 ROS 回归通过；真实标定及跨层 FJT 关联发布器仍待接入，不代表实机验收。[实现与证据](web-ui.md)、[接入契约](../webui/p2-contract.md)（USER-HW-20261013-04；TEAMMATE-WEBUI-P2-20261013；ENV-WEBUI-P2-20261013）。

**2026-10-13 P1 UI 增量：** USER-HW-20261013-02 明确视觉、Planner 与工具证据观察。原生 `/mtc/perception/batteries`、RGB-D 同帧时间与目标 ID 列表高亮已接入；Planner 和试提/落座消费接口已实现，但当前核对的 PR #4 `943bf37…`、PR #5 `dc76a0b…` 没有所需实时规划/工具验证发布器或二维框契约（TEAMMATE-WEBUI-P1-20261013）。实物 D435i、Planner 真发布器、独立工具证据、RViz/3D 仍未验收。完整结果见 [UI 报告](web-ui.md)，正式 pin 与 P0 停止语义不变。62 Python / 20 Node / 6 P1 ROS 与 5 P0 ROS 检查通过（ENV-WEBUI-P1-20261013）；安装命名空间同一 62/6 项重复检查通过。

**2026-10-13 UI 增量：** USER-HW-20261013-06 明确三项 P0 后，新客户端已实现任务/双 FSM、独立安全停止区、关节对比与只读 FJT；54 Python / 12 Node / 5 隔离 ROS 验证通过（ENV-WEBUI-P0-20261013），见 [UI 报告](web-ui.md)。原语/命令标识/预计总时长的执行端发布器仍待交付。只读核对 PR #8 仍为 `7da4322…` OPEN，Phase 2C PR #13 为 `22b0607…` OPEN（TEAMMATE-WEBUI-P0-20261013）；此次只测 UI 接口，不恢复旧 C1 或完整链路验收，正式 pin 不变。下文保留 10 月 12 日各候选的核对范围。

**2026-10-13 主线复验：部分通过，整体验收未通过。** 固定main `b418515` 的15包构建、普通/UBSan各486项C++、269项Python及15/6/54项补充检查通过；并发重复第18轮出现M1断言失败（179次执行通过、1次失败，首败即停）。真实C++ Task→PickPlace基础/序列/及时取消通过，独立PR8 `7da4322` 的C1延迟取消再次ACK后6/520；旧Python220/510/520、原生Status/执行权BLOCKED及MoveIt退出-11仍保留。正式pin不变，无实机验收。

这是用户重新授权后的x86_64/Jazzy实际运行，取代“尚未复验b418515”的当前状态；10月12日Mac终止准备及原签收证据仍按历史范围保留。PR8仍OPEN且未改代码，本轮只补C1/直接启动停止，不新增浏览器验收。源码、报告、日志与交接见[本轮验收](main-acceptance-20261013.md)（USER-HW-20261013，用户会话；TEAMMATE-MAIN-20261013；ENV-MAIN-ACCEPTANCE-20261013）。

## 2026-10-12 文档快照（历史，以下保留原范围）


核对时间：2026-10-12 16:27（UTC+8）。团队 main 为 `b4185155383541e1a4161587c4049a162f74b36d`，个人既有证据归档为 `6e040096986cdf0ea409943ae209d42507da7424`。这是 GitHub 源码、PR 状态与既有报告的文档核对，本轮没有构建或运行 ROS、Fake、仿真、NUC 或实机验收。后续变动须重新核对对应 SHA。

**当前结论：离线模块及部分 Mock 集成通过；完整 Task/PickPlace → MoveIt → FJT → Hardware 抓放闭环和实机仍未验收。** 团队首页此前停留在 Phase 2A；团队后续代码与报告已推进，个人独立复验则固定在不同历史提交，不能按仓库提交时间或测试总数排出统一的验收先后。

## 已合入团队 main

| 内容 | 上游记录 | 个人独立复验边界 |
| --- | --- | --- |
| Phase 2A C++ Action、规划 PR #3 | 已合并；Task → PickPlace 的 Mock Action 链已有测试，规划端口已交付 | 各固定提交报告保留；单独规划/执行成功不等于完整 FSM 闭环 |
| Calibration / TF / TCP PR #6 | 已合并；[标定报告](https://github.com/F1u0rite/meituan_challenge_ws/blob/b4185155383541e1a4161587c4049a162f74b36d/docs/calibration/TONIGHT_STATUS.md)记录 54 项离线测试，真实外参/TCP/工位仍待测 | 个人既有标定候选复验通过；真实安装与采样未验收 |
| Phase 2B 轨迹执行 PR #7 | 已在 main `b418515` 合并；[mutex 合并门禁报告](https://github.com/F1u0rite/meituan_challenge_ws/blob/b4185155383541e1a4161587c4049a162f74b36d/docs/migration/PHASE2B_ACTION_MUTEX_BACKPORT_GATE.md)记录普通/UBSan各486项通过，另有40轮×9项重复检查 | 个人报告固定在旧版 `681bb64`：首次61项套件超时，同二进制61项补跑及独立478项UBSan通过；本轮未复验新修复 |

486 是该报告所测 Phase 2B 候选的结果，不是本轮重测合并后 main。原生 GenericSystem 严格 Status 冷启动、标准 move_group 第二 FJT 客户端及完整联合执行仍是该 Phase 2B 报告的 BLOCKED；TSan 在测试前因环境错误退出，不能标为通过。报告中的“尚未 push/merge”是报告写作时的历史状态；本表以当前 GitHub 合并状态补充，不回写原报告。

## 待合并 PR 与独立分支

| 候选及核对版本 | 状态与报告范围 | 尚未关闭的边界 |
| --- | --- | --- |
| [PR #4](https://github.com/F1u0rite/meituan_challenge_ws/pull/4) `943bf37bec8fc35b510abe56a6844b3f6280cce4` | OPEN，未合并；上游记录40项规划GTest，V2、碰撞反证与场景隔离通过 | V1从home约39.59秒，超过24秒状态预算；个人未复验该最新版 |
| [PR #5](https://github.com/F1u0rite/meituan_challenge_ws/pull/5) `dc76a0bf0a43f9110f3d24cfa38a2b3478f48dcd` | Draft，未合并；个人已有离线/合成回放部分验收 | colcon零收集、默认零等待可靠性、真实FSM消费与实际相机输入仍未关闭 |
| [PR #8](https://github.com/F1u0rite/meituan_challenge_ws/pull/8) `7da43228d602a6b23571bfc599d69529ef7bea23` | OPEN，未合并；个人已验统一C++ Mock/UI、真实HTTP→ROS→Task→PickPlace、40项Action与39项UI及六项正负场景 | **C1未通过**：正常Mock延迟取消ACK受理，父/子最终ABORTED/520；不能将ACK作为取消完成 |
| [PR #9](https://github.com/F1u0rite/meituan_challenge_ws/pull/9) `9f6860d1edbbbd5a161703fbfe88e3d71caa29f8` | OPEN，叠在PR #4；上游记录V1从就绪位七段规划通过 | 从home仍约35.04秒超预算；就绪位规划成功不等于完整FSM执行，个人未复验 |
| [PR #10](https://github.com/F1u0rite/meituan_challenge_ws/pull/10) `748943efde2ada71a71d4ba49fc86fc6fb0155cc` | Draft提案，叠在PR #9，涉及V1策略/FSM；上游记录Fake规划两段接近合计19.68秒 | 待内核负责人审查安全参数与状态语义；未合并、未获个人独立复验，不能据此关闭main的V1阻断 |
| [PR #11](https://github.com/F1u0rite/meituan_challenge_ws/pull/11) `6c1d966c422ee858c4d23cc809743237c3d20c7f` | OPEN，相机底面贴圆盘端面的侧视试装文档；上游记录54项离线检查 | 当前外参仍UNKNOWN/null；旧安装数值不可用于新试装。本项目仅登记上游选择，现场测量与用户确认链另行补充 |
| [Phase 2C独立分支](https://github.com/F1u0rite/meituan_challenge_ws/tree/4a67503492e6bf0f678c6bbca04413e6c670ae30) `4a67503492e6bf0f678c6bbca04413e6c670ae30` | 未合入main；[报告](https://github.com/F1u0rite/meituan_challenge_ws/blob/4a67503492e6bf0f678c6bbca04413e6c670ae30/docs/migration/PHASE2C_P0_EXECUTION_OWNERSHIP_REPORT.md)记录510项普通/UBSan及受信任Fake冷启动下有限Planner→FJT→GenericSystem执行 | 完整Task/PickPlace、异步Cancel/停稳桥与实机未运行；move_group正常退出仍失败，个人未复验 |

不同分支、普通/UBSan、重复执行及CTest包装不累加为一个“整套系统通过”的测试总数。PR #8代码已在团队仓库，个人仓库保存[验收报告](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/blob/6e040096986cdf0ea409943ae209d42507da7424/docs/cpp-mock-webui-acceptance.md)与953文件冻结证据，两处是同轮交付，非两次独立通过。

## 环境与终止记录

团队[驱动手册](https://github.com/F1u0rite/meituan_challenge_ws/blob/b4185155383541e1a4161587c4049a162f74b36d/docs/setup/AUBO_ROS2_DRIVER_JAZZY.md)于2026-10-11记录独立Fake验证环境 **Ubuntu 24.04.4 LTS / x86_64 / ROS 2 Jazzy**，历史日志主机名为asusNUC05。它证明该记录对应的环境，不证明所有项目部署完成，也不是本轮对实际NUC的实时检查。个人Mac为ARM64；ARM容器结果不能直接充当x86_64 NUC的部署和时序验收。

用户已要求“终止验收，清理”。本机C1复验准备中止，未执行测试，没有新增PASS/FAIL；本次新增容器、镜像、下载源码、临时报告及相关启动进程已清理，既有镜像与历史证据保留。本轮同步不恢复监测或验收；原C1未通过结论继续有效。

个人正式源码锁定保持 `1d940f7c5f12561fed6641457c0b4b630a282b05`。后续如重新授权验收，应选定候选SHA、核对原生x86_64/Jazzy环境，并分别验证C1、完整FSM执行/停稳及实际硬件。冻结失败、签收回执与旧报告均保持原字节。

使用OpenAI Codex协助核对公开仓库状态、整理验收范围与文档；本轮未修改功能代码、参数或接口。

来源登记：TEAMMATE-STATUS-20261012；ENV-STATUS-SYNC-20261012；USER-HW-20261012-03、USER-HW-20261012-04（用户会话）。见[来源清单](../materials/manifest.json)。

本轮文档同步交付：团队独立分支已提交[PR #12](https://github.com/F1u0rite/meituan_challenge_ws/pull/12)，提交`32cb1991591b166e0a12521bfd0844631cd22859`；个人按用户授权直接更新main。本轮PR仅同步文档，待审状态不改变功能验收结论。
