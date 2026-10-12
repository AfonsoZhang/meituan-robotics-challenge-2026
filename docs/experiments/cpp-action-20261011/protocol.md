# Phase 2A C++ Action 候选复验协议

来源：ENV-CPP-ACTION-20261011；候选 TEAMMATE-ACTION-20261011，固定 SHA 见 inputs.json。USER-HW-20261011-08、USER-HW-20261011-09 授权隔离集成复验；原监测配置沿用 ENV-UPSTREAM-WAKE-20261011。

1. 本事件 ack 必须返回 CLAIMED；确认原 runner 已结束、原容器停止、summary 有结束/采集信息。读取真实 patch 和逐步日志，不能仅据固定 summary 作功能判定。
2. 校验原 index 的 290 个文件，保留原样；原 container 只用于创建独立 snapshot，不重新启动。新的补跑容器保持 network none、无设备/挂载/端口、2 CPU / 4 GiB、512 PID、ALL caps dropped、no-new-privileges。
3. 复用自动构建的正常候选。按新交付入口核验测试身份、新包 rosdep/XML；另在独立目录编译五个 C++ 包及接口的 UBSan 版本并测试，核对实际编译选项；外部 CMake consumer 验证导出接口。所有命令、开始/结束时间及退出码见 supplement/logs/，自动工具原命令见 automatic/summary.json。
4. 独立程序四场景使用 ROS domain 110–113 和本机发现；逐节点确认唯一 Action Server、发送关联 Goal/Cancel、保存实际 Feedback/Result。延迟 7 秒首任务、基础/保序三色、拒绝非法/并发/重复 ID、关联取消、缺失子服务器失败锁定、单点 Motion 及退出均为必查项。ROS 进程正常 SIGINT 退出且无残留节点才计场景通过。Mock 运动/稳定窗使用模拟时间，不作为物理证明。
5. 补跑不改上游源代码；原 verifier 的 16 目标限制不适用于新增包，保留原失败，使用交付新入口验证 20 个目标 / 358 个独立身份。不存在的可选六项 ROS 接线回归是 NOT RUN；不得按退出 0 写成通过。
6. 探针开发失败不覆盖：v1 保存 UUID 字节时 TypeError，未形成完整结论；字节显式转为 int 后 v2 原场景/断言重跑，记录见 supplement/probe-development-note.json。容器准备时的本地编排失败另存 preparation-note.json。
7. 结束前确认六次 Mock 服务器均退出 0，进程表只剩 keeper，再停止补跑容器，保存 inspect 并采集证据。原容器仍停止。故障、NOT RUN、真实/模拟边界分开报告。原始日志不删；原 source.bundle 仅记录 SHA，镜像、SDK、Git bundle、二进制不冻结入库。
8. index.json 以本目录相对路径列出每个常规文件的 SHA-256 / 大小（不含自身），其哈希由 materials/manifest.json 注册。automatic/original-index.json 是原 outputs 索引，含未复制 bundle，不是本冻结目录索引。日志目录的 latest 符号链接不复制，指向的实际日志完整保留。
9. 本冻结集保存主对话 ACK 和 pre-complete 门禁快照。来源登记、文档同步和清理全部结束后才调用 complete；最终回执在 outputs/moveit-watch-20261011/wake/sha-c0f70172e4b0271046d5f52813e0730d40ae772a/receipt.json，避免为写终态而改动已冻结证据。没有调用 queue 或另启监测。

使用 OpenAI Codex 协助编排、探针与分析。TEAMMATE-ACTION-20261011 的根 LICENSE / package.xml 许可差异原样保留；独立驱动/模型沿用 TEAMMATE-SDK-20261011，不重新授权或归档 SDK。
