# llm-wiki

`llm-wiki` 现在按 Karpathy 提出的 `LLM Wiki` 思路重构：主目标不是“本地规则问答器”，而是一个由 `Claude Code` 维护的持续演化知识库。

核心架构是 3 层：

- `raw/`
  - 原始资料层，只读
- `wiki/`
  - Claude Code 维护的 markdown wiki
- `CLAUDE.md`
  - 约束 ingest / query / lint 行为的 schema

当前仓库保留了早期的抽取、权限、安全、MCP 和文档修复能力，但这些能力现在被定位为 wiki ingest/query 过程中的辅助工具层，而不是系统主产品。

## 目录结构

默认项目根目录如下：

```text
project/
├─ raw/
├─ wiki/
│  ├─ index.md
│  ├─ log.md
│  └─ sources/
├─ cache/
│  └─ extracted/
├─ output/
├─ CLAUDE.md
└─ Permission.json
```

补充说明：

- `raw/`
  - 放原始资料，Claude 不应修改
- `wiki/`
  - 放整理后的知识页
- `wiki/index.md`
  - 全局入口
- `wiki/log.md`
  - ingest/query/lint 的操作日志
- `cache/extracted/`
  - 本地确定性抽取结果，供 Claude ingest 时参考
- `Permission.json`
  - 高危路径、文件、命令的 deny 策略

## 主命令

```powershell
python -m pip install -e .

llm-wiki --project-root D:\llmwiki\demo_workspace init-wiki
llm-wiki --project-root D:\llmwiki\demo_workspace bootstrap-demo --target D:\llmwiki\demo_workspace
llm-wiki --project-root D:\llmwiki\demo_workspace ingest
llm-wiki --project-root D:\llmwiki\demo_workspace ingest-claude
llm-wiki --project-root D:\llmwiki\demo_workspace claude-playbook
llm-wiki --project-root D:\llmwiki\demo_workspace print-ingest-prompt
llm-wiki --project-root D:\llmwiki\demo_workspace print-query-prompt --question "当前 wiki 对 CRM migration 的结论是什么"
llm-wiki --project-root D:\llmwiki\demo_workspace query-wiki --question "gauss runbook 里怎么连接数据库"
llm-wiki --project-root D:\llmwiki\demo_workspace query-wiki-claude --question "当前 wiki 对 CRM migration 的结论是什么"
llm-wiki --project-root D:\llmwiki\demo_workspace lint-wiki
llm-wiki --project-root D:\llmwiki\demo_workspace doctor
llm-wiki --project-root D:\llmwiki\demo_workspace claude-status
llm-wiki-mcp --project-root D:\llmwiki\demo_workspace
```

这些命令的定位分别是：

- `init-wiki`
  - 初始化 `raw/wiki/cache/CLAUDE.md/index.md/log.md`
- `bootstrap-demo`
  - 创建一个 Karpathy 风格 demo 工作区
- `ingest`
  - 本地确定性抽取 raw source，并生成 source packet 与 source page seed
- `ingest-claude`
  - 调 Claude Code 对 wiki 页面做真正的整理和更新
- `claude-playbook`
  - 输出当前项目推荐的 Claude Code 调用手册
- `print-ingest-prompt`
  - 输出标准 ingest prompt，适合直接贴给 Claude Code
- `print-query-prompt`
  - 输出标准 query prompt，适合直接贴给 Claude Code
- `query-wiki`
  - 直接从 `wiki/` 搜索并回答
- `query-wiki-claude`
  - 让 Claude 基于 wiki 片段回答，而不是直接裸读原始资料
- `lint-wiki`
  - 检查 `raw/wiki/index/log` 是否一致

## Claude Code 的位置

这个项目现在把 `Claude Code` 放在主控位置：

- 本地抽取层负责：
  - 文档解析
  - 批注/TODO 抽取
  - 权限拦截
  - source packet 生成
- Claude Code 负责：
  - 维护 `wiki/sources/*.md`
  - 维护更高层的概念页
  - 更新 `wiki/index.md`
  - 记录 `wiki/log.md`
  - 基于 wiki 回答问题

也就是说，当前设计已经从“Claude 只是问答后端”纠偏成了“Claude 是 wiki maintainer”。

## MCP 接入

如果希望 Claude Code 把本项目直接作为外部工具源使用，可以执行：

```powershell
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\llmwiki\demo_workspace
```

当前 MCP 公开了两类能力：

- wiki 主链路
  - `wiki://curation-status`
  - `wiki://claude-playbook`
  - `ingest_wiki_local`
  - `query_wiki_local`
  - `lint_wiki`
  - `get_ingest_prompt`
  - `get_query_prompt`
- 辅助工具层
  - `wiki://status`
  - `wiki://permission-policy`
  - `wiki://security-summary`
  - 文档索引、批注、修复、图表、受控执行等工具

## 兼容层

仓库里仍然保留旧的命令和模块：

- `index`
- `ask`
- `answer`
- `answer-all`
- `ask-claude`
- `answer-claude`

这些能力现在应理解为“辅助工具层 / 旧赛题兼容层”，不是 `llm-wiki` 的主方向。

## 文档

- 开源调研：`docs/OPEN_SOURCE_RESEARCH.md`
- 系统设计：`docs/SYSTEM_DESIGN.md`
- Claude Code 调用说明：`docs/CLAUDE_USAGE.md`
- 当前系统逻辑详解：`docs/LOGIC_DETAILS.md`
- 安全加固说明：`docs/SECURITY_HARDENING.md`
- Karpathy 方向纠偏说明：`docs/KARPATHY_ALIGNMENT.md`

## 当前状态

当前版本已经补上：

- `raw/wiki/schema` 主结构
- `ingest / query / lint` 主命令
- Claude Code 主控 ingest/query 流程
- MCP 的 wiki 资源和工具入口
- deny 路径的结果级过滤

测试状态：

```text
28 passed
```
