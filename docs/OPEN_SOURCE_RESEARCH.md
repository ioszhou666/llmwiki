# llm-wiki 开源方案调研

## 1. 调研结论

本项目不能按本地检索问答器方向实现。更合理的路线是：

- 以 Karpathy 的 `LLM Wiki` 理念为主
- 参考 Claude-native wiki 实现方式
- 结合赛题中的 Office、TODO、批注修复、安全对抗要求做适配

因此主系统应当是：

- `raw/` 作为证据层
- `wiki/` 作为长期维护的知识层
- `Claude Code` 作为主要维护者
- 本地 Python 作为 deterministic 支撑层

## 2. Karpathy 定义带来的约束

重点不是单次问答，而是：

1. 把资料整理成 page
2. 让模型维护 page
3. 让知识持续演化

## 3. 开源实现的共同特征

稳定共性包括：

1. 目录按 page 类型分层
2. 模型直接维护 repo 中的 markdown
3. 有仓库级规则文件
4. 有面向 Claude Code 的命令入口
5. 原始资料与知识页严格分层

## 4. 本地代码应做什么

本地代码应该负责：

- 文档抽取
- TODO / comment 抽取
- deterministic packet 生成
- 安全边界
- Claude workflow scaffolding

当前保留的技术方向包括：

- OOXML 直接读取
- LibreOffice / Tika 兜底
- pandas / matplotlib
- Permission deny + prompt injection 防护

但不再包括持久化检索仓方案。

## 5. 与题目的结合方式

- Office 文档
  - 作为 `raw/` 或辅助 `docs/` 输入源
- 批注 / TODO
  - 进入 extracted packet、summary page、或临时 comment 视图
- 修复任务
  - 保留为 deterministic 辅助工具
- 安全对抗样例
  - 进入统一安全边界设计

## 6. 当前落地结果

当前版本已经落地为：

- Claude-native wiki 主架构
- `AGENTS.md` + `CLAUDE.md`
- `.claude/commands`
- summary / concept / entity seed 体系
- staged Claude workflow
- MCP 接入
- 无状态 deterministic tool layer

## 7. 参考资料

- Karpathy LLM Wiki 说明
  - [gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- Unstructured supported file types
  - [docs](https://docs.unstructured.io/open-source/introduction/supported-file-types)
- Apache Tika supported formats
  - [docs](https://tika.apache.org/2.9.2/formats.html)
- LibreOffice start parameters
  - [docs](https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html)
- python-docx comments analysis
  - [docs](https://python-docx.readthedocs.io/en/latest/dev/analysis/features/comments.html)
- openpyxl comments
  - [docs](https://openpyxl.readthedocs.io/en/stable/comments.html)
- pandas pivot_table
  - [docs](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot_table.html)
- OWASP LLM Prompt Injection Prevention Cheat Sheet
  - [docs](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
