# 技术报告绘图与 PDF 导出

本目录只处理技术报告的文字呈现、矢量图与 PDF，不连接机器人、不运行仿真。脚本由 OpenAI Codex 辅助编写。

`draw_tool.py` 读取归档的固定 STEP 文件，先核验 SHA-256、名义包络和体积，再输出中文四视图。模型未修改；CAD 参考 TCP 与槽底中心沿用报告定义。原始用户 PNG 保持不变。网格与投影的显示精度记在配图来源 JSON 中，不作为实物测量精度。

`export_pdf.py` 从 Markdown 读取全部内容。公式通过 MathJax 转成 SVG；三张流程图由 `render_diagrams.py` 按适合 A4 的固定布局渲染，节点和连线逐条与 Mermaid 源码核对，未知节点或连线会使导出失败。Mermaid 源码仍可独立编辑。正文采用 10.5 pt 宋体，标题与图内标签采用微软雅黑；A4 及 20 mm 页边距，目录、书签、页码自动生成。标题、正文和流程图使用黑白灰，表格为白底三线表。舌规图沿用既有配色与几何。系统架构图左侧将相机和标定并列接入感知模块，反馈线与输入线分开；交付正文、图内及图题已删除工具版本前缀“V1”，原始资产文件名保留以便追溯。

Python 依赖见 `requirements.txt`，Node 依赖见 `package.json`。建议在独立环境中安装。系统需有微软雅黑字体；宋体可通过 `--body-font` 指定，导出器也会检查本地字体目录及 Windows 字体目录，未找到时回退为微软雅黑。绘图检查使用仓库现有的 `nature-figure` 技能脚本。报告中的 GitHub 超链接已按用户要求移除，固定版本及地址仍保存在来源清单。仓库内资料链接指向本地文件，不伪造在线地址。

依赖就绪后，在仓库根目录运行：

```bash
python3 tools/report/draw_tool.py
python3 tools/report/export_pdf.py
```

两个入口分别支持 `--dependency-path` 和 `--node-modules`，可使用外置依赖目录。本次实际使用隔离临时目录安装 CAD 和 Node 依赖，未替换系统 Python 包。输出为 `docs/技术报告.pdf`、`docs/assets/report-v0.4/` 下的矢量图、PNG 预览、Mermaid 源文件及来源信息。HTML 和检查预览写入已忽略的 `outputs/report-v0.4/`。

检查包括源稿差异、尺寸/TCP/公式/指标保持、三张图的节点与连线、四视图对齐、图中文字及线条碰撞、PDF 字体嵌入与逐页目视检查。该检查不新增实机、标定或承载验证。CAD 来源及许可范围沿用 `TEAMMATE-FIELD-20261015` 的原有声明，各导出依赖仍按各自许可证使用。
