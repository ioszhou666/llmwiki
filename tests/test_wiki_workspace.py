from __future__ import annotations

from pathlib import Path

from llm_wiki.wiki_workspace import WikiWorkspace


def test_initialize_creates_karpathy_layout(tmp_path: Path) -> None:
    workspace = WikiWorkspace(tmp_path)
    status = workspace.initialize()

    assert status["raw_exists"] is True
    assert status["wiki_exists"] is True
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / "wiki" / "index.md").exists()
    assert (tmp_path / "wiki" / "log.md").exists()
    assert (tmp_path / ".claude" / "commands" / "ingest-wiki.md").exists()


def test_ingest_local_creates_source_pages_and_packets(tmp_path: Path) -> None:
    workspace = WikiWorkspace(tmp_path)
    workspace.initialize()
    (tmp_path / "raw" / "product_notes.md").write_text(
        "# Product Notes\n\nSearch should be grounded in curated wiki pages.\n",
        encoding="utf-8",
    )
    (tmp_path / "raw" / "gauss.md").write_text(
        "# Gauss\n\nUse gsql for database access.\n",
        encoding="utf-8",
    )

    summary = workspace.ingest_local()

    assert summary["ingested"] == 2
    summary_pages = summary["summary_pages"]
    concept_pages = summary["concept_pages"]
    entity_pages = summary["entity_pages"]
    assert any("product_notes" in path for path in summary_pages)
    assert any("gauss" in path for path in summary_pages)
    assert concept_pages
    assert entity_pages
    assert any("wiki/concepts/" in path for path in concept_pages)
    assert any("wiki/entities/" in path for path in entity_pages)
    assert any(path.name.startswith("raw--product_notes") for path in (tmp_path / "cache" / "extracted").glob("*.md"))
    index_text = (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")
    assert "## Concepts" in index_text
    assert "## Entities" in index_text
    assert "wiki/concepts/" in index_text
    concept_text = (tmp_path / concept_pages[0]).read_text(encoding="utf-8")
    assert "## Related Summary Pages" in concept_text
    assert "## Synthesis Draft" in concept_text


def test_query_and_lint_operate_on_wiki_pages(tmp_path: Path) -> None:
    workspace = WikiWorkspace(tmp_path)
    workspace.initialize()
    (tmp_path / "raw" / "crm.md").write_text(
        "# CRM Migration\n\nCross-team wiki page required for migration assumptions.\n",
        encoding="utf-8",
    )
    workspace.ingest_local()

    query = workspace.query_local("crm migration assumptions")
    assert query["datas"]
    assert any("wiki/summaries/" in item["path"] or "wiki/concepts/" in item["path"] for item in query["datas"])

    lint = workspace.lint()
    assert lint["status"] == "ok"


def test_workspace_builds_claude_prompts_and_playbook(tmp_path: Path) -> None:
    workspace = WikiWorkspace(tmp_path)
    workspace.initialize()
    (tmp_path / "raw" / "ops.md").write_text(
        "# Ops\n\nKeep wiki curation factual and source-backed.\n",
        encoding="utf-8",
    )
    workspace.ingest_local()

    playbook = workspace.build_claude_playbook()
    assert "Workflow A: Ingest Raw Sources Into Wiki" in playbook
    assert "wiki://claude-playbook" in playbook
    assert "source-curation" in playbook
    assert "Curation Rules" in playbook

    ingest_prompt = workspace.build_ingest_prompt()
    assert "Never modify raw/ sources." in ingest_prompt
    assert "cache/extracted/" in ingest_prompt
    assert "Stage: source-curation" in ingest_prompt
    assert "wiki/summaries/" in ingest_prompt

    ingest_workflow = workspace.build_ingest_workflow()
    assert [item.stage for item in ingest_workflow] == [
        "source-curation",
        "concept-and-entity-synthesis",
        "index-and-log-finalize",
    ]
    assert "wiki/concepts/" in ingest_workflow[1].prompt
    assert "wiki/entities/" in ingest_workflow[1].prompt
    assert "Start from existing seed pages under wiki/concepts/ and wiki/entities/" in ingest_workflow[1].prompt
    assert "wiki/log.md" in ingest_workflow[2].prompt

    query_prompt = workspace.build_query_prompt("source-backed")
    assert "Retrieved snippets" in query_prompt
    assert "source-backed" in query_prompt
