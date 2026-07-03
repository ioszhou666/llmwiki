from __future__ import annotations

import json
from pathlib import Path

from .answerer import AnswerEngine
from .indexer import WikiIndex
from .security import PermissionPolicy
from .wiki_workspace import WikiWorkspace


class WikiRuntime:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.docs_root = self.project_root / "docs"
        self.output_root = self.project_root / "output"
        self.permission_path = self.project_root / "Permission.json"
        self.index = WikiIndex(self.docs_root, self.project_root)
        self.policy = PermissionPolicy.from_file(self.permission_path)
        self.wiki_workspace = WikiWorkspace(self.project_root)
        self.engine = AnswerEngine(
            index=self.index,
            policy=self.policy,
            project_root=self.project_root,
            output_root=self.output_root,
        )

    def close(self) -> None:
        self.index.close()

    def doctor(self) -> dict[str, object]:
        self.wiki_workspace.initialize()
        document_count = self.index.refresh()
        return {
            "project_root": self.project_root.as_posix(),
            "raw_exists": self.wiki_workspace.raw_root.exists(),
            "wiki_exists": self.wiki_workspace.wiki_root.exists(),
            "docs_exists": self.docs_root.exists(),
            "output_exists": self.output_root.exists(),
            "document_store": "ephemeral_scan",
            "document_count": document_count,
            "raw_source_count": len(self.wiki_workspace.list_raw_sources()),
        }

    def scan_documents(self) -> dict[str, object]:
        count = self.index.refresh()
        return {"scanned": count, "mode": "ephemeral_scan"}

    def wiki_status(self) -> dict[str, object]:
        return self.wiki_workspace.initialize()

    def ingest_wiki_local(self, source: str | None = None) -> dict[str, object]:
        return self.wiki_workspace.ingest_local(source=source)

    def query_wiki_local(self, question: str, limit: int = 5) -> dict[str, object]:
        return self.wiki_workspace.query_local(question, limit=limit)

    def lint_wiki(self) -> dict[str, object]:
        return self.wiki_workspace.lint()

    def claude_playbook(self) -> dict[str, str]:
        return {"content": self.wiki_workspace.build_claude_playbook()}

    def get_ingest_prompt(self, source: str | None = None) -> dict[str, str]:
        return {"prompt": self.wiki_workspace.build_ingest_prompt(source=source)}

    def get_ingest_workflow(self, source: str | None = None) -> dict[str, list[dict[str, str]]]:
        return {
            "stages": [
                {"stage": item.stage, "prompt": item.prompt}
                for item in self.wiki_workspace.build_ingest_workflow(source=source)
            ]
        }

    def get_query_prompt(self, question: str, limit: int = 6) -> dict[str, str]:
        return {"prompt": self.wiki_workspace.build_query_prompt(question, limit=limit)}

    def list_document_paths(self) -> list[str]:
        self.index.refresh()
        return [path for path in self.index.list_document_paths() if not self.policy.is_path_denied(path)]

    def count_files_by_extension(self, extension: str) -> dict[str, int]:
        self.index.refresh()
        suffix = f".{extension.lower()}"
        total = sum(1 for rel_path in self.list_document_paths() if Path(rel_path).suffix.lower() == suffix)
        return {extension.lower(): total}

    def count_supported_extensions(self) -> dict[str, int]:
        self.index.refresh()
        counts: dict[str, int] = {}
        for rel_path in self.list_document_paths():
            ext = Path(rel_path).suffix.lstrip(".").lower()
            counts[ext] = counts.get(ext, 0) + 1
        return {key: counts[key] for key in sorted(counts)}

    def search_related_paths(self, keyword: str, limit: int = 20) -> dict[str, list[str]]:
        self.index.refresh()
        paths = [
            path
            for path in self.index.search_related_paths(keyword, limit=limit)
            if not self.policy.is_path_denied(path)
        ]
        return {"datas": paths}

    def find_paths_by_basename(self, basename: str) -> dict[str, list[str]]:
        self.index.refresh()
        paths = [
            path
            for path in self.index.find_paths_by_basename(basename)
            if not self.policy.is_path_denied(path)
        ]
        return {"datas": paths}

    def get_document_record(self, rel_path: str) -> dict[str, object]:
        self.index.refresh()
        if self.policy.is_path_denied(rel_path):
            return {"error_msg": "高危命令，拒绝访问"}
        return {
            "path": rel_path,
            "extension": self.index.get_document_extension(rel_path),
            "content": self.index.get_document_content(rel_path) or "",
            "comments": [
                dict(row)
                for row in self.index.list_comments(rel_path=rel_path)
                if not self.policy.is_path_denied(str(row["rel_path"]))
            ],
        }

    def list_comments(
        self,
        rel_path: str | None = None,
        assignee: str | None = None,
        due_date: str | None = None,
    ) -> dict[str, list[dict[str, object]]]:
        self.index.refresh()
        if rel_path and self.policy.is_path_denied(rel_path):
            return {"datas": []}
        rows = self.index.list_comments(rel_path=rel_path, assignee=assignee, due_date=due_date)
        return {"datas": [dict(row) for row in rows if not self.policy.is_path_denied(str(row["rel_path"]))]}

    def answer_question_local(self, question: str) -> dict[str, object]:
        self.index.refresh()
        return self.engine.answer_question(question)

    def apply_fixes(self, rel_path: str) -> dict[str, object]:
        self.index.refresh()
        return self.engine.apply_fixes(rel_path)

    def build_pivot_chart(self, rel_path: str) -> dict[str, object]:
        self.index.refresh()
        return self.engine.build_pivot_chart(rel_path)

    def run_python_document(self, rel_path: str) -> dict[str, object]:
        self.index.refresh()
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
            "wiki_status": self.wiki_status(),
            "document_paths": self.list_document_paths(),
            "permission_policy": self.permission_policy_snapshot(),
            "security_summary": self.security_summary(),
        }

    def resources_snapshot_json(self) -> str:
        return json.dumps(self.resources_snapshot(), ensure_ascii=False, indent=2)

    def security_summary(self) -> dict[str, object]:
        return {
            "deny_dirs": self.policy.deny_dirs,
            "deny_commands": self.policy.deny_commands,
            "deny_files": self.policy.deny_files,
            "enforced_on_runtime_tools": True,
        }
