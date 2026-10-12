"""Write source-backed acceptance report after freeze. Codex assisted."""
from pathlib import Path
import json
raw=Path(__file__).resolve().parent;root=raw.parents[1]
a=json.loads((raw/'supplement-analysis.json').read_text());f=json.loads((raw/'freeze-result.json').read_text());n=a['supplement']['native_gate']
report=root/'docs/trajectory-ownership-acceptance.md';assert not report.exists()
report.write_text(f'''# Phase 2B Goal 归属与实时 Status 验收

**结论：首次轨迹 Action 套件在重复取消用例挂起并超时；未修改二进制的61项补跑及独立478项UBSan通过。间歇性超时未解决。原生GenericSystem与默认MoveIt共存预检均BLOCKED、零Goal；完整FSM和实机未验收。**

固定提交 `681bb64bfb8cd482d1e78950cef4cfe395b21bff`（TEAMMATE-OWNERSHIP-20261012），相对已验 `45f497ce3444e255463faf41f7b736aa9ad07d7b` 共7文件。代码提交 `b8857de49ec5405812f87887b1407092af7335a5`，当前提交补文档。来自监测记录的 `feature/phase2b-trajectory-execution` / `refs/pull/7/head`；这是本地观测，不声明PR实时合并状态。本项目观测 ENV-TRAJECTORY-OWNERSHIP-20261012，按 USER-HW-20261011-08、USER-HW-20261011-09 执行，单次投递约 **{f['queue_to_ack_seconds']:.3f}秒**获得主对话ACK。

**实际变更。** 修改ExecutionSnapshot、FjtMotionPort、探针、测试、身份核验器和两份文档，新增15项ROS异步测试。取消pending阶段“只有一个活动UUID便视为Own”的推断，保存观测UUID，收到本请求Handle后精确核对；增加Status是否收到、合法性和本地接收年龄门禁，内部Status订阅改为RELIABLE/VOLATILE；Result已终结但Status仍Active时阻止后继Goal。Goal归属有Unknown/Own/Foreign/NoActive四类，Unknown不放行。Snapshot结构布局改变，二进制消费者须重新构建。源码已核对；本项目未修改任何上游源码、FSM/Action/Cancel/Motion内核，也未合并或推进正式`1d940f7…`基线。

Status的本地接收年龄不等于消息发布时刻或跨进程独占证明；图发现也不构成原子执行锁。新增Fake夹具使用真实rclcpp_action和真实DDS，但Status使用测试专用重映射/转发/心跳及受控Response延迟。它是软件时序测试，不能当作原生JTC已有相同Status契约。Task、PickPlace、Planner、ROSIDL和驱动配置均未变化；默认PickPlace仍绑定MockPlanner/AsyncMockMotion。

**环境与原失败。** 固定复现上海时间10月12日03:51:48—03:58:43；25步骤起止/退出码完整，stop/collect成功，317个原文件哈希一致。runner59420及旧任务确认停止后，才从已停止原容器创建补跑快照。Ubuntu24.04 / Jazzy / C++17；驱动`53aab837…`、模型`47fa5e02…`、MoveIt2.12.4 / msgs2.6.0，完整SHA见inputs。两容器均无网络、设备映射、宿主挂载和端口映射，2CPU/4GiB/512PID，cap-drop ALL、no-new-privileges。使用已缓存环境，无依赖下载。

| 项目 | 本次实际结果 |
| --- | --- |
| 原构建 | 15包通过 |
| 原C++ XML | 417项通过；另一个FJT XML只有`test_fjt_action.gtest.missing_result`错误 |
| 原FJT套件 | 61项已注册，前6项日志为OK；第7项`DuplicateCancelOnlyOneBackendCall`后无完成输出，120秒CTest超时 |
| 原colcon汇总 | 718 tests / 1 error / 1 failure；包含包装/lint及缺失XML标记，不当独立用例数 |
| 原新身份核验器 | 在保留原XML上运行，明确FAIL missing_result；没有用补跑XML替换原件 |
| 普通补跑 | 同一未改二进制完整61项通过，18.629秒，包含新增15项；一次补跑，有120秒上界 |
| 独立UBSan | 8包重构建、7个C++包478项/26程序通过，源码声明/编译注册/XML核对一致 |
| 其他原测试 | 269 Python / 15纯Mock E2E / 6 ROS接线通过 |
| 安装与参数 | 新包rosdep通过；4个安装头/包文件与源码一致；无参数及非法模式各退出2 |

417=23 Core+87 Task+120 Manipulation+88 Motion+40 Action+29 Planner+30轨迹校验。61补跑与417原XML共同覆盖478个不同身份，但**这不是首次完整478项运行通过**；不能删除原超时，也不能把普通/UBSan重复计为956个不同用例。旧固定cpp-audit还存在16/22个`*_cpp`程序数量及INVALID_TEST宏识别问题，本轮同时有真实missing_result，不能统称“审计器过时”。

UBSan独立build/install使用`-fsanitize=undefined -fno-sanitize-recover=all -fno-omit-frame-pointer`和`halt_on_error=1`，七个包编译命令逐项核对。系统ROS/DDS/MoveIt未重新插桩，TSan未运行。通过的补跑和UBSan不能排除死锁/数据竞争。原挂起进程在自动清理时已经终止，没有原现场线程栈，**尚不能判定是夹具、端口锁/生命周期还是中间件调度问题**。已保留最小触发命令、原LastTest、缺失XML、补跑61项原日志和完整UBSan证据，归因与修复回交孙嘉明。

有界复现入口（在同SHA隔离容器、source Jazzy及candidate-install之后）为：

```bash
timeout --signal=TERM --kill-after=3 120 \
  /candidate-build/mtc_trajectory_execution_cpp/test_fjt_action \
  --gtest_output=xml:/tmp/ownership-review.xml
```

实际本轮命令及时间在冻结`supplement/logs/ordinary.sh`、`container/ordinary-full/full.json`；不能将此单次通过当作稳定性证明。本地分析器第一次把ament合成名称误写成精确`missing_result`而断言失败，原脚本/错误说明已保留；只改了读取谓词，未改运行XML或重跑原始测试。

**原生Status及执行权门禁。** 域155先启动唯一GenericSystem、确认两个active控制器和六关节状态；只读观察器仅订阅，不创建ActionClient。使用已交付、未改参数的success探针，清理后在独立域156加默认move_group运行topology；未注入空Status/心跳、未发预热Goal、未放宽门禁。

| 阶段 | FJT Server / Client | Status / 就绪 | 结果 |
| --- | --- | --- | --- |
| 原生控制器+success探针 | 1 / 1 | received=0、fresh=0、unknown=0、ready=0 | 约10秒预检后退出1，BLOCKED，零Goal |
| 默认move_group+topology探针 | 1 / 2 | 同样未收到Status，ready=0 | 退出2，BLOCKED，零Goal；第二客户端为moveit_simple_controller_manager |

Status发布端观测为RELIABLE/TRANSIENT_LOCAL；本次共观察 **{n['status_messages']}条Status、{n['combined_distinct_joint_stamps']}个不同JointState时戳（两次串行观察合计）**，关节全程保持零。源码中的预检退出路径发生在发送轨迹之前，与零Goal/不运动证据一致。原生mismatch、cancel、identity场景因先决证据不足 **NOT RUN**；本轮不得沿用45f497c的四项执行PASS。这些行为证明当前门禁拒绝，不能写成原生轨迹执行或完整FSM通过。受控Fake的正常/取消/外部Goal/乱序覆盖由61项测试提供，边界不同。

首次只读观察脚本误将success预检的异常退出1预期为topology的退出2，产生AssertionError并在启动MoveIt前退出；`native-gate/summary.json`的FAIL原样保留。该次实际control退出0、无升级/子进程失败、空域通过；其clean_shutdown=FAIL还包含了脚本预期两个launch的计数前提。随后仅补跑尚未执行的MoveIt共存场景，没有重跑native success或改上游行为。这个断言错误属于本项目验收脚本，不能归因给上游内核。

驱动源码/安装 **{n['driver_files_count']}个文件**前后哈希一致。补跑退出子检查 **{n['clean_shutdown']}**，具体各子进程退出和统计线程信息见native-gate/summary及日志；最终空域检查通过、容器只剩keeper后停止。keeper被docker stop终止产生的137与ROS子进程退出分别记录，两个事件容器均已停止且无OOM。

**其他失败与未完成范围。** 原自动Python Mock仍为220/510/520、ABORTED、完成0；Cancel响应接受不等于最终取消完成。独立MoveIt规划执行成功(status4/code1，最大误差`9.161319229751826e-05rad`，209个不同关节时戳)，但move_group退出-11，退出验收失败；它没有经过新的FjtMotionPort，不能解决本轮BLOCKED。旧rosdep缺口、驱动1104汇总中的279失败/259跳过继续保留，不作为实机功能结果。

| 未完成事项 | 交接责任与要求 |
| --- | --- |
| 原DuplicateCancel120秒间歇超时 | 孙嘉明：区分测试夹具与生产端口的锁/生命周期问题，补有界证据；此次未接管修复 |
| 原生Status/唯一执行权及持续证据契约 | 孙嘉明主责，集成配合；不能靠人工心跳、预热动作或取消保护放行 |
| Planner/FJT时间契约、默认MoveIt第二执行客户端 | 孙嘉明、常建烁及集成共同明确；不改stamp、轨迹或扩大限位绕过 |
| 异步FSM Cancel/停稳宿主、真实Task→PickPlace链 | 孙嘉明负责内核，张叔阳负责集成验收；当前独立测试不替代链路 |
| 旧Python、MoveIt退出、依赖/驱动lint、SDK许可与校验、TSan、NUC/实机 | 保留原失败和缺口；当前不扩大验收结论 |

08:00后C++ Mock统一启动、真实Action链、Web UI与双仓交付属于 USER-HW-20261012 / USER-HW-20261012-02 的后续任务；本事件处理时仍未到截止时间，定时器保持SCHEDULED、零投递，未提前开始。监测沿用原60秒轮询和08:00截止，主对话完成证据检查与complete后才释放下一SHA串行门禁；本轮没有queue、新监测、外部消息、提交/推送或基线推进。

**证据入口。** 冻结目录[trajectory-ownership-20261012](experiments/trajectory-ownership-20261012/)，共 **{f['files']}文件**。其[索引](experiments/trajectory-ownership-20261012/index.json) SHA-256：`{f['index_sha256']}`；[协议](experiments/trajectory-ownership-20261012/protocol.md)、[inputs](experiments/trajectory-ownership-20261012/inputs.json)、[summary](experiments/trajectory-ownership-20261012/summary.json)。原始目录为`outputs/moveit-watch-20261011/runs/sha-681bb64bfb8cd482d1e78950cef4cfe395b21bff/`，补跑为`outputs/trajectory-ownership-acceptance-20261012-681bb64/`；原outputs及镜像/bundle不入库，bundle哈希已登记。原超时日志在冻结`supplement/original-trajectory-testing/`，补跑61项、UBSan、原生门禁/清理在`supplement/container/`。最终complete回执另留raw，冻结索引不回写。

OpenAI Codex协助源码审阅、隔离复现、只读观察/有界运行/分析/归档和文档同步；未修改上游算法或内核。上游根MIT与trajectory/Action包Apache-2.0声明差异及驱动/模型/SDK许可待核对范围保留，不重新授权。
''')
print(report)
