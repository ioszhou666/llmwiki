# llm-wiki

`llm-wiki` 当前版本严格收敛到 Karpathy 风格的 `LLM Wiki` 主线：`Claude Code` 直接维护一个持续演化的 markdown wiki，本地 Python 代码只负责 deterministic seed、结构脚手架和安全边界。

与 page curation 无关的旧文件搜索、题组答题、文档修复、图表生成、受控执行等代码已经从主系统中移除。

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
  - 原始证据层，只读
- `wiki/summaries/`
  - source-grounded summary
- `wiki/concepts/`
  - 跨 source 的概念、流程、系统、项目、决策
- `wiki/entities/`
  - 团队、产品、工具、服务、环境、负责人等命名实体
- `wiki/syntheses/`
  - 更高层聚合页
- `wiki/overview/`
  - 导航、dashboard、knowledge map
- `cache/extracted/`
  - deterministic source packet
- `AGENTS.md`
  - 仓库级 maintainer 约束
- `CLAUDE.md`
  - Claude curation 规则
- `.claude/commands/`
  - Claude Code 命令入口

## 设计原则

Karpathy 风格的重点不在“一次性检索问答”，而在：

1. 把原始资料编译成 wiki page
2. 让模型优先维护 page
3. 让知识随着资料增长持续演化

因此当前版本的主流程是：

1. `ingest`
   - 本地生成 `cache/extracted/`、`wiki/summaries/` seed、`wiki/concepts/` seed、`wiki/entities/` seed
2. `ingest-claude`
   - Claude 按 staged workflow 做真正的 curation
3. `query-wiki`
   - 从 `wiki/` 中本地检索
4. `query-wiki-claude`
   - 基于 `wiki/` 片段由 Claude 回答
5. `lint-wiki`
   - 检查结构和覆盖关系

## Claude Code 的角色

当前仓库里，`Claude Code` 不是问答后端，而是：

- `wiki/` 的 maintainer
- `summaries / concepts / entities / syntheses` 的编辑者
- `index.md / overview / log.md` 的维护者

本地代码只做：

- 文档解析
- 批注/TODO 提取
- deterministic seed 生成
- 安全边界

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
llm-wiki --project-root D:\llmwiki\demo claude-status
llm-wiki-mcp --project-root D:\llmwiki\demo
```

## 当前 staged workflow

`ingest-claude` 和 `print-ingest-workflow` 当前输出三个阶段：

1. `source-curation`
   - 维护 `wiki/summaries/*.md`
2. `concept-and-entity-synthesis`
   - 从 `wiki/concepts/` 和 `wiki/entities/` seed 起步
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

- `wiki://status`
- `wiki://curation-status`
- `wiki://claude-playbook`
- `wiki://permission-policy`
- `wiki://security-summary`
- `ingest_wiki_local`
- `query_wiki_local`
- `lint_wiki`
- `get_ingest_prompt`
- `get_ingest_workflow`
- `get_query_prompt`

## 当前状态

当前版本已经落地：

- Claude-native wiki 目录结构
- `AGENTS.md` 与 `CLAUDE.md` 双约束
- `.claude/commands` 入口
- `summaries / concepts / entities / overview` seed 体系
- staged Claude workflow
- wiki-only MCP 资源与工具
- 安全边界

测试状态：

```text
12 passed
```

## 相关文档

- 开源调研：[docs/OPEN_SOURCE_RESEARCH.md](D:/llmwiki/project/docs/OPEN_SOURCE_RESEARCH.md)
- Claude 使用：[docs/CLAUDE_USAGE.md](D:/llmwiki/project/docs/CLAUDE_USAGE.md)
- 系统设计：[docs/SYSTEM_DESIGN.md](D:/llmwiki/project/docs/SYSTEM_DESIGN.md)
- 逻辑细节：[docs/LOGIC_DETAILS.md](D:/llmwiki/project/docs/LOGIC_DETAILS.md)
- 安全加固：[docs/SECURITY_HARDENING.md](D:/llmwiki/project/docs/SECURITY_HARDENING.md)
- Karpathy 对齐说明：[docs/KARPATHY_ALIGNMENT.md](D:/llmwiki/project/docs/KARPATHY_ALIGNMENT.md)
