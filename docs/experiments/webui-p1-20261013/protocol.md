# Web UI P1 独立接口验证协议

范围：USER-HW-20261013-02；源码核对 TEAMMATE-WEBUI-P1-20261013；结果登记 ENV-WEBUI-P1-20261013。正式 pin 不变。此轮不恢复旧自动监测或 C1/完整 FSM 验收；工作区另有独立 C1 修复不并入本补丁。

1. 读取原生 BatteryDetectionArray/ToolState 与固定 Planner/视觉源码，确认没有二维框、实时 Planner 话题或试提/落座 IDL。对可选 JSON 消费约定显式固定发布者。
2. 离线测试非有限位姿、旧 PoseStamped、重复 ID、未知检查、命令证据不得独立确认、验证身份、同一锁内 JPEG+时间戳。Node 检查当前目标/其他任务/过期/暂停等展示边界。
3. 全新 network=none、无设备/挂载/暴露端口、2 CPU/4 GiB 容器，固定 domain 94。原生 ROS 图像、BatteryDetectionArray、ToolState、String 由明确合成夹具发布；没有实体相机、FSM、Planner、Motion/SDK 驱动运行。
4. 六项 P1 检查涵盖 RGB/16UC1 深度 JPEG、三块检测、NaN/旧位姿/零检测、watchdog 原因与新 plan 不继承检查、工具估计与非法独立证据、重复发布源和断流。另跑五项原有 P0 ROS 回归，保留 ACK≠Stop Confirmed 与注入 ABORTED/520。
5. Windows 浏览器通过临时 loopback Docker-exec 转发读取实际 HTTP/ROS 快照。截图均合成输入，明确标注不代表实机。document hidden 引起 rAF/鼠标等待超时；最终使用原生 DOM 按钮与暂停/恢复取得新快照，没有替换前端状态。前台鼠标/键盘覆盖不在本轮声明中，详见 qa/browser-validation-notes.md。
6. 同步到 mtc_webui 命名空间，colcon 构建安装包并重复相同 Python/P1 ROS 检查；28 个安装文件逐字节匹配，Node 文件不作为 package_data 安装。累计补丁在原始 PR8 应用后逐字节相同；结束时 PR8 head 变化但整树相同。
7. 停止测试 ROS、转发和专用容器，保留无 ROS domain 的只读 localhost:8772 预览。keeper 的 137 与 ROS 进程正常关闭分开；失败、重试、旧 P0 冻结不删除或覆盖。

原始运行目录见 inputs/manifest；依赖下载失败后使用旧相机验证容器的只读快照创建新环境，没重启原容器。复现命令、源码哈希、安装映射和实际日志均在本目录。索引覆盖除 index.json 自身以外的全部文件，manifest 登记索引 SHA-256。

使用 OpenAI Codex 协助实现、测试、浏览器核验和文档登记。上游 MIT 许可见 sources/upstream-LICENSE；运行依赖许可与边界见 source-webui/provenance.json。原始下载未用于测试，未把历史 C1 注入显示回归记为实际内核修复。
