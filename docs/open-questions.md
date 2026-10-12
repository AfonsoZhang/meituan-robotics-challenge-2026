# 待确认事项

2026-10-11 当前基线更新：用户回复“按照这个版本”（USER-HW-20261011），后续开发采用 TEAMMATE-FSM-20261011 所登记的 FSM Core v0.1，目标 Ubuntu 24.04 / ROS 2 Jazzy / C++17。用户随后提示 SDK 已补充（USER-HW-20261011-04），当前源码锁定推进到 `1d940f7c5f12561fed6641457c0b4b630a282b05`（TEAMMATE-SDK-20261011）；较初始 `f477f689…` 只新增部署手册并更新 README，核心与接口源码未变。下面保留 2026-09 的设备决策和实验历史；新版目标不证明 NUC 已升级，旧 Humble / Gazebo Classic 结果不计为新版集成验收。软件接入见 Q18 与 [硬件与传统视觉方案第 5 节](hardware-vision-plan.md#5-软件组织与验证顺序)。

2026-09-07 录制补充：已完成单块黄块 → P1 demo，见 [实录](demo-recording.md)。新测的控制器参考/实测关节经名义 FK 得到 TCP 跟踪误差 RMS 0.145 mm、最大 0.326 mm；历史蓝块分析记载 4–6 mm，测量方法、时刻和任务段尚未对齐。保留两组记录，待统一口径后再判断，不能据新单块记录认定三块滑脱已解决。舌规实物试穿与承载结果仍待记录。

2026-09-06 用户已确认：机械臂为遨博 S3、相机为 RealSense D435i、采用传统视觉方案（USER-HW-20260906）；随后补充目前没有夹爪、计算使用本机（USER-HW-20260906-02）。用户进一步确认相机计划安装在机械臂末端，采用眼在手上（eye-in-hand）方式，实际安装状态未核实（USER-HW-20260906-03）。当前并列保留方案一提手钩取（USER-EE-20260906-01）、方案二吸盘侧面吸附（USER-EE-20260906-02）与新增方案三卡环（USER-EE-20260906-04），尚未根据实物验证选出最终方案；此前平行两指夹持仅为历史工程候选，当前无需以采购夹爪作为实施前提。三种末端的具体实现与 S3 控制柜/软件版本仍未知。2026-09-06 另确认引入仿真并指定 S3 模型来源（USER-SIM-20260906-01），仿真器与范围随后由 USER-SIM-20260906-02 定为 Gazebo + ROS 2，剩余待定见 Q16。2026-09-23 用户确定实机使用 ROS（USER-HW-20260923），发行版为 ROS 2 Humble（USER-HW-20260923-02），运行在 NUC 上的原生 Ubuntu 22.04（USER-HW-20260923-03、USER-HW-20260923-04），接入方式待定见 Q17。下表记录尚未解决的部分，并保留已确认的规则答复及历史差异；详细方案见 [硬件与传统视觉方案](hardware-vision-plan.md)及[末端三方案对比](end-effector-options.md)。

## 项目范围与设备

| 编号 | 待确认内容 | 影响 |
| --- | --- | --- |
| Q01（已确认） | 原问题：先完成初赛，还是同时准备决赛？队伍是否已完成报名？2026-09-23 用户答复：**只做初赛，报名已完成**（USER-RULE-20260923）。晋级后是否改为准备决赛未涉及 | 实施范围按初赛固定工位；决赛规则仍保留在规则摘要，Q13 决赛部分与 Q14 不影响当前工作 |
| Q02 | 已确认遨博 S3，ROS 2 驱动定为 `aubo_ros2_driver`（USER-HW-20260923-08）；Jazzy 驱动构建依赖已由新手册与官方 CMake 明确为 SDK `0.24.1-rc.3`（TEAMMATE-SDK-20261011）。待核对实机铭牌、硬件代次、控制柜/软件版本、适用手册、自由度、臂展、负载曲线，以及该 SDK/驱动与实体控制柜的兼容性 | 可达范围、驱动及运动控制；官方不同年代的 S 系列资料需区分，不能套用 i3/iS3 或其他 S 系列机型 |
| Q03 | 候选不局限于以下三种（USER-EE-20260923-02）。方案一为提手钩取（USER-EE-20260906-01）：钩子是否已有、型式、材料、尺寸、TCP、止退方式和 S3 法兰连接待核验。方案二为吸盘侧面吸附（USER-EE-20260906-02）：吸盘型式、数量、有效吸附面积、安装与 TCP，以及真空源、阀、真空反馈、控制接口和实物平整气密吸附面待核验。方案三为卡环（USER-EE-20260906-04）：卡环具体卡持对象（提手或本体）、环内尺寸、开口/闭合方式、材料、锁止方式、TCP 和法兰连接待核验。制作途径：PolyU 3D 打印已确认支持 PLA，其他材料待邮件答复，可网购但需控制价格（USER-EE-20260923）；打印精度、尺寸、排期与金额上限未知 | 钩具须核验通道间隙、承载、防滑脱及落地卸载后的脱钩路径；侧吸须验证密封、侧向承载、偏心负载和释放位移；卡环须验证套入路径、夹持/锁止可靠性、对电池表面或提手的干涉、释放路径和动态承载。三方案通过台架对比确定末端实现，视觉采集和离线识别可先开展 |
| Q04 | 已确认 RealSense D435i 深度相机计划安装在机械臂末端，采用眼在手上方式（USER-HW-20260906-03）；三方案均建议将支架固定在法兰转接件或工具的刚性固定座。实际安装状态未核实，工作距离、支架、USB 连接及固件待核验 | 分别检查钩具进退、吸盘接近、卡环套入/释放的视觉覆盖、遮挡及布线，侧吸另检查气管运动空间。相机安装固定后完成手眼标定；换工具须重新标定相应 TCP，相机相对末端的固定关系改变时重做手眼标定；标定交付54离线测试与只读Fake TF通过，但真实8边UNKNOWN、采样表无实测值；名义支架推导为ESTIMATED，上游V1/安装前提不升级为本项目用户确认（TEAMMATE-CALIBRATION-20261012；ENV-CALIBRATION-20261012） |
| Q05（部分确认） | **当前开发目标**：Ubuntu 24.04 / Jazzy，按 USER-HW-20261011 更新；NUC 实际安装版本及是否完成迁移未核验。以下保留原配置决策：2026-09-06 确认计算使用本机（开发电脑）；实机运行环境 2026-09-23 由用户确定为原生 Ubuntu（USER-HW-20260923-03），不用 WSL2。历史记录：当时终端观测为 Ubuntu 22.04.5 LTS / WSL2 x86_64，曾待定 Windows 还是 WSL。同日确定为 **NUC 上的 Ubuntu 22.04**（USER-HW-20260923-04），与当前开发电脑不是同一台；2026-09-06 所说「本机」经用户澄清指当前开发电脑（USER-HW-20260923-05），即部署计算机已由开发电脑改为 NUC；开发电脑用于开发和跑仿真（USER-HW-20260923-06），并经 SSH 隧道远程查看 NUC（USER-HW-20260923-07；是否允许远程操作未说明）。NUC、S3、D435i 已到位（USER-HW-20260923-11）。2026-10-11 用户提供的任务书写“10/12 全部实物设备预计到位”（SPRINT-PLAN-20261011，开头与 §09），两项记录的设备范围、地点和时点尚未对齐，保留差异。**仍待确认**：NUC 型号、CPU/内存、USB 3 接口与网口，是否已装好系统，开发电脑到 NUC 的网络与 SSH 账户/密钥、代码部署方式，相机与 S3 在 NUC 上的可见性/连通及软件依赖 | 本机开发与实际设备连接环境须区分；终端观测不证明设备已联通 |
| Q06 | 已确认传统视觉路线；已有代码与可用授权待补充，是否需要连续视觉伺服及赛事路线申报口径待明确 | 初版建议颜色分割、几何定位和分阶段视觉复核；不能把该建议视为已实现的连续视觉伺服 |
| Q07（已关闭） | 原问题：队员分工、可投入时间、已具备设备和预算。2026-09-23 用户答复「Q07不是问题」（USER-RULE-20260923-02），不再作为待确认项跟踪；当时未给出具体内容。2026-10-11 用户先明确 **Web UI**（USER-HW-20261011-02），提供 v2 任务书后进一步确认**系统集成与验收，兼做 Web UI**（USER-HW-20261011-03）；任务书的五人分工与 P0 见方案第 7 节，UI 接入见 Q19 | 保留原关闭状态；新增个人职责不推断其他队员、预算或设备状况；买硬件或花钱仍逐项问用户 |
| Q16（部分确认） | **当前开发目标**：USER-HW-20261011 已选定 Jazzy / FSM Core v0.1；物理仿真器版本、Classic 场景/插件迁移及新 FSM 联调仍待验证（TEAMMATE-FSM-20261011）。以下为旧 Humble 路线的范围和检查：仿真器、范围与归档方式已由 USER-SIM-20260906-02 确定：**Gazebo + ROS 2**；本轮做可达性与碰撞、相机 RGB-D 合成图、三块序列端到端，接触物理只做方案一钩取；用户另明确吸盘不适合做仿真（USER-SIM-20260906-03），方案二不建立真空/吸附接触模型；模型不归档只记提交号。已核实 `aubo_type:=aubo_S3` 可直接用（`.urdf.xacro` 由 colcon build 时的 `xacro.sh` 生成）。**当时待确认**：发行版与 Gazebo 版本（按依赖推断为 Humble + Gazebo Classic 11）；后续开发栈以本行当前目标为准，仿真结果如何计入技术报告仍待明确。（「是否同时用 MoveIt 规划」已由 USER-SIM-20260923 确定为使用，与实机 USER-HW-20260923-10 一致；尚未接入，已冻结实验保留冻结轨迹与自写 IK 的原方法） | 仓库缺 gazebo_ros2_control 插件接线、`GazeboSystem` 硬件、`config/` 与场景资产，须自行补齐；许可证状态存在冲突（package.xml 写 BSD，仓库无 LICENSE 文件），按 FAQ p6/Q17 披露前须确认。底图可达性已用名义模型实算，不是待定项。吸盘方案转入实物台架与实机验证。详见 [仿真方案](simulation-plan.md) |
| Q17（部分确认） | **当前开发目标**：Ubuntu 24.04 / Jazzy / C++17（USER-HW-20261011）；用户提示 SDK 已补充（USER-HW-20261011-04）后，已核对新手册：Jazzy 驱动固定 `53aab83735236f0c262ecb11e04ef2600241d9d9`，`aubo_description@47fa5e02…` 加 Fake Xacro 修复，构建通过 FetchContent 下载 `aubo_sdk-0.24.1-rc.3-Linux_x86_64+318754d.zip`（TEAMMATE-SDK-20261011，含官方 CMake 核对）。驱动/SDK 资料与三终端 SOP 已提供；本轮已独立复现 5 包构建、GenericSystem、关节/TF 与单点、多点 FollowJointTrajectory（ENV-FSM-20261011），SDK 包 SHA-256 已登记；本次已复现独立 MoveIt Plan → Execute，退出 -11，未通过干净退出验收（ENV-UPSTREAM-WATCH-20261011）。**当前缺口**：NUC 新机部署、SDK 厂商校验值与许可、依赖声明/测试依赖缺口、MoveIt 退出崩溃、驱动自动测试中的 lint 失败、NUC/控制柜兼容性，以及 Jazzy 相机版本；新 FSM 接入见 Q18。以下为 2026-09-23 的历史选择与驱动检查，版本和能力不能外推到 Jazzy：实机使用 ROS 已由用户确定（USER-HW-20260923，2026-09-23 用户会话），同日确定发行版为 ROS 2 Humble（USER-HW-20260923-02），与仿真一致。运行环境同日确定为原生 Ubuntu（USER-HW-20260923-03，余项见 Q05）。S3 驱动同日确定为 `aubo_ros2_driver`（USER-HW-20260923-08，AUBO-ROS2）：ros2_control 硬件接口，控制器与仿真同为 `joint_trajectory_controller`，构建时从遨博服务器下载二进制 aubo_sdk 0.24.1-rc.3。**仍待确认**：`aubo_type:=aubo_S3` 实机可用性及 SDK 与控制柜/软件版本兼容性（Q02）、aubo_sdk 二进制许可、实机 URDF 校准；另据上游代码，驱动以写死的默认账号 aubo/123456 登录，并会写控制柜参数 `vff_enable = false`、启动即进入伺服保持（接入步骤与安全措施见 [robot/README.md](../robot/README.md)）；D435i 驱动同日确定为 realsense-ros（USER-HW-20260923-09，RS-ROS2；最新发布 4.58.3，Humble apt 候选 4.58.4），其安装方式与版本、在 NUC 上的可见性、实际话题名与深度编码待验证——本项目视觉代码目前只接受 32FC1 米制深度，接实机需加单位换算。MoveIt 同日确定使用（USER-HW-20260923-10），配置用上游 `aubo_moveit_config` 还是自建未定：上游 launch 只接受通用 `aubo_robot.srdf`，其自碰撞豁免表不是按 S3 生成（`aubo_description` 另有 `aubo_S3.srdf`），且不含本项目工具与相机支架的碰撞几何 | 旧方案的同发行版与话题 remap 条件不适用于直接证明 Jazzy 兼容。新基线需核对 ROS 接口、驱动、相机与控制柜，并完成 Q18 的 Mock 集成；在此之前不能声称已接通实机 ；后续新 C++ Action 包根 LICENSE 为 MIT、package.xml 为 Apache-2.0，适用范围待负责人澄清（TEAMMATE-ACTION-20261011；ENV-CPP-ACTION-20261011），不替其重新授权 ；合并候选复跑还观察到 ros2_control_node 退出 -11，第二轮未再现，尚不能关闭；move_group 两次 -11（ENV-WIRING-MERGE-20261011）。规划补验中展开模型三关节 command-interface 限位仍为 `{-2*pi}` / `{2*pi}`，运行时解析/强制限位待核验；其两次 MoveIt 退出仍 -11（ENV-PLANNER-20261012）；新场景增量的上游材料、本机默认失败与诊断分开冻结为 545 文件并登记 index SHA，未将上游时长稳定性转写为本机结论（TEAMMATE-SCENE-20261012；ENV-PLANNER-SCENE-20261012）；视觉分支公开测试 62 通过/1 私有证据跳过，依赖兼容与 NaN 原生消息已局部验证，实时设备/标定和私有 CAD/数据仍未验（TEAMMATE-PERCEPTION-20261012；ENV-VISION-ADAPTER-20261012）；主线 PR #3 合并版本的独立 MoveIt 默认执行出现内部 FJT 客户端未连接，ABORTED/-4；单次额外 5 秒诊断通过但两次退出仍 -11，就绪与退出继续待验（TEAMMATE-PLANNERMAIN-20261012；ENV-PLANNER-MAIN-20261012）；独立轨迹端口688d80d的GenericSystem起点不符/取消通过，success因内部运行证明丢失返回230，控制器到达目标不足以验收；独立MoveIt执行通过但退出-11、Generic统计线程退出报错保留（ENV-TRAJECTORY-20261012）；本次Fake只读核验腕部至末端Z+90°及4条TF，不能证明物理法兰F对齐、相机/TCP标定；MoveIt退出-11和Generic统计线程退出报错保留（ENV-CALIBRATION-20261012）；45f497c独立Fake四项通过，健康谓词未改故旧230仍待归因；本次默认和补跑MoveIt各退出-11，驱动/许可/实机缺口不变（ENV-TRAJECTORY-GATE-20261012）；视觉e53c09f新53测试和62公开回归通过/1私有证据跳过，三次ROS回放受控退出0；真实相机/标定/私有数据仍未验，独立MoveIt仍退出-11（ENV-VISION-SAFETY-20261012）；681bb64独立UBSan478通过不关闭原FJT重复取消120秒挂起；原生Status门禁拒绝零Goal，固定MoveIt退出-11保留（ENV-TRAJECTORY-OWNERSHIP-20261012） |
| Q18（部分确认） | USER-HW-20261011 确认 FSM Core v0.1 / Ubuntu 24.04 / Jazzy / C++17；SDK 文档更新后正式锁定 `1d940f7…`（TEAMMATE-FSM-20261011；TEAMMATE-SDK-20261011）。原 12 包 / 318 C++ / 269 Python / 15 Mock E2E 与旧 Python 启动失败、PR #2 的有限修复及 B03/B05/B06 继续保留（ENV-FSM-20261011；ENV-FSM-FIX-20261011）。按 USER-HW-20261011-08、USER-HW-20261011-09 监测后实际收到 `feature/phase2a-cpp-actions@c0f7017…`：13 包 / 358 C++ / 269 Python / 15 Mock E2E、新审计入口、UBSan 与独立四场景通过（TEAMMATE-ACTION-20261011；ENV-CPP-ACTION-20261011），见[候选验收](cpp-action-acceptance.md)。随后上游 `main@c10f6ed…` 已合入 PR #2，六项 ROS 接线回归与 C++ 四场景再次通过（TEAMMATE-MERGE-20261011；ENV-WIRING-MERGE-20261011） | 新 C++ Action 的 Mock 外壳已局部通过；独立 MoveIt Planner 分支已交付，默认 V1/V2 TF 失败，5 秒等待诊断下 V2 七段规划通过、V1 超状态预算拒绝（TEAMMATE-PLANNER-20261011；ENV-PLANNER-20261012）。规划就绪、整条轨迹执行、真实状态时限、工具间隙、唯一执行权、Fake Hardware 完整接线、视觉/工具证据、完整状态发布和 NUC/实机仍待完成。Task 取消仅覆盖受信 Mock 子服务器约定，独立 MoveIt 规划成功但退出 -11。张叔阳负责集成验收，孙嘉明负责 FSM/Action/执行内核（SPRINT-PLAN-20261011 §01、§06–07；USER-HW-20261011-03）；本项目未执行合并或推进基线，不把独立 Mock/Fake 当实机，不以软件 V1/V2 替代 Q03 实体选型；后续 `a04ac68…` 仅补充交接文档，统一 C++ Bringup 未交付，Node/Action/QoS 观察出现图发现时序问题，见 ENV-HANDOFF-20261012；后续 `4a1a816…` 已合入两套既有模块，387 C++ 与独立 Mock 通过，但默认序列仍有预算/TF 失败、真实 MoveIt 接线未完成（TEAMMATE-INTEGRATION-20261012；ENV-PLANNER-MERGE-20261012）；`30e3c6e…` 的起点/单段重规划单测通过但尚无真实执行调用；默认场景失败、5 秒诊断 V2/碰撞反例通过、V1 上游时长未复现，完整接线仍待验（ENV-PLANNER-SCENE-20261012）；新视觉话题仅离线回放：默认 1/4 帧、5 秒诊断 4/4，退出仍失败；实际 C++ 仍 MockPerception，消费侧有效性/时效门禁与人工 NaN 反例待交接（ENV-VISION-ADAPTER-20261012）；主线 f7eaa2c 与前验 4a1a816 整树一致，387 C++ 等本次回归通过；没有新 Bringup/接线，场景/视觉分支尚不在此快照；旧 Python Cancel 本次 520，停稳未确认（ENV-PLANNER-MAIN-20261012）；新增FjtMotionPort的424普通/UBSan测试通过，但默认Action仍Mock；直接FSM Cancel保留FAULT/520，runtime host/异步停稳桥、实际规划/工具感知链未接入（TEAMMATE-TRAJECTORY-20261012；ENV-TRAJECTORY-20261012）；标定诊断未接入实际适配器；规划仍latest TF，ROS采集stamp与Core时钟转换、单次TCP补偿及工位朝向消费仍待集成，既有src树未变（ENV-CALIBRATION-20261012）；命令身份463项普通/UBSan及四场景通过；默认MoveIt/FJT双客户端门禁BLOCKED、零Goal，真实规划在窄能力下被拒绝，时间契约与异步取消宿主未交付；不能写成完整链路（TEAMMATE-TRAJECTORYGATE-20261012；ENV-TRAJECTORY-GATE-20261012）；视觉安全helper已加可信帧/采集时间TF并补验，但未接FSM；静态true-ring/NaN/旧时间反例仍成立，默认colcon零测试与默认发现就绪待解决（TEAMMATE-VISIONSAFETY-20261012；ENV-VISION-SAFETY-20261012）；681bb64的61项补跑通过但首次套件超时仍待孙嘉明归因；原生GenericSystem实时Status及默认MoveIt双客户端阻断，完整链路未过（TEAMMATE-OWNERSHIP-20261012；ENV-TRAJECTORY-OWNERSHIP-20261012） |
| Q19（部分确认） | 用户主责系统集成与验收，兼做 Web UI（USER-HW-20261011-03）；早期新版 Mock 选择与证据保留（USER-HW-20261011-06；DEMO-WEBUI-MOCK-20261011）。用户随后澄清需要**实机操作台**（USER-HW-20261011-07）。当前默认 ROS 客户端已实现真实 Goal/Cancel/Result、软件停止、Task/Robot/ToolState、关节、RGB-D 与日志；缺失/过期不显示就绪，发布源要求话题唯一并核对节点名，图中 GID 用于识别来源更换。33 项离线/HTTP 与 9 项隔离 Jazzy ROS 检查通过（ENV-WEBUI-ROS-20261011），见 [实现与验证](web-ui.md)。完整 UI 不新增为任务书今晚硬性 P0（SPRINT-PLAN-20261011 §06） | 待 NUC 实际工作空间/SSH/ROS domain 核验、真实设备与整体 FSM 联调、RGB-D 单位与时间同步、检测叠图及任务录像。现有客户端不能消除 Q18 的 B03/B05/B06；隔离测试不代表实机。SSH 隧道方式沿用 USER-HW-20260923-07，新增控制入口与 --readonly 均已提供，本轮未执行实体运动；新 C++ Action Mock 包没有 TaskState/RobotState/ToolState 发布者，现有操作台的来源校验与就绪条件仍待完整链路交付后对齐（ENV-CPP-ACTION-20261011），本轮未做 UI 联调。后续用户已授权 10 月 12 日 08:00 监测及尾部验收清理完成后，同轮开展 C++ Bringup/真实 Task→PickPlace 与 Web UI/桥接接口验收，代码先交队友独立 PR、证据再推个人 main；已在截止后执行：候选 `7da4322…` 的真实 C++ Task→PickPlace/UI 六项场景及冲突/退出检查完成，及时取消5/0通过；正常Mock延迟取消ACK后6/520，C1归孙嘉明，完整链路/NUC/实机仍未通过，Q19继续部分确认（USER-HW-20261012；USER-HW-20261012-02；ENV-CPP-MOCK-WEBUI-20261012） |

## 规则与实物

| 编号 | 原始信息或歧义 | 需要补充的事实 |
| --- | --- | --- |
| Q08 | 底图标电池 7×8 cm、序列内圈 8×8 cm，图示为圆形（MAP p1–2）。新尺寸图直接标注名义底面外包络 70×80、本体高 50、提手高出本体 30、横梁前后厚 26 与竖直高 10；总高 80 由 50＋30 推算。图内单位未明示，当前暂按 mm 解释；这是图中设计尺寸，并非实物测量（BATTERY-DRAWING，无 PDF 页码）。内框采用主体垂直投影面积占比 ≥70%（USER-RULE-20260906-02，见 Q15）。末端设计暂以此图尺寸为准（USER-EE-20260923-02），实测后以实测为准 | 实物尺寸、材质、公差、实际边界及允许摆放姿态仍待确认；方案二还需测量侧面的可密封平面范围、平整度、粗糙度及漏气情况，CAD 外观不能证明实际表面可吸附。按图中设计几何计算放置容差，见 [电池几何与抓取分析](battery-geometry.md)；70×80 矩形不能完全进入直径 80 圆的结论只适用于完整包含，不能直接否定面积占比判定下的可行性 |
| Q09（已确认） | FAQ p5 要求正式拍摄使用组委会寄送底图，同时说明港澳台底图自行打印。2026-09-23 用户确认**正式拍摄用组委会寄送的底图**（USER-RULE-20260923-03） | 物料是否已收到、寄送底图实测尺寸未记录；项目坐标仍取 MAP PDF 设计值，拿到后宜实测核对 |
| Q10（已关闭） | FAQ p3 同时描述前 10 名晋级和按技术路线分配名额。2026-09-23 用户答复「Q10不是问题」（USER-RULE-20260923-04），不再跟踪 | FAQ 两种表述的差异未被澄清，规则摘要照原文保留 |
| Q11 | 规则 p2 写每队两条视频，FAQ p3 写每任务两条；FAQ p1 要求技术报告。v2 任务书称团队已确认 **2026-10-15 提交视频与技术材料**，并安排 10/14 录像与报告定稿（SPRINT-PLAN-20261011，开头与 §10）；此处登记为团队排期，任务书不是官方通知 | 仍需最新官方通知确认准确截止时刻、正式入口、文件格式、任务清单与报告模板；不把团队计划升级为已核实官方截止要求 |
| Q12 | 规则 p4、p6 的时间效率分按用时分布折算 | 计时起止点、超时处理和具体公式 |
| Q13 | 比赛日公布序列口令，决赛由裁判公布目标 | 正式任务通知及输入方式，保留文档示例与正式口令的区别 |
| Q14 | 规则 p5 总表及 p6 标题将决赛障碍区记为 30 分，但 p6 细项为 10+10+5=25 分（项目只做初赛，USER-RULE-20260923，本项不影响当前工作，保留待查） | 缺少的 5 分如何分配，或是否存在表格笔误；当前摘要保留总表的 30 分 |
| Q15（已确认） | 用户 2026-09-06 先补充“垂直投影70%”（USER-RULE-20260906-01），随后确认定义、适用内框且来自组委会答复（USER-RULE-20260906-02）。当前采用 Area(电池主体垂直投影 ∩ 内框) / Area(电池主体总垂直投影) ≥70%，包含恰好 70% 的边界 | 定义、范围及来源已确认，按该答复执行内框判定。保留历史差异：RULES p4 原文为“电池主体完整位于内框内”，未记载 70%。来源为用户转述组委会答复，原答复载体待归档，无 PDF 页码；归档状态不影响当前采用。T0（RULES p3）及外框（RULES p4）保持原文要求，不推广 70% |

## 继续工作的最小信息

软件侧按 USER-HW-20261011、USER-HW-20261011-04 的固定版本，已完成 Jazzy 离线回归和独立 Fake 验收；现有 ROS Task/PickPlace 启动失败，先按 ENV-FSM-20261011 的 B01–B04 修复并复跑，再推进 Action / Planner / Motion / Perception / Tool 完整接线。SDK/驱动来源仍为 TEAMMATE-SDK-20261011。NUC 的当前系统与驱动、Jazzy 安装条件见 Q05/Q17，Gazebo 迁移方式见 Q16，完整接入顺序见 Q18。历史 Humble 脚本继续用于旧版本复现。

个人主责按 USER-HW-20261011-03 调整为系统集成与验收，兼做 Web UI。按 v2 任务书继续处理基础 Goal 阻断和拍摄准备（SPRINT-PLAN-20261011 §06）；构建/graph、启动失败与独立 Fake 结果已登记于 ENV-FSM-20261011；UI 优先复用现有观察与回放能力，新增交互按第 6 节推进。实机 UI 客户端已落地（USER-HW-20261011-07）；Q19 的 NUC 部署与整体验收待完成；FSM/Action 内核由孙嘉明负责；用户已同意集成侧有限修复 B01/B02/B04 并提交独立 PR（USER-HW-20261011-05），具体对接人和产物见方案第 7 节。

当前推进三方案共用的视觉采集、离线识别和标定材料整理，同时查明 S3 控制柜/软件版本及三套末端的已有设备。根据 Q03、Q08 核验钩取通道与承载、侧吸密封条件与真空系统、卡环配合与锁止，先做台架对比，记录获取成功率、搬运稳定性、释放后位移和耗时。结合末端接口确定工具及相机的刚性固定方式，分别检查遮挡、工作距离与连接条件。安装确定后完成相应 TCP 和手眼标定，再验证单块搬运与三块序列；更换工具时按 Q04 区分 TCP 重标定和相机固定关系变化引起的手眼重标定。

## 2026-09-08 视觉接入后的实验缺口

`VISION-CORRECTION-20260907` 已接通黄色单块的 RGB-D 抓取前修正，结果见 [实验记录](vision-correction.md)。待验证：完整钩具遮挡下其余颜色的观察位、偏航修正、真实 RGB-D 对齐与手眼标定、修正路径碰撞检查，以及预先固定扰动矩阵的重复对照。+6 mm 偏移下开环对照也成功，不能据当前记录声称成功率提升；原有三块序列和蓝块问题尚未解决。

`VISION-REPEAT-20260908` 已完成预先固定的 −6/0/+6 mm 横向偏移矩阵，各两次配对、共 12 次；两种模式各 6/6 通过。横向重复对照缺口已补上，偏航、视觉噪声、真实标定与三块序列缺口仍保留；详见 [重复对照结果](vision-repeat.md)。

`VISION-SEQUENCE-20260908` 已验证绿、蓝观察位并接入同一世界的逐块定位；最终诊断版本两次三块通过。但开发中仍出现蓝块掉落，失败瞬间接触原因未知；绿、蓝约 11 mm 的释放偏差待追查。不能把两次成功写作稳定性或旧问题修复证明，见 [三块集成](vision-sequence.md)。

`ROBUST-CONTROL-20260908` 新增 Gazebo effort 控制模式（重力补偿＋边界层滑模），9 次高位对照和 1 次无外加扰动黄块抓取通过。滑模与增益匹配 PD 在测试区间几乎一致，尚无非线性鲁棒优势或安全证明；实机力矩接口、受扰抓取、三块力矩模式与旧蓝块失败仍待验证。见 [控制实验](robust-control.md)。

## 2026-10-11 FSM 基线接入后的实验缺口

以下按观测轮次保留历史缺口；末尾 Phase 2A 候选复验补充新路径结果，不改写旧失败。

TEAMMATE-FSM-20261011 的 318 项 C++、269 项 Python、15 项纯 Python Mock E2E 已在本项目独立 Jazzy 容器复现，12 包构建通过（ENV-FSM-20261011，见[阶段验收](fsm-acceptance.md)）；TSan 动态竞态验收未完成。新版 C++ FSM 到 ROS 2 Action、MoveIt、整条轨迹执行和 Mock Hardware 的链路尚未集成，本项目旧 Gazebo 的抓取、视觉、误差和覆盖率证据不能填补这些缺口。后续还需把真实观测接入挂载、落座、释放和连续稳定性判断，核对 `flange` / `tool0` / TCP 定义、坐标轴、单位与时钟，保留各次失败记录（USER-HW-20261011；接入方案见硬件与传统视觉方案第 5 节）。

Web UI 的早期本地 HTTP Mock 操作台与浏览器证据继续保留（DEMO-WEBUI-MOCK-20261011；USER-HW-20261011-06）。后续按“实机操作台”澄清（USER-HW-20261011-07）实现默认 ROS 客户端；隔离接口验证已完成 33 项离线与 9 项 ROS 检查（ENV-WEBUI-ROS-20261011），与实机结果分别记录于 [Web UI](web-ui.md)。真实 NUC、完整 FSM、相机真值/标定、检测叠图与任务录像仍待验；过去的 Mock 与静态观测不补写为实机通过。

系统集成 P0 的 Jazzy 构建/离线检查已通过，现有 Python Mock 的实际 ROS graph 已采集；Task 时钟成员冲突、PickPlace 配置字段不匹配导致启动退出，基础 Goal 未能发送。另有 Action Server 绑定、V2 解锁服务名不一致问题，均列入负责人问题单（ENV-FSM-20261011）。感知/TF、新 C++ 外壳和整体任务链路仍待接入；任务书截止节点不计为完成记录（SPRINT-PLAN-20261011 §06、§08）。

SDK/驱动资料更新（USER-HW-20261011-04；TEAMMATE-SDK-20261011）：已完成手册/官方 CMake 静态核对、固定源码导入、归档补丁应用后的一致性校验。后续 ENV-FSM-20261011 已完成本项目独立容器五包构建、GenericSystem、六关节/TF、单点和多点 FollowJointTrajectory，并记录 SDK 下载包 SHA-256。当时 MoveIt Plan → Execute/退出复核、NUC 部署、SDK 许可/厂商校验值、驱动自动测试及完整依赖仍未验证；独立 Fake 通过不填补现有 ROS 启动故障及新 C++ FSM 接线缺口。

有限接线修复（USER-HW-20261011-05；ENV-FSM-FIX-20261011）：B01/B02/B04 已作为 [PR #2](https://github.com/F1u0rite/meituan_challenge_ws/pull/2) 提交审阅，正式锁定仍为 `1d940f7…`。新增六项 ROS 回归在原版全部失败、补丁全部通过；两次真实 Mock 中 Task 已可受理 Goal，但 PickPlace 因新发现 B05 ActionClient 绑定错误退出，原 B03 仍被遮挡；延迟首次 Goal 前 INIT 约 5 秒超时进入 FAULT（B06），结果 ABORTED / 510、完成数 0。以上生命周期问题继续交孙嘉明，安全节点 SIGINT 清理异常亦保留；见[补丁复验](fsm-wiring-fix.md)。不能据定向修复通过认定完整任务、取消、MoveIt 或实机已验收。

今晚后续复现安排（USER-HW-20261011-08）：上游各分支与 PR head 每 60 秒监测，更新后在隔离 Jazzy 容器排队复跑，设置与当前状态见 ENV-UPSTREAM-WATCH-20261011 和[监测说明](upstream-monitor.md)。交付预期不计为 MoveIt 或完整 FSM 已通过；旧失败记录保留，新 C++ 启动与实际输入仍按交付验收。

自动唤醒接入（USER-HW-20261011-09；ENV-UPSTREAM-WAKE-20261011）：固定复现完成、失败或超时后向同一主对话投递，由主对话阅读实际变化、补跑固定入口未覆盖项并登记证据；完成回执前下一 SHA 只排队。监测频率、时段及隔离要求沿用，接入测试见[唤醒验收](upstream-wake.md)。传输与回执测试不新增 FSM/MoveIt 功能通过项；当前完整 C++ 闭环、Cancel 停稳、NUC/实机缺口仍保留。

本次监测工具资格检查进一步复现了独立 MoveIt Plan → Execute，但 `move_group` 退出 -11；已知候选的尽早/延迟/取消三种实际 Goal 均未完成任务，取消受理不等于子任务已停止。依赖声明与驱动 lint 失败见 ENV-UPSTREAM-WATCH-20261011，[监测与复现记录](upstream-monitor.md)保留全部失败，不将其算作今晚新交付的结果。

Phase 2A 新交付复验（TEAMMATE-ACTION-20261011；ENV-CPP-ACTION-20261011）：`c0f7017…` 的 C++ Action Mock 已通过新身份审计、UBSan、外部 CMake 消费和四组独立进程检查；延迟首次 Goal、基础 T0、三色序列、关联取消、失败锁定及正常退出均有证据。固定工具的旧 16 可执行文件审计不适配新增 4 个目标，已用交付入口补验，原失败保留；旧 Python 路径仍在 B01/B02 启动失败，可选六项 ROS 回归在此分支不存在，明确 NOT RUN。独立 MoveIt 再次规划执行通过、退出 -11，依赖/驱动 lint 未解决。PickPlace 仍使用本地 Mock Motion，新状态 Topic、完整 MoveIt/轨迹/实体停稳、TSan、NUC/实机及许可差异待核对。两轮容器已停止；[验收报告](cpp-action-acceptance.md)和冻结 index 与原证据分开保存，正式锁定不变。

PR #2 合并后复验（TEAMMATE-MERGE-20261011；ENV-WIRING-MERGE-20261011）：上游 23:35 的 `c10f6ed…` 完整保留三项接线补丁，六项 ROS 回归通过；旧 Python 尽早/延迟/取消 Goal 分别 ABORTED / 220、510、520，B03/B05/B06 保留。新 C++ Action 代码未变，独立四场景通过；没有统一 Bringup 或完整 MoveIt/轨迹交付。独立 MoveIt 原运行与补跑均规划执行成功、move_group 退出 -11，控制器原运行另有 -11、补跑为 0，根因和退出修复待验。维护者转向 C++ Bringup 的建议作为上游交接记录，不当作本事件的新增开发授权。清理与冻结证据见[报告](wiring-merge-acceptance.md)，正式锁定未推进。

## 2026-10-12 规划补验后的实验缺口

TEAMMATE-PLANNER-20261011 / ENV-PLANNER-20261012 的独立 `fcdd8ea…` 已构建并通过 318 核心 + 29 规划单测；该分支不含另一候选 C++ Action 或 PR #2，原 Python Goal 前失败保留。交付 SOP 原样执行时固定姿态通过、V1/V2 均 TF_UNAVAILABLE。外部 TF 存在，独立诊断只延长 TF 等待 0.5→5 秒后 V2 七段规划通过，V1 因轨迹 136.515 秒超过状态可用 24 秒而拒绝。默认配置仍未通过，诊断只支持就绪时序问题，完整根因待常建烁核对。

V2 轨迹字段、关节顺序和规划器数值限位通过，不代表实际工具插入/退出、落座或释放；两个段间起点依赖未执行的 0.03 m 工具位移。真实异步规划与 FSM 2 秒 PLAN_ACQUIRE、Action/FJT 执行和取消停稳交孙嘉明；TCP/工位/动态 TF 与碰撞场景待规划和标定负责人落实。展开 URDF 的三组非数值限位、MoveIt 退出 -11、控制器一次 -2、依赖/lint、SDK/NUC/实机缺口保留。容器已停止，证据见[规划验收](planner-acceptance.md)；没有变更基线、代发消息或依据 V2 规划结果收敛实体末端方案。

交接文档后续检查（TEAMMATE-HANDOFF-20261011；ENV-HANDOFF-20261012）：`a04ac68…` 的运行源码相对已验主线未变，固定 358 C++ / 269 Python / 15 Mock E2E / 6 ROS 回归及新身份审计通过。新增 CLI 检查首次三次 node info 失败，Task/Motion Action 曾显示零服务器；一次有限诊断虽观察到三个唯一服务器及匹配反馈 QoS，仍有空节点列表和 PickPlace info 失败，不能认为加等待已经修复。六次进程均正常退出，默认失败与诊断分开冻结。旧 Python Cancel 本次受理后 ABORTED / 220，不能复用前轮 520 作为本次结果或视为停稳；MoveIt 退出 -11 保留。统一 Bringup、图发现就绪、完整 FSM/轨迹/实机仍是缺口，上游待办不自动变成本事件开发任务，详见[交接验收](cpp-handoff-acceptance.md)。

## 2026-10-12 合并版本后的实验缺口

TEAMMATE-INTEGRATION-20261012 / ENV-PLANNER-MERGE-20261012 的 `4a1a816…` 将已验 Action 与规划代码放到同一分支，14 包 / 387 C++ / 269 Python / 15 Mock E2E / 6 ROS 通过，补跑四场景 40 项检查通过。原样规划 SOP 固定姿态通过，V1 因 42.0717 秒超过 24 秒状态预算拒绝，V2 TF_UNAVAILABLE；两序列无命令输出，move_group 退出 -11。源码、配置未变而 V1 失败阶段不同，不证明发现问题已修复，也不把前次 5 秒诊断的 V2 成功移记本次。

PickPlace 仍用 MockPlanner/AsyncMockMotion；真实异步规划时限、整条轨迹/唯一执行权、工具动作后起点、关联 Cancel 与独立停稳继续交孙嘉明，规划就绪和预算协调交常建烁。旧 Python B03/B05/B06、Safety 清理、依赖/驱动 lint、URDF 限位求值、短时 CLI 漏发现、完整状态/UI、标定/场景、SDK/NUC/实机均未关闭。两容器已停止、原始失败保留，见[合并版本验收](planner-merge-acceptance.md)；未接管内核、代发消息、合并或推进正式基线。

## 2026-10-12 场景/载荷增量后的实验缺口

TEAMMATE-SCENE-20261012 / ENV-PLANNER-SCENE-20261012：14 包 / 393 C++ / 269 Python / 15 Mock E2E / 6 ROS 通过。默认固定姿态通过，其余三个工具在场景初始化退出 2，不能将未执行目标的碰撞探针判成安全拒绝。仅改 TF 等待 0.5→5 秒的诊断中，V2 七段与 table/wrist3_Link 碰撞反例通过；V1 为 joint_interpolated_ik / 180.415 秒，未复现上游提供的约 40 秒。没有完整 IK 终点/被拒轨迹证据，原因未定；MoveIt 原固定与两轮 SOP 仍均 -11。

新起点检查和单段重规划尚未进入真实 FJT 路径，工具前后运动假设、独立停稳、真实规划时限和状态/UI 不因此关闭。载荷是请求级占位几何，名义离桌面 15 mm 与上游文字 10 mm 差异待澄清；未完成实际接触与标定。V1/就绪/场景交常建烁，FSM/Action/Cancel 交孙嘉明，本地留单、不代发消息。旧 Python B03/B05/B06、Safety/依赖/限位、SDK/NUC/实机等历史缺口保留；[报告及冻结集](planner-scene-acceptance.md)将默认、诊断和上游资料分开，未推进基线。

## 2026-10-12 视觉适配器后的实验缺口

TEAMMATE-PERCEPTION-20261012 / ENV-VISION-ADAPTER-20261012 登记独立视觉分支：358 C++ 与既有回归通过，colcon 新包零测试失败；公开视觉 62 通过/1 私有证据跳过。默认 ROS 回放只收末帧，延长周期到 5 秒的一次诊断收齐四帧，两个负输入被拒；发布器 SIGINT 仍重复 shutdown。KEEP_LAST(5) 只读到源码配置，图接口未确认 history/depth；诊断完成 tick 未观察到，不扩大观察窗口。

IDL 未携带 JSON 的 mode/body_valid 等来源标记；实际 FSM 话题消费链尚无实现。人工 true-ring/NaN/旧时间候选通过 Python 静态谓词，是未接通完整门禁的局部反例，不是实际机器人动作。该项交孙嘉明，回放就绪/测试登记/依赖说明交孙浩然，真实 TF/时钟/位姿交韩明赫。16 帧合成不是 22 帧私有回放，也不是私有 215 套件；四色实测、XYZ/Yaw/提环、物理 ID、CAD 私有资产/许可、Python3.12 CAD 后端均未验。上游“official/calibrated”配置标签不改变本项目事实口径，见[验收及证据](vision-adapter-acceptance.md)。旧 Python、MoveIt 退出、SDK/NUC/实机缺口与正式锁定保持。

## 2026-10-12 规划主线合并后的实验缺口

TEAMMATE-PLANNERMAIN-20261012 / ENV-PLANNER-MAIN-20261012：上游 PR #3 合入 main，f7eaa2c 整树等同已验 4a1a816，14 包 / 387 C++ / 269 Python / 15 Mock E2E / 6 ROS 通过。没有新入口，不重跑相同规划 SOP 或把旧四场景结果记为本次；前次默认 V1 超 24 秒预算、V2 TF 失败仍未关闭。

本次默认独立 MoveIt 规划成功，但内部 FJT 客户端未连接，执行 ABORTED/-4；外部探针同时可见唯一 FJT 服务端，不能将它当内部就绪证明。一次额外 5 秒等待诊断执行通过，关节误差约 0.000089 rad；这不证明根因或可靠等待阈值，move_group 两次仍 -11。旧 Python Cancel 本次受理后 ABORTED/520，未取得子任务停稳；内核交孙嘉明，默认规划问题交常建烁，集成继续跟踪就绪和退出。

场景/载荷/视觉增量还在独立分支，不将其能力归入此主线。统一 Bringup、实际 PlannerPort/FJT/工具/感知、完整状态、SDK/限位/实机缺口继续保留。450 文件冻结和原失败见[报告](planner-main-acceptance.md)；域 131 daemon 已按域停止，两个容器停止后才登记完成回执，正式 1d940f7 锁定未变。

## 2026-10-12 Phase 2B 轨迹端口后的实验缺口

TEAMMATE-TRAJECTORY-20261012 / ENV-TRAJECTORY-20261012：新端口普通及UBSan各424项通过，包含新增30验证器/36 ROS Fake Action；14包、269 Python/15 E2E/6 ROS、外部CMake consumer通过。GenericSystem success没有复现上游成功：同UUID控制器SUCCEEDED且六关节+0.02rad，端口却返回STOP_UNKNOWN/230、运行证明失效并锁故障。外部876新时间戳不能证明端口内部健康条件；未定位具体失效谓词，保留失败回交孙嘉明，未重跑覆盖。起点不符和取消各一次通过。

默认Action仍Mock，FSM首段注入不等于完整抓放；直接Cancel保留FAULT/520，异步停稳桥/runtime host仍缺。孙嘉明负责FSM/Action/Motion/Cancel内核与230定位，本轮只本地交接。Planner/视觉/场景增量尚不在此分支，实际执行权、标定输入、工具/接触与完整任务仍待集成。独立MoveIt本次执行通过而退出-11，旧Python220/510/220、Generic统计线程退出报错、依赖/lint/限位、TSan、SDK许可/厂商校验、NUC/实机继续未验收。683文件与原失败见[报告](trajectory-execution-acceptance.md)，全部任务容器停止后登记回执，正式锁定不变。

## 2026-10-12 标定/TF 交付后的实验缺口

TEAMMATE-CALIBRATION-20261012 / ENV-CALIBRATION-20261012：06ab689新增38个离线文件，54测试、6示例、5反例及格式检查通过；14包/387 C++/269 Python/15 E2E/6 ROS为本次固定运行。Fake只读TF核验四条关系、903零关节戳、腕部至ee固定Z+90°；无Goal，不补写为相机标定或完整任务。8条真实变换UNKNOWN、误差/年龄阈值null、手眼/TCP/误差表无样本；末端选型和实际安装不因上游交接陈述自动改变。

动态相机ROS观测时间与Core时钟尚未协调，Planner仍latest TF；已做TCP逆补偿，工位独立朝向未消费，离线拒绝/MEASURED声明不能替代运行接线或实物证据。标定交韩明赫、相机交孙浩然、规划交常建烁、FSM/Action/Cancel及时间/失败传播交孙嘉明。旧Python220/510/220、MoveIt退出-11、统计线程清理报错、依赖/lint/限位、SDK/NUC/实机缺口保留。532文件与原失败见[报告](calibration-acceptance.md)；源码/正式锁定未变，两容器停止后登记完成回执。

## 2026-10-12 命令身份修复后的实验缺口

TEAMMATE-TRAJECTORYGATE-20261012 / ENV-TRAJECTORY-GATE-20261012：45f497c本次15包、463项普通/UBSan、269 Python/15 E2E/6 ROS与四个GenericSystem场景通过。前次230没有对应健康谓词修复，原失败仍待孙嘉明归因；不同ID/内容的结果缓存与当前停稳证据须区分。

默认MoveIt/FJT同时存在2个执行客户端，ready=0、零Goal；需要独立planning-only与唯一执行管理者，不能放宽exclusive_graph。211点/20.94617995秒规划可被跨包读取，但按原窄速度限制拒绝；未改轨迹、stamp或能力范围。Planner生成/观测时刻与FJT调度时刻、异步Cancel/停稳桥、默认真实绑定、工具/感知/标定和完整FSM仍未接通。两次MoveIt退出-11、旧Python220/510/520、统计线程、驱动lint/依赖/限位、TSan/SDK/NUC/实机未完成。869文件、原失败与清理见[验收报告](trajectory-gate-acceptance.md)，只本地交接，不接管内核或推进正式基线。

## 2026-10-12 视觉安全更新后的实验缺口

TEAMMATE-VISIONSAFETY-20261012 / ENV-VISION-SAFETY-20261012：53项新测试、62公开回归通过，1项私有22帧证据跳过；默认和两次插桩回放各4/4，SIGINT exit 0，视觉重复shutdown已局部复现修复。默认源码没有订阅等待屏障，旧1/4漏帧仍保留；两次插桩使用合成数据，其中一次只改mode=replay，均不是实录。

colcon实际调用unittest -v、0 tests/exit 5，新增pytest未自动登记。可信帧/采集戳TF只是独立helper，本地Buffer通过不等于相机标定；调用方回调、坐标变换、来源/时钟契约及FSM真实消费链仍缺。旧Python静态反例仍接受true-ring/NaN/旧戳，没有实际动作。视觉入口交孙浩然，FSM/Action/Cancel交孙嘉明，TF/时钟交韩明赫，只本地留单。旧Python220/510/520、MoveIt退出-11、依赖/lint/SDK/NUC/实机缺口保留。463文件及原失败见[报告](vision-safety-acceptance.md)，两个容器停止后登记complete，正式锁定未变。

## 2026-10-12 监测结束后的新增验收范围（原安排，结果见文末）

USER-HW-20261012 / USER-HW-20261012-02 已明确统一 C++ Mock Bringup、真实 Task→PickPlace Action 与 Web UI/必要桥接为同轮交付，最早开始时刻为北京时间 08:00，且必须先完成原监测最后事件的分析、归档、回执与清理。Q18/Q19 仍未关闭：候选 SHA、真实上下游 Goal/Feedback/Result/Cancel、类型/QoS/唯一服务器、停止重启残留及 UI 接口均待实际验证。对应安排见[硬件与传统视觉方案](hardware-vision-plan.md#2026-10-12-0800-后的-c-mock-与-web-ui-同轮交付待执行)。

启动、最小接线、UI/桥接由集成侧完成；FSM 状态转换、Action/Cancel 和 Motion Execution 内核缺陷仍交孙嘉明。先交队友仓库独立分支/PR，再向个人 origin/main 推送可追溯报告与证据，均已授权；不自动合并、推进基线或接实机。此段记录授权和待办，不是运行结果，旧失败证据保留。

## 2026-10-12 回放自然退出补验后的实验缺口

TEAMMATE-VISIONREPLAY-20261012 / ENV-VISION-REPLAY-20261012：dc76a0b 的57项适配器与80项公开视觉通过，1项私有证据跳过；原安装程序两次4/4自然退出、两次2帧后SIGINT退出均0，可选等待的无订阅者负例明确超时。默认wait=0并无送达保证；首次图快照节点名UNKNOWN，不能当唯一命名节点证明；真实最终ACK超时未注入。colcon仍零收集，新增私有V4.1/V4.2入口均因缺目录/数据在帧处理前失败，不认定性能或实测精度通过。

实际Task感知仍Mock且未调用安全helper，Q18/Q19不因独立回放通过而关闭。视觉自动登记、图采样和输入缺口交孙浩然；FSM/Action/Cancel与原消费者反例交孙嘉明；真实TF/时钟交韩明赫。原Python220/510/520、独立MoveIt退出-11、SDK/NUC/实机缺口保留，详见[本轮报告](vision-replay-acceptance.md)。原/补跑容器已停止、486文件冻结；08:00后集成/UI任务仍待指定时刻与监测排空。

## 2026-10-12 Goal归属更新后的实验缺口

TEAMMATE-OWNERSHIP-20261012 / ENV-TRAJECTORY-OWNERSHIP-20261012：首次FJT套件120秒停在DuplicateCancelOnlyOneBackendCall，missing_result保留；61项同二进制补跑和478项UBSan通过只说明各次运行结果，不证明挂起已修复。没有原现场线程栈，孙嘉明需区分夹具与生产端口锁/生命周期或ROS调度原因，保留有界失败复现与回归。

新的Status门禁在原生GenericSystem无实时Status时拒绝首个Goal；有效接收年龄不等于绝对新鲜度或跨进程互斥。默认MoveIt额外FJT客户端仍阻断。应由孙嘉明确认可信Status/单一执行管理契约，常建烁和集成共同确认规划时基和执行权；不得通过空数组、心跳、预热Goal或修改限制换取通过。原生cancel/mismatch/identity未执行，独立Fake61测试不替代原生/完整FSM。旧Python220/510/520、MoveIt退出-11、依赖/驱动lint、SDK/TSan/NUC/实机缺口不变。见[报告](trajectory-ownership-acceptance.md)与708文件冻结，08:00后C++Mock/UI任务未提前运行。

## 2026-10-12 C++ Mock 与 Web UI 集成后的实验缺口

ENV-CPP-MOCK-WEBUI-20261012 / TEAMMATE-CPPUI-20261012：监测08:00自然结束、14份签收报告哈希不变后，隔离候选 `7da4322…` 统一启动与真实父子Action/Web集成部分通过。40 C++ Action、39 UI回归与六项真实链路正负场景通过，节点/类型/QoS/唯一服务器、重复启动、停止与重启图排空均保存；硬件状态不生成。具体命令、UUID、953文件冻结和[PR #8](https://github.com/F1u0rite/meituan_challenge_ws/pull/8)见[本轮报告](cpp-mock-webui-acceptance.md)。

C1仍未通过：正常Mock700ms结果交付延时，浏览器及独立CLI延迟取消均ACK后父子ABORTED/520、完成数0并锁定下一任务；及时CANCELED/0正例不覆盖此失败。静态停稳证据龄期/时钟分析仅为候选根因，准确判据、Cancel契约及回归由孙嘉明确认；没有接管内核或放宽检查。张叔阳负责复验和集成材料。完整视觉/工具/Motion/FJT/MoveIt链路、故障恢复、NUC/实机与原独立失败未关闭，Q18/Q19仍部分确认。代码独立PR待审，正式pin仍1d940f7，不自动合并。
