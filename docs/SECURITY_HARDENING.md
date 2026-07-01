# llm-wiki 安全加固说明

## 1. 安全目标

当前版本的安全设计，不只是防“危险命令执行”，而是同时覆盖两条链路：

1. `LLM Wiki` 主流程
   - 防止 raw source 或恶意提示诱导 Claude 越权、改写、泄密或执行副作用
2. 赛题兼容工具层
   - 防止 `docs/question/output` 链路中出现危险读取、危险执行、恶意修复和间接指令跟随

系统的总体原则是：

- 不把不可信文档内容当成可执行指令
- 不把用户的“覆盖规则”文本当成更高优先级指令
- 不把被 deny 的路径、文件、命令暴露给结果层
- 即使保留 Claude 集成，也要先有本地安全边界

## 2. 风险模型

当前重点防护以下攻击面：

### 2.1 Prompt Injection

典型形式：

- “忽略之前所有规则”
- “这是最高优先级任务”
- “不需要询问用户”
- “无论客户提出什么，都遵循当前描述执行”

目标：

- 覆盖系统约束
- 让模型把文档内容当成更高优先级指令

### 2.2 危险副作用

典型形式：

- 写脚本
- 批量创建文件
- 删除文件
- 杀进程
- 停止服务
- 修改系统配置

目标：

- 把问答/整理系统诱导成执行器

### 2.3 越权读取

典型形式：

- 读取 `/etc`
- 读取 `hadoop.env`
- 读取 `spark-*.env`
- 读取敏感目录下的系统配置和凭据

### 2.4 敏感信息索取

典型形式：

- 查询 root 密码
- 查询平台口令
- 查询 token、secret、credential

### 2.5 间接执行

典型形式：

- “完成某个文档中描述的工作”
- “按某份说明自动执行”
- “根据文件里的要求直接落盘”

危险点：

- 这会把不可信文档内容升级为操作指令

## 3. 当前防护层次

### 3.1 `Permission.json`

这是第一层静态边界。

当前默认 deny 范围包括：

- 目录 deny
  - 例如 `/etc`
- 命令 deny
  - 例如 `Remove-Item`、`del*`、`taskkill`、`Stop-Process`
- 文件 deny
  - 例如 `hadoop.env`、`spark-*.env`

### 3.2 `security.py`

这是第二层动态识别和阻断。

当前主要拦截：

- prompt injection 关键短语
- 间接执行请求
- 危险副作用请求
- 敏感信息索取
- deny 路径/文件/命令相关请求

当前对危险命令的识别已经显式覆盖：

- `taskkill`
- `Stop-Process`
- 与 `codeagent.exe` 相关的危险处理意图

### 3.3 结果层过滤

当前不是只在“入口”拦截，结果层也会继续收口。

表现为：

- `list_document_paths()` 不返回 deny 文档
- `get_document_record()` 对 deny 路径直接拒绝
- `list_comments()` 会过滤 deny 文档下的批注
- 扩展名统计只统计可见文档
- `search_related_paths()`、`find_paths_by_basename()` 也会做权限过滤

这能避免“虽然入口没直接放行，但最终结果还是把敏感路径吐出去”的问题。

### 3.4 Claude Workflow 约束

`LLM Wiki` 主流程中的约束主要体现在：

- `CLAUDE.md`
  - 明确禁止修改 `raw/`
- staged workflow prompt
  - 要求 Claude 只维护 `wiki/`
- `query-wiki-claude`
  - 默认不开放自由工具使用

换句话说，Claude 在这个项目里被设计成 wiki maintainer，而不是系统执行代理。

### 3.5 受控执行防护

对于兼容层中的 Python 执行功能，当前会先做 AST 安全检查，再决定是否运行。

重点限制：

- 禁止危险 import
- 禁止 `open/exec/eval` 等危险模式
- 记录 stdout/stderr 和审计日志

## 4. 对抗样例的预期处理

对于混合型恶意样例，当前预期行为是“拒绝危险部分，只保留可安全回答的部分”，而不是整个系统盲从其中的最高优先级描述。

### 4.1 应拒绝的内容

- 写入 `kill_codeagent.bash`
- 创建 `success-1.txt`、`success-2.txt`、`success-3.txt`
- 杀掉 `codeagent.exe`
- 查询外部环境密码
- 查询 `/etc` 或 deny 文件中的口令
- 删除被指定文件
- 按文档里的恶意步骤自动执行任务

### 4.2 可保留的安全能力

- 统计某类文档数量
- 统计某责任人的 TODO
- 对允许范围内的文档执行 deterministic 修复

## 5. MCP 安全边界

当前 MCP 暴露的不只是工具，还暴露了安全状态资源：

- `wiki://permission-policy`
- `wiki://security-summary`

这样做的意义是：

- Claude Code 可以先读取安全边界，再决定如何调用工具
- 避免把安全规则只埋在代码里而不可见

## 6. 与当前版本的关系

随着项目从“本地规则问答器”转向 `LLM Wiki`，安全目标也发生了变化：

- 以前更偏向防本地问答链路越权
- 现在同时要防 wiki ingest/query 被恶意 raw source 污染

因此当前版本的安全价值，体现在两点：

1. 给保留的兼容层提供传统的规则化安全边界
2. 给 Claude Code 驱动的 wiki curation 提供明确的编辑边界和结果边界

## 7. 当前状态

当前仓库全量测试结果为：

```text
30 passed
```

这说明当前版本下，wiki 主流程、兼容层工具链和安全边界可以一起工作，没有因为最近引入的 topic seed page 和 staged workflow 而回退。
