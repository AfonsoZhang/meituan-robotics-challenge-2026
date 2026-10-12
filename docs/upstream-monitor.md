# 今晚上游监测与后续复现（2026-10-11）

**最终状态（2026-10-12 08:00 后核验）：** 原 watcher 于08:00:00.267972自然退出，EXPIRED，pending/active/main_review均为空；14个实际事件的报告与complete签名一致，旧runner/复现容器已停止。之后才执行新的C++ Mock/Web同轮任务，无重复监测或新queue。收尾证据及部分通过/C1边界见[同轮验收](cpp-mock-webui-acceptance.md)（ENV-CPP-MOCK-WEBUI-20261012）。下文保留设置和事件发生时的记录。

用户告知“孙嘉明会在今晚补充MoveIt部分内容，做好实时监测，他更新之后，跑剩下的复现”（USER-HW-20261011-08，用户会话）。这是交付预期与执行授权，尚不能据此认定代码已上传或验收通过，也不改写 SPRINT-PLAN-20261011 §01、§06–07 的整体分工。

## 监测安排

本机监测 `F1u0rite/meituan_challenge_ws` 的全部分支与 PR head，每轮结束后间隔 60 秒再次拉取，只读 GitHub。监测窗口为本次启动至 **2026-10-12 08:00（上海时间）**，到期停止接收新更新，已经排队的复现完成收尾后结束；若环境仍未就绪，则保留队列并退出。首次快照的 `main` 仍为 `1d940f7c5f12561fed6641457c0b4b630a282b05`；PR #2 的 `1d3dccf…` 与旧分支纳入已知历史，不误判成今晚的新交付。

运行状态与变更队列在 `outputs/moveit-watch-20261011/state.json`，每次观测保存 ref、前后 SHA、提交信息、改动路径和补丁。代码/配置/测试或 MoveIt/接线相关文档更新进入复现队列；同一 SHA 只执行一次，失败留档，不反复重试。分支未合并也可以单独验收；正式锁定文件保持原有基线。

后台进程独立于聊天窗口运行，依赖当前 WSL 与 Docker 持续可用；电脑关机、休眠或 WSL 停止期间不能监测。用户随后明确授权接入自动唤醒本主对话（USER-HW-20261011-09），现已启用下述队列与回执机制；没有配置 GitHub/邮件通知。运行状态须以实时文件和进程核验为准，本文的设置记录不等于服务永远在线。

```bash
python3 robot/watch_upstream.py status outputs/moveit-watch-20261011/config.json
```

停止时向 `state.json` 所记 PID 发送 SIGTERM；它停止接收更新，并等待已启动的隔离复现保存证据和退出。重新启动须使用同一配置及其 `harness_directory` 下的固定工具副本；中断的运行先按完整参数识别本任务进程并清理带归属标签的容器，记录为中断后唤醒分析，不自动重复执行。

## 自动唤醒、回执与串行验收

新增 `robot/wake_main.py`，使用本机 Codex CLI 0.162.1 已支持的 `codex queue`。独立子进程清除 `CODEX_THREAD_ID`、`CODEX_SESSION_ID`，固定投递到主对话 `01a12a25-b5c5-7b23-98b7-1cf673d68838`，连接 `unix:///home/afonso/.codex/app-server-control/app-server-control.sock`。该通道由 USER-HW-20261011-09 明确授权，不创建新会话、不代发队友消息。

新相关 SHA → 固定隔离复现 → 保存终态与唤醒队列 → 主对话领取、分析并补跑 → 登记证据及完成回执 → 处理下一 SHA。无更新时只有 Git 轮询，不调用模型。固定检查的成功、失败、启动错误、超时或进程中断都会进入同一条分析路径；整体运行上限为 5,400 秒，TERM 清理宽限 180 秒，必要时终止本任务进程组并停止其带归属标签的容器。

唤醒消息包含完整 SHA、比较起点、变更路径、实际结果、失败阶段，以及事件 JSON、原始 patch、summary 与日志的绝对路径。主对话须先领取事件，再阅读实际变更，按交付入口补跑固定脚本未覆盖的复现，区分模块失败与环境失败，并按项目四处同步约定冻结/登记证据。FSM/Action/Cancel 内核问题保留复现证据交孙嘉明，工作范围仍为系统集成与验收。

每个 SHA 使用固定事件键 `sha-<完整SHA>`；落盘事件、运行意图、终态、发送尝试和回执均持久化，JSON 使用原子替换及 fsync。同一输出目录由文件锁限制为一个监测进程。程序重启后恢复待发送或待验收状态，不重复执行已启动的 SHA。固定脚本执行完毕后，主对话的验收门禁持续占用串行位置，期间只发现、排队后续 SHA，不启动第二项复现。

传输最多尝试三次，失败后分别等待 30、120 秒；单次 CLI 上限 30 秒。返回成功只表示消息已受理，不能当作主对话已回执，且不会自动重发已受理消息。超时或中断造成投递结果不确定时，重试仍使用同一令牌；领取操作只会有一次返回 `CLAIMED`，重复为 `ALREADY_ACKNOWLEDGED` / `ALREADY_COMPLETE`，不重复开展工作或再次唤醒。重试耗尽、主对话未回执或验收未完成时保留门禁和队列，不放行下一次复现，也不循环唤醒。

主对话按照消息中的完整命令执行 `ack`，随后输出 `MOVEIT_WAKE_ACK_<令牌>`。完成实际分析、必要补跑与证据整理后执行同一脚本的 `complete`，附 `--report <真实报告>`、`--outcome <结论>`；它检查主任务不在运行、固定复现容器已停止，再保存报告路径和 SHA-256。主对话自己新增的检查也须完成清理后才能提交完成回执。验收结论可以包含 FAIL 或未完成项，回执完成不等于功能通过。

| 本机路径（相对 `outputs/moveit-watch-20261011/`） | 用途 |
| --- | --- |
| `state.json`、`config.json` | 实时 PID、运行状态、排队 SHA、主对话门禁与配置 |
| `monitor-wake-v1.log` | 新监测进程日志 |
| `events/sha-<SHA>.json`、`.patch` | 原始提交与变更范围 |
| `runs/sha-<SHA>/`、同级 `.log` / `.completion.json` | 固定复现的原始证据与终态 |
| `wake/sha-<SHA>/job.json` | 持久化发送状态及有限重试记录 |
| `wake/sha-<SHA>/message.txt`、`attempt-N.log` | 实际消息与 CLI 返回 |
| `wake/sha-<SHA>/receipt.json` | 主对话领取/完成时间、令牌、报告路径及哈希 |
| `harness-wake-v1/`、`environment-ready-wake-v1.json` | 固定工具及哈希、原有镜像与隔离配置 |

到期停止 Git 更新发现，已排队任务和已投递的主对话验收继续收尾；发送耗尽则保留未处理队列。若人工停止，后续使用同一配置恢复，保留原始事件和回执文件。不要删掉状态或令牌来触发重跑。

自动唤醒的切换与端到端检查单独登记为 ENV-UPSTREAM-WAKE-20261011，详见[唤醒接入验收](upstream-wake.md)。原 ENV-UPSTREAM-WATCH-20261011 与所有失败证据不改写。

## 更新后的自动复现

每个新提交使用独立容器、源代码快照和日志目录。容器无网络、无主机/设备挂载、无发布端口，限制为 2 CPU / 4 GiB；不复用正在运行的 ROS 图。所有阶段分别登记结果，任一步采集成功不代表功能通过。

| 检查 | 执行与判定 |
| --- | --- |
| 交付、依赖和构建 | 记录实际 SHA/差异/launch 清单，检查 rosdep，完整构建候选源码；超时停止本轮容器，保留错误 |
| 离线回归 | colcon 已注册测试、已有 C++ 审计入口及纯 Python Mock E2E；实际用例数以新提交的结果为准 |
| 实际 Python ROS Mock | 原交付的 `mock_bringup`，分别检查尽早 Goal、延迟 7 秒 Goal 与 Cancel；保存逐节点服务器、Feedback/Result 和退出异常，复核 B03/B05/B06；不冒充新 C++ 外壳 |
| 独立驱动依赖与自动测试 | 已锁定的五包 rosdep、colcon test / test-result；没有测试用例时据实记录，不把空测试集写成覆盖通过 |
| 独立 MoveIt | 固定 S3 模型，静态与运行时双重确认 GenericSystem、两控制器 active、唯一轨迹服务器；通过 MoveIt 服务规划，再经 MoveIt ExecuteTrajectory 执行完整轨迹；核对终态、六关节反馈和 TF |
| MoveIt 退出 | 单独记录 SIGINT、是否升级终止、子进程退出错误；Plan → Execute 成功与干净退出分开判定 |

规划/执行探针使用 ROS2-MOVEIT-MSGS-20261011（2026-10-11 查阅）的 [GetMotionPlan](https://github.com/moveit/moveit_msgs/blob/ros2/srv/GetMotionPlan.srv) 与 [ExecuteTrajectory](https://github.com/moveit/moveit_msgs/blob/ros2/action/ExecuteTrajectory.action)，并已对照容器内 2.6.0 的实际接口。

独立 MoveIt 使用 TEAMMATE-SDK-20261011 的驱动 `53aab837…`、模型 `47fa5e02…` 和已交付 Fake Xacro 修复。即使新 FSM 构建失败，仍可单独复现这条已知链路，但不会把它算成新 FSM 已接通。新交付若改变驱动锁定或引入新的完整 FSM 启动入口，需要按新 SOP 对齐专门的集成验收；本轮通用自动入口不猜测未知 launch 参数，不自动声称完整闭环通过。

每轮报告位于 `outputs/moveit-watch-20261011/runs/sha-<完整SHA>/summary.json`（旧记录保留原命名），同目录保留命令、退出码、日志、ROS 结果和 SHA-256 索引。运行产物先留在忽略目录，随后由被唤醒的主对话实际复核并登记新实验事实与冻结证据；固定脚本不自行改写文档或旧实验。

仍保留的边界：完整新 C++ FSM / Action / MoveIt / 感知 / 工具闭环、TSan、SDK 许可与厂商校验值、NUC 与实机均不能由通用自动检查替代。FSM 状态转换与 Cancel 内核仍由孙嘉明负责，未扩大到自动修复、合并或实体操作。

## 本次设置核验

设置与检查记录为 ENV-UPSTREAM-WATCH-20261011，见[冻结索引](experiments/upstream-watch-20261011/index.json)。新增 9 项临时 Git 仓库测试覆盖 feature 分支、同 SHA 多 ref/重复轮询、旧提交、无关文档、强推、分支删除、重复初始化、到期行为，以及实际后台轮询向受控测试 runner 派发；既有 robot 7 项测试一并通过，共 16 项。以下用已有 PR 候选 `1d3dccf23c53d299d457564daeb6438190ea2d77` 验证自动流程，不作为孙嘉明今晚新交付的验收结果。


| 已有版本的资格检查 | 结果 |
| --- | --- |
| 新隔离工作空间构建 | 12 包通过；保留完整 Git 历史供 C++ 基线审计 |
| C++ / Python / E2E / ROS 回归 | 分别 318 / 269 / 15 / 6 项通过，不与历史复跑累计 |
| FSM manifest 依赖 | `ament_python` 无 rosdep 定义，检查退出 2；构建成功不能替代依赖声明完整性 |
| XML lint 环境 | 初次无网络容器无法下载 schema；缓存 ROS2-PACKAGE-SCHEMA-20261011 的官方固定 XSD 并使用 XML catalog 后，原失败的 `mtc_interfaces/package.xml` 校验通过，未关闭校验或修改源码 |
| 真实 Python ROS Mock | 3 个场景均 FAIL；尽早 Goal 返回 ABORTED / 220，延迟 Goal 返回 ABORTED / 510；Cancel 已受理但子任务未确认停止，最终 ABORTED / 520；PickPlace 服务器均不可用，B03/B05/B06 未解除 |
| 驱动完整依赖与自动测试 | 缺 `ros-jazzy-ros2-controllers-test-nodes`、`docker.io`；五包 test 已执行，description/msgs 的 lint 有失败。初次 colcon 汇总 1104、失败 281、跳过 259 含包装和生成代码，不能作为功能用例数，也不能记为通过 |
| 独立 MoveIt Plan → Execute | **PASS**；唯一 GenericSystem 与轨迹服务器、控制器、TF 正常；肩关节目标增加 0.05 rad，规划及 MoveIt 执行成功（Action status 4 / MoveIt code 1），最大目标误差 0.0000899766 rad，207 个不同关节时间戳 |
| 独立 MoveIt 退出 | **FAIL**；SIGINT 后 `move_group` 子进程 -11，栈涉及 MoveItCpp / TrajectoryExecutionManager / rclcpp CallbackGroup 析构；launch 本身 0 不代表干净退出。控制节点有清理期错误日志但进程 0，亦保留 |

首次探针导入还触发无 capability 容器的 tar 改属主失败；工具已改用 `--no-same-owner`，不增加容器权限。上述开发失败、网络/schema 失败与真实模块失败分别保留，原有两批 FSM 冻结证据未改动。正式监测使用已核验工具的独立副本与固定镜像，后续工作树编辑不影响本轮任务。

## 首次真实分支交付的主对话补验

`feature/phase2a-cpp-actions@c0f7017…` 在 2026-10-11 23:14（上海时间）进入监测，固定复现后主对话认领并补跑新入口，见[候选验收](cpp-action-acceptance.md)（TEAMMATE-ACTION-20261011；ENV-CPP-ACTION-20261011）。这是 Phase 2A C++ Action Mock，尚未交付 MoveIt 接线。新包构建与 358 C++ / 269 Python / 15 Mock E2E、补充 UBSan 和四组独立进程检查通过；旧 Python、依赖/驱动 lint、独立 MoveIt 退出失败仍保留。固定旧审计要求 16 个可执行文件，交付的新审计已核对实际 20 个 / 358 项；可选 ROS 接线测试文件缺失必须算 NOT RUN。原监测工具与资格检查冻结记录未覆盖，本轮未重启监测或重复 queue。

生成式 AI 披露：使用 OpenAI Codex 编写本机 Git 监测、容器编排和 ROS 验收探针；未修改上游 FSM、驱动或规划算法。上游与第三方依赖沿用 TEAMMATE-FSM-20261011、TEAMMATE-SDK-20261011 的版本和许可说明，未归档 SDK 二进制或重新授权模型。

## PR #2 合并事件

后续 `main@c10f6ed…` 合并了原三项 Python 接线补丁（TEAMMATE-MERGE-20261011）。固定入口已实际运行六项 ROS 回归并通过；主对话补跑新 C++ 身份核验、四组独立程序及一次独立 MoveIt 退出复核，见[合并后验收](wiring-merge-acceptance.md)（ENV-WIRING-MERGE-20261011）。普通构建/回归通过，旧 Python Task 三场景仍失败；独立 MoveIt 两次规划执行通过而退出失败，控制器 -11 一次出现、一次未再现。没有改动当前固定监测工具、另启监测或重复 queue；原失败与每次 SHA 的门禁状态分别保存。

## 独立规划分支事件（10 月 11—12 日）

`feature/moveit-planner@fcdd8ea…` 相对 `1d940f7…` 增加规划包与 53 文件，固定复现后主对话按令牌认领（TEAMMATE-PLANNER-20261011；ENV-PLANNER-20261012）。固定脚本覆盖 13 包 / 347 C++（含新规划 29）/ 269 Python / 15 Mock E2E，但不调用新规划工具，故主对话在同限制独立快照内补跑交付 SOP。默认固定姿态通过、V1/V2 均 TF 失败；一次仅延长 TF 等待的诊断中 V2 七段规划通过、V1 超看门狗拒绝，两轮 MoveIt 退出均 -11。全部默认失败与诊断分开保存，正式监测工具未变，也未另发 queue。

[规划验收](planner-acceptance.md)保存真实变更、轨迹审计、450 文件冻结索引和本地交接；原 runner/容器及补跑容器清理后、来源登记结束才 complete 放行下一 SHA。此分支不含已验过的 C++ Action / PR #2，不把其他分支结果混入，也不把七段规划当完整 FSM/FJT/实机。监测原截止时间保持 10 月 12 日 08:00。

## Phase 2A 交接文档事件（10 月 12 日）

`main@a04ac68…` 只改两份 README（TEAMMATE-HANDOFF-20261011），既有监测按相关文档规则完成一次固定复现，随后主对话认领。358 C++ / 269 Python / 15 Mock E2E / 6 ROS 回归通过；补跑文档指向的新审计和只读 Node/Action/QoS 检查。原样与一次有限诊断均有图发现失败，三个 Action 在诊断后续观测中各有唯一服务器、反馈 QoS 匹配，但不能关闭短时查询缺口；六次 C++ 程序正常退出。原依赖、Python、独立 MoveIt 退出失败保持原记录。

[交接文档验收](cpp-handoff-acceptance.md)（ENV-HANDOFF-20261012）归档 418 文件、源代码不变证明和清理，完成事实同步才提交 complete。此次没有新增生产 Bringup、重启监测、额外 queue 或修复内核；上游交接安排作为数据保留。原 60 秒轮询及 08:00 截止设置不变。

## 规划分支同步主线事件

`feature/moveit-planner` 与 PR #3 head 更新到 `4a1a816…`，双父提交为规划 `fcdd8ea…` 和主线 `a04ac68…`（TEAMMATE-INTEGRATION-20261012）。本次自动 14 包 / 387 C++ / 269 Python / 15 Mock E2E / 6 ROS 通过，旧审计仍因程序数不符失败；主对话约 5.69 秒收到持久化 ACK，再在同限制独立快照补跑交付 verifier、两包依赖/安装身份、独立 Action 四场景和默认规划 SOP。

ENV-PLANNER-MERGE-20261012 的四场景 40 项检查与固定姿态规划通过，默认 V1 超 24 秒预算、V2 TF 不可用；原 Python/依赖/驱动 lint 与两次 MoveIt 退出 -11 保留。源码为两父提交的原模块组合，真实 Action/Planner/FJT 尚未接线；未重复前次 TF/CLI 等待诊断、改算法、另发 queue、启动监测或推进基线。

[合并版本验收](planner-merge-acceptance.md)登记 486 文件及 index SHA、两容器停止和四处事实同步。完成回执用于释放下一 SHA，不表示所有功能通过。既有 60 秒轮询、10 月 12 日 08:00 截止与固定主会话设置保持不变。

## 场景、载荷与起点分支事件

`feature/planning-scene-start-v1@30e3c6e…` 相对监测基线 105 文件、相对上次验收仅 45 个规划/文档增量（TEAMMATE-SCENE-20261012）。原固定 25 步完整，14 包 / 393 C++ / 269 Python / 15 Mock E2E / 6 ROS 通过；一次 queue 后约 5.72 秒收到持久化 ACK。主对话在同隔离限制下串行补验新参数拒绝入口、默认规划 SOP 和一次 5 秒 TF 诊断。

ENV-PLANNER-SCENE-20261012 记录默认场景初始化失败、诊断 V2 七段与碰撞负例通过、V1 180.415 秒超预算且未复现上游约 40 秒；MoveIt 退出仍 -11。新起点/重规划未接实际执行。原始失败、306 原始文件哈希、两容器停止及 545 文件冻结索引见[增量报告](planner-scene-acceptance.md)。文档/manifest/derived_files 同步后才 complete；未新发 queue、另启监测、改算法或推进基线。原 60 秒轮询、固定主会话和上海时间 10 月 12 日 08:00 截止保持。

## 视觉适配器分支事件

`feature/perception-adapter@0e329f1…` 新增 111 个视觉/适配器文件，主线父版本 `a04ac68…`，未含规划包（TEAMMATE-PERCEPTION-20261012）。自动 14 包 / 358 C++ / 269 Python / 15 Mock E2E / 6 ROS 通过，新包 colcon 零测试失败；一次投递至持久化 ACK 约 5.92 秒。

ENV-VISION-ADAPTER-20261012 补齐离线依赖后公开视觉 62 通过/1 跳过，16 帧合成；实际默认回放漏前三帧，唯一 5 秒周期诊断收齐四帧，原生 NaN/时间戳/四色核对通过，退出仍异常。真正 FSM 感知消费链未接。原失败、两容器停止、301 原始哈希与 589 文件冻结见[视觉验收](vision-adapter-acceptance.md)；同步事实链后 complete。既有轮询/固定会话/08:00 截止不变，未另发 queue、新启监测或推进基线。

## 规划 PR #3 合入主线事件

`main@f7eaa2c…`（TEAMMATE-PLANNERMAIN-20261012）固定复现后一次投递，主对话 5.93 秒 ACK；实际 Git 树等同前验 4a1a816、相对旧 main 增 53 个原规划文件。25 步完整、305 原始哈希一致，14 包 / 387 C++ / 269 Python / 15 E2E / 6 ROS 通过，新审计 358/20 补跑通过（ENV-PLANNER-MAIN-20261012）。

本次默认 MoveIt 规划成功，执行因内部 FJT 客户端未连接而 ABORTED/-4；单次域 131 额外等待 5 秒的诊断执行通过，退出仍 -11。原默认失败、旧 Python Cancel/520 和诊断分别保存；相同源码的规划 SOP/独立 Action 四场景按历史冻结证据引用。发现并停止本域 ROS daemon，再核对两个容器停止；450 文件冻结见[主线验收](planner-main-acceptance.md)。文档、manifest/derived_files 与原证据校验后 complete；无 queue、新监测、内核修复或基线推进，既有 60 秒轮询/固定会话/上海 08:00 截止不变。

## Phase 2B 整条轨迹端口事件

`feature/phase2b-trajectory-execution@688d80d…`（TEAMMATE-TRAJECTORY-20261012）固定复现后一次投递，主对话5.15秒ACK；累计41路径、相对已验a04ac68仅新增13文件。25步完整、303原始哈希一致。14包/424 C++/269 Python/15 E2E/6 ROS通过，交付审计、外部consumer及独立UBSan424补验通过（ENV-TRAJECTORY-20261012）。

新GenericSystem入口三场景各一次：success返回运行证明丢失/230并锁故障，控制器到达目标也未认作通过；首项失败清理后，只补齐尚未执行的起点不符和取消，两项通过。没有重试success、改时限/源码或接管内核。默认Action仍Mock，直接FSM取消FAULT/520和完整接线缺口交孙嘉明。独立MoveIt本次执行通过、退出仍-11；全部原失败与683文件冻结见[轨迹验收](trajectory-execution-acceptance.md)。核验空域、无残余任务进程/容器并同步事实链后complete；完成状态表示事件审阅结束，非技术全通过。原60秒轮询/固定会话/上海08:00截止不变，没有queue或新监测。

## 标定 / TF 离线交付事件

`feat/calibration-tf-v1@06ab689…`（TEAMMATE-CALIBRATION-20261012）固定复现后一次投递，主对话8.02秒ACK。累计119路径、相对已验f7eaa2c新增38离线文件，既有src树一致；25步完整、305原始哈希一致，14包/387 C++/269 Python/15 E2E/6 ROS通过。新审计358/20、标定54测试/6示例/5反例补验通过（ENV-CALIBRATION-20261012）。

域138一次只读Fake TF核验4条变换和903零关节时戳，无Goal或TF发布；相机/TCP/工位frames仍缺，真实清单8边UNKNOWN。运行适配器未消费标定拒绝和观测时刻TF；旧Python220/510/220、MoveIt执行通过而退出-11保留。清理与分析helper断言及修正均归档，确认源码未改、无残余任务后停止原/补跑容器。532文件冻结见[标定验收](calibration-acceptance.md)，同步事实链后complete，不以事件完成宣称实机或完整FSM通过；监测频率/固定会话/上海08:00截止不变，没有queue或新监测。

## Phase 2B 命令身份与联合门禁事件

`feature/phase2b-trajectory-execution@45f497c…`（TEAMMATE-TRAJECTORYGATE-20261012）相对688d80d有59路径。固定25步完整、317原始文件哈希一致，单次投递约4.88秒ACK。15包/463 C++/269 Python/15 E2E/6 ROS通过；补跑463 UBSan、原四个Fake场景与安装/跨包检查（ENV-TRAJECTORY-GATE-20261012）。

新topology入口复现默认MoveIt/FJT客户端2、ready=0、退出2 BLOCKED、零Goal。原fixed_pose生成211点规划；纯数据consumer被原窄速度限值拒绝，未执行。旧230与Python220/510/520保留，固定及补跑move_group均退出-11；子进程/daemon清理后两个事件容器已停止。869文件冻结见[报告](trajectory-gate-acceptance.md)，同步事实链后complete，不把事件完成当完整FSM通过。原60秒轮询、固定主会话、上海08:00截止不变，没有queue或新监测。

## 视觉安全与回放清理事件

`feature/perception-adapter@e53c09f…`（TEAMMATE-VISIONSAFETY-20261012）相对0e329f1修改8个适配器文件。固定25步完整、301原件哈希核对一致；一次投递约5.556秒ACK。14包/358 C++/269 Python/15 E2E/6 ROS通过，colcon零测试仍失败；手动新53项、公开62项通过/1私有证据跳过（ENV-VISION-SAFETY-20261012）。

默认和两次插桩回放均4/4、SIGINT exit 0；只有验证脚本等待订阅，不以单次默认通过关闭旧漏帧。局部TF安全helper尚未接FSM，Python静态反例与原220/510/520、MoveIt退出-11保留。旧任务结束后串行补跑，最终两容器停止、无OOM和残留ROS进程。463文件冻结及证据链见[报告](vision-safety-acceptance.md)，同步后complete。无queue或新监测，原固定主会话、60秒轮询和上海08:00截止不变。

2026-10-12 回放退出增量（ENV-VISION-REPLAY-20261012）：dc76a0b 已签收并补验原安装进程自然结束/中途SIGINT，57项适配器和80项公开视觉通过、1项私有跳过。中间 e09d00e 的 relevant=false 视觉增量纳入本次累计18路径；新增私有入口缺输入、默认零收集/送达可靠性与完整FSM仍待验。486文件、原始失败和清理见[报告](vision-replay-acceptance.md)。本事件不更改轮询、过滤规则、08:00截止或后续定时任务，不启动新监测。

## Goal归属与实时Status事件

`681bb64…`（TEAMMATE-OWNERSHIP-20261012）的25步固定复现完整、317原文件哈希一致，一次投递约8.302秒ACK。新增的真实失败为FJT套件第7项DuplicateCancelOnlyOneBackendCall120秒超时；本轮新核验器也对原XML报missing_result。确认runner59420/旧容器停止后补跑同二进制61项及独立UBSan478项均通过，原挂起不关闭（ENV-TRAJECTORY-OWNERSHIP-20261012）。

原生GenericSystem无实时Status，success预检零Goal BLOCKED；加默认MoveIt再因Status及clients=2阻断。无心跳/预热Goal/参数放宽，未补跑原生其余执行场景。原失败、新结果和清理708文件见[验收报告](trajectory-ownership-acceptance.md)。空域、进程及容器停止后归档并complete，只释放下一SHA串行门禁，不等于功能全通过。08:00后集成/UI定时器继续SCHEDULED；原监测60秒轮询、固定主会话和08:00截止不变，没有queue或新监测。

## 08:00 截止排空与同轮交付

ENV-CPP-MOCK-WEBUI-20261012在用户授权时刻后核对原状态、所有14份完整回执、最后681bb64事件报告及旧进程/容器；全部已排空，未丢弃pending。只读状态快照及哈希保存在新的953文件冻结，原签收报告/冻结字节未变。随后从已交付main f7eaa2c创建统一C++ Mock/Web候选7da4322，真实父子Action和UI部分通过，延迟取消520归孙嘉明；TEAMMATE-CPPUI-20261012对应独立PR #8。完整[SOP、结果与双仓库回执](cpp-mock-webui-acceptance.md)另记，未把监测结束或事件complete解释为功能全通过，也未更改正式pin。
