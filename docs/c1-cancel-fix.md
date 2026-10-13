# C1 延迟取消的独立修复 PR 与复验

**C1 已单独提交并推送 [PR #15](https://github.com/F1u0rite/meituan_challenge_ws/pull/15)。** 候选提交 `8603e18e06ad3e8f7f2c0e4cad7e8ae716a3abbe` 基于 main `b4185155383541e1a4161587c4049a162f74b36d`，仍待审、未合并。正常软件 Mock 的延迟取消返回 `CANCELED/0`，同栈再次受理的新任务成功；独立分支 366 项 C++ 用例通过。用户后续明确“单独提交”“单独推送PR”，因此先前组合提交 `062811e` 已通过普通 revert `8f11750` 从 PR #8 撤出，PR #8 源码树与原 `7da4322` 相同。来源：USER-HW-20261013-03（用户会话）、TEAMMATE-CANCELPR-20261013（2026-10-13 查询）、ENV-CANCEL-PR-20261013（本机独立复验）；原组合记录继续使用 TEAMMATE-CANCELFIX-20261013 / ENV-CANCEL-FIX-20261013。正式 pin 保持不变，完整 FSM/FJT、NUC 和实体设备仍未验收。

## 根因与修改

原 PR head 为 `7da43228d602a6b23571bfc599d69529ef7bea23`。底层 Mock 运动即时完成，停稳证据仅保存一次；上层 Future 延迟 700 ms 交付时，PickPlace 的 10 ms 定时器每次仍推进 ManualClock 20 ms。400 ms 后证据龄期约 0.8 s，超过 Core 的 0.3 s 门限。新增确定性回归记录旧反馈 1.7 s、当前时间 2.5 s，原代码返回 520；真实父子 Action 同样复现，完成数 0，下一 Goal 被拒。

修复只增加 `MockMotionAdapter::sample_stationary_feedback(command_id)` 及 AsyncMockMotion 的调用。在适配器锁内读取当前虚拟关节状态，要求同一已知停稳命令、没有在途命令或队列、关节状态未变、采样时间有限且不倒退。保留命令身份和原停稳区间；取得新的虚拟观测后，仍由原 Core 判定。`stop_evidence()` 本身继续返回可能过期的快照。

MotionExecutorCore、0.3 s 新鲜度门限、FSM/ActionSlot/IDL 均未修改。缺失、未知、超时、错误 ID、带载取消与原过期快照负例继续保留。**这是 Mock 内部完整已知状态的显式采样，不是机械臂传感反馈，不能作为实机/FJT“刷新旧时间戳”的实现。** Cancel ACK 与停止完成继续分别判断。

## 独立分支的 main 基线复验

在新的隔离 Jazzy 容器中，从 main 构建六包并测试五个相关 C++ 包：**366 项实际用例通过**（322 Core/Mock + 44 Action，新增 8 项），无失败、错误或跳过。colcon 含 20 个包装项显示 386。源文件与容器字节核验、二进制哈希和完整测试身份见 [独立复验摘要](experiments/c1-standalone-pr-20261013/summary.json)。

独立分支额外加入 `TaskAction.DelayedCancelWaitsForChildStopThenAllowsNextTask`：真实父子 Action 在结果交付延迟 700 ms、移动 Feedback 后等 400 ms 取消，父任务最终 CANCELED/0、完成数 0、执行/停止各一次；同栈下一任务 SUCCEEDED/0、完成数 1。该测试不依赖 PR #8 的 Bringup 或 Web UI。三个运行源码文件及原三个回归文件与先前组合补丁逐字相同；本分支再增加父任务回归。

本次独立 PR 只有三个运行源码文件、四个测试文件、包 README 和修复说明；无 Bringup/Web UI 改动。容器已停止，OOMKilled=false。冻结目录含 **124 个索引成员**；[index.json](experiments/c1-standalone-pr-20261013/index.json) SHA-256：`4c5057842ea67460698ea01bdae27f150a141154ce9fa49add6c9b163b991f2a`。

## 原 PR #8 组合复验（单独保留）

下列 365 项测试及七个独立进程场景运行于 `062811ed2895eadc8b41efe8a8d7b2acff03fe92`（C1 + 原 PR #8），不是独立 PR 提交的运行结果。原冻结目录和索引哈希保持不变。

环境：Ubuntu 24.04.5 x86_64 / ROS 2 Jazzy / C++17，独立容器 2 CPU / 4 GiB，network=none，无设备、宿主挂载或端口映射，cap-drop ALL。首次从固定源构建 7 包，修改的两个包清理重编；[源码字节核验](experiments/c1-cancel-fix-20261013/meta/source-integrity.json)覆盖 225 个编译相关文件。新采样符号和编译前后二进制哈希均保存。

- 旧代码反证：2 个延迟取消正例失败、1 个缺证反例通过；独立父子 Action 重现 ACK 后 `ABORTED/520` 并拒绝下一任务。
- 修复版：**365 项实际 C++ 测试通过**，无失败、错误或跳过；包括原有 358 项和新增 7 项。322 项 Core/Mock、43 项 Action；colcon 加入 20 个包装项显示 385，不重复计为功能用例。
- 原 `StaleFeedbackCannotConfirmStop` 仍通过拒绝断言；新增错误 ID、启动/在途无证据、未知/超时、倒退和非有限时钟测试通过。

以下全部经实际安装的 C++ Task → PickPlace，保存父子 UUID、真实 Feedback/Result、ACK、只读就绪图、日志和清理；没有注入或修改 Result：

| 配置 | 取消延迟 | 结果交付延迟 | 父子终态 | 后续任务 |
| --- | ---: | ---: | --- | --- |
| success | 0 ms | 700 ms | CANCELED/0，完成 0 | 未另发 |
| success | 200 ms | 700 ms | CANCELED/0，完成 0 | 未另发 |
| success | 400 ms | 700 ms | CANCELED/0，完成 0 | 同栈 SUCCEEDED/0，完成 1 |
| success | 600 ms | 700 ms | CANCELED/0，完成 0 | 未另发 |
| success | 1000 ms | 1500 ms | CANCELED/0，完成 0 | 未另发 |
| cancel_unconfirmed | 400 ms | 700 ms | ABORTED/520，完成 0 | 拒绝 |
| status_unknown | 不取消 | 700 ms | ABORTED/230，完成 0 | 拒绝 |

400 ms 正例父 UUID `4c56c2e355434b12b75147e3751ae784`，子 `82159e1cc33f588ddeae3552d5f1e68d`；同栈新 Goal `c6bc2a85cc15438c8428b3ee4c52b0aa`。完整结果见 [summary.json](experiments/c1-cancel-fix-20261013/summary.json)，逐场景结果见 `container/fixed/`。所有七个修复场景的 supervisor、Task、PickPlace 均退出 0，图排空。

## 复现

独立分支按 [提交内 SOP](https://github.com/F1u0rite/meituan_challenge_ws/blob/8603e18e06ad3e8f7f2c0e4cad7e8ae716a3abbe/docs/migration/C1_DELAYED_CANCEL_FIX_20261013.md) 构建和运行回归：

```bash
colcon build --packages-up-to mtc_ros2_action_cpp --executor sequential \
  --cmake-args -DBUILD_TESTING=ON -DCMAKE_CXX_STANDARD=17
source install/setup.bash
colcon test --packages-select mtc_motion_execution_cpp mtc_ros2_action_cpp \
  --executor sequential --event-handlers console_direct+
colcon test-result --verbose
```

以下 CLI 需要组合原 PR #8 与本补丁，或使用已冻结组合提交 `062811e`；独立 PR 本身不提供 Bringup CLI。加载对应 Jazzy 工作空间后，在两个终端使用同一 ROS domain 和全新输出目录：

```bash
ros2 run mtc_cpp_mock_bringup mock_stack --namespace /c1_repro \
  --output-dir /tmp/c1-stack-001 --result-delay-ms 700 --no-web
```

```bash
ros2 run mtc_cpp_mock_bringup mock_task --namespace /c1_repro \
  --output-dir /tmp/c1-client-001 --cancel-at MOVE_PRE_ALIGN \
  --cancel-delay-ms 400 \
  --goal '{"task_id":"c1_repro_001","mode":1,"ordered_colors":[1],"timeout_ms":30000,"placement_stability_sec":3}'
```

应分别检查 ACK 与最终父子 `CANCELED/0`，CLI exit 0 本身只代表取得终态。自动化宿主直接启动安装的 mock_stack 可准确向 supervisor 发送信号；不要只给 `ros2 run` 外层进程发 SIGINT。

## 失败保留与清理

初次基线外部测试给 ros2 CLI 包装进程发 SIGINT 未转发，随后限时终止 wrapper，原 summary 为 CLEANUP_FAIL；真实 C++ 子节点随后退出 0、supervisor 生成 cleanup_ok。该尝试原样留存。改为直接启动安装的 supervisor 后，另存 baseline-clean，再做修复对照；没有修改 Bringup 的清理代码。

首次补丁增量构建因为复制保留的 mtime 早于旧对象而跳过编译。它不计入修复验证；之后以 `--cmake-clean-first` 重编并核验符号、二进制及源文件。两个过程日志都保留。

所有场景结束后，本轮容器已停止、OOMKilled=false。PID1 为 sleep infinity，容器最终 exit 137 单独记录，不计作 C++ 崩溃；初次 wrapper 留下的僵尸随本轮容器停止清理。没有恢复旧监测或操作其他容器。原 [C1 失败报告](cpp-mock-webui-acceptance.md) 与全部冻结证据保持原记录。

冻结目录含 **356 个索引成员**；[index.json](experiments/c1-cancel-fix-20261013/index.json) SHA-256：`4ac6577e8dcb81d2e1194ac7d4590eac3e71ed60b046a3d99f019a9e439b816b`。源码补丁、7 项新增测试、原失败、完整测试身份和构建记录均在冻结目录。

本次范围止于原 PR #8 发现的软件 Mock C1；未验证新浏览器交互，不关闭 M1/FJT 并发、旧 Python 220/510/520、MoveIt 退出、NUC/实机或完整 FSM 问题。既有 Web UI P0 暂存内容和 P1 工作保留，未并入本次独立 PR。

使用 OpenAI Codex 协助根因定位、最小 Mock 补丁、正负回归、日志与文档归档。补丁基于队友仓库根 MIT 代码，原 package.xml/SDK 许可证与厂商校验边界不变；没有重新授权第三方内容。
