# 在另一台机器重建仿真工作空间

观看视频或查看结果不需要 ROS：[Demo Release](https://github.com/AfonsoZhang/meituan-robotics-challenge-2026/releases/tag/demo-v1.0.0)。下载其中 `demo-evidence.zip` 可获得视频、图表、轨迹与结果记录。

## 环境和依赖

本入口面向 Ubuntu 22.04、ROS 2 Humble、Gazebo **Classic 11**；已有实验使用 Gazebo 11.10.2。它不支持直接换成 Gazebo Harmonic。需要能够供 Gazebo 相机渲染的显示/图形环境；WSL2 须具备 WSLg。不能仅凭依赖安装完成推断 RGB-D 渲染可用，先跑 smoke。

先按 [ROS 2 Humble 官方 Ubuntu 安装入口](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) 配置 ROS 软件源及基础环境，再安装本项目依赖：

```bash
sudo apt update
sudo apt install git build-essential cmake ffmpeg \
  python3-colcon-common-extensions python3-numpy python3-opencv python3-matplotlib python3-scipy \
  ros-humble-gazebo-ros-pkgs ros-humble-gazebo-ros2-control \
  ros-humble-kdl-parser liborocos-kdl-dev ros-humble-tf2-ros ros-humble-ros2-controllers ros-humble-xacro ros-humble-robot-state-publisher
```

依赖名称与作者机器已安装包核对；上述 apt 软件源会随时间更新，不能据此保证重装后与原实验二进制版本完全一致。原实验版本见 [仿真方案](../docs/simulation-plan.md)。

## 获取源码并构建

```bash
git clone https://github.com/AfonsoZhang/meituan-robotics-challenge-2026.git
cd meituan-robotics-challenge-2026

# 建议用新的工作空间，避免与自己的机械臂工程混用。
export AUBO_ROS2_WS="$HOME/meituan_demo_ws"
bash demo/setup-workspace.sh

# 先检查，再试录，最后执行单块演示。
bash demo/run.sh --check
bash demo/run.sh --smoke
bash demo/run.sh
```

`setup-workspace.sh` 构建三个包：

| 包 | 来源与获取方式 |
| --- | --- |
| `aubo_description` | 从 `AuboRobot/aubo_description` 获取并锁定 `47fa5e02fa873f27f7e812d31f31e3f4cf5e56b1`；不将上游模型/网格归档到本仓库 |
| `meituan_robust_control` | 本仓库 `simulation/meituan_robust_control/` C++ 力矩插件；ROS 2 Control + KDL |
| `meituan_sim` | 本仓库 `simulation/meituan_sim/` 自建源码；CMake 在构建目录运行场景生成器，生成电池、底图及 world 后安装，不依赖作者机器的 `/tmp` 文件 |

不需要克隆或构建实机 `aubo_ros2_driver`，也不需要下载 AUBO 私有 SDK。上游 `aubo_description` 的 `package.xml` 声明 BSD，但缺独立 LICENSE 的既有问题保留在 manifest，本仓库不替其重新授权。自建源码出处与打包改动见 `simulation/provenance.json`。

脚本使用普通拷贝安装；上游网格中有目录级符号链接，不使用 `--symlink-install`。如果目标目录已经存在且上游提交不匹配或有跟踪文件改动，脚本停止，不执行 reset/覆盖。构建会使用上游原有 `xacro.sh` 生成 `.urdf.xacro`，因此需要可写工作空间。

`AUBO_ROS2_WS` 在构建和运行时必须相同，新终端中需重新 export。默认值为 `$HOME/aubo_ros2_ws`；特殊 ROS 安装位置可通过 `DEMO_ROS_SETUP` 指定 setup 文件。需要镜像来源时可设置 `AUBO_DESCRIPTION_REPOSITORY`，但提交号校验仍然执行。

## 核验与限制

```bash
source /opt/ros/humble/setup.bash
source "$AUBO_ROS2_WS/install/setup.bash"
ros2 pkg prefix aubo_description
ros2 pkg prefix meituan_sim
python3 -m unittest discover -s demo -p 'test_*.py'
```

`--check` 验证包发现、计划及输入准备，不启动 Gazebo；`--smoke` 验证相机、控制器、初始化和视频编码；完整运行才检查单块抓放。不要并行启动多个本入口实例：当前固定使用 ROS domain 67 / Gazebo master 11365。

本轮在作者机器已有 Humble 依赖的条件下，用 `/tmp` 中的新工作空间验证独立构建、`--check` 和 7 秒短试录（105 帧）；上游输入使用本地官方仓库副本的同一提交。这验证了不依赖旧的 `meituan_sim` 安装，不等同于在一台全新操作系统上验证 apt 安装或所有显卡配置。

新增 `meituan_robust_control` 为项目自有 C++ 控制插件，依赖已安装的 ROS 2 Control 和 KDL；开发验证使用 Humble JTC 2.53.3，插件继承其接口，其他版本需重新编译验证。原位置控制入口保持默认。力矩模式与对照见 [鲁棒控制实验](../docs/robust-control.md)。
