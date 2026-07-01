# llm-wiki 当前逻辑详解

## 1. 总览

当前项目同时包含两套能力：

1. `LLM Wiki` 主流程
   - 以 `raw -> cache/wiki seed -> Claude curation -> wiki query` 为中心
2. 赛题兼容工具层
   - 以 `docs/question/output`、本地索引、TODO 修复、图表、受控执行为中心

从版本定位上看，第一套是主叙事，第二套是保留能力。

## 2. 主模块职责

### 2.1 `wiki_workspace.py`

这是当前主系统的核心。

主要职责：

- 初始化 wiki 工作区
- 读取 `raw/`
- 生成 extracted packet
- 生成 `wiki/sources/` source page
- 生成 `wiki/topics/` topic seed page
- 刷新 `wiki/index.md`
- 追加 `wiki/log.md`
- 构造 Claude ingest/query prompt
- 构造 Claude staged workflow
- 对 `wiki/` 做本地查询和 lint

关键对象：

- `SourcePacket`
  - 对单个 raw source 的 deterministic 提取结果
- `WorkflowPrompt`
  - staged Claude workflow 中单个阶段的 prompt
- `TopicSeed`
  - 由本地逻辑生成的 topic seed

### 2.2 `cli.py`

`cli.py` 同时暴露两类命令：

Wiki 主命令：

- `init-wiki`
- `ingest`
- `ingest-claude`
- `query-wiki`
- `query-wiki-claude`
- `lint-wiki`
- `claude-playbook`
- `print-ingest-prompt`
- `print-ingest-workflow`
- `print-query-prompt`
- `bootstrap-demo`

兼容层命令：

- `index`
- `ask`
- `answer`
- `answer-all`
- `ask-claude`
- `answer-claude`
- `answer-all-claude`
- `doctor`
- `claude-status`
- `validate`
- `release`

### 2.3 `claude_client.py`

职责：

- 发现本地 `claude` 可执行文件
- 检查 `Claude Code` 登录状态
- 执行文本 prompt
- 执行 JSON 封装 prompt

当前 `run_text_prompt()` 用于：

- `ingest-claude`
- `query-wiki-claude`

当前 `ask_json()` 主要服务旧兼容层中的 JSON 输出问答链路。

### 2.4 `mcp_runtime.py`

职责：

- 将当前项目的核心能力组织成 Claude 可调用的运行时接口

它本身不负责 prompt 生成逻辑创新，而是把已有逻辑转换成标准调用面。

### 2.5 `mcp_server.py`

职责：

- 用 `FastMCP` 将 `mcp_runtime.py` 暴露为 stdio 服务

资源分成两类：

- 状态与安全资源
- wiki curation 资源

工具分成两类：

- wiki 主工具
- 兼容层工具

### 2.6 `extractors.py`

职责：

- 识别文档类型
- 提取正文、批注、TODO、元信息
- 输出统一文档记录

这部分是旧兼容层和 wiki ingest 都会复用的底座。

### 2.7 `indexer.py`

职责：

- 将 `docs/` 建成 SQLite + FTS5 索引
- 提供路径查找、全文检索、批注检索

注意：

- 它服务的是 `docs/` 兼容层，不是 `wiki/` 主查询路径
- 当前 `query-wiki` 走的是 `wiki_workspace.query_local()`

### 2.8 `answerer.py`

职责：

- 本地问答
- 题组批量答题
- 基于批注的修复
- Excel 图表生成
- 受控 Python 执行
- 审计日志输出

### 2.9 `security.py`

职责：

- 统一识别 prompt injection
- 拦截危险副作用
- 拦截敏感信息获取
- 应用 `Permission.json`
- 对结果层做 deny 过滤

## 3. Wiki 主流程详解

### 3.1 初始化

`init-wiki` 会确保以下内容存在：

- `raw/`
- `wiki/sources/`
- `wiki/topics/`
- `cache/extracted/`
- `output/`
- `CLAUDE.md`
- `wiki/index.md`
- `wiki/log.md`
- `Permission.json`

如果 `Permission.json` 不存在，会写入默认 deny 配置。

### 3.2 `ingest` 的执行逻辑

`ingest_local()` 的主要步骤如下：

1. 收集 `raw/` 内的 source
2. 对每个 source 生成 `SourcePacket`
3. 写入 `cache/extracted/*.md`
4. 写入 `wiki/sources/*.md`
5. 依据标题和 key points 提取 topic phrase
6. 聚合 topic phrase，生成 `TopicSeed`
7. 写入 `wiki/topics/*.md`
8. 刷新 `wiki/index.md`
9. 追加 `wiki/log.md`
10. 返回 ingest summary

当前 summary 会显式返回：

- `source_pages`
- `topic_pages`
- `index_page`
- `log_page`

### 3.3 Topic Seed 的生成逻辑

当前不是 embedding 聚类，而是启发式聚合：

1. 从 source title 提取候选 topic
2. 从 key points 中提取中英文短语
3. 过滤无意义 stop phrase
4. 用 slug 归一化归桶
5. 汇总 source page、evidence points、keywords

生成的 topic seed page 主要是给 Claude 用来继续整理，而不是最终成品。

### 3.4 `ingest-claude` 的执行逻辑

CLI 在执行 `ingest-claude` 时，会先运行本地 `ingest`，再把 staged workflow 依次发给 Claude。

三个阶段分别是：

1. `source-curation`
   - 只整理 `wiki/sources/*.md`
2. `topic-synthesis`
   - 从 `wiki/topics/` seed 起步
   - 合并重复和近义 topic
   - 形成跨 source synthesis
3. `index-and-log-finalize`
   - 刷新导航页和日志页

这比单 prompt 更稳定，也更贴近 Claude Code 的实际工作方式。

### 3.5 `query-wiki` 的执行逻辑

`query_local()` 会：

1. 遍历 `wiki/` 下 markdown
2. 对问题做轻量 token 化
3. 统计 token 命中分数
4. 提取命中片段
5. 返回排序后的候选页

这一步是 deterministic 检索，不会调用模型。

### 3.6 `query-wiki-claude` 的执行逻辑

`build_query_prompt()` 会先基于 `query_local()` 取回 snippets，再将其拼成标准 prompt 发给 Claude。

约束点：

- 回答应基于 `wiki/`
- wiki 不足时应明确说明缺失
- 默认不让 Claude 自由使用工具

### 3.7 `lint-wiki` 的执行逻辑

当前 `lint()` 重点检查：

- source page 是否缺失
- extracted packet 是否缺失
- `wiki/index.md` 是否缺 link

它本质上是当前 wiki 流程的结构完整性检查器。

## 4. Claude Workflow 逻辑

### 4.1 `build_ingest_workflow()`

这是当前 Claude 集成的关键函数。

它会输出一个三阶段列表，每个元素都带：

- `stage`
- `prompt`

第二阶段现在已经明确加入 merge rules，包括：

- 优先强化已有 seed
- 同一核心实体或流程合并
- 近义窄化页面合并
- source-specific summary 与 cross-source synthesis 不混写

### 4.2 `build_claude_playbook()`

它用于给 Claude Code 使用者提供项目级操作说明，当前内容包括：

- ingest workflow A
- query workflow B
- topic merge rules
- 推荐 CLI
- 推荐 MCP 资源和工具

### 4.3 `CLAUDE.md`

这是仓库级别的 maintainer 约束文件。

当前重点规则：

- 不修改 `raw/`
- 保持 `wiki/index.md` 最新
- 变更写入 `wiki/log.md`
- 优先更新已有 topic page
- `wiki/topics/` 用于 cross-source synthesis
- 合并重叠 topic

## 5. MCP 暴露逻辑

### 5.1 Resources

当前包括：

- `wiki://status`
- `wiki://permission-policy`
- `wiki://security-summary`
- `wiki://curation-status`
- `wiki://claude-playbook`

其中：

- `wiki://curation-status`
  - 更偏向 wiki 工作区状态
- `wiki://status`
  - 更偏向整个项目快照

### 5.2 Tools

当前 wiki 主工具包括：

- `ingest_wiki_local`
- `query_wiki_local`
- `lint_wiki`
- `get_ingest_prompt`
- `get_ingest_workflow`
- `get_query_prompt`

它们让 Claude Code 可以把本项目当成一个外部 wiki curation 工具源。

## 6. 兼容层逻辑

### 6.1 文档索引与问答

旧链路仍然支持：

- `ask`
- `answer`
- `answer-all`
- `ask-claude`
- `answer-claude`
- `answer-all-claude`

这部分的逻辑核心仍是：

- `docs/` 建索引
- `question_parser.py` 识别题型
- `answerer.py` 给出确定性结果或 Claude 辅助结果

### 6.2 文档修复

当前仍支持：

- 文本替换式修复
- 批注驱动修复
- `output/fixed/` 产物输出

### 6.3 图表与执行

当前仍支持：

- Excel pivot chart 生成
- 受控 Python 执行

这些能力仍可用于赛题和演示，但不是 LLM Wiki 主循环的中心。

## 7. 当前限制

1. topic seed 生成不是语义级聚类
2. wiki query 不是高召回检索系统
3. lint 还没覆盖链接图和引用图
4. 兼容层和 wiki 页之间还没有更细粒度自动映射
5. 一些旧命令仍然存在，容易让人误以为那才是主系统

## 8. 当前推荐理解方式

如果用一句话概括当前逻辑：

> `llm-wiki` 现在的主系统是 `wiki_workspace + Claude staged workflow + MCP/CLI 接入`，而不是 `docs/question/output` 那条旧问答链路。
