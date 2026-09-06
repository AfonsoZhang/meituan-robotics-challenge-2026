# 单块钩取录制入口

此入口仅连接自行启动的 Gazebo Classic 仿真实例，使用 ROS domain 67、Gazebo master 11365。依赖本机现有 `/opt/ros/humble` 和 `/home/afonso/aubo_ros2_ws/install`，不连接实机、不重规划、不附着电池。模型仍由外部工作空间提供。

```bash
# 只检查依赖、保存输入与计划，不启动仿真
bash demo/run.sh --check

# 恢复初始姿态后录静态短片，不执行抓取
bash demo/run.sh --smoke

# 完整黄块 → P1；口令仅为演示示例
bash demo/run.sh

# 离线评测器测试
python3 -m unittest discover -s demo -p 'test_*.py'

# 根据实际输出目录绘制轨迹和跟踪误差
python3 demo/report.py outputs/demo-YYYYMMDD-HHMMSS
```

每次创建新 `outputs/demo-*` 目录，含 `demo.mp4`、起止帧、`inputs.json`、`plan.json`、`tracking.csv`、`model_states.jsonl`、`summary.json` 和日志。失败运行也保留记录。退出码 0 为此次模式检查通过，2 为抓放检查未通过，1 为运行或录制错误；smoke 通过不表示抓取通过。

视频按相机的仿真时间戳生成 15 fps 视频，丢帧间隔保持上一帧；画面同时标明仿真与墙钟时间。它不是实际墙钟速度录像，也不是正式比赛提交视频。腕部 RGB 只作独立显示，不参与控制；阶段文字来自轨迹计划，不是动作成功识别。

首次实测发现机器人在控制器接管前下垂，且等待收敛仍不能稳定复现。当前启动期间暂时关闭机械臂六个活动连杆的重力，控制器接管后逐个恢复并读回确认重力开启、质量与惯量未变，之后才开始录制；电池重力始终开启，不重设电池位置。读回结果保存为 `startup-gravity.json`。若仍有小幅初始误差，在偏差 ≤0.25 rad 时才尝试经 51 个位形近似胶囊/高度检查的恢复，要求误差 ≤0.02 rad 且四块电池端点位移 ≤2 mm；否则停止。所有初始化发生在录制前并写入 summary；不是连续碰撞或形式化安全保证。

抓放检查包括黄块抬离台面持续时间、最终近水平姿态、内框投影覆盖率、外框包含、运动后至少 3 秒连续稳定观察，以及红/绿/蓝全程位移和转角。稳定及非目标扰动阈值是保守的 demo 工程判据，并非新增比赛规则。没有接触对监测，不能据此声称全过程无碰撞；没有对完整赛事计分逻辑作实现。跟踪误差来自控制器参考/实测关节，经名义 FK 变换，与视觉误差和落点误差分开。

`data/sequence-v1.json` 是历史实验轨迹的冻结副本；来源、哈希和 AI 使用说明见 `data/provenance.json`。原始仿真接线和轨迹由 Claude Code 辅助完成，录制入口与评测由 OpenAI Codex 辅助完成；机器人上游来源、许可证待核事项见项目 manifest 和 `docs/simulation-plan.md`。没有引入队友仓库代码。
