from __future__ import annotations

from pathlib import Path

from llm_wiki.wiki_workspace import WikiWorkspace


def test_initialize_creates_karpathy_layout(tmp_path: Path) -> None:
    workspace = WikiWorkspace(tmp_path)
    status = workspace.initialize()

    assert status["raw_exists"] is True
    assert status["wiki_exists"] is True
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / "wiki" / "index.md").exists()
    assert (tmp_path / "wiki" / "log.md").exists()


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
    source_pages = summary["source_pages"]
    assert any("product_notes" in path for path in source_pages)
    assert any("gauss" in path for path in source_pages)
    assert any(path.name.startswith("raw--product_notes") for path in (tmp_path / "cache" / "extracted").glob("*.md"))
    assert (tmp_path / "wiki" / "index.md").read_text(encoding="utf-8")


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
    assert any("wiki/sources/" in item["path"] for item in query["datas"])

    lint = workspace.lint()
    assert lint["status"] == "ok"
