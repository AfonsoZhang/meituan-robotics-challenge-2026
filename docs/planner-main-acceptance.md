# 规划 PR #3 合入主线后的验收与就绪诊断

**结论：主线合并源码核验与离线回归通过；默认独立 MoveIt 执行失败，唯一一次等待诊断通过，退出仍失败。完整 FSM/实机尚未验收。**

上游 `main@f7eaa2c0d2887aeada4fd635112c63c237962ff7` 于 2026-10-12 01:09:48（上海时间）合入规划 PR #3，登记为 TEAMMATE-PLANNERMAIN-20261012；本项目观测为 ENV-PLANNER-MAIN-20261012。监测完成固定复现后一次投递，主对话约 **5.93 秒**签收。本轮依 USER-HW-20261011-08、USER-HW-20261011-09 审阅、补验与归档，未代为合并、修复内核或改变 `robot/fsm-baseline.repos` 的正式锁定 `1d940f7c5f12561fed6641457c0b4b630a282b05`。

**实际变更与补跑取舍。** 双父提交为 `a04ac68…` 和 `4a1a816…`，相对此前 main 新增 53 个原规划源码/交付文档/证据文件。整个 Git tree（含路径、模式和内容）与已经验收的 `4a1a816…` 完全相同，tree ID 均为 `60a32b660177f50307c18ca3ae00432fcac0f282`；没有新增运行入口。前次 ENV-PLANNER-MERGE-20261012 的 486 个冻结文件、索引 SHA 和签收报告均重新核验一致，固定环境与 harness 元数据也相同。

因此，本轮不重复相同源码的规划采证 SOP、C++ 独立四场景、UBSan 和外部 consumer；历史补跑结果仍见[合并安装环境验收](planner-merge-acceptance.md)。其中默认固定姿态通过、V1 约 42.0717 秒超过 24 秒预算、V2 TF_UNAVAILABLE，以及四场景 40 项检查通过，**均是前次结果，未移记为本轮复跑**。本轮额外核对实际安装身份和交付的审计入口，并针对新出现的 MoveIt 执行失败做一次有界诊断。

该主线仍是原规划版本，未包含 `30e3c6e…` 场景/载荷/起点增量或 `0e329f1…` 视觉适配器分支；这两组验收分别见 ENV-PLANNER-SCENE-20261012、ENV-VISION-ADAPTER-20261012。当前 PickPlace 仍绑定 `MockPlanner` / `AsyncMockMotion`，不能以 PR 合入证明实际 PlannerPort/FJT 已接线。

**本次实际运行结果。** 原固定复现为 01:26:35—01:31:41；补跑沿用已停止原容器的独立快照、Ubuntu 24.04 / Jazzy / C++17、驱动 `53aab837…`、模型 `47fa5e02…`、MoveIt 2.12.4。两容器均无网络/设备/挂载/端口，2 CPU / 4 GiB / 512 PID、cap-drop ALL、no-new-privileges。没有安装新依赖、改上游源码或调整控制/规划参数。

| 检查 | 实际结果与范围 |
| --- | --- |
| 固定运行完整性 | 25 步均有起止时间与退出码，stop/collect 成功；原 `COMPLETED_WITH_FAILURES` 保留，305 个原始文件哈希匹配 |
| 构建 | 14 包通过 |
| C++ GTest | **387 / 24 个程序通过**：核心 318 + Action 40 + Planner 29；每个 XML 用例与源码身份对应，无重复、失败或跳过 |
| Python / 显式 Mock E2E / ROS 接线回归 | **269 / 15 / 6 通过**，本次实际运行 |
| 固定旧 C++ 审计 | 失败：预期 16 个 `*_cpp` 程序，实际 20；missing/unexpected/duplicates/bad 均为空 |
| 交付的新审计入口补跑 | **358 / 20 通过**；其匹配规则不含规划包，规划 29 / 4 另行核验 |
| Action/Planner 依赖及安装身份 | 两包 rosdep 通过；五份 package/config/launch 与源码逐字节一致 |
| 全工作空间与驱动依赖 | 仍缺 `ament_python` rosdep 定义；驱动缺 `docker.io` 和 `ros-jazzy-ros2-controllers-test-nodes` |
| 驱动测试 | 汇总 1104 条、279 failures、259 skipped，含 lint/包装；失败仍涉及 description 的 flake8/lint_cmake/pep257/xmllint 和生成 C 的 uncrustify |

colcon 汇总 685 条包含 CTest 包装及接口 lint，不当作 685 个独立功能用例。两个包依赖通过不能覆盖全空间依赖失败。

**默认 MoveIt 执行失败及一次等待诊断。** 原固定探针已确认 GenericSystem、活动控制器和唯一 FJT 服务端，规划返回成功。ExecuteTrajectory 也受理 Goal，但随后返回 **ABORTED（6）/ MoveIt -4**。`move-group.log` 明确记录：`Action client not connected to action server: joint_trajectory_controller/follow_joint_trajectory`，接着发送轨迹失败；控制器日志没有收到 Goal。内部控制器加入日志到连接错误约 **0.342 秒**。探针在结果断言处退出，没有最终关节误差数据，不能记为目标已执行。

这说明“外部能发现 FJT、控制器 active、MoveIt 对外 Action 可用”不足以证明 MoveIt 内部的 FJT 客户端此时已连接。它是本轮运行的真实失败，整树源码相同也不能用旧成功覆盖。

诊断只改复制到临时目录的本地探针：使用隔离域 131，在原有 20 次 `spin_once` 之后再按单调时钟等待并 spin **5 秒**，实际 5.0034 秒。保留所有上游代码、控制器/规划配置、容差、状态预算和原结果门槛；上限 180 秒、外层 210 秒，实际约 26 秒结束，未超时、未继续重试。

| 项目 | 原固定运行 | 单次等待诊断 |
| --- | --- | --- |
| 规划 | 成功 | 成功 |
| 执行 | ABORTED / -4，内部客户端未连接 | **SUCCEEDED / 1**，控制器收到 Goal 并完成 |
| 最大目标关节误差 | 未测得 | **0.0000887972763273865 rad**，门槛 0.001 rad |
| 不同关节反馈时间戳数 | 未写出该统计 | 1210，包含等待与执行观察窗口，不是单独执行阶段计数 |
| `move_group` / `ros2_control_node` 退出 | **-11 / 0** | **-11 / 0** |
| 总体探针退出 | 1 | 1，因干净退出仍失败 |

一次新进程运行中加入等待后通过，**支持就绪时序假设，不能证明具体竞争根因、固定 5 秒可靠或生产问题已修复**。当前应补足可核验的内部执行就绪条件；尚未修改固定监测脚本或模块实现。两轮 MoveIt 的 -11 都在原日志中保留，launch 包装退出 0 不代表其子进程干净退出。

**旧 Python 与交接范围。** 本次早 Goal 为 ABORTED / 220，延迟 Goal 因 INIT 超时为 ABORTED / 510；Cancel 已受理，最终为 **ABORTED / 520**，消息为未在时限内确认子任务停稳，完成数 0。PickPlace 仍在 `ExecuteJointMove.create_client` 处退出（B05），B03 被启动失败遮挡，B06 未解除；Safety 重复 shutdown 仍在。前次 Cancel / 220 与本次 / 520 分开记录，不能解读为修复。

| 本地交接 | 尚未完成的工作 |
| --- | --- |
| 孙嘉明：FSM/Action/Cancel | B03/B05/B06、Cancel 520 与独立停稳确认；真实异步时限、唯一执行权、整条轨迹/FJT 和工具动作后的实际起点；不接管内核修复 |
| 常建烁：规划 | 默认 TF 就绪、V1 路径时长与状态预算协调，标定后的 TCP/工位/场景输入 |
| 系统集成与验收 | 内部 FJT 客户端就绪门槛、MoveIt/控制器退出、日志与依赖、符号限位实际求值；统一 Bringup、状态来源与 UI 联调 |

分工依据 SPRINT-PLAN-20261011 §01、§03、§06–07。以上为本地交接材料，未代发消息。完整 FSM、感知与工具消费链、场景/载荷分支集成、实际碰撞/接触、TSan、SDK 许可/厂商校验值、NUC 与实机均未验收；不把独立 Plan→Execute 扩大为完整抓放。根/规划 MIT 与 Action package.xml Apache-2.0 的声明差异继续保留。

**清理与证据。** 补跑进程退出后，清理守卫发现域 131 的 ROS CLI daemon，首次检查拒绝直接完成；其进程快照和守卫记录已保留。仅停止这个域的 daemon，再确认只剩 keeper，才停止容器。结束时原 runner 24525 不在，原/补跑容器均停止、无 OOM；keeper 的退出 137 与 ROS 子进程结果分别记录。

- [冻结索引](experiments/planner-main-20261012/index.json)：**450 文件**，SHA-256 `a6641cd712b8538b6dbc5a848359aa483e295e5e76a1c04ccd5453406d35ac9e`。
- [输入与版本](experiments/planner-main-20261012/inputs.json)、[结果摘要](experiments/planner-main-20261012/summary.json)、[验收协议](experiments/planner-main-20261012/protocol.md)、[树与文件身份](experiments/planner-main-20261012/supplement/source-review.json)、[诊断改动](experiments/planner-main-20261012/supplement/probe-diagnostic.patch)。
- 原日志：`outputs/moveit-watch-20261011/runs/sha-f7eaa2c0d2887aeada4fd635112c63c237962ff7/`；原 index SHA-256 `b487c3f35c8e1207fb3b26b31d6916bcf12fedc98db075dc9c74d602e736e580`。
- 补跑与分析：`outputs/planner-main-acceptance-20261012-f7eaa2c/`；诊断原始结果在 `container/moveit-wait5/`，命令/退出在 `logs/`。
- 回执：`outputs/moveit-watch-20261011/wake/sha-f7eaa2c0d2887aeada4fd635112c63c237962ff7/receipt.json`；冻结 complete 前状态，最终回执只存 raw，不回写冻结集。

原始失败与前序冻结/已签收报告保持不变；source.bundle 仅登记哈希，镜像/SDK/构建二进制不入库。既有监测仍按 60 秒轮询、固定主会话、上海时间 10 月 12 日 08:00 截止；本轮未调用 queue 或新启监测。事实链核验后登记 complete，再由原脚本解除下一 SHA 的串行门禁。

生成式 AI 披露：OpenAI Codex 协助比较 Git 树、核验实际测试身份、在本地验收探针中增加一次有限等待诊断、清理与整理事实链；未修改上游规划/FSM/Action/Cancel/驱动算法。来源 TEAMMATE-PLANNERMAIN-20261012、TEAMMATE-INTEGRATION-20261012、TEAMMATE-PLANNER-20261011、TEAMMATE-ACTION-20261011、TEAMMATE-SDK-20261011。
