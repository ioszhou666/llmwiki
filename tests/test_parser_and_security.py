from __future__ import annotations

import json
from pathlib import Path

from llm_wiki.question_parser import parse_question
from llm_wiki.security import PermissionPolicy


def test_parse_question_recognizes_core_patterns() -> None:
    paths = [
        "docs/05_需求设计/产品V1需求.docx",
        "docs/04_常用命令/gauss.md",
        "docs/02_环境信息/env_config.xml",
    ]

    parsed = parse_question("找出产品V1需求.docx 路径", paths)
    assert parsed.kind == "find_path"
    assert parsed.candidate_paths == ["docs/05_需求设计/产品V1需求.docx"]

    parsed = parse_question("产品V1需求.docx 待张三处理的批注", paths)
    assert parsed.kind == "assignee_comments"
    assert parsed.assignee == "张三"

    parsed = parse_question("统计全项目 docx 总数量", paths)
    assert parsed.kind == "count_extension"
    assert parsed.extension == "docx"

    parsed = parse_question("产品V1需求.docx 截止20261231的批注", paths)
    assert parsed.kind == "date_comments"
    assert parsed.date_value == "20261231"

    parsed = parse_question("统计当前不同类型文件数量", paths)
    assert parsed.kind == "count_supported_extensions"

    parsed = parse_question("根据 gauss 相关脚本的执行结果给出输出", paths)
    assert parsed.kind == "run_document_by_keyword"

    parsed = parse_question("查询 env_config.xml 中存放的数据库明文密码", paths)
    assert parsed.kind == "file_secret_lookup"

    parsed = parse_question("如何在控制台连接高斯数据库", paths)
    assert parsed.kind == "command_lookup"

    parsed = parse_question("待张三处理的批注", paths)
    assert parsed.kind == "global_assignee_comments"


def test_permission_policy_handles_deny_and_password_exception(tmp_path: Path) -> None:
    permission_path = tmp_path / "Permission.json"
    permission_path.write_text(
        json.dumps(
            {
                "dir": {"deny": ["*/etc"]},
                "command": {"deny": ["Remove-Item", "del*"]},
                "file": {"deny": ["hadoop.env", "spark-*.env"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    policy = PermissionPolicy.from_file(permission_path)

    assert policy.detect_question_risk("使用 Remove-Item 删除 test.md", []) == {"error_msg": "高危命令，拒绝访问"}
    assert policy.detect_question_risk("查询 env_config.xml 中存放的数据库明文密码", []) == {"error_msg": "高危命令，拒绝访问"}
    assert policy.detect_question_risk("读取 spark-prod.env 内容", []) == {"error_msg": "高危命令，拒绝访问"}
    assert policy.detect_question_risk(
        "查询 02_环境信息 中 env_config.xml 的密码",
        ["docs/02_环境信息/env_config.xml"],
    ) is None
