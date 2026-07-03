from __future__ import annotations

import argparse
from pathlib import Path

from .mcp_runtime import WikiRuntime


def create_server(project_root: Path, db_path: Path | None = None):
    from mcp.server.fastmcp import FastMCP

    runtime = WikiRuntime(project_root=project_root, db_path=db_path)
    server = FastMCP(
        name="llm-wiki",
        instructions=(
            "Use this server to maintain and query a Claude-native LLM Wiki. "
            "The primary workflow is ingest, curation, linting, and wiki-grounded querying."
        ),
    )

    @server.resource("wiki://status", name="wiki-status", mime_type="application/json")
    def wiki_status() -> str:
        return runtime.resources_snapshot_json()

    @server.resource("wiki://permission-policy", name="permission-policy", mime_type="application/json")
    def wiki_permission_policy() -> str:
        import json

        return json.dumps(runtime.permission_policy_snapshot(), ensure_ascii=False, indent=2)

    @server.resource("wiki://security-summary", name="security-summary", mime_type="application/json")
    def wiki_security_summary() -> str:
        import json

        return json.dumps(runtime.security_summary(), ensure_ascii=False, indent=2)

    @server.resource("wiki://curation-status", name="curation-status", mime_type="application/json")
    def wiki_curation_status() -> str:
        import json

        return json.dumps(runtime.wiki_status(), ensure_ascii=False, indent=2)

    @server.resource("wiki://claude-playbook", name="claude-playbook", mime_type="text/markdown")
    def wiki_claude_playbook() -> str:
        return runtime.claude_playbook()["content"]

    @server.tool(name="ingest_wiki_local", description="Seed wiki pages from raw/ using deterministic extraction packets.")
    def ingest_wiki_local(source: str | None = None) -> dict[str, object]:
        return runtime.ingest_wiki_local(source=source)

    @server.tool(name="query_wiki_local", description="Search the curated wiki pages.")
    def query_wiki_local(question: str, limit: int = 5) -> dict[str, object]:
        return runtime.query_wiki_local(question, limit=limit)

    @server.tool(name="lint_wiki", description="Check whether raw/, wiki/, index.md, and log.md stay aligned.")
    def lint_wiki() -> dict[str, object]:
        return runtime.lint_wiki()

    @server.tool(name="get_ingest_prompt", description="Get the canonical Claude Code ingest prompt for this project.")
    def get_ingest_prompt(source: str | None = None) -> dict[str, str]:
        return runtime.get_ingest_prompt(source=source)

    @server.tool(name="get_ingest_workflow", description="Get the staged Claude Code ingest workflow prompts for this project.")
    def get_ingest_workflow(source: str | None = None) -> dict[str, list[dict[str, str]]]:
        return runtime.get_ingest_workflow(source=source)

    @server.tool(name="get_query_prompt", description="Get the canonical Claude Code query prompt for this project.")
    def get_query_prompt(question: str, limit: int = 6) -> dict[str, str]:
        return runtime.get_query_prompt(question, limit=limit)

    return server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the llm-wiki MCP server over stdio")
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--db", type=Path, default=None)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    server = create_server(project_root=args.project_root.resolve(), db_path=args.db)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
