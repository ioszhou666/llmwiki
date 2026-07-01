# llm-wiki 开源方案调研

## 1. 调研目标

本项目最初面向赛题时，需要同时解决四类问题：

1. 多格式办公文档与代码文档抽取
2. 文档内批注、TODO 和结构化线索提取
3. 问答、修复、图表和受控执行
4. Prompt Injection、越权读取和危险副作用防护

在当前版本中，调研目标又增加了一层：

5. 系统整体必须收敛到 Karpathy 风格的 `LLM Wiki`

因此，开源方案的选择不再只是“找一套本地问答技术栈”，而是要回答：

- 哪些组件适合做 deterministic 工具层
- 哪些能力应该交给 `Claude Code` 作为 wiki maintainer

## 2. Karpathy 对 LLM Wiki 的定义

Karpathy 提出的 `LLM Wiki` 核心不是一次性检索问答，而是：

- 维护一套持续演化的知识页
- 把原始资料编译成可读、可增量整理、可引用的 markdown wiki
- 让模型更多地扮演 maintainer，而不是一次性回答器

对本项目的直接影响是：

- `raw/` 应是原始资料层
- `wiki/` 应是最终知识层
- `Claude Code` 应该主要负责 curation
- 本地解析/索引/安全能力应作为辅助工具层，而不是主产品本体

## 3. 开源组件选型结论

### 3.1 文档抽取

当前采用：

- `docx/pptx/xlsx`
  - 优先直接解析 OOXML
- `doc/ppt/xls`
  - 优先 `LibreOffice` 转换，`Apache Tika` 兜底
- `xml/java/py/html/md/js`
  - 纯文本读取 + 规则提取

选择原因：

- 赛题不仅要求读正文，还要读批注和 TODO
- OOXML 直读在 comments、结构定位和稳定性方面更合适
- 旧 Office 格式可以接受转换链路兜底

### 3.2 本地索引

当前采用：

- SQLite FTS5

不默认采用：

- Elasticsearch
- OpenSearch
- 向量数据库

原因：

- 当前规模更适合单机、轻依赖、可复现方案
- deterministic 检索更适合作为 Claude ingest/query 的辅助层

### 3.3 图表能力

当前采用：

- `pandas`
- `matplotlib`

原因：

- 能稳定生成本地可交付 PNG
- 与现有 Python 链路兼容

### 3.4 安全加固

当前采用：

- `Permission.json` deny 规则
- 规则化 prompt injection 拦截
- 危险副作用拦截
- 结果层 deny 过滤
- Python AST 受控执行检查

原因：

- 赛题中存在明确的对抗样例
- LLM Wiki 场景同样存在恶意 source 污染风险

## 4. 为什么没有直接采用现成的“RAG 系统”

很多开源方案更适合：

- 文档切片
- embedding 检索
- LLM 最终回答

但它们通常不天然解决以下问题：

- Office comments/TODO 的细粒度抽取
- 基于批注的 deterministic 修复
- 受控本地执行
- deny 路径和命令的结果级安全边界
- `wiki/` 持续维护而不是一次性回答

所以本项目最终选择的是：

- 用开源组件搭底层能力
- 用本地 deterministic 流程生成 seed
- 用 `Claude Code` 驱动 wiki curation

## 5. 当前项目中的落地方式

当前架构已经把调研结论落实为两层：

### 5.1 Wiki 主层

- `raw/`
- `wiki/sources/`
- `wiki/topics/`
- `cache/extracted/`
- `CLAUDE.md`
- `ingest / ingest-claude / query-wiki / lint-wiki`

### 5.2 工具兼容层

- `docs/question/output`
- SQLite/FTS5
- Office/代码抽取
- TODO 解析
- 文档修复
- 图表生成
- 受控 Python 执行

## 6. 当前版本新增的调研落地点

相较于早期版本，当前版本已经进一步补上：

- `wiki/topics/` 自动 topic seed page
- `topic-synthesis` 阶段的 merge rules
- `ingest-claude` 三阶段 workflow
- `wiki://curation-status` 和 `wiki://claude-playbook` 等更贴近 wiki curation 的 MCP 资源

这使项目更贴近真正的 `LLM Wiki`，而不是“披着 wiki 名字的本地检索工具”。

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
