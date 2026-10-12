# 视觉回放自然退出与 V4.2 增量验收（2026-10-12）

**结论：部分通过。安装后的回放发布器可完整送达四帧后自然退出，也可在中途 SIGINT 后正常退出；适配器 57 项、公开视觉 80 项通过，1 项私有数据测试跳过。默认 colcon 收集、私有性能入口、实际 FSM 消费链与实机仍未通过或未验收。** 来源 TEAMMATE-VISIONREPLAY-20261012，观测 ENV-VISION-REPLAY-20261012。

## 提交、签收与隔离

本次 SHA 为 `dc76a0bf0a43f9110f3d24cfa38a2b3478f48dcd`，父版本 `e09d00ede40b0fafad6cd5428ae1824442e74d3c`，观察自 `feature/perception-adapter` / PR #5 head。相对父版本修改六个文件：适配器 README、publisher、进程验证器、清理测试、新增进程测试及 vision_core README。

前次已验版本为 `e53c09f…`（ENV-VISION-SAFETY-20261012）。中间 `e09d00e…` 的十二个路径只在 vision_core 内，原监测按既有规则记录 `relevant=false`，未触发单独复现；本次累计十八个路径包含其 V4.1/V4.2 数值计算、视觉确认、诊断接口和测试增量，已一并读差异、补跑公开入口。其余 FSM、IDL、Action 源码未变，不能把其他分支的 Planner/FJT/标定能力计入此候选。

按 USER-HW-20261011-08、USER-HW-20261011-09，固定运行于北京时间 **03:31:14—03:35:02** 完成，summary 为 `COMPLETED_WITH_FAILURES`。主对话 ack 返回 `CLAIMED`，输出 `MOVEIT_WAKE_ACK_3f12fa4bcee3b22d8b6f31a9f8d62201`；一次投递至持久化 ACK 为 **5.609921 秒**。没有另调 queue、启动监测或提前执行 08:00 的集成任务。

原 runner PID 56334 已不存在，原及旧任务容器停止后，才从原停止容器建立独立补跑快照。原容器未重启；补跑为 Jazzy、无网络、设备、宿主挂载、端口映射，**2 CPU / 4 GiB / 512 PID**、cap-drop ALL / no-new-privileges。没有打开相机、启动 FSM 或发送补跑 Action Goal。正式锁定 `1d940f7c5f12561fed6641457c0b4b630a282b05` 保持。

## 原固定运行核验

| 检查 | 本次结果 |
| --- | --- |
| summary / 原索引 | 25 步均有起止时间与退出码，stop/collect 成功；301 个原文件逐 SHA 一致 |
| 构建 | 14 包 PASS |
| C++ | 358 项 / 20 个程序 PASS，318 核心 + 40 Action；逐项测试身份匹配源码 |
| Python / Mock E2E / ROS 接线 | 269 / 15 / 6 PASS |
| 旧固定 cpp-audit | FAIL：预期 16 程序、实际 20；missing/unexpected/duplicate/bad 均空。原交付 Action verifier 补跑 358/20 PASS |
| colcon-test | **FAIL / 5**：实际调用 `unittest -v`，0 tests / NO TESTS RAN |
| 独立 MoveIt Plan→Execute | PASS，status 4 / code 1，208 个不同关节时戳，最大误差 `4.1961936559528105e-05 rad`；move_group 子进程退出 **-11**，control 为 0 |

适配器 `setup.py` 仍没有 pytest `tests_require`；手工运行交付 pytest 入口通过不能覆盖自动收集失败。原 `colcon test-result` 汇总 **652** 包含包装/lint，没有给空收集的适配器提供测试证明。保留全部失败输出，没有改上游测试、门限或构建配置。

旧 Python Task 的尽早／延迟／取消场景仍为 ABORTED / **220、510、520**，完成数均为 0；Cancel 被接受后仍未获得子任务停稳证明。PickPlace 的 ActionClient 绑定退出及 B03/B05/B06、Safety 清理问题保留。全空间 rosdep 的 ament_python 定义、驱动 docker.io / controllers-test-nodes 依赖与驱动测试 **1104 条 / 279 failures / 259 skipped** 尚未解决；驱动汇总包含 lint/包装，不是纯功能测试数量。

## 安装程序的真实 ROS 进程验收

先核对安装 package.xml 和 adapter 三个 Python 文件与当前源码字节一致，再运行原交付 `python3 -m pytest -q src/mtc_vision_adapter/test`，得到 **57 PASS**，本地耗时 10.26 秒。构成为 45 输入安全、3 本地 TF Buffer、5 mock 清理、4 真实安装进程；四个进程场景已经包含在 57 内，不重复计数。

| 场景 | ROS domain | 收到数组 | 信号 | 发布器退出 |
| --- | ---: | --- | --- | ---: |
| synthetic 自然完成 | 191 | 4/4，长度 0/4/4/4 | 无 | 0 |
| replay 标签自然完成 | 192 | 4/4，长度 0/4/4/4 | 无 | 0 |
| synthetic 中途退出 | 193 | 2/4，长度 0/4 | SIGINT | 0 |
| replay 标签中途退出 | 194 | 2/4，长度 0/4 | SIGINT | 0 |

本次交付验证器直接执行安装后的 `replay_publisher`，没有前次替换 `Node.create_publisher` 的插桩。四例使用周期 **0.5 秒**和发布器真实新增的 `wait_for_subscriber_s=15`。只增加容器内部 `/candidate/install -> /candidate-install` 别名，满足验证器固定安装路径；没有修改 tracked 源文件或使用宿主挂载。

自然完成两例均观察到 `replay complete`，未发信号；中途两例均发 SIGINT，没有完成日志，只认定两帧被接收。逐字段校验颜色、ID、header、历史采集时戳、null→NaN 和 false-ring；收到数据的独立 helper 对离线模式返回 REPLAY_NOT_MOTION_INPUT，假设 live 调用返回 EMPTY 或 RING_INVALID。它们不是实际 FSM 拒绝日志。

四例的 QoS 日志均报告创建配置 **RELIABLE / KEEP_LAST(5) / VOLATILE**，图上消息类型和兼容性 OK。但首次图快照四例均为 `_NODE_NAME_UNKNOWN_`、history UNKNOWN / depth 0；不能据此声称图已识别命名节点或验证深度 5。来源身份依靠固定安装代码、直接启动的可执行文件和隔离进程检查；测试末尾节点检查与最终 docker top/进程退出分别保存，不把图占位字段作为完整就绪证明。

replay 数据只是相同四帧合成 fixture 改外层 mode、timestamp_source，消息和采集时戳保持，没有实际录制或相机。最终 `wait_for_all_acked` 有 2 秒上限，本次成功路径经过该调用；RELIABLE 中间件确认不代表应用/FSM 已接受，真实最终 ACK 超时分支没有做故障注入。

## 默认入口与无订阅者边界

独立 domain 152 只建立图观察节点、不建订阅器，直接运行同一安装程序：

| 配置 | 实际观察 | 判定 |
| --- | --- | --- |
| 默认 wait=0、period=1 | 四条 publish 日志，约 4.52 秒自然 exit 0，完成日志存在 | 默认自然退出通过；没有接收方，不声称送达 |
| wait=2、period=0.25 | 约 2.41 秒 exit 1，`TimeoutError: no matched replay subscriber`，零 publish、无完成日志 | 明确失败的负例通过；原 traceback 保留 |

两例没有发送清理信号、没有 replay 节点残留或重复 shutdown。可选等待现已在正式发布器内实现，并由匹配订阅者的四例及无订阅者负例验证；**默认值仍是 0**，旧 ENV-VISION-ADAPTER-20261012 中的默认 1/4 发现时序失败不能据可选配置通过而关闭，也未建立多次可靠性统计。

## 累计视觉源码与未交付的私有入口

复用此前缓存、逐 SHA 核对的 **23 个依赖轮子**，复制进无网络容器；独立 venv 保留系统 setuptools 68.1.2，不安装缓存中的旧失败选择 80.9.0。editable 安装和 pip check 通过，Python 3.12.3 / numpy 1.26.4 / scipy 1.11.4 / opencv 4.8.1 / PyYAML 6.0.2 / matplotlib 3.8.4 / pytest 8.3.5 的环境记录已冻结。

`vision_core/tests` 为 **80 PASS / 1 SKIP**：前次 62 项通过保留，新增 6 fast confirmation、7 RGB-D offline、5 interface 测试。旧 27 项 adapter-core 测试已包含其中；私有 22 帧证据仍缺失并跳过，未冒充原私有 215 项套件。

新增计算优化的平面高度在合成数据下与原公式数值等价；视觉确认检查颜色、轮廓、稳定桌面证据与名义 CAD 支撑范围，过期 CAD 候选清空、诊断时间/坐标字段测试通过。这里的 `CONFIRMED_OBJECT` 仍只是视觉假设，body_pose_valid / ring_pose_valid 保持 false，ROS 时钟标记 NOT_MAPPED；不代表物体身份真值、可抓取姿态、正式规则或实测尺寸。

新增两条入口也原样尝试：

```bash
/review-venv/bin/python vision_core/scripts/benchmark_vision_v41.py --phase after
/review-venv/bin/python vision_core/scripts/check_fast_v42.py --phase acceptance-dc76a0b
```

两者均 **exit 1 / BLOCKED**，首先在创建 `outputs/live_rgbd_integration/v41` 或 `v42` 时因父目录不存在而失败，尚未处理任何帧。检查同时确认私有 RGB-D 记录、先前 audit/paired/before 文件、CAD geometry 和 STEP 资产缺失。仅补空目录也不能完成这些入口，本次没有伪造输入、补造基准或据公开测试宣称 V4.1 性能提升、V4.2 私有真实数据验收通过。两份完整 traceback 和八项输入清单保留。

## 未通过范围与交接

| 负责人 | 本地留存的待办 |
| --- | --- |
| 孙浩然，感知 | colcon pytest 登记；可选等待参数的 SOP、默认送达可靠性；进程验证器稳定采样节点身份；私有 benchmark 输入和实时发布链 |
| 孙嘉明，FSM/Action/Cancel | 实际视觉订阅及来源/时效/有限数/可信 TF 消费门禁；旧 Action/Cancel 停稳链和 B03/B05/B06，内核由其负责 |
| 韩明赫，标定 | 实测可信 TF、采集时刻与 ROS/Core 时钟、实际位姿转换 |
| 系统集成与验收 | 保留失败及分支边界，继续跟踪默认入口、退出与隔离；按截止后授权推进下一轮集成 |

C++ Task 仍构造 MockPerception；C++/Python Task 均没有接入该话题及新 helper。旧 true-ring/NaN/旧时间静态反例保留在 ENV-VISION-SAFETY-20261012，本次因对应源码未变未再执行，更没有发布反例或发送 Goal。独立回放、独立 MoveIt、完整 FSM 与实机是不同范围；D435i/USB、跨机通信、真实四色精度、XYZ/Yaw/提环、工具/相机/桌面标定、SDK 许可/厂商校验值与 NUC 仍未验收。

以上是本地问题单，没有代发外部消息或接管内核修复。USER-HW-20261012、USER-HW-20261012-02 的 C++ Mock Bringup／Web UI 同轮交付仍处于 SCHEDULED，08:00 前未执行；定时任务文件未改、没有投递尝试。届时先完成监测尾部事件再实施和推送，此事件本身没有提交或推送。

## 证据、清理与回执

冻结集 [vision-replay-20261012](experiments/vision-replay-20261012/protocol.md) 包含 **486 文件 / 5,148,722 bytes**：全部原固定失败、实际累计差异与源码、57/80 测试 XML、四进程消息与日志、两项无订阅者检查、私有入口失败、依赖版本/许可/哈希、隔离/清理及 complete 前回执。[inputs](experiments/vision-replay-20261012/inputs.json)、[summary](experiments/vision-replay-20261012/summary.json)、[index](experiments/vision-replay-20261012/index.json) 按事实链登记，index 不含自身。

`index_sha256 = b16775413156877bc22ae8b68e9db750bc1776398f281a4abfc5dc30a6946234`

原始运行：`outputs/moveit-watch-20261011/runs/sha-dc76a0bf0a43f9110f3d24cfa38a2b3478f48dcd/`；补跑、分析与最终回执：`outputs/vision-replay-acceptance-20261012-dc76a0b/`。源码 bundle SHA 为 `a6c2e4ba66b31203c0b27c1c6af9c65454a09ce736ef94e076764278d1102397`；bundle、镜像和轮子保留本机，不入冻结集。

原及补跑容器均停止、无 OOM；补跑停止前 docker top 只有 keeper，tracked source diff 为空。keeper 的 137 与 ROS 发布器实际 exit 0、负例/缺数据 exit 1 分开记录。原 runner 不存在，没有残留复现进程；完整原始失败和此前冻结集/签收报告不改。同步 manifest、报告、README、open-questions 与 derived_files，核验后登记 complete；最终回执留 raw，不反写冻结文件。

使用 OpenAI Codex 协助源码/日志核验、原交付入口隔离复现、观察/分析/清理脚本及事实链登记；未修改上游视觉算法或 FSM/Action/Cancel 内核。根 MIT、adapter/Action 的 Apache-2.0 声明差异及 SDK/模型/私有资产许可缺口保留，不重新授权。原监测保持 60 秒轮询及北京时间 08:00 截止。
