# llm-wiki

`llm-wiki` 现在按 Karpathy 的 `LLM Wiki` 理念实现，但不是简单复刻一个本地检索器。主目标是构建一个可由 `Claude Code` 直接维护、持续演化、面向证据的 markdown wiki，并在这个基础上适配当前赛题中的办公文档、TODO、批注修复和安全约束。

当前版本的核心判断是：

- 主系统应是 `Claude Code + wiki workspace`
- 本地 Python 代码应是 deterministic 辅助层
- 赛题能力应被吸收到 ingest / curation / query 过程中，而不是反过来让 wiki 退化成问答器

## 当前主结构

```text
project/
├─ raw/
├─ wiki/
│  ├─ index.md
│  ├─ log.md
│  ├─ overview/
│  ├─ summaries/
│  ├─ concepts/
│  ├─ entities/
│  ├─ syntheses/
│  └─ graph/
├─ cache/
│  └─ extracted/
├─ .claude/
│  └─ commands/
├─ AGENTS.md
├─ CLAUDE.md
└─ Permission.json
```

说明：

- `raw/`
  - 原始资料层，只读
- `wiki/summaries/`
  - 基于 source 的事实摘要页
- `wiki/concepts/`
  - 跨 source 的概念、流程、项目、决策、系统页
- `wiki/entities/`
  - 命名实体页，例如团队、产品、工具、服务、环境、负责人
- `wiki/syntheses/`
  - 更高层聚合页
- `wiki/overview/`
  - 导航页、dashboard、knowledge map
- `cache/extracted/`
  - deterministic source packet
- `AGENTS.md`
  - 仓库级 maintainer 约束
- `CLAUDE.md`
  - Claude curation 规则
- `.claude/commands/`
  - 面向 Claude Code 的命令入口

## 设计原则

Karpathy 风格的重点不在“让模型检索文档”，而在：

1. 把原始资料编译成可维护的 wiki
2. 让模型优先维护 page，而不是直接回答
3. 让知识随着资料增长持续演化

因此当前版本的主流程是：

1. `ingest`
   - 本地生成 `cache/extracted/`、`wiki/summaries/` seed、`wiki/concepts/` seed、`wiki/entities/` seed
2. `ingest-claude`
   - Claude 按 staged workflow 做真正的 curation
3. `query-wiki`
   - 从 wiki 中本地检索
4. `query-wiki-claude`
   - 基于 wiki 片段由 Claude 回答
5. `lint-wiki`
   - 检查结构和覆盖关系

## Claude Code 的角色

当前仓库里，`Claude Code` 不是一个“问答后端”，而是：

- `wiki/` 的 maintainer
- `summaries / concepts / entities / syntheses` 的编辑者
- `index.md / overview / log.md` 的维护者

本地代码只做：

- 文档解析
- 批注/TODO 提取
- deterministic seed 生成
- 安全边界
- 兼容层工具支持

## 主要命令

```powershell
python -m pip install -e .

llm-wiki --project-root D:\llmwiki\demo init-wiki
llm-wiki --project-root D:\llmwiki\demo bootstrap-demo --target D:\llmwiki\demo
llm-wiki --project-root D:\llmwiki\demo ingest
llm-wiki --project-root D:\llmwiki\demo ingest-claude
llm-wiki --project-root D:\llmwiki\demo claude-playbook
llm-wiki --project-root D:\llmwiki\demo print-ingest-workflow
llm-wiki --project-root D:\llmwiki\demo query-wiki --question "CRM migration"
llm-wiki --project-root D:\llmwiki\demo query-wiki-claude --question "当前 wiki 对 CRM migration 的结论是什么"
llm-wiki --project-root D:\llmwiki\demo lint-wiki
llm-wiki-mcp --project-root D:\llmwiki\demo
```

当前这些命令的含义是：

- `init-wiki`
  - 初始化 Claude-native wiki 工作区
- `bootstrap-demo`
  - 创建最小 demo wiki 项目
- `ingest`
  - 生成 deterministic summary/concept/entity seed
- `ingest-claude`
  - 按 staged workflow 让 Claude 真正维护 wiki
- `print-ingest-workflow`
  - 输出当前 staged curation prompt
- `query-wiki`
  - 本地从 `wiki/` 检索
- `query-wiki-claude`
  - 让 Claude 基于 `wiki/` 回答
- `lint-wiki`
  - 检查 wiki 一致性

## 当前 staged workflow

`ingest-claude` 和 `print-ingest-workflow` 当前输出三个阶段：

1. `source-curation`
   - 维护 `wiki/summaries/*.md`
2. `concept-and-entity-synthesis`
   - 从 `wiki/concepts/` 与 `wiki/entities/` seed 起步
   - 合并重复页
   - 提炼跨 source 知识
3. `index-and-log-finalize`
   - 刷新 `index.md`、`overview/`、`log.md`

## MCP 接入

如果要在 Claude Code 中作为外部工具使用：

```powershell
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\llmwiki\demo
```

当前 wiki 主资源与工具：

- `wiki://curation-status`
- `wiki://claude-playbook`
- `ingest_wiki_local`
- `query_wiki_local`
- `lint_wiki`
- `get_ingest_prompt`
- `get_ingest_workflow`
- `get_query_prompt`

## 与赛题的关系

本项目没有丢掉赛题能力，但位置已经调整：

- Office / 代码文档抽取
- TODO / 批注解析
- deterministic 修复
- 图表生成
- 受控执行
- 安全 deny 策略

这些能力仍保留，但它们现在是：

- ingest 的证据抽取层
- Claude curation 的辅助层
- 对抗样例的安全边界层

不是主产品定义本身。

## 当前状态

当前版本已经落地：

- Claude-native wiki 目录结构
- `AGENTS.md` 与 `CLAUDE.md` 双约束
- `.claude/commands` 入口
- `summaries / concepts / entities / overview` seed 体系
- staged Claude workflow
- MCP 资源与工具
- 赛题兼容层与安全边界

测试状态：

```text
30 passed
```

## 相关文档

- 开源调研：[docs/OPEN_SOURCE_RESEARCH.md](D:/llmwiki/project/docs/OPEN_SOURCE_RESEARCH.md)
- Claude 使用：[docs/CLAUDE_USAGE.md](D:/llmwiki/project/docs/CLAUDE_USAGE.md)
- 系统设计：[docs/SYSTEM_DESIGN.md](D:/llmwiki/project/docs/SYSTEM_DESIGN.md)
- 逻辑细节：[docs/LOGIC_DETAILS.md](D:/llmwiki/project/docs/LOGIC_DETAILS.md)
- 安全加固：[docs/SECURITY_HARDENING.md](D:/llmwiki/project/docs/SECURITY_HARDENING.md)
- Karpathy 对齐说明：[docs/KARPATHY_ALIGNMENT.md](D:/llmwiki/project/docs/KARPATHY_ALIGNMENT.md)
