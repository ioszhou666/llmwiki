# llm-wiki 系统设计

## 1. 系统定义

当前系统是：

> 一个以 `Claude Code` 为主要维护者、以 `raw -> wiki` 为主循环、并带有无状态 deterministic 工具层的 Claude-native LLM Wiki。

## 2. 分层设计

### 2.1 主系统层

- `wiki_workspace.py`
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/commands/*`
- `wiki/`

### 2.2 Claude 维护层

Claude Code 负责：

- 维护 summaries
- 提升 concepts
- 完善 entities
- 写 syntheses
- 刷新 index / overview / log

### 2.3 辅助工具层

- `extractors.py`
- `security.py`
- `indexer.py`
- `answerer.py`
- `audit.py`
- `mcp_runtime.py`
- `mcp_server.py`
- `claude_client.py`

这一层负责：

- 文档解析
- TODO / comment 抽取
- 按需扫描 `docs/`
- 辅助统计与检索
- 受控修复与执行
- 安全与注入防护

## 3. 主流程

### 3.1 初始化

`init-wiki`

### 3.2 本地 ingest

`ingest`

### 3.3 Claude staged workflow

- `source-curation`
- `concept-and-entity-synthesis`
- `index-and-log-finalize`

### 3.4 查询

- `query-wiki`
- `query-wiki-claude`

### 3.5 校验

- `lint-wiki`

## 4. 辅助 MCP 工具层

当前辅助工具不再是持久索引系统。

当前设计：

- 无 SQLite
- 无持久索引仓
- 无长期 docs 索引仓
- 调用时扫描 `docs/`
- 在内存里构建临时文档视图

当前可用工具：

- `doctor`
- `scan_documents`
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

## 5. 安全边界

`Permission.json` + `security.py` 负责统一防护：

- deny 目录
- deny 文件
- deny 命令
- prompt injection
- 间接执行诱导
- 危险副作用
- 敏感口令读取限制

## 6. 当前边界结论

当前仓库已经满足：

1. 主系统是 Karpathy 风格 wiki
2. Claude 是核心维护者
3. deterministic Python 是支撑层
4. 旧能力只以无状态 MCP 工具层保留
