from __future__ import annotations

import argparse
import json
import platform
import shutil
import sqlite3
from pathlib import Path
from typing import Any

from .answerer import AnswerEngine
from .claude_client import ClaudeCodeClient
from .constants import SUPPORTED_EXTENSIONS
from .indexer import WikiIndex
from .reporting import build_release_bundle
from .security import PermissionPolicy
from .wiki_workspace import WikiWorkspace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Claude Code oriented LLM Wiki workbench")
    parser.add_argument("--project-root", type=Path, required=True, help="Root folder for the llm-wiki project")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-wiki", help="Initialize a Karpathy-style llm-wiki project layout")

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

    lint_parser = subparsers.add_parser("lint-wiki", help="Check raw/wiki/index/log coverage and consistency")

    claude_playbook_parser = subparsers.add_parser(
        "claude-playbook",
        help="Print the recommended Claude Code workflow for this llm-wiki project",
    )

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

    index_parser = subparsers.add_parser("index", help="Index docs")
    index_parser.add_argument("--db", type=Path, default=None)

    answer_parser = subparsers.add_parser("answer", help="Answer one question group")
    answer_parser.add_argument("--db", type=Path, default=None)
    answer_parser.add_argument("--group", required=True, help="Question file name such as group-1.md")
    answer_parser.add_argument("--reindex", action="store_true")

    answer_all_parser = subparsers.add_parser("answer-all", help="Answer all question groups")
    answer_all_parser.add_argument("--db", type=Path, default=None)
    answer_all_parser.add_argument("--reindex", action="store_true")

    ask_parser = subparsers.add_parser("ask", help="Answer one free-form question")
    ask_parser.add_argument("--db", type=Path, default=None)
    ask_parser.add_argument("--question", required=True)
    ask_parser.add_argument("--reindex", action="store_true")

    ask_claude_parser = subparsers.add_parser("ask-claude", help="Answer one free-form question via Claude Code")
    ask_claude_parser.add_argument("--db", type=Path, default=None)
    ask_claude_parser.add_argument("--question", required=True)
    ask_claude_parser.add_argument("--reindex", action="store_true")

    doctor_parser = subparsers.add_parser("doctor", help="Inspect runtime and optional dependencies")
    doctor_parser.add_argument("--db", type=Path, default=None)

    answer_claude_parser = subparsers.add_parser("answer-claude", help="Answer one question group via Claude Code")
    answer_claude_parser.add_argument("--db", type=Path, default=None)
    answer_claude_parser.add_argument("--group", required=True, help="Question file name such as group-1.md")
    answer_claude_parser.add_argument("--reindex", action="store_true")

    answer_all_claude_parser = subparsers.add_parser("answer-all-claude", help="Answer all question groups via Claude Code")
    answer_all_claude_parser.add_argument("--db", type=Path, default=None)
    answer_all_claude_parser.add_argument("--reindex", action="store_true")

    claude_status_parser = subparsers.add_parser("claude-status", help="Inspect Claude Code relay/runtime status")
    claude_status_parser.add_argument("--db", type=Path, default=None)

    validate_parser = subparsers.add_parser("validate", help="Run an end-to-end project validation")
    validate_parser.add_argument("--db", type=Path, default=None)

    release_parser = subparsers.add_parser("release", help="Build a release bundle with reports and demo outputs")
    release_parser.add_argument("--db", type=Path, default=None)
    release_parser.add_argument("--target", type=Path, required=True)

    bootstrap_parser = subparsers.add_parser("bootstrap-demo", help="Create a Karpathy-style demo llm-wiki workspace")
    bootstrap_parser.add_argument("--target", type=Path, required=True)
    bootstrap_parser.add_argument("--keep-existing", action="store_true")

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

    docs_root = project_root / "docs"
    question_root = project_root / "question"
    output_root = project_root / "output"
    permission_path = project_root / "Permission.json"
    db_arg = getattr(args, "db", None)
    db_path = db_arg or output_root / "wiki.db"
    db_preexists = db_path.exists()
    index = WikiIndex(db_path)
    try:
        if args.command == "index":
            count = index.index_documents(docs_root, project_root)
            print(f"indexed={count}")
            return
        if args.command == "answer":
            if args.reindex or not db_preexists:
                index.index_documents(docs_root, project_root)
            policy = PermissionPolicy.from_file(permission_path)
            engine = AnswerEngine(index=index, policy=policy, project_root=project_root, output_root=output_root)
            question_path = question_root / args.group
            answer_path = output_root / args.group.replace(".md", "-answer.md")
            engine.answer_group(question_path, answer_path)
            print(answer_path.as_posix())
            return
        if args.command == "answer-all":
            if args.reindex or not db_preexists:
                index.index_documents(docs_root, project_root)
            policy = PermissionPolicy.from_file(permission_path)
            engine = AnswerEngine(index=index, policy=policy, project_root=project_root, output_root=output_root)
            produced = engine.answer_all_groups(question_root, output_root)
            for path in produced:
                print(path)
            return
        if args.command == "ask":
            if args.reindex or not db_preexists:
                index.index_documents(docs_root, project_root)
            policy = PermissionPolicy.from_file(permission_path)
            engine = AnswerEngine(index=index, policy=policy, project_root=project_root, output_root=output_root)
            print(json.dumps(engine.answer_question(args.question), ensure_ascii=False, indent=2))
            return
        if args.command == "ask-claude":
            if args.reindex or not db_preexists:
                index.index_documents(docs_root, project_root)
            policy = PermissionPolicy.from_file(permission_path)
            engine = AnswerEngine(index=index, policy=policy, project_root=project_root, output_root=output_root)
            client = ClaudeCodeClient(workdir=project_root)
            print(json.dumps(engine.answer_question_with_claude(args.question, client), ensure_ascii=False, indent=2))
            return
        if args.command == "doctor":
            claude_client = ClaudeCodeClient(workdir=project_root)
            wiki_workspace.initialize()
            print(
                json.dumps(
                    {
                        "project_root": project_root.as_posix(),
                        "raw_exists": wiki_workspace.raw_root.exists(),
                        "wiki_exists": wiki_workspace.wiki_root.exists(),
                        "wiki_status": wiki_workspace.status(),
                        "docs_exists": docs_root.exists(),
                        "question_exists": question_root.exists(),
                        "output_exists": output_root.exists(),
                        "db_path": db_path.as_posix(),
                        "sqlite_fts5": _has_fts5(),
                        "python": platform.python_version(),
                        "soffice": shutil.which("soffice"),
                        "java": shutil.which("java"),
                        "tika_jar": _find_tika_jar(project_root),
                        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
                        "claude_code": claude_client.auth_status(),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return
        if args.command == "claude-status":
            client = ClaudeCodeClient(workdir=project_root)
            print(json.dumps(client.auth_status(), ensure_ascii=False, indent=2))
            return
        if args.command == "answer-claude":
            if args.reindex or not db_preexists:
                index.index_documents(docs_root, project_root)
            policy = PermissionPolicy.from_file(permission_path)
            engine = AnswerEngine(index=index, policy=policy, project_root=project_root, output_root=output_root)
            client = ClaudeCodeClient(workdir=project_root)
            question_path = question_root / args.group
            answer_path = output_root / args.group.replace(".md", "-answer.md")
            engine.answer_group_with_claude(question_path, answer_path, client)
            print(answer_path.as_posix())
            return
        if args.command == "answer-all-claude":
            if args.reindex or not db_preexists:
                index.index_documents(docs_root, project_root)
            policy = PermissionPolicy.from_file(permission_path)
            engine = AnswerEngine(index=index, policy=policy, project_root=project_root, output_root=output_root)
            client = ClaudeCodeClient(workdir=project_root)
            produced = engine.answer_all_groups_with_claude(question_root, output_root, client)
            for path in produced:
                print(path)
            return
        if args.command == "validate":
            summary = _run_validation(index, project_root, docs_root, question_root, output_root, permission_path)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return
        if args.command == "release":
            summary = _run_validation(index, project_root, docs_root, question_root, output_root, permission_path)
            target_dir = build_release_bundle(project_root, summary, args.target.resolve())
            summary = {**summary, "release_dir": target_dir.as_posix()}
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return
    finally:
        index.close()


def _has_fts5() -> bool:
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("create virtual table temp.fts using fts5(content)")
        return True
    except sqlite3.DatabaseError:
        return False
    finally:
        connection.close()


def _find_tika_jar(project_root: Path) -> str | None:
    candidates = [
        project_root / "tools" / "tika-app.jar",
        Path.cwd() / "tools" / "tika-app.jar",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.as_posix()
    return None


def _run_validation(
    index: WikiIndex,
    project_root: Path,
    docs_root: Path,
    question_root: Path,
    output_root: Path,
    permission_path: Path,
) -> dict[str, Any]:
    index_count = index.index_documents(docs_root, project_root)
    policy = PermissionPolicy.from_file(permission_path)
    engine = AnswerEngine(index=index, policy=policy, project_root=project_root, output_root=output_root)
    produced_answers = [
        _relativize_path(project_root, path)
        for path in engine.answer_all_groups(question_root, output_root)
    ]
    fixed_outputs = sorted(
        _relativize_path(project_root, path)
        for path in (output_root / "fixed").glob("*")
        if path.is_file() and not path.name.endswith(".fix-report.md")
    )
    return {
        "status": "ok",
        "project_root": project_root.as_posix(),
        "indexed_documents": index_count,
        "question_groups": len(list(question_root.glob("group-*.md"))),
        "answer_outputs": produced_answers,
        "fixed_outputs": fixed_outputs,
        "audit_log": _relativize_path(project_root, output_root / "audit.jsonl"),
        "sqlite_fts5": _has_fts5(),
    }


def _relativize_path(project_root: Path, path: str | Path) -> str:
    candidate = Path(path)
    try:
        return candidate.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return candidate.as_posix()


if __name__ == "__main__":
    main()
