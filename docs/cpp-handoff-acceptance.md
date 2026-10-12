# Phase 2A 交接文档验收（2026-10-12）

**结论：本次仅更新两份交接文档，运行代码未变；新指定的 358 项测试身份审计通过。新增通信图/QoS 检查已补跑，但两轮短时 CLI 观察均出现漏发现，不能判为整套 SOP 稳定通过。** 既有 Python、依赖/驱动测试及 MoveIt 退出失败继续保留。上游来源 TEAMMATE-HANDOFF-20261011，本机观测 ENV-HANDOFF-20261012。

实际版本为 `main@a04ac6831dd3963e6b1ec4b9e27214eb564f9f24`，父提交 `c10f6ed59966401684851f917f9137b0a6cf12ae`。相对父提交只有 `README.md`、`README_FSM.md` 变化，`src/`、`tests/`、`config/`、`scripts/`、`docs/` 的 Git 字节均未变。上游新增说明清楚区分 Task→PickPlace ROS Action、本地 Mock Motion 和独立 Motion Server，也说明旧 `mock_bringup` 仍为 Python、尚无 C++ Mock Bringup。

文档中的“建立 C++ Mock Bringup”等是提供方的下一步交接安排，已记录为待办；本事件按实际交付验收，没有据上游文字另行开发或合并。它引用 `main@c0f7017` 作为 Phase 2A 交接点，不等于本次观察 SHA，也不更改本项目 `robot/fsm-baseline.repos` 的 `1d940f7…` 正式锁定。另分支的 `mtc_moveit_planner` 不在本提交中；其已验结果继续单独见 ENV-PLANNER-20261012，不能因本次 main 文档而消去该交付或混算测试。

按 USER-HW-20261011-08、USER-HW-20261011-09，前一事件释放门禁后，本次固定复现于 10 月 12 日 00:09:14—00:13:45 运行；00:13:51 ack 返回 `CLAIMED`，主对话已输出 `MOVEIT_WAKE_ACK_0d839dd3b9366e0f39fe1cfff599abad`。一轮投递至持久化 ack 约 6.51 秒。本轮没有调用 queue 或启动另一监测。

## 本次固定复现与身份核验

| 检查 | 实际结果 |
| --- | --- |
| 工作空间构建 | **13 包 PASS** |
| C++ / Python / 显式纯 Python Mock E2E | **358 / 269 / 15 PASS**；C++ 为原四核心 318 + Action 40，共 20 个程序 |
| B01/B02/B04 ROS 回归 | **6 PASS**，本次 XML 确实执行，无失败或跳过 |
| 固定旧 C++ 审计 | **FAIL**，写死 16 个程序而实际为 20；缺失、重复、坏用例列表均为空 |
| 新文档指定 `src/mtc_ros2_action_cpp/test/verify_results.py` | **补跑 PASS**，按实际 `/candidate-build` 检查 358 个测试身份和 20 个程序；没有改旧脚本、测试或判据 |
| 完整 summary 与原始证据 | 25 步、结束时间、stop/collect 完整，原状态 `COMPLETED_WITH_FAILURES` 保留；291 个原索引文件全部通过 SHA 校验 |

当前 colcon 汇总为 652 条，包含 CTest 包装/lint，不能作为 652 个独立业务用例。上游文档引用的 UBSan 历史结果与本次普通回归分开；本轮没有重复 UBSan、外部 CMake consumer 或四场景独立 Goal/Cancel 探针，因为对应实现和测试输入相对已验 `c10f6ed…` 未变。它们的历史结果分别只引用 ENV-CPP-ACTION-20261011、ENV-WIRING-MERGE-20261011，不记为本次新增运行。

## 文档新增观察入口的补跑

原 runner PID 7075 不存在、原容器与前一事件容器均停止后，以停止原容器的独立文件系统快照补跑。原容器没有重启。沿用 Ubuntu 24.04 / Jazzy、无网络/设备/挂载/发布端口、2 CPU / 4 GiB、512 PID、cap-drop ALL / no-new-privileges。overlay 使用实际 `/candidate-install/setup.bash`，只适配文档中的安装路径。

第一轮在域 121 启动交付的 `ros2 run` Task/PickPlace，在另一空域 122 单独启动 Motion，按新增章节检查 node list/info、action list/info 和隐藏反馈 Topic。只读观察，不发送 Goal/Cancel，也不启动驱动或 MoveIt。每条命令限时 20 秒，整体 300 秒；没有超时。

| 观察 | 文档命令原样运行 | 一次有限诊断 |
| --- | --- | --- |
| 节点列表 | 两个域均看到准确的预期 C++ 节点 | 域 123 的 2 秒无 daemon 列表一度为空；域 124 正常 |
| node info | 三个节点都曾返回 `Unable to find node` / 1 | 加 `--no-daemon --spin-time 2` 后 Task、Motion 可见，PickPlace 仍一次失败 |
| action info `-t` | Task、Motion 一度显示 0 个服务器，PickPlace 为 1 | 三个 Action 均显示正确类型及唯一预期服务器 |
| 反馈 Topic / QoS | Task、PickPlace 均一个发布者；PickPlace 有 Task 订阅者；类型正确，均 RELIABLE / VOLATILE | 同样匹配；History/Depth 输出 UNKNOWN，未据此编造深度值 |
| 进程与退出 | 三个 `ros2 run` 均 SIGINT 退出 0，无升级终止；域清空 | 同样三个进程退出 0；域清空 |

诊断使用新空域 123/124，只改变观察侧：node info 直接等待 2 秒；先显式启动 CLI daemon 并等待 3 秒，再执行原 `action info -t`。容器内实际帮助和实现已保存：该 Jazzy 版本的 `action info` 支持 `-t`，没有 `--no-daemon` 参数，内部采用 NodeStrategy，故没有为它拼造参数。两次探针均退出 1，全部首次失败保留。

同轮其他观察能看到服务器/反馈端点、稍后 action info 能给出唯一服务器，**支持图发现/观察时序不稳定的判断；并未确定根因，也未证明简单延时已经修复**。尤其诊断中仍有短时节点查询失败，不能只凭局部空图断言服务器不存在，或把随后可见写成原样 SOP 全通过。六次 Mock 进程正常退出不等于业务任务已完成；本补跑未发送任务，实际 Goal/Feedback/Result/Cancel 的覆盖来自当前自动注册测试及明确分开的历史独立探针。

## 原有失败的本次实测

旧 Python 三场景中 Task 已受理 Goal，PickPlace 仍因 `ExecuteJointMove.create_client` 不存在退出（B05）；B03 被该失败遮挡。尽早 Goal 为 **ABORTED / 220**，延迟 7 秒 Goal 为 **ABORTED / 510**（B06）。本次 Cancel 已受理，最终却是 **ABORTED / 220**、完成数 0，消息指向 5 秒任务截止；前次 `c10f6ed…` 的 Cancel 终态为 520，源码未变也不保证相同时序下先触发同一故障。两次结果分开保存，均不构成子任务停稳证明。Safety 清理仍有 `rcl_shutdown already called`。

全空间 rosdep 仍缺 `ament_python` 定义；驱动依赖仍缺 `docker.io`、`ros-jazzy-ros2-controllers-test-nodes`。驱动测试汇总为 1104 / 279 failures / 259 skipped，含 lint/包装，不能算功能覆盖通过。

独立 MoveIt 固定探针本次 Plan→Execute 通过（status 4 / MoveIt code 1），210 个不同关节反馈时间戳，最大目标误差 `0.000053616809099911455 rad`；move_group SIGINT 后仍 **-11**，控制器 0，未通过干净退出。它使用独立 S3 GenericSystem，没有加载新 C++ FSM 或另一分支 PlannerPort。本轮未再次补跑该未变化链路；原日志完整保留。

## 交接与冻结证据

系统集成继续跟踪观察侧就绪判据、唯一服务器与可重复的 Mock SOP；新的统一 C++ Bringup 仍只有交接要求，没有实际 launch 交付。FSM/Action/Cancel、唯一运动执行权、整条 FJT、工具动作后起点和独立停稳证据继续在本地问题单回交孙嘉明，不接管修复、不发外部消息。TCP/视觉/工具标定、完整状态发布与 Web UI、TSan、SDK 许可/厂商校验值、NUC/实机仍未完成；根 MIT / C++ Action package.xml Apache-2.0 的声明差异也未由文档更新解决。

00:19:25 完成清理：四个补跑域的 CLI daemon 已停止，容器进程表仅剩 sleep keeper 后停止容器；本事件两容器均停止、无 OOM，旧 runner 不存在。keeper 的 137 与 ROS 进程退出单列。冻结前复核原始 291 文件没有变化，原 index SHA-256 为 `90d9ff27367b0fe1ff133367e4bf32f31c20100ead28c773a5d0babb863944f8`。

- [冻结索引](experiments/cpp-handoff-20261012/index.json)：418 文件，SHA-256 `a7f949818200001848963c227ba4432fd6beefd271c548dad308bd1cb542c50a`，登记于 manifest。
- [输入](experiments/cpp-handoff-20261012/inputs.json)、[摘要](experiments/cpp-handoff-20261012/summary.json)、[协议](experiments/cpp-handoff-20261012/protocol.md)。
- 原固定运行：`outputs/moveit-watch-20261011/runs/sha-a04ac6831dd3963e6b1ec4b9e27214eb564f9f24/`。
- 补跑：`outputs/handoff-acceptance-20261012-a04ac68/`；`container/documented-cli/` 与 `container/documented-cli-diagnostic/` 分别保留两轮原始结果。
- 最终回执：`outputs/moveit-watch-20261011/wake/sha-a04ac6831dd3963e6b1ec4b9e27214eb564f9f24/receipt.json`。冻结的是 complete 前快照；报告及四处来源同步后才登记 complete，不回写冻结集。

source.bundle 只登记 SHA，镜像/SDK/二进制不入库。正式锁定及旧冻结失败证据保持不变，既有监测设置仍为每 60 秒、截至 10 月 12 日 08:00（上海时间）。

生成式 AI 披露：OpenAI Codex 协助读取真实 Git 变更、调用已有 verifier、编写临时只读 CLI 观察探针、分析结果与整理证据；未修改 FSM/Action/Cancel、规划或驱动实现，未新增生产 Bringup。来源 TEAMMATE-HANDOFF-20261011、TEAMMATE-ACTION-20261011、TEAMMATE-SDK-20261011，保留原许可声明。
