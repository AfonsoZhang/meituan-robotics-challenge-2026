# 标定 / TF 交付的离线与 Fake 验收

**2026-10-12 固定版本结论：新增 54 项离线测试、6 个示例、5 个生成反例及一次只读 Fake TF 核验通过；当时真实相机外参、TCP、工位标定和运行适配器接线仍未完成。原任务链路与 MoveIt 退出失败保留。**

**2026-10-14 后续用户确认：TCP 已做验证**（USER-HW-20261014-04），具体工具/TCP 版本、数值、方法和结果记录待补充。下文继续保留原固定版本的检查结果，不能据当时的空采样表或 PR #17 的测试范围否定后续现场验证；本轮未重跑或改写冻结证据。

固定提交 `06ab689f25e87dcebf9fd04fdd581ec4755206f6` 来自 `feat/calibration-tf-v1`，登记为 TEAMMATE-CALIBRATION-20261012；本项目观测为 ENV-CALIBRATION-20261012。固定复现后一次投递，主对话约 **8.02 秒**签收；依据 USER-HW-20261011-08、USER-HW-20261011-09 阅读实际变更、补验并归档。没有合并或推进 `robot/fsm-baseline.repos` 的正式锁定 `1d940f7c5f12561fed6641457c0b4b630a282b05`。

**实际变更与确认边界。** 相对监测基线累计 119 个路径；相对已验 `main@f7eaa2c…` 仅新增 **38 文件**，包含离线 SE(3)/TF 输入契约、名义支架推导、旧模型/日志审计、示例、54 项测试、标定清单和交接文档。全部既有 `src` 树、规划证据与配置保持相同，前验 ENV-PLANNER-MAIN-20261012 的 450 文件及签收报告重新核对一致。此分支未包含新轨迹端口、视觉适配器或新规划场景分支；默认 Action 仍绑定 MockPlanner/AsyncMockMotion。

上游交接写有“明天使用 V1 舌规”“用户确认法兰附近相机安装”等前提，**仅登记为上游交接陈述，不作为本项目本会话新增的用户确认**。本报告当时按 USER-HW-20260906-03 区分眼在手上安装计划和实际安装；末端候选范围与未选型状态保留，不把设计夹具变为实测安装外参。**2026-10-14 后续澄清：** 用户明确采用眼在手外（USER-HW-20261014-03），当前方案改用固定相机到基座外参；本报告原版本、测试与冻结证据不因此改写为新布置已验证。

新工具统一 `T_A_B` 将 B 系坐标变到 A 系，保留位置、xyzw 完整姿态、frame 和观测时戳。UNKNOWN 边禁止数值占位；REAL 诊断要求所经边为 MEASURED 且有 evidence 字符串，但工具不能核验引用真实性、实测误差或安装稳定性。所有诊断均输出 `motion_authorized=false`，不产生运动 Goal。

**本次环境与固定复现。** 原运行是上海时间 10 月 12 日 02:06:13—02:11:23；25 步均有起止时间和退出码，stop/collect 成功，305 个原文件哈希一致。先确认原 runner 32186 和旧任务容器停止，再用已停止容器的独立快照补验。Ubuntu 24.04 / Jazzy / C++17、Python 3.12.3、驱动 `53aab837…`、模型 `47fa5e02…`、MoveIt 2.12.4；无网络/设备/挂载/端口，2 CPU / 4 GiB / 512 PID、cap-drop ALL/no-new-privileges。未安装依赖或修改上游源码/控制参数。

| 检查 | 本次结果与范围 |
| --- | --- |
| 构建 | 14 包通过；标定交付是离线脚本，没有新增 ROS 包 |
| C++ | **387 / 24 程序通过**：318 核心 + 40 Action + 29 Planner；源码与 XML 测试身份一致 |
| Python / 显式 Mock E2E / ROS 接线 | **269 / 15 / 6 通过** |
| 旧固定 C++ 审计 | 失败：源码预期 16 个 `*_cpp` 程序、日志实际 20；missing/unexpected/duplicates/bad 均为空，规划包不匹配该 glob |
| 新审计入口 | 补跑 **358 / 20 通过**，规划 29 / 4 另核对；colcon 685 含包装和 lint，不作独立功能计数 |
| 新增标定离线测试 | **54 / 54，无跳过**；AST 测试身份和逐项执行日志对应，不包含在原 269 项中 |
| 交付 CLI 示例 | 6 项全部符合预期，含成功诊断和预期拒绝 |
| 生成反例 | 5 项全部按预期拒绝：超大整数、20 万层 JSON、设计中把 mm 数值误填入 m 标签 |
| 文件检查 | JSON/UNKNOWN-null 纪律、4 类 CSV 列宽与 42 个本地链接通过 |

补跑原 `run_offline_validation.py --out /review-evidence/offline`，输出写到独立证据目录，上游已归档结果未覆盖，运行后 Git tracked diff 为空。5 个单独诊断 JSON 的解析对象与上游一致；生成反例的结果和非命令字段相同，命令仅有 Windows/Linux 临时路径分隔符差异。上游的 Windows/Python 3.11.9 结果与本项目 Linux/Python 3.12.3 运行分别保存。

| 离线入口 | 实际结果 |
| --- | --- |
| synthetic | DIAGNOSTIC_OK；位置 `[1, 1.1, 0.05]`、姿态约 `[-0.70710678, 0, 0, 0.70710678]`，保留 `10000000000 ns`，SYNTHETIC_ONLY |
| unknown_extrinsic | 退出 2 / UNKNOWN_CALIBRATION，未把未知边当单位变换 |
| nominal_mount | ESTIMATED，设计 F 到 depth optical 为 `[0.0825, 0, 0.0358] m`，deployment_ready=false；只是上游设计夹具推导 |
| design_not_real_case | 退出 2 / INVALID_CONFIG，设计 JSON 不是观测输入 |
| site_inventory_not_a_case | 退出 2 / INVALID_POSE，待测清单没有观测 |
| fake_model_audit | 旧 Fake 归档模型、SRDF 与三份 TF 日志一致，样本数 5 / 5 / 7；real_calibration_verified=false |

旧 TF 日志以三位小数打印，最大平移分量差约 0.0002 m，是模型与舍入文本的比较，**不是标定精度**。单位/四元数标签合法也不能从数值自动证明实物单位或 xyzw/wxyz 顺序正确；设计输出的孔位基准、光学偏移、相机 wrapper 约定仍是上游引用与假设。本轮未重新下载或核读该相机 PDF/API 资料，不将算术复现当成厂商尺寸复核。

**只读 Jazzy Fake TF 补验。** 为核对交接中新强调的 `wrist3_Link` 与 `ee_link` 区别，在域 138 启动一次明确的 GenericSystem 驱动。验收观察器只读 JointState、TF、robot_description 和控制器状态；没有创建 ActionClient、TF 发布器或发送 Goal。两个控制器 active，FJT 图为客户端 0、服务端 1，无 Goal 状态，取得 **903 个不同 JointState 时戳**，六关节位置和速度均为 0。

读取实际 `robot_state_publisher` 参数，robot_description SHA-256 为 `f36ba2a4944c16f86a58cb448ef06a7911c4c0d70a49b38da516e7943610618e`。上游 official-source receipt 的四个 AUBO 文件已与本地固定 `47fa5e02…` Git blob 核对，大小/哈希一致；其余七项相机/API 原件未在本轮独立复核。部署用 Fake Xacro 修改与原 Git blob 的来源身份分开记录。

在同一约 200 ms 前的时间 `1791742548271182873 ns` 查询四条变换，返回时戳一致，并与实际展开模型的零关节 FK 对照：

| `T_A_B` | 平移 m | xyzw / 含义 |
| --- | --- | --- |
| world ← base_link | `[0, 0, 0]` | `[0, 0, 0, 1]` |
| wrist3_Link ← ee_link | `[0, 0, 0]` | 约 `[0, 0, 0.70710678, 0.70710678]`，绕 Z **+π/2** |
| base_link ← ee_link | 约 `[0, -0.2562, 0.8072]` | 约 `[0.5, -0.5, 0.5, 0.5]` |
| world ← ee_link | 约 `[0, -0.2562, 0.8072]` | 同上 |

比较误差处于浮点舍入量级，不能外推为实体精度。静止零关节 Fake 的一次过去时刻查询，也不证明随腕相机的采集同步或动态历史 TF 已接入任务链。静态 frame 图的 stamp 0 仍是静态变换语义，不作为相机观测时间。

本次 `camera_link`、`camera_color_optical_frame`、`hook_tcp_v1`、`table_frame`、T0/P1/P2/P3 提案 frame 均不可达，没有补发零 TF。真实清单的 **8 条变换仍全为 UNKNOWN**、阈值仍 null；手眼、TCP、误差验证三个 CSV 只有表头，零实测样本。固定模型旋转没有证明物理法兰设计 F 与机器人腕部坐标已经对齐。

**实际集成缺口。** 已审阅当前规划实现：`MoveGroupBackend::transform_to_planning_frame()` 将 ROS 输入 stamp 设为 0，查询 latest，因为 Core `Pose6D.stamp_s` 属于 FSM 时基。离线诊断要求观测时刻一致，并没有把这一要求接入运行适配器；ROS 采集时间与 Core 看门狗时间仍需明确转换与失败传播。

规划已经按 `T_planning_TCP × inverse(T_EE_TCP)` 做 TCP 补偿，离线算出的 EE 目标不能再当 TCP/ring 目标输入，否则重复补偿。当前工位规划使用落座 TCP 位置并沿用抓取姿态，没有消费独立工位目标朝向；电池中心、台面中心和 TCP 目标语义不能混用。交付没有 ROS TF 监听/发布节点、手眼求解器或实际消费诊断结果的桥接；本次只读观察器是验收工具，不是交付功能。

**原失败继续保留。** 全空间缺 `ament_python` rosdep 定义；驱动缺 `docker.io`、`ros-jazzy-ros2-controllers-test-nodes`。驱动汇总 1104 条、279 failures、259 skipped，包含 description 的 flake8/lint_cmake/pep257/xmllint、生成 C 的 uncrustify 和包装统计，不作实机功能计数。

旧 Python Mock 早 Goal 为 ABORTED / 220，延迟 INIT 为 ABORTED / 510，Cancel 受理后仍 ABORTED / 220，全部完成数 0；B03/B05/B06、PickPlace `create_client` 和 Safety 清理错误未解除。独立 MoveIt 本次执行 SUCCEEDED / 1，最大关节误差 **0.00009371537333354354 rad**、209 个不同反馈时戳，退出仍 **move_group -11 / control 0**。该执行与标定诊断没有接成完整 FSM。

既有运行树未变，因此本次没有重复规划 SOP、独立 Action 四场景、UBSan/外部 consumer；历史结果仍见 ENV-PLANNER-MAIN-20261012、ENV-PLANNER-MERGE-20261012。独立轨迹事件的 230、视觉和场景分支缺口各自保留，未混入此快照的能力或计数。

| 本地交接对象 | 剩余事项 |
| --- | --- |
| 韩明赫：标定 | 物理 F/腕部对齐、实物安装外参、TCP/台面工位与独立误差数据，保存版本及假设 |
| 孙浩然：视觉 | 设备内参/内部 TF、实际 optical frame、采集时戳和 ring 定义 |
| 常建烁：规划 | 观测时刻 TF、单次 TCP 补偿、工位语义/朝向与标定参数消费 |
| 孙嘉明：FSM/Action/Cancel | 完整 Pose6D、ROS/Core 时钟、失败传播、旧任务阻断和实体停稳；不接管内核修复 |
| 系统集成与验收 | TF 发布源/Bringup、采集和日志、证据登记；跟踪退出、依赖及完整链路 |

分工依据 SPRINT-PLAN-20261011 §01–07；以上为本地交接材料，未代发外部消息。真实设备/工具选型与安装、时钟/运动相机同步、手眼精度、真实碰撞/接触、SDK 许可/厂商校验值、符号限位、TSan、NUC 与实机仍未验收，旧仿真范围不变。

**清理和事实链。** 本次只读驱动/控制器退出 0，无升级终止；退出日志仍有 `pal_statistics` invalid-context 线程错误。按域停止 ROS daemon 并确认空域。清理守卫首次因复用脚本的 SHA 比较字符串损坏而拒绝，尚未停止容器；错误脚本/进程快照保留，修正比较值并核验实际 HEAD、源码未改且仅 keeper 后才停止。分析阶段另保留两个比较断言：Windows/Linux 路径分隔符，以及旧审计预期数在源码而非日志；均仅修正证据比较，没有重跑测试或修改运行结果。原 runner 32186 不在，原/补跑容器均停止、无 OOM。

- [冻结索引](experiments/calibration-20261012/index.json)：**532 文件**，SHA-256 `ce5dfdfb811d23d08e6122fca38d1aee16f6b87da2a518cfa99230976f18182d`。
- [输入与版本](experiments/calibration-20261012/inputs.json)、[摘要](experiments/calibration-20261012/summary.json)、[协议](experiments/calibration-20261012/protocol.md)、[逐项分析](experiments/calibration-20261012/supplement/supplement-analysis.json)。
- [54 项测试原日志](experiments/calibration-20261012/supplement/container/offline/unittest.txt)、[离线结果](experiments/calibration-20261012/supplement/container/offline/results.json)、[只读 TF 结果](experiments/calibration-20261012/supplement/container/fake-tf/summary.json)、[运行模型](experiments/calibration-20261012/supplement/container/fake-tf/robot-description.urdf)。
- 原运行：`outputs/moveit-watch-20261011/runs/sha-06ab689f25e87dcebf9fd04fdd581ec4755206f6/`；原 index SHA-256 `f42af8018bc0166a8d39a0b4501ae5184751704e3ba7bee1a9bf389a6f7050a2`。
- 补跑与分析：`outputs/calibration-acceptance-20261012-06ab689/`；命令/退出码在 `logs/`，新增结果在 `container/`。
- 回执：`outputs/moveit-watch-20261011/wake/sha-06ab689f25e87dcebf9fd04fdd581ec4755206f6/receipt.json`；冻结 complete 前状态，最终回执只存 raw。

原始失败、历史冻结与已签收报告保持不变；bundle/镜像/SDK/构建二进制不入库，仅记录版本和哈希。同步 manifest、对应文档、open-questions、README 与 derived_files 并核验后登记 complete，表示本事件分析结束，不表示完整技术验收通过。原 60 秒轮询、固定会话、上海时间 10 月 12 日 08:00 截止不变，本轮没有调用 queue 或新启监测。

生成式 AI 披露：OpenAI Codex 协助源/日志核对、运行交付入口、编写只读 Fake TF 观察及分析/清理脚本、整理可追溯记录；没有上游 FSM/Action/Cancel/规划/标定算法修改。来源 TEAMMATE-CALIBRATION-20261012、TEAMMATE-PLANNERMAIN-20261012、TEAMMATE-PLANNER-20261011、TEAMMATE-SDK-20261011；根/规划 MIT 与 Action package.xml Apache-2.0 差异、模型/SDK 许可缺口保留，不重新授权。
