# llm-wiki

`llm-wiki` 是一个本地可运行的文档 Wiki 工作台，面向赛题里要求的多格式检索、批注治理、安全问答和批量答案生成。

## 已实现能力

- 多格式抽取：`doc/docx/ppt/pptx/xls/xlsx/xml/java/py/html/md/js`
- 批注治理：Office 批注、代码 TODO、按责任人和日期筛选
- 修复输出：文本、`docx`、`xlsx`、`pptx` 的确定性修复
- 批量答题：生成 `output/group-X-answer.md`
- 单题问答：直接回答一条自然语言问题
- 安全防护：`Permission.json`、危险命令、密码类问题、Prompt 注入拦截
- 审计日志：输出 `output/audit.jsonl`

## 目录约定

工作区根目录默认包含：

```text
workspace/
├─ docs/
├─ question/
├─ output/
└─ Permission.json
```

## 常用命令

```powershell
python -m pip install -e .
llm-wiki --project-root D:\llmwiki\demo_workspace index
llm-wiki --project-root D:\llmwiki\demo_workspace answer --group group-1.md
llm-wiki --project-root D:\llmwiki\demo_workspace answer-all
llm-wiki --project-root D:\llmwiki\demo_workspace ask --question "待张三处理的批注"
llm-wiki --project-root D:\llmwiki\demo_workspace doctor
llm-wiki --project-root D:\llmwiki\demo_workspace validate
llm-wiki --project-root D:\llmwiki\demo_workspace release --target D:\llmwiki\deliverables
llm-wiki --project-root D:\llmwiki\demo_workspace bootstrap-demo --target D:\llmwiki\demo_workspace
```

## 说明

- `index`：建立或重建 SQLite 索引
- `answer`：回答单个 `group-x.md`
- `answer-all`：批量回答全部 `group-*.md`
- `ask`：直接回答一条自然语言问题
- `doctor`：检查运行时、可选依赖和索引能力
- `validate`：执行索引、批量答题、修复产物与审计日志的端到端验收
- `release`：生成包含调研文档、系统设计、验证报告和示例输出的交付包
- `bootstrap-demo`：快速生成一套演示工作区

## 持续集成

- 仓库内置 GitHub Actions，会在推送后自动执行 `pytest`
- 本地建议在提交前运行 `python -m pytest tests -q`

## 文档

- 开源调研见 `docs/OPEN_SOURCE_RESEARCH.md`
- 系统设计见 `docs/SYSTEM_DESIGN.md`

## 当前边界

- `doc/ppt/xls` 优先尝试 `LibreOffice` 转换，再回退到 `Tika` 文本提取，最后才是 plain fallback
- “自由批注修复”当前以确定性规则为主，例如“把 A 改成 B”“补充 XXX 字段”
- 受控执行目前只开放了 Python 文件，并通过 AST 做安全检查
