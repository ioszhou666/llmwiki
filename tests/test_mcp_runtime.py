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
