# llm-wiki Implementation Plan

## Stage 1. Foundation
- Clean encoding issues and normalize UTF-8 content
- Centralize constants, answer format, and shared rules
- Rebuild question parsing and security matching
- Status: completed

## Stage 2. Document Extraction
- Parse `docx/pptx/xlsx/xml/java/py/html/md/js`
- Add fallback chain for `doc/ppt/xls`
- Normalize comment metadata and extraction output
- Status: completed

## Stage 3. Index and Retrieval
- Expand SQLite FTS retrieval
- Add path, basename, comment, assignee, date, and snippet queries
- Improve semantic-ish fallback for business and command questions
- Status: completed

## Stage 4. Question Routing
- Cover all contest question classes
- Support mixed natural language and filenames
- Keep answer format strict and machine-readable
- Status: completed

## Stage 5. Fix Engine
- Apply deterministic fixes to code/text documents
- Apply Office comment-driven fixes to `docx/xlsx/pptx`
- Generate fix reports under `output/fixed`
- Status: completed

## Stage 6. Secure Execution
- Enforce `Permission.json`
- Block prompt injection and dangerous commands
- Restrict password-like questions
- Support controlled code execution and audit trail
- Status: completed

## Stage 7. Validation and Delivery
- Add contest-style sample datasets and tests
- Batch answer `group-x.md`
- Produce delivery docs and demo outputs
- Status: completed
