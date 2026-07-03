# llm-wiki 安全加固说明

## 1. 当前安全边界服务于什么

当前安全设计服务两部分：

1. Claude-native wiki 主流程
2. 赛题兼容工具层

主流程中最重要的不是防“答错一个问题”，而是防：

- 恶意 raw source 污染 wiki
- prompt injection 篡改 maintainer 行为
- 越权读取
- 危险副作用

## 2. 风险模型

当前重点防以下问题：

- 覆盖规则型 prompt injection
- 写文件、删文件、杀进程等副作用
- 读取 deny 目录或 deny 文件
- 索取密码、token、secret
- 诱导 Claude 按文档内容直接执行系统动作

## 3. 当前防护结构

### 3.1 `Permission.json`

用于定义：

- deny 目录
- deny 命令
- deny 文件

### 3.2 `security.py`

用于拦截：

- prompt injection
- 危险副作用
- 敏感信息读取
- 间接执行

### 3.3 结果级过滤

当前不是只拦入口，也拦结果输出：

- deny 路径不会出现在结果里
- deny 文件不会出现在记录里
- deny 评论不会被列出

### 3.4 wiki maintainer 约束

`AGENTS.md` 和 `CLAUDE.md` 的意义不仅是组织工作流，也是在定义安全边界：

- `raw/` 不可修改
- summary / concept / entity / synthesis 边界明确
- Claude 的职责是维护 wiki，不是执行系统动作

## 4. 与当前版本结构的关系

这次结构修正后，安全边界也要跟着调整理解：

- 以前更多是在保护本地问答链路
- 现在同样是在保护 `raw -> wiki` 的 curation 链路

因此安全目标已经从“防问答越权”升级为“防 wiki 污染和副作用执行”。

## 5. 当前状态

当前版本下：

- wiki 主流程仍可运行
- 兼容层工具链仍可运行
- 安全边界没有因为目录重构和 staged workflow 调整而退化

测试状态：

```text
30 passed
```
