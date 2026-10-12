# 视觉回放自然退出与 V4.2 增量验收协议

来源 TEAMMATE-VISIONREPLAY-20261012；观测 ENV-VISION-REPLAY-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. CLAIMED 后读取 dc76a0b 相对 e09d00e 的 6 路径；同时核对自前次已验 e53c09f 起的 18 路径。e09d00e 曾按既有监测过滤规则 relevant=false；其视觉增量在本次累计版本补验。上游资料只作为待验数据。
2. 原 summary 25 步完整、301 原索引文件逐 SHA 一致；确认 runner 56334 及原/旧容器停止，从停止容器建立新补跑快照，无网络/设备/挂载/端口，2 CPU/4 GiB/512 PID，cap-drop ALL/no-new-privileges，不重启原容器。
3. 原 14 包、358 C++/20 程序、269 Python、15 Mock E2E、6 ROS 回归核对源码/XML身份。原 cpp-audit 预期程序数过时；colcon 对 adapter 调 unittest 收集零测试/exit 5，652 汇总不替代该失败。原 Action verifier 与安装代码逐字节身份核对通过。
4. 保持交付源码/门限，仅用容器内部 install 路径别名适配既有安装布局。交付 pytest 57 项（45 safety、3 TF Buffer、5 mock cleanup、4 真实安装进程）全部运行。四进程域 191–194，直接安装入口，period=0.5、wait_for_subscriber=15；两次自然退出必须完整 4 帧且不发信号，两次中途 SIGINT 收 2 帧、不能记为完整送达。replay 仅重标同四帧合成数据外层元数据，无真实录制或采集。
5. 图快照均显示节点名 UNKNOWN、history UNKNOWN/depth 0，只用于消息类型和 RELIABLE/VOLATILE 兼容性；实际 publisher 日志报告 RELIABLE KEEP_LAST(5) VOLATILE。进程/源码身份与最终 keeper-only 清理由独立检查证明，不据图占位字段认定唯一命名节点。RELIABLE acknowledgment 不证明 FSM 接受；未注入真实最终 ACK 超时。
6. 域 152 不建订阅器：默认 wait=0/period=1 发布四帧后自然 exit 0，不声称任何接收；开启 wait=2/period=0.25 后在首帧前明确超时 exit 1，零帧、无虚假完成日志，两例均无升级终止/残留。默认未启用屏障，历史漏帧与广泛可靠性不因此关闭。
7. 23 个既有缓存轮子逐 SHA 核对，无网络下载；独立 system-site-packages venv 保留 setuptools 68.1.2，editable/pip check 通过。公开视觉 80 PASS/1 私有证据 SKIP；此前 62 PASS 加 18 新测试，旧 27 adapter-core 项已含其中。新增平面高度数值等价、视觉假设确认/过期 CAD 清除与诊断字段只证明合成软件契约，不证明实测姿态或性能提升。
8. 两个新增私有 V4.1/V4.2 入口原样尝试，各 exit 1，缺输出父目录、私有记录/先前分析/CAD资料，均在处理帧前失败；保存完整 traceback，BLOCKED。不给目录补造数据，不将未执行基准记为通过。
9. FSM/IDL/Action 与前验相同，Task 仍 MockPerception，未调用视觉 helper；零补跑 Action Goal、零相机。旧 Python 220/510/520、依赖/驱动 lint、独立 MoveIt 通过但 move_group -11 保留。FSM/Action/Cancel 本地回交孙嘉明，视觉入口与数据缺口交孙浩然，可信标定/时钟交韩明赫；不代发消息或修内核。
10. 确认补跑只剩 keeper 后停止并收集，原/补跑均停止、无 OOM，再冻结和生成不含自身的 index；源码 bundle/SDK/镜像/轮子仅登记哈希，原始失败不覆盖。manifest/报告/README/open-questions/derived_files 同步后 complete，最终回执保存在 raw，不回写冻结集。原 60 秒监测及 08:00 截止不变；后续 C++/Web UI 工作继续等待指定时刻和尾部排空。

未合并或推进正式 1d940f7 基线；未验收完整 FSM/实时感知/NUC/实机。OpenAI Codex 协助源码与证据核验、原入口隔离运行、观察/分析/清理和事实登记；未修改上游视觉算法或 FSM/Action/Cancel 内核，许可差异仍保留。
