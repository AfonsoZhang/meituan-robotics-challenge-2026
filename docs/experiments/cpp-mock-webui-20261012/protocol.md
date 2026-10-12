# C++ Mock 与 Web UI 冻结协议

来源 ENV-CPP-MOCK-WEBUI-20261012、TEAMMATE-CPPUI-20261012；用户会话授权 USER-HW-20261012 / USER-HW-20261012-02。本集只新增，不改此前签收报告和冻结集。

先确认北京时间 08:00 后 watcher EXPIRED、pending/active/main_review 为空、14 个实际事件签名仍匹配，旧 runner/容器均已停止；再在截止 main 的隔离副本实现。候选提交与完整差异见 inputs.json、source-files.json、source.patch；冻结源码取自实际推送的 Git 提交。未拼接未合并分支，不推进正式 pin。

单容器无外部网络、设备映射、宿主挂载或 Docker 端口映射，2 CPU / 4 GiB。复用已验依赖，源码 docker cp。先构建并运行 40 个 C++ Action 与 39 个 UI 离线回归，再六个串行 HTTP→真实 ROS→C++ Task→C++ PickPlace 场景；记录实际父子 UUID、状态/Feedback/Result/Cancel、唯一服务器/类型/QoS及退出图。浏览器通过本机仅环回的 QA stdio 中转访问，测试后停止中转。

runtime/ 保留全部初次失败和修正后运行、C++ 日志与 Web 会话，host-logs/ 是宿主有界命令记录，host/ 是命令元数据、浏览器回执/截图、环境隔离/清理和既有证据完整性。harness/ 为本轮执行/归档工具。原始 outputs 仍留本机，不整目录上传；不归档实时配置 watch-config.json、缓存或 Git 私有配置。已存在的旧冻结集按自身 index 原样保留。

六项程序断言通过不代表全部取消边界通过：正常 Mock 700 ms Future 延时，浏览器及独立 CLI 延迟取消均 ACK 后实际 ABORTED/520，C1 未关闭。仅静态证据新鲜度分析；内核根因与契约交孙嘉明。正常及时取消 CANCELED/0 不能覆盖此失败。旧 Python/独立 MoveIt/轨迹分支失败同样不被本轮关闭。

完整报告在 docs/cpp-mock-webui-acceptance.md；SOP 与本轮源码在上游独立 PR #8。PR 保持待审、不自动合并。使用 OpenAI Codex 协助启动/观测/UI/诊断与归档；具体导入代码、版本、许可边界见 source/src/mtc_cpp_mock_bringup/provenance.json。未替第三方代码重新授权。
