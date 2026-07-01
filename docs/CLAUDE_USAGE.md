# Claude Code 调用说明

本文档说明当前版本的 `llm-wiki` 如何在 `Claude Code` 中使用。

## 1. 当前定位

当前版本已经纠偏为 Karpathy 风格的 `LLM Wiki`：

- `raw/`
  - 原始资料
- `wiki/`
  - Claude 维护的知识库
- `CLAUDE.md`
  - wiki maintainer 的行为规则

所以 Claude Code 在本项目里的角色不再只是“问答后端”，而是：

- ingest 时维护 wiki 页面
- query 时基于 wiki 回答
- lint 时帮助保持 wiki 结构一致

## 2. 两种调用方式

有两种推荐方式：

1. 直接在 Claude Code 中打开项目目录并对话
2. 通过 `llm-wiki` CLI 或 MCP 先生成标准 prompt / 标准上下文，再让 Claude 执行

## 3. 最推荐的 Claude Code 手动使用流程

### 3.1 初始化项目

```powershell
llm-wiki --project-root D:\llmwiki\demo init-wiki
```

或者直接创建一套演示项目：

```powershell
llm-wiki --project-root D:\llmwiki\demo bootstrap-demo --target D:\llmwiki\demo
```

### 3.2 先做本地 seed ingest

```powershell
llm-wiki --project-root D:\llmwiki\demo ingest
```

这一步会生成：

- `cache/extracted/*.md`
- `wiki/sources/*.md`
- `wiki/index.md`
- `wiki/log.md`

本地结果不是最终 wiki，只是给 Claude 一个确定性起点。

### 3.3 在 Claude Code 中打开项目目录

打开 `D:\llmwiki\demo` 这个目录后，建议 Claude 先读取：

- `CLAUDE.md`
- `wiki/index.md`
- `wiki/log.md`
- `cache/extracted/`
- `raw/`

然后可以直接给 Claude 下这类任务：

```text
请按 CLAUDE.md 维护这个 llm-wiki：
1. 先阅读 CLAUDE.md、wiki/index.md、wiki/log.md
2. 阅读 raw/ 和 cache/extracted/ 中的资料
3. 更新 wiki/sources/*.md
4. 如果有必要，新建更高层的 topic/concept 页面
5. 更新 wiki/index.md
6. 在 wiki/log.md 追加本次整理记录
7. 不要修改 raw/
```

## 4. 用项目直接生成标准 Claude Prompt

为了避免每次手工组织提示词，项目已经提供了标准导出命令。

### 4.1 输出 Claude 调用手册

```powershell
llm-wiki --project-root D:\llmwiki\demo claude-playbook
```

它会输出当前项目推荐的 Claude Code 工作流说明。

### 4.2 输出标准 ingest prompt

```powershell
llm-wiki --project-root D:\llmwiki\demo print-ingest-prompt
```

如果只想让 Claude 处理某一个 source：

```powershell
llm-wiki --project-root D:\llmwiki\demo print-ingest-prompt --source product_v1_requirements.md
```

### 4.3 输出标准 query prompt

```powershell
llm-wiki --project-root D:\llmwiki\demo print-query-prompt --question "当前 wiki 对 CRM migration 的结论是什么"
```

这个命令会先从 `wiki/` 本地检索相关页面，再拼成 Claude 可直接使用的标准 prompt。

## 5. 直接由 CLI 调 Claude

如果你不想手工把 prompt 贴进 Claude Code，也可以直接用项目调用：

### 5.1 Claude ingest

```powershell
llm-wiki --project-root D:\llmwiki\demo ingest-claude
```

### 5.2 Claude query

```powershell
llm-wiki --project-root D:\llmwiki\demo query-wiki-claude --question "当前 wiki 对 CRM migration 的结论是什么"
```

这里的区别是：

- `ingest-claude`
  - Claude 负责真正维护 wiki 页面
- `query-wiki-claude`
  - Claude 基于 wiki 检索片段作答

## 6. 在 Claude Code 中作为 MCP 调用

### 6.1 注册 MCP

```powershell
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\llmwiki\demo
```

或者：

```powershell
claude mcp add llmwiki -- llm-wiki-mcp --project-root D:\llmwiki\demo
```

### 6.2 当前推荐使用的 MCP 资源

- `wiki://curation-status`
- `wiki://claude-playbook`
- `wiki://permission-policy`
- `wiki://security-summary`

### 6.3 当前推荐使用的 MCP 工具

- `ingest_wiki_local`
- `query_wiki_local`
- `lint_wiki`
- `get_ingest_prompt`
- `get_query_prompt`

这意味着在 Claude Code 里可以走一条更标准的 agent 路线：

1. 先读 `wiki://curation-status`
2. 再读 `wiki://claude-playbook`
3. 调 `ingest_wiki_local`
4. 调 `get_ingest_prompt`
5. 再按 prompt 维护 wiki

## 7. 当前最推荐的实际调用顺序

如果你是手工在 Claude Code 中操作，推荐按这个顺序：

1. `bootstrap-demo` 或 `init-wiki`
2. `ingest`
3. `claude-playbook`
4. `print-ingest-prompt`
5. 在 Claude Code 中执行 wiki 维护
6. `lint-wiki`
7. `print-query-prompt`
8. 在 Claude Code 中执行基于 wiki 的问答

## 8. 常见问题

### 8.1 Claude 为什么不直接读 raw，而还要先 ingest？

因为 `LLM Wiki` 的重点不是单次检索，而是把 raw source 编译成持久 wiki。

### 8.2 `ingest` 和 `ingest-claude` 有什么区别？

- `ingest`
  - 本地 deterministic seed
- `ingest-claude`
  - Claude 真正维护 wiki

### 8.3 MCP 和 CLI 哪个更推荐？

- 想快速验证：CLI 更直接
- 想和 Claude Code 深度集成：MCP 更标准

## 9. 当前结论

目前最稳妥的 Claude Code 调用方式已经不是旧的 `ask-claude` / `answer-claude`，而是：

- `ingest`
- `ingest-claude`
- `query-wiki`
- `query-wiki-claude`
- `claude-playbook`
- `print-ingest-prompt`
- `print-query-prompt`

这样更符合 `LLM Wiki` 的真实工作方式，也更接近 Claude Code 作为 wiki maintainer 的定位。
