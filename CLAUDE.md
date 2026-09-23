# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这是什么

2026 美团挑战赛参赛工作区，两类产出并存：

- **可追溯的方案文档**：中文 Markdown 分析 + 归档的原始比赛资料。把规则 PDF、用户口头确认的决策、厂商资料整理成带出处的文档，核心是**事实溯源约定**。
- **Gazebo Classic + ROS 2 仿真与实验**：`demo/` 的 Python 录制/评测入口，`simulation/` 的两个 ROS 2 包；已做单块钩取 demo、RGB-D 抓取前视觉修正、三块逐次观察集成、力矩鲁棒控制对照。全部是仿真，**尚无实机验证**。

动手前先读 `README.md`、`docs/rules-summary.md`、`docs/open-questions.md`；改代码或跑仿真先读 `demo/README.md`、`demo/SETUP.md`。

## 事实链路（必须理解的整体结构）

```
比赛资料                                        仿真实验
materials/original/  原件，只增不改            outputs/<运行目录>/  原始运行（gitignore，不入库）
        ↓ 派生                                         ↓ 冻结摘要
materials/extracted/ + previews/               docs/experiments/<实验>-<日期>/  协议、inputs、summary、index（入库）
        ↓ 登记                                         ↓ 登记（含 index_sha256）
                    materials/manifest.json  唯一的来源注册表
                                  ↓ 引用
                    docs/*.md → README.md    分析、方案与实验记录
```

`materials/manifest.json` 是整个仓库的枢纽，四类条目：

- `sources`：比赛原件（Windows 原始路径、SHA-256、页数、页面尺寸、提取方式）；另有本地仿真实验、GitHub release、研究文献（`type` 字段区分，实验条目带 `report`、`index`、`index_sha256`、`algorithm_provenance`）。
- `project_decisions`：**用户口头确认的每一条事实**，保留 `original_text` 原话、`confirmed` 结构化结论、`scope_note` 未覆盖范围、`subsequent_resolutions` 后续澄清链。
- `external_references`：厂商/官方网页、队友仓库、招聘页，含 `accessed_on`、可识别版本、用途；网页不归档为本地原件。
- `local_observations`：本机环境检查、demo 审计/录制/发布准备等只读或过程记录，写明 `scope` 和方法。

每条都有 `derived_files`，列出引用了它的文件——这是双向索引，改文档要回头补这个字段。

标识体系（文中引用一律用标识，不用文件名）：

| 类别 | 标识 | 引用方式 |
| --- | --- | --- |
| 比赛 PDF | `RULES` / `FAQ` / `MAP` | 必须带 PDF 页序页码，如 `RULES p4` |
| 用户提供图片 | `BATTERY-RENDER` / `BATTERY-DRAWING` | **不得编造页码**，用视图位置描述 |
| 用户确认 | `USER-<HW|RULE|EE|SIM>-<日期>[-<序号>]` | 无页码，注明「用户会话」或「用户转述组委会」 |
| 仿真实验 / 发布 | `VISION-*-<日期>` / `ROBUST-CONTROL-<日期>` | 指向 `docs/experiments/` 冻结证据和对应实验文档 |
| 本地观测 | `ENV-*` / `DEMO-*-<日期>` | 注明观测范围，不外推到部署环境 |
| 研究文献 | `CTRL-SLOTINE-1985` | 注明文献 |
| 外部网页 | `AUBO-*` / `RS-*` / `CV-*` / `VAC-*` / `TEAMMATE-*` / `POLYU-*` | 无页码，注明查阅日期 |

`docs/open-questions.md` 的 Q01–Q16 是稳定编号：已解决的**不删除**，改标 `（已确认）` / `（部分确认）` 并保留历史差异。

## 新增事实时的同步义务

用户给出新决策/新资料，或完成一次要入库的实验时，一次改动通常要落到四处，缺一处就会出现文档间不自洽：

1. `materials/manifest.json` 加条目（用户决策保留原话、写清 `scope_note`；实验登记冻结证据目录和 `index_sha256`）。
2. 对应的 `docs/*.md` 正文。
3. `docs/open-questions.md`（新增待确认项，或把旧项标为已确认并写明被谁澄清；实验缺口写在文末「实验缺口」段）。
4. `README.md` 现状段 / 项目入口 + 该条目的 `derived_files` 列表。

## 代码结构

- `demo/run.sh`：source ROS Humble 和 `${AUBO_ROS2_WS:-$HOME/aubo_ros2_ws}` 后 exec `/usr/bin/python3 demo/record.py`。`record.py` 是唯一仿真入口：起 Gazebo、生成世界、执行冻结轨迹、录视频、写 `outputs/demo-*`。模式开关：`--check`、`--smoke`、`--vision off|observe|correct`、`--sequence`、`--control position|pd|pd_matched|smc`、`--robust-probe`。
- `demo/vision.py`（RGB-D 检测与局部 IK 修正）、`sequence.py`（三块逐次）、`metrics.py`（抓放判定）、`robust_probe.py`；离线工具 `report.py`（轨迹/误差图）、`replay_vision.py`（重放已存相机快照，不需 ROS）、`run_matrix.py` / `summarize_matrix.py` / `run_robust_matrix.py` / `summarize_contacts.py`；测试 `test_*.py`。
- `demo/data/`：`sequence-v1.json` 是历史轨迹冻结副本，`provenance.json` / `vision-provenance.json` 记来源、哈希和 AI 使用说明。
- `simulation/meituan_sim/`：S3 + 钩具 + D435i 的 xacro、控制器配置、launch，`scripts/gen_scene.py` 在构建时生成电池/底图/world。
- `simulation/meituan_robust_control/`：C++ 力矩控制插件（重力补偿＋边界层滑模，继承 Humble JTC），单测 `test/test_sliding.cpp`。
- `simulation/provenance.json`：自建源码出处与打包改动。上游 `aubo_description` 由 `demo/setup-workspace.sh` 锁定提交 `47fa5e02…` 获取，**不归档进本仓库**。

## 常用命令

```bash
# Python 单测（离线，不需 ROS/Gazebo；用 unittest，不是 pytest）
python3 -m unittest discover -s demo -p 'test_*.py'

# 构建仿真工作空间（三个包；已存在且提交不符时脚本停止，不 reset）
export AUBO_ROS2_WS="$HOME/aubo_ros2_ws"; bash demo/setup-workspace.sh

# C++ 滑模单测（在工作空间里）
cd "$AUBO_ROS2_WS" && colcon test --packages-select meituan_robust_control && colcon test-result --verbose

# 仿真：只检查 → 静态短录 → 完整单块；视觉/三块/力矩见 demo/README.md
bash demo/run.sh --check
bash demo/run.sh --smoke
bash demo/run.sh

# 核验比赛原件完整性（与 manifest.json 的 sha256 比对）
sha256sum materials/original/*

# 提取 PDF 文本层（FAQ/MAP 有文本层，RULES 没有）
python3 -c "import fitz,sys; d=fitz.open(sys.argv[1]); [print(f'--- PDF PAGE {i+1} ---\n{p.get_text()}') for i,p in enumerate(d)]" "materials/original/《2026挑战赛FAQ》.pdf"

# 把扫描版 RULES 渲染成图再用 Read 目视核对（唯一可靠的读法）
python3 -c "import fitz; d=fitz.open('materials/original/《2026年挑战赛规则及赛题说明》.pdf'); d[3].get_pixmap(dpi=180).save('/tmp/rules-p4.png')"
```

仿真环境：Ubuntu 22.04（WSL2，需 WSLg 才能渲染相机）、ROS 2 Humble、Gazebo **Classic 11**（实验用 11.10.2，不支持换 Harmonic）。`record.py` 写死 `ROS_DOMAIN_ID=67`、`GAZEBO_MASTER_URI=http://127.0.0.1:11365`，**同一台机器只能跑一个实例**。退出码：0 通过、2 抓放检查未通过、1 运行或录制错误；smoke 通过不代表抓取通过。

2026-09-06 的只读观测（`ENV-LOCAL-20260906`）：`/usr/bin/python3` 3.10.12，有 `fitz`、`cv2`、`numpy`、`PIL`，**没有 `pyrealsense2`**，未验证真实相机可枚举；不代表最终部署环境。

文件名含中文和《》书名号，shell 里必须加引号。

## 内容红线

- **RULES PDF 是扫描件，文本层为空**：绝不能把空提取结果当成「文中没有」，必须渲染成图目视核对，并说明核对了哪几页。
- **区分已确认 / 工程推算 / 待确认**：图纸尺寸是「设计名义值」不是实测；CAD 渲染不能证明表面气密、提手强度或颜色阈值；厂商示例参数不是本项目实测值。文档冲突保留进 open-questions，不擅自消解。
- **仿真不外推**：仿真结果不代表实物承载或实机；demo 的稳定/扰动阈值是工程判据，不是新增比赛规则；没有接触对监测就不能声称全程无碰撞；视觉修正与对照组同样通过时不能声称成功率提升；力矩控制不是形式化安全证明。失败运行和开发中的失败（如蓝块掉落）保留记录，不删。
- **单位**：`BATTERY-DRAWING` 图内未标单位，全项目暂按 mm 解释并每次注明。
- **内框 70% 只管内框**：`USER-RULE-20260906-02` 的 `Area(主体投影 ∩ 内框)/Area(主体总投影) ≥ 0.70` 仅适用于序列内框；T0（RULES p3）和序列外框（RULES p4）仍按「主体完整位于框内」，不要外推。与 RULES p4 原文的差异是已知的，保留在 Q15。
- **末端三方案并列**：方案一钩取提手（`USER-EE-20260906-01`）、方案二侧面吸盘（`USER-EE-20260906-02`）、方案三卡环（`USER-EE-20260906-04`）尚未选型，不要在文档里替用户收敛成一个。仿真只做了方案一的接触物理，吸盘不做仿真（`USER-SIM-20260906-03`），这不等于选型。此前的「平行两指夹持」只是历史候选，当前没有夹爪。
- **任务口令**：文中的「蓝—红—黄」只是示例，正式口令比赛日公布，不得写死。
- **硬件未确认不假定**：新获得的硬件参数、技术选择和规则答复及时更新文档；未确认时不假定品牌、驱动、SDK 或控制接口。
- **披露**：引用开源代码/第三方算法/生成式 AI 需记录仓库、版本、许可证和修改范围，供技术报告披露（FAQ p6, Q17）。文档末尾的「使用 OpenAI Codex 协助…」段落、`demo/data/provenance.json`、`simulation/provenance.json` 都是这个用途，新增文档和代码照此办理。`aubo_description` 的许可证冲突（package.xml 写 BSD、无 LICENSE 文件）保留在 manifest，不替其重新授权。

## 仓库状态

`main` 跟踪 `origin`（GitHub `AfonsoZhang/meituan-robotics-challenge-2026`），已发布 release `demo-v1.0.0`、`vision-v1.1.0`。原始 PDF/JPG 和 `docs/experiments/` 冻结证据入库；`outputs/`、`runs/`、`datasets/`、`checkpoints/`、`recordings/` 在 `.gitignore`。

本机工作规则（2026-09-23 起本仓库由 Claude 一个人负责，不再与 Codex 分工）在本机专用的 `.claude/CLAUDE.md`，计划与进度在 `.agents/`（均不提交）。

每次改动后可用下面这句自查「文档引用的标识是否都已登记」（输出为空即通过）：

```bash
comm -23 \
  <(grep -rhoE 'USER-[A-Z]+-[0-9]{8}(-[0-9]+)?|(VAC|AUBO|RS|CV)-[A-Z0-9]+|(VISION|ROBUST|DEMO|ENV)-[A-Z-]+-[0-9]{8}|CTRL-[A-Z]+-[0-9]{4}|TEAMMATE-[A-Z]+-[0-9]{8}|POLYU-[A-Z0-9]+(-[A-Z0-9]+)*' README.md docs/*.md demo/*.md materials/README.md | sort -u) \
  <(python3 -c "import json;d=json.load(open('materials/manifest.json'));print('\n'.join(sorted(e['id'] for k in ('sources','project_decisions','external_references','local_observations') for e in d[k])))")
```
