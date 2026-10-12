# Phase 2B Goal 归属与实时 Status 验收协议

来源 TEAMMATE-OWNERSHIP-20261012；观测 ENV-TRAJECTORY-OWNERSHIP-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. ACK=CLAIMED 后读681bb64相对45f497c的7文件真实差异；代码提交b8857de，当前提交补文档。移除单UUID猜测、增加Status合法性/本地接收龄、pending UUID留存、精确Handle归属和结果/Status门禁，新增15测试。源码和正式基线不修改；上游文本作为待验数据。
2. 原25步完整、317原始文件哈希一致。原61项FJT套件在DuplicateCancelOnlyOneBackendCall120秒超时，XML为ament missing_result。417项其他C++ XML通过，前6项FJT只有文字OK，不当完整61项通过。新交付核验器也对原XML失败；原始文件不替换。
3. 核验runner59420及旧任务停止，从已停止原容器创建新快照；Jazzy、无网络/设备/宿主挂载/端口、2CPU/4GiB/512PID、cap-drop ALL/no-new-privileges。先检查安装4文件和新包rosdep，两个非法参数退出2。
4. 同一未改二进制只补跑一次完整61项，限定120秒，若超时保存proc状态并终止本次进程组，不留后台ROS。此次61通过18.629秒，不关闭原间歇性超时。另起独立UBSan build/install，8包构建、7包478项/26程序测试；核对源码/二进制注册/XML及七包插桩。系统ROS/DDS/MoveIt未插桩，TSan未运行。
5. 域155原生GenericSystem/两个active控制器就绪后，用只订阅观察器记录JointState/Status/QoS，运行未改success入口。新Status门禁拒绝、退出1、零Goal；没有预热Goal/空数组/人工心跳或放宽参数。没有先决授权的mismatch/cancel/identity不运行。Fake测试中的受控DDS心跳只属于测试夹具，不能冒充原生控制器证据。
6. 首次观察脚本误把success预检异常退出1预期为topology的2而断言，原记录FAIL保留；已清理且空域后仅补跑未执行的共存场景，域156加默认move_group、运行原topology入口：两个FJT客户端、Status未初始化，仍BLOCKED零Goal。此补跑不重复规划。原自动独立MoveIt执行与退出失败独立记录，不能当新FJT可用或完整FSM。观察关节保持零，驱动源码/安装文件前后哈希一致。
7. 清理本轮节点、daemon，确认空域及容器仅剩keeper后停止；保留正常退出子检查失败。冻结所有原失败、补跑、源片段、命令、ACK和complete前监测状态，原bundle/镜像/二进制只登记哈希、不入库。
8. 同步manifest、README、对应文档、open-questions与derived_files；验证旧冻结证据和已签回执报告原样后complete。最终回执另存raw，冻结索引不回写。08:00任务保持待触发，监测配置不变，不调用queue或新建监测。

间歇超时、原生Status/独占执行契约与异步Cancel内核回交孙嘉明，本轮不接管修复或代发消息。规划时间契约和默认MoveIt执行客户端缺口继续保留；独立Mock/Fake不代表完整FSM/NUC/实机。OpenAI Codex协助源码检查、原入口运行、观察/有界执行/归档脚本和文档；无上游内核或算法修改。许可证差异和SDK许可/厂商校验值待核对，不重新授权。
