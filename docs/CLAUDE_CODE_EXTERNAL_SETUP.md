# 在其他 Claude Code 环境中接入 llm-wiki

## 1. 目标

这份文档说明如何在另一台机器、另一个仓库、或另一个 Claude Code 环境中，把 `llm-wiki` 作为 wiki 工作底座接入并运行。

适用场景：

- 你已经有一个项目仓库，想让 Claude Code 维护项目 wiki
- 你想把 `llm-wiki` 当作通用知识整理工作流
- 你想通过 MCP 把 wiki 和辅助 tools 暴露给 Claude Code

## 2. 你需要的前提

目标环境至少需要：

- Python 3.11+
- Claude Code 可用
- 可以执行 `python -m ...`
- 可以在目标目录下创建 `raw/`、`wiki/`、`cache/`、`.claude/`

如果你要用 Office / 图表 / 修复类辅助 tools，建议额外有：

- `openpyxl`
- `pandas`
- `matplotlib`
- 可选的 `LibreOffice` 或 `Tika` 兜底环境

## 3. 获取项目

### 3.1 直接克隆仓库

```powershell
git clone https://github.com/ioszhou666/llmwiki.git
cd llmwiki
python -m pip install -e .
```

### 3.2 或作为已有项目中的工具仓使用

也可以把这个仓库放在任意目录，只要后面 `--project-root` 指向你的目标 wiki 工作区即可。

## 4. 准备目标 wiki 工作区

假设你的目标工作区是：

```text
D:\work\my-wiki-project
```

先初始化：

```powershell
llm-wiki --project-root D:\work\my-wiki-project init-wiki
```

初始化后会得到：

- `raw/`
- `wiki/`
- `cache/extracted/`
- `.claude/commands/`
- `AGENTS.md`
- `CLAUDE.md`
- `Permission.json`

## 5. 应该把什么放进 `raw/`

`raw/` 只放原始证据，不放 Claude 整理后的知识页。

建议放：

- 项目需求文档
- 架构说明
- runbook
- 会议纪要
- 环境说明
- Office 文档转存件
- Markdown / XML / HTML / 代码说明文件

不建议放：

- Claude 已整理好的总结页
- 需要被频繁人工编辑的 wiki page

## 6. 第一次运行顺序

推荐顺序：

### 6.1 先做本地 ingest

```powershell
llm-wiki --project-root D:\work\my-wiki-project ingest
```

### 6.2 查看 staged workflow

```powershell
llm-wiki --project-root D:\work\my-wiki-project print-ingest-workflow
```

### 6.3 让 Claude Code 接手维护

Claude Code 进入项目后，建议先读：

- `AGENTS.md`
- `CLAUDE.md`
- `wiki/index.md`
- `wiki/log.md`
- `cache/extracted/`
- `raw/`

然后按 workflow 做：

1. `source-curation`
2. `concept-and-entity-synthesis`
3. `index-and-log-finalize`

## 7. 在 Claude Code 中注册 MCP

如果你希望 Claude Code 直接调用 wiki 资源和辅助 tools，可以注册 MCP：

```powershell
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\work\my-wiki-project
```

注册后，Claude 可以直接读取这些资源：

- `wiki://status`
- `wiki://curation-status`
- `wiki://claude-playbook`
- `wiki://permission-policy`
- `wiki://security-summary`

也可以调用这些主工具：

- `ingest_wiki_local`
- `query_wiki_local`
- `lint_wiki`
- `get_ingest_prompt`
- `get_ingest_workflow`
- `get_query_prompt`

## 8. Claude 在这个体系里应该如何工作

正确工作方式：

- 把 `wiki/` 当作长期维护对象
- 把 `raw/` 当作证据层
- 优先整理 page，而不是临时回答一次问题
- 通过 `index.md`、`overview/`、`log.md` 维持可导航性

不正确工作方式：

- 直接把 `raw/` 当最终知识页
- 跳过 wiki，直接做一次性文件问答
- 修改 `raw/` 来伪造整理结果

## 9. 辅助 tools 在其他 Claude Code 环境中的用法

这部分 tools 不是主系统，只是 wiki 可调用辅助能力。

当前是无状态模式：

- 每次调用时扫描 `docs/`
- 在内存中临时组织文档视图
- 不落本地数据库
- 不建立持久索引

可用 tools：

- `scan_documents`
- `list_document_paths`
- `count_files_by_extension`
- `count_supported_extensions`
- `search_related_paths`
- `find_paths_by_basename`
- `get_document_record`
- `list_comments`
- `answer_question_local`
- `apply_fixes`
- `build_pivot_chart`
- `run_python_document`

建议把它们理解成：

- `wiki/` 负责长期知识维护
- `docs/` tools 负责临时结构化辅助操作

## 10. 推荐目录约定

如果你在其他项目里接入，建议用下面的目录习惯：

```text
your-project/
├─ raw/
├─ wiki/
├─ cache/
├─ docs/
├─ AGENTS.md
├─ CLAUDE.md
└─ Permission.json
```

其中：

- `raw/` 放证据
- `wiki/` 放 Claude 维护结果
- `docs/` 只给辅助 tools 使用

## 11. 日常使用建议

日常运行建议：

1. 新资料进入 `raw/`
2. 执行 `ingest`
3. 让 Claude 做 staged curation
4. 执行 `lint-wiki`
5. 用 `query-wiki` 或 `query-wiki-claude` 检查结果

如果要做临时文档辅助分析：

1. 把文件放进 `docs/`
2. 调用 `scan_documents`
3. 再调用 `search_related_paths` / `list_comments` / `get_document_record` 等工具

## 12. 最短可用命令集

```powershell
python -m pip install -e .
llm-wiki --project-root D:\work\my-wiki-project init-wiki
llm-wiki --project-root D:\work\my-wiki-project ingest
llm-wiki --project-root D:\work\my-wiki-project print-ingest-workflow
claude mcp add llmwiki -- python -m llm_wiki.mcp_server --project-root D:\work\my-wiki-project
```

## 13. 一句话结论

在其他 Claude Code 环境里，`llm-wiki` 的正确接入方式是：

> 让 Claude Code 持续维护 `wiki/`，并在需要时调用无状态辅助 tools，而不是把它当作本地检索问答器。
