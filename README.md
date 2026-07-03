# llm-wiki

`llm-wiki` 当前版本按 Karpathy 风格的 `LLM Wiki` 实现。主系统不是旧式本地检索问答器，而是由 `Claude Code` 持续维护的 Markdown wiki。

核心定位：

- `raw/` 是原始证据层
- `wiki/` 是持续演化的知识层
- `Claude Code` 是 wiki maintainer
- 本地 Python 代码负责 deterministic seed、结构化抽取、安全边界，以及可调用的无状态辅助工具

## 当前架构

```text
project/
├─ raw/
├─ wiki/
│  ├─ index.md
│  ├─ log.md
│  ├─ overview/
│  ├─ summaries/
│  ├─ concepts/
│  ├─ entities/
│  ├─ syntheses/
│  └─ graph/
├─ cache/
│  └─ extracted/
├─ docs/
├─ .claude/
│  └─ commands/
├─ AGENTS.md
├─ CLAUDE.md
└─ Permission.json
```

## 主流程

主系统只围绕这条链路：

1. `init-wiki`
2. `ingest`
3. `ingest-claude`
4. `query-wiki`
5. `query-wiki-claude`
6. `lint-wiki`

## 辅助工具层

旧的文件检索、批注统计、修复、图表、受控执行等能力不再以持久索引仓的形式存在。

当前保留方式是：

- 不落 SQLite
- 不建持久索引仓
- 不作为主产品流程
- 只作为 wiki 可调用的无状态 MCP tools

这些工具在调用时对 `docs/` 做按需扫描，并在内存里临时组织数据视图。

当前辅助工具包括：

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

## 安装与命令

```powershell
python -m pip install -e .
```

示例：

```powershell
llm-wiki --project-root D:\llmwiki\demo init-wiki
llm-wiki --project-root D:\llmwiki\demo ingest
llm-wiki --project-root D:\llmwiki\demo ingest-claude
llm-wiki --project-root D:\llmwiki\demo query-wiki --question "CRM migration"
llm-wiki --project-root D:\llmwiki\demo query-wiki-claude --question "当前 wiki 对 CRM migration 的结论是什么"
llm-wiki --project-root D:\llmwiki\demo lint-wiki
llm-wiki --project-root D:\llmwiki\demo print-ingest-workflow
llm-wiki --project-root D:\llmwiki\demo claude-playbook
llm-wiki --project-root D:\llmwiki\demo claude-status
llm-wiki-mcp --project-root D:\llmwiki\demo
```

## 在 Claude Code 中接入

```powershell
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\llmwiki\demo
```

建议优先使用的 wiki 资源与工具：

- 资源
  - `wiki://status`
  - `wiki://curation-status`
  - `wiki://claude-playbook`
  - `wiki://permission-policy`
  - `wiki://security-summary`
- 工具
  - `ingest_wiki_local`
  - `get_ingest_workflow`
  - `lint_wiki`
  - `query_wiki_local`
  - `get_query_prompt`

## 当前状态

当前版本已经明确满足两点：

- 主系统收敛到 `raw -> wiki -> Claude-maintained knowledge base`
- 辅助文档能力改为无状态 tool layer，不再使用 SQLite / FTS 持久模式

测试状态：

```text
14 passed
```

## 相关文档

- [docs/OPEN_SOURCE_RESEARCH.md](docs/OPEN_SOURCE_RESEARCH.md)
- [docs/CLAUDE_USAGE.md](docs/CLAUDE_USAGE.md)
- [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md)
- [docs/LOGIC_DETAILS.md](docs/LOGIC_DETAILS.md)
- [docs/SECURITY_HARDENING.md](docs/SECURITY_HARDENING.md)
- [docs/KARPATHY_ALIGNMENT.md](docs/KARPATHY_ALIGNMENT.md)
