# llm-wiki 方向纠偏说明

## 1. 为什么要纠偏

这一轮调整的核心原因是：`llm-wiki` 原本被做得更像“本地文档检索 + 规则问答 + 安全执行平台”，而不是 Karpathy 定义下的 `LLM Wiki`。

Karpathy 的原始定义强调：

- `raw sources`
- `wiki`
- `schema`
- `ingest`
- `query`
- `lint`

因此系统主产物应该是“持续维护的 markdown wiki”，而不是“单次问答 JSON 输出”。

## 2. 纠偏前的问题

纠偏前，项目的重心主要放在：

- SQLite / FTS 检索
- Office 批注抽取
- TODO 修复
- 单题 / 批量答题
- Claude 包装问答
- MCP 工具暴露

这些能力并不是无效，而是层级放错了。它们适合作为：

- ingest 辅助工具
- query 辅助工具
- 安全边界控制层

而不应该作为系统主循环。

## 3. 纠偏后的主循环

现在项目的主循环改为：

1. `init-wiki`
   - 建立 `raw/wiki/cache/CLAUDE.md/index.md/log.md`
2. `ingest`
   - 本地做确定性抽取，生成 source packet 和 source page seed
3. `ingest-claude`
   - Claude Code 真正维护 wiki 页面
4. `query-wiki`
   - 从 wiki 页面本地搜索回答
5. `query-wiki-claude`
   - Claude Code 基于 wiki 片段回答
6. `lint-wiki`
   - 检查 source coverage、index、log 和页面一致性

## 4. 当前分层

### 4.1 主系统层

- `src/llm_wiki/wiki_workspace.py`
- `CLAUDE.md`
- `wiki/index.md`
- `wiki/log.md`

### 4.2 Claude 主控层

- `ingest-claude`
- `query-wiki-claude`
- `src/llm_wiki/claude_client.py`

### 4.3 工具辅助层

- `extractors.py`
- `indexer.py`
- `answerer.py`
- `security.py`
- `mcp_runtime.py`
- `mcp_server.py`

这意味着：

- Claude Code 现在是 wiki maintainer
- 本地能力是 Claude 的辅助工具链

## 5. 保留旧能力的原因

旧命令和旧能力没有被删除，原因有两个：

1. 它们对赛题中的 Office / TODO / 安全场景仍然有价值
2. 它们可以继续作为 ingest/query 的辅助能力存在

所以现在项目采取的是：

- 主方向纠偏
- 工具层保留
- 叙事重新归位

## 6. 当前仍需继续完善的点

虽然方向已经纠正，但还有几部分可以继续增强：

1. `ingest-claude` 目前是单 prompt 驱动，还不是更复杂的多阶段 workflow
2. 还缺少更丰富的概念页、人物页、主题页模板
3. `lint-wiki` 目前偏结构一致性检查，还可以继续加链接完整性和引用完整性检查
4. 旧工具层与 wiki 页之间的映射还可以更细，比如自动生成 topic seed page
5. MCP 仍以本地工具为主，后续可以增加更贴近 wiki curation 的高层工具

## 7. 当前结论

这次改动后，项目已经不再把自己定义成“本地规则问答器”，而是：

> 一个以 Claude Code 为主控、以 raw/wiki/schema 为核心结构、以 ingest/query/lint 为主循环的 LLM Wiki 工作台。
