from __future__ import annotations

from pathlib import Path

from llm_wiki.answerer import AnswerEngine
from llm_wiki.demo_workspace import build_sample_workspace
from llm_wiki.indexer import WikiIndex
from llm_wiki.security import PermissionPolicy


class StubClaudeClient:
    def ask_json(self, prompt: str) -> dict[str, object]:
        assert "用户问题" in prompt
        assert "上下文如下" in prompt
        return {"datas": ["stubbed-by-claude"]}


def test_answer_question_with_claude(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    db_path = tmp_path / "output" / "wiki.db"
    index = WikiIndex(db_path)
    try:
        index.index_documents(tmp_path / "docs", tmp_path)
        policy = PermissionPolicy.from_file(tmp_path / "Permission.json")
        engine = AnswerEngine(index=index, policy=policy, project_root=tmp_path, output_root=tmp_path / "output")
        answer = engine.answer_question_with_claude("待张三处理的批注", StubClaudeClient())
        assert answer == {"datas": ["stubbed-by-claude"]}
    finally:
        index.close()
