from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .answerer import AnswerEngine
from .indexer import WikiIndex
from .security import PermissionPolicy


class WikiRuntime:
    def __init__(self, project_root: Path, db_path: Path | None = None) -> None:
        self.project_root = project_root.resolve()
        self.docs_root = self.project_root / "docs"
        self.question_root = self.project_root / "question"
        self.output_root = self.project_root / "output"
        self.permission_path = self.project_root / "Permission.json"
        self.db_path = (db_path or self.output_root / "wiki.db").resolve()
        self.index = WikiIndex(self.db_path)
        self.policy = PermissionPolicy.from_file(self.permission_path)
        self.engine = AnswerEngine(
            index=self.index,
            policy=self.policy,
            project_root=self.project_root,
            output_root=self.output_root,
        )

    def close(self) -> None:
        self.index.close()

    def index_documents(self) -> dict[str, object]:
        count = self.index.index_documents(self.docs_root, self.project_root)
        return {"indexed": count, "db_path": self.db_path.as_posix()}

    def doctor(self) -> dict[str, object]:
        return {
            "project_root": self.project_root.as_posix(),
            "docs_exists": self.docs_root.exists(),
            "question_exists": self.question_root.exists(),
            "output_exists": self.output_root.exists(),
            "db_path": self.db_path.as_posix(),
            "document_count": len(self.index.list_document_paths()),
        }

    def list_document_paths(self) -> list[str]:
        return self.index.list_document_paths()

    def list_question_groups(self) -> list[str]:
        return sorted(path.name for path in self.question_root.glob("group-*.md"))

    def count_files_by_extension(self, extension: str) -> dict[str, int]:
        return {extension.lower(): self.index.count_files_by_extension(extension)}

    def count_supported_extensions(self) -> dict[str, int]:
        return self.index.count_supported_extensions()

    def search_related_paths(self, keyword: str, limit: int = 20) -> dict[str, list[str]]:
        return {"datas": self.index.search_related_paths(keyword, limit=limit)}

    def find_paths_by_basename(self, basename: str) -> dict[str, list[str]]:
        return {"datas": self.index.find_paths_by_basename(basename)}

    def get_document_record(self, rel_path: str) -> dict[str, object]:
        return {
            "path": rel_path,
            "extension": self.index.get_document_extension(rel_path),
            "content": self.index.get_document_content(rel_path) or "",
            "comments": [dict(row) for row in self.index.list_comments(rel_path=rel_path)],
        }

    def list_comments(
        self,
        rel_path: str | None = None,
        assignee: str | None = None,
        due_date: str | None = None,
    ) -> dict[str, list[dict[str, object]]]:
        return {"datas": [dict(row) for row in self.index.list_comments(rel_path=rel_path, assignee=assignee, due_date=due_date)]}

    def answer_question_local(self, question: str) -> dict[str, object]:
        return self.engine.answer_question(question)

    def answer_group_local(self, group_name: str) -> dict[str, object]:
        question_path = self.question_root / group_name
        answer_path = self.output_root / group_name.replace(".md", "-answer.md")
        answers = self.engine.answer_group(question_path, answer_path)
        return {"answer_path": answer_path.as_posix(), "answers": answers}

    def apply_fixes(self, rel_path: str) -> dict[str, object]:
        return self.engine.apply_fixes(rel_path)

    def build_pivot_chart(self, rel_path: str) -> dict[str, object]:
        return self.engine.build_pivot_chart(rel_path)

    def run_python_document(self, rel_path: str) -> dict[str, object]:
        return self.engine.run_python_document(rel_path)

    def permission_policy_snapshot(self) -> dict[str, object]:
        return {
            "dir": {"deny": self.policy.deny_dirs},
            "command": {"deny": self.policy.deny_commands},
            "file": {"deny": self.policy.deny_files},
        }

    def resources_snapshot(self) -> dict[str, object]:
        return {
            "project_root": self.project_root.as_posix(),
            "document_paths": self.list_document_paths(),
            "question_groups": self.list_question_groups(),
            "permission_policy": self.permission_policy_snapshot(),
        }

    def resources_snapshot_json(self) -> str:
        return json.dumps(self.resources_snapshot(), ensure_ascii=False, indent=2)
