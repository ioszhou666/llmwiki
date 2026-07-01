from __future__ import annotations

import json
from pathlib import Path

from openpyxl import load_workbook

from llm_wiki.answerer import AnswerEngine
from llm_wiki.demo_workspace import build_sample_workspace
from llm_wiki.indexer import WikiIndex
from llm_wiki.security import PermissionPolicy


def test_end_to_end(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    db_path = tmp_path / "output" / "wiki.db"
    index = WikiIndex(db_path)
    try:
        count = index.index_documents(tmp_path / "docs", tmp_path)
        assert count == 7
        policy = PermissionPolicy.from_file(tmp_path / "Permission.json")
        engine = AnswerEngine(index=index, policy=policy, project_root=tmp_path, output_root=tmp_path / "output")
        answers = engine.answer_group(tmp_path / "question" / "group-1.md", tmp_path / "output" / "group-1-answer.md")
        assert answers[0]["answer"] == {"docx": 1}
        assert answers[1]["answer"]["datas"] == ["docs/05_需求设计/产品V1需求.docx"]
        assert answers[2]["answer"]["datas"] == ["todo: 把旧标题改成新标题, to: 张三, end_date: 20261231"]
        assert answers[3]["answer"] == {"count": 1}
        assert answers[4]["answer"]["target"] == "output/fixed/产品V1需求.docx"
        assert answers[5]["answer"] == {"error_msg": "高危命令，拒绝访问"}
    finally:
        index.close()


def test_apply_xlsx_fix(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    db_path = tmp_path / "output" / "wiki.db"
    index = WikiIndex(db_path)
    try:
        index.index_documents(tmp_path / "docs", tmp_path)
        policy = PermissionPolicy.from_file(tmp_path / "Permission.json")
        engine = AnswerEngine(index=index, policy=policy, project_root=tmp_path, output_root=tmp_path / "output")
        answer = engine.apply_fixes("docs/06_日常办公/销售统计.xlsx")
        assert answer["target"] == "output/fixed/销售统计.xlsx"
        workbook = load_workbook(tmp_path / "output" / "fixed" / "销售统计.xlsx")
        sheet = workbook["销售"]
        assert sheet["A2"].value == "华中"
    finally:
        index.close()


def test_answer_all_and_audit(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    additional_group = [
        {"id": "group-2-1", "title": "统计当前不同类型文件数量", "level": "简单"},
        {"id": "group-2-2", "title": "涉及到gauss业务的文件名称和路径", "level": "中等"},
        {"id": "group-2-3", "title": "产品V1需求.docx 截止20261231的批注", "level": "中等"},
    ]
    (tmp_path / "question" / "group-2.md").write_text(json.dumps(additional_group, ensure_ascii=False, indent=2), encoding="utf-8")
    db_path = tmp_path / "output" / "wiki.db"
    index = WikiIndex(db_path)
    try:
        index.index_documents(tmp_path / "docs", tmp_path)
        policy = PermissionPolicy.from_file(tmp_path / "Permission.json")
        engine = AnswerEngine(index=index, policy=policy, project_root=tmp_path, output_root=tmp_path / "output")
        produced = engine.answer_all_groups(tmp_path / "question", tmp_path / "output")
        assert len(produced) == 2
        group2 = json.loads((tmp_path / "output" / "group-2-answer.md").read_text(encoding="utf-8"))
        assert "docx" in group2[0]["answer"]
        assert group2[1]["answer"]["datas"]
        assert group2[2]["answer"]["datas"] == ["todo: 把旧标题改成新标题, to: 张三, end_date: 20261231"]
        audit_lines = (tmp_path / "output" / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        assert audit_lines
    finally:
        index.close()


def test_keyword_based_python_execution(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    db_path = tmp_path / "output" / "wiki.db"
    index = WikiIndex(db_path)
    try:
        index.index_documents(tmp_path / "docs", tmp_path)
        policy = PermissionPolicy.from_file(tmp_path / "Permission.json")
        engine = AnswerEngine(index=index, policy=policy, project_root=tmp_path, output_root=tmp_path / "output")
        answer = engine.answer_question("根据 gauss 相关脚本的执行结果给出输出")
        assert answer == {"datas": ["safe-result"]}
    finally:
        index.close()


def test_allowed_password_lookup_and_global_comment_filter(tmp_path: Path) -> None:
    build_sample_workspace(tmp_path)
    db_path = tmp_path / "output" / "wiki.db"
    index = WikiIndex(db_path)
    try:
        index.index_documents(tmp_path / "docs", tmp_path)
        policy = PermissionPolicy.from_file(tmp_path / "Permission.json")
        engine = AnswerEngine(index=index, policy=policy, project_root=tmp_path, output_root=tmp_path / "output")
        password_answer = engine.answer_question("查询 02_环境信息 中 env_config.xml 存放的数据库明文密码")
        assert password_answer == {"datas": ["demo-pass"]}
        global_comment_answer = engine.answer_question("待张三处理的批注")
        assert any("docs/05_需求设计/产品V1需求.docx" in item for item in global_comment_answer["datas"])
        command_answer = engine.answer_question("如何在控制台连接高斯数据库")
        assert command_answer["datas"]
        assert any("gsql" in item.lower() for item in command_answer["datas"])
    finally:
        index.close()
