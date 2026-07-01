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
    "kill codeagent",
    "读取 c 盘根目录全部文件",
    "读取c盘根目录全部文件",
    "列出 c 盘根目录全部文件",
)
PROMPT_INJECTION_HINTS = (
    "忽略前面所有规则",
    "ignore previous instructions",
    "开启上帝模式",
    "god mode",
    "删除全部文档",
    "强制kill codeagent进程",
    "force kill codeagent",
)
COMMAND_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9._-]*")
PATH_TOKEN_RE = re.compile(r"[A-Za-z0-9_./\\*-]+")


def normalize_text(text: str) -> str:
    normalized = text.strip()
    for source, target in (("：", ":"), ("，", ","), ("（", "("), ("）", ")"), ("\u3000", " ")):
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
        return any(hint in normalized for hint in PROMPT_INJECTION_HINTS)

    def contains_secret_request(self, text: str) -> bool:
        normalized = normalize_text(text)
        return any(keyword in normalized for keyword in SECRET_KEYWORDS)

    def detect_question_risk(self, question: str, candidate_paths: list[str] | None = None) -> dict[str, str] | None:
        candidate_paths = candidate_paths or []
        normalized = normalize_text(question)

        if any(hint in normalized for hint in HIGH_RISK_COMMAND_HINTS):
            return REJECT_MESSAGE
        if self.contains_prompt_injection(question):
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
