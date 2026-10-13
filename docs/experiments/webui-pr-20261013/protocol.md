# Web UI 独立 PR 发布检查 · 2026-10-13

用户授权：USER-HW-20261013-07（原话“推送PR”）。记录：TEAMMATE-WEBUI-PUBLISH-20261013 / ENV-WEBUI-PUBLISH-20261013。

## 候选与边界

- 团队仓库 `89bb7f75994365c1bd3d32ac59f35a81145970c7`，base 为 PR #8 的 `8f11750e0bd2e485826acb904fd31382945ba0b9`；只变更 Web 模块及安装/来源资料。
- 个人源码 `95bfa6002db3dd5330461efcfcd0cc8112323246`，基于最新个人 main `bb7500c`，保留既有主线验收和 C1 记录。原工作区/索引没有被 checkout、reset 或覆盖。
- 当前联合验证仍仅限 C++ Mock / GenericSystem Fake Hardware。本轮只进行离线包构建、测试、来源/文件核验和 GitHub 发布，不运行 ROS/真实机械臂，不自动合并任何 PR。

## 检查方法

1. 同步 36 个 Web 文件，Python 模块名改为 mtc_webui；把跨仓库文档链接固定到个人源码 SHA，修正包内启动和测试路径。各文件转换与前后 SHA-256 见 source-sync.json。
2. `python3 setup.py build --build-base <新目录>` 构建该包；仅以构建产物为 PYTHONPATH，执行 76 项 Python unittest 和模块 --help。33 个构建文件与候选源码逐字节一致。使用宿主 Python 3.10，不声称 colcon/Jazzy 重新验收。
3. 候选 30 项 Node 测试及全部 JS 语法检查；按四组原索引核验 UI 证据字节和入库文件。两个被 ignore 规则遗漏的兼容性日志加入暂存，未改日志内容。
4. 合并最新个人 main 的文档与来源新增项，解决五个文本/JSON 合并冲突。UI P0 用户记录迁移为 USER-HW-20261013-06；旧编号只在四组冻结 UI 目录中按映射解析，不改原文件。
5. 推送两个新分支并创建 PR，不 force-push、不合并。创建时 GitHub 回执保存于 *-pr-created.json；后续资料提交可以正常推进个人 PR head。

包内测试全部通过。此前 P0/P1/P2 的 17 项 ROS 接口检查不重复计作本轮新运行。提交前首次 git commit 因新克隆未配置身份退出，沿用本项目已有作者身份的仓库本地配置后成功；这不是产品测试失败。

使用 OpenAI Codex 协助审计、合并、包适配、测试、来源维护与发布；未引入新的第三方算法或运行依赖。完整来源记录见包内 provenance.json。
