# PR #2 合并后候选验收（2026-10-11）

**结论：上游 `main` 已在 `c10f6ed59966401684851f917f9137b0a6cf12ae` 合入 B01/B02/B04 补丁，六项 ROS 接线回归及 C++ Action Mock 复验通过；整体仍有失败。** 旧 Python 任务链路未通过，独立 MoveIt 规划执行通过但退出失败。上游合并是本次观察到的事实，本项目没有执行合并或推进 `robot/fsm-baseline.repos`，正式锁定仍为 `1d940f7…`。来源 TEAMMATE-MERGE-20261011；本机实测 ENV-WIRING-MERGE-20261011。

按 USER-HW-20261011-08、USER-HW-20261011-09 的监测与回执安排，23:36:32（上海时间）启动固定复现，23:41:09 收集并停止原容器。主对话 23:41:17 的 ack 为 `CLAIMED`，已输出 `MOVEIT_WAKE_ACK_12b18c00b7d84e96e4835f8d22aef486`；一轮 queue 投递到持久化回执约 8.17 秒。本轮未调用 queue 或另启监测。

## 真实变更

Git 合并的两个父提交是 `c0f70172e4b0271046d5f52813e0730d40ae772a` 与原 PR #2 的 `1d3dccf23c53d299d457564daeb6438190ea2d77`。相对前者仅变更五个文件：README、接线复验说明、两个 Python 外壳和 `tests/test_ros_wiring.py`。两个生产文件、测试及说明与原 PR 提交逐字节相同；安装后的 Python 文件也与本次源码一致。

四个 C++ 核心包、`mtc_ros2_action_cpp`、ROSIDL、驱动手册及 Fake 补丁均未变。三项修复分别为 Task 独立 `_fsm_clock`、配置字段 `perception_max_age_s` 映射和默认 `/mtc/tool/trigger_unlock` 服务名。原提交与历史失败保留于 ENV-FSM-FIX-20261011，不把合并当作完整任务验收。

维护者在合并说明中表示认可三项补丁，并提出后续转向 C++ Mock Bringup、随后对接 MoveIt/执行层。这是有出处的上游交接意见，保存于冻结 `source-review.json`；不作为对助手的新增指令或用户决策。本事件只复验实际交付的已有入口，没有另行开发统一 Bringup、修复旧 Action 内核或扩大职责。

## 检查与补跑

固定运行和补跑均在 Ubuntu 24.04 / Jazzy、无网络/设备/挂载/端口、2 CPU / 4 GiB、512 PID、cap-drop ALL / no-new-privileges 容器中进行。补跑使用已停止原容器的独立文件系统快照，未重启原容器；每步串行执行，下一 SHA 仍由主对话回执门禁约束。

| 检查 | 本次结果与证据（相对冻结目录） |
| --- | --- |
| 工作空间构建 | **13 包 PASS**；`automatic/logs/build.log` |
| C++ / Python / 显式纯 Python Mock E2E | **358 / 269 / 15 项 PASS**；20 个独立 C++ 测试程序，保留原 318 个身份；`supplement/automatic-counts.json`、原 XML、E2E 日志 |
| B01/B02/B04 ROS 回归 | **6 PASS / 0 FAIL / 0 SKIP**；`automatic/container/ros-wiring.xml`，本次已执行，不再是前一候选的文件缺失 NOT RUN |
| 补跑交付的新 C++ 审计入口 | **PASS**；`supplement/logs/identity.log`。固定旧入口仍因写死 16 个程序返回 1，原失败保留；不是 C++ 测试失败 |
| 安装文件 / 合并范围 | **PASS**；两个 Python 外壳安装字节与源码一致；四个核心、新 Action、IDL、驱动输入未改；`supplement/container/installed-python-identity.json`、`supplement/source-review.json` |
| C++ 独立程序 | **四场景 / 40 条断言 PASS**；`supplement/container/standalone/summary.json`，使用未修改的 `robot/probe_cpp_actions.py` |

六项 ROS 回归只覆盖三项接线：配置测试在真实参数和配置构造后主动停止，工具测试使用合成的 Mock 生命周期输入；解锁受理后仍断言未验证释放。不能以这六项通过宣布 PickPlace 已启动或实体卸载成功。

C++ 补跑在独立域 110–113 确认唯一服务器：启动空闲 7 秒后基础 T0 成功、随后三色 `[3,1,2]` 保序完成 P1/P2/P3；关联 Task 取消为 CANCELED / 0；缺少子服务器时 ABORTED / 220 并锁定后续 Goal；独立 Motion 单点与结果交付窗口的关联取消通过。六次服务器进程均 SIGINT 退出 0，无升级终止和残留 Mock 节点。Task→PickPlace 使用 ROS Action，PickPlace→Motion 仍为本地 Mock；取消仅证明受信 Mock 约定，未接通 MoveIt/FJT/实体停稳。

UBSan 与外部 CMake consumer 本次**未重跑**：相关 C++、构建文件和接口未变，其历史通过记录只引用 ENV-CPP-ACTION-20261011，不计入本次新增运行。TSan 仍未完成。

## 失败与退出复核

| 入口 / 问题 | 实际结果与分析 |
| --- | --- |
| 旧 Python 尽早 Goal | Task 已启动并受理；PickPlace 因 B05 的 `ExecuteJointMove.create_client` 不存在退出 1；最终 ABORTED / 220，完成数 0 |
| 旧 Python 延迟 7 秒 Goal | Goal 前 INIT 已超时进入 FAULT；Goal 受理后 ABORTED / 510，完成数 0（B06） |
| 旧 Python Cancel | 关联取消受理，随后 ABORTED / 520，消息为子任务未报告停稳；不能按取消受理算成功 |
| 旧 Python 清理 | `safety_supervisor` 出现 `rcl_shutdown already called` 并退出 1；各 launch 的 0 不抵消子进程失败。B03 被 B05 遮挡，仍未运行到该分支 |
| 工作空间 rosdep / 驱动依赖 | 旧包 `ament_python` 键未定义；缺 `ros-jazzy-ros2-controllers-test-nodes`、`docker.io`。驱动测试汇总 1104 / 279 failures / 259 skipped 含 lint 和外层记录，不是独立功能用例数 |

实际 Python 三场景都有逐节点服务器、Goal/Feedback/Result，见 `automatic/container/task-mock/`。B01/B02/B04 通过与 B03/B05/B06 未解决并不冲突；旧路径问题继续保留并由模块负责人处理，本轮没有修改其实现。

本轮新增观测到控制器退出崩溃，因此在相同驱动、模型、镜像快照及隔离限制下，用原探针额外复跑一次，未改变退出顺序或放宽判据：

| 独立 MoveIt / GenericSystem | 固定复现 | 主对话补跑 |
| --- | --- | --- |
| Plan → Execute | PASS，status 4 / MoveIt code 1 | PASS，status 4 / MoveIt code 1 |
| 肩关节目标增量 / 最大目标误差 | +0.05 rad / `0.00009758972660638392 rad` | +0.05 rad / `0.00009342823652550579 rad` |
| 不同关节反馈时间戳 | 210 | 208 |
| `move_group` SIGINT 退出 | **-11，FAIL** | **-11，FAIL** |
| `ros2_control_node` SIGINT 退出 | **-11，FAIL** | **0**，此前崩溃本次未重现 |

原始文件为 `automatic/container/moveit/{result.json,move-group.log,control.log}`；补跑为 `supplement/container/moveit-repeat/`。两次 launch 外层均为 0，探针均因子进程退出异常返回 1，均不算干净退出。`move_group` 堆栈涉及 MoveItCpp / TrajectoryExecutionManager / rclcpp CallbackGroup 析构。原控制器在 shutdown 日志后，堆栈仍位于 ControllerManager / JointTrajectoryController::update → Trajectory::time_from_start → rclcpp::Time，伴随无效 context 日志；一次失败、一次正常退出不足以判定根因或宣称修复。此独立驱动链路未加载新 C++ FSM，不能将崩溃归因于本次两处 Python 补丁。

本地编排有一次在准备完成前调用尚未复制的 `run_step.py`，返回文件不存在；该次未启动补跑。记录保留于 `supplement/preparation-note.json`，准备完成后按原入口运行；没有覆盖失败或计为功能用例。

## 清理、交接和证据

补跑后已停止 ROS domain 99 的 CLI daemon，确认容器进程表只剩 keeper 再停止容器。原容器和补跑容器均停止，无 OOM，旧 runner PID 已不存在；keeper 137 不混作 ROS 子进程崩溃。清理记录、逐步命令/时间/退出码和 inspect 均归档。

原 summary 的步骤、结束时间、stop/collect 信息完整；**291 个原索引文件逐个校验通过**，原 index SHA-256 为 `7001dd1105bfecf9d2968be52bae8824fccc35d73ba4ca6f05bf855b5ec976a7`。保留原 `COMPLETED_WITH_FAILURES`，新结果另存；source.bundle、镜像、SDK 和构建二进制不入库，来源 SHA 保留。

新增[冻结索引](experiments/wiring-merge-20261011/index.json)、[输入](experiments/wiring-merge-20261011/inputs.json)、[摘要](experiments/wiring-merge-20261011/summary.json)及[协议](experiments/wiring-merge-20261011/protocol.md)，index SHA 登记于 `materials/manifest.json`。原始路径：

- 固定复现：`outputs/moveit-watch-20261011/runs/sha-c10f6ed59966401684851f917f9137b0a6cf12ae/`。
- 本轮补跑：`outputs/wiring-merge-acceptance-20261011-c10f6ed/`。
- 最终回执：`outputs/moveit-watch-20261011/wake/sha-c10f6ed59966401684851f917f9137b0a6cf12ae/receipt.json`。冻结的是 complete 前快照，完成证据登记后才提交 complete；终态以该实时回执为准。

按 SPRINT-PLAN-20261011 §01、§06–07、USER-HW-20261011-03，FSM/Action/Cancel 内核仍归孙嘉明；本地交接保留 B03/B05/B06、Mock 停稳契约、完整 MoveIt/FJT 与唯一执行权缺口，不代发外部消息。驱动退出异常与依赖/lint 在集成问题单保留，不能以规划成功关闭。完整状态发布、Web UI、视觉/工具证据、NUC/实机、SDK 许可/厂商校验值、TSan 和既有许可证差异均未由本轮解决。旧证据和正式版本锁定保持原状，监测时段仍截至 2026-10-12 08:00（上海时间）。

生成式 AI 披露：OpenAI Codex 协助审阅 Git 变更、调用已有 ROS 验收探针、分析日志与整理事实链；未新增或修改上游 FSM/规划/驱动算法。上游来源与许可沿用 TEAMMATE-MERGE-20261011、TEAMMATE-ACTION-20261011、TEAMMATE-SDK-20261011，保留原声明，不重新授权。
