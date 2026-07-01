from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .extractors import discover_documents, dump_json, extract_document


REQUIRED_DIRS = ("raw", "wiki", "wiki/sources", "cache", "cache/extracted", "output")


@dataclass(slots=True)
class SourcePacket:
    rel_path: str
    title: str
    extension: str
    extracted_path: str
    wiki_page: str
    content_preview: str
    comment_signals: list[str]
    key_points: list[str]


class WikiWorkspace:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.raw_root = self.project_root / "raw"
        self.wiki_root = self.project_root / "wiki"
        self.sources_root = self.wiki_root / "sources"
        self.cache_root = self.project_root / "cache"
        self.extracted_root = self.cache_root / "extracted"
        self.output_root = self.project_root / "output"
        self.claude_md = self.project_root / "CLAUDE.md"
        self.index_md = self.wiki_root / "index.md"
        self.log_md = self.wiki_root / "log.md"
        self.permission_path = self.project_root / "Permission.json"

    def initialize(self) -> dict[str, object]:
        for rel_dir in REQUIRED_DIRS:
            (self.project_root / rel_dir).mkdir(parents=True, exist_ok=True)
        if not self.permission_path.exists():
            self.permission_path.write_text(
                json.dumps(
                    {
                        "dir": {"deny": ["/etc"]},
                        "command": {"deny": ["Remove-Item", "del*", "taskkill", "Stop-Process"]},
                        "file": {"deny": ["hadoop.env", "spark-*.env"]},
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        if not self.claude_md.exists():
            self.claude_md.write_text(self._default_claude_md(), encoding="utf-8")
        if not self.index_md.exists():
            self.index_md.write_text(self._default_index_md(), encoding="utf-8")
        if not self.log_md.exists():
            self.log_md.write_text("# Wiki Log\n\n", encoding="utf-8")
        return self.status()

    def status(self) -> dict[str, object]:
        return {
            "project_root": self.project_root.as_posix(),
            "raw_exists": self.raw_root.exists(),
            "wiki_exists": self.wiki_root.exists(),
            "claude_md_exists": self.claude_md.exists(),
            "index_md_exists": self.index_md.exists(),
            "log_md_exists": self.log_md.exists(),
            "raw_sources": len(self.list_raw_sources()),
            "wiki_pages": len(list(self.wiki_root.rglob("*.md"))),
        }

    def list_raw_sources(self) -> list[Path]:
        if not self.raw_root.exists():
            return []
        return [path for path in discover_documents(self.raw_root) if path.is_file()]

    def ingest_local(self, source: str | None = None) -> dict[str, object]:
        self.initialize()
        sources = self.list_raw_sources()
        if source:
            source_path = (self.raw_root / source).resolve()
            sources = [path for path in sources if path.resolve() == source_path]
        packets = [self._build_source_packet(path) for path in sources]
        for packet in packets:
            self._write_extracted_packet(packet)
            self._write_source_page(packet)
        self._refresh_index(packets)
        self._append_log(
            "ingest-local",
            {
                "count": len(packets),
                "sources": [packet.rel_path for packet in packets],
            },
        )
        return {
            "mode": "local-deterministic-seed",
            "raw_sources": len(sources),
            "ingested": len(packets),
            "source_pages": [packet.wiki_page for packet in packets],
            "index_page": self.index_md.relative_to(self.project_root).as_posix(),
            "log_page": self.log_md.relative_to(self.project_root).as_posix(),
        }

    def query_local(self, question: str, limit: int = 5) -> dict[str, object]:
        self.initialize()
        candidates: list[dict[str, str]] = []
        for page in sorted(self.wiki_root.rglob("*.md")):
            text = page.read_text(encoding="utf-8", errors="ignore")
            score = self._score_text(question, text)
            if score <= 0:
                continue
            candidates.append(
                {
                    "path": page.relative_to(self.project_root).as_posix(),
                    "snippet": self._extract_snippet(question, text),
                    "score": str(score),
                }
            )
        candidates.sort(key=lambda item: int(item["score"]), reverse=True)
        self._append_log("query-local", {"question": question, "matches": [item["path"] for item in candidates[:limit]]})
        return {
            "question": question,
            "datas": [{k: v for k, v in item.items() if k != "score"} for item in candidates[:limit]],
        }

    def lint(self) -> dict[str, object]:
        self.initialize()
        issues: list[str] = []
        raw_sources = self.list_raw_sources()
        source_pages = {page.relative_to(self.project_root).as_posix() for page in self.sources_root.glob("*.md")}
        extracted_pages = {page.relative_to(self.project_root).as_posix() for page in self.extracted_root.glob("*.md")}
        index_text = self.index_md.read_text(encoding="utf-8", errors="ignore") if self.index_md.exists() else ""
        for source in raw_sources:
            slug = self._source_slug(source.relative_to(self.project_root).as_posix())
            wiki_page = f"wiki/sources/{slug}.md"
            extracted_page = f"cache/extracted/{slug}.md"
            if wiki_page not in source_pages:
                issues.append(f"missing source page: {wiki_page}")
            if extracted_page not in extracted_pages:
                issues.append(f"missing extracted packet: {extracted_page}")
            if wiki_page not in index_text:
                issues.append(f"index missing link: {wiki_page}")
        status = "ok" if not issues else "needs_attention"
        self._append_log("lint", {"status": status, "issues": issues})
        return {
            "status": status,
            "issues": issues,
            "raw_sources": len(raw_sources),
            "source_pages": len(source_pages),
            "extracted_packets": len(extracted_pages),
        }

    def build_ingest_prompt(self, source: str | None = None) -> str:
        self.initialize()
        selected = self.list_raw_sources()
        if source:
            source_path = (self.raw_root / source).resolve()
            selected = [path for path in selected if path.resolve() == source_path]
        raw_paths = [path.relative_to(self.project_root).as_posix() for path in selected]
        return (
            "You are maintaining a Karpathy-style LLM Wiki.\n"
            "Operate on the local repository files directly.\n"
            "Follow CLAUDE.md exactly.\n"
            "Task:\n"
            "1. Read CLAUDE.md, wiki/index.md, wiki/log.md.\n"
            "2. Review the raw sources listed below and the deterministic packets in cache/extracted/.\n"
            "3. Update wiki/sources/*.md and any higher-level concept pages needed.\n"
            "4. Keep wiki/index.md current.\n"
            "5. Append a short factual entry to wiki/log.md describing what changed.\n"
            "6. Do not modify raw/ sources.\n"
            f"Raw sources to ingest:\n{json.dumps(raw_paths, ensure_ascii=False, indent=2)}\n"
            "Return a short plain-text summary of files you changed."
        )

    def build_query_prompt(self, question: str, limit: int = 6) -> str:
        result = self.query_local(question, limit=limit)
        context = json.dumps(result["datas"], ensure_ascii=False, indent=2)
        return (
            "You are answering from a Karpathy-style LLM Wiki.\n"
            "Use wiki/index.md, wiki/log.md, and the retrieved wiki page snippets below as context.\n"
            "If the wiki is insufficient, say what is missing instead of inventing.\n"
            f"Question: {question}\n"
            f"Retrieved snippets:\n{context}\n"
            "Return a concise plain-text answer."
        )

    def build_demo_project(self, reset: bool = True) -> Path:
        if reset and self.project_root.exists():
            for child in self.project_root.iterdir():
                if child.is_dir():
                    for nested in sorted(child.rglob("*"), reverse=True):
                        if nested.is_file():
                            nested.unlink()
                        elif nested.is_dir():
                            nested.rmdir()
                    child.rmdir()
                else:
                    child.unlink()
        self.initialize()
        (self.project_root / "docs").mkdir(parents=True, exist_ok=True)
        (self.project_root / "question").mkdir(parents=True, exist_ok=True)
        (self.project_root / "question" / "group-1.md").write_text(
            dump_json(
                [
                    {"id": "group-1-1", "title": "统计 md 文件的数量", "level": "简单"},
                    {"id": "group-1-2", "title": "找出 gauss_runbook.md 路径", "level": "简单"},
                ]
            ),
            encoding="utf-8",
        )
        samples = {
            "raw/product_v1_requirements.md": "# Product V1\n\nThe first release focuses on search, source ingestion, and wiki curation.\n",
            "raw/gauss_runbook.md": "# Gauss Runbook\n\nUse gsql to connect to the database. Keep operational notes factual.\n",
            "raw/market_notes.xml": "<notes><topic>CRM migration</topic><detail>Need cross-team wiki page for migration assumptions.</detail></notes>",
        }
        for rel_path, content in samples.items():
            target = self.project_root / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        self.ingest_local()
        return self.project_root

    def _build_source_packet(self, source_path: Path) -> SourcePacket:
        record = extract_document(source_path, self.project_root)
        slug = self._source_slug(record.relative_path)
        comments = [comment.text for comment in record.comments][:8]
        key_points = self._extract_key_points(record.content)
        return SourcePacket(
            rel_path=record.relative_path,
            title=source_path.stem,
            extension=record.extension,
            extracted_path=f"cache/extracted/{slug}.md",
            wiki_page=f"wiki/sources/{slug}.md",
            content_preview=record.content[:2000].strip(),
            comment_signals=comments,
            key_points=key_points,
        )

    def _write_extracted_packet(self, packet: SourcePacket) -> None:
        target = self.project_root / packet.extracted_path
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "rel_path": packet.rel_path,
            "title": packet.title,
            "extension": packet.extension,
            "comment_signals": packet.comment_signals,
            "key_points": packet.key_points,
            "content_preview": packet.content_preview,
        }
        target.write_text(
            "# Extracted Source Packet\n\n```json\n"
            + dump_json(payload)
            + "\n```\n",
            encoding="utf-8",
        )

    def _write_source_page(self, packet: SourcePacket) -> None:
        target = self.project_root / packet.wiki_page
        target.parent.mkdir(parents=True, exist_ok=True)
        comment_lines = "\n".join(f"- {item}" for item in packet.comment_signals) or "- None"
        key_points = "\n".join(f"- {item}" for item in packet.key_points) or "- Pending Claude curation"
        content = (
            f"# Source: {packet.title}\n\n"
            "## Metadata\n\n"
            f"- Raw source: `{packet.rel_path}`\n"
            f"- Extracted packet: `{packet.extracted_path}`\n"
            f"- File type: `{packet.extension}`\n\n"
            "## Canonical Summary\n\n"
            "_Local deterministic seed. Claude should refine this section during ingest._\n\n"
            "## Key Points\n\n"
            f"{key_points}\n\n"
            "## Comment / TODO Signals\n\n"
            f"{comment_lines}\n\n"
            "## Raw Preview\n\n"
            "```text\n"
            f"{packet.content_preview}\n"
            "```\n"
        )
        target.write_text(content, encoding="utf-8")

    def _refresh_index(self, packets: list[SourcePacket]) -> None:
        source_pages = sorted(page.relative_to(self.project_root).as_posix() for page in self.sources_root.glob("*.md"))
        lines = [
            "# LLM Wiki Index",
            "",
            "## Operating Mode",
            "",
            "- `raw/` stores immutable source material.",
            "- `wiki/` stores the curated knowledge base maintained by Claude Code.",
            "- `cache/extracted/` stores deterministic extraction packets used as ingest aids.",
            "",
            "## Source Pages",
            "",
        ]
        for page in source_pages:
            lines.append(f"- [{Path(page).stem}]({page})")
        lines.extend(
            [
                "",
                "## Curation Notes",
                "",
                "- Create higher-level concept pages when multiple source pages converge on one topic.",
                "- Keep factual claims tied back to a source page or raw source.",
            ]
        )
        self.index_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _append_log(self, event: str, payload: dict[str, object]) -> None:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")
        block = f"## {timestamp} - {event}\n\n```json\n{dump_json(payload)}\n```\n\n"
        existing = self.log_md.read_text(encoding="utf-8", errors="ignore") if self.log_md.exists() else "# Wiki Log\n\n"
        self.log_md.write_text(existing + block, encoding="utf-8")

    def _extract_key_points(self, text: str, limit: int = 6) -> list[str]:
        sentences = [part.strip() for part in re.split(r"[\n。!?]+", text) if part.strip()]
        cleaned: list[str] = []
        for sentence in sentences:
            normalized = re.sub(r"\s+", " ", sentence)
            if len(normalized) < 12:
                continue
            cleaned.append(normalized[:160])
            if len(cleaned) >= limit:
                break
        return cleaned

    def _score_text(self, question: str, text: str) -> int:
        tokens = self._tokens(question)
        lowered = text.lower()
        return sum(lowered.count(token) for token in tokens)

    def _extract_snippet(self, question: str, text: str) -> str:
        lowered = text.lower()
        for token in self._tokens(question):
            index = lowered.find(token)
            if index >= 0:
                start = max(index - 80, 0)
                end = min(index + 220, len(text))
                return text[start:end].strip()
        return text[:220].strip()

    def _tokens(self, text: str) -> list[str]:
        parts = re.findall(r"[A-Za-z0-9_.+-]+|[\u4e00-\u9fff]{2,}", text.lower())
        stopwords = {"the", "and", "for", "with", "what", "how", "wiki", "llm", "source"}
        tokens: list[str] = []
        for part in parts:
            if part in stopwords:
                continue
            if part not in tokens:
                tokens.append(part)
        return tokens

    def _source_slug(self, rel_path: str) -> str:
        source_path = Path(rel_path)
        normalized = source_path.with_suffix("").as_posix().replace("\\", "--").replace("/", "--")
        normalized = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "-", normalized)
        return normalized.strip("-").lower()

    def _default_claude_md(self) -> str:
        return (
            "# CLAUDE.md\n\n"
            "You are maintaining a Karpathy-style LLM Wiki.\n\n"
            "## Architecture\n\n"
            "- `raw/`: immutable source material.\n"
            "- `wiki/`: curated markdown knowledge base.\n"
            "- `cache/extracted/`: deterministic extraction packets that help ingest, but are not the final wiki.\n\n"
            "## Primary Operations\n\n"
            "1. Ingest: read raw sources and update wiki pages.\n"
            "2. Query: answer from the curated wiki, not directly from raw sources when avoidable.\n"
            "3. Lint: keep index, links, and source coverage clean.\n\n"
            "## Editing Rules\n\n"
            "- Never modify `raw/`.\n"
            "- Keep `wiki/index.md` current.\n"
            "- Append factual entries to `wiki/log.md` whenever the wiki changes.\n"
            "- Prefer updating existing concept pages over creating duplicates.\n"
            "- Cite raw sources by path inside the relevant source page.\n"
        )

    def _default_index_md(self) -> str:
        return (
            "# LLM Wiki Index\n\n"
            "## Operating Mode\n\n"
            "- `raw/` stores immutable source material.\n"
            "- `wiki/` stores the curated knowledge base maintained by Claude Code.\n"
            "- `cache/extracted/` stores deterministic extraction packets used as ingest aids.\n\n"
            "## Source Pages\n\n"
            "_No source pages yet._\n"
        )
