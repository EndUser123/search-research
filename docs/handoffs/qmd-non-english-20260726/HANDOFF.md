---
thread_id: 019f9f4f-qmd-non-english-20260726
parent_handoff_path: none
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
current_terminal_id: grok-build-terminal
produced_at: 2026-07-26T21:15:00Z
status: open
handoff_type: investigation
accurate_as_of_head: ea0a48be110dee12dd78317a611c1f6231c4d0f5
---

# Handoff: qmd non-English (Chinese) — remaining translation

## Objective

Translate the remaining 273 Chinese-language lines (docstrings + comments) across 18 files in the installed `qmd` package to English. Runtime-visible log messages (15 lines) were already translated this session; docstrings/comments remain and violate the workspace English-only rule.

## Status

OPEN — runtime fix shipped; docstrings/comments deferred. Work is mechanical (translation only, no logic changes) but will be overwritten on `pip install --upgrade qmd`.

## Read-first list

1. `C:/Users/brsth/AppData/Roaming/Python/Python314/site-packages/qmd/core/embedding.py` — worst offender (14 Chinese lines), has the model-loading log that was already translated
2. `C:/Users/brsth/AppData/Roaming/Python/Python314/site-packages/qmd/models.py` — 45 Chinese lines (most of any file)
3. `~/.claude/Claude.md` § "Language" — the English-only rule this work serves

## Verified facts

- [FACT] Runtime-visible log messages translated this session: 15 lines across 8 files (embedding.py, db.py, models.py, client.py, collection.py, expansion.py, rerank.py, fakes.py). Receipt: `qmd search` verified emitting English log output.
- [FACT] Remaining Chinese: 273 lines across 18 .py files, all in docstrings and comments (not runtime-visible). Receipt: scan script output this session.
- [FACT] Files with most Chinese: models.py (45), core/collection.py (40), core/chunking.py (37), testing/fakes.py (37), core/config.py (19), core/embedding.py (14 — minus the 5 already translated = 9 remaining in comments/docstrings).
- [FACT] Local edits to site-packages will be overwritten on `pip install --upgrade qmd`. The durable fix is upstream contribution.

## Current state

**Done:** runtime-visible log messages translated. `qmd search` now emits English.
**Remaining:** 273 docstring/comment lines in 18 files.

## Task packet

### QMD-TRANS-01: Translate remaining Chinese docstrings/comments

- **goal:** translate all 273 remaining Chinese lines to English
- **in scope:** all `.py` files under `C:/Users/brsth/AppData/Roaming/Python/Python314/site-packages/qmd/` (excluding `__pycache__`)
- **out of scope:** logic changes (translation only); config changes (loguru suppression is a separate concern)
- **acceptance:** re-run the scan script; 0 Chinese lines remain; `qmd search` still works correctly
- **falsifier:** translation breaks a docstring that's used as a test fixture or assertion (unlikely but check)
- **verification level required:** STATIC_INSPECTION (docstrings don't execute)
- **note:** changes will be lost on `pip install --upgrade qmd`. Consider: (a) upstream PR, (b) a re-apply script that can be run post-upgrade, (c) accept the loss and re-translate after upgrades

## Open decisions

### Decision 1: How to make the fix durable

- **(A) Upstream PR to qmd** — best long-term but requires finding the qmd repo, contributing, waiting for merge + release
- **(B) Re-apply script** — save a Python script that translates all known Chinese strings; run it after every `pip install --upgrade qmd`
- **(C) Accept ephemeral fix** — translate locally now; re-translate manually after upgrades
- **selection criterion:** how often qmd is upgraded (if rare, (C) is fine; if frequent, (A) or (B))
- **currently leads:** (B) — lowest effort for durability; the script can live at `P:/.agents/scripts/fix_qmd_english.py`

## Hard constraints

1. **Translation only.** Do not change logic, function signatures, or behavior. Chinese docstrings describe existing behavior; the English translation must describe the same behavior.
2. **Preserve technical accuracy.** Some Chinese terms are domain-specific (e.g., "懒加载" = lazy-loaded, "类级单例" = class-level singleton). Translate the meaning, not word-by-word.

## Cross-reference couplings

- `~/.claude/Claude.md` § "Language" — the English-only rule this work serves
- `pip install --upgrade qmd` → will overwrite all local edits; the re-apply script (if chosen) must be run after every upgrade

## Resumption protocol

1. Read this handoff.
2. Re-scan: `python -c "import re; from pathlib import Path; [print(f) for f in Path(r'C:\Users\brsth\AppData\Roaming\Python\Python314\site-packages\qmd').rglob('*.py') if re.search(r'[\u4e00-\u9fff]', f.read_text(encoding='utf-8')) and '__pycache__' not in f.name]"` — confirm the 273 lines still exist (no upgrade has reset them)
3. Translate each file's docstrings/comments to English
4. Run the scan again; verify 0 Chinese lines remain
5. Resolve Decision 1 (upstream PR vs re-apply script vs accept ephemeral)

## Suggested next invocation

```
Translate remaining Chinese docstrings/comments in qmd to English.
Read P:/docs/handoffs/qmd-non-english-20260726/HANDOFF.md for scope.
273 lines across 18 files — translation only, no logic changes.
After translation, create re-apply script at P:/.agents/scripts/fix_qmd_english.py.
```

## Last user message (verbatim)

> "/handoff file for non-English use."

## Epistemic labels

- All "Verified facts" are `[FACT]` with scan-script receipts cited inline.
- Decision 1 "currently leads (B)" is `[INFERENCE]` — operator has not stated preference on durability approach.
- "Changes will be lost on upgrade" is `[FACT]` — standard pip behavior for site-packages edits.
