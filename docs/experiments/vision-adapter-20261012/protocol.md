# 视觉源码迁移与 ROS 回放适配器验收协议

来源 TEAMMATE-PERCEPTION-20261012；观测 ENV-VISION-ADAPTER-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. CLAIMED 后审阅实际 111 文件增量：9 个适配器文件、102 个视觉核心文件。其余源码/IDL 与 main 父版本一致；本分支没有规划包，不把前次场景版本结果移记此分支。
2. 核验自动 25 步、301 原始哈希与已停止原 runner/容器。14 包构建及 358 C++/269 Python/15 E2E/6 ROS 成功；colcon-test 的适配器零测试退出 5 保留，不能用成功 XML 掩盖。
3. 补跑使用停止原容器的独立快照，保持无网络/设备/挂载/端口、2 CPU/4 GiB/512 PID、cap-drop ALL/no-new-privileges；所有入口串行。无相机/Task Goal/运动命令，原安装 ROS 发布器保持不变。
4. 源码新增测试 test_ros2_p0 单独 27 通过、1 私有数据跳过；全视觉测试原环境缺 cv2，保留 collection error。主机下载锁定二进制轮子并记录哈希/许可元数据，再复制至无网络容器。隔离 venv 中初选 setuptools 80.9 与现有 colcon <80 冲突，原 editable 安装失败；PEP517 只解除安装错误，版本冲突仍留。恢复自带 68.1.2 后两条 editable 入口和 pip check 均通过，无上游修改。
5. 公开视觉 62 通过、1 私有 22 帧证据跳过；初始/最终环境两次通过不累加，27 个 adapter 测试包含在 62 内，不等于私有 215 套件。两相机脚本只 --help；生成器产生 16 帧/50 候选严格 JSON，均不可用于运动，真实 replay 0 帧单列。
6. 实际 Jazzy 生成消息/安装发布器/DDS 订阅：域 129 默认 period_s=1，发布 4 帧但只收到最后 1 帧；不得改写为默认通过。一次域 130、period_s=5 的有界诊断收齐 4 帧，逐字段验证颜色/ID/旧时间戳/帧/null→原生 NaN，未改输入、算法或时间戳。匹配就绪的具体根因未定。
7. 图发现实际确认唯一消息类型、RELIABLE、VOLATILE；history UNKNOWN/depth 0，KEEP_LAST(5) 仅记源码配置。默认已看到 replay complete 后仍 spin；诊断末帧后只观察 1.5 秒，尚未到下一 5 秒完成 tick，其原探针 no-loop 标签只能覆盖该窗口。两次 SIGINT 均 shutdown 重复退出 1，无升级杀进程。
8. 默认实测两个负例（空记录/live mode）明确拒绝。收到的 ring=false NaN 候选被现有 Python 静态谓词拒绝；将 flag 人为改 true 的 NaN/旧时间候选被该谓词接纳，只作函数级反例、不发布、不建 Task Goal。C++ 仍 MockPerception、Python 只有注入 provider，无真实 topic 消费链；JSON mode/body_valid 也不在 IDL 中，不能声称完整输入门禁通过。
9. 私有 CAD/真实数据、物理四色/位姿/ID 精度、标定、实际接触/运动均未运行。上游配置 explicit_official/map_calibrated 标签不升级为项目规则/实测事实。根 MIT 与新适配器 Apache-2.0 声明、移植来源/私有许可待核对。
10. 所有进程结束仅剩 keeper 后停止容器，确认原/补跑停止、无 OOM、原 PID 不在。冻结原失败、脚本、初始/最终环境、数据/源码及 ACK/pre-complete；wheel/SDK/镜像/bundle 不冻结，保存版本与哈希。index 不含自身。同步文档四处和 derived_files、核验后 complete，最终回执仅存 raw。

OpenAI Codex 协助验收探针、有限环境诊断、数据核验与事实登记；自身调用参数、wheel 元数据与分析假设错误保留在 harness notes/原日志，未归咎上游算法。视觉问题本地交孙浩然，FSM/Action/Cancel 内核与消费门禁交孙嘉明，标定交韩明赫；未代发消息、queue、新监测、合并或推进基线。
