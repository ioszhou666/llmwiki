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
            "Use this server to inspect indexed documents, comments, local question-answering results, "
            "and deterministic fix/execution helpers for the llm-wiki project."
        ),
    )

    @server.resource("wiki://status", name="wiki-status", mime_type="application/json")
    def wiki_status() -> str:
        return runtime.resources_snapshot_json()

    @server.resource("wiki://permission-policy", name="permission-policy", mime_type="application/json")
    def wiki_permission_policy() -> str:
        import json

        return json.dumps(runtime.permission_policy_snapshot(), ensure_ascii=False, indent=2)

    @server.tool(name="index_documents", description="Index docs/ into the local SQLite and FTS store.")
    def index_documents() -> dict[str, object]:
        return runtime.index_documents()

    @server.tool(name="doctor", description="Inspect llm-wiki runtime status for the current project root.")
    def doctor() -> dict[str, object]:
        return runtime.doctor()

    @server.tool(name="list_document_paths", description="List every indexed relative document path.")
    def list_document_paths() -> dict[str, list[str]]:
        return {"datas": runtime.list_document_paths()}

    @server.tool(name="list_question_groups", description="List every question/group-*.md file name.")
    def list_question_groups() -> dict[str, list[str]]:
        return {"datas": runtime.list_question_groups()}

    @server.tool(name="count_files_by_extension", description="Count files by extension such as docx, md, py, xlsx.")
    def count_files_by_extension(extension: str) -> dict[str, int]:
        return runtime.count_files_by_extension(extension)

    @server.tool(name="count_supported_extensions", description="Count all supported file types in the index.")
    def count_supported_extensions() -> dict[str, int]:
        return runtime.count_supported_extensions()

    @server.tool(name="search_related_paths", description="Find related document paths by keyword using FTS and comment search.")
    def search_related_paths(keyword: str, limit: int = 20) -> dict[str, list[str]]:
        return runtime.search_related_paths(keyword, limit=limit)

    @server.tool(name="find_paths_by_basename", description="Find paths by exact basename match.")
    def find_paths_by_basename(basename: str) -> dict[str, list[str]]:
        return runtime.find_paths_by_basename(basename)

    @server.tool(name="get_document_record", description="Read indexed content and comments for one relative path.")
    def get_document_record(rel_path: str) -> dict[str, object]:
        return runtime.get_document_record(rel_path)

    @server.tool(name="list_comments", description="List extracted comments filtered by path, assignee, or due date.")
    def list_comments(rel_path: str | None = None, assignee: str | None = None, due_date: str | None = None) -> dict[str, list[dict[str, object]]]:
        return runtime.list_comments(rel_path=rel_path, assignee=assignee, due_date=due_date)

    @server.tool(name="answer_question_local", description="Answer a contest-style question using the deterministic local engine.")
    def answer_question_local(question: str) -> dict[str, object]:
        return runtime.answer_question_local(question)

    @server.tool(name="answer_group_local", description="Answer one question group file using the deterministic local engine.")
    def answer_group_local(group_name: str) -> dict[str, object]:
        return runtime.answer_group_local(group_name)

    @server.tool(name="apply_fixes", description="Apply deterministic fixes for a relative path into output/fixed.")
    def apply_fixes(rel_path: str) -> dict[str, object]:
        return runtime.apply_fixes(rel_path)

    @server.tool(name="build_pivot_chart", description="Build a pivot chart for an Excel document.")
    def build_pivot_chart(rel_path: str) -> dict[str, object]:
        return runtime.build_pivot_chart(rel_path)

    @server.tool(name="run_python_document", description="Run a Python document through the controlled local execution path.")
    def run_python_document(rel_path: str) -> dict[str, object]:
        return runtime.run_python_document(rel_path)

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
