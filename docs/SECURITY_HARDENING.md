# llm-wiki 安全加固说明

## 1. 安全边界服务于什么

当前安全设计服务于两层能力：

- Claude-native wiki 主流程
- 可调用的无状态 deterministic 工具层

## 2. 风险模型

重点防：

- 恶意 `raw/` source 污染 wiki
- prompt injection 篡改 maintainer 行为
- 越权读写
- 危险副作用执行
- 密码 / token / secret 索取

## 3. 防护结构

### 3.1 `Permission.json`

- deny 目录
- deny 命令
- deny 文件

### 3.2 `security.py`

负责：

- prompt injection 检测
- 危险副作用检测
- 敏感信息请求检测
- 间接执行诱导检测
- 路径和命令命中检测

### 3.3 工具层约束

辅助工具虽然保留，但不再有本地持久索引仓。

当前工具：

- `scan_documents`
- `search_related_paths`
- `get_document_record`
- `list_comments`
- `answer_question_local`
- `apply_fixes`
- `build_pivot_chart`
- `run_python_document`

都仍然受 `PermissionPolicy` 约束。

## 4. 当前状态

当前安全边界已经与本版本一致：

1. 主系统是 wiki
2. 工具层是无状态按需扫描
3. 两者共享统一权限与注入防护

测试状态：

```text
14 passed
```
