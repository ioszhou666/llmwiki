# llm-wiki 系统设计

## 1. 当前系统定义

当前版本的系统定义是：

> 一个以 `Claude Code` 为主要维护者、以 `raw -> wiki` 为主循环、以 deterministic Python 工具为辅助层的 Claude-native LLM Wiki。

## 2. 主目录设计

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
├─ .claude/
│  └─ commands/
├─ AGENTS.md
├─ CLAUDE.md
└─ Permission.json
```

## 3. 分层架构

### 3.1 Claude-native 主层

- `AGENTS.md`
- `CLAUDE.md`
- `wiki_workspace.py`

### 3.2 Deterministic 辅助层

- `extractors.py`
- `security.py`
- `mcp_runtime.py`
- `mcp_server.py`
- `claude_client.py`

当前不再保留旧文件搜索、答题器、修复执行、图表生成、发布报告等无关模块。

## 4. 主流程

### 4.1 init

`init-wiki`

作用：

- 初始化 wiki workspace
- 写入 `AGENTS.md`
- 写入 `CLAUDE.md`
- 生成 `.claude/commands`

### 4.2 ingest

`ingest`

作用：

1. 扫描 `raw/`
2. 生成 `cache/extracted/*.md`
3. 生成 `wiki/summaries/*.md`
4. 自动生成 `wiki/concepts/*.md` seed
5. 自动生成 `wiki/entities/*.md` seed
6. 更新 `wiki/overview/*.md`
7. 更新 `wiki/index.md`
8. 追加 `wiki/log.md`

### 4.3 ingest-claude

`ingest-claude`

当前使用三阶段 workflow：

1. `source-curation`
2. `concept-and-entity-synthesis`
3. `index-and-log-finalize`

### 4.4 query

- `query-wiki`
  - 本地对 `wiki/` 检索
- `query-wiki-claude`
  - 基于 wiki 片段调用 Claude

### 4.5 lint

`lint-wiki`

当前检查：

- summary 是否齐全
- extracted packet 是否齐全
- index 是否包含 summary link

## 5. Claude Code 集成方式

当前支持三种：

1. 手工在 Claude Code 中执行 staged workflow
2. 通过 `ingest-claude` 由 CLI 顺序调用 Claude
3. 通过 MCP 挂接到 Claude Code

## 6. 当前边界

1. `wiki/concepts` 与 `wiki/entities` 的 seed 仍是启发式生成
2. `wiki/syntheses/` 与 `wiki/graph/` 还只是预留结构
3. 当前系统已经删除与 wiki 主线无关的旧搜索/答题器代码
