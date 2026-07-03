from __future__ import annotations

import argparse
import json
from pathlib import Path

from .claude_client import ClaudeCodeClient
from .wiki_workspace import WikiWorkspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Claude-native LLM Wiki workbench")
    parser.add_argument("--project-root", type=Path, required=True, help="Root folder for the llm-wiki project")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-wiki", help="Initialize a Claude-native llm-wiki project layout")

    ingest_parser = subparsers.add_parser("ingest", help="Seed wiki pages from raw/ using deterministic local extraction")
    ingest_parser.add_argument("--source", help="Optional relative source path under raw/")

    ingest_claude_parser = subparsers.add_parser(
        "ingest-claude",
        help="Run the staged Claude Code ingest workflow over raw/ and cache/extracted/",
    )
    ingest_claude_parser.add_argument("--source", help="Optional relative source path under raw/")

    query_wiki_parser = subparsers.add_parser("query-wiki", help="Answer from wiki/ pages using local wiki search")
    query_wiki_parser.add_argument("--question", required=True)
    query_wiki_parser.add_argument("--limit", type=int, default=5)

    query_wiki_claude_parser = subparsers.add_parser(
        "query-wiki-claude",
        help="Ask Claude Code to answer using the curated wiki context",
    )
    query_wiki_claude_parser.add_argument("--question", required=True)
    query_wiki_claude_parser.add_argument("--limit", type=int, default=6)

    subparsers.add_parser("lint-wiki", help="Check raw/wiki/index/log coverage and consistency")
    subparsers.add_parser("claude-playbook", help="Print the recommended Claude Code workflow for this llm-wiki project")

    ingest_prompt_parser = subparsers.add_parser(
        "print-ingest-prompt",
        help="Print the canonical ingest prompt for manual Claude Code invocation",
    )
    ingest_prompt_parser.add_argument("--source", help="Optional relative source path under raw/")

    ingest_workflow_parser = subparsers.add_parser(
        "print-ingest-workflow",
        help="Print all staged Claude Code ingest prompts in order",
    )
    ingest_workflow_parser.add_argument("--source", help="Optional relative source path under raw/")

    query_prompt_parser = subparsers.add_parser(
        "print-query-prompt",
        help="Print the canonical query prompt for manual Claude Code invocation",
    )
    query_prompt_parser.add_argument("--question", required=True)
    query_prompt_parser.add_argument("--limit", type=int, default=6)

    bootstrap_parser = subparsers.add_parser("bootstrap-demo", help="Create a Claude-native demo llm-wiki workspace")
    bootstrap_parser.add_argument("--target", type=Path, required=True)
    bootstrap_parser.add_argument("--keep-existing", action="store_true")

    subparsers.add_parser("claude-status", help="Inspect Claude Code relay/runtime status")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "bootstrap-demo":
        workspace = WikiWorkspace(args.target.resolve())
        workspace.build_demo_project(reset=not args.keep_existing)
        print(args.target.resolve().as_posix())
        return

    project_root = args.project_root.resolve()
    wiki_workspace = WikiWorkspace(project_root)
    if args.command == "init-wiki":
        print(json.dumps(wiki_workspace.initialize(), ensure_ascii=False, indent=2))
        return
    if args.command == "ingest":
        print(json.dumps(wiki_workspace.ingest_local(source=getattr(args, "source", None)), ensure_ascii=False, indent=2))
        return
    if args.command == "ingest-claude":
        wiki_workspace.ingest_local(source=getattr(args, "source", None))
        client = ClaudeCodeClient(workdir=project_root)
        results: list[dict[str, str]] = []
        for workflow_prompt in wiki_workspace.build_ingest_workflow(source=getattr(args, "source", None)):
            output = client.run_text_prompt(workflow_prompt.prompt, allow_tools=True)
            results.append({"stage": workflow_prompt.stage, "summary": output})
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    if args.command == "query-wiki":
        print(json.dumps(wiki_workspace.query_local(args.question, limit=args.limit), ensure_ascii=False, indent=2))
        return
    if args.command == "query-wiki-claude":
        client = ClaudeCodeClient(workdir=project_root)
        print(client.run_text_prompt(wiki_workspace.build_query_prompt(args.question, limit=args.limit), allow_tools=False))
        return
    if args.command == "lint-wiki":
        print(json.dumps(wiki_workspace.lint(), ensure_ascii=False, indent=2))
        return
    if args.command == "claude-playbook":
        print(wiki_workspace.build_claude_playbook())
        return
    if args.command == "print-ingest-prompt":
        print(wiki_workspace.build_ingest_prompt(source=getattr(args, "source", None)))
        return
    if args.command == "print-ingest-workflow":
        payload = [
            {"stage": item.stage, "prompt": item.prompt}
            for item in wiki_workspace.build_ingest_workflow(source=getattr(args, "source", None))
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if args.command == "print-query-prompt":
        print(wiki_workspace.build_query_prompt(args.question, limit=args.limit))
        return
    if args.command == "claude-status":
        client = ClaudeCodeClient(workdir=project_root)
        print(json.dumps(client.auth_status(), ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
