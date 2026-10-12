# 规划与 Action 合并版本验收协议

来源 TEAMMATE-INTEGRATION-20261012；观测 ENV-PLANNER-MERGE-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. ack=CLAIMED 后才工作。核对双父提交与逐路径身份：相对规划父提交改 28 文件，相对 main 父提交仅增加原有 53 个规划文件；原模块均字节不变。合并事实不视为已完成模块接线。
2. 核验自动 25 步 summary、305 原始文件哈希、原 PID/容器与旧事件容器停止。只快照原容器文件系统至新容器，不重启或覆盖原始运行。
3. 补跑沿用无网络/设备/挂载/端口、2 CPU / 4 GiB / 512 PID、cap-drop ALL / no-new-privileges。整个事件受原主对话门禁保护，独立场景与规划 SOP 串行。
4. 14 包/387 C++/269 Python/15 E2E/6 ROS 是本次自动实测。XML 对应 24 个真实 GTest 程序且逐项对应源码身份；新 Action verifier 只覆盖 358/20，再单独计规划 29/4。不把 colcon 的 685 条包装/lint 汇总当独立用例。
5. 补跑未修改的 Action verifier、两包 rosdep、安装文件身份和既有四场景独立程序探针。Mock Task/PickPlace 与独立 Motion 分域运行，40 项检查通过；六次服务器均正常退出，容器仅剩 keeper 后才进入下一步。Mock Cancel 不证明物理停稳。
6. 容器内仅建两处工作空间路径别名，保持交付 SOP 和默认配置原样，域 126 上限 360 秒/host 400 秒。固定姿态通过；V1 超 24 秒状态预算、V2 TF 不可用，两序列均无命令输出。SOP 返回 0 不能覆盖工具子进程 1 或 move_group -11。
7. 核验固定姿态 YAML 的关节顺序、时间单调、有限数值、规划器数值位置界限；记录 URDF 未求值限位字面量，运行时强制限位未验。此 SOP 只规划，不发送规划器轨迹。原自动独立 MoveIt Plan/Execute 另列。
8. 前次默认/5 秒 TF 诊断与本次原样结果分开。相同代码出现不同失败阶段不等于修复；无新证据需要时不重复旧诊断或循环重跑。UBSan、外部 consumer、CLI 图观察诊断只引用历史，不算本次运行。
9. 清理前确认无本轮 ROS 进程/daemon、tracked source diff 为空，仅剩 keeper。停止新容器、收集证据，核实两容器均停止且无 OOM、旧 runner 不在；keeper 137 与 ROS 子进程结果分开。
10. 冻结原始失败、源码/补跑命令、数据、清理与 ACK/pre-complete。source.bundle 只登记 SHA；SDK、镜像、构建二进制不冻结。index 索引常规文件且不含自身，SHA 登记 manifest。文档四处及 derived_files 同步后才 complete；最终回执保存在原始目录，不回写冻结集。

FSM/Action/Cancel 内核问题仅本地回交孙嘉明；规划问题交常建烁，集成侧保留清理/依赖/就绪验证。未接管内核、发外部消息、调用 queue、启动监测、合并或推进基线。OpenAI Codex 协助既有入口编排、只读身份/结果核验和事实登记；无上游算法修改，根 MIT / Action Apache-2.0 声明差异保留。
