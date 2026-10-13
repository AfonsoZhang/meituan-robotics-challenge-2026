# Web UI 接口兼容性检查 · 2026-10-13

来源：USER-HW-20261013-05（用户会话）；本地观测 ENV-WEBUI-API-20261013。

本轮按用户接口约定审计现有 Web HTTP / ROS 客户端，修复 P2 导出的兼容性遗漏。只修改 Web 导出、兼容性测试与接口说明，不修改 FSM / Action / Cancel / Motion 内核。

## 边界和输入

当前联合验证限定 C++ Mock / GenericSystem Fake Hardware。本轮只运行开发电脑的 Python / loopback HTTP 桩测试，不启动 ROS、C++ Mock、GenericSystem、实体设备或硬件控制；生产 transport 的读取仅作静态审计。

输入为本仓库先前冻结的 `docs/experiments/webui-p2-20261013/source-webui/`。本目录 source.patch 是在该版本之上的增量补丁，路径为 webui/；可以在复制该目录后的独立 Git 目录用 `git apply --check` 和 `git apply` 复核。不是旧累计上游包补丁的重写，也未重新构建安装包。

## 检查

1. 确认生产 transport 的 ActionClient 类型只有 ExecuteTask，现有 RequestStop 保留，PickPlace/FJT 只有只读反馈/状态和 GetResult；不新增低层控制。
2. 新增三项检查：旧 HTTP 请求和下载字段、完整任务事件及子 Goal 筛选、快照产生 UNKNOWN 时事件与导出一致。HTTP 请求只到临时 loopback 端口，transport 是只记录调用的进程内桩。
3. 执行 `python3 -m unittest discover -s webui -p 'test_*.py' -v`；76 项包含上述三项，不重复累计。
4. 增量补丁应用到 P2 源码副本，37 个文件与当前 webui 源码逐字节一致。
5. 替换本会话旧的只读离线预览进程，验证无 ROS domain、连接离线、写操作全部关闭；GET /api/export 保留旧字段及附件名。

新用例首次及完整套件均通过。没有本轮 ROS、浏览器、C++ 或实机通过结论；以往冻结结果保持原范围。

使用 OpenAI Codex 协助审计、兼容性修正、测试和文档。未引入新第三方运行依赖；依赖/许可见 webui/provenance.json。原始日志与补丁按 SHA-256 索引冻结。
