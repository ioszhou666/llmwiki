from __future__ import annotations

from pathlib import Path

from llm_wiki.demo_workspace import build_sample_workspace
from llm_wiki.mcp_server import create_server
from llm_wiki.mcp_runtime import WikiRuntime


def test_create_server_builds_fastmcp_instance(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    server = create_server(project_root=tmp_path)
    assert server is not None


def test_runtime_supports_auxiliary_document_tool_layer(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "report.md").write_text("report body\n", encoding="utf-8")

    runtime = WikiRuntime(project_root=tmp_path)
    try:
        runtime.index_documents()
        assert runtime.list_document_paths() == ["docs/report.md"]
        assert runtime.get_document_record("docs/report.md")["content"] == "report body\n"
    finally:
        runtime.close()
