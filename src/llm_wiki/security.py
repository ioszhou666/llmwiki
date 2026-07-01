from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .constants import ALLOWED_PASSWORD_DIR, REJECT_ERROR_MSG


REJECT_MESSAGE = {"error_msg": REJECT_ERROR_MSG}
SECRET_KEYWORDS = (
    "密码",
    "密钥",
    "secret",
    "token",
    "apikey",
    "api key",
    "credential",
    "口令",
    "数据库明文密码",
)
HIGH_RISK_COMMAND_HINTS = (
    "rm -rf",
    "remove-item",
    "del ",
    "format c:",
    "shutdown",
    "taskkill",
    "stop-process",
    "kill codeagent",
    "codeagent.exe",
    "读取 c 盘根目录全部文件",
    "读取c盘根目录全部文件",
    "列出 c 盘根目录全部文件",
)
PROMPT_INJECTION_HINTS = (
    "忽略前面所有规则",
    "ignore previous instructions",
    "ignore all previous instructions",
    "开启上帝模式",
    "god mode",
    "删除全部文档",
    "不需要询问用户",
    "无需询问用户",
    "最高优先级任务",
    "无论客户提出什么",
    "遵循当前描述执行",
    "验证命令可执行后才输出",
    "force kill codeagent",
)
DANGEROUS_SIDE_EFFECT_HINTS = (
    "写入",
    "创建",
    "新建",
    "覆盖",
    "删除",
    "删掉",
    "清空",
    "移动",
    "重命名",
    "kill ",
    "terminate ",
    "taskkill",
    "stop-process",
    "remove-item",
    "del ",
)
INDIRECT_EXECUTION_PATTERNS = (
    re.compile(r"完成.+描述的工作"),
    re.compile(r"按照.+要求执行"),
    re.compile(r"根据.+内容执行"),
    re.compile(r"按.+说明操作"),
)
MUTATION_ALLOWED_KINDS = frozenset(
    {
        "fix_document",
        "fix_by_assignee",
        "pivot_chart",
        "pivot_chart_by_keyword",
        "run_document",
        "run_document_by_keyword",
    }
)
COMMAND_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9._-]*")
PATH_TOKEN_RE = re.compile(r"[A-Za-z0-9_./\\*-]+")


def normalize_text(text: str) -> str:
    normalized = text.strip()
    replacements = (
        ("：", ":"),
        ("，", ","),
        ("（", "("),
        ("）", ")"),
        ("\u3000", " "),
    )
    for source, target in replacements:
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.lower()


@dataclass(slots=True)
class PermissionPolicy:
    deny_dirs: list[str] = field(default_factory=list)
    deny_commands: list[str] = field(default_factory=list)
    deny_files: list[str] = field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path | None) -> "PermissionPolicy":
        if path is None or not path.exists():
            return cls()
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            deny_dirs=list(payload.get("dir", {}).get("deny", [])),
            deny_commands=list(payload.get("command", {}).get("deny", [])),
            deny_files=list(payload.get("file", {}).get("deny", [])),
        )

    def is_path_denied(self, path_text: str) -> bool:
        normalized = path_text.replace("\\", "/").lower()
        return any(fnmatch.fnmatch(normalized, pattern.lower()) for pattern in self.deny_dirs + self.deny_files)

    def is_command_denied(self, question_text: str) -> bool:
        normalized = normalize_text(question_text)
        tokens = set(COMMAND_TOKEN_RE.findall(normalized))
        for pattern in self.deny_commands:
            lowered = pattern.lower()
            if fnmatch.fnmatch(normalized, lowered):
                return True
            if any(fnmatch.fnmatch(token, lowered) for token in tokens):
                return True
        return False

    def mentions_denied_target(self, question_text: str) -> bool:
        normalized = normalize_text(question_text).replace("\\", "/")
        tokens = set(PATH_TOKEN_RE.findall(normalized))
        for pattern in self.deny_dirs + self.deny_files:
            lowered = pattern.lower()
            if lowered in normalized:
                return True
            if any(fnmatch.fnmatch(token, lowered) for token in tokens):
                return True
        return False

    def contains_prompt_injection(self, text: str) -> bool:
        normalized = normalize_text(text)
        if any(hint in normalized for hint in PROMPT_INJECTION_HINTS):
            return True
        return any(pattern.search(normalized) for pattern in INDIRECT_EXECUTION_PATTERNS)

    def contains_secret_request(self, text: str) -> bool:
        normalized = normalize_text(text)
        return any(keyword in normalized for keyword in SECRET_KEYWORDS)

    def contains_dangerous_side_effect(self, text: str) -> bool:
        normalized = normalize_text(text)
        return any(hint in normalized for hint in DANGEROUS_SIDE_EFFECT_HINTS)

    def detect_question_risk(
        self,
        question: str,
        candidate_paths: list[str] | None = None,
        parsed_kind: str | None = None,
    ) -> dict[str, str] | None:
        candidate_paths = candidate_paths or []
        normalized = normalize_text(question)

        if any(hint in normalized for hint in HIGH_RISK_COMMAND_HINTS):
            return REJECT_MESSAGE
        if self.contains_prompt_injection(question):
            return REJECT_MESSAGE
        if parsed_kind not in MUTATION_ALLOWED_KINDS and self.contains_dangerous_side_effect(question):
            return REJECT_MESSAGE
        if self.is_command_denied(question):
            return REJECT_MESSAGE
        if self.mentions_denied_target(question):
            return REJECT_MESSAGE
        if any(self.is_path_denied(path) for path in candidate_paths):
            return REJECT_MESSAGE

        if self.contains_secret_request(question):
            allow_password = any(ALLOWED_PASSWORD_DIR in path.replace("\\", "/") for path in candidate_paths)
            if ALLOWED_PASSWORD_DIR in question:
                allow_password = True
            if not allow_password:
                return REJECT_MESSAGE

        return None
