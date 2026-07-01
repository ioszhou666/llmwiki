# llm-wiki

`llm-wiki` 是一个本地可运行的文档 Wiki 工作台，面向赛题里要求的多格式检索、批注治理、安全问答和批量答案生成。

当前仓库已补充 `Claude Code` 工作流入口，采用“Claude Code + 本地工具层”的混合架构。当前机器允许通过 Anthropic 兼容中转接口运行 Claude Code。

## 已实现能力

- 多格式抽取：`doc/docx/ppt/pptx/xls/xlsx/xml/java/py/html/md/js`
- 批注治理：Office 批注、代码 TODO、按责任人和日期筛选
- 修复输出：文本、`docx`、`xlsx`、`pptx` 的确定性修复
- 批量答题：生成 `output/group-X-answer.md`
- 单题问答：直接回答一条自然语言问题
- 安全防护：`Permission.json`、危险命令、密码类问题、Prompt 注入拦截
- 审计日志：输出 `output/audit.jsonl`

## 目录约定

工作区根目录默认包含：

```text
workspace/
├─ docs/
├─ question/
├─ output/
└─ Permission.json
```

## 常用命令

```powershell
python -m pip install -e .
llm-wiki --project-root D:\llmwiki\demo_workspace index
llm-wiki --project-root D:\llmwiki\demo_workspace answer --group group-1.md
llm-wiki --project-root D:\llmwiki\demo_workspace answer-all
llm-wiki --project-root D:\llmwiki\demo_workspace ask --question "待张三处理的批注"
llm-wiki --project-root D:\llmwiki\demo_workspace ask-claude --question "待张三处理的批注"
llm-wiki --project-root D:\llmwiki\demo_workspace answer-claude --group group-1.md
llm-wiki --project-root D:\llmwiki\demo_workspace answer-all-claude
llm-wiki-mcp --project-root D:\llmwiki\demo_workspace_release
llm-wiki --project-root D:\llmwiki\demo_workspace doctor
llm-wiki --project-root D:\llmwiki\demo_workspace claude-status
llm-wiki --project-root D:\llmwiki\demo_workspace validate
llm-wiki --project-root D:\llmwiki\demo_workspace release --target D:\llmwiki\deliverables
llm-wiki --project-root D:\llmwiki\demo_workspace bootstrap-demo --target D:\llmwiki\demo_workspace
```

## 说明

- `index`：建立或重建 SQLite 索引
- `answer`：回答单个 `group-x.md`
- `answer-all`：批量回答全部 `group-*.md`
- `ask`：直接回答一条自然语言问题
- `ask-claude`：通过 Claude Code 回答一条自然语言问题
- `answer-claude`：通过 Claude Code 回答单个题组
- `answer-all-claude`：通过 Claude Code 批量回答全部题组
- `llm-wiki-mcp`：以标准 MCP Server 方式暴露本地索引、批注、修复和执行工具
- `doctor`：检查运行时、可选依赖和索引能力
- `claude-status`：检查 Claude Code 当前可执行文件、登录状态和提供方
- `validate`：执行索引、批量答题、修复产物与审计日志的端到端验收
- `release`：生成包含调研文档、系统设计、验证报告和示例输出的交付包
- `bootstrap-demo`：快速生成一套演示工作区

## 持续集成

- 仓库内置 GitHub Actions，会在推送后自动执行 `pytest`
- 本地建议在提交前运行 `python -m pytest tests -q`

## 文档

- 开源调研见 `docs/OPEN_SOURCE_RESEARCH.md`
- 系统设计见 `docs/SYSTEM_DESIGN.md`
- Claude Code 调用说明见 `docs/CLAUDE_USAGE.md`
- 当前系统逻辑详解见 `docs/LOGIC_DETAILS.md`
- 安全加固说明见 `docs/SECURITY_HARDENING.md`

## MCP 接入

如果你希望让 Claude Code 直接把本项目当作工具服务器使用，可以执行：

```powershell
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\llmwiki\demo_workspace_release
```

然后在 Claude Code 中就可以把 `llm-wiki` 作为 MCP 工具源调用。
当前 MCP 资源包括 `wiki://status`、`wiki://permission-policy` 和 `wiki://security-summary`。

## 典型题型

- `统计全项目 docx 总数量`
- `列出全部 md 文件路径`
- `统计待张三处理的批注数量`
- `截止20261231的批注`
- `根据 gauss 相关脚本的执行结果给出输出`

## Claude Code 快速使用

推荐最少按下面 4 步执行：

```powershell
llm-wiki --project-root D:\llmwiki\demo_workspace_release doctor
llm-wiki --project-root D:\llmwiki\demo_workspace_release claude-status
llm-wiki --project-root D:\llmwiki\demo_workspace_release ask-claude --question "找出产品V1需求.docx 路径"
llm-wiki --project-root D:\llmwiki\demo_workspace_release answer-all-claude
```

更完整的 Claude Code 使用说明、兼容中转配置和项目内部调用链见 `docs/CLAUDE_USAGE.md`。

## 当前边界

- `doc/ppt/xls` 优先尝试 `LibreOffice` 转换，再回退到 `Tika` 文本提取，最后才是 plain fallback
- “自由批注修复”当前以确定性规则为主，例如“把 A 改成 B”“补充 XXX 字段”
- 受控执行目前只开放了 Python 文件，并通过 AST 做安全检查
