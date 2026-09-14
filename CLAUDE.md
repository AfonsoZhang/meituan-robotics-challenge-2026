# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这是什么

2026 美团挑战赛参赛工作区，目前**没有源码、没有构建/测试命令**，全部产出是中文 Markdown 分析文档 + 归档的原始比赛资料。工作内容是「把规则 PDF、用户口头确认的硬件决策、厂商资料整理成可追溯的方案文档」，所以本仓库的核心不是代码结构，而是**事实溯源约定**。动手前先读 `README.md`、`docs/rules-summary.md`、`docs/open-questions.md`。

## 事实链路（必须理解的整体结构）

```
materials/original/    原件，逐字节归档，只增不改（三份 PDF + 两张 JPG）
        ↓ 派生
materials/extracted/   PDF 文本层逐页提取；materials/previews/ 屏幕预览 PNG
        ↓ 登记
materials/manifest.json  唯一的来源注册表
        ↓ 引用
docs/*.md → README.md    分析与方案
```

`materials/manifest.json` 是整个仓库的枢纽，三类条目：

- `sources`：原件的 Windows 原始路径、SHA-256、页数、页面物理尺寸、提取方式。
- `project_decisions`：**用户口头确认的每一条事实**，保留 `original_text` 原话、`confirmed` 结构化结论、`scope_note` 未覆盖范围、`subsequent_resolutions` 后续澄清链。
- `external_references`：厂商/官方网页，含 `accessed_on`、可识别版本、用途；网页不归档为本地原件。

每条都有 `derived_files`，列出引用了它的文档——这是双向索引，改文档要回头补这个字段。

标识体系（文中引用一律用标识，不用文件名）：

| 类别 | 标识 | 引用方式 |
| --- | --- | --- |
| 比赛 PDF | `RULES` / `FAQ` / `MAP` | 必须带 PDF 页序页码，如 `RULES p4` |
| 用户提供图片 | `BATTERY-RENDER` / `BATTERY-DRAWING` | **不得编造页码**，用视图位置描述 |
| 用户确认 | `USER-<HW|RULE|EE>-<日期>-<序号>` | 无页码，注明「用户会话」或「用户转述组委会」 |
| 外部网页 | `AUBO-*` / `RS-*` / `CV-*` / `VAC-*` | 无页码，注明查阅日期 |

`docs/open-questions.md` 的 Q01–Q15 是稳定编号：已解决的**不删除**，改标 `（已确认）` 并保留历史差异。

## 新增事实时的同步义务

用户给出新决策/新资料时，一次改动通常要落到四处，缺一处就会出现文档间不自洽：

1. `materials/manifest.json` 加条目（保留用户原话，写清 `scope_note`）。
2. 对应的 `docs/*.md` 正文。
3. `docs/open-questions.md`（新增待确认项，或把旧项标为已确认并写明被谁澄清）。
4. `README.md` 现状段 + 该条目的 `derived_files` 列表。

## 常用命令

无构建、无测试。可复现的操作只有资料核验与读图：

```bash
# 核验归档完整性（与 manifest.json 的 sha256 比对）
sha256sum materials/original/*

# 提取 PDF 文本层（FAQ/MAP 有文本层，RULES 没有）
python3 -c "import fitz,sys; d=fitz.open(sys.argv[1]); [print(f'--- PDF PAGE {i+1} ---\n{p.get_text()}') for i,p in enumerate(d)]" "materials/original/《2026挑战赛FAQ》.pdf"

# 把扫描版 RULES 渲染成图再用 Read 目视核对（唯一可靠的读法）
python3 -c "import fitz; d=fitz.open('materials/original/《2026年挑战赛规则及赛题说明》.pdf'); d[3].get_pixmap(dpi=180).save('/tmp/rules-p4.png')"
```

本机（WSL Ubuntu 22.04，`/usr/bin/python3` 3.10.12）已有 `fitz` 1.28.0、`cv2` 4.13.0、`numpy` 2.2.6、`PIL`；**没有 `pyrealsense2`**，也未验证过相机可枚举。这些是只读观测，不代表最终部署环境（见 `ENV-LOCAL-20260906`）。

文件名含中文和《》书名号，shell 里必须加引号。

## 内容红线

- **RULES PDF 是扫描件，文本层为空**：绝不能把空提取结果当成「文中没有」，必须渲染成图目视核对，并说明核对了哪几页。
- **区分已确认 / 工程推算 / 待确认**：图纸尺寸是「设计名义值」不是实测；CAD 渲染不能证明表面气密、提手强度或颜色阈值；厂商示例参数不是本项目实测值。文档冲突保留进 open-questions，不擅自消解。
- **单位**：`BATTERY-DRAWING` 图内未标单位，全项目暂按 mm 解释并每次注明。
- **内框 70% 只管内框**：`USER-RULE-20260906-02` 的 `Area(主体投影 ∩ 内框)/Area(主体总投影) ≥ 0.70` 仅适用于序列内框；T0（RULES p3）和序列外框（RULES p4）仍按「主体完整位于框内」，不要外推。与 RULES p4 原文的差异是已知的，保留在 Q15。
- **末端两方案并列**：方案一钩取提手（`USER-EE-20260906-01`）、方案二侧面吸盘（`USER-EE-20260906-02`）尚未选型，不要在文档里替用户收敛成一个；此前的「平行两指夹持」只是历史候选，当前没有夹爪。
- **任务口令**：文中的「蓝—红—黄」只是示例，正式口令比赛日公布，不得写死。
- **硬件未确认不假定**：新获得的硬件参数、技术选择和规则答复及时更新文档；未确认时不假定品牌、驱动、SDK 或控制接口。
- 引用开源代码/第三方算法/生成式 AI 需记录仓库、版本、许可证和修改范围，供技术报告披露（FAQ p6, Q17）。现有文档末尾的「使用 OpenAI Codex 协助…」段落就是这个用途，新增文档照此办理。

## 仓库状态

Git 已初始化但**尚无任何提交**，全部文件仍是 untracked。原始 PDF/JPG 有意纳入版本管理；`.gitignore` 预留了 `datasets/`、`checkpoints/`、`recordings/`、`outputs/`、`runs/` 给后续实验产物。

每次改动后可用下面这句自查「文档引用的标识是否都已登记」：

```bash
comm -23 \
  <(grep -rhoE 'USER-[A-Z]+-[0-9]{8}(-[0-9]+)?|VAC-[A-Z]+|AUBO-[A-Z0-9]+|RS-[A-Z0-9]+|CV-[A-Z]+' README.md docs/*.md | sort -u) \
  <(python3 -c "import json;d=json.load(open('materials/manifest.json'));print('\n'.join(sorted(e['id'] for k in ('sources','project_decisions','external_references') for e in d[k])))")
```
