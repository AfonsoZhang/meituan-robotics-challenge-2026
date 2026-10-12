# MoveIt 规划分支隔离验收协议

来源 ENV-PLANNER-20261012；提交 TEAMMATE-PLANNER-20261011；授权 USER-HW-20261011-08、USER-HW-20261011-09。事件 10 月 11 日收到，补跑与证据整理跨到 10 月 12 日，均按上海日期标注。

1. ack 为 CLAIMED 后才工作；确认原 PID 和容器停止，核对完整 25 步 summary、完整 53 文件 diff 与原 290 个文件 SHA。
2. 只对停止原容器做独立文件系统快照；无网络/设备/挂载/发布端口，2 CPU / 4 GiB / 512 PID、cap-drop ALL、no-new-privileges。未重启或改写原失败容器；下一 SHA 保持主对话门禁。
3. 单独核验正常 XML：原四核心 318 + 新规划 29 = 347；新 29 个测试身份和源码 TEST 全部对应。此分支没有 C++ Action 包或 PR #2 回归，不套用另一分支的 358/6 数字。FakeBackend/spy Motion 的 FSM 用例不能替代真实 MoveIt 执行。
4. 保持代码与默认参数不变，只在容器内用目录别名适配既有 workspace/install 布局；ROS domain 116 运行交付 run_planning_evidence.sh。固定姿态 PASS、V1/V2 均 TF_UNAVAILABLE；所有原文件保留。脚本 0 不等于各工具或退出通过。
5. 外部 TF 文本和图有 world/base_link，故执行一次有界诊断：domain 117，唯一参数变化 backend.tf_timeout_s 0.5→5.0（其余数值、帧、RMW、几何、状态时限不变）。独立 SOP 副本与 patch 留档，未修改上游源文件或安装配置；固定姿态 PASS，V1 超看门狗拒绝，V2 七段规划 PASS。上限 360 秒、host 400 秒；本轮均未超时。不继续重跑直到通过。
6. 离线独立校验完整 YAML 的关节顺序、时间递增、有限位置/速度/加速度、规划器数值位置限位、时长与状态预算、simulation_only、空 target_rad；对未输出的工具插入/退出明确保留起点假设。此阶段不执行新轨迹。初版解析器在 URDF 的 {-2*pi}/{2*pi} 字面量失败，保留脚本/错误；修订只按已阅 planner_config.cpp 数值审计，不能据此声称 ros2_control 已强制限位。
7. 单独检查新包 rosdep 与安装 config/launch/package.xml 源码身份；旧全空间依赖/旧 Python/驱动 lint 失败不覆盖。控制器与 move_group 子进程退出逐条判定，不按 launch/SOP 0 或图清空认定干净退出。
8. 两次 SOP 后进程表仅剩 sleep keeper，再停止补跑容器；原容器亦停止、无 OOM、原 runner 不存在。记录两容器 inspect 与清理。keeper 137 不作 ROS 崩溃计数。
9. automatic/original-index.json 是原始 outputs 索引，含未入库 source.bundle；只登记 bundle SHA。镜像、SDK 和构建二进制不入库；符号链接不复制。index.json 对冻结集全部常规文件计 SHA，不包含自身；其 SHA 登记 manifest。
10. 冻结 ACK/pre-complete 快照；报告及 README、open-questions、manifest/derived_files 同步后才 complete。FSM/Action/Cancel 交孙嘉明；规划事项交常建烁。仅本地交接，不修内核、不发外部消息、不合并或推进基线。

OpenAI Codex 协助编排已有 SOP、独立核验与事实登记；原上游 MIT 声明保留，无算法修改。新规划器成功范围仅为模拟规划，工具候选未由本轮收敛。
