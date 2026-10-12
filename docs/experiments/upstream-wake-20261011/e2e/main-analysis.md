# 主对话端到端回执分析

观测：ENV-UPSTREAM-WAKE-20261011。用户授权：USER-HW-20261011-09。

主对话于 2026-10-11T11:58:04.389923+00:00 领取本事件，ack 返回 CLAIMED，实际输出 MOVEIT_WAKE_ACK_3c392fa680d4687280a3e289dbce1c2d；已用支持的 read_thread 工具在指定主对话中读回该助手消息（见同目录 main-thread-receipt.json）。队列首次投递成功，未重试；该回执来自排队消息触发的新执行轮。

实际变更只有 docs/moveit-wake-acceptance-fixture.md 的 3 行新增文本。本地 SHA 为 8a4f99632354642786e856788466a03984844075，父提交是现有 PR 候选 1d3dccf23c53d299d457564daeb6438190ea2d77。没有功能源码变化，没有推送，不能计为孙嘉明的新交付。

监测真实发现提交并调用既有隔离复现脚本。容器 mtc-repro-0b5df45920d5-8a4f99632354 的 network=none、无设备/挂载/发布端口、2 CPU、4 GiB、pids=512、cap-drop ALL 和 no-new-privileges 已核对。测试人为限制 12 秒；在构建阶段触发 SIGTERM，监测终态 TIMEOUT/124，runner 记 INFRASTRUCTURE_OR_HARNESS_ERROR 和 Runner interrupted by signal 15。build.log 有启动记录，但阶段被打断，不能把缺少完整 build 结果记为通过。stop/collect 命令均为 0，容器已停止且 OOMKilled=false，keeper 退出 137；与历史 MoveIt move_group -11 问题无关。

独立保留的真实依赖错误为 mtc_manipulation 的 ament_python 无 rosdep 定义，dependencies 退出 2；日志末尾 All system dependencies have been satisfied 不覆盖前面的非零退出和错误。该问题在此前资格检查中已存在，不由这份测试文档引入，不在本轮修改上游。

本次触发→领取 291.301 秒，队列受理→领取 265.288 秒；主要包含主对话继续实现和切换监测的忙碌时间，当前执行轮结束后自动进入回执轮。这不是空闲主对话延迟测试，也不沿用侧对话所报约 5.4 秒。

结论：真实 Git 发现→隔离 runner→受控超时与清理→固定主对话队列→实际助手回执通过。功能构建/ROS/MoveIt 检查在本轮有意截断，不形成新功能验收结论；按测试范围不额外启动 ROS/MoveIt。主对话完成此分析后提交 complete，再核对门禁解除和单次派发；正式上游监测保持独立运行。

没有触碰 FSM/Action/Cancel 内核、正式基线、NUC 或实体设备。旧失败证据保持原状。生成式 AI：OpenAI Codex 协助实现、执行和撰写本验收分析。
