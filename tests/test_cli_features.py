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


def test_cli_ask_doctor_and_bootstrap(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    workspace = tmp_path / "workspace"
    build_sample_workspace(workspace)

    ask = _run_cli(
        "--project-root",
        str(workspace),
        "ask",
        "--question",
        "env_config.xml",
        workdir=project_root,
    )
    assert ask.returncode == 0
    assert "env_config.xml" in ask.stdout

    doctor = _run_cli("--project-root", str(workspace), "doctor", workdir=project_root)
    assert doctor.returncode == 0
    payload = json.loads(doctor.stdout)
    assert payload["sqlite_fts5"] is True
    assert "docx" in payload["supported_extensions"]

    bootstrap_target = tmp_path / "bootstrapped"
    bootstrap = _run_cli("--project-root", str(workspace), "bootstrap-demo", "--target", str(bootstrap_target), workdir=project_root)
    assert bootstrap.returncode == 0
    assert (bootstrap_target / "docs").exists()
    assert (bootstrap_target / "question" / "group-1.md").exists()


def test_cli_validate_runs_end_to_end(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    workspace = tmp_path / "workspace"
    build_sample_workspace(workspace)

    validate = _run_cli("--project-root", str(workspace), "validate", workdir=project_root)
    assert validate.returncode == 0
    payload = json.loads(validate.stdout)
    assert payload["status"] == "ok"
    assert payload["indexed_documents"] == 11
    assert payload["question_groups"] == 2
    assert payload["answer_outputs"] == ["output/group-1-answer.md", "output/group-2-answer.md"]
    assert payload["fixed_outputs"] == ["output/fixed/产品V1需求.docx"]
    assert (workspace / "output" / "group-1-answer.md").exists()
    assert (workspace / "output" / "group-2-answer.md").exists()
    assert (workspace / "output" / "audit.jsonl").exists()


def test_cli_release_builds_deliverables(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    workspace = tmp_path / "workspace"
    target = tmp_path / "release_bundle"
    build_sample_workspace(workspace)

    release = _run_cli(
        "--project-root",
        str(workspace),
        "release",
        "--target",
        str(target),
        workdir=project_root,
    )
    assert release.returncode == 0
    payload = json.loads(release.stdout)
    assert payload["status"] == "ok"
    assert payload["release_dir"] == target.as_posix()
    assert (target / "OPEN_SOURCE_RESEARCH.md").exists()
    assert (target / "SYSTEM_DESIGN.md").exists()
    assert (target / "VALIDATION_REPORT.md").exists()
    assert (target / "demo_output" / "group-1-answer.md").exists()
    assert (target / "demo_output" / "group-2-answer.md").exists()
    assert (target / "demo_output" / "audit.jsonl").exists()
    assert (target / "fixed" / "产品V1需求.docx").exists()
