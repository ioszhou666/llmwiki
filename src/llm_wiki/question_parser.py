from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .constants import SUPPORTED_EXTENSIONS


EXTENSION_PATTERN = "|".join(sorted(SUPPORTED_EXTENSIONS, key=len, reverse=True))
FILE_PATTERN = rf"([^\s]+\.(?:{EXTENSION_PATTERN}))"
DATE_PATTERN = r"(20\d{6})"
SECRET_PATTERN = r"(?:密码|密钥|secret|token|apikey|api key|credential|口令|数据库明文密码)"


@dataclass(slots=True)
class ParsedQuestion:
    title: str
    normalized_title: str
    kind: str
    basename: str | None = None
    candidate_paths: list[str] = field(default_factory=list)
    extension: str | None = None
    assignee: str | None = None
    keyword: str | None = None
    date_value: str | None = None


def normalize_question(text: str) -> str:
    normalized = text.strip()
    for source, target in (("：", ":"), ("，", ","), ("（", "("), ("）", ")"), ("\u3000", " ")):
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def resolve_candidate_paths(title: str, all_paths: list[str]) -> tuple[str | None, list[str]]:
    normalized_title = normalize_question(title)
    for rel_path in sorted(all_paths, key=len, reverse=True):
        basename = Path(rel_path).name
        if basename in normalized_title:
            return basename, [rel_path]
    filename = extract_filename(normalized_title)
    if not filename:
        return None, []
    matches = [path for path in all_paths if Path(path).name.casefold() == filename.casefold()]
    return filename, matches


def extract_filename(title: str) -> str | None:
    match = re.search(FILE_PATTERN, title, re.IGNORECASE)
    if not match:
        return None
    raw = match.group(1)
    for prefix in ("找出", "查询", "读取", "统计", "获取", "运行", "执行"):
        if raw.startswith(prefix) and "." in raw:
            remainder = raw[len(prefix) :]
            if re.search(rf"\.(?:{EXTENSION_PATTERN})$", remainder, re.IGNORECASE):
                return remainder
    return raw


def parse_question(title: str, all_paths: list[str]) -> ParsedQuestion:
    normalized_title = normalize_question(title)
    basename, candidate_paths = resolve_candidate_paths(normalized_title, all_paths)

    if match := re.search(rf"统计全项目\s+({EXTENSION_PATTERN})\s+总数量", normalized_title, re.IGNORECASE):
        return ParsedQuestion(title, normalized_title, "count_extension", extension=match.group(1).lower())

    if re.search(r"统计.*不同类型文件.*数量", normalized_title):
        return ParsedQuestion(title, normalized_title, "count_supported_extensions")

    if basename and re.search(SECRET_PATTERN, normalized_title, re.IGNORECASE):
        return ParsedQuestion(title, normalized_title, "file_secret_lookup", basename=basename, candidate_paths=candidate_paths)

    if basename and "路径" in normalized_title:
        return ParsedQuestion(title, normalized_title, "find_path", basename=basename, candidate_paths=candidate_paths)

    if basename and "统计批注数量" in normalized_title:
        return ParsedQuestion(title, normalized_title, "comment_count", basename=basename, candidate_paths=candidate_paths)

    if basename and (match := re.search(r"(?:待|由)(.+?)处理的批注", normalized_title)):
        return ParsedQuestion(
            title,
            normalized_title,
            "assignee_comments",
            basename=basename,
            candidate_paths=candidate_paths,
            assignee=match.group(1).strip(),
        )

    if basename and (match := re.search(rf"(?:截止|到期|end_date[:： ]*){DATE_PATTERN}", normalized_title)):
        date_value = re.search(DATE_PATTERN, match.group(0))
        return ParsedQuestion(
            title,
            normalized_title,
            "date_comments",
            basename=basename,
            candidate_paths=candidate_paths,
            date_value=date_value.group(1) if date_value else None,
        )

    if match := re.search(r"(?:待|由)(.+?)处理的批注", normalized_title):
        return ParsedQuestion(title, normalized_title, "global_assignee_comments", assignee=match.group(1).strip())

    if match := re.search(rf"(?:截止|到期|end_date[:： ]*){DATE_PATTERN}", normalized_title):
        date_value = re.search(DATE_PATTERN, match.group(0))
        return ParsedQuestion(
            title,
            normalized_title,
            "global_date_comments",
            date_value=date_value.group(1) if date_value else None,
        )

    if basename and any(token in normalized_title for token in ("批注修复", "TODO修复", "todo修复", "自由批注优化整理", "优化整理", "修复")):
        return ParsedQuestion(title, normalized_title, "fix_document", basename=basename, candidate_paths=candidate_paths)

    if basename and any(token in normalized_title for token in ("透视图", "图表")):
        return ParsedQuestion(title, normalized_title, "pivot_chart", basename=basename, candidate_paths=candidate_paths)

    if basename and any(token in normalized_title for token in ("执行结果", "运行结果")):
        return ParsedQuestion(title, normalized_title, "run_document", basename=basename, candidate_paths=candidate_paths)

    if any(token in normalized_title for token in ("执行结果", "运行结果")):
        return ParsedQuestion(title, normalized_title, "run_document_by_keyword", keyword=normalized_title)

    if any(token in normalized_title for token in ("透视图", "图表")):
        return ParsedQuestion(title, normalized_title, "pivot_chart_by_keyword", keyword=normalized_title)

    if match := re.search(r"涉及到(.+?)业务(?:的文件名称和路径)?", normalized_title):
        return ParsedQuestion(title, normalized_title, "business_search", keyword=match.group(1).strip())

    if match := re.search(r"(?:如何|怎么)?(.+?)命令是什么", normalized_title):
        return ParsedQuestion(title, normalized_title, "command_lookup", keyword=match.group(1).strip())

    if "如何" in normalized_title or "怎么" in normalized_title:
        return ParsedQuestion(title, normalized_title, "command_lookup", keyword=normalized_title)

    if basename:
        return ParsedQuestion(title, normalized_title, "generic_file_lookup", basename=basename, candidate_paths=candidate_paths)

    return ParsedQuestion(title, normalized_title, "fulltext_search", keyword=normalized_title)
