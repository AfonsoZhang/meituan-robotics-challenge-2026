# FSM 阶段验收 2026-10-11

后续接线补丁：B01/B02/B04 已提交独立 PR 并完成定向复验，结果和新发现见[补丁复验报告](fsm-wiring-fix.md)（ENV-FSM-FIX-20261011）。以下保留原固定基线的验收结论与失败证据。

**离线核心通过，现有 ROS Mock 任务链路未通过。** 本轮按用户上一轮确定的四项清单，实际复跑固定提交 `1d940f7c5f12561fed6641457c0b4b630a282b05`。Jazzy 下 12 包构建、318 项 C++、269 项 Python、15 项纯 Python Mock E2E 均通过；实际启动时 Task、PickPlace 两个 Python 节点退出，基础任务 Action 不可用。独立 Fake 驱动的控制器、关节/TF 与单点、多点轨迹检查通过。

本项目运行证据登记为 **ENV-FSM-20261011**，与上游报告 TEAMMATE-FSM-20261011、TEAMMATE-SDK-20261011 分开。原始运行目录为 `outputs/integration-20261011-164931-1d940f7/`；可入库的命令、结果、失败日志和测试 XML 见[冻结证据](experiments/fsm-acceptance-20261011/index.json)。职责按 SPRINT-PLAN-20261011 §06–07：集成侧定位并留证，FSM/Action 修复交由孙嘉明。

## 四项清单的结果

| 项目 | 结果 | 实际证据与范围 |
| --- | --- | --- |
| 版本与接口交付 | **FAIL：交付尚不自洽** | 源码锁定、12 包与 12 份 IDL 清单、SDK 声明、Fake 补丁一致性通过；发现启动接口和 V2 解锁名称不匹配，见问题单 |
| 纯 Python Mock | **PASS** | 269 项 pytest、15 项显式 E2E；无用例失败或跳过。Python 3.10 主机与 Python 3.12 Jazzy 容器分别复跑，不能重复累计为不同场景 |
| 四个 C++ 核心包 | **PASS** | Jazzy/C++17，318 个独立 GTest 用例、16 个可执行文件，保留原 290 项并执行新增 28 项；无失败或跳过。Humble 补充检查单列 |
| 独立 Fake 驱动 | **PASS** | 5 包构建成功，唯一 GenericSystem、两控制器 active、六关节位置/时间戳与两段 TF 正常；单点与多点 FollowJointTrajectory 均成功，最终误差 0 rad |

`colcon test-result` 的 **608** 包含 CTest 包装及 lint 条目；测试用例为 **318 + 269 + 15 = 602**，不把包装项或两套环境的重复执行计作新增覆盖。E2E 的 `mtc_motion_planning` 依赖提示不可用，但 15 个用例使用自带 MockPlanner，最终 `PASS 15 / FAIL 0 / SKIP 0`；这不代表 MoveIt 已接通。

## 运行环境与来源

| 项目 | 本轮记录 |
| --- | --- |
| 开发主机 | Ubuntu 22.04.5 / WSL2，原有 ROS 2 Humble、Python 3.10.12、GCC 11.4 |
| 正式离线复跑 | 独立 Docker 容器内 Ubuntu 24.04.5 / ROS 2 Jazzy、Python 3.12.3、GCC 13.3、CMake 3.28.3；与 NUC 分开 |
| 镜像 | `ros:jazzy-ros-base`，实际固定 digest `sha256:066420e07f60aa18262f2479981def87ebcfcec42eefb0c0c57c4a46098348ca` |
| FSM | `1d940f7c5f12561fed6641457c0b4b630a282b05`，测试前后源码工作树干净；未修改上游 FSM/Action |
| 驱动 | `53aab83735236f0c262ecb11e04ef2600241d9d9`；模型 `47fa5e02fa873f27f7e812d31f31e3f4cf5e56b1` 加已交付 Fake Xacro 补丁 |
| 隔离 | 容器不挂载设备、不发布端口；ROS Mock domain 93，独立驱动 domain 94，发现范围 LOCALHOST；Fake 运行前已断开容器外部网络 |

依赖包的实际版本另存证据，不把本轮容器当作与上游机器逐包相同的快照。新建目录保留了历史工作空间；容器和日志用于本机复现，不证明 NUC 已部署。验收容器 `mtc-acceptance-20261011-164931` 已停止并保留。

## 独立 Fake 驱动观测

本轮按 TEAMMATE-SDK-20261011 固定源码与补丁，普通复制安装 5 包。`aubo_moveit_config` 仅安装配置文件；本轮准备的是独立 Fake 所需运行依赖，未据此认定完整 MoveIt 依赖齐全或 Plan → Execute 通过。

- 硬件组件仅 `mock_components/GenericSystem`，`joint_state_broadcaster` 和 `joint_trajectory_controller` 都为 active；配置/运行日志为 200 Hz，不是硬实时性能认证。
- 采到 1,610 条时间戳不同的 JointState；按关节名称映射六个有限位置。`world → base_link`、`base_link → ee_link` 两段 TF 成功查询。
- 单点：wrist3 从 0 到 0.03 rad，3 秒；多点：同一 Goal 内 0.015 rad / 2 秒、0 rad / 4 秒。两次均为 Action `SUCCEEDED`（4）、`error_code=0`，观测最终误差 0 rad，满足本轮工程门限 ≤0.001 rad。
- GenericSystem 未提供 effort 状态接口，原始 JointState 的 effort 为 NaN；原文保存在 `fake-smoke/result.raw.txt`，标准 JSON 投影为 null 并附转换说明。通过结论针对位置、时间戳、TF 与轨迹结果，不包括力矩反馈。

SDK 实际文件为 `aubo_sdk-0.24.1-rc.3-Linux_x86_64+318754d.zip`，22,312,004 字节，观测 SHA-256 为 `b76fc5024c4e2a91a6b55e4217ce326a3c263ae53091526eedce3eab46609e80`；VERSION 为 `0.24.1-rc.3+318754d`。驱动构建及安装库的 `ldd` 解析通过。此哈希是本机观测值，未与厂商独立发布的校验值比对；许可仍待核对，未加载真实 AUBO 硬件插件或连接控制柜。

这是理想状态跟随器的独立轨迹验收，不包含物理动力学、抓放、MoveIt 规划、完整 FSM、取消/断流故障注入或实机性能。完整依赖检查、驱动自动测试与 SDK/控制柜兼容性仍保留为后续项。

## 实际 ROS 通信与基础 Goal

固定版本 `mock_bringup` 启动五个 **Python** 节点；四个 C++ 包仍是核心库。两次启动均复现相同的 Task/PickPlace 启动故障。第一次 CLI 的 Action/Service 列表为空，第二次用独立 rclpy 节点等待发现后直接取 graph，确认 Motion Action 和工具服务存在；保留两次原始记录，避免把首次空列表当作接口不存在。

| 接口或节点 | 实际观测 |
| --- | --- |
| `/motion_executor`、`/tool_manager`、`/safety_supervisor` | 存活，来自现有 Python 外壳 |
| `/task_executor` | 启动退出 1，时钟成员冲突 |
| `/pick_place_server` | 启动退出 1，配置关键字错误 |
| `/mtc/motion/execute_joint_move` | `mtc_interfaces/action/ExecuteJointMove`，已发现 |
| `/mtc/robot/state`、`/mtc/tool/state`、`/mtc/safety/interlock_state` | 类型分别为 RobotState、ToolState、RobotState，已发现 |
| `/mtc/tool/trigger_unlock` | `mtc_interfaces/srv/TriggerUnlock`，已发现 |
| `/mtc/task/execute`、`/mtc/manipulation/pick_place` | 不可用；对应节点已退出 |
| 感知与 TF | 此 Mock 组合未观察到 `/mtc/perception/batteries`、`/tf`、`/tf_static`；不替代视觉/标定交付 |

预定基础 Goal 为 `task_id=acceptance-20261011-basic-yellow`、`mode=1`、`ordered_colors=[3]`、`timeout_ms=5000`、`placement_stability_sec=3.0`。黄色只是验收输入。**客户端等不到任务服务器，Goal 未发送**，没有受理、Feedback、Result 或任务错误码；不能将节点进程退出码写成 Action 错误码。日志采集脚本退出 0 只说明完成了采集，基础任务烟测仍为 **FAIL**。

## 阻断问题单

| 编号 | 证据与影响 | 负责人及解除条件 |
| --- | --- | --- |
| B01 | `task_executor.py:178` 将 `self._clock` 设为函数，覆盖 rclpy Node 的 Clock；`_ros_clock()` 调用 `get_clock().now()` 报 `AttributeError: 'function' object has no attribute 'now'`。两次真实 Jazzy 启动复现 | 孙嘉明；避免覆盖 Node 成员，复跑真实节点启动与 ExecuteTask Goal/Feedback/Result |
| B02 | `pick_place_server.py:651` 传入 `perception_max_age_sec`，`PickPlaceConfig` 实际字段为 `perception_max_age_s`，构造时报 TypeError；两次启动复现 | 孙嘉明；对齐配置字段，增加真实入口验收，再复跑 PickPlace Action |
| B03 | `PickPlaceServer` 构造中调用 `action_type.Server(...)`；生成的 `mtc_interfaces.action.PickPlace` 实测没有 `Server` 属性。这是被 B02 遮挡的后续接线缺陷，未声称启动已走到此行 | 孙嘉明；使用真实 rclpy ActionServer 绑定并验证 Goal/Cancel/Result，不能只使用离线 CallbackActionType 替身 |
| B04 | 客户端默认 `/mtc/tool/unlock`，实际服务 `/mtc/tool/trigger_unlock`；Mock launch 无 remap，V2 解锁接口不一致 | 孙嘉明；统一名称或显式 remap，并复核 V2 请求与独立释放证据；不影响 V1“无需电磁 IO”的定义 |

以上均定位于 TEAMMATE-FSM-20261011 / TEAMMATE-SDK-20261011 对应的固定源码，具体路径、行号、运行日志见冻结证据。问题单尚未代发给队友；验收过程中没有改动这些模块。

## 复现与后续验收

在独立 Jazzy 工作空间导入 [robot/fsm-baseline.repos](../robot/fsm-baseline.repos)，依照固定版本 README 构建、测试，再显式执行 `tests/verify_cpp_audit_results.py` 和 `tests/test_mock_end_to_end.py`。本轮的实际命令、退出码与 Docker 编排脚本均保存在冻结证据中，源码、SDK 二进制和构建目录不入库。

运行 Mock 的最小入口（只适用于独立测试环境）：

```bash
source /opt/ros/jazzy/setup.bash
MTC_ACCEPT_WS="$HOME/mtc_fsm_acceptance_ws"  # 改为本次独立工作空间
source "$MTC_ACCEPT_WS/install/setup.bash"
export ROS_DOMAIN_ID=93 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
ros2 launch mtc_bringup mock_bringup.launch.py backend:=mock
```

当前该命令应复现 B01/B02，不能作为已通过的整体启动 SOP。修复后需保存新提交号，重新检查 graph、基础任务与取消；新 C++ Action、MoveIt/整条轨迹适配和完整 FSM 闭环仍按各模块交付情况验收。TSan、实体末端、控制柜兼容、相机/TF 标定和 NUC 实机结果均未由本轮证明。

生成式 AI 披露：本轮使用 OpenAI Codex 执行源码核对、构建和测试，编写日志采集与 Fake 验收脚本，整理本报告及来源索引。上游 FSM 根 LICENSE 为 MIT，各包 manifest 的许可声明另存输入清单；驱动、模型与 SDK 许可分别记录，不统一视为 MIT。仅在独立模型副本应用 TEAMMATE-SDK-20261011 已归档的 Fake 补丁，原始资料、历史冻结实验及上游 FSM 源码保持原状。
