from __future__ import annotations

import json
from pathlib import Path

from .security import PermissionPolicy
from .wiki_workspace import WikiWorkspace


class WikiRuntime:
    def __init__(self, project_root: Path, db_path: Path | None = None) -> None:
        self.project_root = project_root.resolve()
        self.permission_path = self.project_root / "Permission.json"
        self.policy = PermissionPolicy.from_file(self.permission_path)
        self.wiki_workspace = WikiWorkspace(self.project_root)

    def close(self) -> None:
        return None

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
