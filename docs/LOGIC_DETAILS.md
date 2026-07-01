# llm-wiki 当前逻辑详细说明

## 1. 总体定位

当前版本的 `llm-wiki` 不是单一形态的程序，而是 3 种使用模式共存：

1. 本地 deterministic 模式
   - 直接用规则和本地索引回答问题
   - 入口：`ask` / `answer` / `answer-all`
2. Claude Code 混合模式
   - 先用本地模块做安全检查和上下文抽取
   - 再交给 Claude Code 生成最终 JSON 结果
   - 入口：`ask-claude` / `answer-claude` / `answer-all-claude`
3. MCP Server 模式
   - 把本项目暴露成 Claude Code 可直接调用的资源和工具服务器
   - 入口：`llm-wiki-mcp`

可以把它理解成：

- 本地模块：负责“结构化、可控、可复现”
- Claude Code：负责“理解问题、综合上下文、生成答案”
- MCP：负责“把本项目嵌入 Claude 的标准工具体系”

## 2. 目录与运行对象

默认工作区结构如下：

```text
workspace/
├─ docs/
├─ question/
├─ output/
└─ Permission.json
```

各目录含义：

- `docs/`
  - 存原始文档
  - 包括 `doc/docx/ppt/pptx/xls/xlsx/xml/java/py/html/md/js`
- `question/`
  - 存 `group-*.md`
  - 每个文件本质上是一个 JSON 数组
- `output/`
  - 存答案文件、索引数据库、审计日志、修复产物
- `Permission.json`
  - 存高危目录、命令、文件的 deny 策略

## 3. 模块分工

### 3.1 `extractors.py`

职责：

- 识别文档类型
- 读取正文内容
- 抽取 Office 批注
- 抽取代码 TODO / 注释
- 为索引阶段提供标准化输出

当前实现方式：

- `docx`
  - 解压 OOXML
  - 读取 `word/document.xml`
  - 读取 `word/comments.xml`
- `pptx`
  - 解压 OOXML
  - 读取 `ppt/slides/*.xml`
  - 读取 `ppt/comments/*.xml`
- `xlsx`
  - 使用 `openpyxl`
  - 读取单元格值和 `cell.comment`
- `xml/java/py/html/md/js`
  - 走文本读取
  - 再用规则抽取 TODO 和块注释
- `doc/ppt/xls`
  - 先尝试 `LibreOffice` 转换
  - 再尝试 `Tika`
  - 最后退回 plain text

### 3.2 `indexer.py`

职责：

- 建立本地 SQLite 库
- 建立文档表、批注表、FTS 虚表
- 提供检索能力

当前表结构：

- `documents`
  - 存路径、扩展名、正文、元数据
- `comments`
  - 存批注文本、责任人、截止日期、作者、定位等
- `docs_fts`
  - 文档正文全文索引
- `comments_fts`
  - 批注全文索引

当前检索能力：

- 按扩展名计数
- 按 basename 找路径
- 按关键词全文查文档
- 按关键词查批注
- 合并文档和批注结果做“related paths”

### 3.3 `question_parser.py`

职责：

- 把自然语言问题映射成内部固定题型

当前主要题型包括：

- `count_extension`
- `count_supported_extensions`
- `list_extension_paths`
- `find_path`
- `comment_count`
- `assignee_comments`
- `date_comments`
- `global_assignee_comments`
- `global_assignee_comment_count`
- `global_date_comments`
- `global_date_comment_count`
- `business_search`
- `command_lookup`
- `run_document`
- `run_document_by_keyword`
- `pivot_chart`
- `pivot_chart_by_keyword`
- `fix_document`

它做的事情不是“理解完整语义世界”，而是把比赛题目先压缩到有限的规则集合里。

### 3.4 `security.py`

职责：

- 在任何回答或执行之前做统一风险检查

当前检查点：

- 高危命令关键词
  - 如 `rm -rf`、`remove-item`
- Prompt 注入关键词
  - 如“忽略前面所有规则”“god mode”
- 敏感口令问题
  - 如密码、token、secret
- `Permission.json` 黑名单
  - 目录 deny
  - 命令 deny
  - 文件 deny

输出策略：

- 一旦命中风险，统一返回：

```json
{"error_msg":"高危命令，拒绝访问"}
```

### 3.5 `answerer.py`

职责：

- 统一调度本地回答、Claude 回答、修复、图表、执行和审计

它是当前项目的核心调度层。

### 3.6 `claude_client.py`

职责：

- 封装 `Claude Code CLI`
- 检查可执行文件
- 查询登录状态
- 发送 prompt 并解析 JSON 包装结果

### 3.7 `mcp_runtime.py`

职责：

- 把已有的本地能力整理成 MCP 可调用的运行时接口

它本身不和 Claude 聊天，只暴露工具操作：

- 索引
- 查文档
- 查批注
- 本地答题
- 修复
- 画图
- 执行

### 3.8 `mcp_server.py`

职责：

- 用官方 `mcp` Python SDK 启动标准 `FastMCP` 服务器

对外暴露：

- resources
- tools

## 4. 本地 deterministic 问答流程

入口命令：

```powershell
llm-wiki --project-root <root> ask --question "..."
```

流程如下：

1. CLI 解析命令
2. 加载项目根目录
3. 打开 SQLite 索引
4. 如果需要则先重建索引
5. `question_parser` 识别题型
6. `security` 做风险检查
7. `answerer` 根据题型走本地逻辑
8. 返回 JSON 结果
9. 记录审计日志到 `output/audit.jsonl`

这一模式的优点：

- 稳定
- 可预测
- 测试容易
- 不依赖模型输出波动

## 5. Claude Code 混合问答流程

入口命令：

```powershell
llm-wiki --project-root <root> ask-claude --question "..."
```

流程如下：

1. CLI 解析命令
2. 加载本地索引和权限策略
3. `question_parser` 先把问题归类
4. `security` 先拦截高危请求
5. `answerer` 构造 Claude 上下文
6. `claude_client` 执行：

```powershell
claude -p "<prompt>" --output-format json --tools ""
```

7. Claude Code 输出一个 JSON 包装对象
8. 项目读取其中的 `result`
9. 再把 `result` 解析成最终答案 JSON

这里最重要的一点是：

- Claude 不是直接“看整个仓库”
- 而是先由本地索引选出相关路径、内容摘要和批注
- 再把这些上下文交给 Claude 生成答案

也就是说，它是“本地检索 + Claude 综合”，不是完全裸问。

## 6. Claude 提示词构造逻辑

在 `answerer.py` 里，给 Claude 的 prompt 大致包括：

- 角色说明
- 只能输出 JSON
- 危险请求必须返回固定错误格式
- 问题类型
- 用户问题
- 本地检索到的上下文

上下文内容通常包括：

- `candidate_paths`
- `related_paths`
- `snippets`
  - 文档内容预览
  - 批注列表

这样做的目标是：

- 尽量减少模型幻觉
- 保持答案格式固定
- 保留本地安全控制权

## 7. 文档修复流程

入口：

- 本地答题中的 `fix_document`
- 或 MCP 工具 `apply_fixes`

流程：

1. 先取目标文档的批注列表
2. 从批注文本里抽取修复动作
3. 当前只支持确定性规则：
   - 把 A 改成 B
   - 补充 XXX 字段
4. 按文档类型执行修复：
   - 文本类：直接替换字符串
   - `docx`：改 `document.xml`
   - `xlsx`：改单元格值 / 增加字段列
   - `pptx`：改 slide xml
5. 结果写入 `output/fixed/`
6. 再额外生成 `.fix-report.md`

## 8. Python 受控执行流程

入口：

- 本地问题类型 `run_document`
- MCP 工具 `run_python_document`

流程：

1. 找到目标 Python 文件
2. 读取源码
3. 用 AST 检查高风险操作
   - 禁止危险 import
   - 禁止 `open/exec/eval`
4. 通过后才运行 `subprocess`
5. 收集 stdout/stderr
6. 写审计日志

当前只开放 Python，Java/JS 还没有做沙箱执行。

## 9. Excel 图表流程

入口：

- 本地问题类型 `pivot_chart`
- MCP 工具 `build_pivot_chart`

流程：

1. 用 `pandas.read_excel` 读取 Excel
2. 自动找一个类别列
3. 自动找一个数值列
4. 构造 `pivot_table`
5. 用 `matplotlib` 生成柱状图
6. 输出到 `output/*.png`

## 10. MCP Server 逻辑

入口命令：

```powershell
llm-wiki-mcp --project-root <root>
```

当前传输方式：

- `stdio`

### 10.1 resources

目前暴露：

- `wiki://status`
  - 项目概览、文档路径、题组、权限策略快照
- `wiki://permission-policy`
  - 当前权限配置

### 10.2 tools

目前暴露：

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

注意：

- 现在 MCP 工具暴露的是“本地 deterministic 能力”
- 不是在 MCP 里再去反调 Claude Code
- 这样避免 Claude 调 MCP，MCP 再调 Claude，形成递归复杂性

## 11. 为什么同时保留 CLI、Claude、MCP 三种入口

因为三种入口对应的目标不同：

### 11.1 CLI

适合：

- 本地开发
- 回归测试
- 批处理

### 11.2 Claude 混合入口

适合：

- 贴近赛题“依赖 Claude Code”的要求
- 利用模型做更强的问题理解

### 11.3 MCP

适合：

- 让 Claude Code 直接把本项目当作外部工具服务器
- 后续扩展成更标准的 Agent 工具链

## 12. 当前限制

当前逻辑还有这些边界：

1. Claude 提示词仍是规则化 prompt，不是更复杂的多轮 agent workflow
2. 文档修复仍以确定性替换为主，不是自由语义编辑
3. MCP 暴露的还是本地工具层，Claude 主导逻辑主要在 `ask-claude` / `answer-claude`
4. 老 Office 格式增强效果依赖 `LibreOffice` / `Tika`
5. 向量检索还没有接入，当前还是 FTS 为主

## 13. 当前最推荐的使用方式

如果是比赛或答辩演示，我建议按这个顺序展示：

1. `doctor`
2. `claude-status`
3. `ask-claude`
4. `answer-all-claude`
5. `claude mcp list`
6. 说明 `llmwiki` MCP 已连接
7. 展示 `release` 产物目录

这样能最完整地说明：

- 本地能力已经实现
- Claude Code 已接入
- MCP 也已标准化接入
- 项目既能跑，也能展示系统化架构
