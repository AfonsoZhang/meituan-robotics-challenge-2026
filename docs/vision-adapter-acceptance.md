# 视觉源码迁移与 ROS 回放适配器验收（2026-10-12）

**结论：部分通过。现有回归通过；补齐离线依赖后，公开视觉测试 62 项通过、1 项私有证据跳过。真实 Jazzy 默认回放只收齐 1/4 帧，延长周期的一次诊断收到 4/4 帧并核对 NaN 位姿；发布器退出仍失败。实时相机、标定与完整 FSM 消费链尚未验收。** 来源 TEAMMATE-PERCEPTION-20261012，本地观测 ENV-VISION-ADAPTER-20261012。

## 实际变更与分支范围

SHA `0e329f10e6f607c9c417a54ae60d290b8e2395b5` 来自 `feature/perception-adapter`，Git 作者 BHBAllen，父版本为 `a04ac6831dd3963e6b1ec4b9e27214eb564f9f24`。实际新增 111 文件：9 个 `mtc_vision_adapter` 文件、102 个 `vision_core` 文件。其余源码与父版本逐路径相同，既有 IDL、FSM、Action 未改。此前主线版本验收见 ENV-HANDOFF-20261012。

此分支从主线分出，**没有 `mtc_moveit_planner` 包**。因此本次 358 项 C++ 与前一场景分支的 393 项是不同分支范围，不能解释为相同源码退化或漏测，也不能把两个分支拼成已接线系统。本项目正式锁定继续为 `1d940f7c5f12561fed6641457c0b4b630a282b05`。

上游声明这是已有 RGB/HSV、RGB-D、像素关联、CAD 候选、录制/回放、评估与合成代码的源码迁移。没有提供私有 STEP、真实图像、22 帧回放或原私有 215 项套件。独立 Python 核心使用通用模块名 `input/perception/config`，文档只声明 editable 源码布局；本轮不扩展为可独立分发 wheel、原算法出处或真实精度认证。

ROS 入口 `replay_publisher` 只接受标有 `synthetic/replay` 的 JSONL，保留记录时间戳，将未测量的 JSON null 转为 ROS NaN，并强制 `ring_pose_valid=false`。它没有实时相机输入，未向执行器发出运动请求。

## 自动复现与补跑条件

按照 USER-HW-20261011-08、USER-HW-20261011-09，原固定运行于上海时间 **01:04:55—01:09:38** 完成。主对话 ack 返回 `CLAIMED`，已输出 `MOVEIT_WAKE_ACK_c2eae3a8db5faca107f54677c54c3497`；一次投递至持久化 ACK 约 **5.92 秒**。本轮未另发 queue 或启动另一监测。

先确认原 runner PID 18721 和前序复现进程结束、原/旧事件容器停止，再从停止原容器建立独立文件系统快照。补跑保持无网络/设备/挂载/发布端口、2 CPU / 4 GiB / 512 PID、cap-drop ALL / no-new-privileges，所有入口串行。没有重启原容器、覆盖原始失败，或打开相机/发送 Task Goal。

| 检查 | 本次结果及边界 |
| --- | --- |
| 固定 summary 与原件 | 25 步完整，stop/collect 成功；301 个原索引文件 SHA 核对一致，`COMPLETED_WITH_FAILURES` 保留 |
| 构建 | **14 包 PASS**，包含新视觉适配器，未包含规划包 |
| C++ | **358 / 20 个程序 PASS**：核心 318 + Action 40，真实 XML 身份逐项对应源码 |
| Python / 纯 Mock E2E / ROS 接线回归 | **269 / 15 / 6 PASS** |
| 旧固定 C++ 审计 | **FAIL**：旧预期 16 个 `*_cpp` 程序，实际 20；无缺失/意外/重复/坏用例 |
| 交付的 Action verifier 补跑 | **358 / 20 PASS**；适配器安装代码与源码一致 |
| `colcon-test` | **FAIL / 5**：`mtc_vision_adapter` 收集到 0 测试，日志明确 `NO TESTS RAN` |

`colcon test-result` 的 652 条成功 XML 汇总含包装/lint，而且未覆盖没有收集到测试的新适配器，不能用它取消上述失败。`vision_core/tests` 位于 ROS 包外，固定脚本没有运行，故本轮单独补验。未重复无变化的独立 C++ 四场景、UBSan/外部 consumer，也未运行本分支不存在的规划包入口。

## 离线依赖、公开测试与合成入口

原容器直接运行 `vision_core/tests/test_ros2_p0.py` 得到 **27 PASS / 1 SKIP**。直接运行完整公开目录则在 collection 阶段因缺少 `cv2` 退出 2；原 pytest 7.4.4 也低于新声明的 `pytest>=8`。这些初始结果保留。

在主机从 PyPI 获取 23 个 CPython 3.12 二进制依赖轮子，保存每个版本、SHA、来源和许可元数据，再复制到**仍无网络**的容器安装。使用独立、可见原 ROS site-packages 的 `/review-venv`，没有改宿主 Python 或上游算法。

| 安装阶段 | 实际结果 |
| --- | --- |
| 初次工具链 | 验收脚本选择的 setuptools 80.9.0 不符合现有 colcon-core `<80`，且 adapter 旧 editable 安装在 `develop script_dir` 处失败；属于环境选择/兼容性证据，未归为视觉算法失败 |
| 一次 PEP517 诊断 | adapter editable 构建成功，但 `pip check` 仍报告 setuptools/colcon 冲突 |
| 最终兼容环境 | 恢复镜像自带 setuptools **68.1.2**，两条交付 editable 安装及 `pip check` **PASS**，无源码修改 |

最终 Python 3.12.3、numpy 1.26.4、scipy 1.11.4、opencv-python 4.8.1.78（模块版本 4.8.1）、PyYAML 6.0.2、matplotlib 3.8.4、pytest 8.3.5、pip 25.0.1。依赖锁定及原失败见冻结脚本/日志，轮子不入冻结集。此环境结果不证明任意未来版本组合均兼容。

初始补齐环境和最终兼容环境各运行一次公开目录，均 **62 PASS / 1 SKIP**。计数只登记最终一套 62，不累加两次；前述 27 adapter 测试已经包含在 62 内。跳过项为 `test_saved_offline_evidence`，它要求未交付的私有 22 帧记录，不能写成通过或原私有 215 项已复现。

两相机脚本 `live_rgbd_preview.py --help`、`live_realsense_handheld.py --help` 均通过，仅验证入口导入/参数解析，没有打开设备。`replay_ros2_p0.py` 生成 **16 帧合成输入、50 个候选、5 个历史 ID**，覆盖枚举 1/2/3/4；所有未测位姿保持严格 JSON null，16 帧的本地 helper 均标记 `REPLAY_NOT_MOTION_INPUT`。缺失真实 session 的 replay 部分为 **0 帧**，单独记录，不能算真实数据回放通过。

这些是合成软件路径和像素关联结果，不证明真实四色识别率、相机运动下物理身份稳定、定位精度或姿态可用性。

## 实际 Jazzy 消息与默认漏帧

使用原来 colcon 安装的发布器、真实生成的 `BatteryDetectionArray` 和独立 DDS 订阅器，未用 SimpleNamespace 替代原生消息。订阅器先创建，然后启动上游 README 命令，输入为原四帧 `examples/synthetic.jsonl`。

| 检查 | 默认域 129，period 1 秒 | 一次诊断域 130，period 5 秒 |
| --- | --- | --- |
| 发布器日志 | 四帧均记为已 publish，随后 `replay complete` | 四帧均记为已 publish |
| 订阅器实际收到 | **1/4 帧，FAIL**；只有最后一帧，stamp 为 1700000000 / 750000128 | **4/4 帧，消息契约 PASS** |
| 时间戳/帧/颜色/ID/NaN 全序列核对 | 未收齐，不通过全序列检查 | 与原 JSON 逐帧匹配；四色枚举、null→原生 NaN、false ring flag 均通过 |
| 实际发现的类型/QoS | 唯一 `mtc_interfaces/msg/BatteryDetectionArray`、RELIABLE、VOLATILE | 同左 |
| history/depth | 图接口返回 UNKNOWN / 0 | 图接口返回 UNKNOWN / 0 |
| 控制退出 | SIGINT 后退出 **1**，无升级终止 | SIGINT 后退出 **1**，无升级终止 |

**KEEP_LAST(5) 是已读源码中的配置；本次图接口没有证实运行时 history/depth 值。** 诊断只改变发送周期和隔离域，输入字节、旧时间戳、安装发布器和消息内容不变。默认只收到最后一帧、延长周期后收齐，与本环境发现/就绪时序问题相符；发布器没有等待订阅匹配的屏障，具体原因仍未定位，不能据一次诊断宣布默认入口已修复。

默认完成后仍保持 spin，需要外部结束；SIGINT 引发 KeyboardInterrupt，finally 再次调用 shutdown，报 `rcl_shutdown already called`。诊断也有同一退出异常。诊断在末帧后只观察 1.5 秒就结束，尚未到下一次 5 秒 timer 的完成日志；原探针 “no-loop” 标签只能覆盖该观察窗口，不能扩展为已验证此轮 timer 取消。默认已实际观察到完成日志和空闲状态。两个晚加入订阅器在各自窗口内均没有历史消息。

原默认运行另测空文件和 `mode=live` 两个输入负例，均在发布前明确拒绝、退出 1；它们与成功回放后的退出异常分开分类。

## 消费门禁与标定边界

实际收到的候选均为 `ring_pose_valid=false`、body/ring 非有限位姿；调用现有 Python `TaskExecutorNode._is_usable_candidate` 静态谓词会拒绝这些实际候选。随后只在验收进程内复制一个候选，**人为将 ring flag 改 true、保留 NaN 和旧时间戳，该谓词返回 true**。这是函数级输入校验缺口；反例没有发布、没有创建 Task 节点或 Goal，不能描述为已经使机器人接受了危险运动。

源码进一步表明：

- C++ Task 仍直接创建 `MockPerception`，未订阅新视觉话题。
- Python Task 只有可注入 perception provider，未提供该话题的真实订阅适配。
- `motion_rejection` 只在独立 helper/测试/回放生成器使用，没有接成实际 FSM 输入门禁。
- ROS IDL 仅含 header/detections 及对象字段，没有 JSON 外层的 `mode`、`body_pose_valid`、坐标模式或标定来源字段。接口裁决和消费侧回放/时效/有限数/坐标门禁仍需落实。

因此本轮证明的是隔离消息传递和部分局部检查，不能外推为真实 FSM 已拒绝所有 replay/NaN/过期输入。该项按职责本地回交孙嘉明，不接管 FSM/Action/Cancel 内核。

帧名含 `synthetic_unregistered`，未建立已标定 TF；body/ring 位姿全无效。真实 XYZ/Yaw、提环孔位、桌面/工具/手眼标定、物理 ID 稳定性、真实四色验收、CAD 私有原件及 Python 3.12 CAD 后端均 **NOT RUN / NOT MEASURED**。`competition.yaml` 的 `explicit_official/map_calibrated` 是上游标签，本轮未重新对照原件或实测，不能据此新增比赛规则、认定标定完成或改变本项目尺寸口径。

## 原有失败、交接与证据

原固定运行的旧 Python 仍有 B05 PickPlace `ExecuteJointMove.create_client` 启动失败，B03 被遮挡；尽早 Goal ABORTED / 220、延迟 Goal ABORTED / 510（B06），Cancel 接受后最终 ABORTED / 220、完成 0，Safety 清理仍失败。全空间 rosdep 缺 `ament_python` 定义，驱动缺 `docker.io` 与 `ros-jazzy-ros2-controllers-test-nodes`；驱动 1104 条汇总 / 279 failures / 259 skipped 含 lint/包装，未通过。

原自动独立 MoveIt Plan→Execute **PASS**（Action status 4 / MoveIt code 1），209 个不同关节反馈时间戳，最大误差 `8.713780655525625e-05 rad`；move_group 退出 **-11**、控制节点 0。这条路径未连接新视觉，也不是完整 FSM/实机。

| 本地交接对象 | 待办与未验范围 |
| --- | --- |
| 孙浩然：感知接口（按 SPRINT-PLAN-20261011 §04、§07–08 分工） | ROS 包测试登记、默认回放就绪/退出、依赖兼容说明、实时发布入口、有效性与移植来源/资产授权 |
| 孙嘉明：FSM/Action/Cancel | 实际感知订阅、回放/时效/非有限/坐标门禁、上述静态反例；旧 B03/B05/B06 及完整执行闭环 |
| 韩明赫：标定 | frame/时钟来源、TF、手眼/工具/桌面、真实位姿与孔位证据 |
| 系统集成与验收 | 保留默认失败和诊断边界、依赖/过程核验、干净退出与事实归档；没有代发外部消息 |

前序签收报告和冻结原件未改。原/补跑容器均停止、无 OOM，原 runner 不存在；全部本轮 ROS/测试进程结束，只剩 keeper 后才停止容器，keeper 137 与发布器退出 1 分列。tracked source diff 为空；editable 安装生成的临时元数据另记，未冒充工作树完全无生成文件。

- [冻结索引](experiments/vision-adapter-20261012/index.json)：**589 文件**，SHA-256 `ba6929bb5ed074845709b904625eda122ba552849755081de69d858ba017586c`。
- [输入](experiments/vision-adapter-20261012/inputs.json)、[摘要](experiments/vision-adapter-20261012/summary.json)、[协议](experiments/vision-adapter-20261012/protocol.md)、[实际源码核对](experiments/vision-adapter-20261012/supplement/source-review.json)、[补跑分析](experiments/vision-adapter-20261012/supplement/supplement-analysis.json)。
- [原默认 ROS 失败](experiments/vision-adapter-20261012/supplement/container/ros-replay/)、[5 秒诊断](experiments/vision-adapter-20261012/supplement/container/ros-replay-wait5/)、[合成输出](experiments/vision-adapter-20261012/supplement/container/synthetic/)、[最终测试 XML](experiments/vision-adapter-20261012/supplement/container/vision-suite-compatible.xml)、[离线依赖来源](experiments/vision-adapter-20261012/supplement/offline-dependencies.json)。
- 原固定日志：`outputs/moveit-watch-20261011/runs/sha-0e329f10e6f607c9c417a54ae60d290b8e2395b5/`，原 index SHA-256 `3a169a53699ec142a93bf5e3ae7244f6cb74b1bba2735582ddd6e24487548fc1`。
- 原补跑：`outputs/vision-adapter-acceptance-20261012-0e329f1/`。最终回执：`outputs/moveit-watch-20261011/wake/sha-0e329f10e6f607c9c417a54ae60d290b8e2395b5/receipt.json`。

冻结集保留 ACK/pre-complete；文档、manifest/derived_files 校验后才 complete，最终回执仅存原目录。既有固定会话、60 秒轮询、上海时间 10 月 12 日 08:00 截止保持，未合并或推进正式基线。complete 表示本事件分析归档结束，不表示全部功能验收通过。

生成式 AI 披露：OpenAI Codex 协助编排交付入口、编写隔离消息探针、依赖兼容诊断、合成/测试结果核对及事实登记。自身错误参数调用、wheel 元数据选择和诊断完成时机分析假设保留于 harness notes/失败记录，没有归咎上游算法。未改视觉、FSM、Action、Cancel 或驱动实现。来源 TEAMMATE-PERCEPTION-20261012、TEAMMATE-ACTION-20261011、TEAMMATE-SDK-20261011；根 MIT / 新适配器 Apache-2.0 声明差异保留，原视觉迁移来源和私有 CAD 授权仍需负责人核对；SDK、镜像、wheel 和 source.bundle 不入冻结集，仅登记必要版本与哈希。
