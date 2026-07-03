from __future__ import annotations

import re
from pathlib import Path

from .constants import SUPPORTED_EXTENSIONS
from .extractors import discover_documents, extract_document
from .models import DocumentRecord


class WikiIndex:
    def __init__(self, docs_root: Path, project_root: Path) -> None:
        self.docs_root = docs_root
        self.project_root = project_root
        self._documents: dict[str, DocumentRecord] = {}
        self._comment_rows: list[dict[str, object]] = []

    def close(self) -> None:
        return None

    def refresh(self) -> int:
        self._documents = {}
        self._comment_rows = []
        if not self.docs_root.exists():
            return 0
        indexed = 0
        for path in discover_documents(self.docs_root):
            extension = path.suffix.lstrip(".").lower()
            if extension not in SUPPORTED_EXTENSIONS and path.suffix:
                continue
            record = extract_document(path, self.project_root)
            self._documents[record.relative_path] = record
            for comment in record.comments:
                self._comment_rows.append(
                    {
                        "rel_path": record.relative_path,
                        "ext": record.extension,
                        "text": comment.text,
                        "todo_text": comment.todo_text,
                        "kind": comment.kind,
                        "assignee": comment.assignee,
                        "due_date": comment.due_date,
                        "author": comment.author,
                        "created_at": comment.created_at,
                        "location": comment.location,
                        "structured": int(comment.structured),
                    }
                )
            indexed += 1
        self._comment_rows.sort(key=lambda row: (str(row["rel_path"]), str(row["location"] or "")))
        return indexed

    def list_document_paths(self) -> list[str]:
        return sorted(self._documents)

    def find_paths_by_basename(self, basename: str) -> list[str]:
        target = basename.casefold()
        return [path for path in self.list_document_paths() if Path(path).name.casefold() == target]

    def count_files_by_extension(self, extension: str) -> int:
        suffix = f".{extension.lower()}"
        return sum(1 for rel_path in self.list_document_paths() if Path(rel_path).suffix.lower() == suffix)

    def count_supported_extensions(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for rel_path in self.list_document_paths():
            ext = Path(rel_path).suffix.lstrip(".").lower()
            counts[ext] = counts.get(ext, 0) + 1
        return {key: counts[key] for key in sorted(counts)}

    def search_paths(self, keyword: str, limit: int = 20) -> list[str]:
        terms = _search_terms(keyword)
        matches: list[str] = []
        for rel_path in self.list_document_paths():
            record = self._documents[rel_path]
            haystacks = (record.relative_path, record.content)
            if _matches_terms(haystacks, terms):
                matches.append(rel_path)
            if len(matches) >= limit:
                break
        return matches

    def search_snippet_rows(self, keyword: str, limit: int = 5) -> list[dict[str, str]]:
        terms = _search_terms(keyword)
        rows: list[dict[str, str]] = []
        for rel_path in self.list_document_paths():
            record = self._documents[rel_path]
            snippet = _build_snippet(record.content, terms)
            if snippet:
                rows.append({"rel_path": rel_path, "snippet": snippet})
            if len(rows) >= limit:
                break
        return rows

    def search_comment_paths(self, keyword: str, limit: int = 20) -> list[str]:
        terms = _search_terms(keyword)
        matches: list[str] = []
        for row in self._comment_rows:
            if _matches_terms((str(row["text"]), str(row["todo_text"] or ""), str(row["assignee"] or "")), terms):
                rel_path = str(row["rel_path"])
                if rel_path not in matches:
                    matches.append(rel_path)
            if len(matches) >= limit:
                break
        return matches

    def search_related_paths(self, keyword: str, limit: int = 20) -> list[str]:
        merged: list[str] = []
        for path in self.search_paths(keyword, limit=limit):
            if path not in merged:
                merged.append(path)
        for path in self.search_comment_paths(keyword, limit=limit):
            if path not in merged:
                merged.append(path)
        return merged[:limit]

    def get_document_content(self, rel_path: str) -> str | None:
        record = self._documents.get(rel_path)
        return record.content if record else None

    def get_document_absolute_path(self, rel_path: str) -> str | None:
        record = self._documents.get(rel_path)
        return record.absolute_path if record else None

    def get_document_extension(self, rel_path: str) -> str | None:
        record = self._documents.get(rel_path)
        return record.extension if record else None

    def list_comments(
        self,
        rel_path: str | None = None,
        assignee: str | None = None,
        due_date: str | None = None,
    ) -> list[dict[str, object]]:
        rows = self._comment_rows
        if rel_path is not None:
            rows = [row for row in rows if row["rel_path"] == rel_path]
        if assignee is not None:
            rows = [row for row in rows if row["assignee"] == assignee]
        if due_date is not None:
            rows = [row for row in rows if row["due_date"] == due_date]
        return list(rows)


def _search_terms(keyword: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"[\s/\\]+", keyword) if part.strip()]
    return parts or [keyword]


def _matches_terms(haystacks: tuple[str, ...], terms: list[str]) -> bool:
    lowered_haystacks = [item.casefold() for item in haystacks]
    return any(term.casefold() in haystack for term in terms for haystack in lowered_haystacks)


def _build_snippet(content: str, terms: list[str], window: int = 120) -> str | None:
    lowered = content.casefold()
    best_index: int | None = None
    best_term = ""
    for term in terms:
        index = lowered.find(term.casefold())
        if index >= 0 and (best_index is None or index < best_index):
            best_index = index
            best_term = term
    if best_index is None:
        return None
    start = max(best_index - 30, 0)
    end = min(best_index + max(len(best_term), 1) + 60, len(content))
    snippet = content[start:end].replace("\n", " ").strip()
    if len(snippet) > window:
        snippet = snippet[:window].rstrip()
    return snippet
