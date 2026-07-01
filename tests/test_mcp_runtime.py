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
        runtime.wiki_workspace.initialize()
        snapshot = runtime.resources_snapshot()
        assert "document_paths" in snapshot
        assert "question_groups" in snapshot
        assert snapshot["permission_policy"]["command"]["deny"] == ["Remove-Item", "del*"]
        assert snapshot["security_summary"]["enforced_on_runtime_tools"] is True
        assert snapshot["wiki_status"]["wiki_exists"] is True
    finally:
        runtime.close()


def test_mcp_runtime_hides_denied_records(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    denied_dir = tmp_path / "docs" / "99_mock_system_dir" / "etc"
    denied_dir.mkdir(parents=True, exist_ok=True)
    denied_doc = denied_dir / "root.md"
    denied_doc.write_text("secret root note\n<!-- TODO: hidden secret task, to: 张三, end_date: 20261231 -->", encoding="utf-8")

    runtime = WikiRuntime(project_root=tmp_path)
    try:
        runtime.index_documents()
        assert "docs/99_mock_system_dir/etc/root.md" not in runtime.list_document_paths()
        denied_record = runtime.get_document_record("docs/99_mock_system_dir/etc/root.md")
        assert denied_record == {"error_msg": "高危命令，拒绝访问"}
        denied_comments = runtime.list_comments(assignee="张三")
        assert all(item["rel_path"] != "docs/99_mock_system_dir/etc/root.md" for item in denied_comments["datas"])
    finally:
        runtime.close()


def test_mcp_runtime_wiki_flows(tmp_path: Path) -> None:
    runtime = WikiRuntime(project_root=tmp_path)
    try:
        runtime.wiki_status()
        (tmp_path / "raw" / "team_notes.md").write_text(
            "# Team Notes\n\nClaude should maintain a persistent wiki.\n",
            encoding="utf-8",
        )
        ingest = runtime.ingest_wiki_local()
        assert ingest["ingested"] == 1
        query = runtime.query_wiki_local("persistent wiki")
        assert query["datas"]
        lint = runtime.lint_wiki()
        assert lint["status"] == "ok"
        playbook = runtime.claude_playbook()
        assert "Workflow A: Ingest Raw Sources Into Wiki" in playbook["content"]
        ingest_prompt = runtime.get_ingest_prompt()
        assert "Do not modify raw/ sources." in ingest_prompt["prompt"]
        query_prompt = runtime.get_query_prompt("persistent wiki")
        assert "persistent wiki" in query_prompt["prompt"]
    finally:
        runtime.close()
