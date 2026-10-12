# 视觉安全校验、TF 与回放清理验收（2026-10-12）

**结论：部分通过。新增 53 项测试、公开视觉 62 项回归及三次隔离 ROS 回放通过；发布器 SIGINT 清理已在本环境复现修复。默认 colcon 仍未收集新测试，安全 helper 尚未接入 FSM，实时视觉与完整任务未验收。** 上游来源 TEAMMATE-VISIONSAFETY-20261012，本地观测 ENV-VISION-SAFETY-20261012。

## 提交范围与签收

本次 SHA `e53c09fba0ac6082d97d53676413d6e285140dc1`，父版本 `0e329f10e6f607c9c417a54ae60d290b8e2395b5`，观察到 `feature/perception-adapter` / PR #5 head。一个提交修改 8 个适配器文件：README、core、publisher、package.xml 和 4 个测试/验证脚本。其他源码与父版本逐路径相同，既有 IDL、FSM、Action、vision_core 算法未改。

这是此前视觉分支（TEAMMATE-PERCEPTION-20261012；ENV-VISION-ADAPTER-20261012）的增量，没有包含其他分支的 Planner、FJT 端口或标定交付。本次 358 项 C++ 与轨迹分支的 463 项不属于同一源码范围。本项目正式锁定仍为 `1d940f7c5f12561fed6641457c0b4b630a282b05`，没有合并或推进基线。

按 USER-HW-20261011-08、USER-HW-20261011-09 授权，固定运行于上海时间 **02:47:06—02:51:03** 完成，summary 状态 `COMPLETED_WITH_FAILURES`。主对话 ack 返回 `CLAIMED`，已输出 `MOVEIT_WAKE_ACK_12cbb8a4e6632f439448c4eb2c8450f5`；一次投递至持久化 ACK **5.556253 秒**。未调用 queue 或启动另一监测。

确认原 runner PID 39773 和全部旧任务容器停止后，从停止容器建立独立补跑快照。保持无网络、设备、挂载、发布端口，2 CPU / 4 GiB / 512 PID，cap-drop ALL / no-new-privileges；原容器未重启，原始失败未覆盖。补跑只涉及视觉校验与消息传递，没有打开相机、启动 FSM 或发送 Action Goal。

## 固定运行与新增测试

| 检查 | 本次结果与计数边界 |
| --- | --- |
| 原 summary / 文件 | 25 步完整、stop/collect 成功，301 个原索引文件逐 SHA 核对一致 |
| 构建 | 14 包 PASS |
| C++ | 358 项 / 20 个程序 PASS，318 核心 + 40 Action；XML 测试身份逐项核对源码 |
| 既有 Python / Mock E2E / ROS 接线回归 | 269 / 15 / 6 PASS |
| 旧固定 C++ 审计 | FAIL：预期 16 个程序、实际 20；missing/unexpected/duplicate/bad 均空。交付 Action verifier 补跑 358/20 PASS |
| 默认 colcon-test | **FAIL / 5**：实际执行 `/usr/bin/python3 -m unittest -v`，0 tests / NO TESTS RAN |
| 新交付 pytest 入口 | **53 PASS**：45 个输入安全检查、3 个本地 TF Buffer、5 个清理检查 |
| 公开 vision_core 回归 | **62 PASS / 1 SKIP**；跳过未交付的私有离线证据 |

`package.xml` 新增了 pytest/TF 测试依赖，但 `setup.py` 未登记 pytest `tests_require`，本环境 colcon 仍选择 unittest。原 `colcon test-result` 汇总为 **652**，含包装/lint，且不包含空收集的新包，不能替代这项失败。手动 pytest 通过与默认收集修复分开验收。

53 项新测试使用原 Jazzy 环境执行；公开视觉目录复用先前事件本地缓存的依赖轮子，逐 SHA 核对后复制进无网络容器。独立 venv 使用系统 setuptools **68.1.2**、pytest **8.3.5**；两条 editable 安装和 `pip check` 通过，没有重复下载、修改宿主 Python 或升级到此前失败的 setuptools 80.9.0。Python 3.12.3、numpy 1.26.4、scipy 1.11.4、opencv 4.8.1、PyYAML 6.0.2、matplotlib 3.8.4 的观测记录已冻结。

旧 27 项适配器测试已包含在 62 项公开测试内，不重复相加。私有 22 帧数据、原私有 215 项套件和真实相机仍未复现；本次不重复无变化的 C++ 独立场景、UBSan、规划或轨迹端口入口。

## 安全 helper 与 TF 的实际边界

`motion_rejection` 新增明确的 trusted_frames、target_frame 和 tf_validator 输入；缺少配置时拒绝。它要求时间字段合法、年龄有限且在界内、ring flag 严格为布尔 true、两个 PoseStamped 头一致、位置/四元数完整且有限、四元数归一化，并把**采集时间戳**传给回调。未知帧、回调缺失/抛异常/返回非严格 True 均拒绝；同帧也不能省略验证。

三项 TF 测试使用真实 tf2 本地内存 Buffer：无 TF 拒绝；采集时刻变换存在时允许；只有较新的变换、不能覆盖历史采集时刻时拒绝。这证明局部契约，未启动真实 TF listener、没有测量相机外参。回调仍由调用者实现，helper 信任其严格 True 返回值，本身不变换位姿，也未建立运行时可信标定与时钟来源。

实际 C++ Task 仍构造 `MockPerception`，Python Task 未实现该话题订阅；两者均未调用新 helper。ROS IDL 仍不含 JSON 外层的 mode/body_pose_valid 等来源字段。本次实际回放候选 false-ring/NaN 被旧 Python 静态谓词拒绝；**只在观察进程内把一个候选改为 true-ring、保留 NaN/旧时间戳，该谓词仍返回 true**。反例没有发布或转为 Goal，不能描述为机器人执行了动作，也不能因独立 helper 通过就宣布完整消费门禁修复。

## 三次原生 ROS 回放

| 入口 | 默认发布器 | 上游验证脚本：synthetic | 上游验证脚本：replay 标签 |
| --- | --- | --- | --- |
| 隔离域 / 周期 | 148 / 1 秒 | 149 / 2 秒 | 150 / 2 秒 |
| 启动方式 | 先起订阅器，`ros2 run` 原安装入口，无插桩等待 | 脚本 monkeypatch 创建 publisher，等待订阅匹配后启动 timer | 同左 |
| 原生消息接收 | 4/4，时间/帧/颜色/ID/null→NaN 核对通过 | 4/4，全帧精确核对通过 | 4/4，全帧精确核对通过 |
| 完成日志 | 已观察 | 已观察 | 已观察 |
| SIGINT | exit 0，无升级终止 | exit 0，无升级终止 | exit 0，无升级终止 |
| 清理证据 | 补跑最终进程清单只有 keeper | 验证脚本确认 replay 节点消失、订阅器清理 | 同左 |

两次上游验证脚本保持源码原样，仅在容器内加入 `/candidate/install -> /candidate-install` 路径别名，适配它写死的工作空间安装布局。其注入逻辑等待订阅匹配上限 20 秒，读取**实际创建 publisher 的 qos_profile**，确认 RELIABLE / KEEP_LAST / depth 5 / VOLATILE。图发现接口另外确认兼容性 OK、RELIABLE / VOLATILE；图上仍是 history UNKNOWN / depth 0，不能用图字段证明队列深度。

两种数据都来自原四帧合成 fixture，replay 版本只改外层 mode，消息内容与旧采集时间戳不变；不是新增真实录制。收到数组长度为 0/4/4/4，独立 helper 对离线模式均返回 REPLAY_NOT_MOTION_INPUT；假设 live 调用分别得到 EMPTY、RING_INVALID、RING_INVALID、RING_INVALID。没有合法运动输入或执行请求。

默认入口本次也收齐四帧、晚加入订阅者在 1.5 秒观察窗内无历史消息，空文件与 live 标记两个负输入均在发布前拒绝、exit 1。**默认发布器没有新增等待订阅者的屏障**；本次单次 4/4 不关闭 ENV-VISION-ADAPTER-20261012 中默认 1/4 的发现时序问题，也不作成功率推断。验证脚本的等待不能转写为发布器默认修复。

三次成功回放均在完成日志后以 SIGINT 退出，未出现原 `rcl_shutdown already called`。完成逻辑只是取消 timer，发布器仍 spin，退出依赖外部信号；本次证明的是受控清理，不是进程自然结束。5 项 mock 清理测试与这三次真实 rclpy 进程证据分列。

## 原有失败与本地交接

原固定运行的旧 Python Task 三场景仍为 ABORTED / **220、510、520**，完成 0；Cancel 返回接受但未取得子任务停稳证明。PickPlace 仍在 `ExecuteJointMove.create_client` 退出，B03/B05/B06 未关闭；Safety 的重复 shutdown 也未被本次视觉发布器修复覆盖。

全空间 rosdep 缺 ament_python 定义；驱动缺 docker.io 与 ros-jazzy-ros2-controllers-test-nodes；驱动测试汇总 1104 条 / 279 failures / 259 skipped，含 lint/包装，仍失败。固定独立 MoveIt Plan→Execute PASS（status 4 / code 1），206 个不同关节时间戳、最大误差 `9.145290479063988e-05 rad`；move_group 子进程退出 **-11**，控制 launch 为 0、无升级终止。此独立路径未连接视觉或完整 FSM。

| 本地交接对象 | 保留的待办 |
| --- | --- |
| 孙浩然，感知（SPRINT-PLAN-20261011 §04、§07–08） | pytest 自动登记、默认回放发现就绪、实时发布入口、来源标记与真实数据/资产 |
| 孙嘉明，FSM/Action/Cancel（§02、§07） | 实际视觉消费者与来源/时效/有限数/TF 门禁、静态谓词反例、旧 B03/B05/B06 与取消停稳链 |
| 韩明赫，标定（§05、§07） | 可信实测 TF、采集时刻与 ROS/Core 时钟契约、坐标转换 |
| 系统集成与验收（§06、§08） | 保留默认失败和各分支边界，核对清理、依赖、复现与证据 |

以上仅落在本地问题记录，没有代发外部消息或接管内核修复。真实四色准确率、物理 ID、XYZ/Yaw/提环、相机/TCP/工具/桌面标定、完整 FSM→Planner→FJT→工具/Cancel、SDK 许可/厂商校验值、NUC 与实机均未验收。

## 冻结证据与监测

冻结集为 [vision-safety-20261012](experiments/vision-safety-20261012/protocol.md)：**463 文件**，保留全部原固定失败、新测试 XML、原生消息、日志、实际源文件、依赖版本/许可/哈希、隔离/清理与签收状态；清单不含自身。[inputs](experiments/vision-safety-20261012/inputs.json)、[summary](experiments/vision-safety-20261012/summary.json)、[index](experiments/vision-safety-20261012/index.json) 已登记于 materials/manifest.json。

`index_sha256 = c7088dbe257a6a45a4be64600ce5a39ad2d43492b125aaacc7d70912c2362fc0`

原始目录：`outputs/moveit-watch-20261011/runs/sha-e53c09fba0ac6082d97d53676413d6e285140dc1/`；补跑与最终回执：`outputs/vision-safety-acceptance-20261012-e53c09f/`。源码 bundle SHA 为 `560de028a56e74092d7c33da9307d13fd2f833d8ceb53b5d96467bdc3d7a68d5`，bundle、镜像与轮子保留在原始目录/本机，不入冻结集。

原/补跑容器均停止、无 OOM；原 runner 不存在，补跑停止前只有 keeper。keeper 137 与已验证 exit 0 的 ROS 发布器分开记录。上游 tracked source diff 为空，容器内 editable 元数据与安装路径别名另记。先前冻结集和签收报告保持原状；同步 README、open-questions、对应计划、manifest 与 derived_files 后登记 complete，最终回执存原始事件目录，不回写冻结集。事件完成不代表全部系统验收通过。

原监测继续使用固定主会话 `01a12a25-b5c5-7b23-98b7-1cf673d68838`，60 秒轮询，上海时间 10 月 12 日 08:00 截止；相关新 SHA 经串行复现后再唤醒，无更新仅脚本轮询。

使用 OpenAI Codex 协助源码与证据核对、隔离复现、观察/分析/清理脚本和事实链登记；未修改上游视觉算法或 FSM/Action/Cancel 内核。根 MIT、adapter/Action 的 Apache-2.0 声明差异及 SDK/模型/私有资产许可缺口保留，不重新授权。
