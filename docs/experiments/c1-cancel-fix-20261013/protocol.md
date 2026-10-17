# PR #8 C1 修复验证协议

来源：USER-HW-20261013-03（用户会话）、TEAMMATE-CANCELFIX-20261013（固定 PR 候选），本机证据 ENV-CANCEL-FIX-20261013。

1. 从 PR #8 的 7da4322 建立独立工作树和 Jazzy 容器；保存原暂存区哈希与正式 pin，保持原冻结证据。
2. 原运行代码仅加入回归测试：确定性桥接和真实 PickPlace 延迟取消正例必须失败为 520，缺失证据反例通过。实际父子 Action 700/400 ms 重现 6/520，下一任务被拒。首次 supervisor CLI 包装退出问题保留；改为直接调用安装的 supervisor 后单列 baseline-clean。
3. 只新增 Mock 显式采样方法及 AsyncMockMotion 调用；保留 Core 和旧 StaleFeedbackCannotConfirmStop 负例。新增匹配 ID、缺证、未知/超时、倒退/非法时钟和真实 PickPlace 回归。
4. 按 logs/fixed-clean-build.log 完全重编两个受影响包；检查导出符号、二进制哈希和全部编译相关源码字节，再运行五包 C++ 测试。colcon 包装数与实际 gtest 身份分开统计。
5. 独立进程串行验证五档取消延迟 0/200/400/600/1000 ms（结果交付 700 ms，最后一档 1500 ms）。所有父子实际终态须 5/0、完成数 0；400 ms 后同栈新任务 4/0/1。缺证 6/520、未知状态 6/230，均拒绝下一 Goal。只根据实际 Result 判断，不由 ACK 推断。
6. 每个场景核验关联 UUID、唯一就绪图、自有进程退出与图排空；停止本轮容器。冻结失败、通过、源码补丁和测试身份；不修改旧证据。

使用 OpenAI Codex 协助分析、补丁、回归与冻结。Mock 采样不是实机停稳证据；未合并 PR 或推进正式 pin。
