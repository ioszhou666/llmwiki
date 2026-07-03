# llm-wiki 逻辑细节

## 1. 主逻辑

当前主逻辑是：

- `raw/` 输入原始证据
- 本地代码生成 deterministic seed
- Claude Code 维护和提升 `wiki/`
- 用户和工具从 `wiki/` 获取知识结果

这与旧版“直接对文件做本地问答”不同。

## 2. `wiki_workspace.py` 的职责

`wiki_workspace.py` 负责：

- 初始化 wiki 目录
- 写入 `AGENTS.md`
- 写入 `CLAUDE.md`
- 写入 `.claude/commands`
- 将 `raw/` 转成 `cache/extracted/`
- 生成 `wiki/summaries/`
- 生成 `wiki/concepts/`
- 生成 `wiki/entities/`
- 刷新 `wiki/overview/`
- 刷新 `wiki/index.md`
- 维护 `wiki/log.md`
- 构造 Claude workflow prompt
- 提供本地 wiki 查询
- 提供 wiki lint

## 3. ingest 逻辑

### 3.1 SourcePacket

每个 `raw` source 会被转换成一个 packet，包含：

- 相对路径
- 标题
- 文件类型
- extracted packet 路径
- summary page 路径
- 内容预览
- comment / TODO 线索
- key points

### 3.2 summary seed

每个 source 对应：

- `cache/extracted/<slug>.md`
- `wiki/summaries/<slug>.md`

### 3.3 concept / entity seed

系统从 source title 和 key points 里提取 topic phrase，再生成：

- `wiki/concepts/<slug>.md`
- `wiki/entities/<slug>.md`

这些只是 Claude 后续整理的起点，不是最终知识页。

### 3.4 overview 页

当前自动生成：

- `wiki/overview/dashboards.md`
- `wiki/overview/knowledge-map.md`

## 4. Claude workflow 逻辑

### 4.1 `source-curation`

只更新：

- `wiki/summaries/*.md`

### 4.2 `concept-and-entity-synthesis`

主要更新：

- `wiki/concepts/*.md`
- `wiki/entities/*.md`
- `wiki/syntheses/*.md`

### 4.3 `index-and-log-finalize`

主要更新：

- `wiki/index.md`
- `wiki/overview/*.md`
- `wiki/log.md`

## 5. query 逻辑

### 5.1 `query_local()`

对 `wiki/**/*.md` 做轻量文本打分，返回相关页面片段。

### 5.2 `build_query_prompt()`

先调用本地 wiki query，再将结果拼成 Claude 可用上下文。

## 6. 辅助工具层逻辑

### 6.1 `indexer.py`

负责：

- 扫描 `docs/`
- 提取可支持文档
- 存入 SQLite
- 建立 FTS5 索引
- 提供 comment 检索

### 6.2 `extractors.py`

负责：

- OOXML 文档提取
- 文本文档提取
- legacy Office 转换兜底
- 结构化 TODO 抽取
- fix action 抽取

当前支持标准结构：

```text
TODO: <todo text> TO: <assignee> END_DATE: YYYYMMDD
```

### 6.3 `answerer.py`

负责：

- 题目风格问题解析后的本地回答
- TODO 修复落盘到 `output/fixed/`
- Excel 透视图输出
- 受控 Python 执行
- 审计日志输出

### 6.4 `mcp_runtime.py` / `mcp_server.py`

负责把两类能力统一暴露给 Claude：

- wiki 主工具
- auxiliary utility tools

## 7. 当前真实边界

一句话概括：

> 现在的主系统是 `wiki_workspace + Claude staged curation + wiki query`，而旧式文件处理逻辑只是可调用工具层。
