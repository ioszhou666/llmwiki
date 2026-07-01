from __future__ import annotations

from pathlib import Path

from llm_wiki.demo_workspace import build_sample_workspace
from llm_wiki.mcp_runtime import WikiRuntime


def test_mcp_runtime_core_flows(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    runtime = WikiRuntime(project_root=tmp_path)
    try:
        indexed = runtime.index_documents()
        assert indexed["indexed"] == 11

        doctor = runtime.doctor()
        assert doctor["docs_exists"] is True
        assert doctor["document_count"] == 11

        md_paths = runtime.count_files_by_extension("md")
        assert md_paths == {"md": 2}

        search = runtime.search_related_paths("gauss")
        assert "docs/04_常用命令/gauss.md" in search["datas"]

        record = runtime.get_document_record("docs/05_需求设计/产品V1需求.docx")
        assert "应该把旧标题改成新标题" in record["content"]
        assert record["comments"]

        answer = runtime.answer_question_local("找出产品V1需求.docx 路径")
        assert answer == {"datas": ["docs/05_需求设计/产品V1需求.docx"]}
    finally:
        runtime.close()


def test_mcp_runtime_resources_snapshot(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    runtime = WikiRuntime(project_root=tmp_path)
    try:
        runtime.index_documents()
        snapshot = runtime.resources_snapshot()
        assert "document_paths" in snapshot
        assert "question_groups" in snapshot
        assert snapshot["permission_policy"]["command"]["deny"] == ["Remove-Item", "del*"]
    finally:
        runtime.close()
