# llm-wiki 系统设计

## 分层架构

当前版本采用“Claude Code 主执行体 + 本地工具层”的混合架构。

1. 抽取层
   - 负责识别文档类型
   - 提取正文、批注、TODO、元数据
2. 索引层
   - 持久化到 SQLite
   - 建立 `documents/comments` 和 FTS 索引
3. Claude 交互层
   - 通过 Claude Code 进行问题理解、上下文综合和最终答案生成
   - 当前机器允许通过 Anthropic 兼容中转接口运行 Claude Code
4. 执行层
   - 本地检索、修复、代码执行、图表生成
5. 安全层
   - 统一做高危请求拦截和权限控制
6. 审计层
   - 记录答题、执行、修复事件

## 关键流程

### 入库流程

`docs/*` -> 文档抽取 -> 标准化记录 -> SQLite/FTS

### 问答流程

问题文本 -> 本地题型解析/安全检查 -> 本地索引抽取上下文 -> Claude Code 生成答案 -> JSON 输出

### 修复流程

批注文本 -> 修复动作提取 -> 确定性替换/补字段 -> 输出到 `output/fixed`

## 模块划分

| 文件 | 职责 |
|---|---|
| `extractors.py` | 多格式抽取与批注解析 |
| `indexer.py` | 索引和检索 |
| `question_parser.py` | 题型识别 |
| `claude_client.py` | Claude Code CLI 封装 |
| `security.py` | 风险拦截 |
| `answerer.py` | 统一执行引擎 |
| `reporting.py` | 报告和发布包生成 |
| `cli.py` | 命令行入口 |

## 当前边界

- 自由语义修文仍以规则修复为主
- 受控执行目前只开放 Python
- 语义召回以 FTS 为主，后续可增强向量检索
