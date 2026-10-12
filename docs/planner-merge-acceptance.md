# 规划与 C++ Action 合并版本验收（2026-10-12）

**结论：两模块已在同一 Jazzy 工作空间构建，普通回归及独立 C++ Mock 四场景通过；默认规划序列和 MoveIt 干净退出仍失败，完整 FSM→MoveIt→Fake/实机未验收。** 上游来源 TEAMMATE-INTEGRATION-20261012，本地观测 ENV-PLANNER-MERGE-20261012。失败原件保留，没有修复 FSM/Action/Cancel 内核或推进正式基线。

## 实际提交与接线边界

验收 SHA 为 `4a1a81652fca39efe2916a19ad49187d29789697`，观察于 `feature/moveit-planner` 和 PR #3 head。它由常建烁将 `main@a04ac683…` 合入规划分支，两个父提交分别为：

- 规划父提交 `fcdd8eae897cbc37c539d4bad57b712f08124938`，此前观测 ENV-PLANNER-20261012。
- 主线父提交 `a04ac6831dd3963e6b1ec4b9e27214eb564f9f24`，此前观测 ENV-HANDOFF-20261012。

相对规划父提交改动 28 个文件，纳入 C++ Action、B01/B02/B04 Python 接线补丁、6 项 ROS 回归和交接文档；相对主线父提交仅增加原有的 53 个规划文件。逐路径 Git 身份核对证明，规划包及 `docs/planning/` 与第一父提交完全相同，其余文件与第二父提交完全相同。此次是两套既有内容的组合，没有新改动的运行算法。

实际 `pick_place_server.cpp` 仍构造 `MockPlanner` 和 `AsyncMockMotion`，Action 包没有声明或链接 `mtc_moveit_planner`。Task→PickPlace 是 ROS 子 Action，PickPlace→Motion 仍是本地 Mock；独立 Motion Server 仍只提供已有单点 Mock 接口。规划包的 4 项 FSM 接受测试使用 FakeBackend/spy Motion，不能据此认定真实 MoveGroup、工具动作、完整轨迹和 FJT 已接线。统一 C++ Bringup、完整状态发布与 Web UI 闭环仍未交付。当前本项目正式锁定继续为 `1d940f7c5f12561fed6641457c0b4b630a282b05`。

## 自动复现与补跑

依据 USER-HW-20261011-08、USER-HW-20261011-09，既有监测于 00:25:16—00:30:20（上海时间）执行固定复现，随后主对话 ack 返回 `CLAIMED`，输出 `MOVEIT_WAKE_ACK_7e65587e43f277680a9efc6466d1f1ed`。一次投递至持久化 ack 约 5.69 秒；没有新增 queue 或另启监测。

原 PID 12886 不存在、原容器及旧事件容器均停止后，使用停止原容器的独立文件系统快照补跑。原始失败容器没有重启。实际 inspect 确认无网络、无设备、无挂载和发布端口，2 CPU / 4 GiB、512 PID、cap-drop ALL / no-new-privileges。各步骤串行，保持 Jazzy / C++17 和 Fast DDS，未连接实体设备。

| 检查 | 本次结果与范围 |
| --- | --- |
| 完整固定运行 | 25 步有起止时间及退出码，stop/collect 成功；原 `COMPLETED_WITH_FAILURES` 状态保留，305 个原索引文件 SHA 全部匹配 |
| 工作空间构建 | **14 包 PASS**，Action 与 Planner 同时安装 |
| C++ GTest | **387 PASS / 24 个程序**：核心 318 + Action 40 + Planner 29；每项 XML 身份与对应源码匹配，无重复、失败或跳过 |
| Python / 显式 Mock E2E / ROS 接线回归 | **269 / 15 / 6 PASS**，均为本次实际运行 |
| 固定旧 C++ 审计 | **FAIL**：旧脚本预期 16 个 `*_cpp` 程序，实际 20；缺失、意外、重复、坏用例均为空 |
| 交付的新 Action 审计入口 | **补跑 PASS：358 / 20**；其通配规则不含 `mtc_moveit_planner`，额外 29 / 4 已独立核对，不把它写成覆盖全部 387 |
| 两个新包的 rosdep 与安装身份 | **PASS**；package.xml、规划默认配置、V2 覆盖配置和 launch 与源码一致 |
| C++ 独立进程四场景 | **PASS：40 项检查，六次服务器正常退出**；执行的是当前合并安装环境 |

colcon 的 685 条汇总含 CTest 包装和接口 lint，不能当作 685 个独立功能用例。全工作空间的依赖错误也不因两包 rosdep 通过而消失。

四场景复用已有 `probe_cpp_actions.py`，分别使用域 110–113：空闲 7 秒后的基础 T0 和三色 P1/P2/P3、实际子任务关联取消、缺失子服务器的失败及锁定、独立 Motion 单点和关联取消。检查包括拒绝非法/并发/重复业务 ID、实际反馈和终态。基础/序列成功，关联 Task 取消为 CANCELED / 0，缺失子任务为 ABORTED / 220；独立 Motion 取消结果有 `stop_confirmed`。**这些仍是可信 Mock 契约；PickPlace 公共结果没有独立停稳字段，不能证明实体或完整 MoveIt 停稳。** 六次子进程均退出 0，无升级终止；确认只剩容器 keeper 后才运行规划 SOP。

## 默认规划入口的实际失败

域 126 使用交付的 `run_planning_evidence.sh`，代码、默认参数、状态预算均未改。只在容器内部为现有构建目录建立两处路径别名：`/driver_ws/install_no_symlink → /driver_work/install`、`/candidate/install/planner → /candidate-install`。脚本上限 360 秒、外层上限 400 秒，本次约 60 秒结束，没有超时。

静态和运行时 GenericSystem 检查、活动控制器、TF 采证均完成。新入口只做规划，没有执行其输出轨迹。

| 工具 | 默认参数下的实际结果 |
| --- | --- |
| 固定姿态 | **PASS**，89 个点、8.758936911 秒；位置误差约 `0.0000718345 m`，姿态误差约 `0.000695822 rad`；子进程 0 |
| V1 `passive_hook_v1` | **FAIL / 200 / EXCEEDS_STATE_WATCHDOG**，`side_insert` 轨迹约 42.0717 秒，超过 MOVE_PRE_ALIGN 的 `30 × 0.8 = 24 秒` 预算；无命令输出，子进程 1 |
| V2 `magnetic_latch_v2` | **FAIL / 200 / TF_UNAVAILABLE**，`top_insert` 无法在工具内将 ring pose 从 `base_link` 转为 `world`；无命令输出，子进程 1 |
| SOP 总退出与节点清空 | 脚本退出 **0**、报告节点清空；这两项不能覆盖上面的工具失败 |
| MoveIt / 控制节点退出 | `move_group` **-11**，`ros2_control_node` **0**；干净退出 **FAIL** |

固定姿态 YAML 的六关节顺序、单调时间、有限位置/速度/加速度及规划器声明的数值位置边界已经独立核对。展开 URDF 中三关节仍保留 `{-2*pi}` / `{2*pi}` 命令限位字面量；核对规划器数值不代表控制器运行时限位强制执行已验收。

与 ENV-PLANNER-20261012 的原默认运行相比，本次 V1 通过 TF 查询后才在状态预算处失败，V2 仍卡在 TF。源码和配置相同，失败阶段的变化支持继续检查发现/就绪时序，**不构成修复或性能提升证明**。前一提交的 5 秒 TF 等待诊断、V1 136.5 秒拒绝和 V2 七段规划通过仍是分别保存的历史结果，本次未重复诊断或延长看门狗，也未将历史 V2 成功记成本次通过。

本轮不重复未变化的 UBSan、外部 CMake consumer、短时 Node/Action/QoS CLI 诊断；历史来源分别为 ENV-CPP-ACTION-20261011、ENV-HANDOFF-20261012。当前 Action 客户端有界等待后成功，并未关闭前次 CLI 图观察的漏发现问题。

## 固定运行的其他失败

旧 Python Mock 三场景中 Task 已受理 Goal，PickPlace 仍因 `ExecuteJointMove.create_client` 不存在退出（B05），B03 尚被启动失败遮挡。尽早 Goal 为 ABORTED / 220，延迟 Goal 为 ABORTED / 510（B06）；本次 Cancel 已受理，但最终为 ABORTED / 220、完成 0，仍不能证明子任务已停稳。Safety 清理继续出现 `rcl_shutdown already called`。这些属于旧 Python 路径，不能覆盖上面 C++ Mock 的通过，也不能因 C++ 通过而删除。

全空间 rosdep 缺 `ament_python` 定义；驱动缺 `docker.io`、`ros-jazzy-ros2-controllers-test-nodes`。驱动汇总 1104 条 / 279 failures / 259 skipped，含 lint 与包装；实际失败涉及 aubo_description 的 flake8/lint_cmake/pep257/xmllint 和 aubo_msgs 生成 C 的 uncrustify。该组没有通过，不当作实体驱动功能测试结论。

固定探针中的独立 MoveIt Plan→Execute **通过**（Action status 4 / MoveIt code 1），209 个不同关节反馈时间戳，最大目标误差 `0.00008607770199887454 rad`；退出时 `move_group` **-11**、控制节点 0。此执行链路与新增规划端口分开，不是 FSM 整体抓放。加上默认 SOP，本事件两次 MoveIt 启动均出现退出 -11，全部原始日志保留。

## 本地交接与证据

| 负责人/范围 | 保留的工作与未完成项 |
| --- | --- |
| 孙嘉明：FSM/Action/Cancel | B03/B05/B06、真实异步 PLAN_ACQUIRE 时限、唯一运动执行权、整条轨迹/FJT 接线、工具动作后实际起点、关联取消与独立停稳证据；记录回交，未接管修复 |
| 常建烁：规划 | 默认 TF 就绪、V1 路径/时长与 FSM 预算协调、TCP/工位/场景与附着物校准门禁；未通过放宽预算强行变绿 |
| 系统集成与验收 | 观察侧就绪、驱动/MoveIt 退出、依赖声明、URDF 限位求值及来源证据；统一 Bringup、完整状态 Topic 与 UI 尚未验收 |

TCP、感知和工具标定、未输出的插入/撤离工具动作、完整碰撞场景、TSan、SDK 许可/厂商校验值、NUC 与实机仍未完成。原根 MIT、规划 MIT 与 Action package.xml Apache-2.0 的许可声明差异保留；没有替上游重新授权。此表是本地交接材料，本轮未代发外部消息。

结束前确认无本轮 ROS 进程或 daemon，仅剩 keeper 后停止补跑容器；原/补跑两个容器均停止、无 OOM，原 runner 不存在。keeper 的退出 137 与实际 ROS 子进程的退出分别记录。原 305 个文件再次 SHA 核对一致，原 index SHA-256 为 `559f3ae5102e6fbccdc83aa6acb0011891ac6c0669173b8a9e5fbc5ebba84366`。

- [冻结索引](experiments/planner-merge-20261012/index.json)：486 文件，SHA-256 `11a2655ffd43f976ab2a9922e29b9d029e3bd2c60c98d5978cbfed9d29519b04`。
- [输入](experiments/planner-merge-20261012/inputs.json)、[摘要](experiments/planner-merge-20261012/summary.json)、[协议](experiments/planner-merge-20261012/protocol.md)、[逐路径源码核对](experiments/planner-merge-20261012/supplement/source-review.json)。
- 原固定日志：`outputs/moveit-watch-20261011/runs/sha-4a1a81652fca39efe2916a19ad49187d29789697/`。
- 补跑日志：`outputs/planner-merge-acceptance-20261012-4a1a816/`，其中 `container/standalone/`、`container/planning-sop/` 分别保存 Action 与规划结果。
- 最终回执：`outputs/moveit-watch-20261011/wake/sha-4a1a81652fca39efe2916a19ad49187d29789697/receipt.json`；冻结集保存 complete 前状态，文档与 manifest/derived_files 同步后提交 complete，最终回执不回写冻结集。

source.bundle 只登记 SHA，镜像、SDK 和构建二进制不入库。既有监测每 60 秒轮询、截至 10 月 12 日 08:00（上海时间）的配置不变；工作区 HEAD、正式锁定和前序冻结/签收报告保持原状。

生成式 AI 披露：OpenAI Codex 协助比较双父提交、复用既有验收探针、编排交付 SOP、独立核对结果和登记事实链。未修改规划、FSM、Action、Cancel 或驱动算法；来源 TEAMMATE-INTEGRATION-20261012、TEAMMATE-PLANNER-20261011、TEAMMATE-ACTION-20261011、TEAMMATE-SDK-20261011。
