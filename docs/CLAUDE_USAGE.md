# Claude Code 调用说明

## 1. 当前角色定义

`Claude Code` 在当前版本中是 wiki maintainer，不是旧式检索问答后端。

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

### 2.2 查看 staged workflow

```powershell
llm-wiki --project-root D:\llmwiki\demo print-ingest-workflow
```

当前 workflow 分三段：

1. `source-curation`
2. `concept-and-entity-synthesis`
3. `index-and-log-finalize`

### 2.3 在 Claude Code 中执行维护

建议先读取：

- `AGENTS.md`
- `CLAUDE.md`
- `wiki/index.md`
- `wiki/log.md`
- `cache/extracted/`
- `raw/`

## 3. 直接由 CLI 调 Claude

```powershell
llm-wiki --project-root D:\llmwiki\demo ingest-claude
```

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

```powershell
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\llmwiki\demo
```

建议优先读取资源：

- `wiki://status`
- `wiki://curation-status`
- `wiki://claude-playbook`
- `wiki://permission-policy`
- `wiki://security-summary`

建议优先调用 wiki 主工具：

- `ingest_wiki_local`
- `get_ingest_workflow`
- `lint_wiki`
- `query_wiki_local`
- `get_query_prompt`

## 6. 辅助工具层如何使用

当前还保留一组 auxiliary utility tools，但它们不再依赖持久索引仓。

当前方式是：

- 调用时扫描 `docs/`
- 在内存中临时组织文档视图
- 完成后直接返回结果

可用工具：

- `scan_documents`
- `list_document_paths`
- `count_files_by_extension`
- `search_related_paths`
- `get_document_record`
- `list_comments`
- `answer_question_local`
- `apply_fixes`
- `build_pivot_chart`
- `run_python_document`

## 7. 当前结论

Claude Code 的正确嵌入方式仍然是：

> 作为这个仓库里 `wiki/` 的维护者和整理者，并在需要时调用无状态辅助 tools。
