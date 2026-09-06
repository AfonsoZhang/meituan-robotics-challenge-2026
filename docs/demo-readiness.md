# 仿真 demo 录制评估

后续实现更新（2026-09-07）：已补齐单块运行、录像和数据记录入口，实际完成黄块 → P1 录制并生成误差图；结果及新增验证边界见 [单块 demo 实录](demo-recording.md)。以下保留录制前的审计状态，不能将其中“未录制”理解为后续仍未完成。

整理日期：2026-09-07；核查资料与实验记录日期：2026-09-06。本轮读取本机代码、轨迹与 STL，检查队友仓库及视频抽帧、PolyU 官方职位页；**未重新执行本项目抓取实验，也未录制新视频**。既有实验成绩与本轮静态复算分别标明。来源登记于 `materials/manifest.json`。

结论：已有成果足以准备工程原型 demo。队内展示优先录单块被动钩搬运与舌规试配；RA 申请优先呈现轨迹执行、约束与定量失败分析。三块序列仍不稳定，视觉定位尚未接入抓取执行，不能称为稳定的视觉闭环抓取系统。

## 1. 与队友 demo 的关系

核查主仓提交 `b2981c5a152002dd2ce7788f19f625bf8c0a270c`；视频归档仓库提交 `7c0891123c1562b3bcf69815cb92f18fc31a4002`。两条视频哈希与归档验收文件一致；序列视频抽看九个时刻，基础视频解码检查通过，没有逐帧人工审阅全部动作，也没有在本机重跑队友代码。

| 方面 | 队友实现 | 本项目现状及展示价值 |
| --- | --- | --- |
| 平台 | S3、腕部 D435i；ROS 2 Humble、Gazebo Harmonic、MoveIt 2 | 同样 S3、D435i；Gazebo Classic 11，自写 IK 与胶囊近似碰撞检查。可交流接口，插件不可直接照搬 |
| 感知输入 | 相机出图，但规划读 `/simulation/ground_truth` | 已有独立 RGB-D 颜色定位回归；抓取仍按固定设计坐标，尚未连接视觉输出 |
| 末端保持 | 半圆锁扣概念；对准检查通过后创建 fixed joint | 完整被动钩通过接触提举，不使用物体附着插件；能展示钩取与滑脱这一不同问题 |
| 展示与复现 | 固定总览、腕相机小窗、阶段/仿真计时；每次运行有快照、轨迹、接触与 summary | 场景和历史实验已具备，录像、持续显示、稳定运行入口尚待整理 |

依据：[主仓 README](https://github.com/CHANGJianshuo/meituan_challenge/blob/b2981c5a152002dd2ce7788f19f625bf8c0a270c/README.md)、[接口约定](https://github.com/CHANGJianshuo/meituan_challenge/blob/b2981c5a152002dd2ce7788f19f625bf8c0a270c/docs/architecture/INTERFACES.md)、[fixed joint 实现](https://github.com/CHANGJianshuo/meituan_challenge/blob/b2981c5a152002dd2ce7788f19f625bf8c0a270c/src/mtc_simulation/src/simulation_system.cpp#L81)。

队友归档序列视频长 38.36 秒，对应 summary 中任务仿真时间 37.544 秒、运行墙钟时间 409.406 秒。因此不能把视频长度当作本机实时执行性能。三块中心误差约 0.018 / 0.010 / 0.045 mm，来自真值输入与固定连接假设，不能直接与本项目被动钩的毫米级误差排名；一个成功运行也不是重复成功率。[视频](https://github.com/CHANGJianshuo/gap-gazebo-lab/blob/7c0891123c1562b3bcf69815cb92f18fc31a4002/legacy/meituan_challenge/data/videos/sequence_demo.mp4)、[原始 summary](https://github.com/CHANGJianshuo/gap-gazebo-lab/blob/7c0891123c1562b3bcf69815cb92f18fc31a4002/legacy/meituan_challenge/data/runs/sequence_demo/summary.json)。

协作前应对齐两个假设：队友模型电池质量为 0.4 kg，而 FAQ p5 为 200–250 g，本项目仿真取 0.225 kg；队友仍记录内圈完整包含不可行，本项目已按用户转述组委会答复采用主体投影交集占比 ≥70%（USER-RULE-20260906-02，无 PDF 页码，历史 RULES p4 差异保留）。[队友假设文件](https://github.com/CHANGJianshuo/meituan_challenge/blob/b2981c5a152002dd2ce7788f19f625bf8c0a270c/config/scenario_assumptions.yaml)、[本项目规则摘要](rules-summary.md)。本轮没有向队友发送消息。

## 2. 舌规究竟能证明什么

已直接读取 `/mnt/c/Users/afonso/Downloads/钩具舌规_44x5x5_v1.stl`，SHA-256：`db7dd06d5c1b141294fb33e5735a26e10531c1e9eee8e1852c9b23360924d9f7`。它是舌规，不是完整装机钩具。

| 几何 | 本轮 STL 核验 |
| --- | --- |
| 整体包络 | 90×44×10 mm；X −40…50、Y −22…22、Z 0…10 |
| 功能舌 | X 0…50，50×44×5 mm |
| 上翘尖 | X 45…50、Z 5…10，5×44×5 mm |
| 手持段 | X −40…0，40 mm 延伸 |
| 网格 | 28 三角面、16 唯一顶点、42 边；每边两面且绕向相反；封闭体积 20.9 cm³ |

STL 本身不携带标准单位；这里按历史导出说明的 mm 解释。功能段与 `~/aubo_ros2_ws/src/meituan_sim/urdf/hook.urdf.xacro` 的 50/44/5/5 参数一致。仿真另有 150 mm 钩柄、固定连接与 TCP，使用盒体几何，**没有直接加载此 STL**。网格封闭和尺寸一致不证明打印件承载能力。

已有实验记录：完整被动钩可提举并搬运电池，单块落点误差 3.5 mm；六次序列重复中黄→P1、绿→P2 各 6/6，蓝→P3 仅 2/6。内框覆盖率分别约 84%、77%、成功时约 77%。这些是 [2026-09-06 实验记录](simulation-plan.md)，本轮未复跑，也不是完整赛事评分。

44 mm 舌宽在名义 50 mm 孔内只剩每侧 3 mm 余量。历史记录指出窄舌侧滑、宽舌插入对准困难，并将蓝块失效与 4–6 mm 运动跟踪误差联系起来。现有证据支持把滑脱作为主要失效解释；仍应以同步记录的相对位姿、接触与跟踪误差进一步验证因果。**视觉定位精度 0.8–1.9 mm 不等于插入总误差小于 3 mm**：还有控制、姿态、外参及工具误差，单次视觉预校正不能保证消除运动中的跟踪误差。模型近距离深度也受裁剪限制，不能直接承诺在穿钩位置连续 RGB-D 伺服。

向队友最有说服力的组合是：尺寸对照 → 侧面完整拍到穿孔、承托、卸载、清尖、退出 → 单块搬运 → 重复统计和失败样本。再补打印舌规对真实电池的试穿及卡尺读数，才能验证实物尺寸链。真实提手强度、打印材料与层间强度、摩擦、装机连接、动态抗滑脱仍待验证。历史会话中用户已说获得实物，但当前未见试穿测量结果归档。

## 3. PolyU Part-time RA 的适配程度

职位 260904015 属康复治疗科学系，2 名 Part-time Research Assistant，各聘 2 个月；项目为 *Simulation study on robust safe tracking control of nonlinear rehabilitation robotic systems*。要求 honours degree 或同等资格，优先非线性控制、协同控制、安全控制经历；HK$125/小时；**2026-09-11 开始审理，直至聘满，并非明确截止日**。用户学历资格与相关经历尚未核对。[官方职位页](https://jobs.polyu.edu.hk/job_detail.php?job=260904015)（网页工具直开失败后，以 HTTPS 读取官方 HTML 核实）。

现有成果能支撑仿真实验搭建、ROS 2 集成、几何约束处理、重复测量和失败诊断。当前控制是标准 `JointTrajectoryController` 的 position command；不能称为已实现鲁棒非线性控制、安全控制保证、协同控制或康复机器人研究。

申请 demo 的建议主线：一个受几何约束的搬运任务 → 参考与实际轨迹 → 跟踪误差与滑脱 → 已做改动及重复结果 → 下一步可验证假设。优先补同步 TCP 跟踪误差曲线、最小间隙和一项受控对比实验（如相同路径、已知初始偏移、基线与实际实现的修正策略），报告 RMS/最大误差和成功率。实验未做时只能列为计划。负责人官方研究方向也包含康复机器人的安全、学习与协同控制。[Dr Chenchen Fan 官方主页](https://www.polyu.edu.hk/rs/people/research-assistant-professors/dr-chenchen-fan/?sc_lang=en)。

建议申请材料用 90–120 秒讲解版视频加一页结果说明；保留完整原始运行，明确团队分工和个人贡献。不要为追求三块全成功而推迟申请准备，也不要把团队与 AI 辅助成果全部归为个人独立实现。本轮没有提交申请或联系招聘方。

## 4. 录制前的最小补齐项

| 优先级 | 当前证据或缺口 | 完成标准 |
| --- | --- | --- |
| 必做 | Gazebo GUI 历史记录可用；本机有 `gzclient`、`ffmpeg`，尚无本轮试录 | 冷启动后试录 10–20 秒，检查机位、遮挡、帧率、播放与计时；不能仅凭工具存在判定录制已通过 |
| 必做 | `plan_seq.py`、`exec_seq.py`、`ik6.py`、`seq_plan.json` 在 `/tmp/.../scratchpad`，执行器硬编码该路径；launch 只起场景 | 将必要脚本与输入整理进受版本管理的运行入口，保留来源和初始关节角一致性，明确重置与执行顺序 |
| 必做 | 当前没有本项目 MP4/WebM 成品；缺运行级证据绑定 | 每次保存视频、模型/代码版本、输入、计划与实测轨迹、接触摘要、结果和失败原因 |
| 必做 | `exec_seq.py` 末尾只查覆盖率和 z；未连续验证放置后稳定、姿态和非目标物体 | 用完整观测判据；其 `start` 未存 red，红块扰动检查分支不会执行，不能将“全部达标”输出当作全规则通过 |
| 按用途 | `setup.py` 声明 `detector_node`，但源目录和安装目录均无 `detector_node.py`；只有 detector 与 regression | 仅展示视觉回归可用已有模块；需要实时识别小窗或视觉驱动抓取时，先补节点、可视化与执行接口 |
| 申请增强 | 尚无同步误差/约束曲线与扰动对比 | 加参考/实际 TCP、误差和间隙记录；报告相同条件下的基线与改动结果 |

本轮按现有 `seq_plan.json` 和 `exec_seq.py` 配时规则静态复算：461 点，总计划时长 **166.5316 秒**（黄约 49.67、绿约 67.06、蓝约 49.80 秒）；计划文件记录的碰撞代价全部 ≤1。该结果是计划数据核验，**不是实时运行、连续碰撞检测或本轮新成功记录**。执行器使用墙钟等待并轮询模型，录制时须区分计划时间、仿真时钟与墙钟；不能据 167 秒直接宣称符合比赛时限。

建议先制作两种用途的版本：队内 60–90 秒，突出单块接触搬运和舌规尺寸/试配；申请 90–120 秒，突出轨迹与失败分析。时长是剪辑和内容建议，不是当前已测运行时间；需要完整三块过程时保留完整长版。两者均明确标注 Simulation。正式比赛另按 FAQ p2–3 的固定机位、单镜头连续、不得倍速/拼接、完整场景与计时器要求准备，仿真展示不能据此视为正式提交材料；FAQ p3 建议 180 秒以内、最多 250 秒。

## 5. 证据位置与披露

- 项目历史实验：`docs/simulation-plan.md`、manifest 的 `ENV-SIM-20260906`，以及 `.memsearch/memory/2026-09-06.md`；记忆检索数据库因只读锁失败，本轮回读原始 Markdown，并以现有代码和 STL 复核。
- 本地代码：`/home/afonso/aubo_ros2_ws/src/meituan_sim/`、`/home/afonso/aubo_ros2_ws/src/meituan_vision/`。
- 临时执行与轨迹：`/tmp/claude-1000/-home-afonso-meituan-robotics-challenge-2026/056bb1da-3c41-4c66-bc09-9962a0815f4c/scratchpad/`。本轮登记关键文件 SHA-256，但未归档代码/模型；临时目录仍存在丢失风险。
- 本轮使用 OpenAI Codex 协助仓库审计、STL 核验、静态配时计算及评估整理；历史仿真与舌规由 Claude Code 辅助，见既有记录。未移植队友代码。后续引用第三方模型、代码和 AI 工具按 FAQ p6/Q17 保留出处、许可核实与使用说明。
