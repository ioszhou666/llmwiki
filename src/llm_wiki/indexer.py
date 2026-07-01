from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .constants import SUPPORTED_EXTENSIONS
from .extractors import discover_documents, extract_document
from .models import CommentRecord, DocumentRecord


class WikiIndex:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_schema()

    def close(self) -> None:
        self.connection.close()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            create table if not exists documents (
                path text primary key,
                rel_path text not null,
                ext text not null,
                content text not null,
                metadata text not null
            );
            create table if not exists comments (
                id integer primary key autoincrement,
                rel_path text not null,
                ext text not null,
                text text not null,
                todo_text text,
                kind text not null,
                assignee text,
                due_date text,
                author text,
                created_at text,
                location text,
                structured integer not null default 0
            );
            create virtual table if not exists docs_fts using fts5(
                rel_path,
                ext,
                content
            );
            create virtual table if not exists comments_fts using fts5(
                rel_path,
                ext,
                text,
                todo_text,
                assignee
            );
            """
        )
        self.connection.commit()

    def reset(self) -> None:
        self.connection.executescript(
            """
            delete from documents;
            delete from comments;
            delete from docs_fts;
            delete from comments_fts;
            """
        )
        self.connection.commit()

    def index_documents(self, docs_root: Path, project_root: Path) -> int:
        self.reset()
        indexed = 0
        for path in discover_documents(docs_root):
            extension = path.suffix.lstrip(".").lower()
            if extension not in SUPPORTED_EXTENSIONS and path.suffix:
                continue
            record = extract_document(path, project_root)
            self._upsert_document(record)
            indexed += 1
        self.connection.commit()
        return indexed

    def _upsert_document(self, record: DocumentRecord) -> None:
        self.connection.execute(
            """
            insert or replace into documents(path, rel_path, ext, content, metadata)
            values(?, ?, ?, ?, ?)
            """,
            (
                record.absolute_path,
                record.relative_path,
                record.extension,
                record.content,
                json.dumps(record.metadata, ensure_ascii=False),
            ),
        )
        self.connection.execute(
            "insert into docs_fts(rel_path, ext, content) values(?, ?, ?)",
            (record.relative_path, record.extension, record.content),
        )
        for comment in record.comments:
            self._insert_comment(record.relative_path, record.extension, comment)

    def _insert_comment(self, rel_path: str, extension: str, comment: CommentRecord) -> None:
        self.connection.execute(
            """
            insert into comments(rel_path, ext, text, todo_text, kind, assignee, due_date, author, created_at, location, structured)
            values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rel_path,
                extension,
                comment.text,
                comment.todo_text,
                comment.kind,
                comment.assignee,
                comment.due_date,
                comment.author,
                comment.created_at,
                comment.location,
                int(comment.structured),
            ),
        )
        self.connection.execute(
            "insert into comments_fts(rel_path, ext, text, todo_text, assignee) values(?, ?, ?, ?, ?)",
            (rel_path, extension, comment.text, comment.todo_text or "", comment.assignee or ""),
        )

    def count_files_by_extension(self, extension: str) -> int:
        row = self.connection.execute(
            "select count(*) as total from documents where ext = ?",
            (extension.lower(),),
        ).fetchone()
        return int(row["total"])

    def count_supported_extensions(self) -> dict[str, int]:
        rows = self.connection.execute(
            "select ext, count(*) as total from documents group by ext order by ext"
        ).fetchall()
        return {row["ext"]: int(row["total"]) for row in rows}

    def find_paths_by_basename(self, basename: str) -> list[str]:
        rows = self.connection.execute("select rel_path from documents order by rel_path").fetchall()
        target = basename.casefold()
        return [row["rel_path"] for row in rows if Path(row["rel_path"]).name.casefold() == target]

    def list_document_paths(self) -> list[str]:
        rows = self.connection.execute("select rel_path from documents order by rel_path").fetchall()
        return [row["rel_path"] for row in rows]

    def search_paths(self, keyword: str, limit: int = 20) -> list[str]:
        rows = self.connection.execute(
            """
            select rel_path
            from docs_fts
            where docs_fts match ?
            group by rel_path
            limit ?
            """,
            (to_fts_query(keyword), limit),
        ).fetchall()
        if rows:
            return [row["rel_path"] for row in rows]
        fallback = self.connection.execute(
            """
            select rel_path
            from documents
            where rel_path like ? or content like ?
            order by rel_path
            limit ?
            """,
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()
        return [row["rel_path"] for row in fallback]

    def search_snippets(self, keyword: str, limit: int = 5) -> list[str]:
        return [row["snippet"] for row in self.search_snippet_rows(keyword, limit=limit)]

    def search_snippet_rows(self, keyword: str, limit: int = 5) -> list[sqlite3.Row]:
        rows = self.connection.execute(
            """
            select rel_path, snippet(docs_fts, 2, '[', ']', '...', 12) as snippet
            from docs_fts
            where docs_fts match ?
            limit ?
            """,
            (to_fts_query(keyword), limit),
        ).fetchall()
        filtered_rows = [row for row in rows if row["snippet"]]
        if filtered_rows:
            return filtered_rows
        fallback = self.connection.execute(
            """
            select rel_path, substr(content, 1, 120) as snippet
            from documents
            where content like ?
            limit ?
            """,
            (f"%{keyword}%", limit),
        ).fetchall()
        return [row for row in fallback if row["snippet"]]

    def search_comment_paths(self, keyword: str, limit: int = 20) -> list[str]:
        rows = self.connection.execute(
            """
            select distinct rel_path
            from comments_fts
            where comments_fts match ?
            limit ?
            """,
            (to_fts_query(keyword), limit),
        ).fetchall()
        if rows:
            return [row["rel_path"] for row in rows]
        fallback = self.connection.execute(
            """
            select distinct rel_path
            from comments
            where text like ? or todo_text like ?
            limit ?
            """,
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()
        return [row["rel_path"] for row in fallback]

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
        row = self.connection.execute("select content from documents where rel_path = ?", (rel_path,)).fetchone()
        return row["content"] if row else None

    def get_document_absolute_path(self, rel_path: str) -> str | None:
        row = self.connection.execute("select path from documents where rel_path = ?", (rel_path,)).fetchone()
        return row["path"] if row else None

    def get_document_extension(self, rel_path: str) -> str | None:
        row = self.connection.execute("select ext from documents where rel_path = ?", (rel_path,)).fetchone()
        return row["ext"] if row else None

    def list_comments(
        self,
        rel_path: str | None = None,
        assignee: str | None = None,
        due_date: str | None = None,
    ) -> list[sqlite3.Row]:
        clauses = []
        params: list[str] = []
        if rel_path:
            clauses.append("rel_path = ?")
            params.append(rel_path)
        if assignee:
            clauses.append("assignee = ?")
            params.append(assignee)
        if due_date:
            clauses.append("due_date = ?")
            params.append(due_date)
        where = f"where {' and '.join(clauses)}" if clauses else ""
        rows = self.connection.execute(
            f"""
            select rel_path, ext, text, todo_text, kind, assignee, due_date, author, created_at, location, structured
            from comments
            {where}
            order by rel_path, location, id
            """,
            params,
        ).fetchall()
        return rows


def to_fts_query(keyword: str) -> str:
    terms = [part.strip() for part in keyword.replace("/", " ").replace("\\", " ").split() if part.strip()]
    if not terms:
        return keyword
    return " OR ".join(f'"{term}"' for term in terms)
