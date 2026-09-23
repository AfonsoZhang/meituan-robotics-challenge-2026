# 单块钩取录制入口

此入口仅连接自行启动的 Gazebo Classic 仿真实例，使用 ROS domain 67、Gazebo master 11365。需要 ROS 2 Humble 和已构建的仿真工作空间；通过 `AUBO_ROS2_WS` 指定路径，默认 `$HOME/aubo_ros2_ws`。不连接实机、不重规划、不附着电池。[另一台机器的完整搭建步骤](SETUP.md)包含上游模型获取、自建包构建和短试录检查。

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

## 视觉抓取前修正（实验入口）

```bash
# 同样观察，但保持冻结轨迹：偏移对照
bash demo/run.sh --vision observe --yellow-offset-mm 6
# 用 RGB-D 测量修正源位置，P1 目标位置不变
bash demo/run.sh --vision correct --yellow-offset-mm 6
# 名义布局检查
bash demo/run.sh --vision correct
```

`--yellow-offset-mm` 只改变新世界中黄色电池的初始 x；控制修正函数不接收这个参数或模型真值。两种视觉模式都先到同一个观察位，使用时间戳匹配的 RGB-D 和深度时刻 TF，随后回到起始位。`observe` 仅记录测量；`correct` 修正源端接近、穿钩和提升，并在搬运段逐渐回到原目标轨迹。执行期间仍是开环轨迹，不是连续视觉伺服。

保存 `vision-snapshot.npz`、`vision-observation.png`、`vision-detections.json`、`vision-result.json`、`observer-model-states.json` 和（修正模式）`corrected-plan.json`。观察动作发生在主抓取视频之前；图像快照单独保存。识别门限不通过时停止，不发送抓取轨迹。完整对照结论见 [视觉修正实验](../docs/vision-correction.md)。

局部 IK 保持法兰方向、检查模型关节限位与连续性，限修正半径 10 mm。原轨迹碰撞代价不会冒充修正轨迹的碰撞验证；尚无修正后全路径接触监测或连续碰撞检查。该入口只适用于当前理想相机、近名义位置和近零偏航的黄色单块实验。

离线重放已保存的相机测量（不启动 ROS/Gazebo）：

```bash
/usr/bin/python3 demo/replay_vision.py outputs/你的运行目录/vision-snapshot.npz
```

固定偏移重复实验可使用 `run_matrix.py` 与 `summarize_matrix.py`。运行协议、命令和完整计数规则见 [重复实验说明](../docs/vision-repeat.md)。

## 三块逐次观察（集成调试）

```bash
bash demo/run.sh --sequence --timeout 180
```

同一世界按黄、绿、蓝顺序逐块定位和抓取，失败停止。原单块入口保留；三块模式自动应用视觉修正，不与 `--vision` 或 `--smoke` 混用。蓝块接触记录只用于审计。全部开发尝试、视频计时边界和未解决问题见 [三块集成记录](../docs/vision-sequence.md)。

## 可选力矩闭环

重新构建后可执行 `bash demo/run.sh --control smc --vision correct`；`--control pd` 为重力补偿 PD 基线，`--control pd_matched` 为边界层增益匹配对照。默认仍为 position。高位受扰对照使用 `--robust-probe --disturbance-nm 2`，不要与抓取/序列选项混用；详见 [算法、协议和实测结果](../docs/robust-control.md)。

## 浏览器监控台

```bash
bash demo/dashboard.sh            # 打开 http://127.0.0.1:8765/
```

一个页面里并排：多个 ROS 终端（每个是本机 PTY 中的交互 bash，已设 `ROS_DOMAIN_ID=67`、`GAZEBO_MASTER_URI`，工作目录为仓库根；可选预设如节点/话题列表、控制器状态、关节跟踪误差、相机帧率，「运行 demo」预设只键入命令不回车）、相机实时画面（自动列出 `sensor_msgs/Image` 话题，经 MJPEG 限 15 fps 推送；深度图按每帧 2–98 分位伪彩，只作目视，不是量测）、`outputs/` 下已录 mp4 回放，以及 gzserver / record.py 进程与 ROS 节点状态。

监控台只观察、不改 `record.py` 的任何行为；仿真由 `record.py` 自行起停，所以实时画面只在一次运行期间有。终端即本机 shell，默认只监听 127.0.0.1，不要改成对外地址。实机部署在 NUC、由开发电脑经 SSH 隧道远程查看（USER-HW-20260923-07）。用户只确认了「看」，所以 NUC 上用只读模式：

```bash
# NUC 上：不开交互 shell，只允许监控预设（节点/话题/控制器/帧率等），键盘输入一律忽略
bash demo/dashboard.sh --readonly --ros-domain-id <实机所用值>
# 开发电脑上：本地 8766 转发到 NUC 的 127.0.0.1:8765（8765 留给本机仿真监控台），再打开 http://127.0.0.1:8766/
ssh -N -L 8766:127.0.0.1:8765 <用户>@<NUC 地址>
```

NUC 上仍只监听 127.0.0.1，不要为远程访问改 `--host`；WSL2 里建立的隧道，Windows 浏览器也能经 localhost 转发访问。`--ros-domain-id` 默认 67 只对应仿真，实机值未定。实机话题名以届时的相机与 S3 驱动为准（Q17），监控台自动列出图像话题，终端预设里的仿真话题需相应替换。所有模式下终端 WebSocket 都校验 Origin，拒绝其他网页借浏览器连本机终端。只读模式与跨站校验已在开发电脑上验证，尚未在 NUC 上运行过，SSH 隧道也未实测。

终端组件 xterm.js（MIT，`@xterm/xterm@5.5.0`、`@xterm/addon-fit@0.10.0`）从 jsdelivr CDN 加载，离线时终端不可用；页面与后端 `dashboard.py` 由 Claude Code 编写，未引入其他第三方代码。
