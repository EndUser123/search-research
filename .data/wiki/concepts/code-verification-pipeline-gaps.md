---
title: "Code verification pipeline: what tools catch what, and where our gaps are"
created: 2026-07-29
source: session-019fa94d (/www research + _mark_row incident)
sources:
  - https://pylint.readthedocs.io/en/latest/messages/error/no-member.html
  - https://github.com/microsoft/pyright/discussions/5926
  - https://docs.astral.sh/ruff/rules/undefined-name/
  - https://futurumgroup.com/insights/why-ai-coding-agents-need-an-independent-review-layer-trust-not-output-is-the-bottleneck/
  - https://www.appsecengineer.com/blog/why-static-analysis-fails-on-ai-generated-code
  - https://medium.com/@addyosmani/my-llm-coding-workflow-going-into-2026-52fe1681325e
tags: [verification, static-analysis, pyright, pylint, ruff, vulture, trace, dead-code, missing-definition, pipeline, check, review, refactor]
host: both
agent: grok
verification: multi-source-verified
cognitive_load: 3
summary: >
  Maps each code verification tool to the bug classes it catches and misses.
  Identifies that our /check pipeline has a gap: called-but-undefined methods
  (like _mark_row) escape ruff (F821 = undefined name, not attribute),
  vulture (finds defined-but-unused, not called-but-undefined), and pyright
  (only catches if run on the file, which fails for cross-workspace). The
  recommendation: no new skill needed. Instead, add pylint --errors-only as
  a third deterministic layer in /check Step 0.9 (catches no-member/E1101),
  and add a "definition existence check" to /check and /review verifier
  protocols. Port the Claude /trace skill only if static analysis isn't enough.
relations:
  - target: wiki/concepts/cross-workspace-pyright-blind-spot.md
    type: extends
  - target: wiki/concepts/dead-code-detection-workflow.md
    type: extends
  - target: wiki/concepts/textual-tui-pitfall-checklist.md
    type: complements
  - target: wiki/concepts/check-vs-review-complementary-not-redundant.md
    type: complements
  - target: wiki/concepts/capability-hierarchy-for-hook-path-verification.md
    type: extends
---

# Code verification pipeline: what tools catch what, and where our gaps are

## Decision context

The `_mark_row` incident (session 019fa94d) exposed a gap: a method definition
was accidentally removed during batch edits, its 5 callers remained, and no
tool in our `/check` → `/review` pipeline caught it. The app crashed at
runtime. This research answers: which tool SHOULD have caught it, what do
practitioners recommend, and should we build a new `/trace` skill or improve
existing ones?

## What each tool catches — the complete map

| Bug class | Example | ruff F-rules | pyright | pylint | vulture | Claude /trace | Runtime test |
|-----------|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Undefined name** (`NameError`) | `foo()` where `foo` never defined | ✅ F821 | ✅ | ✅ E0602 | ❌ | ✅ | ✅ |
| **Undefined attribute on `self`** | `self._mark_row(...)` where method removed | ❌ (F821 = names only, not attrs) | ✅ reportAttributeAccessIssue | ✅ E1101 no-member | ❌ | ✅ | ✅ |
| **Defined but unused** (dead code) | `def _helper()` never called | ✅ F401 (imports only) | ⚠️ (with config) | ✅ W0612 | ✅ | ✅ | ❌ |
| **Type mismatch** | `x: int = "hello"` | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Missing import** | `os.path.join` without `import os` | ✅ F401/E | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Unused import** | `import json` never used | ✅ F401 | ⚠️ | ✅ W0611 | ✅ | ✅ | ❌ |
| **Resource leak** | file opened, not closed | ❌ | ❌ | ⚠️ W | ❌ | ✅ | ⚠️ |
| **Logic error** | wrong condition, off-by-one | ❌ | ❌ | ❌ | ❌ | ✅ (manual trace) | ✅ |
| **I/O safety** | delete-before-copy | ❌ | ❌ | ❌ | ❌ | ✅ (manual trace) | ✅ |

**Key insight:** The `_mark_row` bug (undefined attribute on `self`) falls
into a gap between ruff (catches undefined names, not attributes) and
vulture (catches defined-but-unused, not called-but-undefined). Pyright
catches it BUT only if run on the file — which didn't happen because the
file was on `D:\` (cross-workspace blind spot).

**Pylint E1101 (`no-member`)** is the tool specifically designed for this.
It does inference-based analysis and catches `obj.missing_method()`.
Pylint 4.0 (Oct 2025) improved false-positive handling for dynamic dispatch.
We don't run pylint in our pipeline at all.

## What practitioners recommend (2025-2026 consensus)

The recommended stack from web research (Reddit, HN, blog posts, Addy Osmani's workflow guide):

1. **Ruff** (speed: lint + format + import sort) — replaces flake8/isort/black
2. **basedpyright or pyright** (type checking + IDE) — catches attribute issues
3. **Pylint `--errors-only`** (deeper inference for no-member, resource leaks) — complementary
4. **Semgrep** (custom patterns, security) — for specific bug classes
5. **AI agent review** (context, logic, cross-file) — for what static tools miss

Key principle from practitioners: **"Treat AI-generated code as untrusted
(junior dev output). Independent verification layers are non-negotiable."**
The Futurum Group research puts it bluntly: "Trust, not output, is the
bottleneck" for AI coding agents.

Reddit consensus on code review tools: CodeRabbit and Qodo are popular for
PR-level review. But for local/in-editor verification, the deterministic
stack (ruff + pyright + pylint) is still the floor. AI review is the ceiling
layer, not the floor.

## Our current pipeline vs the recommended one

| Layer | Recommended | What we have | Gap |
|-------|------------|-------------|-----|
| Fast lint | ruff E,F | ✅ ruff E,F | — |
| Type checking | pyright/mypy | ✅ pyright | Cross-workspace scope gap (fixed this session) |
| Deep inference | pylint --errors-only | ❌ **NOT RUNNING** | **E1101 no-member would have caught _mark_row** |
| Dead code | vulture | ✅ vulture (advisory) | Can't catch called-but-undefined (by design) |
| AI review | specialist agents | ✅ /review + /check | Logic + context; can't catch missing defs if they don't look |
| Runtime test | pytest | ✅ 17 tests | Copy/move path not exercised (handoff exists) |
| Manual trace | /trace skill | ❌ Claude side only | Would catch by reading code + tracing calls |

## Recommendation: improve existing skills, don't add a new one

**No new `/trace` skill needed — yet.** The research shows the gap is in
our deterministic layer, not in our skill architecture. Three improvements
to existing skills close it:

### 1. Add pylint --errors-only to /check Step 0.9 (highest ROI)

```powershell
# After ruff + pyright, add:
$pylint = pylint --errors-only --output-format=json @pyFiles 2>$null
```

Pylint E1101 (`no-member`) catches `self._mark_row()` when `_mark_row`
doesn't exist on the class. It's the exact tool for this bug class. Run
with `--errors-only` to suppress style noise. Pylint 4.0 improved
dynamic-dispatch FP handling.

**Cost:** ~2-5s per file (slower than ruff, faster than pyright on large files).
**Falsifier:** if pylint produces too many false positives on Textual
`@on`/`compose`/`watch_*` methods, add `--generated-members` or disable
specific checks. The `--errors-only` flag already suppresses style warnings.

### 2. Add "definition existence check" to /check + /review verifier protocols

Already done this session (Step 8 of /check verifier prompt). Verifiers now
grep `def _method_name` for every `self._method(...)` call in changed code.
This is a manual trace step — slower than pylint but catches edge cases
pylint misses (e.g., methods defined on parent classes via MRO that pylint
might not resolve).

### 3. Fix the cross-workspace scope gap (already done)

`/check` Step 0.9 now extracts scope_files from the evidence packet including
files on any drive, not just `P:\`. This was the structural reason pyright
didn't run on `D:\.code\Keep-Smaller-Copy\app.py`.

### When to reconsider a /trace skill

Port the Claude `/trace` skill to Grok Build if:
- pylint --errors-only still misses bugs that manual trace-through catches
- The fleet starts doing more cross-module refactoring where call-graph
  analysis (pyan/tldr) would surface impact before editing
- `/go` needs a "trace before implement" step for high-risk changes

The Claude `/trace` skill has 100+ checklist items, state-table methodology,
and integration with `/code` Phase 3.5. It's comprehensive but heavy —
only port if the deterministic improvements aren't enough.

## What this means for /check, /review, /refactor, /go

| Skill | Change | Status |
|-------|--------|--------|
| `/check` Step 0.9 | Add pylint --errors-only as 4th deterministic layer | **TODO** |
| `/check` verifier Step 8 | Add "definition existence check" | ✅ Done |
| `/check` Step 0.9 scope | Extract scope_files cross-workspace | ✅ Done |
| `/review` specialist prompts | Add "check that called methods exist" to checklist | ✅ Done |
| `/refactor` | No change needed — already verifies per-seam | — |
| `/go` | No change needed — delegates to /check + /review | — |

## Falsifier

If pylint --errors-only produces >5 false positives per run on our typical
codebase (Textual apps, skill scripts, hook code), the noise will train
operators to ignore it. In that case, switch to basedpyright (which has
better inference for dynamic Python) or port the Claude /trace skill for
manual trace-through as a fallback.

## Sources

- [Pylint no-member docs](https://pylint.readthedocs.io/en/latest/messages/error/no-member.html) — E1101 catches `obj.missing_method()`
- [Pyright attribute access discussion](https://github.com/microsoft/pyright/discussions/5926) — `reportAttributeAccessIssue` behavior
- [Ruff undefined-name rule](https://docs.astral.sh/ruff/rules/undefined-name/) — F821 scope (names only, not attributes)
- [Futurum Group: independent review layer](https://futurumgroup.com/insights/why-ai-coding-agents-need-an-independent-review-layer-trust-not-output-is-the-bottleneck/) — "Trust not output is the bottleneck"
- [AppSecEngineer: why static analysis fails on AI code](https://www.appsecengineer.com/blog/why-static-analysis-fails-on-ai-generated-code) — AI code needs hybrid verification
- [Addy Osmani: LLM coding workflow 2026](https://medium.com/@addyosmani/my-llm-coding-workflow-going-into-2026-52fe1681325e) — layered pipeline recommendation
- Reddit r/cursor, r/ClaudeAI, r/AI_Agents — practitioner consensus on hybrid verification

## Receipts

- Claude `/trace` skill: `P:\packages\.claude-marketplace\plugins\cc-skills-analysis\skills\trace\SKILL.md` — 100+ checklist items, state-table methodology, call-graph (pyan)
- `/check` Step 0.9: `P:\.grok\skills\check\SKILL.md` lines ~180-240 — ruff + pyright + vulture; pylint NOT present
- `_mark_row` incident: 5 call sites in `D:/.code/Keep-Smaller-Copy/app.py` (lines ~1154-1208), method definition removed during batch edits, caught only at runtime

## Related

- [[cross-workspace-pyright-blind-spot]] — the specific incident that motivated this
- [[dead-code-detection-workflow]] — vulture scope (defined-but-unused only)
- [[textual-tui-pitfall-checklist]] — broader patterns
- [[check-vs-review-complementary-not-redundant]] — why both skills exist
- [[capability-hierarchy-for-hook-path-verification]] — capability tiers (syntax < static < unit < integration < runtime)
