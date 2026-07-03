# Karpathy 对齐说明

## 1. 当前修正点

你指出的问题是对的。之前的版本虽然开始使用 `raw/wiki` 叙事，但本质上仍然太像：

- 本地 Python 工具主导
- wiki 只是一个被包装出来的结果层
- `sources/topics` 结构过于简化

这和 Karpathy 定义下的 `LLM Wiki` 还有明显偏差。

## 2. Karpathy 风格的关键点

对齐 Karpathy，不是只要有：

- `raw/`
- `wiki/`

就算完成。

真正关键的是：

1. 模型应主要维护 wiki page
2. wiki page 应是长期积累的工作对象
3. 原始资料应被“编译”成 wiki，而不是直接被模型拿来即时问答
4. 目录形态应支持 summary、entity、concept、synthesis 等更稳定的知识组织

## 3. 当前仓库之前的偏差

主要有四个：

### 3.1 主系统重心错误

旧版本虽然引入了 `ingest/query/lint`，但代码和文档重心仍偏向：

- `docs/question/output`
- `ask/answer`
- 本地 deterministic 问答器

这会让 wiki 看起来像“兼容层附属功能”，而不是系统主线。

### 3.2 目录组织过于扁平

旧的：

- `wiki/sources/`
- `wiki/topics/`

虽然比纯问答器更进一步，但仍不够接近主流 Claude-native wiki 实践。

### 3.3 缺少 Claude 原生命令入口

如果项目真的以 Claude Code 为主控，就不应只提供：

- Python CLI
- MCP

还应有：

- `AGENTS.md`
- `.claude/commands/*`

### 3.4 赛题能力没有被正确吸收

赛题里的：

- Office 文档
- 批注/TODO
- 安全对抗

不应独立构成主产品，而应被纳入 wiki ingest 的证据抽取与安全边界。

## 4. 当前已做的修正

当前版本已经改成：

### 4.1 目录结构

从：

- `wiki/sources/`
- `wiki/topics/`

改为：

- `wiki/summaries/`
- `wiki/concepts/`
- `wiki/entities/`
- `wiki/syntheses/`
- `wiki/overview/`
- `wiki/graph/`

### 4.2 Claude-native 入口

新增：

- `AGENTS.md`
- `.claude/commands/ingest-wiki.md`
- `.claude/commands/query-wiki.md`
- `.claude/commands/lint-wiki.md`

### 4.3 staged workflow

当前 ingest 三阶段调整为：

1. `source-curation`
2. `concept-and-entity-synthesis`
3. `index-and-log-finalize`

### 4.4 seed 形态

当前 deterministic ingest 不再只生成：

- source page seed
- topic page seed

而是生成：

- summary seed
- concept seed
- entity seed
- overview seed

## 5. 当前仍未完全到位的部分

严格说，现在只是把方向修正到了正确轨道，还没全部做完。

还存在这些后续工作：

1. `wiki/syntheses/` 还未深用
2. `wiki/graph/` 还只是预留结构
3. concept/entity seed 仍是启发式，不是更强的知识聚类
4. 旧兼容层代码仍偏重，需要继续降权和收口

## 6. 当前结论

目前这次修正后的版本，已经比之前更接近 Karpathy 和 GitHub 上更成熟的 Claude-native wiki 方案，因为它满足了：

- Claude 是 maintainer
- page 是主工作对象
- raw 是证据层
- deterministic 代码是辅助层
- 赛题能力被吸收到 ingest/query/security 中

但要完全贴近更成熟实现，下一步仍应继续强化：

- synthesis 层
- graph 层
- entity / concept 的更准分类
- 更少的旧问答器叙事
