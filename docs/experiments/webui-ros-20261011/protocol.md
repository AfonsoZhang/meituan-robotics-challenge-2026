# 实机 UI 客户端隔离验证协议

来源：ENV-WEBUI-ROS-20261011；需求：USER-HW-20261011-07。

本轮开发默认 ROS 客户端；任务、设备、图像与关节通过真实 Jazzy API/DDS 接收，但测试服务/数据都是隔离 fixture，无实体硬件。固定接口基线为 TEAMMATE-SDK-20261011 / 1d940f7c5f12561fed6641457c0b4b630a282b05，未修改上游源码、FSM 或驱动。

1. 离线 unittest 校验输入、所有权、Result/停稳分离、时效、并发/重复、只读、HTTP 与图像编码；开发电脑和 Jazzy 各运行 33 项。
2. 从保留的 Jazzy 验收容器创建独立镜像/容器，补齐 OpenCV/NumPy 后断开安装网络；ROS 测试时 network=none、无设备映射/端口、域 94 / LOCALHOST。
3. 运行 webui.ros_integration_check 的 9 项真实 ROS 链路测试；fixture 的 simulation_mode=false 仅为门禁输入，不证明实体硬件。失败重跑使用新日志名，保留退出码和所有错误。
4. Windows Chrome 通过仅用于 QA 的本机 HTTP 转发器访问无网络容器，验证自选三色 Goal/Result、另一 Goal 的 Cancel/RequestStop、相机切换、关节、刷新/暂停、导出接口和手机布局。结束后关闭 fixture、转发器与 QA 标签，保留实际离线 UI 标签。
5. fixture 故意不把停止回执转成 stop_confirmed；验收页面继续禁止新任务。多发布端或未知来源不得通过放宽身份检查来恢复。

通过门槛：最终 33 + 9 项通过；浏览器真实 DDS 交互返回预期字段，未伪造完成数或停稳；源码/记录能追溯。下载文件落盘、完整 FSM/MoveIt、NUC、实机运动与相机真值不在本次通过范围。

失败记录：缺相机依赖；QoS 常量不兼容；MessageInfo 属性/键缺失；首次 setUp 清理不完整的 134 退出；同名来源移除后的 UNKNOWN 身份与测试 ActionServer 未销毁导致恢复失败。后续修正唯一发布端策略、失败清理与显式 Action 对象销毁，最终 9 项通过。关闭 fixture 后浏览器临时转发器报告 31 次 502，属于该结束阶段；原始记录保留。

冻结截图/浏览器任务发生在最后两项后端修复前（未知节点拒绝和显式 Action 销毁），前端及正常操作路径未改；最终代码以 ROS 9 项复验覆盖。inputs.json 记录最终源码哈希。此目录冻结后不改写；后续实机试验另建目录。

使用 OpenAI Codex 协助实现、测试、浏览器 QA 与证据归档；依赖来源/版本/许可见 webui/provenance.json。公开披露按 FAQ p6/Q17。
