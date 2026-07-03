# llm-wiki 逻辑细节

## 1. 主逻辑

当前主逻辑是：

- `raw/` 输入原始证据
- 本地代码生成 deterministic seed
- Claude Code 维护 `wiki/`
- 用户和工具从 `wiki/` 获取知识结果

## 2. `wiki_workspace.py` 的职责

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

每个 `raw` source 会生成 packet、summary seed、concept seed、entity seed。

## 4. Claude workflow 逻辑

- `source-curation`
- `concept-and-entity-synthesis`
- `index-and-log-finalize`

## 5. query 逻辑

- `query_local()`
- `build_query_prompt()`

## 6. 辅助工具层逻辑

### 6.1 `indexer.py`

当前职责不是建库，而是：

- 扫描 `docs/`
- 提取支持的文档
- 在内存中构造临时文档表
- 在内存中构造 comment 视图
- 提供 basename / keyword / comment 检索

### 6.2 `extractors.py`

负责：

- OOXML 文档提取
- 文本文档提取
- legacy Office 转换兜底
- 结构化 TODO 抽取
- fix action 抽取

支持结构：

```text
TODO: <todo text> TO: <assignee> END_DATE: YYYYMMDD
```

### 6.3 `answerer.py`

负责：

- 题目风格问题的本地回答
- TODO 修复落盘到 `output/fixed/`
- Excel 图表输出
- 受控 Python 执行
- 审计日志输出

### 6.4 `mcp_runtime.py` / `mcp_server.py`

负责把两类能力暴露给 Claude：

- wiki 主工具
- 无状态 auxiliary tools

## 7. 当前真实边界

一句话概括：

> 现在的主系统是 `wiki_workspace + Claude staged curation + wiki query`，旧式文档处理逻辑只是按需扫描的可调用工具层。
