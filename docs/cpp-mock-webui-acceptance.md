# C++ Mock Bringup、真实 Action 链路与 Web UI 同轮验收

后续更新：软件 Mock C1 已单独修复并推送 [PR #15](https://github.com/F1u0rite/meituan_challenge_ws/pull/15)，见 [新报告](c1-cancel-fix.md)（ENV-CANCEL-PR-20261013；ENV-CANCEL-FIX-20261013）。PR #8 源码树已恢复原内容；下文保留 2026-10-12 的原始失败和交付记录。

2026-10-12 本机观测：**集成部分通过，取消完成边界 C1 未通过。** 统一启动和 Web UI 已实际连通 C++ Task → C++ PickPlace；基础/序列成功、非法/并发拒绝、反馈、失败传播、及时取消、冲突门禁及清理有真实 ROS 证据。正常 Mock 配置下较晚取消虽收到 ACK，父子最终均为 ABORTED/520，不能认定取消完成。源码已交独立 [PR #8](https://github.com/F1u0rite/meituan_challenge_ws/pull/8)，请求 F1u0rite 审阅；C1 内核契约交孙嘉明。来源：TEAMMATE-CPPUI-20261012、ENV-CPP-MOCK-WEBUI-20261012；授权：USER-HW-20261012、USER-HW-20261012-02（用户会话）。

## 版本、时序与修改边界

原监测于北京时间 **08:00:00.267972** 自行结束，状态 EXPIRED，pending 为空、active/main_review 均为空，最后成功轮询为 07:59:34.023137。08:00:07 签收本轮延时任务后先核验旧 runner、容器和进程；没有丢弃事件、重复启动监测或发送新 queue。14 个实际事件的 complete 报告 SHA 与原回执逐一匹配；最后 `681bb64…` 的原超时、补跑与回执仍按 [Goal 归属验收](trajectory-ownership-acceptance.md) 保存（ENV-TRAJECTORY-OWNERSHIP-20261012）。因此新增工作没有占用仍在运行的监测复现，也没有留下串行门禁待办。

| 项目 | 实际版本 / 结论 |
| --- | --- |
| 截止时上游 main | `f7eaa2c0d2887aeada4fd635112c63c237962ff7`；已包含 C++ Task 的真实 PickPlace ActionClient |
| 本轮候选 / 实际推送源码 | `7da43228d602a6b23571bfc599d69529ef7bea23`，分支 `fix/cpp-mock-webui-integration-20261012` |
| 上游审阅 | [F1u0rite/meituan_challenge_ws PR #8](https://github.com/F1u0rite/meituan_challenge_ws/pull/8)，OPEN，已请求 F1u0rite；没有自动合并 |
| 个人仓库起点 / 导入 UI 来源 | `96b76245da4c9ffe856d26d156bbd72f7f956a84`；原文件哈希见候选 package `provenance.json` |
| 正式 FSM pin | `1d940f7c5f12561fed6641457c0b4b630a282b05`，`robot/fsm-baseline.repos` 字节未变 |
| 未合入能力 | Phase 2B、视觉、标定、Planning Scene 的未合并分支均未拼入本候选 |

40 个文件的候选差异归档为 [source.patch](experiments/cpp-mock-webui-20261012/source.patch)。原 Task 已经有 C++ 下游 ActionClient，本轮通过统一 remap、就绪检查和 UUID 日志使它可重复启动和验收；没有另写旁路代替下游。新增 `mtc_cpp_mock_bringup` 包、显式 `cpp_mock` Web/ROS 桥接、100 ms 只读状态和已有 Mock 选项的启动参数。`src/mtc_task_cpp`、`mtc_manipulation_cpp`、`mtc_motion_execution_cpp`、`mtc_core_cpp`、`mtc_interfaces` 和 `ActionSlot` 未改；IDL 亦与正式 pin 相同。候选 C++/UI 源码哈希与验证副本对应，见 `runtime/source-integrity.json`、`host/upstream-staging.json`。

## 环境和统一启动 SOP

Ubuntu 24.04.5 / Jazzy / C++17；g++ 13.3.0、Python 3.12.3、rclcpp/rclcpp_action 28.1.22、rclpy 7.1.12、std_msgs 5.3.8、rmw_fastrtps_cpp 8.4.4、colcon 0.21.3。完整已安装版本在 [环境日志](experiments/cpp-mock-webui-20261012/host-logs/environment.log)。只复用截止主线原隔离运行的缓存依赖，新增两包在 `/integration-build`、`/integration-install` 重建；不把这次增量构建计为重跑全部历史包。

快照镜像 `sha256:2f0a27c475acb9ec056cb1741777bd83a08b919e0d9b4ab6bfcc95f3e7af6da9`，来自已停止的截止主线容器；其原镜像为 `sha256:8c442d3be3d5c2671d149d320da09388350d261fa452e23bb848aa5978b8a5f1`。单容器 `mtc-cpp-webui-review`，network=none、无设备映射、无宿主挂载、无 Docker 端口映射、2 CPU/4 GiB、pids-limit=512、cap-drop=ALL、no-new-privileges。源码通过 docker cp；没有下载依赖、启动驱动或接真实设备。缓存驱动为 `53aab83735236f0c262ecb11e04ef2600241d9d9`，本轮未运行它。

完整 [固定提交 SOP](https://github.com/F1u0rite/meituan_challenge_ws/blob/7da43228d602a6b23571bfc599d69529ef7bea23/src/mtc_cpp_mock_bringup/README.md) 覆盖源码、依赖、构建、启动、就绪、发任务、取消、日志、退出、重启和常见故障。以下命令在已有依赖的隔离工作空间使用，每次输出目录必须全新：

```bash
source /opt/ros/jazzy/setup.bash
cd /path/to/meituan_challenge_ws
# git rev-parse HEAD 应为本报告候选 7da43228d602a6b23571bfc599d69529ef7bea23
export MAKEFLAGS='-j2 -l2'
colcon build --packages-up-to mtc_cpp_mock_bringup --executor sequential \
  --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo -DBUILD_TESTING=ON
source install/setup.bash
export ROS_DOMAIN_ID=161
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
ros2 run mtc_cpp_mock_bringup mock_stack \
  --namespace /mtc_cpp_mock --output-dir /tmp/cpp-mock-run-001 --port 8767
```

看到 READY 后，网页地址为运行环境内 `http://127.0.0.1:8767/`；`mock_check --namespace /mtc_cpp_mock --output /tmp/ready-001.json` 可保存就绪快照。软件 Mock 依赖位于 C++ 适配器中，不需要 Python Task/PickPlace、Motion Action Server、MoveIt 或驱动。运行图与 PID/实际 ELF 路径写入 `launch.json`；SIGINT/SIGTERM 只清理本启动器拥有的进程组，写 `cleanup.json`、`cleanup-graph.json`；超时强杀会记失败，不视为正常退出。

实际浏览器验证使用宿主仅环回 QA 中转 `127.0.0.1:8769 → docker exec 标准输入输出 → 容器环回:8767`，没有放宽容器网络或映射 Docker 端口；实现归档 `harness/qa_relay.py`，测试后中转已停止。此为本地验证通路，不是实机部署方式。

## 真正的父子 Action 与 Web 接口结果

接口为 `mtc_interfaces/action/ExecuteTask` 与 `mtc_interfaces/action/PickPlace`。默认节点 `/mtc_cpp_mock/mtc_mock_task`、`/mtc_cpp_mock/mtc_mock_pick_place`；Action 地址分别为 `/mtc_cpp_mock/task/execute`、`/mtc_cpp_mock/manipulation/pick_place`。各场景使用独立命名空间并串行运行。Web 只向 Task 发 Goal，C++ Task 自己发 PickPlace Goal；C++ MTC_TRACE 关联父子 UUID、request_id、响应、取消与结果，旁路订阅保存两级原生 Status/Feedback。

本次 40 个实际 C++ Action gtest 通过（colcon 总计 44 含 4 项包装）；39 个 UI 离线测试通过。这些单测单独记账。下面六个集成场景另起实际 C++ 进程，经 HTTP/rclpy 访问，均通过相应正例或反例断言；[逐场景总结](experiments/cpp-mock-webui-20261012/runtime/acceptance-final/summary.json) 含完整 UUID、终态、时刻与清理，原始事件在各场景目录。

| 场景 | Task Goal UUID | Feedback 条数 | 实际终态 / 错误码 / 完成数 | 判定 |
| --- | --- | ---: | --- | --- |
| basic | `439b9dfd-7aaa-44e6-9c28-1db45cbe5d32` | 16 | SUCCEEDED / 0 / 1，T0 | 通过 |
| sequence | `67b1736d-0fa5-4635-b75c-b8abac5d27d6` | 50 | SUCCEEDED / 0 / 3，P1/P2/P3 | 通过 |
| cancel，及时取消 | `b7f0a715-bdba-42ff-ba12-b511dd35c2fc` | 5 | CANCELED / 0 / 0；子状态 2→3→5 | 本时序通过 |
| planning_failure | `2e41456b-4b62-410f-bcf0-e7943e2d9f90` | 14 | ABORTED / 200 / 0；两个真实子 Goal 均失败 | 注入失败正确传播 |
| cancel_unconfirmed | `6b4b445e-e083-43e4-8075-273e1b22abe3` | 5 | ACK 后 ABORTED / 520 / 0，保持锁定 | 证据不足反例通过 |
| status_unknown | `3c223bb1-e4b3-47c3-b66c-9450bbe45a0c` | 3 | ABORTED / 230 / 0，保持锁定 | 未知状态反例通过 |

基础任务子 UUID 为 `d1ed2a0cd4681efdd2798404be6b5596`，及时取消子 UUID 为 `0ae98b52085b62447fb3ac40dbcf9fb9`；序列逐次创建三个子 Goal，全部保存在 summary/原始 ROS 事件。C++ 服务端本身拒绝非法 Goal 和已受理任务期间的并发 Goal；Web HTTP 并发返回 409。HTTP 202 仅代表请求入队，必须等 ROS ACCEPTED 后才能作受理与并发判断。

浏览器实际点击提交产生父 UUID `19b6406a6c3f4fc3b6ca4a584470700f`，下游 `302ea5b2066cc0eec79aac9267d36983`；北京时间 08:16:38.843 请求、38.861 受理、08:16:45.461 SUCCEEDED/0/T0，17 条实际 Feedback。网页显示真实进度和结果、可导出原会话；没有使用纯 Mock 定时器或既有 ROS fixture 冒充 C++ 链路。实际点击 Cancel 的未通过结果详见下一节，网页如实显示失败及 520，没有在 ACK 时显示取消完成。

## C1：正常 Mock 下延迟取消未完成

**负责人：孙嘉明（FSM/Action/Cancel/Motion 内核）；张叔阳负责复验和材料。** 正常 `success` 配置、`result-delay-ms=700`，没有注入 `stop_evidence_available=false`。浏览器显示 MOVE_PRE_ALIGN 后点击取消：

| 关键点（北京时间） | 原始观测 |
| --- | --- |
| 08:17:02.666 / 02.681 | 父请求 / 受理，UUID `07750616e1bd41eaba003cdfff9ba0bc` |
| 08:17:02.709 | 页面接收 MOVE_PRE_ALIGN Feedback；关联子 `b82da195d639f268b9f47da27b2dec08` |
| 08:17:03.054 / 03.059 | Cancel 请求 / ACK 受理 |
| 08:17:03.069 | C++ Task 对关联子 Goal 发取消 |
| 08:17:03.087 / 03.091 | 子 / 父实际 Result：ABORTED（6）、520、完成数 0 |

浏览器等待“已取消”的测试在 30 秒后超时，实际早已进入上述失败终态；原超时、诊断快照和截图都保存，不能把测试超时误记成 ROS 无结果。父子原始日志在 `runtime/browser-stack`，网页文件 `web-session/ui-fbf04324-6dd5-455e-8c5f-4ff7e4ab0aa7.json`；[失败截图](experiments/cpp-mock-webui-20261012/host/browser-failure.png)。

停止旧栈、确认空图后，干净重启同一命名空间，以独立 CLI 再现同类结果：

```bash
# 终端一，保持相同 source / ROS_DOMAIN_ID，使用全新输出目录
ros2 run mtc_cpp_mock_bringup mock_stack --namespace /cpp_browser \
  --output-dir /tmp/cpp-cancel-boundary-001 --result-delay-ms 700
# 终端二
ros2 run mtc_cpp_mock_bringup mock_task --namespace /cpp_browser \
  --output-dir /tmp/cpp-cancel-boundary-client-001 --cancel-at MOVE_PRE_ALIGN \
  --cancel-delay-ms 400 \
  --goal '{"task_id":"delayed_cancel_001","mode":1,"ordered_colors":[1],"timeout_ms":30000,"placement_stability_sec":3}'
```

CLI 父 `3587bc1fe5b64da7a99405eded248d69`、子 `c861a09931ce7ecf74f2261aca0a6f74`；08:19:50.754 父受理并下发子 Goal、08:19:51.183 取消、51.202 子终态、51.203 父 ABORTED/520。见 [原始事件](experiments/cpp-mock-webui-20261012/runtime/delayed-cancel/events.jsonl)、[真实 Result](experiments/cpp-mock-webui-20261012/runtime/delayed-cancel/result.json)。CLI 返回 0 只表示取得终态，不表示任务或取消成功。

静态分析提示：AsyncMockMotion 的结果延时只延后 Future 交付，底层 Mock 运动即时完成；定时器继续推进 ManualClock。MotionExecutorCore 的停稳证据龄期默认上限 0.3 s，无在途命令的 stop 不刷新已保存证据。这与晚取消出现 520 一致，**尚未以内核内部观测证明确切失败判据**。请负责人确认持续反馈/停稳证据新鲜度与取消契约，增加正常操作时序回归；本轮没有改内核、放宽有效性门禁、伪造反馈或自动重启解除 admission lock。及时取消正例不关闭 C1。

## 冲突、QoS、停止与重启

每轮 `launch.json` 记录实际 C++ ELF 路径及 argv；图中各 Action 只有一个预期 C++ Server，无旧 Python Task/PickPlace Server。图检查包含 Task 的下游客户端、类型、节点、发布 GID 和 QoS。原始 ROS 图也把仅订阅 Action Feedback/Status 的记录器列入 clients；它没有向 PickPlace 发送 Goal，父子调用关系以 C++ send/response/Result trace 和 UUID 交叉确认。

Feedback 与只读状态发布端观测 Reliable/Volatile，Status 为 Reliable/TransientLocal；本 DDS 图 API 对 history 返回 UNKNOWN（3）、depth=0，**没有把源码配置的 depth=5 当成实测队列深度**。只读状态要求唯一来源与新鲜时戳，是工程就绪检查，不是恶意 ROS 节点认证机制。

故意额外启动一个 C++ PickPlace Server 后，UI 禁用任务提交、HTTP 409，零新 Goal；移除该受控进程后恢复唯一服务器。重复启动相同 domain/namespace 被文件锁拒绝。同一 namespace 停止后重启，新 Web 会话历史为空、不自动重放旧任务；外部 CLI 任务标为外部、没有旧任务句柄便不能代取消。页面明确“C++ Mock / 硬件未接入”，没有生成 RobotState/ToolState，硬件、关节、相机状态保持未知。390 px 页面无横向溢出。

最终六个场景及两次浏览器栈的自有 Task/PickPlace/Web 进程退出码均为 0，命名空间图排空；宿主 QA 中转退出，无运行中的 mtc 复现容器。容器中仅剩 `sleep infinity` PID1 后执行 docker stop，其退出码为 137、OOMKilled=false；这是容器保活进程的最终终止，**不记作 C++ 节点崩溃，也不隐去 137**。见 [最终清理](experiments/cpp-mock-webui-20261012/host/final-cleanup.json)、`host/processes-before-container-stop.txt`、`host/isolation-stopped.json` 及各栈 cleanup 文件。停止页面后提交保持禁用。

## 原始失败、冻结和未完成范围

早期验收工具有 HTTP 名称覆盖导致请求未发出、DDS 未匹配导致回执/短状态漏观测、HTTP 202 后并发抢发导致第二个 ROS Goal 先受理等错误。分别修正工具命名、有界匹配和测试顺序后，保留 acceptance-v1/v2/v3/v4，再单列 acceptance-final；没有改写原日志或用重跑覆盖。cap-drop ALL 下更名目录的权限失败、浏览器测试代码 ReferenceError、停启期间 HTTP 502/负例 409、初次候选提交缺本地 Git 身份的失败也保留。没有放宽隔离或修改全局 Git 配置。

冻结目录：[docs/experiments/cpp-mock-webui-20261012](experiments/cpp-mock-webui-20261012/)，**953 个索引成员**；[index.json](experiments/cpp-mock-webui-20261012/index.json) SHA-256：

```text
0da681cc8ad09f6f75a5f88ea90b2fc19165d76f7960c1f6e0f64384799d7f22
```

`runtime/` 为全部新原始运行/失败、ROS/Web 会话与构建/测试日志；`host/` 为命令元数据、截图、隔离/清理、PR 和来源校验；`host-logs/` 为有界命令输出；`source/` 与 `source.patch` 对应实际代码提交；`inputs.json`、`summary.json`、`protocol.md` 说明环境/口径。本机原始目录 `outputs/cpp-mock-webui-20261012/` 保留，不整体上传；不上传实时 watch-config、缓存或本机用户配置。

此前 22 个注册索引 SHA 已逐一核验，其中 20 个平面 files 索引的成员逐项验哈希；另 2 个历史 runs 格式这里只验证 index 字节，不冒充成员全验。14 个签收报告的字节不变。相关旧监测脚本/报告/冻结文件按各自索引显式纳入个人仓库提交；原自动失败、旧 Python 故障、MoveIt 退出 -11、Phase 2B 挂起/执行权/时钟问题均不被本轮关闭。

未完成：C1 和故障恢复契约归孙嘉明；真实视觉/工具输入、Motion Execution/FJT/MoveIt 全链、NUC 与实机验收仍待后续交付和系统集成。本轮是 C++ 软件 Mock Action/UI 联调，既不是独立 MoveIt/Fake 新验收，也不是完整 FSM 或实机通过。

## 双仓库交付回执

队友仓库 `F1u0rite/meituan_challenge_ws` 的独立分支已实际推送 `7da43228d602a6b23571bfc599d69529ef7bea23`；[PR #8](https://github.com/F1u0rite/meituan_challenge_ws/pull/8) 请求 F1u0rite 审阅。未推队友 main、未自动合并、未推进正式 FSM pin。个人仓库 `AfonsoZhang/meituan-robotics-challenge-2026` 的 `origin/main` 已实际推送证据提交 [`23c33af62c8a69409dcfbaef96f4129067d7a678`](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/commit/23c33af62c8a69409dcfbaef96f4129067d7a678)，随后以本报告所在的后续回执提交补记发布结果；PR 反向关联不可变报告与冻结索引版本。

[机器可核验发布回执](cpp-mock-webui-publication.json)保存双仓库版本、23个注册index、14份原签收报告、8份监测/检查脚本的既有冻结来源以及8935个变更文件的暂存字节核验。原始日志/补丁带有原生行尾空白，首次全路径`git diff --check`据此返回非零；保持证据字节，源码/报告/脚本范围的格式检查通过。没有为格式检查重写冻结记录。

使用 OpenAI Codex 协助源码检查、统一启动/只读观测/Web 桥接实现、真实 ROS/浏览器测试、失败分析和事实链归档。导入 UI 的原始版本/哈希、上游根 MIT 与部分 package.xml 许可证差异、原 UI 未单独声明根许可证的边界见候选 provenance；未替第三方重新授权。未开展 FSM/Action/Cancel/Motion 内核修复。
