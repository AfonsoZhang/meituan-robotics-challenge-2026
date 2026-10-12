# FSM 接线补丁与复验（2026-10-11）

**B01、B02、B04 已在独立分支修复并提交 PR，三项范围内复验通过；完整 ROS Mock 任务仍未通过。**
补丁为 [PR #2](https://github.com/F1u0rite/meituan_challenge_ws/pull/2)，提交
`1d3dccf23c53d299d457564daeb6438190ea2d77`，分支 `fix/ros-startup-wiring-b01-b02-b04`。
原 17:25 提交时已请求仓库负责人 `F1u0rite` 审阅、尚未合并；该状态为历史快照。后续 23:35 上游已合并，见文末追踪；正式基线仍为 `1d940f7…`，
[版本锁定文件](../robot/fsm-baseline.repos)未推进。

用户在“是否应该由我进行修复”的建议后回复“按照你的建议执行”（USER-HW-20261011-05，用户会话）。
本次限定为三项启动／接口接线补丁、独立分支／PR 和复验；按 SPRINT-PLAN-20261011 §06–07，
孙嘉明继续负责 FSM/Action 内核及 B03，张叔阳负责集成补丁和最终验收。

本轮证据为 **ENV-FSM-FIX-20261011**，见[冻结索引](experiments/fsm-wiring-fix-20261011/index.json)。
原基线的失败结论和证据 ENV-FSM-20261011 保留在[首次验收报告](fsm-acceptance.md)，未覆盖或改写。

## 补丁范围与结果

| 问题 | 补丁 | 本轮结果 |
| --- | --- | --- |
| B01 时钟成员冲突 | `TaskExecutorNode` 使用独立 `_fsm_clock`，保留 rclpy 的 `_clock` | 默认 ROS 时钟与注入时钟两例通过，实际 Task 节点启动成功 |
| B02 配置关键字错误 | ROS 参数 `perception_max_age_sec` 映射到配置字段 `perception_max_age_s` | 默认值与 ROS 参数覆盖两例通过，实际启动已越过原 TypeError |
| B04 解锁服务名不一致 | 默认客户端改为 `/mtc/tool/trigger_unlock`，保持显式覆盖能力 | 真实 DDS 联锁拒绝与 Mock 脉冲受理两例通过；受理后仍不报告已释放 |

生产修改仅两个 Python 外壳文件，5 行新增、4 行删除；另加六项 ROS 回归、复验说明和 README 入口。
FSM 状态转换、Cancel 内核、Action IDL、四个 C++ 核心包及驱动未改动。PR 的“待审阅”不等于模块负责人已批准。

## 复验环境与计数

继续使用独立 Ubuntu 24.04.5 / ROS 2 Jazzy / Python 3.12.3 容器，在上轮 12 包安装基础上构建
独立的两个 Python 包 overlay。测试使用 domain 95 / LOCALHOST，容器外部网络断开、无设备挂载和端口映射。
安装后的两个生产文件及测试文件哈希均与提交内容一致；验收容器已停止并保留。

| 检查 | 未修复基线 | 候选补丁 |
| --- | --- | --- |
| 同一版六项 ROS 接线回归 | 6 FAIL，均为预期的三类缺陷 | 6 PASS / 0 FAIL / 0 SKIP |
| 两个 Python 包 overlay 构建 | 使用前次已验收安装 | 2/2 PASS |
| 既有 Python 包测试 | 前次 269 PASS | 本次逐包 269 PASS / 0 FAIL / 0 SKIP |
| 显式纯 Python Mock E2E | 前次 15 PASS | 本次 15 PASS / 0 FAIL / 0 SKIP |
| 实际完整 Python Mock | Task/PickPlace 启动失败，Goal 未发送 | 两次仍为 FAIL，见下文 |

本次共 290 个通过用例（269＋6＋15），不与基线重复执行相加。未重跑未改动的 318 项 C++ 和独立 Fake 驱动；
前次结果只按 ENV-FSM-20261011 引用。E2E 的 MockPlanner 不等于 MoveIt 已接通。

配置回归使用真实 ROS 参数及配置构造，然后主动截断入口以隔离未修复的 Action 接线；不以此宣布 PickPlace 启动通过。
工具服务回归使用 `MockUnlockIo` 和明确标注的合成挂载／释放阶段输入，不是实体落座或释放证据。
测试命令与前期失败也已保留：colcon 的可选 `--allow-overriding` 参数在此容器不可用，移除后构建成功；
pytest 合并收集各包时遇到同名 `test` 模块，分进程逐包运行后通过。最初工具测试未准备 RELEASING 阶段，
联锁按预期拒绝；修正测试准备流程后，同一版最终测试在基线失败、补丁通过。

## 仍需模块负责人处理

| 编号 | 实际证据与边界 | 负责人及复验要求 |
| --- | --- | --- |
| B03，保留 | `PickPlaceServer` 的 `action_type.Server(...)` 和 `action_type.CancelResponse()` 不属于生成 Action 类型的接口；本轮仍被 B05 遮挡 | 孙嘉明；真实 ActionServer 的 Goal/Cancel/Result 和并发行为 |
| B05，新增 | B02 修复后，两次在 `RosMotionPort.__init__` 的 `action_type.create_client(...)` 报 `ExecuteJointMove` 无该属性，PickPlace 退出 1 | 孙嘉明；接入真实 ActionClient 并核验目标／结果／取消适配 |
| B06，新增 | 两次启动约 5 秒后、首个 Goal 前，Task 的 INIT 超时进入 FAULT；随后 Goal 被受理，收到 FAULT Feedback 和 ABORTED Result（6），`error_code=510`、完成数 0 | 孙嘉明；明确初始化／待命与看门狗契约，覆盖延迟首次 Goal；本轮未推断及时发送 Goal 的行为 |
| 退出观测 | SIGINT 时 `safety_supervisor` 报 `rcl_shutdown already called`，进程退出 1；launch/采集脚本退出 0 | 安全节点负责人复核清理流程；不能把采集退出码当作任务结果 |

两次示例 Goal 均为黄色基础任务、`timeout_ms=5000`，保持默认 `dry_run=True`；不是正式比赛口令。
Task 和 Motion 服务器已发现。第二次逐节点服务器查询及 `wait_for_server` 确认 PickPlace **服务器不可用**；
通用 Action 名单包含 Task 的 PickPlace 客户端，不能据此认定服务器存在。完整感知、工具证据、MoveIt、
新 C++ FSM 链路、NUC 和实机仍待接入／验收。

## 交接与复现

PR 中已有[六项 ROS 测试](https://github.com/F1u0rite/meituan_challenge_ws/blob/1d3dccf23c53d299d457564daeb6438190ea2d77/tests/test_ros_wiring.py)
及[运行说明](https://github.com/F1u0rite/meituan_challenge_ws/blob/1d3dccf23c53d299d457564daeb6438190ea2d77/docs/migration/ROS_WIRING_FIX_20261011.md)。
原始运行目录为 `outputs/fsm-wiring-fix-20261011-171337/`，冻结证据含基线／补丁 XML、两个启动日志、
Goal/Feedback/Result、实际命令、补丁及 MIT 许可文本。审阅及后续修复完成后，以新的实际提交号重新验收，
再按交接结果更新正式锁定；不覆盖本轮失败记录。

生成式 AI 披露：使用 OpenAI Codex 编写三项补丁、ROS 回归和验收脚本，运行隔离复验、创建 PR 并整理来源索引。
上游来源为 TEAMMATE-FSM-20261011 / TEAMMATE-SDK-20261011；FSM 根许可证 MIT，冻结补丁附原许可，
没有归档第三方模型或 SDK 二进制，也没有连接实体硬件。

## 后续合并追踪（23:35）

监测在上游 `main` 发现合并提交 `c10f6ed59966401684851f917f9137b0a6cf12ae`，双父提交包含本补丁 `1d3dccf…` 与 C++ Action 交付 `c0f7017…`；两个 Python 文件、六项测试和复验说明均与原 PR 相同（TEAMMATE-MERGE-20261011）。合并后的六项 ROS 回归再次通过，但实际旧 Python 尽早/延迟/取消任务分别 ABORTED / 220、510、520，B03/B05/B06 不据合并关闭。新 C++ 独立四场景另行通过，独立 MoveIt 退出仍失败，见[本次验收](wiring-merge-acceptance.md)（ENV-WIRING-MERGE-20261011）。原 ENV-FSM-FIX-20261011 的 OPEN 快照、失败与冻结索引不改写；本项目未代为合并或推进锁定。
