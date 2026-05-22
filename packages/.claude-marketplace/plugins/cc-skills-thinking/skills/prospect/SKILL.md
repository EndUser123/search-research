---
name: prospect
description: Mines wiki vault, memory files, and knowledge sources for actionable improvements, architectural gaps, and ideas applicable to the current environment. Produces a prioritized prospect report.
version: 1.0
category: engineering
triggers:
  - /prospect
  - /prospect [query]
  - "what can we improve?"
  - "any good ideas in the wiki?"
  - "what's missing from our setup?"
allowed_tools: ["Read", "Bash", "Grep", "Glob", "mcp__plugin_search-research_sr__search-research__unified_search"]
---

# Prospect — Knowledge Miner (/prospect)

**Lead Idea Prospector.** Mines the workspace's own knowledge sources for improvements, architectural gaps, and techniques worth borrowing — ranked by applicability to the current environment.

## Core Directive

Find ideas that are **actionable right now** vs. **interesting to note**. An actionable idea has: (a) a clear problem it solves, (b) a named target in this codebase, and (c) no fundamental rearchitecture required. Surface the best 5–10 per run.

## Sources & What to Extract

### Phase 1: Knowledge Sources (Discovery)

#### 1. Wiki Vault — `P:/.data/wiki/`

**High-value extractions** (scan in priority order):
- `concepts/*.md` — "NEXT" sections, verification checkboxes not yet checked, "Bridge-to-Impl" callouts
- `cognitive/*.md` — cognitive patterns with applicability to our hooks/skills
- `hooks/*.md` — existing hook patterns, known limitations, "why this fails" sections
- `sources/spec-*.md` — recently ingested specs (last 30 days) with unfulfilled "Next" actions
- `sources/research/*.md` — research with concrete findings not yet implemented
- `proposals/*.md` — accepted proposals with unimplemented steps

**What to skip:**
- Background reference material (architecture overviews, glossary pages)
- Archived/deprecated content
- Content older than 90 days unless explicitly tagged "NEXT: implement"

### 2. Memory Files — `C:\Users\brsth\.claude\projects\P--\memory\`

**High-value extractions:**
- MEMORY.md — pending tasks, open feedback items, unresolved corrections
- Topic files with `pending` or `TODO` in their body
- Files with `**READ FIRST**` markers (these are load-bearing reminders we may be violating)
- `feedback_*.md` — explicit corrections and rules with "why" and "how to apply"

**What to skip:**
- Stable reference content (conventions, tool patterns)
- Completed task records

### 3. Vault Log — `P:/.data/wiki/log.md`

**High-value extractions:**
- INGORE/ARCHIVE patterns — what we've deliberately rejected (often has useful reasoning)
- Recently ingested sources with "Next: /sdlc:init" that were never actioned
- Gaps between "interesting" and "implemented" over time

### 4. Pending Task List

Scan task output for items marked `pending` that relate to environment improvement (hook tuning, skill gaps, diagnostic coverage).

## Classification Rubric

Assign one class to each finding:

| Class | Signal | Actionability |
|-------|--------|---------------|
| **GAP** | A missing thing we should have | → file a task or add to backlog |
| **UNFULFILLED** | "Next" callout never acted on | → create implementation plan |
| **BORROW** | Technique from another workspace that fits here | → write adapter spec |
| **REGRESSION** | A historical correction we may be violating | → check current state against rule |
| **REFERENCE** | Useful context for a future decision | → note in findings, no action |

## Workflow

### Phase 0: Semantic Scout (1 search-research call)

1. **With argument** — `unified_search` with mode `unified` on the query:
   - `"[query] Claude Code hook OR skill OR memory OR wiki"` — semantic across wiki + web
   - e.g., `/prospect self-healing hooks` → search for self-healing patterns, hook resilience, memory decay
2. **Without argument** — default query: `"Claude Code hook architecture improvement skill memory pipeline"` — broad semantic scan to surface what the literal grep pass might miss

Use the top 5–8 results to seed the next phase. They are the seed bank, not the findings — confirm applicability before surfacing.

### Phase 1: Fast Scan (1–2 tool calls)

1. **Wiki: "NEXT" hunt** — Grep `concepts/` and `cognitive/` for `→ /` or `Next:` patterns. Read the top 10 files returned.
2. **Memory: pending items** — Read MEMORY.md, extract pending tasks and open feedback.
3. **Snapshot handoff** — Read the V2 handoff envelope from `P:/.claude/.artifacts/{terminal_id}/snapshot/` via `SnapshotFileStorage` to get current session goal and pending work. Flag any goals that are stale (no pending work but active goal).

### Phase 2: Canonical Source Scan (NEW — parallel subagents when sources > 5)

**Purpose:** Detect drift between what's documented and what's actually implemented.

Run `python skills/prospect/scripts/phase2_scan.py` first to count sources.
- If total source count **≤ 5** → run sequentially (no subagents, avoid token overhead)
- If total source count **> 5** → dispatch parallel subagents (one per scanner below)

**Scanners (run in parallel when >5 sources):**

| Scanner | What it checks |
|---------|---------------|
| `hooks_doc_vs_code` | `P:/.data/wiki/hooks/*.md` vs `P:/.claude/hooks/*.py` — doc/code drift |
| `skill_md_vs_scripts` | Skill SKILL.md step sequences vs actual script files — missing scripts, orphaned scripts |
| `phase_ledger` | `~/.claude/.state/enforce/` — phases that are always blocked or never complete |
| `snapshot_handoff` | `P:/.claude/.artifacts/{terminal_id}/snapshot/` — V2 handoff goal stall, missing pending work |
| `compilation_state` | `P:/.claude/.artifacts/gitpack_full.md`, `doc-compiler_full.md` — uncommitted/stuck artifacts |

**Drift findings are highest priority** — doc/code mismatch means someone acted on outdated information.

**Output:** `Phase2Report` with findings typed as: `DRIFT | REGRESSION | UNFULFILLED | GHOST | BORROW | PRESENT`

### Phase 3: Targeted Read (3–5 tool calls)

4. For each "NEXT" found in Phase 1, read the parent file to confirm actionability.
5. Check log.md for recently rejected/archived ideas with useful reasoning.
6. Scan task list for pending improvement tasks.
7. Cross-reference Phase 2 drift findings with Phase 1 wiki findings — the same item appearing in both is high-confidence DRIFT.

### Phase 4: Classification & Ranking

6. Classify each finding by rubric above.
7. Rank by:
   - **Broken tool / blocking GAP** (anything that prevents a skill from loading) → #1 priority
   - Then: actionability (GAP/UNFULFILLED > BORROW > REGRESSION > REFERENCE)
   - Then: recency (≤90 days), specificity (named file/function beats vague "improve X")
   - **Skip**: `/sdlc:init` triggers — these are ceremonial hooks that don't move work forward; surface only if the initiation itself is broken
   - **Split** GAPs by estimated implementation size: small (1–2 files, <1h) vs large (multi-file, >1h) — small ones rise in priority

## Output Format

```
## Prospect Report — {date}

### Actionable (do this week)
| # | Finding | Source | Target | Class | TOOLS_VERIFIED | Est. Size | Action |
|---|---------|--------|--------|-------|-----------------|-----------|--------|
| 1 | /s broken: constitutional filter import fails | run_heavy.py:1416 | skills/s | GAP | N (import verified) | small | stub or wire __csf filter |

### Interesting (note for later)
| # | Finding | Source | Why interesting |
|---|---------|--------|----------------|

### Regressions to check
| # | Rule | Memory source | Verify against |
|---|------|---------------|----------------|
| 1 | fact-guard PreToolUse: no bare literals | feedback_no-bare-literals.md | Stop.py |

### Reference (context for future decisions)
...

Sources scanned: {n} files from wiki, {n} memory files, log.md, tasks
```

**Column definitions:**
- `TOOLS_VERIFIED`: whether the finding was confirmed by running the broken tool/script, not just reading docs — `Y` = confirmed at runtime, `N` = doc-only inference, `N/A` = no tool involved
- `Est. Size`: `small` (<1h, 1–2 files) | `large` (>1h, multi-file or rearchitecture)

## Quality Gates

- [ ] All findings cite a specific file path or source
- [ ] Each finding names a concrete target (file, function, hook)
- [ ] No finding is older than 90 days unless tagged `NEXT: implement`
- [ ] Output includes at least one GAP or UNFULFILLED finding (otherwise note "environment is current")
- [ ] REGRESSION findings include the specific rule text to check

## Scope Limits

- Do NOT search for generic "best practices" or "patterns" without a named target
- Do NOT recommend rearchitecture unless the finding explicitly names a failure that rearchitecture solves
- Maximum 10 findings in the Actionable section (prioritize ruthlessly)
- If no actionable findings: say "no immediate gaps found" and list 3–5 BORROW candidates instead

## Metadata
- **Target OS**: Cross-platform (Windows primary)
- **Tone**: Clinical, opinionated — "this is worth doing" not "here's what exists"
- **Efficiency**: <10 tool calls total; <300 tokens per finding
- **Recency guard**: Default to last 90 days; older only if tagged NEXT