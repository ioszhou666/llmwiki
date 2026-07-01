# llm-wiki 开源方案调研

## 调研范围

围绕赛题的 4 个核心能力做选型：

1. 多格式文档抽取与批注读取
2. 本地检索与问答
3. Office/代码文档修复
4. 安全执行与 Prompt 注入防护

## 选型结论

### 文档抽取

- `docx/pptx/xlsx`：原生 OOXML 解析
- `doc/ppt/xls`：LibreOffice 无头转换优先，Apache Tika 兜底
- `xml/java/py/html/md/js`：纯文本解析 + 规则抽取 TODO/注释

这样选的原因是：赛题不仅要“读到正文”，还要读到批注、责任人、截止日期等结构化信息。OOXML 原生解析在这方面最稳，老 Office 再用转换和文本抽取做回退链路。

### 检索与问答

- 默认采用 SQLite FTS5
- 不默认引入 Elasticsearch / OpenSearch

原因是赛题规模在数百文件量级，本地单机、零服务依赖和可复制性比重型搜索集群更重要。

### Excel 图表

- 采用 `pandas.pivot_table` + `matplotlib`

原因是它们能稳定生成本地 PNG 结果，并且和 Python 工作流天然兼容。

### 安全防护

- 采用规则和权限策略双层防护
- 关键点：
  - `Permission.json` 黑名单
  - 危险命令拦截
  - 敏感口令问题拦截
  - Prompt 注入关键句拦截
  - Python AST 安全检查

## 官方资料

- Unstructured supported file types
  - https://docs.unstructured.io/open-source/introduction/supported-file-types
- Apache Tika supported formats
  - https://tika.apache.org/2.9.2/formats.html
- LibreOffice start parameters
  - https://help.libreoffice.org/latest/en-US/text/shared/guide/start_parameters.html
- python-docx comments analysis
  - https://python-docx.readthedocs.io/en/latest/dev/analysis/features/comments.html
- openpyxl comments
  - https://openpyxl.readthedocs.io/en/stable/comments.html
- SQLite FTS5
  - https://sqlite.org/fts5.html
- pandas pivot_table
  - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pivot_table.html
- OWASP LLM Prompt Injection Prevention Cheat Sheet
  - https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html
