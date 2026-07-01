from __future__ import annotations

import argparse
import json
import platform
import shutil
import sqlite3
from pathlib import Path

from .answerer import AnswerEngine
from .constants import SUPPORTED_EXTENSIONS
from .demo_workspace import build_sample_workspace
from .indexer import WikiIndex
from .security import PermissionPolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local wiki workbench")
    parser.add_argument("--project-root", type=Path, required=True, help="Root folder containing docs/question/output")
    subparsers = parser.add_subparsers(dest="command", required=True)

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

    doctor_parser = subparsers.add_parser("doctor", help="Inspect runtime and optional dependencies")
    doctor_parser.add_argument("--db", type=Path, default=None)

    bootstrap_parser = subparsers.add_parser("bootstrap-demo", help="Create a demo workspace")
    bootstrap_parser.add_argument("--target", type=Path, required=True)
    bootstrap_parser.add_argument("--keep-existing", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "bootstrap-demo":
        build_sample_workspace(args.target.resolve(), reset=not args.keep_existing)
        print(args.target.resolve().as_posix())
        return

    project_root = args.project_root.resolve()
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
        if args.command == "doctor":
            print(
                json.dumps(
                    {
                        "project_root": project_root.as_posix(),
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
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
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


if __name__ == "__main__":
    main()
