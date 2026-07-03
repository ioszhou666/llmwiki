# llm-wiki 安全加固说明

## 1. 安全边界服务于什么

当前安全设计服务于两层能力：

- Claude-native wiki 主流程
- 可选的 deterministic 辅助工具层

目标是防止：

- 恶意 `raw/` source 污染 wiki
- prompt injection 篡改 maintainer 行为
- 越权读写
- 危险副作用执行

## 2. 风险模型

当前重点防以下问题：

- 覆盖规则型 prompt injection
- 写文件、删文件、杀进程等危险副作用
- 读取 deny 目录或 deny 文件
- 索取密码、token、secret
- 诱导 Claude 按文档内文本直接执行系统动作

## 3. 防护结构

### 3.1 `Permission.json`

定义三类策略：

- deny 目录
- deny 命令
- deny 文件

### 3.2 `security.py`

负责检测：

- prompt injection
- 危险副作用意图
- 敏感信息请求
- 间接执行诱导
- 命令黑名单命中
- 路径黑名单命中

### 3.3 结果级过滤

不只拦输入，也拦结果输出：

- 命中 deny 路径的文档不会被列出
- 命中 deny 文件的记录不会返回
- 非允许目录下的 secret 请求会被拒绝

### 3.4 maintainer 约束

`AGENTS.md` 和 `CLAUDE.md` 同时承担行为边界：

- `raw/` 不可被 Claude 修改
- Claude 负责维护 wiki，而不是执行系统破坏动作

## 4. 当前与辅助工具层的关系

旧式工具虽然被降级为 auxiliary tools，但安全要求没有放松。

当前：

- `index_documents`
- `search_related_paths`
- `get_document_record`
- `list_comments`
- `answer_question_local`
- `apply_fixes`
- `build_pivot_chart`
- `run_python_document`

都仍受同一套 `PermissionPolicy` 约束。

## 5. 当前状态

安全边界已经与当前版本架构一致：

1. 主系统是 wiki
2. 工具层是可选辅助
3. 两者共享统一权限和注入防护

测试状态：

```text
14 passed
```
