# Claude Code 调用说明

## 1. 当前角色定义

在当前版本里，`Claude Code` 不是“文件搜索问答后端”，而是这个仓库里的 wiki maintainer。

它主要维护：

- `wiki/summaries/`
- `wiki/concepts/`
- `wiki/entities/`
- `wiki/syntheses/`
- `wiki/overview/`
- `wiki/index.md`
- `wiki/log.md`

它不应修改：

- `raw/`

## 2. 推荐调用方式

### 2.1 本地先生成 deterministic seed

```powershell
llm-wiki --project-root D:\llmwiki\demo ingest
```

该命令会生成：

- `cache/extracted/*.md`
- `wiki/summaries/*.md`
- `wiki/concepts/*.md`
- `wiki/entities/*.md`
- `wiki/overview/*.md`
- `wiki/index.md`
- `wiki/log.md`

### 2.2 查看 staged workflow

```powershell
llm-wiki --project-root D:\llmwiki\demo print-ingest-workflow
```

当前 workflow 分三段：

1. `source-curation`
2. `concept-and-entity-synthesis`
3. `index-and-log-finalize`

### 2.3 在 Claude Code 中执行维护

建议 Claude Code 先读取：

- `AGENTS.md`
- `CLAUDE.md`
- `wiki/index.md`
- `wiki/log.md`
- `cache/extracted/`
- `raw/`

然后按三段 workflow 依次执行：

1. 维护 `wiki/summaries/*.md`
2. 维护 `wiki/concepts/*.md` 和 `wiki/entities/*.md`
3. 刷新 `wiki/index.md`、`wiki/overview/*.md`、`wiki/log.md`

## 3. 直接由 CLI 调 Claude

```powershell
llm-wiki --project-root D:\llmwiki\demo ingest-claude
```

行为：

1. 先执行本地 `ingest`
2. 再按 staged workflow 顺序调用 Claude Code

## 4. 查询方式

### 4.1 本地查询 wiki

```powershell
llm-wiki --project-root D:\llmwiki\demo query-wiki --question "CRM migration"
```

### 4.2 让 Claude 基于 wiki 回答

```powershell
llm-wiki --project-root D:\llmwiki\demo query-wiki-claude --question "当前 wiki 对 CRM migration 的结论是什么"
```

## 5. 通过 MCP 接入 Claude Code

注册方式：

```powershell
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\llmwiki\demo
```

建议 Claude 优先读取这些资源：

- `wiki://status`
- `wiki://curation-status`
- `wiki://claude-playbook`
- `wiki://permission-policy`
- `wiki://security-summary`

建议 Claude 优先调用这些 wiki 主工具：

- `ingest_wiki_local`
- `get_ingest_workflow`
- `lint_wiki`
- `query_wiki_local`
- `get_query_prompt`

## 6. 辅助工具层如何使用

当前还保留了一组 auxiliary utility tools，供 Claude 在需要时调用，但它们不是主系统：

- `index_documents`
- `list_document_paths`
- `count_files_by_extension`
- `search_related_paths`
- `get_document_record`
- `list_comments`
- `answer_question_local`
- `apply_fixes`
- `build_pivot_chart`
- `run_python_document`

正确理解是：

- `wiki` 主流程负责长期知识维护
- `docs` 工具层负责可选的结构化辅助操作

## 7. 当前结论

当前版本中，Claude Code 的正确嵌入方式是：

> 作为这个仓库里 `wiki/` 的维护者和整理者，而不是一个单次文件问答接口。
