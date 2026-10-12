# MoveIt 规划分支验收（2026-10-11—12）

**结论：新规划包构建、29 项单测和固定姿态规划通过；默认 SOP 的 V1/V2 均被 TF 就绪问题阻断。仅把 TF 等待从 0.5 秒改为 5 秒的独立诊断中，V2 七段规划通过，V1 因轨迹超出状态时限而拒绝。整体未通过，完整 FSM→MoveIt→轨迹执行尚未验收。** 上游来源 TEAMMATE-PLANNER-20261011，本地实测 ENV-PLANNER-20261012。

本次验收的是 `feature/moveit-planner@fcdd8eae897cbc37c539d4bad57b712f08124938`，相对 `1d940f7c5f12561fed6641457c0b4b630a282b05` 共 53 个文件。它是常建烁的独立规划分支，尚不含另一分支的 C++ Action 包和 PR #2 接线修复；本轮不套用 `c10f6ed…` 的 358 项 C++ / 6 项 ROS 数字。未执行合并或推进 `robot/fsm-baseline.repos`。

按 USER-HW-20261011-08、USER-HW-20261011-09，固定复现于 10 月 11 日 23:50:46—23:54:59 运行；23:55:05 的 ack 为 `CLAIMED`，主对话已输出 `MOVEIT_WAKE_ACK_a1f1b9b45d0e0d44df7c1a39a1db10b8`。一次 queue 投递至持久化 ack 约 5.54 秒；本轮未调用 queue 或另启监测。补跑从 23:59 跨到 10 月 12 日，以下均区分原样运行和诊断运行。

## 实际交付与固定复现

实际 Git 差异包括 `mtc_moveit_planner`、规划交接说明和上游自存证据。四个核心包、旧 Python、ROSIDL 与 SDK/驱动说明相对比较起点未变。上游 `docs/planning/evidence/20261011_075828/` 是提供方报告，不当作本机实测；完整路径和哈希见冻结 `supplement/source-review.json`。本包及根目录均声明 MIT，未解决先前 SDK、模型及另一分支的许可问题。

规划包分为纯 C++ `PlannerPort`/轨迹转换和 MoveGroupInterface/tf2 后端，交付 `plan_fixed_pose`、`plan_battery_sequence`、参数/launch 及一键采证 SOP。它输出每个运动原语的完整时间参数化轨迹，不下发执行 Goal。四项 `FsmAcceptsPlannerOutput` 测试使用真实 PickPlaceFsm 配合 FakeBackend、简化运动学和 spy Motion，只证明契约接收及拒绝行为，不能代表真实 MoveIt 接进 FSM。

| 固定复现检查 | 实际结果 |
| --- | --- |
| 工作空间构建 | **13 包 PASS** |
| C++ | **347 PASS = 原四核心 318 + 新规划 29**，20 个测试程序；29 个新测试身份逐个对应源码，原 XML 无失败/跳过 |
| Python / 显式纯 Python Mock E2E | **269 / 15 PASS**，两种入口分开记录 |
| 原固定 C++ 审计 | **318 / 16 程序 PASS**；它只覆盖原核心，新增规划包由本次独立 XML/源码身份审计补齐 |
| 可选六项 ROS 接线回归 | **NOT RUN**，本分支没有该测试文件；C++ Action 包同样不存在 |
| 旧 Python 实际 Mock | 三场景均在 Task 服务器不可用时失败，基础 Goal 未发送；这是未含接线修复的分支，不是已合并分支的回退 |
| 新规划包依赖与安装身份补查 | **PASS**；已安装 overlay 下独立 rosdep 通过，两个配置、launch、package.xml 与源码逐字节一致 |
| 全空间依赖 / 驱动检查 | `ament_python` 键未定义；驱动缺 test-nodes / docker.io；测试汇总 1104 / 279 failures / 259 skipped 含 lint 和外层记录，不算独立功能用例 |

原 summary 的 25 步、结束时间、stop/collect 均完整，状态保持 `COMPLETED_WITH_FAILURES`。原索引 **290 个文件全部校验通过**，index SHA-256 为 `3f8899b35bd335d23655c0c2f73edb85d4cabefe0c825935c1915bfb9be5610d`。

## 新入口补跑

先确认原 runner PID 94194 和前一事件进程已结束、相关容器停止，再以原停止容器的独立文件系统快照补跑。沿用 Ubuntu 24.04 / Jazzy、2 CPU / 4 GiB、512 PID、无网络/设备/挂载/发布端口、cap-drop ALL / no-new-privileges。仅用容器内目录别名对齐既有安装布局，未改上游源码、已安装配置或算法。各次串行执行，外层有 360 秒时限与 400 秒兜底，本次均未超时。

原样 SOP 使用域 116、Fast DDS、`backend.tf_timeout_s=0.5`。静态 Xacro 和运行时插件均为唯一 `mock_components/GenericSystem`，两控制器 active；实际 `world→base_link` 为零平移/单位旋转，TF 文本与图完整保存。三个工具的实际结果如下：

| 入口 | 原样 SOP | TF 等待诊断（域 117） |
| --- | --- | --- |
| 固定姿态：当前六关节零位 → SRDF home 的 FK 位姿 | **PASS**，61 点 / 5.909337444 秒；末端位置误差 `0.00006192415625 m`，姿态误差 `0.001408115661 rad`；进程 0 | **PASS**，157 点 / 15.58985093 秒；位置误差 `0.00009044997035 m`，姿态误差 `0.001185652259 rad`；进程 0 |
| V1 `passive_hook_v1` | **FAIL**，ACQUIRE / side_insert，`TF_UNAVAILABLE` / 200，commands 为空；进程 1 | **FAIL**，`EXCEEDS_STATE_WATCHDOG` / 200，commands 为空；进程 1 |
| V2 `magnetic_latch_v2` | **FAIL**，ACQUIRE / top_insert，`TF_UNAVAILABLE` / 200，commands 为空；进程 1 | **有条件规划 PASS**，ACQUIRE 2 段 + TRANSPORT 5 段；进程 0 |

诊断只改变 `backend.tf_timeout_s: 0.5→5.0`，其余参数值、几何、帧名、速度和状态时限保持一致；独立 SOP 副本、差异和参数文件全部保存。外部 TF 已可见而新工具默认等待失败，延长等待后本次可进入规划，**支持启动/发现就绪时序问题的判断，但未确定完整根因或证明普遍修复**。默认交付仍记失败，没有改默认参数后重写原结果。OMPL 解及点数/时长可变化，两次固定姿态结果不要求逐点一致；此处误差是工具 FK 报告值，不是执行后的测量。

V1 的 OMPL 路径经速度约束时间缩放后长 **136.5147489 秒**、135 点，超过 `MOVE_PRE_ALIGN` 30 秒看门狗的 80%（24 秒）。拒绝门禁按实现生效，但任务路径仍不可用；本轮未放宽时限或修改 FSM/动作分解。它和默认配置的 TF 失败是两个不同阶段的问题。

诊断 V2 的完整轨迹如下，均保留 `simulation_only=true`、空 `target_rad` 及完整 trajectory：

| 原语 | 点数 | 时长（秒） |
| --- | --- | --- |
| top_insert | 35 | 13.177715 |
| test_lift | 9 | 1.877579 |
| lift | 18 | 3.283565 |
| transport | 24 | 2.253245 |
| pre_seat | 23 | 5.126590 |
| seat_contact | 12 | 7.746108 |
| retreat | 26 | 5.864072 |

离线独立检查确认六关节顺序、有限的位置/速度/加速度、严格递增时间戳、点数与末时刻、规划器声明的数值位置边界及各段状态预算。四个无工具间隙的段间端点一致；top_insert→test_lift 和 seat_contact→retreat 分别有最大约 0.13222 / 0.13662 rad 的关节差，源码明确假设工具插入/退出 0.03 m 后到达新起点，**相应工具轨迹没有输出、执行或核验**。序列从软件中的 SRDF home 起算，并未将 Fake 硬件移动到 home；七段规划不能拼写为完整抓放执行成功。

TCP、提环和工位仍为占位输入，接触段仅表示意图；场景未验收相机、末端、电池、底图/环境和附着物碰撞几何。`world` / `base_link` 当前静态重合不消除动态 TF 时钟问题。V2 通过不表示末端选型完成，仍沿用 USER-EE-20260906-01、USER-EE-20260906-02、USER-EE-20260906-04、USER-EE-20260923-02 的开放候选约定。

## 退出和未解决项

固定通用探针另行复现了独立 MoveIt Plan→Execute：status 4 / code 1、208 个不同关节反馈时间戳，最大目标误差 `0.00009981840057298541 rad`，但 move_group 退出 -11、控制器 0。该探针没有使用新规划包或 FSM，不能填补新轨迹执行缺口。

新规划 SOP 的 move_group 在原样及诊断两次均退出 **-11**，堆栈涉及 MoveItCpp / TrajectoryExecutionManager / rclcpp CallbackGroup 析构；原样控制器退出 **-2（SIGINT）**，诊断控制器退出 0。-2 与段错误区分记录，也不按正常 0 处理。两份 SOP 总退出码都为 0、ROS 图最终为空，仍不能抵消内部失败或证明干净退出。原始堆栈和所有工具退出行均冻结，不据此把驱动库问题归因于新规划算法。

独立轨迹审计还发现展开 URDF 的 shoulder / upperArm / wrist2 command-interface 限位仍是 `{-2*pi}` / `{2*pi}` 字面量。初版只读解析器尝试转浮点失败，脚本与错误保留；修订后明确按已读 `planner_config.cpp` 的数值边界审计，原 XML 字节不变。**本次没有证明控制器运行时解析或强制了这些限位**，需在驱动集成项中继续核验。

| 本地交接事项 | 责任与验收缺口 |
| --- | --- |
| 默认 TF 就绪及 V1 规划配置 | 交常建烁复核：保留默认失败和 5 秒诊断；V1 动作/速度/状态预算需与孙嘉明共同对齐 |
| FSM / Action / Cancel / 完整轨迹执行 | 交孙嘉明：真实异步 PlannerPort 与 2 秒 PLAN_ACQUIRE 时限、工具间隙实际起点、唯一执行权、整条 FJT、取消与独立停稳证据均未接通；不接管内核修复 |
| 标定与规划场景 | 规划及视觉/标定负责人继续核对 TCP、工位、动态 TF、物体/工具/环境碰撞几何与附着物；Mock 占位值不能用于实机 |
| 集成与环境 | 保留 MoveIt/控制器退出异常、URDF 限位字面量、依赖与驱动 lint；TSan、SDK 许可/厂商校验值、完整状态发布/Web UI、NUC 与实机未由本轮解决 |

以上交接只写入本地报告，没有代发外部消息。原 Python B01/B02 等失败、另一候选的 B03/B05/B06、此前 Action Mock 和合并验收分别保留，不能混为同一 SHA 的运行结论（ENV-CPP-ACTION-20261011；ENV-WIRING-MERGE-20261011）。

## 清理与证据位置

10 月 12 日 00:02:39 完成清理：补跑进程表仅剩 sleep keeper 后停止容器；原容器和补跑容器均停止、无 OOM，原 runner 已不存在。keeper 的 137 单列为停止结果，不计作 ROS 子进程崩溃。清理、隔离 inspect、每步命令/开始结束时间/退出码均已保存。

- [冻结索引](experiments/planner-acceptance-20261012/index.json)：450 个文件，SHA-256 `ac87b4b8ac220be508dc14cd30d266cd21f124a062f703e7ddd799d842581af9`；已登记 manifest。
- [输入](experiments/planner-acceptance-20261012/inputs.json)、[摘要](experiments/planner-acceptance-20261012/summary.json)、[协议](experiments/planner-acceptance-20261012/protocol.md)、[规划文件审计](experiments/planner-acceptance-20261012/supplement/planning-analysis.json)。
- 固定原始证据：`outputs/moveit-watch-20261011/runs/sha-fcdd8eae897cbc37c539d4bad57b712f08124938/`。
- 补跑原始证据：`outputs/planner-acceptance-20261011-fcdd8ea/`，其中 `container/planning-sop/` 是默认失败，`container/diagnostic-tfwait/` 是独立诊断。
- 最终回执：`outputs/moveit-watch-20261011/wake/sha-fcdd8eae897cbc37c539d4bad57b712f08124938/receipt.json`。冻结保留 complete 前 ACK 快照；报告及四处事实同步结束才登记 complete，终态不回写冻结证据。

source.bundle 只记录哈希，镜像、SDK 与编译二进制不入库。监测继续沿用每 60 秒轮询、截至 10 月 12 日 08:00（上海时间）的原设置；本事件 complete 前下一 SHA 保持排队。

生成式 AI 披露：OpenAI Codex 协助审阅固定 Git 变更、运行交付 SOP、作有限参数诊断、独立核验轨迹文件及整理事实链。未新增或修改上游规划/FSM/驱动算法，保留 MIT 等原始声明，不重新授权；来源 TEAMMATE-PLANNER-20261011、TEAMMATE-SDK-20261011。
