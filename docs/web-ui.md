# 实机 Web 操作台：实现与验证

用户澄清“我要的是实机操作台”（USER-HW-20261011-07，2026-10-11 用户会话）。新版 `webui/` 默认连接真实 **ROS 2 Jazzy** 客户端，提供任务提交/取消、软件停止、FSM/设备/工具状态、RGB-D、关节及日志。没有配置或设备消息时显示离线、禁止提交，不生成演示状态。个人主责仍为系统集成与验收，兼做 Web UI（USER-HW-20261011-03）。

```bash
# 在 NUC 已 source/构建的 Jazzy 环境中；domain 沿用该实机环境的 ROS_DOMAIN_ID
bash webui/run.sh
# 本机网页：http://127.0.0.1:8767/
# 开发电脑仅预览离线页面：python3 -m webui.server
# 历史 UI 演练须明确指定：python3 -m webui.server --mock
```

[启动配置、依赖与 HTTP 契约](../webui/README.md)提供完整说明。工作空间 `/home/aaet/meituan_challenge_ws`、节点与话题来自固定队友仓库（TEAMMATE-FSM-20261011、TEAMMATE-SDK-20261011，查阅日期 2026-10-11）；当次再次核对远端 main 仍为 `1d940f7c5f12561fed6641457c0b4b630a282b05`。NUC SSH 地址、现场 ROS domain 未在该仓库确认；91 是 Fake SOP 示例，67 是旧仿真域，均不作为实机默认值。

![实机操作台的离线页面](experiments/webui-ros-20261011/offline-desktop.png)

## 当前实现

浏览器仅展示和输入，后端持有 rclpy Action 句柄。HTTP 202 表示排队；服务端受理、反馈、Result、Cancel 回执、独立停稳状态分别记录。任务完成数只取 TaskState/Result，不根据时间推算。重连不会重发请求；重复 task_id、第二个活动 Goal、错误 Goal 取消均拒绝。Goal 回执未知或取消异常时保留未决状态，不伪造失败/成功。

Task/Robot/ToolState 使用消息 stamp 与接收单调时钟检查新鲜度；同时显示来源、工具证据和独立验证。机器人需明确报告非 simulation_mode、通信/就绪/联锁/停稳正常且无运动，FSM 为 WAIT_TASK、工具已分离，才开放任务。RequestStop 只提供软件停止，回执不替代 `stop_confirmed` 或实体急停。`--readonly` 禁用全部写操作。

**发布源限制**：本次安装的 rclpy 7.1.12 回调 MessageInfo 是字典，未提供逐消息 publisher_gid。操作台因此要求话题恰有一个发布端，再核对节点名；图中的 GID 仅识别发布端更换，不冒充逐消息来源过滤。默认 robot 节点为 `/mtc_aubo_bridge`。若与 motion executor 同时发布 `/mtc/robot/state`，必须将权威机器人状态 remap 到独立话题后配置 UI；冲突、未知节点或丢失发布端时显示不可用。每条样本与提交前重新检查来源。此限制由 ENV-WEBUI-ROS-20261011 的实测登记，不是已完成团队全链路配置的声明。

彩色与深度通过实际 ROS Image/CompressedImage 接入，支持唯一相机自动发现和显式话题；显示来源、编码、尺寸与龄期，旧帧失效后隐藏。深度按 16UC1/mm 或 32FC1/m 转为固定 0–2 m 观察伪彩，处理行步长、端序和非法值；现场单位、相机同步、标定仍待核验。关节位置从 JointState 的 rad 转为 °。尚无检测叠图和任务录像关联，`recordings` 保持空。

## 本地与隔离 Jazzy 验证

本轮观测登记 **ENV-WEBUI-ROS-20261011**。证据见 [index.json](experiments/webui-ros-20261011/index.json)、[summary.json](experiments/webui-ros-20261011/summary.json)、[浏览器检查](experiments/webui-ros-20261011/artifacts/browser-checks.json)和[协议](experiments/webui-ros-20261011/protocol.md)。原始记录保存在 `outputs/webui-real-20261011-175646/`。旧的 FSM、接线补丁与 Mock UI 冻结目录未修改。

Jazzy 运行在独立容器 `mtc-webui-20261011`，源自保留验收环境的镜像快照，测试前断开依赖安装网络，使用 **network=none、无设备映射、无暴露端口、ROS 域 94 / LOCALHOST**。测试发布器及 Action 服务均为 `webui.ros_integration_check`。其中 simulation_mode=false 是测试输入，目的为覆盖实机门禁，**不代表物理硬件**；没有启动 FSM、SDK、MoveIt 或驱动。

| 验证 | 结果与范围 |
| --- | --- |
| 离线行为与 HTTP | 33 项通过；开发电脑 Python 3.10 与独立 Jazzy Python 3.12 均通过。涵盖输入、并发/重复、Goal 所有权、旧/重复/未来时间戳、取消/停稳分离、UNKNOWN、只读、持久化、相机编码与跨站限制 |
| 实际 Jazzy / DDS / Action | 9 项通过：状态/关节/RGB-D/ROS 日志、成功 Goal/反馈/Result、拒绝、ABORTED、Cancel/RequestStop、断流、simulation_mode 阻断、第二发布端拒绝、同名冲突与重新建立唯一来源后的恢复 |
| 浏览器 ROS 链路 | 经临时 HTTP 转发进入无网络测试容器；自选三色任务收到 3/3 的 fixture Result；另一个 Goal 收到精确 Cancel 回执与 CANCELED。RequestStop 回执为 true 而停稳仍为 false，页面继续禁止下一任务 |
| 浏览器状态恢复 | 刷新保留 task ID；暂停禁用提交并隐藏旧图像；恢复读取当前状态，没有重复提交；彩色/深度切换和六关节显示通过 |
| 布局 | 离线三视图在 320/390/768/1024/1440 宽均无页面横向溢出；连接 fixture 的桌面/手机截图已核对 |
| 导出 | 浏览器内 HTTP 200、attachment 与两任务 JSON 正确；仍未独立验证 Chrome 下载文件落盘 |
| 依赖版本 | rclpy 7.1.12、sensor_msgs 5.3.8、rcl_interfaces 2.0.4、unique_identifier_msgs 2.5.1、OpenCV 4.6.0、NumPy 1.26.4；安装包版本和许可证原始输出已冻结 |

![隔离 ROS 测试页面，画面内明确标注无实体机器人](experiments/webui-ros-20261011/ros-fixture-desktop.png)

**开发失败保留**：初始测试缺少 OpenCV，补齐后再启动 ROS；旧 QoS 常量导入失败、MessageInfo 属性访问/键访问失败分别保留，修正为实际 Jazzy API。多发布端门禁正确拒绝，但删除同名节点后图中的节点身份变为 UNKNOWN，测试夹具重建后又因旧 ActionServer 未显式销毁而不能恢复；补充 ActionServer/ActionClient 显式清理后，9 项复验通过。没有通过放宽来源检查消除失败。首次 setUp 失败后未清理线程造成进程 134 退出，随后完善失败路径清理，原始日志保留。

浏览器测试完成后主动关闭 fixture，临时转发器产生 31 次快照 HTTP 502；这是测试服务停止后的记录，不写成全程零错误。fixture Ctrl+C 的退出堆栈亦保留。浏览器截图/操作发生在最后的未知来源拒绝和 Action 销毁修复前；前端与正常操作路径未改，最后版本另以 9 项实际 ROS 回归覆盖这些改动。

## 仍待实机验收

本次完成的是**面向实机的操作台客户端与隔离接口验证**。NUC 部署、实际 SSH/domain/工作空间、权威状态独立话题、相机编码/单位/标定、真实末端与整轮抓放、任务录像仍未验收。上游 B03/B05/B06 和新 C++ ROS 外壳缺口继续见 [FSM 接线复验](fsm-wiring-fix.md)及 Q18；操作台没有接管或修复 FSM 内核。

## 早期 Mock 记录

USER-HW-20261011-06 保存当时选择，随后由 USER-HW-20261011-07 澄清为实机目标；原始记录不改写。DEMO-WEBUI-MOCK-20261011 的 [冻结索引](experiments/webui-mock-20261011/index.json)、[摘要](experiments/webui-mock-20261011/summary.json)保留 16 项 Mock/HTTP 检查、6 个浏览器演练任务及当时的失败/限制。现用 `--mock` 可继续演练，这些计时样例不作为 ROS 或实机验收。

使用 OpenAI Codex 协助前端设计、ROS 客户端、测试、浏览器 QA、证据与文档。第三方接口与依赖来源、版本、许可和改动范围见 [provenance.json](../webui/provenance.json)，按 FAQ p6/Q17 披露；本轮未复制上游 FSM 实现。
