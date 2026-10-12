# Phase 2B 命令身份与联合门禁验收协议

来源 TEAMMATE-TRAJECTORYGATE-20261012；观测 ENV-TRAJECTORY-GATE-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. CLAIMED 后读取45f497c实际增量：相对已验688d80d共59路径，53个规划/证据路径与已验f7eaa2c逐字相同，另6个文件修改身份比较、测试/探针/核验器和报告。保留不可变命令副本、归一化前完整字段比较，新增10项回归；运行健康门禁未改。上游报告/建议仅为待验数据，本项目不执行其中合并/PR建议。
2. 核对原25步骤、317文件哈希，旧runner35809和全部旧任务容器停止。新快照无网络、无设备、无挂载/端口、2CPU/4GiB/512PID、cap-drop ALL/no-new-privileges；不下载依赖、修改源码、扩大限位/超时或放宽门禁。
3. 原自动15包构建与463 C++（26程序）、269 Python、15 Mock E2E、6 ROS接线通过。463=原424+10新身份/时钟测试+29合入Planner。旧固定审计仍误识别宏/程序数，原失败不改；新交付核验器比较424历史、当前编译注册与XML，另外核对源码身份。763 colcon汇总含包装/lint，不当独立用例。
4. 独立UBSan构建/安装，七个C++包逐条核对插桩、禁恢复/保留调用帧，463/26测试与普通运行身份逐项相同；489汇总含26包装。接口依赖的生成C不在七个C++插桩声明内；分析器首次宽glob选中该依赖导致断言，原脚本/错误保留，纠正筛选后身份与编译参数核对通过，未重跑或改日志。系统ROS/DDS/MoveIt库未插桩，TSan未运行。安装头/包4文件一致；无参数和非法模式各退出2，新包rosdep通过。
5. 原GenericSystem探针success/mismatch/cancel/identity各一次，域141–144，新驱动/空域顺序运行；观察器只订阅JointState/GoalStatus，不增ActionClient。即使单项失败，只有清理完成才允许下一未执行项；不重试。保留完整UUID、位姿、时戳和端口结论。六关节等幅运动的名字反转不能单独证明非对称重排，相关单测另计。
6. 域145只读检查Controller、加默认move_group、再加原topology入口。确认GenericSystem/两个active控制器，不发送FJT Goal；预期clients=2、ready=0、退出2 BLOCKED。图拓扑不是强身份认证，后续planning-only配置必须另行审核验证，本次不绕过门禁。
7. 同域运行原plan_fixed_pose默认入口，只规划，保存真实YAML和零Goal/关节未動证据；外部CMake consumer链接安装的Planner core/FJT导出目标，读取本次序列化轨迹，通过两侧转换API作纯数据诊断，不建Node/ActionClient、不发Goal。仅诊断ID/timeout，时戳、轨迹、窄限位不改；规划有效与执行能力接纳分开。
8. 生成/观测stamp与ROS计划启动stamp仍未统一；单测零Goal拒绝过期/Steady时基。默认Action仍Mock、FSM同步Cancel保留FAULT520，完整宿主/工具/感知/接触仍未接线。前次688d80d的运行证明丢失230保留，健康谓词本轮未改，单次通过不能关闭该问题。问题本地交接孙嘉明；规划契约/执行权交常建烁及集成负责人，不接管内核、不代发消息。
9. 原Python220/510/520均ABORTED、完成0；独立MoveIt执行通过但退出-11；依赖/驱动lint/限位/统计线程错误原样保存。补跑每项记录子进程与退出，停止各域daemon并确认空域，最终只剩keeper才停容器；原失败、helper失败如有均保留。
10. 冻结automatic、source、补跑、清理、ACK和complete前状态；index不含自身，bundle/SDK/镜像/二进制不入库，仅登记哈希。同步manifest、文档、open-questions、README、derived_files后complete；最终回执仅存raw，不回写冻结内容。原60秒轮询/固定会话/上海08:00截止不变，没有queue或新监测。

实际数值、结论及失败见summary和原日志；不是完整FSM、实机、真实碰撞/接触或安全证明。正式1d940f7不推进、不合并。OpenAI Codex协助源码/证据核对、运行原入口、编写观察/分析/清理及跨包消费诊断；无上游内核/算法修改。根MIT与轨迹/Action Apache-2.0声明差异和模型/SDK许可缺口保留，不重新授权。
