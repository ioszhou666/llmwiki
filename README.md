# llm-wiki

`llm-wiki` 当前版本按 Karpathy 风格的 `LLM Wiki` 实现：主系统不是“本地文件搜索问答器”，而是一个由 `Claude Code` 持续维护的 Markdown wiki。

核心定位：

- `raw/` 是原始证据层
- `wiki/` 是持续演化的知识层
- `Claude Code` 是 wiki maintainer
- 本地 Python 代码负责 deterministic seed、结构化抽取、安全边界，以及可选的辅助工具层

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

目录职责：

- `raw/`
  - 原始资料，只作为证据输入
- `wiki/summaries/`
  - source-grounded summary page
- `wiki/concepts/`
  - 概念、流程、系统、主题页
- `wiki/entities/`
  - 团队、服务、环境、负责人、产品等实体页
- `wiki/syntheses/`
  - 跨页面综合页
- `wiki/overview/`
  - 导航、dashboard、knowledge map
- `cache/extracted/`
  - 本地 deterministic source packet
- `docs/`
  - 可选的辅助文档工具层输入目录，不属于主 wiki 知识流

## 主流程

主系统只强调这条链路：

1. `init-wiki`
   - 初始化 wiki 工作区、`AGENTS.md`、`CLAUDE.md`、`.claude/commands`
2. `ingest`
   - 从 `raw/` 生成 `cache/extracted/` 和 wiki seed page
3. `ingest-claude`
   - 调用 Claude Code 按 staged workflow 维护 wiki
4. `query-wiki`
   - 本地查询 `wiki/`
5. `query-wiki-claude`
   - 让 Claude 基于 `wiki/` 片段回答
6. `lint-wiki`
   - 检查 `raw/`、`wiki/`、`index.md`、`log.md` 的一致性

## 辅助工具层

之前的文件检索、批注统计、修复、透视图、受控执行等能力没有再作为产品主流程保留。

当前处理方式是：

- 主系统仍然是 Claude-native wiki
- 这些旧能力作为可选的 MCP auxiliary utility tools 保留
- 它们只服务于补充分析、结构化抽取、任务辅助，不再定义整个系统方向

当前辅助 MCP 工具包括：

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

将 MCP server 注册到 Claude Code：

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

当前版本已经明确完成两件事：

- 按 Karpathy 风格收敛到 `raw -> wiki -> Claude-maintained knowledge base`
- 将旧式文件问答/修复/执行逻辑降级为 MCP 辅助工具层，而不是主系统

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
