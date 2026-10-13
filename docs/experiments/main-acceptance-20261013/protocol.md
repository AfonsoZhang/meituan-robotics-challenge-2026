# 主线及既有未通过项验收协议

用户会话 USER-HW-20261013：本次重新要求“验收”，随后确认“最新主线及既有未通过项（推荐）”。来源 TEAMMATE-MAIN-20261013；本地观测 ENV-MAIN-ACCEPTANCE-20261013。旧 Mac 终止记录、监测回执和冻结失败仍按各自日期有效，不回写旧记录。

固定 main b4185155383541e1a4161587c4049a162f74b36d。PR #8 的7da43228d602a6b23571bfc599d69529ef7bea23使用另一份源码/容器，仅诊断既有C1和直接启动/停止。未拼接分支，正式pin不变。主线327个跟踪文件、PR8的306个跟踪文件身份已归档；主线构建前后跟踪源码不变。当前源码及前后GitHub快照见inputs、host/source-comparisons及source。

两容器串行、Ubuntu24.04.5 x86_64/Jazzy/C++17，无网络、设备映射、宿主挂载及端口映射，2CPU/4GiB/512PID、cap-drop ALL和no-new-privileges。复用固定缓存依赖，不在线安装。主线使用全新/main-source、/main-build、/main-install；UBSan另用/main-ubsan-build/install；PR8使用/pr8-source/build/install。旧/candidate目录未用于本轮构建。初始化Git所有权检查曾失败，随后仅对该容器路径设置进程级safe.directory；保留原失败，没有改权限或全局配置。

先完整构建/测试并核对486个C++身份、269项Python，再对原ConcurrentGoalsSingleOwner、原DuplicateCancel和新增8项做40轮计划、每轮40秒上限、首败即停。实际第18轮1个断言失败，保留全部18轮XML/日志/命令，后续22轮不运行；这180次执行不是180个新增用例。UBSan独立重构建/测试，不覆盖普通或重复失败。TSan未运行，系统ROS/DDS/MoveIt未插桩。

再验15项离线E2E、6项ROS接线、54项标定离线测试；实际C++与Python Mock、原生Status/执行权门禁和独立MoveIt。C++只读观察器采集父子UUID、状态、Feedback、接收时刻、GetResult及进程身份，原观察器将反馈订阅节点误计为发送客户端，两个场景在Goal前停止；v2核对真实send_goal服务客户端，只补未运行的两项。没有更改上游接口/内核或降低检查。Python/MoveIt失败和统计线程报错照存。

原生Fake不注入Status心跳、不预热Goal、不放宽执行权：两种门禁均BLOCKED、零Goal。独立MoveIt执行成功不替代FjtMotionPort或完整FSM。PR8延迟取消仍6/520；外部ros2-run包装进程SIGINT后未返回、最终TERM的记录保留，之后仅启动无Goal的同命名空间复查，直接supervisor SIGINT及空图通过。不重跑C1以覆盖失败。

本轮容器与ROS进程均停止。另一会话的WebUI P0容器于05:23 UTC创建并保持运行，网络独立；本轮M1于05:16 UTC已发生。未触碰其进程或webui改动，不声称宿主整段无其他负载。本轮证据与文档在独立工作树提交。

runtime、pr8-runtime及host-logs保留原始运行字节，harness为实际外部验收工具，source为固定版本的最小源码见证。原始outputs、完整Git、二进制、缓存、CMakeCache及实时任务配置不上传；archive-selection列明排除项。index逐文件SHA-256，不含index自身。旧23份索引、9260个成员及14份签收报告在验收前核验，提交前再次核验。

OpenAI Codex协助独立观察、有界复现、分析和证据整理。没有修改FSM/Action/Cancel/Motion内核；缺陷交孙嘉明，集成与复验由张叔阳跟进。第三方源码版本和许可边界见inputs；不将软件Mock或Fake外推到实机。
