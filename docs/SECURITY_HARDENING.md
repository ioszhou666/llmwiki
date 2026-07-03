# llm-wiki 安全加固说明

## 1. 当前安全边界服务于什么

当前安全设计服务于 Claude-native wiki 主流程：

- 防恶意 raw source 污染 wiki
- 防 prompt injection 篡改 maintainer 行为
- 防越权读取
- 防危险副作用

## 2. 风险模型

当前重点防以下问题：

- 覆盖规则型 prompt injection
- 写文件、删文件、杀进程等副作用
- 读取 deny 目录或 deny 文件
- 索取密码、token、secret
- 诱导 Claude 按文档内容直接执行系统动作

## 3. 当前防护结构

### 3.1 `Permission.json`

定义：

- deny 目录
- deny 命令
- deny 文件

### 3.2 `security.py`

拦截：

- prompt injection
- 危险副作用
- 敏感信息读取
- 间接执行

### 3.3 结果级过滤

当前不只拦入口，也拦结果输出。

### 3.4 wiki maintainer 约束

`AGENTS.md` 和 `CLAUDE.md` 同时承担安全边界角色：

- `raw/` 不可修改
- Claude 负责维护 wiki，不负责执行系统动作

## 4. 当前状态

当前版本下，wiki 主流程和安全边界可以一起工作，没有因为本次删除旧搜索/答题器代码而回退。

测试状态：

```text
12 passed
```
