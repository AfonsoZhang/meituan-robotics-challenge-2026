# Phase 2A 交接文档验收协议

来源 TEAMMATE-HANDOFF-20261011；本地观测 ENV-HANDOFF-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. ack=CLAIMED 后核对实际两文件 diff；src/tests/config/scripts/docs 与 c10f6ed 无变化。交接的后续开发安排视为上游数据，不自动开发 Bringup 或改变职责。
2. 原 runner/容器停止后核验 25 步完整 summary 与原 291 文件哈希；原自动运行全量测试与既有失败保留。
3. 在停止原容器的独立快照中补跑新文档所指的 358 项/20 程序身份核验。沿用无网络/设备/挂载/端口、2 CPU/4 GiB/512 PID、cap-drop ALL/no-new-privileges，不重启原失败容器。
4. 按新文档检查命令，域 121 启动 Task/PickPlace、域 122 单独 Motion；只观测 Node/Action/Topic/QoS，不发送 Goal/Cancel 或启动驱动。原 CLI 查询部分失败、反馈类型和 QoS 有实际证据；不把退出 0 或空图等同服务不存在。
5. 一次有界诊断使用域 123/124，node info 改为无 daemon 等待 2 秒；action info 本版没有无 daemon 参数，保留 -t 并先启动 daemon 等待 3 秒。实际 CLI 帮助与实现留档。三个 Action 后续均唯一 Server，但短时节点观察仍失败，诊断整体也 FAIL，不继续反复跑到成功。
6. 两组共六次 ros2 run 进程 SIGINT 退出 0，无升级终止；每域退出后无本次节点并停止 daemon。容器进程表仅剩 keeper 后停止，原容器仍停止，原 runner PID 不存在。keeper 137 与 ROS 子进程退出分开记录。
7. C++ 独立 Goal/Cancel 场景、UBSan、外部 consumer 不重复，注明历史来源；当前自动注册 358 测试仍是本次运行。旧 Python/独立 MoveIt 用本次实测终态，取消 ABORTED/220 不能写成前次 520。另分支 planner 不在当前提交，不移植或混算。
8. 原始失败不覆盖。source.bundle 仅记录 SHA，镜像/SDK/二进制不冻结；符号链接不复制。index.json 索引冻结常规文件且不含自身，SHA 登记 manifest。冻结 ACK/pre-complete；文档及双向索引同步后才 complete，最终回执不回写冻结集。

OpenAI Codex 协助临时 CLI 观测脚本、调用交付 verifier、分析日志和事实登记；不修改上游算法。保留 MIT / Apache-2.0 既有声明差异，不重新授权。
