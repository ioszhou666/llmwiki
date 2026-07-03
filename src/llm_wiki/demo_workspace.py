from __future__ import annotations

import shutil
from pathlib import Path


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_sample_workspace(root: Path, reset: bool = True) -> Path:
    if reset and root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)

    write_text(
        root / "raw" / "product_v1_requirements.md",
        "# Product V1\n\n"
        "The first release focuses on search, source ingestion, and wiki curation.\n"
        "Claude Code should maintain durable markdown pages instead of answering directly from raw files.\n",
    )
    write_text(
        root / "raw" / "gauss_runbook.md",
        "# Gauss Runbook\n\n"
        "Use gsql to connect to the database.\n"
        "Keep operational notes factual and traceable.\n",
    )
    write_text(
        root / "raw" / "crm_migration.xml",
        "<notes><topic>CRM migration</topic><detail>Need a cross-team concept page for migration assumptions and owners.</detail></notes>",
    )
    write_text(
        root / "raw" / "service_map.md",
        "# Service Map\n\n"
        "The platform team owns billing-api and gauss integration.\n"
        "Production environment changes require explicit review.\n",
    )
    return root
