# Karpathy 对齐说明

## 1. 这次修正解决了什么

之前方向偏差主要有两点：

1. 把主系统做成了本地文件搜索 / 问答引擎
2. wiki 只是附属结构，没有成为核心工作对象

当前已经修正为：

- `Claude Code` 是 wiki maintainer
- `wiki page` 是主要工作对象
- `raw/` 是证据层
- deterministic Python 只是支撑层
- 旧式文件问答 / 修复 / 执行逻辑不再充当产品定义

## 2. Karpathy 风格的关键点

Karpathy 所说的 `LLM Wiki` 重点不是一次性 RAG，而是：

1. 把原始资料整理成 page
2. 让模型持续维护这些 page
3. 让知识随着资料增长持续演化

因此真正重要的是：

- summary page
- concept page
- entity page
- synthesis page
- overview / map / graph

## 3. 当前实现如何对齐

当前仓库结构已经围绕这些对象重组：

- `wiki/summaries/`
- `wiki/concepts/`
- `wiki/entities/`
- `wiki/syntheses/`
- `wiki/overview/`
- `wiki/graph/`
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/commands/*`

这比旧式的 `sources/topics` 或“直接搜文件回答”更接近 Karpathy 定义。

## 4. 旧能力为何仍然保留

用户场景仍然需要：

- Office 文档抽取
- TODO / 批注统计
- 修复建议
- 受控执行
- 安全对抗检测

这些能力现在保留，但只作为 auxiliary MCP tools：

- 不再充当主系统
- 不再决定产品叙事
- 不再替代 wiki curation

## 5. 当前结论

当前版本已经收敛到以下定义：

> 一个以 `Claude Code` 为主要维护者、以 `raw -> wiki` 为核心循环、并保留可选 deterministic 工具层的 Karpathy 风格 LLM Wiki。
