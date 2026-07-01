# CLAUDE.md

## Project Purpose

This repository implements a local wiki workbench for the contest scenario:

- multi-format document retrieval
- Office/code comment governance
- controlled execution and chart generation
- dangerous request blocking
- batch answering from `question/group-*.md`

## Required Runtime

- This project is expected to run with `Claude Code`
- In the current machine setup, Claude Code is routed through an Anthropic-compatible relay
- Local deterministic modules remain available as tool layers for indexing, extraction, security, and file transformation

## Preferred Workflow

1. Index local files first
2. Use local security checks before any model-driven answer
3. Use Claude Code for question understanding and final answer synthesis
4. Use deterministic local modules for:
   - SQLite retrieval
   - Office/code comment extraction
   - document fix output
   - Python execution checks
   - Excel pivot chart generation

## Output Rules

- Return JSON only for question answering flows
- For dangerous requests, always return:
  - `{"error_msg":"高危命令，拒绝访问"}`
- Paths should be relative to the project root when possible

## Local Commands

- `llm-wiki --project-root <root> doctor`
- `llm-wiki --project-root <root> claude-status`
- `llm-wiki --project-root <root> ask-claude --question "..."`
- `llm-wiki --project-root <root> answer-claude --group group-1.md`

