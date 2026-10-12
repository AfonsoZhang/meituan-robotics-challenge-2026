# MoveIt 场景、载荷与起点一致性增量验收（2026-10-12）

**结论：部分通过。14 包、393 项 C++ 与既有 Python 回归通过；默认规划入口仍在场景初始化失败。仅增加 TF 等待的诊断中，V2 七段规划及碰撞拒绝反例通过，V1 的上游时长未复现，MoveIt 退出仍为 -11。实际 FSM→MoveIt→FJT 与实机未验收。** 来源 TEAMMATE-SCENE-20261012，本地观测 ENV-PLANNER-SCENE-20261012。原始失败及前序签收报告保持原状。

## 实际提交与新入口

本次 SHA `30e3c6e64516c47afe9ada25d02df7ed4669825c` 来自 `feature/planning-scene-start-v1`，提交人为常建烁。新分支相对监测初始基线 `1d940f7…` 累计 105 文件；相对已验 `4a1a816…`（ENV-PLANNER-MERGE-20261012）实际增量 **45 文件**，全部属于规划包或 `docs/planning/`。非规划源码逐路径不变，不能把新分支的 previous 字段误解为本地基线回退。

增量包含 `082810b7…` 的场景/载荷/起点 API、`63d24e33…` 的关节插值，以及当前提交补充的第二轮上游证据。实际源码增加：

- 通过 `/apply_planning_scene` 加入占位桌面；规划请求的起始 RobotState 按阶段带入占位电池载荷。载荷仅在请求中附着，并非全局 attach。
- `check_trajectory_start` 按关节名比较起点，默认容差 0.01 rad；`replan_primitive` 用测量状态重规划指定一段，并跳过原工具间隙假设。
- V1 自由空间先尝试直线，失败后用 seeded IK 关节目标及每步不超过 0.02 rad 的关节插值，通过 `/check_state_validity` 逐点检查，再回退到 OMPL。这不证明全局最近 IK 解或跨环境确定性。
- launch 拒绝不存在的主/覆盖参数文件；采证 SOP 增加桌内目标碰撞探针；`MTC_INSTALL` 支持实际安装目录。

新增起点一致性 3 项、payload/单段重规划 3 项单测均在本次 35 项规划测试中执行。**实际 MotionAdapter/FJT 发送侧尚无这些 API 的调用者**；PickPlace 仍构造 MockPlanner/AsyncMockMotion，未链接真实规划包。单测/FakeBackend 通过不能证明工具动作后的真实起点或执行接线。`planning_time_s=1` 也不是包含 IK、逐点服务等待及所有回退的端到端期限；真实 FSM PLAN_ACQUIRE 时限仍待联调。

## 自动运行与隔离条件

依据 USER-HW-20261011-08、USER-HW-20261011-09，原固定运行于上海时间 **00:43:40—00:48:45** 完成。主对话 ack 返回 `CLAIMED`，已输出 `MOVEIT_WAKE_ACK_c625add1e8f451de3abc02c085b0ad3c`；一次投递至持久化 ACK 约 **5.72 秒**。本轮没有调用 queue 或另启监测。

先确认原 runner PID 15339 不存在、旧事件和原容器停止，再从停止原容器创建独立快照补跑。实际 inspect 核对无网络/设备/挂载/发布端口、2 CPU / 4 GiB / 512 PID、cap-drop ALL / no-new-privileges。所有入口串行，Jazzy / C++17 / Fake 环境，没有连接实体设备。原容器没有重启，原失败日志没有覆盖。

| 检查 | 本次结果及解释 |
| --- | --- |
| 固定 summary | 25 步有起止及退出码，stop/collect 成功；`COMPLETED_WITH_FAILURES` 保留，306 个原索引文件 SHA 全部核对 |
| 工作空间构建 | **14 包 PASS** |
| C++ | **393 / 25 个程序 PASS**：核心 318 + Action 40 + Planner 35，逐项 XML 对应源码身份，无重复/失败/跳过 |
| Python / 纯 Mock E2E / ROS 接线回归 | **269 / 15 / 6 PASS**，均为本次自动实际运行 |
| 旧固定 C++ 审计 | **FAIL**：预期 16 个 `*_cpp` 程序、实际 20；无缺失/意外/重复/坏用例，通配规则未包含规划包 |
| 新 Action verifier 补跑 | **358 / 20 PASS**；额外规划 35 / 5 独立核对，不将 verifier 夸为全包覆盖 |
| 两包 rosdep / 安装身份 | **PASS**，包括新增 collision override、配置及 launch |
| 缺主参数文件 / 缺覆盖文件负例 | **2 项 PASS**：均退出 1、明确 missing-file 信息，未启动节点 |

colcon 汇总 692 条包含包装和 lint，不当作 692 个独立功能用例。本轮没有重复源码未变的独立 C++ 四场景补跑；该项仅引用 ENV-PLANNER-MERGE-20261012 历史结果。UBSan/外部 consumer 和 CLI 图观察诊断分别保留在 ENV-CPP-ACTION-20261011、ENV-HANDOFF-20261012，不移记为本次运行。

## 默认失败与一次有界诊断

原配置 SOP 使用域 127。仅为现有 driver 安装目录建别名，规划目录使用交付支持的 `MTC_INSTALL=/candidate-install`，源码和默认参数未改。内层 360 秒、主机 400 秒上限；本轮默认约 63 秒结束，没有超时。

默认固定姿态通过，61 个点、5.906563507 秒；位置误差 `3.652543049e-06 m`、姿态误差 `1.954268969e-07 rad`。但随后碰撞探针、V1、V2 均出现 **`failed to apply planning scene obstacles`，各退出 2**。这三个工具没有进入目标规划，因此没有输出 YAML；属于初始化失败，不是轨迹采集遗漏或碰撞拒绝通过。SOP 仍返回 0，SUMMARY 的 “goal inside table was NOT rejected” 也不能当成碰撞测试实际执行的证据。

为了检查新交付的场景/载荷路径，只追加一次独立诊断，域 128，唯一参数差异为 **`backend.tf_timeout_s: 0.5 → 5.0`**。保存原参数、诊断副本和完整脚本 patch；脚本搬迁只修正 SCRIPT_DIR，碰撞覆盖照常使用。全部工具结束后附加只读场景/状态查询，不改变前面的规划结果。诊断约 64 秒结束，没有超时，未延长 FSM 状态预算。

| 项目 | 默认参数 | 5 秒 TF 等待诊断 |
| --- | --- | --- |
| 固定姿态 | PASS，61 点 / 5.90656 秒，退出 0 | PASS，同点数、时长及终点误差，退出 0 |
| 桌内目标碰撞反例 | 场景初始化失败，目标未测，退出 2 | **预期拒绝 PASS**：NO_PLAN，无轨迹，退出 1 |
| V1 `passive_hook_v1` | 场景初始化失败，无命令，退出 2 | **FAIL / EXCEEDS_STATE_WATCHDOG / 200**，无命令，退出 1 |
| V2 `magnetic_latch_v2` | 场景初始化失败，无命令，退出 2 | **七段规划 PASS**，退出 0，仅 simulation_only |
| SOP 总退出 | 0，不覆盖子工具失败 | 0，不覆盖子工具失败 |
| `move_group` / `ros2_control_node` | **-11 / 0** | **-11 / 0** |

诊断碰撞反例在关节插值第 **219/236** 个状态返回 invalid（1 contact），后续规划也失败；实际 MoveIt 日志明确记录 **`table` 与 `wrist3_Link` 接触**。由拒绝原因和接触对象共同确认反例，不使用“任意 PLAN FAILED 即通过”的弱判定。这仍只是一条采样路径反例，不证明连续碰撞安全或实体安全。

工具结束后的只读 `/get_planning_scene` 显示唯一世界物体为 `table`、尺寸 `[0.90, 1.20, 0.05] m`、frame `world`，当前 Fake 状态有效。全局 attached objects 为空符合本版请求级载荷的实现，不能据此声称实体载荷接入或场景中有已标定电池。

## V1 上游时长未复现

本机诊断明确使用 **`joint_interpolated_ik`**，不是观测到 OMPL 回退。直线规划先在 fraction 0.505556 / 最大关节步长 0.032 rad 被拒；后续插值轨迹估计时长 **180.4150345 秒**，超过 MOVE_PRE_ALIGN 的 `30 × 0.8 = 24 秒`，因此输出失败，没有发出命令或执行轨迹。

| V1 同一报告字段 | 上游提供的第二轮 YAML | 本机诊断 YAML |
| --- | --- | --- |
| 方法 | joint_interpolated_ik | joint_interpolated_ik |
| 轨迹点数 | 121 | 231 |
| 时长 | 42.07966529 秒 | 180.4150345 秒 |
| 时间缩放系数 | 3.527474696 | 7.846174666 |
| 最大末端线速度 | 0.01718560401 m/s | 0.01960784314 m/s |
| 最大末端角速度 | 0.09803921569 rad/s | 0.06915349185 rad/s |

两份报告中的工具、工位、命名起点关节、ring pose、TCP、目标 EE 和方法逐字段相同，但结果不同。上游文字所述约 39.6–42.1 秒的稳定性**本机未复现**，不能写成已改善。工具没有序列化被拒轨迹的完整点集或实际 IK 关节终点；现有证据不能定位 solver、模型或运行时差异的根因。此差异交常建烁补充可追溯 IK/模型输入，并与孙嘉明协调真实运动预算；本轮未循环重跑至通过、改规划算法或放宽看门狗。

## V2 的通过边界

诊断生成以下完整 JointTrajectory，六关节顺序、有限位置/速度/加速度、时间单调、源码数值位置边界、轨迹时长不超过对应状态预算的 80%、命令 timeout 大于轨迹时长均已核对。旧单点 `target_rad` 为空。

| 段 | 点数 | 时长（秒） | 请求级载荷 |
| --- | --- | --- | --- |
| top_insert | 45 | 16.455019 | 无 |
| test_lift | 9 | 1.864831 | 有 |
| lift | 18 | 3.305818 | 有 |
| transport | 24 | 2.253277 | 有 |
| pre_seat | 23 | 5.168050 | 有 |
| seat_contact | 12 | 7.756963 | 有，接触意图标记 |
| retreat | 25 | 5.917212 | 无 |

四处普通段间起点相接；两处工具动作仍使用未输出的 ENGAGE_INSERT/WITHDRAW 各 0.03 m 假设，相应最大关节间隙约 0.137086 rad，不能直接串发七段当作完整任务。新单段重规划 API 尚未被真实执行侧调用，本次未验“工具运动→实际关节状态→重规划→FJT”。`seat_contact` 仅为接触意图，不代表受力/接触闭环。

桌面、电池、TCP、ring 与工位均为 **PLACEHOLDER**。按配置静态计算，桌面顶为 -0.005 m，载荷底为 `0.13 - 0.07 - 0.05 = 0.01 m`，名义间距 **15 mm**，与上游文字“1 cm”不一致，登记为待澄清；两者都不是实测值。V1/V2 工具名称也不构成用户末端选型。

URDF 中三个命令限位仍保留 `{-2*pi}` / `{2*pi}`，本次只核对规划器使用的数值界限，没有证明控制器运行时强制限位有效。所有新增 SOP 轨迹均只规划，未实际执行。

## 原固定运行的其他失败与交接

旧 Python Task 接受 Goal，PickPlace 仍在 B05 `ExecuteJointMove.create_client` 处退出，B03 被启动失败遮挡；尽早 Goal ABORTED / 220、延迟 Goal ABORTED / 510（B06），Cancel 接受后最终 ABORTED / 220、完成 0。Safety 仍有 `rcl_shutdown already called`。全空间 rosdep 缺 `ament_python` 定义，驱动缺 `docker.io`、`ros-jazzy-ros2-controllers-test-nodes`；驱动汇总 1104 条 / 279 failures / 259 skipped 含 lint/包装，未通过。

自动固定探针的独立 MoveIt Plan→Execute **PASS**，Action status 4 / MoveIt code 1，207 个不同关节反馈时间戳，最大误差 `9.958734335377812e-05 rad`；退出 move_group **-11**、控制节点 0。它与新增规划端口分开，不是完整 FSM 抓放。本事件自动及两次 SOP 共三次 MoveIt 启动均退出 -11，原始日志全部保留。

| 本地交接范围 | 尚待处理 |
| --- | --- |
| 孙嘉明：FSM/Action/Cancel | B03/B05/B06；真实规划期限、整轨迹/FJT、起点检查及单段重规划调用、唯一执行权、工具动作与关联取消/独立停稳 |
| 常建烁：规划 | 默认场景 TF 就绪；V1 时长未复现及缺少 IK/被拒轨迹追溯；占位场景/载荷/15 mm 与文字差异、实际标定门禁 |
| 系统集成与验收 | SOP 返回码/碰撞标签、MoveIt 清理、依赖与限位、图发现就绪、统一启动和完整状态/UI 的验收 |

表格是本地交接材料，未代发外部消息，未接管内核修复。完整 FSM、真实 TCP/视觉/工具/环境标定、TSan、SDK 许可/厂商校验值、NUC 与实机仍未完成。正式锁定继续为 `1d940f7c5f12561fed6641457c0b4b630a282b05`，没有合并或推进。

## 冻结与回执

补跑结束确认无本轮 ROS/daemon、仅剩 keeper 后停止容器。原/补跑容器均停止、无 OOM，原 runner 不存在。keeper 137 与上面的 ROS 进程退出分开记录；原 306 个文件再次 SHA 核对一致，原 index SHA-256 为 `96af408ff80f00682ea78a249f99bd053214826d3172512558bf7aa0c57e68f5`。

- [冻结索引](experiments/planner-scene-20261012/index.json)：**545 文件**，SHA-256 `ab5bb1fe6665d2882bda214ac4b58f25ccbc64b57a7d84cced87ce5539d73361`。
- [输入](experiments/planner-scene-20261012/inputs.json)、[摘要](experiments/planner-scene-20261012/summary.json)、[协议](experiments/planner-scene-20261012/protocol.md)、[实际差异审阅](experiments/planner-scene-20261012/supplement/source-review.json)、[轨迹/对照分析](experiments/planner-scene-20261012/supplement/planning-analysis.json)。
- [默认失败日志](experiments/planner-scene-20261012/supplement/container/planning-sop/)、[诊断日志](experiments/planner-scene-20261012/supplement/container/diagnostic-tfwait/)、[诊断脚本差异](experiments/planner-scene-20261012/supplement/diagnostic-sop.patch)、[上游提供的第二轮材料](experiments/planner-scene-20261012/source/docs/planning/evidence/20261011_113932/)。
- 原固定运行：`outputs/moveit-watch-20261011/runs/sha-30e3c6e64516c47afe9ada25d02df7ed4669825c/`；原补跑：`outputs/planner-scene-acceptance-20261012-30e3c6e/`，命令和分步退出码见 `logs/`。
- 最终签收：`outputs/moveit-watch-20261011/wake/sha-30e3c6e64516c47afe9ada25d02df7ed4669825c/receipt.json`。冻结集保留 ACK/pre-complete；四处文档及 manifest/derived_files 校验后提交 complete，最终回执仅保存在原目录，不修改冻结集或签收报告。

监测仍沿用固定主会话、60 秒轮询、上海时间 10 月 12 日 08:00 截止；complete 仅表示本次分析及证据归档完成，用于解除下一 SHA 门禁，不表示所有功能通过。source.bundle 只登记 SHA，SDK、镜像、构建二进制不入库。

生成式 AI 披露：OpenAI Codex 协助读取实际 Git 差异、编排交付入口和一次有界诊断、只读场景观察、核对轨迹与上游报告、清理和登记证据。未修改规划/FSM/Action/Cancel/驱动算法。来源 TEAMMATE-SCENE-20261012、TEAMMATE-PLANNER-20261011、TEAMMATE-ACTION-20261011、TEAMMATE-SDK-20261011；根/规划 MIT 与 Action package.xml Apache-2.0 声明差异及既有 SDK/模型许可问题保留。
