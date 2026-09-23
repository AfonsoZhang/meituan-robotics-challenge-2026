# NUC 实机接入

实机栈：NUC 原生 Ubuntu 22.04 + ROS 2 Humble，S3 用 `aubo_ros2_driver`，D435i 用 realsense-ros，规划用 MoveIt（USER-HW-20260923-02 至 -10）。本目录只做**接入与验证**：装环境、逐项检查、单关节小幅点动。尚未在 NUC 与实机上运行过；检查脚本和点动脚本只在开发电脑的仿真里试过（仿真与驱动的控制器同名）。

## 驱动的已知行为（读过上游代码，提交 `85684075`）

- 连接控制柜 RPC 30004、RTDE 30010，用**写死的默认账号** `aubo` / `123456` 登录；控制柜改过密码就连不上。
- 连上后会写控制柜硬件参数 `vff_enable = false`（关速度前馈），这是**改动控制柜配置**，不是只读。
- 激活后进入伺服模式，并以当前位置作为保持目标：驱动一起来机械臂就处于受控状态。没有「只读不伺服」的启动方式。
- 控制柜不在 Running / 正常或缩减安全模式时，驱动拒绝下发并报错，需要先在示教器上处理再重启驱动。

## 步骤（每步通过后再进行下一步）

| 步 | 做什么 | 通过标准 |
| --- | --- | --- |
| 1 | `bash robot/setup-nuc.sh`（需要 sudo、外网；ROS 2 Humble 先按官方文档装好） | 构建完成；`python3 robot/bringup_check.py env --robot-ip <IP>` 除「与示教器一致」外全部通过 |
| 2 | 假硬件空跑：`ros2 launch aubo_ros2_driver aubo_control.launch.py aubo_type:=aubo_S3 use_fake_hardware:=true`，另开终端 `python3 robot/bringup_check.py driver` | 两个控制器 active，`/joint_states` 6 个关节 |
| 3 | 连实机（急停在手边，工作空间清空）：同上但 `use_fake_hardware:=false robot_ip:=<IP>`，再跑 `bringup_check.py driver` | 同上，且打印的关节角与示教器逐个一致（人工对照，记进报告） |
| 4 | 单关节点动：`python3 robot/jog.py --joint wrist3_joint --delta-deg 3`，确认后再 `--delta-deg -3` 回位；再逐个试其他关节 | 转的是所选关节，方向与符号一致，终点误差小；急停能停 |
| 5 | 相机：`ros2 launch realsense2_camera rs_launch.py align_depth.enable:=true`（参数名以 `--show-args` 为准），再 `python3 robot/bringup_check.py camera` | 彩色、深度、对齐深度都有数据；实际话题名与编码记在报告里 |
| 6 | 监控台：`bash demo/dashboard.sh --readonly --ros-domain-id <值> --presets <第 5 步生成的 dashboard-presets.json>`，开发电脑 `ssh -N -L 8766:127.0.0.1:8765 <用户>@<NUC>` | 开发电脑浏览器能看到画面、节点和关节角 |

每次检查的报告写在 `outputs/claude_bringup_<阶段>_<时间>/report.json`，退出码 0 全部通过、2 有未通过项。

点动脚本限幅：单次 ≤5°、时长 ≥5 s（≤1°/s），只动一个关节，执行前必须输入 `yes`。它不是碰撞检查，第一次请从末端关节开始。

## 出处与披露

`setup-nuc.sh` 锁定 `AuboRobot/aubo_ros2_driver` 提交 `85684075d6ff06c5385e39611208e99ebf0f94c6`（submodule `aubo_description` `47fa5e02`），不归档进本仓库；驱动构建时下载的二进制 aubo_sdk 0.24.1-rc.3 许可未核对（Q17）。realsense-ros 由 apt 安装（RS-ROS2）。本目录脚本由 Claude Code 编写，未复制第三方代码。
