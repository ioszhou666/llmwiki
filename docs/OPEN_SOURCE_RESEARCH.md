# llm-wiki 开源方案调研

## 1. 调研结论

本项目不能按“本地检索问答器”方向实现。更合理的路线是：

- 以 Karpathy 的 `LLM Wiki` 理念为主
- 参考 GitHub 上更接近 Claude-native wiki 的实现方式
- 再结合赛题中的 Office、TODO、批注修复、安全对抗要求做适配

因此主系统应当是：

- `raw/` 作为证据层
- `wiki/` 作为长期维护的知识层
- `Claude Code` 作为主要维护者
- 本地 Python 作为 deterministic 支撑层

## 2. Karpathy 定义带来的约束

Karpathy 风格强调的不是单次问答，而是：

1. 把资料编译成 page
2. 让模型优先维护 page
3. 让知识随着资料增长持续演化

所以真正需要长期存在的对象是：

- summary
- concept
- entity
- synthesis
- overview / map / graph

## 3. 开源实现的共同特征

结合公开实现，可以抽取出几条稳定共性：

1. 目录按 page 类型分层
2. 模型直接维护 repo 内 markdown
3. 有仓库级规则文件，例如 `AGENTS.md` / `CLAUDE.md`
4. 有面向 Claude Code 的命令入口
5. 原始资料与整理后的知识页严格分层

这也是当前仓库采用：

- `wiki/summaries/`
- `wiki/concepts/`
- `wiki/entities/`
- `wiki/syntheses/`
- `wiki/overview/`
- `wiki/graph/`

而不再使用旧式 `wiki/sources/` / `wiki/topics/` 的原因。

## 4. 本地代码应做什么

本地代码不应该决定最终知识表达，而应该负责：

- 文档抽取
- 批注 / TODO 抽取
- deterministic packet 生成
- 安全边界
- Claude workflow scaffolding

可保留的技术组件包括：

- OOXML 直接读取
- LibreOffice / Tika 兜底
- SQLite FTS5
- pandas / matplotlib
- Permission deny + prompt injection 防护

但这些都只是辅助层，不是产品本体。

## 5. 与题目的结合方式

赛题中的内容应被吸收到 wiki 主流程中：

- Office 文档
  - 作为 `raw/` 或辅助 `docs/` 输入源
- 批注 / TODO
  - 进入 extracted packet、summary page、或辅助 comment index
- 修复任务
  - 保留为 deterministic 辅助工具层
- 安全对抗样例
  - 进入统一安全边界设计

## 6. 当前落地结果

当前版本已经落地为：

- Claude-native wiki 主架构
- `AGENTS.md` + `CLAUDE.md`
- `.claude/commands`
- summary / concept / entity seed 体系
- staged Claude workflow
- MCP 接入
- auxiliary deterministic tool layer

## 7. 参考资料

- Karpathy LLM Wiki 说明
  - [gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- Unstructured supported file types
  - [docs](https://docs.unstructured.io/open-source/introduction/supported-file-types)
- Apache Tika supported formats
  - [docs](https://tika.apache.org/2.9.2/formats.html)
- LibreOffice start parameters
  - [docs](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html)
- python-docx comments analysis
  - [docs](https://python-docx.readthedocs.io/en/latest/dev/analysis/features/comments.html)
- openpyxl comments
  - [docs](https://openpyxl.readthedocs.io/en/stable/comments.html)
- SQLite FTS5
  - [docs](https://sqlite.org/fts5.html)
- pandas pivot_table
  - [docs](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot_table.html)
- OWASP LLM Prompt Injection Prevention Cheat Sheet
  - [docs](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
