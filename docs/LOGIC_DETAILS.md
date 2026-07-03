# llm-wiki 当前逻辑细节

## 1. 当前主线

当前主线是：

- `raw/` 输入证据
- 本地生成 wiki seed
- Claude 维护 wiki page
- 用户和工具从 wiki 获取答案

与 page curation 无关的旧搜索、题组答题、修复、执行链路已经删除。

## 2. `wiki_workspace.py` 的职责

负责：

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

### 3.3 concept / entity seed

当前会从：

- source title
- key points

提取 topic phrase，然后写入：

- `wiki/concepts/<slug>.md`
- `wiki/entities/<slug>.md`

### 3.4 overview 页面

当前自动生成：

- `wiki/overview/dashboards.md`
- `wiki/overview/knowledge-map.md`

## 4. Claude workflow 逻辑

### 4.1 source-curation

只更新：

- `wiki/summaries/*.md`

### 4.2 concept-and-entity-synthesis

更新：

- `wiki/concepts/*.md`
- `wiki/entities/*.md`

### 4.3 index-and-log-finalize

更新：

- `wiki/index.md`
- `wiki/overview/*.md`
- `wiki/log.md`

## 5. query 逻辑

### 5.1 `query_local()`

当前对 `wiki/**/*.md` 做轻量文本命中打分。

### 5.2 `build_query_prompt()`

先调用本地 query，再将结果拼成 Claude 可用上下文。

## 6. `AGENTS.md` 和 `CLAUDE.md`

`AGENTS.md`

- 说明仓库是什么
- 定义 Claude 是 maintainer
- 定义 page 类型边界

`CLAUDE.md`

- 约束具体编辑行为
- 定义不能修改 `raw/`
- 定义 summary / concept / entity / synthesis 的职责

## 7. `.claude/commands`

当前生成：

- `ingest-wiki.md`
- `query-wiki.md`
- `lint-wiki.md`

## 8. 当前真实状态

一句话概括：

> 现在的主系统就是 `wiki_workspace + AGENTS/CLAUDE + staged Claude curation + wiki query`。
