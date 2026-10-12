# Phase 2A C++ Action 候选验收（2026-10-11）

**结论：`c0f70172e4b0271046d5f52813e0730d40ae772a` 的 C++ ROS 2 Action 离线 Mock 交付通过本轮检查；完整 FSM → MoveIt → 轨迹执行、Web UI 和实机尚未验收。** 正式锁定仍为 `1d940f7…`，本轮没有合并分支或推进基线。来源为 TEAMMATE-ACTION-20261011，本项目实测登记 ENV-CPP-ACTION-20261011。

这是 USER-HW-20261011-08、USER-HW-20261011-09 授权监测后收到的真实分支交付，区别于此前自动唤醒的本地测试提交。监测在 23:14:06（上海时间）发现 `feature/phase2a-cpp-actions`，固定复现结束后自动投递主对话；本轮 `ack` 返回 `CLAIMED`，23:19:06 登记回执，并输出 `MOVEIT_WAKE_ACK_6e9ffb20dc67525623909a2d70b0e9a5`。消息到回执约 11.3 秒；这是本次观测，不是时延保证。

## 实际变更和适用边界

相对 `1d940f7c5f12561fed6641457c0b4b630a282b05` 共变更 23 个文件：README、Phase 2A 报告及新增 `mtc_ros2_action_cpp`。四个 C++ 核心包、ROSIDL 和旧 Python Task/PickPlace 源码无变化。实际 diff、版本信息与上游报告分别保存在[事件补丁](experiments/cpp-action-20261011/event/change.patch)、[输入](experiments/cpp-action-20261011/inputs.json)和冻结 source 目录；上游自述的测试与本项目复跑分开计数。

| 新程序 / Action | 实际后端与通信 |
| --- | --- |
| `mock_task_server` / `/mtc/task/execute` | TaskFsm，通过真实 ROS PickPlace ActionClient 请求子任务 |
| `mock_pick_place_server` / `/mtc/manipulation/pick_place` | PickPlaceFsm、模拟感知/规划/工具，经本地 AsyncMockMotion 调用 MotionExecutorCore |
| `mock_motion_server` / `/mtc/motion/execute_joint_move` | 另一套 MockMotionAdapter，只支持六关节单点目标；PickPlace 没有调用这个 ROS Action |

没有 MoveIt Planner、FollowJointTrajectory 或 ros2_control 接入；两套 Mock Motion 不能当作共享硬件执行权。非零模拟关节输出、挂载/放置反馈和停稳结果都是软件 Mock 证据。运动时钟按 ManualClock 推进，默认 100 ms 是结果交付延迟；`placement_stability_sec=3.0` 在本轮不是三秒实体稳定性测量，也不是新增赛事规则。

新 C++ 包没有 TaskState/RobotState/ToolState 发布者。现有实机 Web UI 还要求这些状态、唯一发布源及相应节点身份，故相同 Action 名称不代表操作台已接通。该结论来自静态接口核对，本轮未执行 UI 联调。PickPlace Result 没有独立 `stop_confirmed` 字段，Task 的取消成功只适用于本次受信 Mock 子服务器约定，不能外推到任意服务器或实体停稳。

## 本项目实测结果

固定复现使用 Ubuntu 24.04 / ROS 2 Jazzy，原始镜像、依赖版本与逐步命令见冻结 `automatic/summary.json`。随后对**已停止**的原容器做独立文件系统快照用于补跑，原容器未重启。两轮均为 network none、无设备透传/挂载/端口、2 CPU、4 GiB、512 PID、cap-drop ALL、no-new-privileges。补跑顺序为身份核验、UBSan、外部 CMake consumer、独立进程 Action；没有并行跑另一 SHA。

| 检查 | 结果与原始证据（相对冻结目录） |
| --- | --- |
| 固定候选构建 | **PASS，13 包**；`automatic/logs/build.log` |
| 普通 C++ 回归 | **358 项独立 GTest / 20 个可执行文件，FAIL 0 / SKIP 0**；原 318 个完整身份保留，新增 40 项；`supplement/logs/identity.log` 与 `automatic/container/test-results/` |
| Python / 纯 Python Mock E2E | **269 / 15 项通过**；分别为包测试和显式 E2E，不能作为新 MoveIt 闭环计数；`supplement/automatic-counts.json`、`automatic/logs/python-mock-e2e.log` |
| 新包依赖 / package XML | **PASS**；离线官方 XSD 与 `rosdep check --from-paths src/mtc_ros2_action_cpp --ignore-src`；`supplement/logs/identity.log` |
| UBSan 独立构建和回归 | **358 项通过**；五个 C++ 包的编译命令确认 `-fsanitize=undefined -fno-sanitize-recover=all`；`supplement/logs/ubsan.log`、`supplement/container/ubsan/`。系统 ROS/DDS 库未插桩；TSan 未运行 |
| 导出库外部消费 | **PASS**；独立 CMake 工程仅 find_package 并链接导出目标，三个公共头文件、构造和销毁通过；`supplement/logs/consumer.log`、`supplement/container/CMakeLists.txt` 与 `main.cpp` |
| 独立可执行程序 | **4 场景通过，40 条探针断言**；不是另加 40 项 GTest；`supplement/container/standalone-v2/summary.json` |

普通 `colcon test-result` 的 652、UBSan 的 378 含 CTest 外层记录，不能用作独立用例数。以上计数来自实际 testcase XML 和本次交付的新身份核验入口，没有删除历史测试或放宽判据。

独立进程使用交付的三个默认可执行文件，逐节点核对唯一服务器；每场景使用单独 ROS domain（110–113）。[探针](../robot/probe_cpp_actions.py)和全部 Goal、UUID、Feedback、Result、Cancel 回应已归档：

| 场景 | 实际结果 |
| --- | --- |
| 启动后空闲 7 秒、基础任务、随后三色序列 | 基础任务 SUCCEEDED / 0，完成 1 个 T0；随后 `[3,1,2]` 保序完成 P1/P2/P3，Feedback 对象颜色逐项对应。非法颜色/重复序列/零稳定窗、并发请求及已用业务 ID 均拒绝 |
| Task 关联取消 | 多次观测 MOVE_PRE_ALIGN 后对原 Goal handle 取消，回应含该 UUID；最终 CANCELED / 0，完成数 0。只证明受信 Mock 子任务约定的传播 |
| 缺少 PickPlace 服务器 | Goal 受理后 150 ms 任务期限触发 ABORTED / 220，完成数 0；随后新 Goal 被 FAULT 锁定拒绝，没有伪造成功 |
| 独立 Motion 单点和取消 | float32 的 0.2 边界受理；非零六关节目标完整返回且 `stop_confirmed=true`。关联取消在 Mock 结果交付窗口返回 CANCELED / 0 / stop_confirmed；不代表取消了实体在途运动 |

四场景累计六次服务器进程启动，SIGINT 均退出 0，无升级终止；图中随后只剩探针节点。补跑结束前进程表只剩容器 keeper `sleep infinity`，再停止容器。两容器最终均停止、无 OOM；keeper 的 137 与下述 MoveIt 子进程 -11 分开记录。

## 固定复现的失败及完整性

自动 summary 有完整结束时间、全部步骤退出码和 stop/collect 成功记录，状态仍保留 `COMPLETED_WITH_FAILURES`。原始 index 的 **290 个文件逐一校验通过**，包括本地 source.bundle；原 index SHA-256 为 `5f3a496f8f1cf050066f2e72e925212b832bcaf175faf38b97ce0b4eaa2eb18f`。冻结副本不收入 Git bundle、SDK 或镜像，明确保留 bundle 哈希；不覆盖原失败记录。

| 失败 / 未执行项 | 分析与处理 |
| --- | --- |
| 旧 `cpp-audit` 返回 1 | 旧入口固定要求 16 个可执行文件；实际为 20，missing/unexpected/duplicates/bad 均为空。采用交付的新 `src/mtc_ros2_action_cpp/test/verify_results.py` 补验通过；原错误不删除，不归因于 C++ 用例失败 |
| 旧 Python `mock_bringup` 三场景失败 | Task/PickPlace 仍因 B01 时钟成员冲突、B02 配置字段不匹配退出，基础 Goal 未发送。此分支未包含 PR #2，旧 Python 源码未改；不能称为新 C++ 外壳回归。B03/B05/B06 等旧路径问题未由本轮关闭 |
| 可选六项 ROS 接线回归 | `tests/test_ros_wiring.py` 在该分支不存在，日志为 **NOT RUN**。包装命令退出 0 不能算 6 项通过 |
| 全工作空间依赖 | `mtc_manipulation` 的 `ament_python` rosdep 键仍未定义；新包自己的依赖检查通过不等于全工作空间通过 |
| 驱动依赖 / 自动测试 | 缺 `ros-jazzy-ros2-controllers-test-nodes`、`docker.io`；结果汇总 1104 / 279 failures / 259 skipped 含外层测试与 lint，不能解读为 1104 个功能用例。保留 description/消息生成代码等失败日志；与旧轮差异不宣称功能改进 |
| 独立 MoveIt | 同一固定驱动/模型的 Plan → Execute **PASS**：status 4 / code 1，肩关节目标 +0.05 rad，最大目标误差 `0.00009746883334591985 rad`，212 个不同关节时间戳；退出 **FAIL**：`move_group` -11，launch 0 不抵消子进程崩溃。它与新 C++ Mock 是分离的链路，补跑未重复这条未变的驱动测试 |
| 本地探针开发失败 | 首轮 standalone-v1 保存 NumPy UUID 字节时 JSON TypeError，未形成完整结果、后续场景未运行。保留脚本、日志和子进程日志；只把字节转为 Python int 后原场景/断言重跑 v2，通过。另保留补跑容器准备完成前读取 runtime.json 的编排失败记录；该次未启动测试 |

## 交接和未完成范围

按 SPRINT-PLAN-20261011 §01、§06–07 与 USER-HW-20261011-03，FSM/Action/Cancel 与 Motion Execution 仍归孙嘉明。本轮只做集成复现，没有修改上游核心或代发外部消息。以下作为本地待交接清单，不冒充已通知或已修复：

| 待交接项 | 负责人 / 后续验收依据 |
| --- | --- |
| Phase 2B MoveIt Planner、整条轨迹传递、唯一执行权 | 孙嘉明交付接口与入口；张叔阳按实际 SHA 补跑 FSM → MoveIt → FJT → Fake，避免把多个单点当轨迹 |
| 取消停稳、迟到反馈和真实负载上下文 | 孙嘉明明确公共证据契约；本次 Mock 的 CANCELED 不能填补独立实体停稳证明；TSan 仍 NOT RUN |
| 旧 Python B01–B06 路径 | 保留 ENV-FSM-20261011、ENV-FSM-FIX-20261011 的原问题和 PR 状态；由负责人明确保留/退役路径，本轮不接管修复 |
| 状态 Topic 与 Web UI 身份映射 | C++ Action 包未提供完整状态来源；按真实节点/话题交付后再由张叔阳核对，不在 UI 中伪造就绪 |
| MoveIt 退出 -11、依赖及驱动 lint | 系统集成侧保留日志并复核环境/上游依赖；不以规划成功关闭退出问题，不据此归责 FSM 内核 |
| 许可差异 | 根 LICENSE 为 MIT，新包 package.xml 为 Apache-2.0；请仓库负责人明确适用范围，本项目保留原文，不替其重新授权。SDK 与模型既有许可问题仍在 Q17 |

NUC、真实机器人/相机/工具、碰撞模型与标定、物理放置证据、完整 Web UI 联调、Gazebo 路线迁移均未由本轮完成。独立 Mock 结果不改变末端选型或比赛规则。

## 证据与运行入口

- 本轮来源：ENV-CPP-ACTION-20261011；[冻结索引](experiments/cpp-action-20261011/index.json)、[结果摘要](experiments/cpp-action-20261011/summary.json)、[协议](experiments/cpp-action-20261011/protocol.md)。index SHA-256 登记于 `materials/manifest.json`。
- 原自动运行：`outputs/moveit-watch-20261011/runs/sha-c0f70172e4b0271046d5f52813e0730d40ae772a/`；事件与完整 patch 在同级监测根目录的 `events/`。
- 主对话补跑：`outputs/phase2a-acceptance-20261011-c0f7017/`；`logs/` 保存逐步命令和退出码，`container/` 保存测试 XML、Action 记录和子进程日志。
- 自动回执：`outputs/moveit-watch-20261011/wake/sha-c0f70172e4b0271046d5f52813e0730d40ae772a/receipt.json`；冻结的 pre-complete 状态刻意保留主对话持有门禁时的快照，最终 complete 回执以此实时文件为准。

监测仍沿用原每 60 秒、截至 2026-10-12 08:00（上海时间）的设置。本轮分析、清理和证据登记完成后才提交 complete 解除下一 SHA 门禁；未调用 queue 或另起监测。未发生更新时由后台脚本轮询。

生成式 AI 披露：使用 OpenAI Codex 协助审阅真实提交、编写隔离验收探针、执行测试、分析失败和整理证据。新增探针调用标准 ROS Action 接口，不修改上游 FSM、规划或驱动算法；上游来源、版本和许可证原文见 TEAMMATE-ACTION-20261011，独立驱动沿用 TEAMMATE-SDK-20261011。
