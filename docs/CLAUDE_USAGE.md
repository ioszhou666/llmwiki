# llm-wiki 中的 Claude Code 调用说明

## 1. 目标

这份文档说明本项目中 `Claude Code` 的实际使用方式，包括：

- 如何安装和验证 `Claude Code`
- 如何通过 Anthropic 兼容中转接口接入模型
- 如何在本项目里调用 `ask-claude`、`answer-claude`、`answer-all-claude`
- 项目内部到底是如何把本地索引能力和 Claude Code 组合起来的
- 常见问题如何排查

## 2. 当前架构

本项目不是“纯本地规则引擎”，也不是“完全让模型直接读全量文件”。

当前采用的是混合架构：

1. 本地工具层负责：
   - 多格式文档抽取
   - SQLite/FTS 索引
   - Office / TODO 批注抽取
   - 本地安全检查
   - 文档修复
   - Python 受控执行
2. Claude Code 负责：
   - 问题理解
   - 上下文综合
   - 最终 JSON 结果生成

也就是说，`Claude Code` 是当前项目里的“主问答执行体”，本地模块是它的辅助能力层。

## 3. 安装与验证

### 3.1 安装

Windows 下可以使用：

```powershell
winget install --id Anthropic.ClaudeCode --accept-source-agreements --accept-package-agreements
```

如果当前终端还没刷新 PATH，可以直接使用本机已安装的绝对路径：

```powershell
C:\Users\29678\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe
```

### 3.2 验证安装

```powershell
claude --version
claude auth status
```

如果 `claude` 命令还没生效，可以先用绝对路径执行。

## 4. 使用中转接口

当前项目允许通过 `Anthropic 兼容接口` 中转到模型提供方，例如你现在使用的 `DeepSeek`。

项目运行时读取的是：

```text
C:\Users\<用户名>\.claude\settings.json
```

典型配置形式如下：

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "<your-relay-token>",
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "deepseek-v4-flash",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "deepseek-v4-pro[1M]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL_NAME": "deepseek-v4-pro",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "deepseek-v4-pro[1M]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL_NAME": "deepseek-v4-pro",
    "ANTHROPIC_MODEL": "deepseek-v4-pro"
  }
}
```

注意：

- 不要把真实 token 提交到 Git 仓库
- 文档里只能写占位符，不能写真实密钥
- 如果你切换回 Anthropic 官方链路，删除这些覆盖项即可

## 5. 项目内如何调用 Claude Code

### 5.1 状态检查

建议先检查 Claude Code 当前状态：

```powershell
llm-wiki --project-root D:\llmwiki\demo_workspace_release claude-status
```

期望看到类似输出：

```json
{
  "loggedIn": true,
  "authMethod": "oauth_token",
  "apiProvider": "firstParty",
  "available": true,
  "executable": "..."
}
```

### 5.2 单题问答

```powershell
llm-wiki --project-root D:\llmwiki\demo_workspace_release ask-claude --question "找出产品V1需求.docx 路径"
```

### 5.3 单题组批量回答

```powershell
llm-wiki --project-root D:\llmwiki\demo_workspace_release answer-claude --group group-1.md
```

### 5.4 全题组批量回答

```powershell
llm-wiki --project-root D:\llmwiki\demo_workspace_release answer-all-claude
```

### 5.5 完整流程建议

```powershell
llm-wiki --project-root D:\llmwiki\demo_workspace_release bootstrap-demo --target D:\llmwiki\demo_workspace_release
llm-wiki --project-root D:\llmwiki\demo_workspace_release index
llm-wiki --project-root D:\llmwiki\demo_workspace_release claude-status
llm-wiki --project-root D:\llmwiki\demo_workspace_release answer-all-claude
llm-wiki --project-root D:\llmwiki\demo_workspace_release release --target D:\llmwiki\deliverables
```

## 6. 作为 MCP Server 接入 Claude Code

如果你希望把本项目直接嵌入到 Claude Code 的工具体系里，推荐使用 MCP 方式，而不是只让 Claude 调普通 CLI。

### 6.1 启动方式

本项目已经提供了标准 MCP server 入口：

```powershell
llm-wiki-mcp --project-root D:\llmwiki\demo_workspace_release
```

它默认使用 `stdio` 传输。

### 6.2 在 Claude Code 中注册

```powershell
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\llmwiki\demo_workspace_release
```

如果已经执行过 `python -m pip install -e .`，也可以直接：

```powershell
claude mcp add llmwiki -- llm-wiki-mcp --project-root D:\llmwiki\demo_workspace_release
```

### 6.3 检查是否注册成功

```powershell
claude mcp list
claude mcp get llmwiki
```

### 6.4 当前 MCP 暴露内容

当前 MCP Server 暴露了两类能力：

1. `resources`
   - `wiki://status`
   - `wiki://permission-policy`
2. `tools`
   - `index_documents`
   - `doctor`
   - `list_document_paths`
   - `list_question_groups`
   - `count_files_by_extension`
   - `count_supported_extensions`
   - `search_related_paths`
   - `find_paths_by_basename`
   - `get_document_record`
   - `list_comments`
   - `answer_question_local`
   - `answer_group_local`
   - `apply_fixes`
   - `build_pivot_chart`
   - `run_python_document`

### 6.5 为什么 MCP 更适合 Claude

相比只保留 `ask-claude` 这种外层 CLI 包装，MCP 的优点是：

- Claude Code 可以按需读取资源，不用每次都走整段 prompt
- Claude Code 可以自行决定调用哪个工具
- 更符合 Claude Code / Agent 的标准集成方式
- 后续更容易继续扩展成多工具协作

## 7. 代码内部调用链

### 7.1 入口文件

- `src/llm_wiki/cli.py`
- `src/llm_wiki/answerer.py`
- `src/llm_wiki/claude_client.py`

### 7.2 实际调用过程

项目里的 Claude 路径大致如下：

1. `cli.py` 接收 `ask-claude` / `answer-claude` / `answer-all-claude`
2. `AnswerEngine` 先做本地题型解析和安全检查
3. 再从 SQLite 索引里抽取相关路径、正文摘要和批注作为上下文
4. `ClaudeCodeClient` 调用 Claude Code CLI：

```powershell
claude -p "<prompt>" --output-format json --tools ""
```

5. Claude Code 返回 JSON 包装结果
6. 项目再把 `result` 字段解析成最终答案对象

### 7.3 为什么要 `--tools ""`

当前实现里禁用了 Claude Code 默认工具集，原因是：

- 先把文件访问、命令执行和安全边界收敛到本地工具层
- 避免 Claude Code 在项目外自由扩展命令面
- 先保证比赛场景里的输出格式稳定

后续如果需要增强成更强的 Agent 模式，可以再逐步开放工具。

## 8. 当前与本地 deterministic 能力的关系

项目目前同时保留两套入口：

- 本地 deterministic 入口：
  - `ask`
  - `answer`
  - `answer-all`
- Claude Code 入口：
  - `ask-claude`
  - `answer-claude`
  - `answer-all-claude`

建议理解为：

- 本地入口：更稳定、可预测、方便回归测试
- Claude 入口：更符合“依赖 Claude Code”的赛题要求，也更适合后续扩展语义能力

## 9. 常见问题

### 9.1 `claude` 命令找不到

原因：

- 刚安装完成，当前终端还没刷新 PATH

解决：

- 重开终端
- 或使用绝对路径执行 `claude.exe`

### 9.2 `claude-status` 显示未登录

原因：

- 没有完成官方登录
- 或中转 token / base_url 配置失效

解决：

- 检查 `~/.claude/settings.json`
- 检查中转 token 是否可用
- 重新执行 `claude auth status`

### 9.3 `ask-claude` 报编码错误

本项目已经在 `claude_client.py` 中强制使用：

- `encoding="utf-8"`
- `errors="ignore"`

如果仍出问题，优先检查 Claude Code 输出是否被其他壳层工具二次处理。

### 9.4 返回格式不稳定

项目已经通过 prompt 限制 Claude Code：

- 只输出 JSON
- 禁止输出解释
- 对危险请求统一返回固定错误格式

如果需要更强约束，可以继续增强 prompt 模板或增加结构化校验。

### 9.5 `claude mcp add` 后工具不可见

优先检查：

- `llm-wiki-mcp --project-root ...` 是否能单独启动
- `claude mcp get llmwiki` 是否报错
- 当前 Python 环境里是否已安装 `mcp` 依赖

## 10. 推荐使用顺序

对于比赛和验收，建议固定按这个顺序执行：

1. `doctor`
2. `claude-status`
3. `index`
4. `answer-all-claude`
5. `validate`
6. `release`

这样更容易定位问题，也更方便留痕。
