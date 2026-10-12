# Phase 2B 轨迹执行端口验收

**结论：424 项普通与 UBSan 测试、外部链接和默认禁用检查通过；GenericSystem 的起点不符、取消场景通过，成功执行场景因运行证明失效返回 230，未通过验收。完整 FSM/实机尚未验收。**

固定提交 `688d80d63ba2196e3c1753b69d18c1bfa30919b3` 来自 `feature/phase2b-trajectory-execution`，登记为 TEAMMATE-TRAJECTORY-20261012；本项目观测为 ENV-TRAJECTORY-20261012。监测固定复现后一次投递，主对话约 **5.15 秒**签收。依据 USER-HW-20261011-08、USER-HW-20261011-09 执行系统集成、复现与验收；正式锁定仍为 `1d940f7c5f12561fed6641457c0b4b630a282b05`，未合并或推进基线。

**实际交付边界。** 相对监测基线共 41 个变更路径；相对已验 `a04ac68…` 仅新增 **13 文件**：`mtc_trajectory_execution_cpp` 包的 12 文件和 Phase 2B 报告，其余源码未变。实现位于父提交 `b47b5fe…`，`688d80d…` 补充报告。该分支不含规划/视觉包，现有 C++ Action 默认仍绑定 `MockPlanner` / `AsyncMockMotion`。

新增 `FjtMotionPort` 是整条 `TimedTrajectory` 的异步 MotionPort：按关节名映射向量、保留时序，一条轨迹只发一个 FJT Goal；默认禁用，须明确启用 Fake、提供六关节限位，且运行时验证 GenericSystem、控制器、独占执行图和新鲜反馈。起点容差 0.01 rad、终点 0.005 rad、停稳速度 0.005 rad/s、停稳窗口 0.2 秒、反馈有效期 0.3 秒、硬件/控制器证明有效期 0.7 秒，均沿用交付值。

验证器包含线性/三次/五次插值的 Bernstein 包络约束；这是保守的软件运动范围检查，不是碰撞或实机安全证明。单点、接触/笛卡尔入口没有实现。Cancel 只针对所持 Goal，ACK 不等于停稳；故障隔离和异步确认均保留。没有将轨迹拆成旧 ExecuteJointMove，也没有修改现有 FSM/Action 内核。

**运行与计数。** 原固定复现为上海时间 10 月 12 日 01:43:59—01:49:27。先核对原 runner 28269 和全部旧任务容器停止，再从原停止容器创建独立补验快照。环境为 Ubuntu 24.04 / Jazzy / C++17、驱动 `53aab837…`、模型 `47fa5e02…`、MoveIt 2.12.4。原/补跑均无网络、设备、挂载、端口，限制 2 CPU / 4 GiB / 512 PID，cap-drop ALL/no-new-privileges；未安装新依赖或调整上游源码、控制参数和时限。

| 检查 | 本次实际结果 |
| --- | --- |
| 原运行完整性 | 25 步具备起止和退出码，stop/collect 成功；303 个原始文件哈希一致，保留 `COMPLETED_WITH_FAILURES` |
| 构建与普通 C++ 测试 | 14 包构建通过；**424 项 / 22 个程序通过**：318 核心 + 40 Action + 66 新轨迹 |
| 新轨迹 66 项 | **30 验证器 + 36 ROS Fake Action**，含整条轨迹、重排、唯一 Goal、错误/超时、取消、反馈和首段 FSM 注入；无失败/跳过 |
| Python / 显式 Mock E2E / ROS 接线 | **269 / 15 / 6 通过** |
| 固定旧 C++ 审计 | 失败：预期 16、实际 22 个程序；宏定义占位名 `TrajectoryValidator.Name` 被误识别，22 个 `INVALID_TEST` 展开漏识别 |
| 交付新审计补跑 | **424 / 22 通过**；编译后注册列表与 XML 对应，另核验源码身份，既有 358 项完整保留 |
| 新包依赖/安装身份 | 新包 rosdep 通过，package.xml 和三份安装头文件与源码逐字一致 |
| 显式入口限制 | 无参数、非法模式各返回 2，均在 ROS 初始化前拒绝 |
| 外部 CMake consumer | 只查找新包并链接导出目标，构建/运行通过；合法轨迹在默认关闭状态被拒绝，ready=false、Goal/Cancel 均为 0 |
| UBSan 独立构建 | 六个 C++ 包重新编译，逐条编译参数有 undefined sanitizer、不可恢复和调用帧；**424 / 22 通过**，测试身份与普通构建一致 |

普通 colcon 汇总 720 包含 CTest 包装及接口 lint；UBSan 汇总 446 包含 22 个包装，均不当作独立功能用例数。UBSan 没有给 ROS/DDS 系统库插桩，也没有运行 TSan。分析器最初未去掉 colcon XML 的包名前缀，身份比较断言失败；原脚本/断言已保存，修正分析归一化后通过，测试和 XML 未改动或重跑。

**GenericSystem 三场景。** 使用原交付 `fake_trajectory_probe --verify-generic-system`，目标为 0/1/2 秒三点轨迹、六关节各增加 0/0.01/0.02 rad。起点不符模式给肩关节整条轨迹加 0.1 rad 偏移；取消模式约 0.5 秒请求停止。只读观察器订阅 JointState/GoalStatus，不创建 ActionClient，以免破坏端口的唯一客户端条件。

最初组合入口在 success 失败后停止并清理；随后把尚未运行的 mismatch、cancel 各放入一个新隔离域和新驱动进程，串行执行一次。**success 没有重跑或被后续结果覆盖**，没有扩大时限或修改测试输入。

| 场景 | 端口结果 | 独立观察与判定 |
| --- | --- | --- |
| success，域 134 | 退出 1；1 Goal、1 次取消尝试、36 次关联反馈；`STOP_UNKNOWN / 230`，`stop_confirmed=0`、`status_unknown=1`、`fault_locked=1` | 同一 UUID 状态 2→4，控制器报告成功；六关节最终均 +0.02 rad，但端口验收失败 |
| mismatch，域 135 | 退出 0；明确 `trajectory start differs`，REJECTED / 210；0 Goal、0 Cancel | 无新 UUID、六关节未动，**起点不符拒绝通过** |
| cancel，域 136 | 退出 0；初次停稳为 false，最终 true；1 Goal、1 Cancel、10 次关联反馈，无 unknown/fault | 同一 UUID 状态 2→3→5，六关节约 +0.00490571 rad 后停止，**取消及停稳通过** |

success 的 UUID 为 `1ad994a3870c95d6b873a41f93123561`，错误消息为 `runtime Fake/controller/state/graph proof lost`。本场景独立接收 876 个不同、递增的 JointState 时间戳，最大源时间间隔约 **9.40 ms**、最大接收间隔约 **9.55 ms**；观察到的最终目标误差为 0。终态消息之后、探针退出之前还有 56 个新样本覆盖约 0.275 秒，速度和位置差分速度均为 0。

这些外部数据说明“控制器到达目标”和“端口确认成功”在本次运行中不一致，**不能证明端口内部回调已处理这些样本，或硬件/控制器/独占图的证明当时有效**。聚合错误没有指出具体失败谓词，现有日志不能归因到某一个时限、发现过程或代码位置；不宣称根因已定位或故障已修复。上游报告的三个场景通过与本项目这次实际失败分别登记。

cancel 的 UUID 为 `edcbf44dd6198bfef5f9427c6e99afcb`；终态后、探针退出前观察到 76 个新样本覆盖约 0.375 秒，速度和位置差分速度为 0。该场景通过只覆盖独立端口取消，不代表上层 Task/PickPlace 取消链已接通。原探针反转关节名，但六关节等幅运动；不同数值的重排由单测覆盖，不能把本次 GenericSystem 运动另算为独立证明。

三次驱动/控制器均退出 0，无强制升级终止；各自停止 ROS daemon 后确认隔离域为空。但每次退出日志均有 `pal_statistics` invalid-context 线程错误，仍保留该清理日志缺口。

**固定运行的其他失败。** 全空间依赖仍缺 `ament_python` rosdep 定义；驱动缺 `docker.io` 和 `ros-jazzy-ros2-controllers-test-nodes`。驱动测试汇总 1104 条、279 failures、259 skipped，含 lint 和包装；失败包括 description 的 flake8/lint_cmake/pep257/xmllint、生成 C 的 uncrustify。不能以新包 rosdep 通过覆盖它们，也不能把 lint 汇总当实机功能测试。

旧 Python Mock 早 Goal 为 ABORTED / 220，延迟 INIT 为 ABORTED / 510，Cancel 受理后仍 ABORTED / 220，全部完成数 0；B05 `create_client` 启动错误、B03 被遮挡、B06 和 Safety 重复 shutdown 未解除。

固定独立 MoveIt 本次 Plan→Execute 为 **SUCCEEDED / 1**，最大关节误差 **0.00007646470312029123 rad**，206 个不同反馈时间戳；退出仍 **move_group -11 / control 0**。这条链没有消费新增 FjtMotionPort，不是 Planner→新端口→完整 FSM 的验收。前次主线事件的内部 FJT 未连接失败及 5 秒诊断仍作为原事件保留，未以本次成功删除。

**职责与剩余范围。** 源码与已执行测试明确：现有 PickPlace FSM 注入测试仅运行首段运动、`placement_verified=false`；直接请求取消时，第一次异步停稳尚未完成会使 FSM 保留 **FAULT / 520**，后续端口停稳也不会把它改为取消成功。当前没有 runtime host 或异步停稳桥，默认 Action 服务也没有接入新端口。

| 本地交接对象 | 需继续处理的事项 |
| --- | --- |
| 孙嘉明：FSM/Action/Motion/Cancel | Generic success 的运行证明丢失 / 230；上层异步停稳与 FAULT/520；默认服务绑定、唯一执行权和旧 B03/B05/B06；本轮记录证据，不接管内核修复 |
| 常建烁：规划 | 规划结果与整条轨迹契约、标定后的 TF/TCP/场景输入；此分支无 Planner 依赖，仍需统一执行权和接线 |
| 系统集成与验收 | 将端口内部证明诊断与外部状态对齐，跟踪 MoveIt -11、GenericSystem 退出日志、依赖与符号限位，完成统一 Bringup/状态/UI 验收 |

分工依据 SPRINT-PLAN-20261011 §01–03、§06–07；以上为本地交接材料，未代发外部消息。完整 Task/PickPlace、感知与工具消费、接触/笛卡尔执行、场景/载荷/视觉分支集成、实测 TCP/限位、TSan、SDK 许可/厂商校验值、NUC 和实机仍未验收。独立 Fake 不外推到实体碰撞、承载或安全；旧 Humble/Gazebo Classic 范围不变。

**证据与回执。** 核验只剩 keeper 后停止补跑容器。原 runner 28269 不在，原/补跑容器均停止、无 OOM；keeper 退出 137 与上述 ROS 子进程结果分别记录。冻结并保留所有失败和前序已签收证据：

- [冻结索引](experiments/trajectory-execution-20261012/index.json)：**683 文件**，SHA-256 `6f9445c42b173874fef0217cd86175f32cb7ae3a754ab7a440b1699b3dc1e12a`。
- [输入与版本](experiments/trajectory-execution-20261012/inputs.json)、[摘要](experiments/trajectory-execution-20261012/summary.json)、[协议](experiments/trajectory-execution-20261012/protocol.md)、[逐项分析](experiments/trajectory-execution-20261012/supplement/supplement-analysis.json)。
- [success 原日志](experiments/trajectory-execution-20261012/supplement/container/generic/success.log)、[独立关节反馈](experiments/trajectory-execution-20261012/supplement/container/generic/joint-states.json)、[Goal 状态](experiments/trajectory-execution-20261012/supplement/container/generic/action-status.json)、[取消日志](experiments/trajectory-execution-20261012/supplement/container/cancel/cancel.log)。
- 原运行：`outputs/moveit-watch-20261011/runs/sha-688d80d63ba2196e3c1753b69d18c1bfa30919b3/`；原 index SHA-256 `fd382472456f0833d9d36de30ed9e29219e03d45d9f71e3ea7849a345064838c`。
- 补跑/分析：`outputs/trajectory-acceptance-20261012-688d80d/`，命令和退出码位于 `logs/`，运行数据位于 `container/`。
- 回执：`outputs/moveit-watch-20261011/wake/sha-688d80d63ba2196e3c1753b69d18c1bfa30919b3/receipt.json`。冻结 complete 前状态，最终回执只存 raw，不回写冻结集。

source.bundle 仅记录 SHA，镜像/SDK/构建二进制不入库。同步 manifest、对应文档、open-questions、README 与 derived_files，核验事实链后才登记 complete；该状态表示本事件分析完成，不表示所有技术验收通过。既有监测仍是 60 秒轮询、固定主会话、上海时间 10 月 12 日 08:00 截止；本轮未调用 queue 或新启监测。

生成式 AI 披露：OpenAI Codex 协助审阅实际差异、补跑交付入口、编写只读观察/分析/清理脚本、冻结证据与登记事实链，没有修改上游 FSM/Action/Cancel/轨迹/驱动算法。来源 TEAMMATE-TRAJECTORY-20261012、TEAMMATE-ACTION-20261011、TEAMMATE-SDK-20261011；上游根 MIT 与轨迹/Action package.xml 的 Apache-2.0 声明差异继续保留，SDK/模型许可尚待核对，不重新授权。
