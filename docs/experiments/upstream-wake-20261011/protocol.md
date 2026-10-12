# 自动唤醒主对话的验收协议与范围

本批为 ENV-UPSTREAM-WAKE-20261011，授权 USER-HW-20261011-09；沿用 USER-HW-20261011-08 / ENV-UPSTREAM-WATCH-20261011 的时段和隔离边界。

1. 检查旧监测 PID、状态、队列和固定工具；保留切换前配置/状态及旧冻结哈希。旧进程空闲时 SIGTERM 正常退出，使用同一输出目录及持久化状态启用新固定工具。旧工具、失败运行、原冻结证据不覆盖。
2. 30 项 unittest（其中新增 14 项）覆盖临时 Git、去重、串行回执、进程中断与恢复、失败/超时、传输重试和环境清理；测试传输为明确的替身，无真实聊天调用。完整日志保留。
3. 真实端到端另建本地 Git 候选副本，在已存在 PR 候选上新增三行 MoveIt 测试说明，不推送；初始化监测后提交，必须由实际 fetch/discover 入口触发。与正式监测相同的源码和工具哈希，真实运行既有隔离 runner。
4. 控制 12 秒超时，保留部分构建、依赖失败和清理结果。核验 network=none、无主机/设备挂载/端口、2 CPU、4 GiB、pids=512、cap-drop ALL、no-new-privileges；停止真实容器，不将受控中断记作功能通过或新的模块失败。
5. runner 结束后真实 codex queue 投递到固定主对话；清除 CODEX_THREAD_ID / CODEX_SESSION_ID，不创建其他会话。主对话忙碌时消息排队，当前实现轮结束后新回执轮开始；领取 CLAIMED、输出确切 ACK、支持的 read_thread 读回才算实际回执。队列返回 0 本身不算通过。
6. 主对话阅读实际 patch/summary/日志、写分析报告并 complete；确认报告哈希、门禁解除、一个事件/运行/投递，后续无重复。仅停止测试监测，正式上游监测继续运行。
7. 新证据单独冻结；README、计划、open-questions、监测说明及 manifest 双向索引同步。FSM/Action/Cancel 内核、正式锁定、实机范围未变，不自动联系队友或推进合并。

原始目录为 outputs/upstream-wake-20261011。source.bundle、Git 对象库、fixture 源代码副本和二进制不入库；source.bundle 哈希保留在原始 summary。嵌套 original-run-index.json 保留原 runner 索引字节，指向原始目录的完整文件集合；本冻结集合以本目录根 index.json 为准。

切换前、pre-ack 和实际运行的初始环境快照保持原状，因此可能写有旧工具哈希或待回执；最终实际工具哈希见 inputs.json 和 harness-v1-sha256.json，最终结果见 summary.json、完成回执及真实主对话消息提取。不是改写历史失败。

OpenAI Codex 协助编排、测试、实际回执和归档；未实现或修改上游规划或 FSM 算法。旧依赖来源沿用既有登记，不重新授权 SDK/模型。
