from __future__ import annotations

import json
import subprocess
from pathlib import Path

from llm_wiki.claude_client import ClaudeCodeClient


def test_auth_status_parses_json(monkeypatch: object, tmp_path: Path) -> None:
    executable = tmp_path / "claude.exe"
    executable.write_text("", encoding="utf-8")
    client = ClaudeCodeClient(executable=executable, workdir=tmp_path)

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["claude", "auth", "status"],
            returncode=0,
            stdout=json.dumps({"loggedIn": True, "authMethod": "oauth_token", "apiProvider": "firstParty"}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    payload = client.auth_status()
    assert payload["available"] is True
    assert payload["loggedIn"] is True
    assert payload["apiProvider"] == "firstParty"


def test_ask_json_uses_result_field(monkeypatch: object, tmp_path: Path) -> None:
    executable = tmp_path / "claude.exe"
    executable.write_text("", encoding="utf-8")
    client = ClaudeCodeClient(executable=executable, workdir=tmp_path)

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["claude", "-p"],
            returncode=0,
            stdout=json.dumps({"result": json.dumps({"datas": ["ok"]}, ensure_ascii=False)}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert client.ask_json("test") == {"datas": ["ok"]}
