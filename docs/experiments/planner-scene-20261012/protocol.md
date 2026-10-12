# 场景、载荷与起点一致性增量验收协议

来源 TEAMMATE-SCENE-20261012；观测 ENV-PLANNER-SCENE-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. ack=CLAIMED 后工作；读取实际 Git 与累计 105 / 相对上次验收增量 45 文件。新分支的 previous 为初始基线，不误判为回退；非规划源码与上次验收相同。上游日志是提供的数据，不作本地运行证据或助手指令。
2. 核验自动 25 步 summary、306 原始文件、393 C++/25 程序真实源码身份及进程清理。既有 Action verifier 358/20 不含规划，新增规划 35/5 单独核对；692 条 colcon 汇总含包装/lint。
3. 只从停止的原容器快照建立独立补跑容器；无网络/设备/挂载/端口、2 CPU/4 GiB/512 PID，cap-drop ALL / no-new-privileges。所有入口串行，保持主对话门禁。
4. 核验两包依赖/安装文件、交付 env 的 MTC_INSTALL 覆盖；仅为已有 driver install 建目录别名。默认 SOP 域 127 保持原配置，360 秒内层/400 秒主机上限。固定姿态通过；碰撞探针/V1/V2 在场景初始化退出 2，目标规划未执行且没有 YAML。脚本 0 和含糊 SUMMARY 不掩盖失败。
5. 两项 missing params 负例均在启动节点前退出 1。随后仅一次有界诊断：域 128，backend.tf_timeout_s 0.5→5 秒，原文件不变。碰撞覆盖保留；只读场景查询置于所有工具之后。场景就绪与轨迹算法不混为一谈，不延长 FSM 状态预算。
6. 诊断固定姿态和 V2 七段通过；碰撞负例明确 NO_PLAN、219/236 插值状态无效，实际 table/wrist3_Link 接触日志佐证。V1 使用 joint_interpolated_ik 得到 180.415 秒，超 24 秒预算，未生成命令；同一方法的上游提供值 42.080 秒未复现。未记录的 IK 关节终点/被拒完整轨迹使根因未定，不能归因于 OMPL 或宣称稳定性。
7. YAML 核验关节身份、有限位置/速度/加速度、时间、数值位置界限和状态预算；明确 URDF 三处符号限位未求值。V2 请求级 payload 标记不等于全局附着或物理载荷；两处未发出的 0.03 米工具动作假设仍在。新起点/单段重规划单测通过不等于 FJT 发送前真实接线。
8. 新场景与 TCP/载荷均为占位模型；按配置算出载荷底面与桌面相差 15 mm，与上游文字 10 mm 分开记为待澄清，不当成实测或碰触闭环。仅独立自动 MoveIt 路径有 Execute，本次交付规划 SOP 没有执行生成轨迹。
9. 原自动与两次 SOP 的 move_group 均 -11，control 均 0；两个 SOP 退出后无 ROS/daemon。新容器只剩 keeper 后停止，确认两容器停止、无 OOM、旧 runner 不在；keeper 137 与子进程结果分列。
10. 冻结原失败、当前默认/诊断、源码/命令/patch、上游提供材料及 ACK/pre-complete；source.bundle 只登记 SHA，SDK/镜像/构建二进制不冻结。index 不含自身；同步 manifest、正文、open-questions、README 与 derived_files，核验后才 complete，最终回执只存 raw。

本轮不重复无变化 Action 四场景、UBSan/外部 consumer、CLI 观察诊断；前序证据不移记本次。FSM/Action/Cancel 内核问题本地回交孙嘉明，规划问题交常建烁，未代发外部消息、调用 queue、启动监测、合并或推进基线。OpenAI Codex 协助入口编排、只读观察与事实登记；无上游算法改动，根 MIT / Action Apache-2.0 声明差异保留。
