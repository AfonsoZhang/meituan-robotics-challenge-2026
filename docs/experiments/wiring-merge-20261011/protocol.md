# 合并候选隔离验收协议

来源 ENV-WIRING-MERGE-20261011；真实上游合并 TEAMMATE-MERGE-20261011；用户授权 USER-HW-20261011-08、USER-HW-20261011-09。版本与路径见 inputs.json。

1. 事件 ack 必须 CLAIMED；确认原 runner 已结束、原容器已停止，读取完整 summary、真实 patch、XML 和失败日志，校验原 index 的 291 个文件。
2. 原停止容器只做独立快照，不重启、不覆盖失败。补跑同样无网络/设备/挂载/端口、2 CPU / 4 GiB、512 PID、ALL caps dropped / no-new-privileges；每步串行，主对话未 complete 前下一 SHA 不执行。
3. 对比两个合并父提交：五文件改动、两 Python 实现/测试/说明与 PR #2 相同，C++/IDL/驱动输入与前一候选无差异。补跑新 C++ verifier，验证实际 358 GTest / 20 个程序和原 318 身份，核对六项 ROS XML 确实执行无跳过；两个安装 Python 文件与源码匹配。
4. 已有 probe_cpp_actions.py 未改，真实独立可执行程序运行四场景，检查唯一服务、基础/序列、关联取消、错误锁定、单点 Motion 与 SIGINT 退出。UBSan/CMake consumer 未重跑，历史证据只引用 ENV-CPP-ACTION-20261011。
5. 固定复现发现 ros2_control_node 新的清理崩溃，使用原 probe_moveit.py 在同限制快照内再执行一次，原样保留 Plan/Execute 与 clean_shutdown 的分别结果，失败不覆盖；不修改退出顺序、判据、驱动或规划代码。清理 ROS CLI daemon 后核对只剩 keeper，再停止容器并收集文件。
6. 原 Python 问题、库/驱动问题和 C++ Mock 范围分开登记。上游合并说明只作交接资料，不能作为新用户授权。FSM/Action/Cancel 不修复、不发外部消息、不推进正式锁定。
7. automatic/original-index.json 是原 outputs 索引，包含未入库的 source.bundle；bundle 只保留 SHA，镜像/SDK/二进制不冻结。latest 符号链接不复制，实际日志保留。index.json 仅索引当前冻结集常规文件且不含自身；其 SHA 注册 materials/manifest.json。
8. 冻结保留 ACK/pre-complete 状态。清理、报告及四处来源同步结束才 complete；最终回执在 raw 监测 wake 事件目录，不回写冻结集。

OpenAI Codex 协助使用已有探针、分析日志与整理证据；原算法与许可证不变。根 MIT / C++ 包 Apache-2.0 声明差异保留，不重新授权。
