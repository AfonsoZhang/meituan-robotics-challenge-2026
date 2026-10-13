# Web UI P0 隔离验证协议

依据 USER-HW-20261013 的任务/FSM、运动与独立安全反馈要求，验证 Web 客户端语义。接口参考 TEAMMATE-WEBUI-P0-20261013、ROS2-CONTROLMSGS-20261013；本轮观测 ENV-WEBUI-P0-20261013。

1. 保持正式 pin 与旧实验目录不变。读取 PR #8 固定 head 和 Phase 2C PR #13 的接口；只变更 Web 模块及安装依赖。
2. 本机 unittest 与 Node 原生测试检查旧/缺失/未来消息、Goal 归属、颜色顺序/完成数分离、FJT 遥测关联及 Stop Request / ACK / Result / 独立证据。
3. 新建独立 Jazzy x86_64 容器：network=none、2 CPU / 4 GiB、cap_drop=ALL、无设备/端口/挂载。固定 domain 94 / LOCALHOST；不启动 FSM/MoveIt/驱动。详见 inputs.json、cleanup.json。
4. `python3 -m webui.p0_integration_check --isolated-fixture` 运行真实 rclpy/DDS/Action 刺激。断言 UI 没有 FJT send_goal/cancel_goal 客户端，验证原生反馈/结果、注入 520、请求后新独立消息与断流。fixture 的 simulation_mode=false 是门禁输入，不是硬件证据。
5. 浏览器经仅用于 QA 的 loopback stdio relay 进入容器 HTTP：选绿—蓝—红（测试口令），观察 1/3 与最终 3/3；另一个 Goal 取消后保留 ACK 和 ABORTED/520、独立停稳未确认。检查暂停和三视图在 320/390/768/1440 宽的布局。消息均来自实际测试发布器，不篡改页面状态。
6. 将同一 UI 以命名空间转换同步到 PR #8 包，colcon 构建并从安装路径运行同一接口检查。source-sync.json 记录映射与哈希，source.patch 限定 Web/依赖；patch-validation.json 记录应用到原 head 后字节一致。安装测试不是新增独立用例数。
7. 停止测试发布器/服务与 relay；确认仅剩 keeper 后停止容器。最终静态资源补打包后再清理，未运行新 ROS actors。离线只读预览无 domain，保留在 host 8772。

通过仅指客户端、包安装与隔离 ROS 接口。执行端真实遥测发布器、C1 修复、完整 Phase 2C、NUC 与硬件均待交付或验收。JSON 示例、测试中的预计时长和进度不是上游已发布字段。旧 33/9、PR #8 的真实 C1 失败与其他冻结运行不改写。

development-notes.json 保留开发失败与截图到最终代码的差异。harness 记录本轮操作，不作为可直接用于实机的部署脚本。source-webui 固定本轮个人源码；index.json 对所有冻结文件计哈希（不自包含）。使用 OpenAI Codex 协助实现、验证和归档。
