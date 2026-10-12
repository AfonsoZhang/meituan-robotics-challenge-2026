# Phase 2B 命令身份与 MoveIt 联合门禁验收

**结论：命令身份回归、463 项普通/UBSan 测试及四个独立 GenericSystem 场景通过；默认 MoveIt/FJT 联合执行仍被双客户端门禁阻断，完整 FSM 未验收，退出失败保留。**

固定提交 `45f497ce3444e255463faf41f7b736aa9ad07d7b`，来自 `feature/phase2b-trajectory-execution`（TEAMMATE-TRAJECTORYGATE-20261012）；本项目观测 ENV-TRAJECTORY-GATE-20261012。依据 USER-HW-20261011-08、USER-HW-20261011-09，固定复现后一次投递，约 **4.88 秒**取得主对话 ACK，再检查实际差异和补跑。本项目未合并、未推进正式 `1d940f7…` 锁定。

**变更范围。** 相对已验 `688d80d…` 共 59 路径：53 个 Planner/规划证据路径与已验主线 `f7eaa2c…` 逐字相同；另 6 文件包含执行端比较逻辑、测试/核验器/探针、README 和最终门禁报告。代码提交 `d491a96…` 增加不可变命令身份，`3750d99…` 合入规划主线，`2e00a36…` 增补测试，当前提交补文档。默认 Action 仍为 MockPlanner/AsyncMockMotion；没有视觉、标定或新 Planning Scene 分支，也没有完整运行宿主。

新的 Session 和完成账本保存不可变 MotionCommand，在 ROS 归一化前比较原始关节顺序、路点、ID、时戳、scaling、timeout、安全字段及完整 intent Pose。Core 的 MotionPrimitive 相等比较原来不含 target_pose，适配器单独补比；Core API 没有修改。同内容可轮询/重读，不同内容返回 REJECTED，不增发 Goal/Cancel、不清 FAULT。完成账本仍最多 10000 条、无自动淘汰；完整轨迹副本和逐次 O(路点数) 比较成本仍需宿主约束。缓存成功只是历史结果，不是当前停稳证明。

**环境及固定复现。** 原运行上海时间 10 月 12 日 **02:26:01—02:32:02**，25 步有完整起止和退出码，stop/collect 成功；317 个原始文件核验一致。先确认 runner 35809 及旧任务停止，再从已停止原容器创建独立快照。Ubuntu 24.04 / Jazzy / C++17、驱动 `53aab837…`、模型 `47fa5e02…`、MoveIt 2.12.4；无网络/设备/挂载/端口，2 CPU / 4 GiB / 512 PID，cap-drop ALL、no-new-privileges。上游源、安装代码、控制参数、时限和限位未改。

| 检查 | 本项目实际结果 |
| --- | --- |
| 构建 | **15 包通过** |
| 普通 C++ | **463 项 / 26 程序，失败/跳过 0**；318 Core + 40 Action + 29 Planner + 76 轨迹端口 |
| 轨迹端口 | 30 验证器 + 46 ROS Fake Action，较前次新增 **10 项**身份/时钟回归 |
| Python / 显式 Mock E2E / ROS 接线 | **269 / 15 / 6 通过** |
| 新身份核验器 | 原 424 身份全部保留；源码、编译注册与实际 XML 对应，新增 10 + 合入 29 |
| 独立 UBSan | **同一 463 项 / 26 程序通过**；七个 C++ 包编译参数逐条核对 |
| 安装/依赖/参数 | 新包 rosdep 通过，4 个头/包文件源与安装一致；无参数/非法模式均在 ROS init 前退出 2 |
| 外部 consumer | 安装的 Planner core 与 FJT 导出目标能被独立 CMake 项目链接，实际规划数据可转换；执行能力拒绝另列 |

763 条原 colcon 汇总和 489 条 UBSan 汇总包含包装/lint，不能与独立用例重复累计；普通与 UBSan 也是同一测试集合的两种运行。旧固定 C++ 审计仍失败：预期 16、实际 22 个 `*_cpp` 程序（另 4 个 Planner 不匹配 glob），并误识别 `TrajectoryValidator.Name` 模板、漏 22 个 INVALID_TEST 展开。原错误日志不改。

UBSan 在独立 build/install 目录重新构建，halt_on_error=1，不可恢复、保留调用帧。接口依赖的生成 C 不属于七个 C++ 包插桩声明，系统 ROS/DDS/MoveIt 库也未重新插桩；TSan 本次未运行。分析器首次宽 glob 包含该生成 C 依赖而断言失败，已保留脚本/错误，纠正筛选后通过；未重跑或修改测试日志。

**四个原交付 Fake 场景，各一次。** 按域 141–144 串行启动新驱动，先确认空域、GenericSystem、两个 active 控制器；独立观察器只订阅 JointState/GoalStatus，不创建 ActionClient。每项结束后停 daemon、确认空域，再进行下一项。

| 场景 | 端口结果 | 独立观察与计数 |
| --- | --- | --- |
| success | PASS，stop_confirmed=1，unknown/fault=0 | 1 Goal / 0 Cancel / 40 反馈；同 UUID 状态 2→4，六关节各 +0.02 rad，902 个不同反馈戳 |
| mismatch | PASS，REJECTED / 210 | 0 Goal / 0 Cancel / 0 反馈；起点偏差被拒绝，无新 UUID，关节未动 |
| cancel | PASS，初次 stop_confirmed=0，最终为 1 | 1 Goal / 1 Cancel / 10 反馈；同 UUID 2→3→5，六关节约 +0.004999913 rad，608 个不同反馈戳 |
| identity | PASS，缓存重读和三次变更拒绝 | 1 Goal / 0 Cancel / 39 反馈；同 UUID 2→4，六关节各 +0.02 rad，908 个不同反馈戳；改路点/timeout/simulation_only 都未再发令 |

success/cancel/identity 在控制器终态后、探针退出前分别观察到约 **0.376 / 0.380 / 0.385 秒**零速度反馈；这是独立订阅证据，不证明端口内部所有健康回调。三次 UUID、完整反馈和时戳在冻结日志中。原探针反转关节名但六关节等幅运动，不能单独证明非对称关节重排；相应验证器单测另计。

前次 ENV-TRAJECTORY-20261012 的 success **STOP_UNKNOWN / 230** 及其原始证据继续保留。此次源差异没有修改健康/运行证明谓词；本轮单次通过不能证明该失败已修复或执行可靠性已达标。归因仍回交孙嘉明。

**默认 MoveIt 的执行权门禁。** 域 145 运行原 GenericSystem 驱动及原 move_group 配置，再调用新 `topology` 入口，没有放宽 exclusive_graph：

| 运行图 | FJT Server | FJT Client | 直接轨迹 Publisher | 结果 |
| --- | --- | --- | --- | --- |
| Controller | 1 | 0 | 0 | 两个控制器 active |
| 加默认 move_group | 1 | 1 | 0 | 客户端为 moveit_simple_controller_manager |
| 再加 FjtMotionPort | 1 | 2 | 0 | foreign_active_goals=0，ready=0，**BLOCKED / 退出 2**，零 Goal |

move_group 日志仍加载 MoveGroupExecuteTrajectoryAction，规划工具确认 MoveGroup Action client/server ready；`allow_trajectory_execution` 查询是 Parameter not set，不能当作 false。单次 CLI Action 列表仅列出 FJT，未完整观察其他入口，不作为完整 Action 图证据。规划业务代码只调用 plan 并不等于默认 move_group 不具备执行能力。图检查也不是强身份认证或竞态排除证明。后续需要明确的 planning-only 配置与唯一执行管理者，再重新验收；本次未创建替代配置或绕过门禁。

**只规划与跨包数据检查。** 同域运行交付的默认 `plan_fixed_pose`，输出 **211 点**、首点 t=0、总长 **20.94617995 秒**的有效规划；工具退出 0。整个拓扑/规划过程无 FJT Goal，3915 个不同 JointState 时戳、六关节保持零。该工具仅规划，未把轨迹交给执行端。

独立 CMake consumer 读取本次 YAML，链接安装的两个库并调用实际转换 API；不初始化 ROS、不建 Node/ActionClient、不发 Goal。Planner 转换成功；未赋 ID 时 FJT 以缺少完整身份拒绝。仅在纯数据诊断中给出 ID 与 32420 ms timeout 后，仍按原探针 ±0.5 rad / 0.2 rad/s / 0.5 rad/s² 范围拒绝，实际错误 **velocity limit exceeded**。输出最大绝对速度 0.315 rad/s、最大绝对位置 6.283046528 rad；没有扩大能力、改时戳、修改轨迹或关闭 spline/起点校验。

这说明规划数据可被跨包消费、当前窄执行能力不接受此轨迹；不等于规划无效或联合执行通过。输出中的绕周解和实际部署关节限位仍需负责人核对。序列化结果 SHA-256 为 `a6c86249832c866044e75f28c1030c8d27952d3bc6c7432841c373225f97b066`。

生成/观测时刻与 ROS 调度启动时刻仍是不同契约。新两项 ROS Action 测试实际验证 SteadyClock/已过去生成时间零 Goal 拒绝，但没有提供时间转换宿主；不能静默设 stamp=0。直接 FSM Cancel 仍保留“异步停稳待确认时 FAULT / 520”的旧测试边界，原 Task/PickPlace/工具/感知并未接入完整新链。

**失败与清理。** 原 Python Mock 早 Goal / 延迟 INIT / Cancel 受理后分别 ABORTED **220 / 510 / 520**，完成数均 0；B03/B05/B06、PickPlace create_client、Safety 重复 shutdown 未关闭。全空间 ament_python rosdep 缺口、驱动 docker.io/controllers-test-nodes 和 lint 失败保留；驱动汇总 1104 条 / 279 failures / 259 skipped 包含包装与 lint，不作实机能力计数。

固定独立 MoveIt 本次执行 SUCCEEDED / 1，最大关节误差 **0.0000930385054089129 rad**、208 个不同反馈戳，退出仍 move_group **-11** / control 0。补跑拓扑与只规划功能完成，但 move_group 再次 **-11**，因此补跑整体退出码 1、clean_shutdown=FAIL；未把外层 launch 退出 0 当作子进程成功。五次补跑控制器退出均 0、无升级终止，仍保留 pal_statistics invalid-context 线程错误。

全部 ROS 域/daemon 清理完成，容器只剩 keeper 后才停止；原 runner 35809 不在，原/补跑容器停止且无 OOM，候选源码 tracked diff 为空。keeper 退出 137 与各 ROS 子进程结果分开记录。既有 Planner 源码未变，未重复完整 V1/V2 SOP；其默认 TF、状态预算、场景、起点、工具接触及独立视觉/标定分支缺口保留。

| 本地交接对象 | 未完成事项 |
| --- | --- |
| 孙嘉明：FSM/Action/Motion/Cancel | 旧 230 归因、运行宿主、异步停稳桥、默认真实绑定及旧 Python 阻断；本轮不接管内核修复 |
| 常建烁及集成 | planning-only 执行权、生成/调度时钟、经审核的轨迹/限位/spline/起点契约、退出生命周期 |
| 系统集成与验收 | 统一 Bringup、工具/感知/标定接口和日志、完整任务回归；本次只保存本地交接材料，未代发外部消息 |

分工依据 SPRINT-PLAN-20261011 §01–07。真实碰撞/接触、实物停稳、TCP/相机与工位数据、SDK 许可/厂商校验、符号/未强制限位、TSan、NUC 与实机仍未验收。

- [冻结索引](experiments/trajectory-gate-20261012/index.json)：**869 文件**，SHA-256 `f4768b59f415bd90e2074293f795499533447fbdf58c47206acdf16794abe644`。
- [输入](experiments/trajectory-gate-20261012/inputs.json)、[摘要](experiments/trajectory-gate-20261012/summary.json)、[协议](experiments/trajectory-gate-20261012/protocol.md)、[逐项分析](experiments/trajectory-gate-20261012/supplement/supplement-analysis.json)。
- [拓扑/规划结果](experiments/trajectory-gate-20261012/supplement/container/topology-plan/summary.json)、[实际规划](experiments/trajectory-gate-20261012/supplement/container/topology-plan/planning/fixed_pose_plan_20261011_184148.yaml)、[跨包检查日志](experiments/trajectory-gate-20261012/supplement/logs/consumer-plan.log)。
- 原运行：`outputs/moveit-watch-20261011/runs/sha-45f497ce3444e255463faf41f7b736aa9ad07d7b/`；补跑：`outputs/trajectory-gate-acceptance-20261012-45f497c/`。
- 回执：`outputs/moveit-watch-20261011/wake/sha-45f497ce3444e255463faf41f7b736aa9ad07d7b/receipt.json`；冻结 complete 前状态，最终回执只存 raw。

原失败、历史冻结及已签收报告不改；bundle/SDK/镜像/构建二进制不入库。同步 manifest、对应文档、open-questions、README 与 derived_files 后核验并 complete，表示本事件分析结束。原 60 秒轮询、固定主会话和上海 08:00 截止不变，没有 queue 或新监测。

生成式 AI 披露：OpenAI Codex 协助实际源/日志审阅、复用交付入口、编写只读观察、跨包数据诊断及分析/清理脚本，整理事实链；没有上游 FSM/Action/Cancel/规划算法修改。来源 TEAMMATE-TRAJECTORYGATE-20261012、TEAMMATE-TRAJECTORY-20261012、TEAMMATE-PLANNERMAIN-20261012、TEAMMATE-SDK-20261011；根/规划 MIT 与轨迹/Action package.xml Apache-2.0 差异、模型/SDK 许可缺口保留，不重新授权。
