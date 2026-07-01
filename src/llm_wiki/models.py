from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CommentRecord:
    path: str
    file_type: str
    text: str
    kind: str
    assignee: str | None = None
    due_date: str | None = None
    author: str | None = None
    created_at: str | None = None
    location: str | None = None
    structured: bool = False
    todo_text: str | None = None


@dataclass(slots=True)
class DocumentRecord:
    absolute_path: str
    relative_path: str
    extension: str
    content: str
    comments: list[CommentRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
