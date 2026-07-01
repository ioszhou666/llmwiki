from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .extractors import discover_documents, dump_json, extract_document


REQUIRED_DIRS = ("raw", "wiki", "wiki/sources", "wiki/topics", "cache", "cache/extracted", "output")


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


@dataclass(slots=True)
class WorkflowPrompt:
    stage: str
    prompt: str


@dataclass(slots=True)
class TopicSeed:
    slug: str
    title: str
    source_pages: list[str]
    evidence_points: list[str]
    keywords: list[str]


class WikiWorkspace:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.raw_root = self.project_root / "raw"
        self.wiki_root = self.project_root / "wiki"
        self.sources_root = self.wiki_root / "sources"
        self.topics_root = self.wiki_root / "topics"
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
            "topic_pages": len(list(self.topics_root.glob("*.md"))),
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
        topic_seeds = self._build_topic_seeds(packets)
        for topic_seed in topic_seeds:
            self._write_topic_seed_page(topic_seed)
        self._refresh_index(packets)
        self._append_log(
            "ingest-local",
            {
                "count": len(packets),
                "sources": [packet.rel_path for packet in packets],
                "topic_seeds": [seed.slug for seed in topic_seeds],
            },
        )
        return {
            "mode": "local-deterministic-seed",
            "raw_sources": len(sources),
            "ingested": len(packets),
            "source_pages": [packet.wiki_page for packet in packets],
            "topic_pages": [f"wiki/topics/{seed.slug}.md" for seed in topic_seeds],
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
        return self.build_ingest_workflow(source=source)[0].prompt

    def build_ingest_workflow(self, source: str | None = None) -> list[WorkflowPrompt]:
        self.initialize()
        selected = self.list_raw_sources()
        if source:
            source_path = (self.raw_root / source).resolve()
            selected = [path for path in selected if path.resolve() == source_path]
        raw_paths = [path.relative_to(self.project_root).as_posix() for path in selected]
        source_pages = sorted(page.relative_to(self.project_root).as_posix() for page in self.sources_root.glob("*.md"))
        topic_pages = sorted(page.relative_to(self.project_root).as_posix() for page in self.topics_root.glob("*.md"))
        shared_header = (
            "You are maintaining a Karpathy-style LLM Wiki.\n"
            "Operate on the local repository files directly.\n"
            "Follow CLAUDE.md exactly.\n"
            "Never modify raw/ sources.\n"
        )
        return [
            WorkflowPrompt(
                stage="source-curation",
                prompt=(
                    shared_header
                    + "Stage: source-curation\n"
                    + "1. Read CLAUDE.md, wiki/index.md, and wiki/log.md.\n"
                    + "2. Review the raw sources listed below and the deterministic packets in cache/extracted/.\n"
                    + "3. Update only wiki/sources/*.md pages so each source page has a clean canonical summary, key points, and source-grounded notes.\n"
                    + "4. Do not create topic pages yet.\n"
                    + f"Raw sources in scope:\n{json.dumps(raw_paths, ensure_ascii=False, indent=2)}\n"
                    + "Return a short plain-text summary of the source pages you changed."
                ),
            ),
            WorkflowPrompt(
                stage="topic-synthesis",
                prompt=(
                    shared_header
                    + "Stage: topic-synthesis\n"
                    + "1. Read wiki/sources/*.md and identify themes that deserve shared topic or concept pages.\n"
                    + "2. Start from existing seed pages under wiki/topics/ and strengthen them instead of creating duplicates when possible.\n"
                    + "3. Create or update pages under wiki/topics/ when multiple sources converge on one operational topic, concept, project, or decision.\n"
                    + "4. Prefer a small number of durable topic pages over many thin pages.\n"
                    + "5. Merge overlapping topic pages when they describe the same idea, workflow, system, or decision boundary.\n"
                    + "6. Use these merge rules:\n"
                    + "   - merge if two pages share the same core entity or process name\n"
                    + "   - merge if one page is only a narrower wording variant of another\n"
                    + "   - do not merge if one page is a source-specific factual summary and the other is a cross-source synthesis\n"
                    + "7. Add backlinks or references from source pages when useful, but keep the main work in wiki/topics/.\n"
                    + f"Existing source pages:\n{json.dumps(source_pages, ensure_ascii=False, indent=2)}\n"
                    + f"Existing topic pages:\n{json.dumps(topic_pages, ensure_ascii=False, indent=2)}\n"
                    + "Return a short plain-text summary of topic pages you created or updated."
                ),
            ),
            WorkflowPrompt(
                stage="index-and-log-finalize",
                prompt=(
                    shared_header
                    + "Stage: index-and-log-finalize\n"
                    + "1. Refresh wiki/index.md so it links to all important source and topic pages.\n"
                    + "2. Append a factual entry to wiki/log.md describing what changed in this ingest session.\n"
                    + "3. Do a brief consistency sweep for broken structure or duplicate pages.\n"
                    + "4. Keep edits concise and operationally useful.\n"
                    + "Return a short plain-text summary of the final index/log updates."
                ),
            ),
        ]

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

    def build_claude_playbook(self) -> str:
        self.initialize()
        return (
            "# Claude Code Playbook\n\n"
            "## Workflow A: Ingest Raw Sources Into Wiki\n\n"
            "1. Open the project root.\n"
            "2. Read `CLAUDE.md`, `wiki/index.md`, and `wiki/log.md` first.\n"
            "3. Review files in `raw/` and deterministic packets in `cache/extracted/`.\n"
            "4. Run the staged ingest workflow in order:\n"
            "   - source-curation\n"
            "   - topic-synthesis\n"
            "   - index-and-log-finalize\n"
            "5. Never edit `raw/`.\n\n"
            "### Topic Merge Rules\n\n"
            "- Strengthen an existing topic page before creating a new overlapping page.\n"
            "- Merge pages that clearly describe the same system, workflow, decision, or business theme.\n"
            "- Keep source-specific summary pages under `wiki/sources/` and cross-source synthesis under `wiki/topics/`.\n\n"
            "## Workflow B: Query The Wiki\n\n"
            "1. Read `wiki/index.md` to find relevant areas.\n"
            "2. Inspect linked pages and `wiki/log.md` when recent curation matters.\n"
            "3. Answer from `wiki/` first.\n"
            "4. If the wiki is insufficient, state the missing coverage clearly.\n\n"
            "## Recommended CLI Helpers\n\n"
            f"- `llm-wiki --project-root {self.project_root.as_posix()} ingest`\n"
            f"- `llm-wiki --project-root {self.project_root.as_posix()} ingest-claude`\n"
            f"- `llm-wiki --project-root {self.project_root.as_posix()} print-ingest-workflow`\n"
            f"- `llm-wiki --project-root {self.project_root.as_posix()} query-wiki --question \"...\"`\n"
            f"- `llm-wiki --project-root {self.project_root.as_posix()} query-wiki-claude --question \"...\"`\n"
            f"- `llm-wiki --project-root {self.project_root.as_posix()} lint-wiki`\n\n"
            "## Recommended MCP Resources / Tools\n\n"
            "- Resource: `wiki://curation-status`\n"
            "- Resource: `wiki://claude-playbook`\n"
            "- Tool: `ingest_wiki_local`\n"
            "- Tool: `query_wiki_local`\n"
            "- Tool: `lint_wiki`\n"
            "- Tool: `get_ingest_prompt`\n"
            "- Tool: `get_ingest_workflow`\n"
            "- Tool: `get_query_prompt`\n"
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

    def _write_topic_seed_page(self, topic_seed: TopicSeed) -> None:
        target = self.topics_root / f"{topic_seed.slug}.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        source_lines = "\n".join(f"- `{page}`" for page in topic_seed.source_pages) or "- None"
        evidence_lines = "\n".join(f"- {item}" for item in topic_seed.evidence_points) or "- Pending synthesis"
        keyword_lines = ", ".join(f"`{item}`" for item in topic_seed.keywords) or "`pending`"
        content = (
            f"# Topic: {topic_seed.title}\n\n"
            "## Topic Type\n\n"
            "_Seed topic page generated by deterministic ingest. Claude should refine and merge when needed._\n\n"
            "## Candidate Keywords\n\n"
            f"{keyword_lines}\n\n"
            "## Related Source Pages\n\n"
            f"{source_lines}\n\n"
            "## Evidence Points\n\n"
            f"{evidence_lines}\n\n"
            "## Synthesis Draft\n\n"
            "- What stable concept, workflow, or decision boundary ties these sources together?\n"
            "- Should this topic merge with an existing topic page?\n"
            "- What facts belong here instead of staying only in source pages?\n"
        )
        target.write_text(content, encoding="utf-8")

    def _refresh_index(self, packets: list[SourcePacket]) -> None:
        source_pages = sorted(page.relative_to(self.project_root).as_posix() for page in self.sources_root.glob("*.md"))
        topic_pages = sorted(page.relative_to(self.project_root).as_posix() for page in self.topics_root.glob("*.md"))
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
        lines.extend(["", "## Topic Pages", ""])
        if topic_pages:
            for page in topic_pages:
                lines.append(f"- [{Path(page).stem}]({page})")
        else:
            lines.append("_No topic pages yet._")
        lines.extend(
            [
                "",
                "## Curation Notes",
                "",
                "- Create higher-level concept pages when multiple source pages converge on one topic.",
                "- Merge overlapping topic pages instead of proliferating synonyms.",
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

    def _build_topic_seeds(self, packets: list[SourcePacket]) -> list[TopicSeed]:
        grouped: dict[str, dict[str, object]] = {}
        for packet in packets:
            for topic_phrase in self._extract_topic_phrases(packet):
                slug = self._slugify_topic(topic_phrase)
                if not slug:
                    continue
                bucket = grouped.setdefault(
                    slug,
                    {
                        "title": self._display_topic(topic_phrase),
                        "source_pages": [],
                        "evidence_points": [],
                        "keywords": Counter(),
                    },
                )
                if packet.wiki_page not in bucket["source_pages"]:
                    bucket["source_pages"].append(packet.wiki_page)
                for point in packet.key_points[:3]:
                    if point not in bucket["evidence_points"]:
                        bucket["evidence_points"].append(point)
                for keyword in self._topic_keywords_from_phrase(topic_phrase):
                    bucket["keywords"][keyword] += 1
        topic_seeds: list[TopicSeed] = []
        for slug, bucket in grouped.items():
            source_pages = bucket["source_pages"]
            evidence_points = bucket["evidence_points"][:5]
            keywords = [item for item, _count in bucket["keywords"].most_common(6)]
            if not source_pages:
                continue
            topic_seeds.append(
                TopicSeed(
                    slug=slug,
                    title=bucket["title"],
                    source_pages=source_pages,
                    evidence_points=evidence_points,
                    keywords=keywords,
                )
            )
        topic_seeds.sort(key=lambda item: (len(item.source_pages), item.slug), reverse=True)
        return topic_seeds

    def _extract_topic_phrases(self, packet: SourcePacket) -> list[str]:
        phrases: list[str] = []
        title_phrase = self._normalize_topic_phrase(packet.title)
        if title_phrase:
            phrases.append(title_phrase)
        for point in packet.key_points:
            for phrase in re.findall(r"[A-Za-z][A-Za-z0-9 _-]{2,}|[\u4e00-\u9fff]{2,}", point):
                normalized = self._normalize_topic_phrase(phrase)
                if normalized and normalized not in phrases:
                    phrases.append(normalized)
        focused: list[str] = []
        for phrase in phrases:
            if self._is_useful_topic_phrase(phrase):
                focused.append(phrase)
        return focused[:5]

    def _normalize_topic_phrase(self, phrase: str) -> str:
        normalized = re.sub(r"\s+", " ", phrase).strip(" -_:,.")
        return normalized

    def _is_useful_topic_phrase(self, phrase: str) -> bool:
        lowered = phrase.lower()
        stop_phrases = {
            "product",
            "notes",
            "runbook",
            "first release",
            "source",
            "summary",
            "preview",
        }
        if len(lowered) < 4:
            return False
        return lowered not in stop_phrases

    def _slugify_topic(self, phrase: str) -> str:
        normalized = phrase.lower().replace("/", " ").replace("\\", " ")
        normalized = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "-", normalized)
        normalized = normalized.strip("-")
        if not normalized:
            return ""
        return normalized[:60]

    def _display_topic(self, phrase: str) -> str:
        if re.search(r"[\u4e00-\u9fff]", phrase):
            return phrase
        return " ".join(part.capitalize() for part in phrase.split())

    def _topic_keywords_from_phrase(self, phrase: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z0-9_.+-]+|[\u4e00-\u9fff]{2,}", phrase.lower())
        return [token for token in tokens if token not in {"the", "and", "for", "with"}]

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
            "- Use `wiki/topics/` for cross-source synthesis, not source-local facts.\n"
            "- Merge overlapping topic pages when they represent the same concept or workflow.\n"
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
