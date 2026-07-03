from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from llm_wiki.demo_workspace import build_sample_workspace


def _run_cli(*args: str, workdir: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, "-m", "llm_wiki.cli", *args],
        cwd=str(workdir),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_cli_bootstrap_and_workflow_commands(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    workspace = tmp_path / "workspace"
    build_sample_workspace(workspace)

    bootstrap_target = tmp_path / "bootstrapped"
    bootstrap = _run_cli("--project-root", str(workspace), "bootstrap-demo", "--target", str(bootstrap_target), workdir=project_root)
    assert bootstrap.returncode == 0
    assert (bootstrap_target / "raw").exists()
    assert (bootstrap_target / "wiki" / "index.md").exists()
    assert (bootstrap_target / "CLAUDE.md").exists()
    assert (bootstrap_target / "AGENTS.md").exists()
    assert (bootstrap_target / ".claude" / "commands" / "ingest-wiki.md").exists()

    workflow = _run_cli("--project-root", str(bootstrap_target), "print-ingest-workflow", workdir=project_root)
    assert workflow.returncode == 0
    workflow_payload = json.loads(workflow.stdout)
    assert [item["stage"] for item in workflow_payload] == [
        "source-curation",
        "concept-and-entity-synthesis",
        "index-and-log-finalize",
    ]


def test_cli_ingest_query_lint_and_status(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    workspace = tmp_path / "workspace"
    build_sample_workspace(workspace)

    ingest = _run_cli("--project-root", str(workspace), "ingest", workdir=project_root)
    assert ingest.returncode == 0
    ingest_payload = json.loads(ingest.stdout)
    assert ingest_payload["ingested"] == 4
    assert ingest_payload["summary_pages"]
    assert ingest_payload["concept_pages"]
    assert ingest_payload["entity_pages"]

    query = _run_cli(
        "--project-root",
        str(workspace),
        "query-wiki",
        "--question",
        "gauss database connection",
        workdir=project_root,
    )
    assert query.returncode == 0
    query_payload = json.loads(query.stdout)
    assert query_payload["datas"]

    lint = _run_cli("--project-root", str(workspace), "lint-wiki", workdir=project_root)
    assert lint.returncode == 0
    lint_payload = json.loads(lint.stdout)
    assert lint_payload["status"] == "ok"

    claude_status = _run_cli("--project-root", str(workspace), "claude-status", workdir=project_root)
    assert claude_status.returncode == 0
    status_payload = json.loads(claude_status.stdout)
    assert "available" in status_payload
