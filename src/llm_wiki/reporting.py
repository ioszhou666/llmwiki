from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path
from typing import Any


def render_open_source_research(report_date: date | None = None) -> str:
    report_date = report_date or date.today()
    return f"""# llm-wiki 开源方案调研

调研日期：{report_date.isoformat()}

## 目标拆解

本项目要同时解决 4 类问题：

1. 多格式文档抽取：覆盖 `doc/docx/ppt/pptx/xls/xlsx/xml/java/py/html/md/js`
2. 批注与 TODO 治理：抽取、筛选、统计、修复
3. 本地知识检索与问答：文件数量、路径、业务相关、命令说明
4. 安全执行与防护：拦截高危命令、敏感信息、Prompt 注入

## 开源方案调研结论

### 1. 文档抽取

- `docx/pptx/xlsx` 优先采用原生 OOXML 解析。
  - 原因：批注结构直接保存在 XML 部件里，最适合做责任人、日期和修复映射。
- `doc/ppt/xls` 采用“LibreOffice 转换优先，Apache Tika 兜底”的回退链路。
  - 原因：老 Office 格式结构不统一，直接精确抽取批注成本较高。

### 2. 批注治理

- `xlsx` 采用 `openpyxl` 读取单元格批注并回写修复结果。
- `docx/pptx` 采用 zip + XML 方式读取注释部件并做确定性替换。
- 代码与文本文件采用正则规则抽取结构化 TODO 和自由批注。

### 3. 索引检索

- 选型 `SQLite FTS5` 作为默认全文检索方案。
  - 原因：轻量、零服务依赖、适合 200+ 文档的本地索引场景。
- 没有默认引入 Elasticsearch / OpenSearch。
  - 原因：部署成本高，超过当前赛题的体量需求。

### 4. 安全防护

- 采用策略型防护而不是把文档内容直接喂给执行器。
- 关键防线包括：
  - `Permission.json` 黑名单
  - 高危命令和敏感口令问题拦截
  - Prompt 注入关键语句拦截
  - Python AST 安全检查和最小执行面

## 方案映射

| 赛题能力 | 当前实现 | 选型理由 |
|---|---|---|
| OOXML 批注抽取 | 原生 XML 解析 | 可直接拿到批注文本、作者、日期 |
| 老 Office 文档兼容 | LibreOffice + Tika 回退 | 提升兼容性，降低主链复杂度 |
| Excel 数据透视图 | `pandas` + `matplotlib` | 本地生成稳定、依赖成熟 |
| 全文检索 | SQLite FTS5 | 本地化、无外部服务 |
| 安全拦截 | 规则 + 权限策略 | 行为可解释，适合赛题验收 |

## 官方资料

- Unstructured 支持文件类型：
  - https://docs.unstructured.io/open-source/introduction/supported-file-types
- Apache Tika 支持的文档格式：
  - https://tika.apache.org/2.9.2/formats.html
- LibreOffice `--convert-to` 参数：
  - https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html
- python-docx 对 comments 结构的分析：
  - https://python-docx.readthedocs.io/en/latest/dev/analysis/features/comments.html
- openpyxl comments 文档：
  - https://openpyxl.readthedocs.io/en/stable/comments.html
- SQLite FTS5：
  - https://sqlite.org/fts5.html
- pandas pivot_table：
  - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot_table.html
- OWASP LLM Prompt Injection Prevention Cheat Sheet：
  - https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
"""


def render_system_design() -> str:
    return """# llm-wiki 系统设计

## 架构总览

1. 抽取层：按格式解析正文、批注、TODO、元数据
2. 索引层：写入 SQLite `documents/comments` 和 FTS 虚表
3. 路由层：把自然语言问题归类为固定题型
4. 执行层：检索、修复、受控运行、图表生成
5. 安全层：统一在执行前做风险判断
6. 审计层：把每次答题、修复、执行记录到 `audit.jsonl`

## 关键流程

### 文档入库

`docs/*` -> 格式识别 -> 内容/批注抽取 -> 标准化记录 -> SQLite / FTS

### 问题回答

问题文本 -> 题型解析 -> 安全检查 -> 检索/执行 -> JSON 格式化输出

### 批注修复

文档路径 -> 抽取批注动作 -> 确定性规则修复 -> 写入 `output/fixed`

## 模块对应

| 模块 | 职责 |
|---|---|
| `extractors.py` | 多格式内容和批注抽取 |
| `indexer.py` | SQLite/FTS 建表、索引、检索 |
| `question_parser.py` | 自然语言题型识别 |
| `security.py` | 高危请求和权限策略拦截 |
| `answerer.py` | 统一执行引擎 |
| `reporting.py` | 调研、设计、验证、发布包生成 |
| `cli.py` | `index/answer/answer-all/ask/doctor/validate/release` |

## 边界与扩展

- 当前对自由语义修文采用确定性规则优先，复杂重写可扩展到外部 LLM 编辑器
- 当前受控执行默认只开放 Python，Java/JS 可按同样模式扩展沙箱
- 当前检索以规则和 FTS 为主，后续可增补向量索引增强业务语义召回
"""


def render_validation_report(summary: dict[str, Any]) -> str:
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    return f"""# llm-wiki 验证报告

## 验证结论

- 状态：{summary.get("status", "unknown")}
- 索引文档数：{summary.get("indexed_documents", 0)}
- 题组数：{summary.get("question_groups", 0)}
- FTS5：{summary.get("sqlite_fts5")}

## 产物

- 答案文件：
{_render_markdown_list(summary.get("answer_outputs", []))}
- 修复文件：
{_render_markdown_list(summary.get("fixed_outputs", []))}
- 审计日志：`{summary.get("audit_log", "")}`

## 原始摘要

```json
{payload}
```
"""


def build_release_bundle(project_root: Path, summary: dict[str, Any], target_dir: Path) -> Path:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    demo_output_dir = target_dir / "demo_output"
    fixed_dir = target_dir / "fixed"
    demo_output_dir.mkdir(parents=True, exist_ok=True)
    fixed_dir.mkdir(parents=True, exist_ok=True)

    for answer_path in summary.get("answer_outputs", []):
        source = _resolve_output_path(project_root, answer_path)
        if source.exists():
            shutil.copy2(source, demo_output_dir / source.name)

    audit_path = _resolve_output_path(project_root, summary.get("audit_log", ""))
    if audit_path.exists():
        shutil.copy2(audit_path, demo_output_dir / audit_path.name)

    for fixed_path in summary.get("fixed_outputs", []):
        source = _resolve_output_path(project_root, fixed_path)
        if source.exists():
            shutil.copy2(source, fixed_dir / source.name)
        report_path = source.with_suffix(source.suffix + ".fix-report.md")
        if report_path.exists():
            shutil.copy2(report_path, fixed_dir / report_path.name)

    (target_dir / "OPEN_SOURCE_RESEARCH.md").write_text(render_open_source_research(), encoding="utf-8")
    (target_dir / "SYSTEM_DESIGN.md").write_text(render_system_design(), encoding="utf-8")
    (target_dir / "VALIDATION_REPORT.md").write_text(render_validation_report(summary), encoding="utf-8")
    (target_dir / "FINAL_STATUS.md").write_text(
        json.dumps(
            {
                "status": summary.get("status"),
                "indexed_documents": summary.get("indexed_documents"),
                "question_groups": summary.get("question_groups"),
                "release_dir": target_dir.as_posix(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return target_dir


def _resolve_output_path(project_root: Path, path_text: str) -> Path:
    if not path_text:
        return project_root / "__missing__"
    candidate = Path(path_text)
    return candidate if candidate.is_absolute() else project_root / candidate


def _render_markdown_list(items: list[str]) -> str:
    if not items:
        return "- 无"
    return "\n".join(f"- `{item}`" for item in items)
