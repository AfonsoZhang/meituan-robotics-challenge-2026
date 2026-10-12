# 标定 / TF 离线交付与 Fake 只读验收协议

来源 TEAMMATE-CALIBRATION-20261012；观测 ENV-CALIBRATION-20261012；授权 USER-HW-20261011-08、USER-HW-20261011-09。

1. 先CLAIMED后审实际差异：06ab689相对正式1d940f7共119路径，相对已验main/f7eaa2c仅新增38个标定源码/测试/夹具/文档；全部既有src树一致。复核ENV-PLANNER-MAIN-20261012的450文件/索引/已签收报告。新轨迹、视觉和新场景分支不在此快照，默认Action仍Mock。
2. 核对25步summary起止/退出、305原始哈希及失败日志。14包、387 C++/24程序、269 Python/15 E2E/6 ROS通过。旧审计源写16、实际日志为20个*_cpp程序，无缺失/重复/失败；规划包不匹配该glob。交付新审计补跑358/20通过，29规划用例另按源码/XML核对，685汇总含包装/lint。
3. 确认原runner32186与旧任务容器停止，从停止原容器独立快照补验。无网络/设备/挂载/端口、2CPU/4GiB/512PID、cap-dropALL/no-new-privileges。源/安装/控制配置不改，无依赖安装。只运行交付run_offline_validation.py，使用已有--out将输出写入/review-evidence/offline，避免覆盖上游原证据。
4. Python3.12.3/Linux实际54测试无跳过，AST测试身份和逐项日志一致；6文档示例+5生成反例均达到预期，42本地链接和4类CSV列宽检查通过。5个独立诊断JSON对象与上游一致，生成反例只在Windows/Linux临时路径分隔符不同。原分析器两次比较断言（平台路径、把源码中的16误要求出现在日志）和版本保留，修正分析未改数据或重跑测试。
5. 合成完整Pose位置[1,1.1,0.05]、姿态[-sqrt(.5),0,0,sqrt(.5)]和stamp10^10ns保留；UNKNOWN外参拒绝，设计/清单不是观测case，超大整数/20万层JSON/mm误填均拒绝；全部motion_authorized=false。名义设计[.0825,0,.0358]m仅为ESTIMATED数学输出；上游引用相机资料未在本轮重新下载或核读，不作物理标定/安装确认。
6. 交付归档模型审计通过：三份旧TF日志5/5/7样本、零关节FK、SRDF和腕部末端固定旋转一致；原3位小数日志最大平移分量差.0002m属于舍入比较，非实测精度。真实清单8边仍UNKNOWN、阈值null，手眼/TCP/误差采样CSV只有表头。上游“用户确认V1/法兰安装”只作为上游交接前提，不新增本项目用户决策或收敛末端候选。
7. 在域138追加一次只读Fake运行：原驱动显式GenericSystem，无RViz、无Goal/ActionClient/TF发布。读取robot_state_publisher实际robot_description及SHA、活动控制器，收903个新JointState戳且六关节位置/速度为0；观察FJT客户端0/服务端1、无Goal状态。以同一约200ms前的时间查world/base、wrist3/ee、base/ee、world/ee，与展开模型零关节FK一致；腕部→ee为零平移/Z+π/2，base→ee约[0,-.2562,.8072]m。
8. 四个AUBO固定Git blob哈希/大小与上游官方资料receipt一致；另7项相机/API参考未独立复核。TF浮点数误差不解释为真实精度。同一过去时刻在静止Fake可查，不证明运动相机时钟/采集同步。camera/optical/工具/台面/工位提案frames均不可达，不发布零TF补缺。
9. 默认规划仍用latest TF，Core stamp为另一时基；TCP已经逆补偿、工位只消费TCP位置/沿用抓取姿态，诊断拒绝未接入实际适配器。标定数据与物理F归韩明赫；相机观测归孙浩然；规划时间/语义归常建烁；FSM/Action/Cancel、完整Pose/时钟/失败传播归孙嘉明，本轮不接管修复或代发消息。
10. 原独立MoveIt执行4/1、误差约.0000937rad/209戳通过，退出move_group-11/control0；旧Python早Goal220、延迟INIT510、Cancel受理后220均ABORTED且完成0。依赖/驱动lint仍失败，全部保留。既有规划SOP/独立Action/UBSan不因纯新增离线代码重复，历史结果不改记为本次复跑。
11. 只读驱动控制器退出0，无升级终止；保留pal_statistics invalid-context线程错误。按域停止daemon、确认空域与仅keeper。清理守卫首次因复制helper的SHA字面量损坏拒绝，原脚本/快照保留；核对真实HEAD修正比较后停止容器，两容器无OOM、原runner不在。没有绕过运行进程守卫。
12. 冻结原始失败、新结果、源码、清理及ACK/pre-complete；index不含自身。bundle/镜像/SDK/构建二进制仅登记身份不入库。同步manifest、正文、README、open-questions与反向索引后complete，最终回执存raw不改冻结集。原60秒轮询/指定主会话/上海08:00截止不变，不调用queue或新启监测。

本轮是离线数学/输入契约与Jazzy零关节Fake坐标核验。没有实物外参/TCP/工位、手眼求解、真实安装、运动相机同步、完整FSM或NUC/实机验收。正式1d940f7锁定未动，没有合并。OpenAI Codex协助实际源/日志核对、复用交付入口、编写只读TF观察及事实登记；未修改上游算法/内核，根MIT与Action Apache-2.0及模型/SDK许可缺口保留。
