from __future__ import annotations

import argparse
from pathlib import Path

from .mcp_runtime import WikiRuntime


def create_server(project_root: Path):
    from mcp.server.fastmcp import FastMCP

    runtime = WikiRuntime(project_root=project_root)
    server = FastMCP(
        name="llm-wiki",
        instructions=(
            "Use this server to maintain and query a Claude-native LLM Wiki. "
            "The primary workflow is ingest, curation, linting, and wiki-grounded querying. "
            "Auxiliary deterministic document tools are available as a secondary utility layer."
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

    @server.tool(name="doctor", description="Inspect runtime status for the wiki workspace and optional on-demand docs tool layer.")
    def doctor() -> dict[str, object]:
        return runtime.doctor()

    @server.tool(
        name="scan_documents",
        description="Auxiliary utility tool: scan docs/ on demand and build an ephemeral in-memory document view.",
    )
    def scan_documents() -> dict[str, object]:
        return runtime.scan_documents()

    @server.tool(
        name="list_document_paths",
        description="Auxiliary utility tool: list allowed document paths from docs/ using on-demand scan.",
    )
    def list_document_paths() -> dict[str, list[str]]:
        return {"datas": runtime.list_document_paths()}

    @server.tool(
        name="count_files_by_extension",
        description="Auxiliary utility tool: count docs/ files by extension such as docx, xlsx, md, or py.",
    )
    def count_files_by_extension(extension: str) -> dict[str, int]:
        return runtime.count_files_by_extension(extension)

    @server.tool(
        name="count_supported_extensions",
        description="Auxiliary utility tool: count all supported docs/ file types currently present.",
    )
    def count_supported_extensions() -> dict[str, int]:
        return runtime.count_supported_extensions()

    @server.tool(
        name="search_related_paths",
        description="Auxiliary utility tool: search docs/ and extracted comments by keyword using on-demand scan.",
    )
    def search_related_paths(keyword: str, limit: int = 20) -> dict[str, list[str]]:
        return runtime.search_related_paths(keyword, limit=limit)

    @server.tool(
        name="find_paths_by_basename",
        description="Auxiliary utility tool: find docs/ paths by exact basename.",
    )
    def find_paths_by_basename(basename: str) -> dict[str, list[str]]:
        return runtime.find_paths_by_basename(basename)

    @server.tool(
        name="get_document_record",
        description="Auxiliary utility tool: inspect one scanned document's content and extracted comments.",
    )
    def get_document_record(rel_path: str) -> dict[str, object]:
        return runtime.get_document_record(rel_path)

    @server.tool(
        name="list_comments",
        description="Auxiliary utility tool: list extracted comments filtered by path, assignee, or due date.",
    )
    def list_comments(
        rel_path: str | None = None,
        assignee: str | None = None,
        due_date: str | None = None,
    ) -> dict[str, list[dict[str, object]]]:
        return runtime.list_comments(rel_path=rel_path, assignee=assignee, due_date=due_date)

    @server.tool(
        name="answer_question_local",
        description="Auxiliary utility tool: answer contest-style questions with the deterministic on-demand docs engine.",
    )
    def answer_question_local(question: str) -> dict[str, object]:
        return runtime.answer_question_local(question)

    @server.tool(
        name="apply_fixes",
        description="Auxiliary utility tool: apply deterministic TODO/comment fixes to a document into output/fixed/.",
    )
    def apply_fixes(rel_path: str) -> dict[str, object]:
        return runtime.apply_fixes(rel_path)

    @server.tool(
        name="build_pivot_chart",
        description="Auxiliary utility tool: build a pivot chart from a scanned Excel document.",
    )
    def build_pivot_chart(rel_path: str) -> dict[str, object]:
        return runtime.build_pivot_chart(rel_path)

    @server.tool(
        name="run_python_document",
        description="Auxiliary utility tool: run a scanned Python document through the controlled execution path.",
    )
    def run_python_document(rel_path: str) -> dict[str, object]:
        return runtime.run_python_document(rel_path)

    return server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the llm-wiki MCP server over stdio")
    parser.add_argument("--project-root", type=Path, required=True)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    server = create_server(project_root=args.project_root.resolve())
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
