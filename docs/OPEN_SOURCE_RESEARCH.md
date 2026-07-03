# llm-wiki 开源方案调研

## 1. 调研结论

本项目不能按“本地检索问答器”方向实现。正确方向应当是：

- 以 Karpathy 的 `LLM Wiki` 理念为主
- 参考 GitHub 上更接近 Claude-native wiki 的实现方式
- 再把赛题里的 Office、TODO、批注修复和安全要求吸收进来

因此，系统主线应是：

- `raw/` 作为证据层
- `wiki/` 作为长期维护的知识层
- `Claude Code` 作为主要维护者
- 本地 Python 作为 deterministic 辅助层

## 2. Karpathy 定义带来的约束

Karpathy 风格强调的不是“一次性检索回答”，而是：

1. 把资料整理成 page
2. 让模型持续维护这些 page
3. 让知识随着资料增长不断演化

所以真正重要的不是单次 RAG，而是：

- summary page
- concept page
- entity page
- synthesis page
- overview / map / graph

## 3. 参考 GitHub 实现的共同特征

结合对公开实现方案的调研，比较稳定的共同点是：

1. 目录以 page 类型分层
2. 模型直接维护 repo 内 markdown
3. 有仓库级规则文件，例如 `AGENTS.md` / `CLAUDE.md`
4. 有面向 Claude Code 的命令入口
5. 原始资料和整理后的 page 明确分层

所以当前版本已经把主结构调整为：

- `wiki/summaries/`
- `wiki/concepts/`
- `wiki/entities/`
- `wiki/syntheses/`
- `wiki/overview/`
- `wiki/graph/`

而不是旧的：

- `wiki/sources/`
- `wiki/topics/`

## 4. 本项目中的本地代码应做什么

本地代码不应主导最终知识表达，而应负责：

- 文档抽取
- 批注与 TODO 提取
- deterministic packet 生成
- 安全边界
- Claude workflow scaffolding

因此，当前保留的技术选型仍然成立：

- OOXML 直读
- LibreOffice / Tika 兜底
- SQLite FTS5
- pandas / matplotlib
- Permission deny + 规则防护

但这些都是辅助层，不是产品定义本身。

## 5. 与赛题的结合方式

赛题里的内容应被吸收到 wiki 主流程中：

- Office 文档
  - 作为 `raw/` 证据来源
- 批注 / TODO
  - 进入 extracted packet 和 summary page
- 修复任务
  - 仍保留 deterministic 工具链，但不再定义系统主线
- 安全对抗样例
  - 进入安全边界设计

## 6. 当前版本的落地结果

当前版本已经落地：

- Claude-native wiki 目录
- `AGENTS.md` + `CLAUDE.md`
- `.claude/commands`
- `summary / concept / entity` seed 生成
- staged workflow
- MCP 接入

## 7. 参考资料

- Karpathy LLM Wiki 说明
  - https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Unstructured supported file types
  - https://docs.unstructured.io/open-source/introduction/supported-file-types
- Apache Tika supported formats
  - https://tika.apache.org/2.9.2/formats.html
- LibreOffice start parameters
  - https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html
- python-docx comments analysis
  - https://python-docx.readthedocs.io/en/latest/dev/analysis/features/comments.html
- openpyxl comments
  - https://openpyxl.readthedocs.io/en/stable/comments.html
- SQLite FTS5
  - https://sqlite.org/fts5.html
- pandas pivot_table
  - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot_table.html
- OWASP LLM Prompt Injection Prevention Cheat Sheet
  - https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
