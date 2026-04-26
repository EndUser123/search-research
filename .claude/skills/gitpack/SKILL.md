---
name: gitpack
version: "3.0.0"
status: "stable"
category: integration
enforcement: advisory
description: >
  Pack any Python directory into a compact LLM-ready context file. Use this skill whenever the user wants to
  distill, pack, compress, or prepare code for LLM consumption — phrases like "make this repo LLM-ready", "compress
  this codebase for context", "prepare code for AI analysis", "pack this directory", "create a context file from this
  repo". Also use when comparing /gitpack vs /repomix. Pure Python — no external AI tools required.
triggers:
  - /gitpack
aliases:
  - /gitpack
  - /pack
workflow_steps:
  - DISCOVER
  - EXTRACT
  - BUILD
  - APPEND
---

# /gitpack - LLM-Ready Code Packer

Pack a Python directory into a compact context file using only Python's stdlib (AST parsing + direct file reads). No external AI tools, no corruption, deterministic output.

## What This Does

Takes a Python codebase and produces two output files:
- **`<name>_sig.md`** — SIGNATURE TOC + DIRECTORY/FILE INDEX (compact, scannable)
- **`<name>_full.md`** — same + APPENDIX with full source code read directly from disk

Signatures are extracted via Python's `ast` module — exact, deterministic, no LLM involvement.

## Workflow

```
python scripts/gitpack.py <target_dir> [--exclude <patterns>]
```

1. **DISCOVER** — Glob for all `.py` files in `<target_dir>`, applying exclusions
2. **EXTRACT** — Parse each file with `ast`, collect function/class signatures with type annotations
3. **BUILD** — Write two markdown files to `<target_dir>/.aid/<name>/`:
   - `_sig.md` — signatures + indexes only
   - `_full.md` — signatures + indexes + full source appendix
4. **APPEND** — Top-level `.md` files from `<target_dir>` appended to both outputs

**Default exclusions** — always applied unless user overrides with `--exclude`:
```
__pycache__/,*.pyc,*.pyo,*.so,*.dll,*.exe
.venv/,venv/,env/,site-packages/
.pytest_cache/,.mypy_cache/,.ruff_cache/,.tox/
.git/,.hg/,.svn/
dist/,build/,out/,target/,egg-info/,*.egg-info/
.idea/,.vscode/,.DS_Store,Thumbs.db
.env,.env.*,*.log
```

## Output Files

| File | Contents |
|------|----------|
| `<name>_sig.md` | PACK INFO, HOW TO USE, SIGNATURE TOC, DIRECTORY INDEX, FILE INDEX |
| `<name>_full.md` | All of the above + APPENDIX: FULL IMPLEMENTATIONS (full source from disk) |

## Features

- **Pure Python** — uses `ast` for signature extraction, no external dependencies
- **No corruption** — source read directly from disk for appendix, no LLM processing
- **Deterministic** — same input always produces same output
- **Markdown included** — top-level `.md` files appended automatically
- **Type annotations preserved** — return types and arg types shown when present

## Examples

```bash
# Pack the skills directory
/gitpack P:\.claude\skills\gitpack

# Pack with exclusions
/gitpack ./my-project --exclude __pycache__,*.pyc,.aid
```

## Architecture

```
scripts/
  gitpack.py              # Main entry point — pure Python, no external deps
  gitpack_structured.py  # Legacy structurer (uses aid if available)
  gitpack_toc.py          # Legacy TOC builder
```

`gitpack.py` (v3.0) is the recommended entry point. It supersedes the aid-based workflow.

## See Also

- `/gitingest` — Clone + slice + upload to NotebookLM
- `/repomix` — XML/JSON output, skill generation
- `/aid` — Single-file or directory distillation with analysis prompts