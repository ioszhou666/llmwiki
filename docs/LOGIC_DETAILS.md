# llm-wiki 当前逻辑细节

## 1. 当前主线

当前主线不是：

- `docs/` 建索引
- `question/` 解析题目
- 模型或规则直接答题

当前主线是：

- `raw/` 输入证据
- 本地生成 wiki seed
- Claude 维护 wiki page
- 用户和工具从 wiki 获取答案

## 2. `wiki_workspace.py` 的职责

这是当前主系统的核心。

主要负责：

- 初始化 wiki 目录
- 写入 `AGENTS.md`
- 写入 `CLAUDE.md`
- 写入 `.claude/commands`
- 将 `raw/` 转成 `cache/extracted/`
- 生成 `wiki/summaries/`
- 生成 `wiki/concepts/`
- 生成 `wiki/entities/`
- 更新 `wiki/overview/`
- 更新 `wiki/index.md`
- 维护 `wiki/log.md`
- 构造 Claude workflow prompt
- 提供本地 wiki 查询
- 提供 wiki lint

## 3. ingest 逻辑

### 3.1 SourcePacket

每个 `raw` source 会被转成 `SourcePacket`，包含：

- 相对路径
- 标题
- 文件类型
- extracted packet 路径
- summary page 路径
- 内容预览
- comment/TODO 线索
- key points

### 3.2 summary seed

每个 source 会生成：

- `cache/extracted/<slug>.md`
- `wiki/summaries/<slug>.md`

summary 页是 source-grounded 的，不承担跨 source synthesis 的职责。

### 3.3 concept / entity seed

当前实现会从：

- source title
- key points

中提取 topic phrase，然后写入：

- `wiki/concepts/<slug>.md`
- `wiki/entities/<slug>.md`

这一步仍然是启发式 seed，不是最终知识组织。

### 3.4 overview 页面

当前自动生成：

- `wiki/overview/dashboards.md`
- `wiki/overview/knowledge-map.md`

目的是让 Claude 和用户都更容易看到当前 wiki 的全局状态。

## 4. Claude workflow 逻辑

### 4.1 source-curation

只更新：

- `wiki/summaries/*.md`

目标：

- 让 source summary 更准确
- 将关键事实沉淀下来

### 4.2 concept-and-entity-synthesis

更新：

- `wiki/concepts/*.md`
- `wiki/entities/*.md`

目标：

- 从 summary 提炼跨 source 知识
- 合并重复页
- 区分抽象概念与命名实体

### 4.3 index-and-log-finalize

更新：

- `wiki/index.md`
- `wiki/overview/*.md`
- `wiki/log.md`

目标：

- 导航清晰
- 变更可追踪

## 5. query 逻辑

### 5.1 `query_local()`

当前对 `wiki/**/*.md` 做轻量文本命中打分。

输出：

- 命中的 page 路径
- 对应 snippet

### 5.2 `build_query_prompt()`

先调用本地 query，再将结果拼成 Claude 可用上下文。

注意点：

- 查询基于 wiki
- wiki 不足时要求显式说明缺口

## 6. AGENTS.md 和 CLAUDE.md 的关系

`AGENTS.md`

- 说明整个仓库是什么
- 定义 Claude 是 maintainer，不是问答器
- 定义 page 类型边界

`CLAUDE.md`

- 约束具体编辑行为
- 定义不能修改 `raw/`
- 定义 summary / concept / entity / synthesis 的职责分工

## 7. `.claude/commands`

当前生成三个命令入口：

- `ingest-wiki.md`
- `query-wiki.md`
- `lint-wiki.md`

这让项目更接近 Claude Code 原生工作流，而不是只靠 Python CLI 组织全部行为。

## 8. 为什么旧兼容层仍在

当前仓库仍保留：

- `indexer.py`
- `answerer.py`
- `question_parser.py`
- `ask/answer/release/validate`

原因不是这些是主系统，而是：

1. 赛题里仍有大量结构化任务
2. Office/TODO/修复/执行链路仍有价值
3. 这些能力可以继续作为 ingest 证据抽取与安全工具层存在

## 9. 当前真实状态

如果只用一句话描述当前逻辑：

> 现在的主系统是 `wiki_workspace + AGENTS/CLAUDE + staged Claude curation + wiki query`，兼容层只是附属工具，不是核心定义。
