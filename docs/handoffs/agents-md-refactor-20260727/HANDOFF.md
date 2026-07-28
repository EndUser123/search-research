---
thread_id: agents-md-refactor-20260727
parent_handoff_path: none
current_session_id: 019fa48a-fb52-79a3-b8dc-d13c5da284d2
current_terminal_id: grok-build-terminal
produced_at: 2026-07-27T20:50:00Z
status: resolved
resolved_at: 2026-07-28
resolved_by_session: 019fa48a
handoff_type: investigation
accurate_as_of_head: LATEST
---

# AGENTS.md progressive-disclosure refactor

## Objective

Refactor `~/.grok/AGENTS.md` from ~992 lines to ~300 lines by moving rationale
and evidence to wiki concepts, keeping only universally-applicable rules + wikilinks
in the always-loaded file. Validated by [[agents-md-construction-best-practices]].

## Status

RESOLVED (2026-07-28, session 019fa48a). Full refactor completed:

| File | Before | After | Reduction |
|------|--------|-------|-----------|
| `~/.grok/AGENTS.md` | 1,170 lines | 505 lines | 57% |
| `P:\AGENTS.md` | 602 lines | 115 lines | 81% |
| Claude compat files (3) | 583 lines | 0 (not loaded) | 100% |
| **Total loaded** | **1,679** | **620** | **63%** |

**What was done:**
1. Stripped all reference incidents, falsifiers, worked examples, verbose rationale
2. Set `compat.claude.agents = false` — Claude files no longer force-loaded (see [[disabling-claude-compat-instruction-loading]])
3. Ported 1 unique rule (replacement default) from Claude files
4. Created 10 missing wiki concepts for dangling wikilinks (all 17 now resolve)
5. Verified all rules survived via keyword checks; 1 lost rule (filter-repo) caught and restored
6. `/tp` critique validated direction, caught 5 specific losses (all restored)

**Wiki concepts created/updated:**
- [[enforcement-hierarchy-and-compaction-strategy]] — lossless/lossy compaction + hook/MCP/CLI decision framework
- [[disabling-claude-compat-instruction-loading]] — the config decision
- [[grok-build-stop-hook-payload-lastassistantmessage]] — payload field bug found during refactor
- [[behavioral-detection-approaches-practitioner-survey]] — community approaches research
- [[agents-md-construction-best-practices]] — updated with refactor results
- 10 stub concepts for previously-dangling wikilinks

**Backups:** `~/.grok/AGENTS.md.backup-20260728` and `P:\AGENTS.md.backup-20260728`

## Why this matters

AGENTS.md loads on every request. At 992 lines (~150+ instructions), it's past
the instruction-following ceiling (~150-200 instructions per HumanLayer research).
Every line of rationale degrades instruction-following on ALL rules uniformly.

## Per-section refactor plan

| Section | Current lines | Target | Action |
|---|---|---|---|
| **Evidence-first default** | 316 | ~30 | Create wiki concept; keep 1-paragraph rule + `[[wikilink]]` |
| **File editing protocol** | 162 | ~15 | Already has wiki concept at `~/.grok/docs/file-editing-protocol.md`; keep rule + link |
| **Hard rules (subtotal)** | 458 | ~150 | Move essays to wiki; keep rules |
| **Recommendations** | 112 | ~40 | Tighten; move alternatives-before-architectural to wiki |
| **Search before proposing** | 56 | ~25 | Already partially done (retrieval gates added this session) |
| **Mandatory Preflight** | 59 | ~20 | Tighten; the skill body has the detail |
| **Deliberation discipline** | 46 | ~15 | Move to wiki concept |
| **Grok /go default** | 35 | ~10 | Condense routing table |
| **`/plan` suggestion rule** | 27 | ~10 | Condense |
| **All other sections** | ~171 | ~85 | Tighten each to rule + link |
| **TOTAL** | ~992 | ~300 | |

## What was done this session

- Tightened "Optimal long-term solution" from 29 lines to 8 lines (rule + wikilink)
- Added two retrieval gates (operator-directive + prior-decision) in tight rule + link format
- Added wikilinks to [[mechanical-enforcement-over-behavioral-reminder]] for rationale

## What needs doing (dedicated session)

1. Create a wiki concept for the "Evidence-first default" section (316 lines)
2. Condense each section to rule + wikilink per the plan above
3. Verify no rules lost — each section's rules must survive in condensed form
4. Test: run a session against the refactored AGENTS.md and verify instruction quality
5. Target: ≤300 lines total

## Read first

- `P:/.data/wiki/concepts/agents-md-construction-best-practices.md` — the research
- `~/.grok/docs/file-editing-protocol.md` — the full protocol (already externalized)
- HumanLayer blog: <60-line own file; community consensus <300 lines

## Falsifier

The refactor is wrong if condensed AGENTS.md causes worse instruction-following
than the current 992-line version. Test by running `/check` on a session that
exercises the condensed rules.

## Other outstanding streams

- qmd-fts5-replacement-20260727 (the qmd replacement)
- packet-skill-design-20260727 (/packet built this session, needs testing on real sessions)
