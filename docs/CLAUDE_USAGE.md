# Claude Code 调用说明

## 1. 当前定位

当前版本里，`Claude Code` 的角色不是“调用项目后端问答”，而是直接作为这个 wiki 的 maintainer。

也就是说，最重要的不是：

- `ask-claude`
- `answer-claude`

而是：

- `ingest`
- `ingest-claude`
- `print-ingest-workflow`
- `query-wiki`
- `query-wiki-claude`

## 2. Claude 维护的对象

当前 Claude 主要维护以下目录：

- `wiki/summaries/`
- `wiki/concepts/`
- `wiki/entities/`
- `wiki/syntheses/`
- `wiki/overview/`
- `wiki/index.md`
- `wiki/log.md`

它不应修改：

- `raw/`

## 3. 当前推荐流程

### 3.1 初始化项目

```powershell
llm-wiki --project-root D:\llmwiki\demo init-wiki
```

或者：

```powershell
llm-wiki --project-root D:\llmwiki\demo bootstrap-demo --target D:\llmwiki\demo
```

### 3.2 先生成 deterministic seed

```powershell
llm-wiki --project-root D:\llmwiki\demo ingest
```

这一步会生成：

- `cache/extracted/*.md`
- `wiki/summaries/*.md`
- `wiki/concepts/*.md`
- `wiki/entities/*.md`
- `wiki/overview/*.md`
- `wiki/index.md`
- `wiki/log.md`

这些内容不是最终成品，而是 Claude 的 curation 起点。

### 3.3 在 Claude Code 中打开项目

建议 Claude 先读取：

- `AGENTS.md`
- `CLAUDE.md`
- `wiki/index.md`
- `wiki/log.md`
- `cache/extracted/`
- `raw/`

## 4. 当前 staged ingest workflow

### 4.1 输出 workflow

```powershell
llm-wiki --project-root D:\llmwiki\demo print-ingest-workflow
```

当前会输出三个阶段：

1. `source-curation`
2. `concept-and-entity-synthesis`
3. `index-and-log-finalize`

### 4.2 各阶段职责

`source-curation`

- 只维护 `wiki/summaries/*.md`
- 使 summary 更准确、更紧贴 source evidence

`concept-and-entity-synthesis`

- 从现有 `wiki/concepts/` 和 `wiki/entities/` seed 起步
- 合并重复页
- 提炼跨 source 概念、系统、工具、团队、决策、流程

`index-and-log-finalize`

- 更新 `wiki/index.md`
- 更新 `wiki/overview/*.md`
- 追加 `wiki/log.md`

## 5. 最推荐的 Claude 使用方式

### 5.1 手工在 Claude Code 中执行

顺序如下：

1. `ingest`
2. `print-ingest-workflow`
3. 在 Claude Code 中按三个阶段顺序执行
4. `lint-wiki`
5. `query-wiki` 或 `query-wiki-claude`

### 5.2 直接由 CLI 调 Claude

```powershell
llm-wiki --project-root D:\llmwiki\demo ingest-claude
```

当前 `ingest-claude` 的行为是：

- 先执行本地 `ingest`
- 再顺序执行三阶段 workflow

不是旧版那种单 prompt 方式。

## 6. 通过 MCP 接入 Claude Code

### 6.1 注册

```powershell
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\llmwiki\demo
```

### 6.2 建议先读的资源

- `wiki://curation-status`
- `wiki://claude-playbook`
- `wiki://permission-policy`
- `wiki://security-summary`

### 6.3 建议先调用的工具

- `ingest_wiki_local`
- `get_ingest_workflow`
- `lint_wiki`
- `query_wiki_local`
- `get_query_prompt`

## 7. `.claude/commands` 的位置

当前项目已经生成：

- `.claude/commands/ingest-wiki.md`
- `.claude/commands/query-wiki.md`
- `.claude/commands/lint-wiki.md`

这意味着项目不是把 Claude 当外部聊天模型，而是按 Claude Code 原生仓库工作方式组织入口。

## 8. 与旧命令的关系

以下命令仍然存在：

- `ask-claude`
- `answer-claude`
- `answer-all-claude`

但它们只属于兼容层，不代表当前主方向。

当前主方向是：

- 先维护 wiki
- 再基于 wiki 回答

而不是“直接拿模型答题”。

## 9. 当前结论

如果按当前版本正确使用 Claude Code，应理解为：

> Claude Code 是这个项目里的 wiki maintainer，而不是简单的问答后端。
