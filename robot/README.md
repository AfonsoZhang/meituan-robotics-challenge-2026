# NUC 实机接入

当前开发目标：**Ubuntu 24.04 / ROS 2 Jazzy / C++17，FSM Core v0.1**（USER-HW-20261011）。用户提示 SDK 已补充后（USER-HW-20261011-04），当前源码锁定为 `F1u0rite/meituan_challenge_ws@1d940f7c5f12561fed6641457c0b4b630a282b05`（TEAMMATE-SDK-20261011）。其父提交为初始 TEAMMATE-FSM-20261011 的 `f477f689…`，仅增加部署文档，未改 FSM/接口代码；[接入计划](../docs/hardware-vision-plan.md#5-软件组织与验证顺序)从离线回归推进到 C++ Action / MoveIt / Mock Hardware。本项目尚未完成该链路或 NUC 部署。

个人职责已明确为**系统集成与验收，兼做 Web UI**（USER-HW-20261011-03）。v2 任务书要求复现 Mock 启动、核对实际 ROS graph，并按驱动 SOP 在独立 Fake Hardware 环境留存关节/控制器/Action 证据（SPRINT-PLAN-20261011 §06）。上游已提供该 SOP，本轮已完成独立 Fake 复验并保存实际 ROS Mock 启动失败证据（ENV-FSM-20261011）。`/home/aaet/aubo_driver_validation_ws` 为上游只读参考路径；本项目使用自己的隔离容器，不能直接套用下方历史 Humble 命令。具体交付见 [系统集成与验收计划](../docs/hardware-vision-plan.md#7-系统集成与验收主责)。


新版 [实机操作台](../webui/README.md) 已按 USER-HW-20261011-07 接入 Jazzy ROS 客户端：ExecuteTask、取消、RequestStop、Task/Robot/ToolState、关节、RGB-D 与日志。`bash webui/run.sh` 默认 source 仓库记录的 `/home/aaet/meituan_challenge_ws/install/setup.bash`，可用 `MTC_UI_SETUP` 覆盖；ROS domain 从实机环境或显式配置取得，未提供时显示离线。客户端不启动驱动或使能机器人；隔离接口检查通过（ENV-WEBUI-ROS-20261011），NUC 部署与实体设备联调仍待验，详情见 [实现与验证](../docs/web-ui.md)。

## SDK 与 Jazzy 驱动资料已核对

来源：TEAMMATE-SDK-20261011（2026-10-11 查阅），[固定版本部署手册](https://github.com/F1u0rite/meituan_challenge_ws/blob/1d940f7c5f12561fed6641457c0b4b630a282b05/docs/setup/AUBO_ROS2_DRIVER_JAZZY.md)。本次新增的是 SDK 依赖、驱动部署与验证说明；SDK 二进制由官方驱动的 CMake FetchContent 下载，未作为此提交新增文件入库。

| 项目 | 已核对的输入 | 仍需完成的本项目验证 |
| --- | --- | --- |
| 官方驱动 | `AuboRobot/aubo_ros2_driver` 的 Jazzy 提交 `53aab83735236f0c262ecb11e04ef2600241d9d9` | 本轮独立 Jazzy 容器 5 包构建通过；完整运行依赖与实体设备兼容性仍待核验 |
| SDK 构建依赖 | `aubo_sdk-0.24.1-rc.3-Linux_x86_64+318754d.zip`；已直接核对该驱动提交的 [CMakeLists.txt](https://github.com/AuboRobot/aubo_ros2_driver/blob/53aab83735236f0c262ecb11e04ef2600241d9d9/aubo_ros2_driver/CMakeLists.txt) | 本轮下载/链接通过，包 SHA-256 见[阶段验收](../docs/fsm-acceptance.md)；官方构建未设 `URL_HASH`，厂商校验值、许可及控制柜兼容性仍待核对（ENV-FSM-20261011） |
| 模型与 Fake 修复 | `aubo_description@47fa5e02fa873f27f7e812d31f31e3f4cf5e56b1` 加手册链接的 Xacro 补丁；Fake 分支选择 `mock_components/GenericSystem` | 纯上游 clone 缺该修复；本轮独立副本应用补丁、核对字节后已实际展开 Xacro，并启动唯一 GenericSystem（ENV-FSM-20261011） |
| 独立驱动/MoveIt SOP | 手册 §04–10：环境隔离、Fake 控制器、JointState/TF、MoveIt/RViz、轨迹与退出检查 | 本项目独立 Fake 控制器、关节/TF、单点和多点轨迹 `PASS`；MoveIt Plan → Execute 仍为 `NOT RUN`（ENV-FSM-20261011） |
| 完整 FSM 集成 | 手册 §11 的 Action/Planner/MotionAdapter 边界 | C++ Action、完整轨迹适配及端到端任务仍待接入；独立 MoveIt Mock 成功不计为 FSM 抓放通过 |

复现时先取得包含 Fake 修复的独立源码副本，再核对 overlay、模型、唯一 GenericSystem 和同一 ROS domain，最后按手册三终端流程检查。控制 launch 必须明确指定 S3 与 Fake 参数；`aubo_moveit.launch.py` 未声明 `use_fake_hardware` 参数，不向它补造参数。手册使用的 `ROS_DOMAIN_ID=91` 是该 SOP 的隔离示例，原 demo 的 67 仍仅用于历史仿真。

本轮结果与原始命令见[阶段验收](../docs/fsm-acceptance.md)（ENV-FSM-20261011）。独立 Fake 的 5 包构建、两控制器、六关节反馈、两段 TF 和两次完整轨迹通过；GenericSystem 是理想状态跟随器，不代表实机或物理仿真。当前仍缺完整 MoveIt 运行依赖（含 `joint_state_publisher_gui`）、MoveIt Plan → Execute/退出复核、驱动自动测试、SDK 许可/厂商校验值及 NUC/控制柜兼容性。上游原始日志路径继续只属于上游机器。

## 固定源码版本

有限接线修复已按 USER-HW-20261011-05 提交 [PR #2](https://github.com/F1u0rite/meituan_challenge_ws/pull/2)，候选提交为 `1d3dccf23c53d299d457564daeb6438190ea2d77`。B01/B02/B04 的 6 项 ROS 回归及既有 269 Python / 15 Mock E2E 通过，但仍有 B03/B05/B06，整体任务未通过（ENV-FSM-FIX-20261011，见[补丁复验](../docs/fsm-wiring-fix.md)）。该 PR 尚未合并，下面的正式版本锁定未推进。

[fsm-baseline.repos](fsm-baseline.repos) 只固定源码版本。在已有 `vcstool` 的环境中，从本仓库根目录导入到独立目录：

```bash
MTC_BASELINE_DIR=$(mktemp -d "$HOME/mtc_fsm_baseline-XXXXXX")
vcs import "$MTC_BASELINE_DIR" < robot/fsm-baseline.repos
git -C "$MTC_BASELINE_DIR/meituan_challenge_ws" rev-parse HEAD
# 应为 1d940f7c5f12561fed6641457c0b4b630a282b05
```

2026-10-11 初始 `f477f689…` 曾完成本机 `vcstool 0.3.0` 的临时目录导入校验；SDK 资料更新后，对新 `1d940f7…` 单独重做源码导入和 HEAD/工作树核对，结果登记于 TEAMMATE-SDK-20261011。上述两次导入只验证源码取得；随后本轮已在独立 Jazzy 容器复跑构建与离线测试，并复现现有 Python Mock 启动失败，见[阶段验收](../docs/fsm-acceptance.md)（ENV-FSM-20261011）。`vcs validate` 在初始完整 SHA 上触发过 `UnboundLocalError: version_type`，因此采用实际导入与 Git 提交核对，未修改系统工具。

构建和测试按该固定版本 README，在独立 Ubuntu 24.04 / Jazzy 环境中执行。上游根许可证为 MIT；代码使用时保留许可与修改记录。上游的离线结果、设备交接资料及路径只描述上游验证范围，不能作为本项目 NUC 的安装或连通证明（TEAMMATE-FSM-20261011，2026-10-11 查阅）。

## 历史 Humble 脚本的适用范围

本目录现有 `setup-nuc.sh`、`bringup_check.py`、`jog.py` 对应此前的 NUC 原生 Ubuntu 22.04 + ROS 2 Humble 方案，尚未迁移到 Jazzy。S3 用 `aubo_ros2_driver`，D435i 用 realsense-ros，规划用 MoveIt 的选择来自 USER-HW-20260923-02 至 -10；ROS / OS 的后续目标由 USER-HW-20261011 更新。NUC 实际安装状态待核验。这些脚本尚未在 NUC 与实机上运行；检查和点动只在开发电脑的历史仿真中试过。

## 历史驱动的已知行为（读过上游代码，提交 `85684075`）

- 连接控制柜 RPC 30004、RTDE 30010，用**写死的默认账号** `aubo` / `123456` 登录；控制柜改过密码就连不上。
- 连上后会写控制柜硬件参数 `vff_enable = false`（关速度前馈），这是**改动控制柜配置**，不是只读。
- 激活后进入伺服模式，并以当前位置作为保持目标：驱动一起来机械臂就处于受控状态。没有「只读不伺服」的启动方式。
- 控制柜不在 Running / 正常或缩减安全模式时，驱动拒绝下发并报错，需要先在示教器上处理再重启驱动。

## 历史 Humble 接入步骤（不适用于直接部署 Jazzy）

| 步 | 做什么 | 通过标准 |
| --- | --- | --- |
| 1 | `bash robot/setup-nuc.sh`（需要 sudo、外网；ROS 2 Humble 先按官方文档装好） | 构建完成；`python3 robot/bringup_check.py env --robot-ip <IP>` 除「与示教器一致」外全部通过 |
| 2 | 假硬件空跑：`ros2 launch aubo_ros2_driver aubo_control.launch.py aubo_type:=aubo_S3 use_fake_hardware:=true`，另开终端 `python3 robot/bringup_check.py driver` | 两个控制器 active，`/joint_states` 6 个关节 |
| 3 | 连实机（急停在手边，工作空间清空）：同上但 `use_fake_hardware:=false robot_ip:=<IP>`，再跑 `bringup_check.py driver` | 同上，且打印的关节角与示教器逐个一致（人工对照，记进报告） |
| 4 | 单关节点动：`python3 robot/jog.py --joint wrist3_joint --delta-deg 3`，确认后再 `--delta-deg -3` 回位；再逐个试其他关节 | 转的是所选关节，方向与符号一致，终点误差小；急停能停 |
| 5 | 相机：`ros2 launch realsense2_camera rs_launch.py align_depth.enable:=true`（参数名以 `--show-args` 为准），再 `python3 robot/bringup_check.py camera` | 彩色、深度、对齐深度都有数据；实际话题名与编码记在报告里 |
| 6 | 监控台：`bash demo/dashboard.sh --readonly --ros-domain-id <值> --presets <第 5 步生成的 dashboard-presets.json>`，开发电脑 `ssh -N -L 8766:127.0.0.1:8765 <用户>@<NUC>` | 开发电脑浏览器能看到画面、节点和关节角 |

每次检查的报告写在 `outputs/claude_bringup_<阶段>_<时间>/report.json`，退出码 0 全部通过、2 有未通过项。

点动脚本限幅：单次 ≤5°、时长 ≥5 s（≤1°/s），只动一个关节，执行前必须输入 `yes`。它不是碰撞检查，第一次请从末端关节开始。

## 出处与披露

`setup-nuc.sh` 锁定 `AuboRobot/aubo_ros2_driver` 提交 `85684075d6ff06c5385e39611208e99ebf0f94c6`（submodule `aubo_description` `47fa5e02`），不归档进本仓库；驱动构建时下载的二进制 aubo_sdk 0.24.1-rc.3 许可未核对（Q17）。realsense-ros 由 apt 安装（RS-ROS2）。本目录脚本由 Claude Code 编写，未复制第三方代码。

2026-10-11 使用 OpenAI Codex 协助登记 FSM 基线、添加源码锁定文件及标注历史脚本范围；未修改旧脚本、复制上游实现、启动驱动或连接设备。

同日按用户的 SDK 更新提示，使用 OpenAI Codex 核对新提交、官方驱动 CMake、版本指纹与补丁，在临时目录验证补丁和源码导入，并更新当前来源锁定与接入文档；未安装 SDK、构建或启动驱动。

阶段验收轮次：使用 OpenAI Codex 在独立容器完成 FSM 离线回归、5 包驱动构建及 GenericSystem 轨迹检查，记录 4 条 ROS 接入问题并冻结证据（ENV-FSM-20261011）。SDK 已由构建下载，观测哈希已登记；未连接实体设备。

接线修复轮次：使用 OpenAI Codex 准备 B01/B02/B04 补丁、真实 ROS 回归、两包 overlay 与实际 Mock 复验并提交 PR；证据为 ENV-FSM-FIX-20261011。本目录历史脚本、驱动及实体设备未改动或运行。
