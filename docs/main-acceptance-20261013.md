# 最新主线及既有未通过项验收（2026-10-13）

**结论：部分通过，整体验收未通过。** 主线完整普通/UBSan各486项C++通过，但并发重复检查第18轮出现新断言失败M1；C1延迟取消、旧Python运行、原生Fake执行门禁和MoveIt正常退出仍未关闭。未修改或接管内核，没有合并分支或推进正式pin。

用户本轮重新要求“验收”，并确认“最新主线及既有未通过项（推荐）”（USER-HW-20261013，用户会话）。这是本次新授权；10月12日Mac准备阶段终止的历史记录继续保留。来源TEAMMATE-MAIN-20261013；本地运行ENV-MAIN-ACCEPTANCE-20261013。旧监测EXPIRED、pending为空，原单次集成任务COMPLETE，未重新启动监测或queue。

## 固定版本与环境

- 团队main：`b4185155383541e1a4161587c4049a162f74b36d`，开工及收尾GitHub核对相同。相对已验`681bb64…`新增FJT锁修复与8项并发测试；原61项FJT文件仍为新文件的逐字节前缀。
- [PR #8](https://github.com/F1u0rite/meituan_challenge_ws/pull/8)：`7da43228d602a6b23571bfc599d69529ef7bea23`，仍OPEN、未合并，代码未变。本轮另建隔离副本仅重验C1及停止/重启，不把它拼进main。
- C++ Task/PickPlace/Mock/接口与`f7eaa2c…`相同；旧Python运行路径与`c10f6ed…`相同；标定源码与`06ab689…`相同。完整差异与比较在冻结`host/source-comparisons.json`、`host/since-ownership.patch`。
- Ubuntu **24.04.5 / x86_64 / Jazzy / GCC13.3 / C++17**，WSL2宿主，非实际NUC。驱动`53aab83735236f0c262ecb11e04ef2600241d9d9`、模型`47fa5e02fa873f27f7e812d31f31e3f4cf5e56b1`、MoveIt2.12.4、msgs2.6.0；SDK0.24.1-rc.3继承既有缓存，未新增厂商校验或许可确认。
- 本轮两个容器串行，均network=none、无设备/宿主挂载/端口映射、2CPU/4GiB/512PID、cap-drop ALL/no-new-privileges。main全新build/install，UBSan独立build/install；327个main跟踪文件运行前后不变。PR8重构建7包，306个源文件及17个安装Python文件身份留证。

本项目正式pin仍为`1d940f7c5f12561fed6641457c0b4b630a282b05`。新Phase2C、规划、视觉及Gazebo候选未纳入本轮，不借其他分支报告扩大main结论。

## 实测结果

| 项目 | 本轮结果与限度 |
| --- | --- |
| main构建 | 15包通过；Python byte-compiling disabled为日志警告 |
| 普通C++ | 486个不同身份/26程序，通过、零跳过；源码声明/编译注册/XML核对一致 |
| Python与补充 | 269包内测试、15离线Mock E2E、6 ROS接线、54标定离线检查通过；不代表实际Python启动或实测标定 |
| UBSan | 8包独立构建、7个C++包486项通过；编译命令逐项核实插桩；系统ROS/DDS/MoveIt未插桩，TSan未跑 |
| 有界重复 | 计划40个独立进程×10项、每进程40秒；第18轮首败即停，179次执行通过、1次断言失败、无超时，其余22轮未跑 |
| 主线C++实际进程 | 基础/序列、及时取消、缺失子Server故障、独立Motion四场景通过，均正常退出；前两项初次观察器误判另存 |
| 旧Python实际进程 | 早发/延迟/取消三次均ABORTED，分别220/510/520、完成0；未通过 |
| 原生GenericSystem | 首次Goal前Status received=0/fresh=0、ready=0，success探针退出1，BLOCKED/零Goal |
| 默认MoveIt共存 | 1个FJT Server/2个Client，topology退出2，BLOCKED/零Goal；共4929个不同关节时戳、关节保持零 |
| 独立MoveIt | Plan→Execute返回status4/code1，209个不同关节时戳，最大误差`9.828713480383159e-05 rad`；move_group退出-11，整体退出项FAIL |
| 依赖/安装 | 新轨迹包rosdep及4项安装身份/2个非法参数检查通过；全src rosdep仍缺ament_python定义，驱动仍缺docker.io和ros2-controllers-test-nodes。旧驱动lint未重跑、未关闭 |

普通colcon汇总786、UBSan汇总512含CTest包装等，不能当独立C++用例数；普通/UBSan/重复执行也不相加成新的用例总数。

## M1：并发重复断言失败，交孙嘉明

第一次完整69项FJT及独立UBSan通过。随后固定同一未改普通二进制，第18个进程中`FjtAction.LateGoalResponseAfterFaultRetainsOriginalSession`在`test_fjt_action.cpp:766`失败：`before->timed_out`预期true、实际false，用例约114ms；该进程其他9项通过并退出1。完整[原日志](experiments/main-acceptance-20261013/runtime/repeat-fjt/18.log)、[XML](experiments/main-acceptance-20261013/runtime/repeat-fjt/18.xml)、[命令与起止](experiments/main-acceptance-20261013/runtime/repeat-fjt/18.json)均保留，未重试覆盖。

测试设400ms期限，但只等待`fault_locked`；端口还有JointState、Status、图和归属等提前故障路径。原日志没有首个故障message/snapshot，**尚不能确定是夹具时序还是端口缺陷**。本次不是旧120秒死锁复发的证据；旧挂起本轮未复现，也不能据此宣布彻底消除。负责人应捕获首个故障快照/时序，保持严格门禁并给出有界回归证据。最小命令保留在18.json，固定重复驱动为`harness/tools/repeat_fjt.py`；新增8项加原ConcurrentGoals及DuplicateCancel共10项，与上游40×9口径不同。

## C++ Task→PickPlace 真实链路

实际运行main安装的C++ ELF；唯一PickPlace `send_goal`服务客户端是`mtc_mock_task`。观察器只订阅状态/Feedback，并在父任务终结后只读查询子GetResult，不发子Goal/Cancel。父子关联依据独立容器、唯一实际发送服务客户端、请求时间窗、原生UUID/Feedback/Result与固定源码；不是独立Server测试的替代描述，也不是网络抓包或跨进程原子独占证明。

| 场景 | 父Goal UUID | 子Goal UUID | 最终结果 |
| --- | --- | --- | --- |
| 基础 | `07ed0071f8b64b979c70fd7f59d48271` | `802e369420b81e832b58dc0540cc7348` | 父子4/0；T0完成1，父Feedback243条 |
| 三块序列 | `add697920cd0454795f2fce310b7bed1` | `805a7ddfb092beb05228edcc589416c5`、`0ea27b6ec969b3c328260cebf824c4f5`、`c747483f254886f81deebf96c6f29378` | 父子4/0；P1/P2/P3完成3，父Feedback729条 |
| 及时取消 | `543b4987df0d478b9461d9a3f7f71bae` | `ba3973aa81a26eab632d648d88a433a2` | 关联ACK受理，父子最终5/0，完成0；父Feedback8条 |

4=SUCCEEDED、5=CANCELED、6=ABORTED，斜杠后为error_code。非法颜色/序列/稳定性、并发和重复业务ID拒绝；缺失子Server返回6/220并锁定后继任务，独立Motion单点/取消通过。详细请求、接收时间、状态序列、类型/QoS、二进制哈希见`runtime/cpp-mock-v2/*/result.json`及`runtime/cpp-mock/`。

Feedback为RELIABLE/VOLATILE，Status为RELIABLE/TRANSIENT_LOCAL；DDS返回的history UNKNOWN/depth0不当成实际深度实测值。原观察器图API把反馈/状态订阅者也列为Action Client，在两个场景发Goal前失败；v2核对实际send_goal服务客户端后只补这两项。v1失败、源码及退出证据原样保留，未修改上游或忽略真正的第二发送客户端。所有该批C++节点退出0、无升级清理；没有同时启动Python Task/PickPlace。

及时取消只验证交付的可信Mock契约，PickPlace Result没有独立物理停稳字段，不证明真实硬件停止。

## C1及其他未通过项

PR8在另一干净容器重构建，使用success profile、结果延迟700ms，在实际MOVE_PRE_ALIGN反馈后延迟400ms取消；没有注入stop-evidence故障。父Goal `f19af380b54e40f183cf4ba00567e1d3`、子Goal `98a83fb219a120f8e2acde49c01880a1`，ACK受理，最终父子**6/520、完成0**。C++日志关联child_send/response/cancel/result，原始[结果](experiments/main-acceptance-20261013/pr8-runtime/c1/client/result.json)、[事件](experiments/main-acceptance-20261013/pr8-runtime/c1/client/events.jsonl)与Task/PickPlace日志均归档。CLI退出0只表示收到终态；外部验收脚本正确返回失败。

旧Python PickPlace仍在`ExecuteJointMove.create_client`处AttributeError；Safety在SIGINT后重复`rclpy.shutdown`退出1。原生Fake两道执行门禁保持拒绝，未伪造Status、预热Goal或放松证明；原生success/cancel/identity执行仍未完成。独立MoveIt与门禁观察各出现一次move_group退出-11；控制器统计线程的无效context报错保留。驱动5656个源/安装文件前后哈希相同。

| 未完成事项 | 责任交接 |
| --- | --- |
| M1提前故障/超时断言、C1延迟取消、旧Python FSM/Action及Safety退出 | 孙嘉明确认内核/夹具契约并修复；张叔阳保留复现和复验，不降低检查完成验收 |
| 原生Status、执行权、完整Task/PickPlace→Planner/FJT执行和停稳 | 孙嘉明主责，规划/集成共同确认；当前Mock或独立MoveIt不能代替 |
| MoveIt正常退出、驱动依赖/lint | 张叔阳跟进环境与复现，规划/驱动负责人定位；本轮未修改第三方内核 |
| TSan、SDK许可/厂商校验、真实标定、NUC和实机 | 继续待验；未合入的规划/视觉/Phase2C/Gazebo候选另案按固定SHA验收 |

责任交接已登记本仓库；本轮未代发外部消息。C1沿用既有ENV-CPP-MOCK-WEBUI-20261012；原超时和门禁范围见ENV-TRAJECTORY-OWNERSHIP-20261012，原报告与冻结集未改。

## 启动、复验与清理 SOP

完整命令、超时及退出码在冻结`host/*.json`和`harness/tools/*.sh`。每次使用新输出目录及新容器名；不覆盖本轮原文件。先核对固定SHA、缓存镜像ID与`inputs.json`版本，复制干净源码和外部观察脚本到新容器，禁止复用宿主ROS图或实体配置。

```bash
# 宿主：使用新目录/容器名；源码固定，不改变本项目正式pin。
git clone https://github.com/F1u0rite/meituan_challenge_ws outputs/new-main-review-source
git -C outputs/new-main-review-source checkout --detach b4185155383541e1a4161587c4049a162f74b36d
docker run -d --name mtc-main-new-review --network none --cpus 2 --memory 4g \
  --pids-limit 512 --cap-drop ALL --security-opt no-new-privileges \
  sha256:3985c32ff28a0095ccfab22b7addaa0fa4e36d5e5c7628be7b2c0c1cfc3ad77f sleep infinity
docker exec mtc-main-new-review mkdir /main-source /review /review-tools
docker cp outputs/new-main-review-source/. mtc-main-new-review:/main-source/
docker cp docs/experiments/main-acceptance-20261013/harness/tools/. mtc-main-new-review:/review-tools/
docker exec -it mtc-main-new-review bash
# 以下在新容器内执行。
source /opt/ros/jazzy/setup.bash
source /driver_work/install/setup.bash
unset ROS_STATIC_PEERS ROS_LOCALHOST_ONLY FASTRTPS_DEFAULT_PROFILES_FILE FASTDDS_DEFAULT_PROFILES_FILE CYCLONEDDS_URI
export ROS_DOMAIN_ID=171 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export PYTHONDONTWRITEBYTECODE=1 ROS_LOG_DIR=/review/roslogs
export XML_CATALOG_FILES=/acceptance-tools/offline-schema/catalog.xml
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0=/main-source
export CMAKE_BUILD_PARALLEL_LEVEL=2 MAKEFLAGS='-j2 -l2'
cd /main-source
colcon --log-base /review/build-log build --build-base /main-build \
  --install-base /main-install --executor sequential \
  --cmake-args -DBUILD_TESTING=ON -DCMAKE_CXX_STANDARD=17
source /main-install/setup.bash
colcon --log-base /review/test-log test --build-base /main-build \
  --install-base /main-install --executor sequential --return-code-on-test-failure
python3 src/mtc_trajectory_execution_cpp/test/verify_results.py --build-base /main-build
python3 /review-tools/probe_cpp_observed_v2.py /review/new-cpp-run --install /main-install
```

缓存镜像未随Git仓库发布；新环境须先按[既有环境准备证据](fsm-acceptance.md)核对驱动/SDK/依赖，不能把缺少镜像当作测试通过。以上命令在本机固定缓存环境可重跑；每个长步骤应使用冻结`harness/step.py`同样的有界监督，超时停止本轮容器。完整实际环境见`host/environment.json`，不修改宿主全局设置。主线未合入统一UI包，统一启动入口属于PR8，按其固定SHA独立构建/source后使用：

```bash
# 新容器 /pr8-source，按实际 pr8-build.sh 构建 /pr8-install；不与main任务并发。
source /pr8-install/setup.bash
export ROS_DOMAIN_ID=181 ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST
python3 -m mtc_cpp_mock_bringup.bringup --namespace /cpp_c1 \
  --output-dir /pr8-review/new-stack --result-delay-ms 700 --no-web
# 新终端，同容器同环境；ready.json须ok，核对唯一C++服务和参数。
ros2 run mtc_cpp_mock_bringup mock_task --namespace /cpp_c1 \
  --output-dir /pr8-review/new-client --cancel-at MOVE_PRE_ALIGN --cancel-delay-ms 400 \
  --goal '{"task_id":"new_c1_goal","mode":1,"ordered_colors":[1],"timeout_ms":30000,"placement_stability_sec":3}'
```

上述取消命令预期用于复现未通过项，不保证CANCELED。常规UI入口仍为PR8的`ros2 run mtc_cpp_mock_bringup mock_stack --namespace /mtc_cpp_mock --output-dir <新目录> --port 8767`；本轮没有新增浏览器验收，旧UI证据不冒充本次main能力。

停止时对实际supervisor发SIGINT，等待`cleanup.json`、子进程退出码和空图，再停止容器；不要只给外围`ros2 run`包装进程发信号。本轮C1外部脚本首次只给包装进程SIGINT，22秒未返回后对进程组TERM，包装进程-15；实际supervisor稍后cleanup=0、两个C++子进程0、空图。该失败保留，随后同命名空间直接supervisor启动/停止、无Goal重启检查通过，不重新执行C1。用docker cp收集日志/原XML/身份清单后停止keeper；最终两验收容器停止、无OOM，keeper137与ROS退出码区分。

如依赖检查、就绪、身份、终态或超时失败，保留原日志，不将ACK、CLI退出0、控制器到点或单次重跑通过改写为验收成功。运行前后保留`docker inspect/top`和源码哈希；本轮已停止的镜像/容器保留作本地证据。

## 证据和交付

本轮原始目录：`outputs/main-acceptance-20261013-b418515/`；[冻结索引](experiments/main-acceptance-20261013/index.json)、[协议](experiments/main-acceptance-20261013/protocol.md)、[输入](experiments/main-acceptance-20261013/inputs.json)、[结构化结果](experiments/main-acceptance-20261013/summary.json)。冻结 **1152个文件**，index SHA-256：`9e36fbd4ff15c9412ccdc95da63022d57eb6b2fb61bef13117cf1a54309ecfa9`。原始outputs、Git对象、二进制、缓存及本机实时配置不上传，按index显式纳入被忽略的证据。

验收前已验证23份旧索引、9260个成员、14份监测签收报告及旧C++/UI签收报告；本轮提交前再次核验；其中两份旧视觉runs格式只核验索引SHA，未展开其成员，9260为其余files格式的实际核验数。另一个会话于05:23UTC启动WebUI P0容器，早于本轮收尾但晚于M1发生的05:16UTC；它的容器、进程与webui改动保留在该会话工作范围。本轮仅声明自己的容器串行/已清理，不声称宿主没有其他负载。为避免混入另一会话代码，本轮使用独立工作树提交验收文档与冻结证据，目标为个人仓库origin/main。队友仓库源码未改，未新建修复PR；PR8仍是原待审提交。

OpenAI Codex协助隔离复现、外部观察脚本、分析与材料整理；内核/算法源码未改。第三方版本、许可证声明差异和SDK待核对项沿用事实索引，不重新授权；软件Mock/Fake结果不外推为完整FSM、真实标定、NUC部署或实机验收。
