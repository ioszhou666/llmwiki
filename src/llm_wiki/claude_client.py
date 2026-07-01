from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


DEFAULT_CLAUDE_PATH = Path(
    r"C:\Users\29678\AppData\Local\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe"
)


class ClaudeCodeClient:
    def __init__(self, executable: Path | None = None, workdir: Path | None = None) -> None:
        self.executable = executable or self.detect_executable()
        self.workdir = workdir

    @classmethod
    def detect_executable(cls) -> Path | None:
        discovered = shutil.which("claude")
        if discovered:
            return Path(discovered)
        if DEFAULT_CLAUDE_PATH.exists():
            return DEFAULT_CLAUDE_PATH
        return None

    def is_available(self) -> bool:
        return self.executable is not None and self.executable.exists()

    def auth_status(self) -> dict[str, object]:
        if not self.is_available():
            return {"available": False, "loggedIn": False, "authMethod": "missing", "apiProvider": "missing"}
        result = self._run("auth", "status")
        payload = json.loads(result.stdout.strip())
        payload["available"] = True
        payload["executable"] = self.executable.as_posix()
        return payload

    def ask_json(self, prompt: str) -> dict[str, object]:
        if not self.is_available():
            raise RuntimeError("Claude Code is not installed")
        result = self._run("-p", prompt, "--output-format", "json", "--tools", "")
        envelope = json.loads(result.stdout.strip())
        raw = envelope.get("result", "")
        if not isinstance(raw, str):
            raise RuntimeError("Claude Code returned a non-text result")
        return json.loads(raw)

    def run_text_prompt(self, prompt: str, allow_tools: bool = True) -> str:
        if not self.is_available():
            raise RuntimeError("Claude Code is not installed")
        args = ["-p", prompt]
        if not allow_tools:
            args.extend(["--tools", ""])
        result = self._run(*args)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Claude Code prompt execution failed")
        return result.stdout.strip()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        if not self.executable:
            raise RuntimeError("Claude Code executable is unavailable")
        return subprocess.run(
            [str(self.executable), *args],
            cwd=str(self.workdir) if self.workdir else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=False,
        )
