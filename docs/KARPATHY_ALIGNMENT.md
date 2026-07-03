# Karpathy 对齐说明

## 1. 当前修正点

之前的问题有两个：

1. 主系统重心错放在本地文件搜索和答题器
2. wiki 结构过于简化

这次已经进一步修正为：

- Claude Code 是 maintainer
- wiki page 是主工作对象
- `raw/` 是证据层
- deterministic 本地代码只是辅助层
- 与 page curation 无关的旧搜索/答题器代码已经删除

## 2. Karpathy 风格的关键点

关键不是只要有：

- `raw/`
- `wiki/`

而是：

1. 模型主要维护 wiki page
2. wiki page 是长期积累的工作对象
3. 原始资料被编译成 wiki，而不是直接拿来即时问答
4. 目录结构支持 summary、entity、concept、synthesis 等稳定知识组织

## 3. 当前版本对齐后的结构

当前结构：

- `wiki/summaries/`
- `wiki/concepts/`
- `wiki/entities/`
- `wiki/syntheses/`
- `wiki/overview/`
- `wiki/graph/`
- `AGENTS.md`
- `.claude/commands/*`

这比旧的：

- `wiki/sources/`
- `wiki/topics/`

更接近 Claude-native wiki 实践。

## 4. 当前结论

目前仓库已经不再把自己定义成文件搜索/答题器，而是：

> 一个以 `Claude Code` 为主要维护者、围绕 `raw -> wiki` 循环运转的 Karpathy 风格 LLM Wiki。
