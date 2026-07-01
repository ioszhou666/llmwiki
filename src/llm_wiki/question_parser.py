from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .constants import SUPPORTED_EXTENSIONS


EXTENSION_PATTERN = "|".join(sorted(SUPPORTED_EXTENSIONS, key=len, reverse=True))
FILE_PATTERN = rf"([^\s]+\.(?:{EXTENSION_PATTERN}))"
DATE_PATTERN = r"(20\d{6})"
SECRET_PATTERN = r"(?:密码|密钥|secret|token|apikey|api key|credential|口令|数据库明文密码)"
TODO_PATTERN = r"(?:TODO|todo|批注)"
FIX_PATTERN = r"(?:修复|优化整理|批注修复|TODO修复|todo修复)"
FIX_HINTS = ("修复", "优化整理", "批注修复", "TODO修复", "todo修复")
PATH_HINTS = ("路径", "位置")
PIVOT_HINTS = ("透视图", "图表")
RUN_HINTS = ("执行结果", "运行结果")


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


def _extract_assignee(normalized_title: str) -> str | None:
    patterns = (
        rf"责任人为(.+?)的{TODO_PATTERN}",
        rf"待(.+?)(?:处理的)?{TODO_PATTERN}",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized_title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def parse_question(title: str, all_paths: list[str]) -> ParsedQuestion:
    normalized_title = normalize_question(title)
    basename, candidate_paths = resolve_candidate_paths(normalized_title, all_paths)
    assignee = _extract_assignee(normalized_title)

    if match := re.search(
        rf"(?:统计(?:全项目|当前)?\s*)?({EXTENSION_PATTERN})\s*(?:文件)?(?:的)?(?:总)?数量",
        normalized_title,
        re.IGNORECASE,
    ):
        return ParsedQuestion(title, normalized_title, "count_extension", extension=match.group(1).lower())

    if re.search(r"统计.*不同类型文件.*数量", normalized_title):
        return ParsedQuestion(title, normalized_title, "count_supported_extensions")

    if match := re.search(
        rf"(?:找出|列出|获取).*(?:全部|所有)?\s*({EXTENSION_PATTERN})\s*文件(?:的)?路径",
        normalized_title,
        re.IGNORECASE,
    ):
        return ParsedQuestion(title, normalized_title, "list_extension_paths", extension=match.group(1).lower())

    if basename and re.search(SECRET_PATTERN, normalized_title, re.IGNORECASE):
        return ParsedQuestion(title, normalized_title, "file_secret_lookup", basename=basename, candidate_paths=candidate_paths)

    if basename and any(token in normalized_title for token in PATH_HINTS):
        return ParsedQuestion(title, normalized_title, "find_path", basename=basename, candidate_paths=candidate_paths)

    if basename and re.search(rf"(?:统计)?{TODO_PATTERN}数量", normalized_title, re.IGNORECASE):
        return ParsedQuestion(title, normalized_title, "comment_count", basename=basename, candidate_paths=candidate_paths)

    if basename and assignee:
        return ParsedQuestion(
            title,
            normalized_title,
            "assignee_comments",
            basename=basename,
            candidate_paths=candidate_paths,
            assignee=assignee,
        )

    if basename and (match := re.search(rf"(?:截止|到期|end_date[:]*)\s*{DATE_PATTERN}", normalized_title, re.IGNORECASE)):
        date_value = re.search(DATE_PATTERN, match.group(0))
        return ParsedQuestion(
            title,
            normalized_title,
            "date_comments",
            basename=basename,
            candidate_paths=candidate_paths,
            date_value=date_value.group(1) if date_value else None,
        )

    if basename and any(token in normalized_title for token in FIX_HINTS):
        return ParsedQuestion(title, normalized_title, "fix_document", basename=basename, candidate_paths=candidate_paths)

    if basename and any(token in normalized_title for token in PIVOT_HINTS):
        return ParsedQuestion(title, normalized_title, "pivot_chart", basename=basename, candidate_paths=candidate_paths)

    if basename and any(token in normalized_title for token in RUN_HINTS):
        return ParsedQuestion(title, normalized_title, "run_document", basename=basename, candidate_paths=candidate_paths)

    if assignee and any(token in normalized_title for token in ("数量", "数目", "总数")):
        return ParsedQuestion(title, normalized_title, "global_assignee_comment_count", assignee=assignee)

    if assignee and re.search(FIX_PATTERN, normalized_title, re.IGNORECASE):
        return ParsedQuestion(title, normalized_title, "fix_by_assignee", assignee=assignee)

    if assignee:
        return ParsedQuestion(title, normalized_title, "global_assignee_comments", assignee=assignee)

    if match := re.search(rf"(?:统计)?.*(?:截止|到期|end_date[:]*)\s*{DATE_PATTERN}.*(?:批注|TODO).*数量", normalized_title, re.IGNORECASE):
        date_value = re.search(DATE_PATTERN, match.group(0))
        return ParsedQuestion(
            title,
            normalized_title,
            "global_date_comment_count",
            date_value=date_value.group(1) if date_value else None,
        )

    if match := re.search(rf"(?:截止|到期|end_date[:]*)\s*{DATE_PATTERN}", normalized_title, re.IGNORECASE):
        date_value = re.search(DATE_PATTERN, match.group(0))
        return ParsedQuestion(
            title,
            normalized_title,
            "global_date_comments",
            date_value=date_value.group(1) if date_value else None,
        )

    if any(token in normalized_title for token in RUN_HINTS):
        return ParsedQuestion(title, normalized_title, "run_document_by_keyword", keyword=normalized_title)

    if any(token in normalized_title for token in PIVOT_HINTS):
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
