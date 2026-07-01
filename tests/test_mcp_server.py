from __future__ import annotations

from pathlib import Path

from llm_wiki.demo_workspace import build_sample_workspace
from llm_wiki.mcp_server import create_server


def test_create_server_builds_fastmcp_instance(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    server = create_server(project_root=tmp_path)
    assert server is not None
