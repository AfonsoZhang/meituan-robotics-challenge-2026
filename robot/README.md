# NUC 实机接入

**实机验收全部完成（2026-10-17）：** 用户确认“实机全部完成”（USER-HW-20261017），第 6–8 阶段亦已完成，见[阶段清单](../docs/hardware-vision-plan.md#real-hardware-acceptance-20261014)；现场版本、数值与日志待补充归档。

**实机验收进度（2026-10-14）：** 第 1–5 阶段（版本锁定、设备与安全、只读接入、标定与几何、空载运动）已由用户现场确认完成（USER-HW-20261014）。后续按[第 6–8 阶段清单](../docs/hardware-vision-plan.md#real-hardware-acceptance-20261014)验收停止/异常、单块闭环及三块/重复运行。现场 SHA、参数与原始日志路径待补充归档；该确认不表示下方历史 Humble 脚本已迁移到 Jazzy，也不表示完整 FSM 或带载任务已通过。下文记录保留各自日期与版本范围。

2026-10-12 当前状态同步：团队main `b418515`已合入标定与Phase 2B；新回归数字及PR #4/#9/#10、Phase 2C结果仅为上游报告，个人尚未复验。PR #8的C++ Mock/UI部分通过、C1未通过，完整FSM/实机未验收。团队手册记录的Fake验证环境为x86_64 / Ubuntu24.04.4 / Jazzy，NUC当前部署仍须现场核对；PR #11的新侧视试装外参仍UNKNOWN。Mac复验准备已终止清理，未执行测试。正式pin不变，详见[当前状态](../docs/current-status.md)（TEAMMATE-STATUS-20261012；ENV-STATUS-SYNC-20261012；USER-HW-20261012-03/04）。
**2026-10-13 主线复验：部分通过，整体验收未通过。** 固定main `b418515` 的15包构建、普通/UBSan各486项C++、269项Python及15/6/54项补充检查通过；并发重复第18轮出现M1断言失败（179次执行通过、1次失败，首败即停）。真实C++ Task→PickPlace基础/序列/及时取消通过，独立PR8 `7da4322` 的C1延迟取消再次ACK后6/520；旧Python220/510/520、原生Status/执行权BLOCKED及MoveIt退出-11仍保留。正式pin不变，无实机验收。实际源码、命令、UUID、清理与职责见[本轮验收](../docs/main-acceptance-20261013.md)（USER-HW-20261013-06，用户会话；TEAMMATE-MAIN-20261013；ENV-MAIN-ACCEPTANCE-20261013）。

2026-10-12 历史状态同步：团队main `b418515`已合入标定与Phase 2B；新回归数字及PR #4/#9/#10、Phase 2C结果仅为上游报告，个人尚未复验。PR #8的C++ Mock/UI部分通过、C1未通过，完整FSM/实机未验收。团队手册记录的Fake验证环境为x86_64 / Ubuntu24.04.4 / Jazzy，NUC当前部署仍须现场核对；PR #11的新侧视试装外参仍UNKNOWN。Mac复验准备已终止清理，未执行测试。正式pin不变，详见[当前状态](../docs/current-status.md)（TEAMMATE-STATUS-20261012；ENV-STATUS-SYNC-20261012；USER-HW-20261012-03/04）。

当前开发目标：**Ubuntu 24.04 / ROS 2 Jazzy / C++17，FSM Core v0.1**（USER-HW-20261011）。用户提示 SDK 已补充后（USER-HW-20261011-04），当前源码锁定为 `F1u0rite/meituan_challenge_ws@1d940f7c5f12561fed6641457c0b4b630a282b05`（TEAMMATE-SDK-20261011）。其父提交为初始 TEAMMATE-FSM-20261011 的 `f477f689…`，仅增加部署文档，未改 FSM/接口代码；[接入计划](../docs/hardware-vision-plan.md#5-软件组织与验证顺序)从离线回归推进到 C++ Action / MoveIt / Mock Hardware。本项目尚未完成该链路或 NUC 部署。

个人职责已明确为**系统集成与验收，兼做 Web UI**（USER-HW-20261011-03）。v2 任务书要求复现 Mock 启动、核对实际 ROS graph，并按驱动 SOP 在独立 Fake Hardware 环境留存关节/控制器/Action 证据（SPRINT-PLAN-20261011 §06）。上游已提供该 SOP，本轮已完成独立 Fake 复验并保存实际 ROS Mock 启动失败证据（ENV-FSM-20261011）。`/home/aaet/aubo_driver_validation_ws` 为上游只读参考路径；本项目使用自己的隔离容器，不能直接套用下方历史 Humble 命令。具体交付见 [系统集成与验收计划](../docs/hardware-vision-plan.md#7-系统集成与验收主责)。


新版 [实机操作台](../webui/README.md) 已按 USER-HW-20261011-07 接入 Jazzy ROS 客户端：ExecuteTask、取消、RequestStop、Task/Robot/ToolState、关节、RGB-D 与日志。`bash webui/run.sh` 默认 source 仓库记录的 `/home/aaet/meituan_challenge_ws/install/setup.bash`，可用 `MTC_UI_SETUP` 覆盖；ROS domain 从实机环境或显式配置取得，未提供时显示离线。客户端不启动驱动或使能机器人；隔离接口检查通过（ENV-WEBUI-ROS-20261011），NUC 部署与实体设备联调仍待验，详情见 [实现与验证](../docs/web-ui.md)。

## 截止后的 C++ Mock 与 Web UI 入口

截止主线 `f7eaa2c…` 上的候选 `7da4322…` 已在独立 Jazzy 容器验证：`ros2 run mtc_cpp_mock_bringup mock_stack --namespace /mtc_cpp_mock --output-dir /tmp/cpp-mock-run-001 --port 8767`，需先按固定提交 SOP 构建/source，输出目录必须新建。完整[环境、就绪、任务/取消与清理 SOP 和验收报告](../docs/cpp-mock-webui-acceptance.md)对应 TEAMMATE-CPPUI-20261012 / ENV-CPP-MOCK-WEBUI-20261012。实际 C++ 父子 Action/UI 正负场景已跑；延迟取消最终520仍未通过、归孙嘉明。代码在队友独立 PR #8 待审，不修改本仓库正式pin，不直接部署NUC/实机。

原监测已于北京时间2026-10-12 08:00排空退出，14份事件回执/报告哈希匹配、旧进程与容器停止；以下保留历史监测工具及事件入口，未再启动监测。

## 今晚更新监测与独立复现

按 USER-HW-20261011-08，新增 `watch_upstream.py`、`reproduce_upstream.py`、`probe_moveit.py` 与 `probe_task_mock.py`，监测上游分支/PR head 并在无网络、无设备的独立 Jazzy 容器中按 SHA 复跑。它们与下方历史 Humble 实机脚本适用范围不同。运行窗口、状态入口与未覆盖项见[监测说明](../docs/upstream-monitor.md)（ENV-UPSTREAM-WATCH-20261011）；没有合并上游或执行实体运动。

后续按 USER-HW-20261011-09 接入 `wake_main.py`：固定复现结束后用 `codex queue` 唤醒指定主对话，失败/超时亦触发；按 SHA、持久化令牌和完成回执串行，最多三次传输尝试，无更新不调用模型。主对话负责实际变更复核、额外隔离检查与证据登记；详情见[自动唤醒验收](../docs/upstream-wake.md)（ENV-UPSTREAM-WAKE-20261011）。

真实更新 `c0f7017…` 的 Phase 2A C++ Action Mock 已完成补跑（TEAMMATE-ACTION-20261011；ENV-CPP-ACTION-20261011）。新增 `probe_cpp_actions.py` 只在上述隔离 Jazzy 容器内运行，以 `/candidate-install` 为默认安装目录；分别启动交付的 Task/PickPlace 与独立 Motion 程序，检查唯一服务器、Goal/Feedback/Result/Cancel 和退出。独立四场景通过，详情及可复现的完整环境命令见[候选验收](../docs/cpp-action-acceptance.md)与其冻结 `supplement/logs/*.sh`。它是主对话按实际交付补跑的入口，尚未改动正在运行的固定监测工具；不得直接套到实体 ROS graph。

新规划分支 `fcdd8ea…` 的交付 `run_planning_evidence.sh` 已在域 116 的独立 Fake 容器补跑：固定姿态通过，默认 V1/V2 因 TF 未就绪失败；域 117 只延长 TF 等待至 5 秒的诊断中 V2 七段规划通过、V1 超状态时限被拒绝。全部命令、目录别名及唯一参数差异在[规划验收](../docs/planner-acceptance.md)与冻结日志中（TEAMMATE-PLANNER-20261011；ENV-PLANNER-20261012）。本入口只规划，不下发新轨迹；完整 FSM/FJT、工具动作和实机仍未验收。

后续主线交接文档 `a04ac68…` 的身份审计及 Node/Action/QoS 命令已补验（TEAMMATE-HANDOFF-20261011；ENV-HANDOFF-20261012）。新身份审计通过；两轮 CLI 图观察仍有漏发现，不能只凭短时空图认定服务器不存在。类型/QoS、诊断唯一服务器和六次正常退出均留存，[完整命令与失败记录](../docs/cpp-handoff-acceptance.md)在冻结证据中；未新增生产 Bringup 或更改运行代码。

规划分支同步主线的 `4a1a816…` 已按合并安装环境复验（TEAMMATE-INTEGRATION-20261012；ENV-PLANNER-MERGE-20261012）：14 包 / 387 C++ / 269 Python / 15 Mock E2E / 6 ROS 通过，既有独立 Action 四场景 40 项检查通过。默认规划 SOP 在域 126 固定姿态通过、V1 超状态预算、V2 TF 失败，退出仍 -11；未改代码或配置。两套模块尚未真实接线，详见[合并版本报告及命令](../docs/planner-merge-acceptance.md)，原始失败和正式锁定保持不变。

新场景分支 `30e3c6e…` 已补验交付的新 SOP、碰撞反例和参数文件拒绝入口（TEAMMATE-SCENE-20261012；ENV-PLANNER-SCENE-20261012）。393 C++ 通过；域 127 原配置的三项场景初始化失败保留，域 128 仅改 TF 等待 5 秒后 V2 七段/碰撞拒绝通过、V1 180.42 秒超预算，MoveIt 两轮仍 -11。新起点 API 未接实际 FJT；两容器已停止，见[场景增量报告与命令](../docs/planner-scene-acceptance.md)。

视觉分支 `0e329f1…` 已按新交付入口补验（TEAMMATE-PERCEPTION-20261012；ENV-VISION-ADAPTER-20261012）：公开视觉 62 通过/1 私有数据跳过，16 帧合成生成通过；原生 ROS 回放域 129 默认只收 1/4，域 130 仅改周期 5 秒后收 4/4，退出仍失败。没有相机/Task Goal/运动，实际 FSM 消费链未接通；[报告](../docs/vision-adapter-acceptance.md)记录无网络 venv 依赖、全部原失败、NaN/时间戳/有效性边界和清理。

生成式 AI 披露：上述六个工具及监测/唤醒测试由 OpenAI Codex 协助编写，仅做集成验收编排；调用已安装的标准 ROS/MoveIt 接口，不实现或改写规划/FSM 算法。

原规划 PR #3 已由上游合入 `main@f7eaa2c…`，整树与已验 4a1a816 相同（TEAMMATE-PLANNERMAIN-20261012；ENV-PLANNER-MAIN-20261012）。本次 387 C++ 等回归通过，默认独立 MoveIt 执行因内部 FJT 客户端未连接而 ABORTED/-4；一次域 131 额外 5 秒等待诊断通过、退出仍 -11。未修改固定探针或上游配置；两容器和本域 daemon 已清理，旧 Cancel/520 保留，见[主线合并报告](../docs/planner-main-acceptance.md)。没有新入口，规划 SOP/独立四场景引用同树历史记录；场景/视觉分支尚不在此主线，正式锁定不变。

Phase 2B 独立轨迹端口 `688d80d…` 已复跑（TEAMMATE-TRAJECTORY-20261012；ENV-TRAJECTORY-20261012）：424普通/UBSan、外部CMake导出目标与默认禁用检查通过。GenericSystem起点不符/取消通过，success虽到达目标仍因端口运行证明失效返回230，保留失败；没有重复成功场景。默认Action继续Mock、直接FSM Cancel保留FAULT/520，异步停稳桥尚未接线。683文件冻结、控制器反馈和本地交接见[轨迹报告](../docs/trajectory-execution-acceptance.md)。两容器及ROS任务已停止；独立MoveIt仍有-11退出，完整FSM/NUC/实机未验收，正式1d940f7锁定不变。

标定/TF分支06ab689已补验（TEAMMATE-CALIBRATION-20261012；ENV-CALIBRATION-20261012）：新增54离线测试、6示例和5反例通过；域138只读Fake核验4条TF、腕部→ee的Z+90°及903零关节反馈戳，无Goal。真实清单8边仍UNKNOWN、采样表无实测值，Planner仍latest TF，诊断规则未接入运行适配器；不据上游V1/安装前提改变本项目选型。532文件、robot_description哈希、原失败与清理见[标定报告](../docs/calibration-acceptance.md)。两容器均停止，旧任务失败及MoveIt退出-11保留，正式锁定未推进。

轨迹身份更新45f497c已补验（TEAMMATE-TRAJECTORYGATE-20261012；ENV-TRAJECTORY-GATE-20261012）：463项普通/UBSan、四个独立Fake场景通过。默认MoveIt/FJT客户端2、ready=0，topology零Goal拒绝；211点规划的纯转换消费被原窄速度限值拒绝。时间契约/唯一执行者/异步取消宿主仍未接通，旧230和两次MoveIt退出-11保留。869文件及清理见[门禁验收](../docs/trajectory-gate-acceptance.md)，未合并或推进正式锁定，不能当完整FSM/实机。

视觉安全增量e53c09f已补验（TEAMMATE-VISIONSAFETY-20261012；ENV-VISION-SAFETY-20261012）：53项新测试、62公开回归通过/1私有证据跳过；默认和两次插桩回放各4/4、SIGINT exit 0。默认colcon仍零测试，默认订阅就绪未修复；可信帧/采集戳TF helper尚未接入真实FSM，旧静态反例与MoveIt退出-11保留。463文件及清理见[视觉安全验收](../docs/vision-safety-acceptance.md)，未推进正式锁定，不代表相机/完整任务/实机通过。

681bb64轨迹Goal归属/Status补验（TEAMMATE-OWNERSHIP-20261012；ENV-TRAJECTORY-OWNERSHIP-20261012）：原FJT套件重复取消120秒超时；同二进制61项补跑、独立478项UBSan通过，但间歇挂起仍交孙嘉明。原生GenericSystem无Status及默认MoveIt双客户端均BLOCKED零Goal，旧45f497c四项执行PASS不沿用。708文件、原失败和清理见[归属验收](../docs/trajectory-ownership-acceptance.md)，未修改内核/正式基线；完整C++Mock/UI后续任务仍等08:00。

## SDK 与 Jazzy 驱动资料已核对

来源：TEAMMATE-SDK-20261011（2026-10-11 查阅），[固定版本部署手册](https://github.com/F1u0rite/meituan_challenge_ws/blob/1d940f7c5f12561fed6641457c0b4b630a282b05/docs/setup/AUBO_ROS2_DRIVER_JAZZY.md)。本次新增的是 SDK 依赖、驱动部署与验证说明；SDK 二进制由官方驱动的 CMake FetchContent 下载，未作为此提交新增文件入库。

| 项目 | 已核对的输入 | 仍需完成的本项目验证 |
| --- | --- | --- |
| 官方驱动 | `AuboRobot/aubo_ros2_driver` 的 Jazzy 提交 `53aab83735236f0c262ecb11e04ef2600241d9d9` | 本轮独立 Jazzy 容器 5 包构建通过；完整运行依赖与实体设备兼容性仍待核验 |
| SDK 构建依赖 | `aubo_sdk-0.24.1-rc.3-Linux_x86_64+318754d.zip`；已直接核对该驱动提交的 [CMakeLists.txt](https://github.com/AuboRobot/aubo_ros2_driver/blob/53aab83735236f0c262ecb11e04ef2600241d9d9/aubo_ros2_driver/CMakeLists.txt) | 本轮下载/链接通过，包 SHA-256 见[阶段验收](../docs/fsm-acceptance.md)；官方构建未设 `URL_HASH`，厂商校验值、许可及控制柜兼容性仍待核对（ENV-FSM-20261011） |
| 模型与 Fake 修复 | `aubo_description@47fa5e02fa873f27f7e812d31f31e3f4cf5e56b1` 加手册链接的 Xacro 补丁；Fake 分支选择 `mock_components/GenericSystem` | 纯上游 clone 缺该修复；本轮独立副本应用补丁、核对字节后已实际展开 Xacro，并启动唯一 GenericSystem（ENV-FSM-20261011） |
| 独立驱动/MoveIt SOP | 手册 §04–10：环境隔离、Fake 控制器、JointState/TF、MoveIt/RViz、轨迹与退出检查 | 本项目独立 Fake 控制器、关节/TF、单点和多点轨迹 `PASS`；MoveIt Plan → Execute 已在本次资格检查通过，退出 -11 为 FAIL（ENV-UPSTREAM-WATCH-20261011）；原阶段未运行的历史记录见 ENV-FSM-20261011 |
| 完整 FSM 集成 | 手册 §11 的 Action/Planner/MotionAdapter 边界 | 后续 `c0f7017…` 已通过 C++ Action Mock 候选检查（ENV-CPP-ACTION-20261011）；独立 Planner 包已交付并补验默认失败及有条件 V2 规划（ENV-PLANNER-20261012）；Planner→完整轨迹执行适配、Fake/实体任务仍待接入，独立 MoveIt 成功不计为完整 FSM 抓放通过 |

复现时先取得包含 Fake 修复的独立源码副本，再核对 overlay、模型、唯一 GenericSystem 和同一 ROS domain，最后按手册三终端流程检查。控制 launch 必须明确指定 S3 与 Fake 参数；`aubo_moveit.launch.py` 未声明 `use_fake_hardware` 参数，不向它补造参数。手册使用的 `ROS_DOMAIN_ID=91` 是该 SOP 的隔离示例，原 demo 的 67 仍仅用于历史仿真。

本轮结果与原始命令见[阶段验收](../docs/fsm-acceptance.md)（ENV-FSM-20261011）。独立 Fake 的 5 包构建、两控制器、六关节反馈、两段 TF 和两次完整轨迹通过；GenericSystem 是理想状态跟随器，不代表实机或物理仿真。本次已补齐 MoveIt 与 `joint_state_publisher_gui`，独立 Plan → Execute 通过，但退出 -11；完整依赖检查与驱动自动测试仍有失败，见 ENV-UPSTREAM-WATCH-20261011。SDK 许可/厂商校验值及 NUC/控制柜兼容性继续待核对。上游原始日志路径继续只属于上游机器。

## 固定源码版本

有限接线修复已按 USER-HW-20261011-05 提交 [PR #2](https://github.com/F1u0rite/meituan_challenge_ws/pull/2)，候选提交为 `1d3dccf23c53d299d457564daeb6438190ea2d77`。B01/B02/B04 的 6 项 ROS 回归及既有 269 Python / 15 Mock E2E 通过，但仍有 B03/B05/B06，整体任务未通过（ENV-FSM-FIX-20261011，见[补丁复验](../docs/fsm-wiring-fix.md)）。后续上游已在 `c10f6ed…` 合并该 PR，六项 ROS 回归再次通过；新 C++ 独立四场景通过，旧 Python 仍失败，见[合并后验收](../docs/wiring-merge-acceptance.md)（TEAMMATE-MERGE-20261011；ENV-WIRING-MERGE-20261011）。本项目未执行合并，下面的正式版本锁定未推进。

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

回放自然退出增量（ENV-VISION-REPLAY-20261012）：dc76a0b 的57项适配器、80项公开视觉通过（1私有跳过）；安装进程两种合成标签各4/4自然退出和中途SIGINT通过。可选订阅等待已在发布器，但默认仍0，colcon仍零测试；私有V4.1/V4.2入口缺数据，实际FSM消费/实时视觉/实机未完成。见[验收、486文件冻结及清理](../docs/vision-replay-acceptance.md)。未改正式锁定，08:00后C++ Bringup/Web UI已另行部分验收，C1未通过，见当前状态；本机复验已终止。
