# llm-wiki 系统设计

## 1. 系统定义

当前系统定义是：

> 一个以 `Claude Code` 为主要维护者、以 `raw -> wiki` 为主循环、并带有可选 deterministic 工具层的 Claude-native LLM Wiki。

## 2. 分层设计

### 2.1 主系统层

主系统只围绕 wiki：

- `wiki_workspace.py`
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/commands/*`
- `wiki/` 目录本身

职责：

- 初始化 wiki 目录
- 从 `raw/` 生成 seed pages
- 输出 Claude ingest/query workflow
- 执行本地 wiki 查询
- 检查 wiki 完整性

### 2.2 Claude 维护层

Claude Code 负责：

- 整理 `wiki/summaries/`
- 合并并提升 `wiki/concepts/`
- 完善 `wiki/entities/`
- 写入 `wiki/syntheses/`
- 刷新 `wiki/index.md`
- 刷新 `wiki/overview/*.md`
- 追加 `wiki/log.md`

### 2.3 Deterministic 辅助层

辅助层不再定义产品主线，只作为支撑：

- `extractors.py`
- `security.py`
- `indexer.py`
- `answerer.py`
- `audit.py`
- `mcp_runtime.py`
- `mcp_server.py`
- `claude_client.py`

这层职责包括：

- 文档解析
- TODO / comment 抽取
- 文档索引
- 辅助统计与检索
- 受控修复与执行
- 权限与注入防护

## 3. 主流程

### 3.1 初始化

`init-wiki`

作用：

- 初始化 `raw/`、`wiki/`、`cache/extracted/`
- 写入 `AGENTS.md`
- 写入 `CLAUDE.md`
- 写入 `.claude/commands`

### 3.2 本地 ingest

`ingest`

作用：

1. 扫描 `raw/`
2. 生成 `cache/extracted/*.md`
3. 生成 `wiki/summaries/*.md`
4. 生成 `wiki/concepts/*.md` seed
5. 生成 `wiki/entities/*.md` seed
6. 刷新 `wiki/overview/*.md`
7. 刷新 `wiki/index.md`
8. 追加 `wiki/log.md`

### 3.3 Claude staged workflow

`ingest-claude` / `get_ingest_workflow`

当前工作流：

1. `source-curation`
2. `concept-and-entity-synthesis`
3. `index-and-log-finalize`

### 3.4 查询

- `query-wiki`
  - 本地搜索 `wiki/**/*.md`
- `query-wiki-claude`
  - 先构造 wiki 上下文，再由 Claude 回答

### 3.5 校验

`lint-wiki`

检查：

- extracted packet 是否齐全
- summary page 是否齐全
- `index.md` 是否覆盖 summary 链接
- `log.md` 是否存在

## 4. 辅助 MCP 工具层

辅助工具层保留，但其定位已经改变：

- 不再是产品主流程
- 不再通过 CLI 作为主入口推广
- 只作为 MCP 下的 utility tools 存在

当前可用工具包括：

- `doctor`
- `index_documents`
- `list_document_paths`
- `count_files_by_extension`
- `count_supported_extensions`
- `search_related_paths`
- `find_paths_by_basename`
- `get_document_record`
- `list_comments`
- `answer_question_local`
- `apply_fixes`
- `build_pivot_chart`
- `run_python_document`

这些工具主要面向：

- 文档辅助分析
- Office / TODO 辅助处理
- 竞赛题风格的局部自动化
- 受控的可审计操作

## 5. 安全边界

`Permission.json` + `security.py` 负责统一防护：

- deny 目录
- deny 文件
- deny 命令
- prompt injection 检测
- 间接执行诱导检测
- 危险副作用检测
- 敏感口令读取限制

## 6. 当前边界结论

当前仓库已经从“本地文件问答系统”修正为：

1. 主系统是 Karpathy 风格的 wiki
2. Claude 是核心维护者
3. deterministic Python 是支撑层
4. 旧能力只以 MCP 辅助工具层保留
