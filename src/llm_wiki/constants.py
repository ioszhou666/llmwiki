from __future__ import annotations


SUPPORTED_EXTENSIONS = {
    "doc",
    "docx",
    "ppt",
    "pptx",
    "xls",
    "xlsx",
    "xml",
    "java",
    "py",
    "html",
    "md",
    "js",
}

TEXT_EXTENSIONS = {"xml", "java", "py", "html", "md", "js", "txt", "json"}
OFFICE_EXTENSIONS = {"doc", "docx", "ppt", "pptx", "xls", "xlsx"}
CODE_EXTENSIONS = {"xml", "java", "py", "html", "md", "js"}
ALLOWED_PASSWORD_DIR = "02_环境信息"
REJECT_ERROR_MSG = "高危命令，拒绝访问"
