# 单块钩取 demo 实录

日期：2026-09-07。此次已实际启动 Gazebo、执行黄块 → P1，并录制完整过程；与此前仅作静态检查的 [录制评估](demo-readiness.md) 区分。口令为演示示例，不是正式任务口令。

## 交付文件

- [完整视频，约 56.7 秒](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/download/demo-v1.0.0/demo.mp4)：1600×880、15 fps、H.264，约 1.25 MB。
- [TCP 参考/实测轨迹与误差图](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/download/demo-v1.0.0/tracking.png)，另有 [PDF](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/download/demo-v1.0.0/tracking.pdf)。
- [结果 JSON](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/download/demo-v1.0.0/summary.json)、[原始跟踪 CSV](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/download/demo-v1.0.0/tracking.csv)、[电池位姿记录](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/download/demo-v1.0.0/model_states.jsonl)。
- [输入与来源哈希](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/download/demo-v1.0.0/inputs.json)、[恢复重力的读回记录](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/download/demo-v1.0.0/startup-gravity.json)。
- [可复现运行入口及说明](../demo/README.md)。原始运行目录仍在 `.gitignore` 的 `outputs/` 下；上述交付文件通过 GitHub Release 发布，可下载 [完整证据包](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/download/demo-v1.0.0/demo-evidence.zip) 和 [SHA-256 校验清单](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/download/demo-v1.0.0/SHA256SUMS.txt)。

## 本次运行结果

| 指标 | 最终录制运行 |
| --- | ---: |
| 冻结轨迹 | 黄块单段，118 点 |
| 计划动作时间 | 49.668 s |
| 视频时间 | 56.733 s，含开头静态画面及末尾观察 |
| 记录器墙钟用时 | 66.094 s，含启动等待等；不能与视频时间混用 |
| 黄块落点中心误差 | 2.255 mm |
| 内框投影覆盖率 | 84.429%（近水平矩形足迹网格积分） |
| 外框包含 / 姿态 | 通过 / 近水平 |
| 离台高度 >20 mm 的最长连续观测 | 14.2 s |
| 动作结束后稳定观察 | 至少 3 s，检查通过 |
| 红、绿、蓝扰动 | 采样中均未观察到位置或转角变化 |
| TCP 跟踪误差 RMS / 最大值 | 0.145 / 0.326 mm |
| 跟踪样本 | 547 |
| 控制器 Action | 成功，错误码 0 |

这些是单块 demo 工程判据，不是完整赛事计分或实机验收。内框 ≥70% 沿用 USER-RULE-20260906-02（用户转述组委会答复，无 PDF 页码）；稳定时长参考 FAQ p2–3、RULES p3–4，而位移/转角阈值为本入口自定的工程判据。没有接触对监测，不能据电池未移动或离散路点检查断言全过程无碰撞。

本次 TCP 误差定义为同一控制器状态消息中的参考关节与实测关节，分别经名义 URDF 正运动学计算 TCP 后取欧氏距离。**它不是视觉定位误差、落点误差或相对提手误差**。此前 4–6 mm 记录的测量方法和时刻尚未与本次统一，不能宣称本次已证明消除蓝块失效，或用单块结果更新三块序列成功率。

## 初始化与录像方式

首先尝试直接启动时，Gazebo 在沙箱内无法创建 `~/.gazebo/server-11365`，获准在沙箱外运行后解决。随后检测到机械臂在轨迹控制器接管前下垂；单纯等待收敛仍有较大且不稳定的初始偏差，入口按初始状态检查停止，没有继续抓取。

最终方案是：仅在启动期间关闭六个活动连杆的重力，控制器接管后逐连杆恢复，并通过服务读回确认重力开启、质量和惯量不变，然后等待稳定再录制。电池重力始终开启，没有重新放置电池，没有物体附着。最终运行无需额外关节恢复动作，初始最大关节误差约 0.000052 rad。启动阶段不在视频中，读回证据保留于 `startup-gravity.json`。

视频来自独立固定总览相机，右侧为腕部 RGB；末端没有视觉反馈控制。右侧尺寸是完整仿真钩的舌宽/厚/尖高；STL 舌规与完整钩具的关系仍按 [录制评估](demo-readiness.md) 解释，不把这条视频当作该 STL 的装机验证。

录制按相机仿真时间戳生成恒定 15 fps 视频；收到 814 帧，37 帧用前帧保持补齐，最终 851 帧。最大源图像时间戳间隔 0.204 s，因此不能称为零丢帧录像。画面同时标注仿真与墙钟时间；阶段名称来自计划，不是动作成功检测。它不是正式比赛所要求的实拍单镜头视频（FAQ p2–3）。

## 验证与保留的运行

- 离线评测器 5 项测试通过，覆盖正常放置、非目标电池移动后返回、稳定观察不足/缺测、倾倒和目标外掉落。
- 最终 MP4 经 ffprobe 检查元数据、ffmpeg 全片解码，无解码错误；目视检查初始、提升等关键帧与轨迹图。
- `demo-20260907-005406` 为静态短试录；`005738` 和 `010012` 为两次完成的单块运行，均通过 demo 判据，中心误差分别 2.000 / 2.255 mm。两次相机参数不同，不是严格的多次同配置成功率实验。
- 其他输出目录保留了准备检查和启动失败，未将启动失败记作抓取成功。没有新做三块闭环实验。

## 展示建议与披露

队内可直接用完整视频解释被动钩的穿入、承托、搬运和释放；确认舌规实物可行性仍需真实电池试穿与尺寸记录。RA 申请可同时附轨迹图，说明仿真实验、控制器集成和定量验证能力；当前标准位置轨迹控制不等于自研鲁棒安全控制，下一步扰动对比仍是待做实验。个人贡献、团队协作和 AI 使用应按事实分别说明。

冻结轨迹和原仿真接线来自此前 Claude Code 辅助的项目工作；本轮 OpenAI Codex 辅助开发录制、测量、失败判定和图表。没有移植队友代码。此后按用户要求将本次视频与结果发布到 GitHub Release；没有发送招聘申请或联系他人。来源与产物哈希见 manifest 的 `DEMO-RECORDING-20260907`。
