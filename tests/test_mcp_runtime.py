from __future__ import annotations

from pathlib import Path

from llm_wiki.demo_workspace import build_sample_workspace
from llm_wiki.mcp_runtime import WikiRuntime


def test_mcp_runtime_resources_snapshot(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    runtime = WikiRuntime(project_root=tmp_path)
    try:
        snapshot = runtime.resources_snapshot()
        assert "wiki_status" in snapshot
        assert "permission_policy" in snapshot
        assert snapshot["security_summary"]["enforced_on_runtime_tools"] is True
        assert snapshot["wiki_status"]["wiki_exists"] is True
    finally:
        runtime.close()


def test_mcp_runtime_wiki_flows(tmp_path: Path) -> None:
    runtime = WikiRuntime(project_root=tmp_path)
    try:
        initial_status = runtime.wiki_status()
        assert initial_status["concept_pages"] == 0
        assert initial_status["entity_pages"] == 0
        (tmp_path / "raw" / "team_notes.md").write_text(
            "# Team Notes\n\nClaude should maintain a persistent wiki.\n",
            encoding="utf-8",
        )
        ingest = runtime.ingest_wiki_local()
        assert ingest["ingested"] == 1
        assert ingest["concept_pages"]
        assert ingest["entity_pages"]
        query = runtime.query_wiki_local("persistent wiki")
        assert query["datas"]
        lint = runtime.lint_wiki()
        assert lint["status"] == "ok"
        playbook = runtime.claude_playbook()
        assert "Workflow A: Ingest Raw Sources Into Wiki" in playbook["content"]
        assert "Curation Rules" in playbook["content"]
        ingest_prompt = runtime.get_ingest_prompt()
        assert "Never modify raw/ sources." in ingest_prompt["prompt"]
        ingest_workflow = runtime.get_ingest_workflow()
        assert [item["stage"] for item in ingest_workflow["stages"]] == [
            "source-curation",
            "concept-and-entity-synthesis",
            "index-and-log-finalize",
        ]
        query_prompt = runtime.get_query_prompt("persistent wiki")
        assert "persistent wiki" in query_prompt["prompt"]
    finally:
        runtime.close()


def test_mcp_runtime_legacy_utility_tools(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    docs_root = tmp_path / "docs"
    docs_root.mkdir(parents=True, exist_ok=True)
    (docs_root / "notes.md").write_text(
        "# Notes\n\nTODO: update CRM migration note TO: 李四 END_DATE: 20260703\nCRM migration depends on gauss.\n",
        encoding="utf-8",
    )
    (docs_root / "script.py").write_text("print('ok')\n", encoding="utf-8")

    runtime = WikiRuntime(project_root=tmp_path)
    try:
        doctor = runtime.doctor()
        assert doctor["docs_exists"] is True
        assert doctor["wiki_exists"] is True
        assert doctor["document_store"] == "ephemeral_scan"

        scanned = runtime.scan_documents()
        assert scanned == {"scanned": 2, "mode": "ephemeral_scan"}

        paths = runtime.list_document_paths()
        assert "docs/notes.md" in paths
        assert "docs/script.py" in paths

        assert runtime.count_files_by_extension("md") == {"md": 1}
        assert runtime.count_supported_extensions() == {"md": 1, "py": 1}

        related = runtime.search_related_paths("gauss")
        assert "docs/notes.md" in related["datas"]

        found = runtime.find_paths_by_basename("notes.md")
        assert found == {"datas": ["docs/notes.md"]}

        record = runtime.get_document_record("docs/notes.md")
        assert record["extension"] == "md"
        assert "CRM migration" in record["content"]

        comments = runtime.list_comments(assignee="李四")
        assert len(comments["datas"]) == 1

        answered = runtime.answer_question_local("统计 md 文件数量")
        assert answered == {"md": 1}

        executed = runtime.run_python_document("docs/script.py")
        assert executed == {"datas": ["ok"]}
    finally:
        runtime.close()
