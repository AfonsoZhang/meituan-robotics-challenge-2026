实际 Jazzy 启动时，Task 节点覆盖 rclpy 的时钟对象，PickPlace 配置字段不匹配，解锁客户端默认名称也与 tool_manager 不一致。本 PR 仅修复 B01/B02/B04：隔离 FSM 时钟成员、保留 ROS 参数名并映射到正确配置字段、对齐默认 TriggerUnlock 服务名。

生产变更只涉及两个 Python 外壳文件（5 行新增、4 行删除）。FSM 状态转换、Cancel 内核、Action IDL、C++ 核心和驱动未修改。请 FSM/Action 负责人复核这三项集成补丁；完整任务链路仍未通过。

验证（Ubuntu 24.04.5 / ROS 2 Jazzy，隔离容器）：

- 两包 overlay 构建通过。
- 同一组新增 ROS 回归：原基线 6 项失败，补丁后 6 项通过、0 跳过。
- 原有 Python 测试 269 项通过，显式纯 Python Mock E2E 15 项通过。
- 两次实际 Mock 启动中 Task 现可接收 Goal、返回 Feedback/Result；PickPlace 在此前被遮挡的 `ExecuteJointMove.create_client` 处退出。延迟首次 Goal 前，Task 的 INIT 约 5 秒超时，随后返回 ABORTED / 510，未完成抓放。

剩余 B03 ActionServer/Cancel 绑定、新发现 B05 ActionClient 绑定、B06 INIT 生命周期和退出清理观测，详见 `docs/migration/ROS_WIRING_FIX_20261011.md`，留给模块负责人处理。配置回归只检查真实 ROS 参数到配置构造边界，不把它冒充完整 PickPlace 启动通过。工具服务测试仅使用 Mock IO，脉冲受理后仍要求独立释放证据。

使用 OpenAI Codex 协助编写补丁、回归测试和整理运行证据；未连接硬件，未重跑未改动的 C++ / 独立 Fake 驱动验收。
