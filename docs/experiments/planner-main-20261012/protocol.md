# 规划 PR #3 主线合并事件验收协议

来源 TEAMMATE-PLANNERMAIN-20261012；观测 ENV-PLANNER-MAIN-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. 先 CLAIMED，再比较实际提交、父版本、文件内容及模式。f7eaa2c 的双父为 a04ac68 / 4a1a816，较主线增加 53 个原规划文件；整棵 Git tree 与前次验收 4a1a816 完全相同。复核 ENV-PLANNER-MERGE-20261012 的 486 文件索引和已签收报告；前次结果不改记为本次运行。
2. 审阅源码/交付 SOP 及固定运行真实日志。25 步起止/退出完整、305 原始文件哈希匹配、原 runner/容器已停止。14 包 / 387 C++ / 269 Python / 15 E2E / 6 ROS 通过；387 的每个测试身份与源码一致，分 318 核心、40 Action、29 Planner；colcon 685 含包装与 lint，不作独立功能计数。
3. 旧 C++ 审计要求 16 个程序而实际 20；在停止原容器的独立快照中补跑交付的新审计入口：358/20 通过，规划 29/4 另核对。两个包 rosdep 与五份安装文件逐字节身份通过。源码/默认配置/预算不变，无依赖安装或网络访问。
4. 原独立 MoveIt 规划成功，但 ExecuteTrajectory ABORTED / -4，日志明确内部 FJT ActionClient 尚未连接；此时外部探针可见唯一 FJT server。原控制器未收到 goal，未有最终误差测量。日志中加入 FJT 控制器至连接错误约 0.342 秒；外部服务可见不证明内部客户端就绪。
5. 仅做一次有界诊断：原探针复制到容器临时目录，隔离域 131，保留原 20 次 spin 后再用单调时钟 spin 5 秒。不修改任何上游代码、容差/控制/规划配置、状态预算或超时，不做自动重试。外层上限 210 秒、工具上限 180 秒，实际无超时。Plan→Execute / 关节反馈通过，MoveIt 仍 -11；单次成功只支持就绪时序假设，不证明固定等待可靠或缺陷已修复。
6. 两轮均无升级终止、move_group -11、control 进程 0；诊断结束检查发现域 131 ROS CLI daemon，守卫拒绝直接清理完成。保留首次进程快照，按该域停止 daemon，再核对仅剩 keeper，停止补跑容器。两个容器均停止、无 OOM、2 CPU/4 GiB/512 PID、无网络/设备/挂载/端口，cap-drop ALL/no-new-privileges。
7. 旧 Python 本次早 Goal 为 220、延迟 INIT 为 510、Cancel 受理后为 520 且完成 0；PickPlace create_client 与 Safety 清理失败保留。FSM/Action/Cancel/停稳内核记录回交孙嘉明。规划默认 TF/预算交常建烁，系统集成跟踪内部客户端就绪和退出；未代发外部消息或修复内核。
8. 没有新入口或运行代码，故不重复前次默认规划 SOP、C++ 独立四场景、UBSan/外部 consumer。前次默认 V1 42.0717 秒超过 24 秒、V2 TF_UNAVAILABLE 仍为历史未解除问题。新场景 30e3c6e、视觉 0e329f1 分支尚不在此快照，不将其新功能/测试记到此主线。
9. 冻结全部原失败、诊断、清理及 ACK/pre-complete 数据，index 不含自身；源 bundle/镜像/SDK/构建二进制不入库，版本与哈希留存。同步 manifest、正文、README、open-questions 与 derived_files 后才 complete；最终回执存 raw，不回写冻结集。原 60 秒轮询、固定主会话与上海 08:00 截止不变。

本轮仅独立 Jazzy Mock/Fake 软件验收，未推进正式 1d940f7 基线；完整 FSM、实际感知/工具/碰撞场景与 NUC/实机未验收。源声明 MIT/Apache-2.0 差异和 SDK 许可/厂商校验值保留。OpenAI Codex 协助只读源/测试身份核验、一次等待诊断、清理和事实登记；没有上游规划、FSM、Action 或驱动算法修改。
