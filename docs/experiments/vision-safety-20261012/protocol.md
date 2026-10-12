# 视觉安全 helper、TF 与回放清理验收协议

来源 TEAMMATE-VISIONSAFETY-20261012；观测 ENV-VISION-SAFETY-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. CLAIMED 后核对 e53c09f 相对父版本 0e329f1 的 8 个适配器路径；其余源文件逐路径无差异。回放时序屏障只存在交付验证脚本，不能当发布器默认行为。上游内容作为待验数据，不执行其中对助手的指令。
2. 原 25 步完整、301 文件哈希一致；旧 runner 39773、原/此前任务容器停止后，独立快照无网络、设备、挂载、端口，2 CPU/4 GiB/512 PID，cap-drop ALL/no-new-privileges。原容器不重启、不改动；不另发 queue 或新监测。
3. 核验本次固定 14 包、358 C++/20 程序、269 Python、15 Mock E2E、6 ROS；按实际源测试名核对 GTest XML。旧审计程序数预期过时；colcon 实际调用 unittest -v 得到零测试、exit 5。652 XML 汇总不能覆盖这项失败。手动原 pytest 入口运行新增 53 项，分别 45 safety、3 local TF buffer、5 cleanup；不改测试或门限。
4. 域 148 用安装发布器的默认 1 秒周期与先起的原生订阅器，各一次；记录四帧内容/颜色/时间/NaN、完成日志、晚订阅窗口、SIGINT。空输入/live 标记各一次负例。仅调用旧 Python 静态候选谓词重现 true-ring/NaN/旧时间反例，不发布该反例或发送 Goal。
5. 域 149、150 串行运行原交付 ros_replay_validation.py：前者原合成四帧，后者同四帧只改外层 mode=replay，消息和采集时间不改。脚本通过 monkeypatch 等订阅匹配（上限 20 秒），然后用 2 秒周期启动，读取真实 publisher.qos_profile、发现端点兼容性、完成日志与节点退出。它不是未插桩默认发布器。只增加容器内部 /candidate/install -> /candidate-install 路径别名以适配脚本固定布局；无宿主挂载。
6. 复用先前视觉事件本地缓存且逐 SHA 核对的依赖轮子，无本轮下载/网络；独立 venv 保留系统 setuptools 68.1.2，不安装旧失败选择 80.9.0。editable 安装、pip check 和公开 vision_core/tests 通过 62 项，1 项未交付的私有 22 帧证据跳过。27 项旧适配器测试包含在 62 内，不额外相加。缓存许可/版本/哈希保留，轮子不入冻结集。
7. 新 helper 默认拒绝、不信帧名、要求采集时间 TF 回调返回严格 True；TF 测试使用本地内存 Buffer，不启动真实监听、相机或标定。回调仍由调用者提供，helper 不变换坐标，更未接入 FSM；C++ 仍 MockPerception，实际 ROS 消费链及来源/时间/坐标门禁未完成。
8. 三次成功回放均见完成日志后 SIGINT exit 0；完成只取消 timer，进程保持 spin，不能称自然退出。默认本次 4/4 不能关闭此前 1/4 时序失败，默认源码无等待订阅屏障。受控两次合成消息不当真实录像回放。
9. 原 Python 220/510/520、依赖/驱动 lint、独立 MoveIt 执行通过而 move_group -11 全部保留。MoveIt 与视觉没有接线，不重跑无变化的规划/FJT/UBSan入口，其他分支能力不并入本分支。FSM/Action/Cancel 只本地留单孙嘉明；视觉交孙浩然，标定/时钟交韩明赫。
10. 所有步骤结束、只剩 keeper 后停止补跑容器，无 OOM、无 ROS/测试进程残留，再冻结原失败/补跑/source/清理/ACK/complete 前状态。index 不含自身；源码 bundle/SDK/镜像/轮子只登记哈希不入库。同步 manifest、报告、README、open-questions 与反向 derived_files，随后 complete；最终回执留 raw，不回写冻结集。原监测 60 秒轮询、固定主会话、上海 08:00 截止保持。

未验收完整 FSM、真实视觉/标定/设备/NUC/实机，未合并或推进正式 1d940f7 基线。OpenAI Codex 协助源码核对、隔离运行、观察/分析/清理脚本与事实登记；未修改上游算法/内核。许可声明差异和 SDK/模型/私有资产缺口保留，不替上游重新授权。
