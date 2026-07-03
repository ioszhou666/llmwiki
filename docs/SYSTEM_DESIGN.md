# llm-wiki 系统设计

## 1. 当前系统定义

当前版本的系统定义是：

> 一个以 `Claude Code` 为主要维护者、以 `raw -> wiki` 为主循环、以 deterministic Python 工具为辅助层的 Claude-native LLM Wiki。

这和早期“本地文档检索 + 规则问答”有本质区别。

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

语义：

- `raw/`
  - 原始证据层
- `wiki/summaries/`
  - source-grounded summary
- `wiki/concepts/`
  - 概念、流程、系统、项目、决策
- `wiki/entities/`
  - 团队、产品、服务、工具、环境、负责人等命名实体
- `wiki/syntheses/`
  - 大范围聚合页
- `wiki/overview/`
  - 导航、dashboard、knowledge map
- `cache/extracted/`
  - deterministic ingest packet
- `.claude/commands/`
  - Claude Code 命令入口

## 3. 分层架构

### 3.1 Claude-native 主层

- `AGENTS.md`
  - 定义仓库级维护模型
- `CLAUDE.md`
  - 定义 curation 规则
- `wiki_workspace.py`
  - 管理 wiki workspace、seed ingest、workflow prompt、query、lint

### 3.2 Deterministic 辅助层

- `extractors.py`
  - 文档内容、批注、TODO 提取
- `security.py`
  - 安全边界
- `mcp_runtime.py`
  - 将能力整理成工具运行时
- `mcp_server.py`
  - 暴露 MCP server

### 3.3 兼容层

- `indexer.py`
- `answerer.py`
- `question_parser.py`
- `docs/question/output` 相关逻辑

这些代码仍保留，但不再是主产品定义中心。

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

分两种：

- `query-wiki`
  - 本地对 `wiki/` 检索
- `query-wiki-claude`
  - 基于检索到的 wiki 片段调用 Claude

### 4.5 lint

`lint-wiki`

当前主要检查：

- summary 是否齐全
- extracted packet 是否齐全
- index 是否包含 summary link

## 5. Claude Code 集成方式

当前支持三种：

1. 手工在 Claude Code 中执行 staged workflow
2. 通过 `ingest-claude` 由 CLI 顺序调用 Claude
3. 通过 MCP 挂接到 Claude Code

## 6. 为什么这是更接近 Karpathy 的实现

关键不是“有没有 raw/wiki 两层”，而是：

1. 主工作对象是不是 wiki page
2. 模型是不是 maintainer
3. 知识是不是持续沉淀在 page 中

当前版本已经满足这三个条件。

## 7. 当前边界

1. `wiki/concepts` 与 `wiki/entities` 的 seed 仍是启发式生成
2. `wiki/syntheses` 与 `wiki/graph` 还只是留出结构，尚未深做
3. 兼容层代码还存在较多旧逻辑，需要后续继续收口
