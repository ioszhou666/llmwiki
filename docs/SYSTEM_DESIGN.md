# llm-wiki 系统设计

## 1. 当前定位

`llm-wiki` 当前版本已经按 Karpathy 风格的 `LLM Wiki` 重新收敛，核心目标不是“本地规则问答器”，而是一个由 `Claude Code` 持续维护的知识工作区。

系统的主循环是：

1. `raw/` 接收不可变原始资料
2. 本地 deterministic 逻辑生成 `cache/extracted/`、`wiki/sources/` 和 `wiki/topics/` seed
3. `Claude Code` 按 staged workflow 维护 `wiki/`
4. 查询优先从 `wiki/` 获取答案
5. `lint-wiki` 持续检查结构一致性

旧的 `docs/question/output`、本地索引、TODO 修复、受控执行与图表能力仍然保留，但现在属于兼容层和辅助工具层，不再是主产品叙事中心。

## 2. 核心目录结构

当前项目同时支持两套目录语义：

### 2.1 Wiki 主目录

```text
project/
├─ raw/
├─ wiki/
│  ├─ index.md
│  ├─ log.md
│  ├─ sources/
│  └─ topics/
├─ cache/
│  └─ extracted/
├─ output/
├─ CLAUDE.md
└─ Permission.json
```

- `raw/`
  - 原始资料，只读，不允许 Claude 改写
- `wiki/sources/`
  - source 级别的事实页
- `wiki/topics/`
  - 跨 source 的主题页、概念页、流程页、决策页
- `wiki/index.md`
  - 当前 wiki 的导航入口
- `wiki/log.md`
  - ingest/query/lint 相关事实日志
- `cache/extracted/`
  - 本地 deterministic packet，作为 Claude 的 ingest 辅助上下文
- `CLAUDE.md`
  - 维护规则和编辑边界

### 2.2 兼容层目录

```text
project/
├─ docs/
├─ question/
└─ output/
```

- `docs/`
  - 赛题原始办公文档、代码文档和系统样例
- `question/`
  - 结构化题目组
- `output/`
  - 答题结果、修复产物、审计日志、SQLite 索引

## 3. 分层架构

### 3.1 Wiki 主控层

- `src/llm_wiki/wiki_workspace.py`
  - 管理 `raw/wiki/cache/CLAUDE.md/index.md/log.md`
  - 负责 deterministic seed ingest、topic seed 生成、本地 wiki 查询、lint、Claude prompt/workflow 构造
- `CLAUDE.md`
  - 定义 Claude 作为 wiki maintainer 的操作边界
- `claude_client.py`
  - 对接本地 `Claude Code CLI`

### 3.2 文档与索引工具层

- `extractors.py`
  - 多格式文档抽取、批注和 TODO 解析
- `indexer.py`
  - `docs/` 的 SQLite + FTS5 索引
- `question_parser.py`
  - 将赛题式问题映射为固定动作类型
- `answerer.py`
  - 本地问答、批量答题、修复、图表、受控执行

### 3.3 接入层

- `cli.py`
  - 对外暴露 `init-wiki / ingest / ingest-claude / query-wiki / lint-wiki` 等主命令
- `mcp_runtime.py`
  - 将 wiki 流程和兼容工具层整理成可调用运行时
- `mcp_server.py`
  - 通过 `FastMCP` 以 stdio 暴露资源和工具

### 3.4 安全层

- `security.py`
  - 统一做 prompt injection、危险副作用、敏感信息读取与路径权限检查
- `Permission.json`
  - 目录、命令、文件 deny 策略

## 4. 主流程设计

### 4.1 初始化流程

入口：

```powershell
llm-wiki --project-root <root> init-wiki
```

结果：

- 创建 `raw/`
- 创建 `wiki/index.md`、`wiki/log.md`
- 创建 `wiki/sources/`、`wiki/topics/`
- 创建 `cache/extracted/`
- 创建 `CLAUDE.md`
- 创建默认 `Permission.json`

### 4.2 Deterministic Seed Ingest

入口：

```powershell
llm-wiki --project-root <root> ingest
```

流程：

1. 遍历 `raw/`
2. 抽取文档文本、批注、TODO 和关键片段
3. 生成 `cache/extracted/*.md`
4. 生成 `wiki/sources/*.md`
5. 自动聚合 topic phrase，生成 `wiki/topics/*.md` seed page
6. 刷新 `wiki/index.md`
7. 追加 `wiki/log.md`

设计目的：

- 先给 Claude 一个稳定、可复现、可审计的起点
- 降低 Claude 直接从杂乱原始资料开始整理的成本
- 自动暴露 topic 合并候选，减少重复页面

### 4.3 Claude Staged Ingest

入口：

```powershell
llm-wiki --project-root <root> ingest-claude
```

当前 `ingest-claude` 不再走单个大 prompt，而是顺序执行三个阶段：

1. `source-curation`
2. `topic-synthesis`
3. `index-and-log-finalize`

其中第二阶段内置了 topic merge rules：

- 优先强化已有 `wiki/topics/` seed
- 遇到重名、近义、同一系统或同一流程的 topic 时合并
- source-specific summary 和 cross-source synthesis 不混写

### 4.4 Wiki 查询流程

有两种主要方式：

1. `query-wiki`
   - 直接在 `wiki/` 中做本地检索并返回片段
2. `query-wiki-claude`
   - 先从 `wiki/` 取回上下文，再交给 Claude 生成自然语言答案

设计原则：

- 查询优先面向 `wiki/`，而不是绕过整理层直接读 `raw/`
- wiki 不足时要明确说缺什么，不鼓励编造

### 4.5 Lint 流程

入口：

```powershell
llm-wiki --project-root <root> lint-wiki
```

当前检查：

- `raw/` source 是否有对应 source page
- `cache/extracted/` packet 是否存在
- `wiki/index.md` 是否包含对应 source link
- 日志是否可持续追加

## 5. Claude Code 集成设计

当前支持三种接入方式：

### 5.1 手工在 Claude Code 中维护

- 先执行 `ingest`
- 再执行 `print-ingest-workflow`
- 将三个阶段 prompt 按顺序交给 Claude

### 5.2 CLI 直连 Claude Code

- `ingest-claude`
- `query-wiki-claude`
- `claude-playbook`

### 5.3 通过 MCP 嵌入 Claude Code

资源：

- `wiki://status`
- `wiki://permission-policy`
- `wiki://security-summary`
- `wiki://curation-status`
- `wiki://claude-playbook`

Wiki 主工具：

- `ingest_wiki_local`
- `query_wiki_local`
- `lint_wiki`
- `get_ingest_prompt`
- `get_ingest_workflow`
- `get_query_prompt`

兼容层工具：

- `index_documents`
- `doctor`
- `list_document_paths`
- `list_question_groups`
- `count_files_by_extension`
- `count_supported_extensions`
- `search_related_paths`
- `find_paths_by_basename`
- `get_document_record`
- `list_comments`
- `answer_question_local`
- `answer_group_local`
- `apply_fixes`
- `build_pivot_chart`
- `run_python_document`

## 6. 兼容层保留原因

之所以保留旧工具层，是因为赛题里仍然包含：

- Office/代码文档解析
- TODO 责任人统计
- 批注驱动修复
- 受控代码执行
- 图表生成
- 安全对抗样例

这些能力现在更适合作为 wiki ingest 的补充工具和安全演示能力，而不是系统唯一主线。

## 7. 当前边界

当前版本已经稳定，但还有这些边界：

1. topic seed 生成仍是启发式规则，不是语义聚类引擎
2. `lint-wiki` 目前偏结构检查，还没做完整链接图分析
3. `query-wiki` 目前还是轻量关键字匹配，不是向量检索
4. 旧兼容层和 wiki 页之间的自动映射还可以继续增强
5. Claude 的高层 wiki curation 仍主要通过 prompt/workflow 驱动

## 8. 当前结论

当前版本最准确的系统定义是：

> 一个以 `Claude Code` 为 wiki maintainer、以 `raw/wiki/cache/CLAUDE.md` 为核心结构、以 `ingest/query/lint` 为主循环、并保留赛题兼容工具层的 LLM Wiki 工作台。
