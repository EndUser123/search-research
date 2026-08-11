# Handoff: /maintain-ifile skill + scatter-gather pattern + AGENTS.md optimization

## Status: OPEN — skill built, first optimization run complete, pattern captured

## Session: 019fe3ff-afbc-71c1-b2a3-3cfbccfd2bc7
## Last updated: 2026-08-11

## Objective

Create the best possible skill for optimizing AGENTS.md and CLAUDE.md files. This evolved from a manual optimization attempt into a full skill design with /tp critique, web research, and a generalizable concurrency pattern.

## Work completed this session

### 1. `/maintain-ifile` skill built (v1.0)
- **Path:** `~/.grok/skills/maintain-ifile/SKILL.md` (406 lines)
- **Design:** 4-phase pipeline (AUDIT → CLASSIFY → EXTRACT → VERIFY)
- **Key innovation:** 5-bucket classifier with binding awareness (not binary litmus test)
  - A: lossless+binding, B: lossy-rationale, C: lossless-isolated, D: heuristic-keep-flag, E: scope-conflict
- **Execution model:** batched loop with diminishing-returns stopping (< 10 lines/pass)
- **Scatter-gather Phase 2:** parallel classification for files >500 lines (temp files as coordination boundary, serial gather+write)
- **/tp critique:** 6 findings, all CONFIRMED and integrated (retrieval verification, sync drift detection, 5-bucket rubric, round-trip log, enforcement hierarchy routing, no-op defaults to KEEP)
- **Wired to /maintain:** fleet_health.py tip now points to /maintain-ifile (not /config-audit); composition table documents DIAGNOSE→ACT relationship
- **Commits:** `6aec633` (initial), `b873435` (rename), `56050dc` (/maintain wiring), `2e02d15` (loop model), `ea3a8fb` (scatter-gather)

### 2. AGENTS.md optimization (background subagent, 10 passes)
- **Result:** 1632 → 1363 lines (−269, −16.5%)
- **Stopping reason:** diminishing returns (last 3 passes: 16, 2, 0 lines)
- **1 new wiki concept:** `[[claims-require-receipts-worked-examples]]`
- **30+ sections condensed inline** (reference incidents, rationale, citations compressed; firing rules preserved)
- **Remaining 1363 lines are largely firing rules** — file editing protocol, action manifest table, push policy
- **Subagent commits:** `dc460b9` through `3730e4a` (10 commits in ~/.grok, 1 in P:/)

### 3. Scatter-gather pattern captured as wiki concept
- **Path:** `P:/.data/wiki/concepts/scatter-gather-for-single-artifact-parallel-analysis.md`
- **Pattern:** parallel read-only analysis → temp files → serial gather+write
- **Applies to:** `/go` discovery, `/refine`, `/design`, `/check` (not yet cross-referenced from those skills)
- **Validated** and committed (`64ffcc6`)

### 4. Batch accounting gate (earlier in session)
- Added to `~/.grok/AGENTS.md` — prevents silent drift when batch items are deferred
- Requires terminal status (DONE/DEFERRED) for every authorized batch item

## Open work / remaining items

### A. Cross-reference scatter-gather pattern from other skills (NEXT)
The wiki concept `[[scatter-gather-for-single-artifact-parallel-analysis]]` documents the pattern but the skills that should use it don't reference it yet:
- `/go` H3-discover: could use scatter-gather for parallel codebase analysis
- `/check`: multi-concern verification could parallelize concerns
- `/refine`: could fan out independent analysis aspects
- `/design`: reviewer could fan out to specialists
- Each skill needs a one-line pointer in its SKILL.md

### B. AGENTS.md further optimization (LATER — diminishing returns)
- 1363 lines remains above the <1000 target
- The remaining content is mostly firing rules (bucket A/D) that can't extract without losing binding
- Further reduction requires structural changes (e.g., converting prose rules to hooks) not just extraction
- The `/maintain-ifile` scatter-gather mode (Phase 2) would speed up the next optimization run by parallelizing classification

### C. Retrieval verification gap (LATER)
- The /tp critique flagged that syntactic verification (needle-grep) doesn't test whether extracted rules are *retrieved* when needed
- The skill documents retrieval testing in Phase 4 Layer 2 but it's expensive
- No retrieval test has been run against the extracted `[[claims-require-receipts-worked-examples]]` concept

### D. Stop-hook receipt-scope binding (LATER)
- The session started with an investigation of receipt-identity-provenance (from the compaction summary)
- This is a separate workstream that predates the maintain-ifile work

## Key decisions made

1. **New skill over extending config-audit** — operator said "create the best skill," which means clean-slate design incorporating all existing strengths
2. **5-bucket classifier over binary litmus test** — handles rule+incident binding that real AGENTS.md rules have
3. **Scatter-gather over serial-only Phase 2** — operator correction: "how can we work in parallel without breaking agents.md?" led to the temp-file coordination boundary design
4. **Loop with diminishing-returns stopping over fixed-pass count** — adapts to file size and content density
5. **No-op defaults to KEEP+flag, never batch delete** — operator correction on sign-off timidity
6. **`/maintain-ifile` over `/instruction-health`** — operator recall: "I'll never remember it"

## Files modified/created

- `~/.grok/skills/maintain-ifile/SKILL.md` (NEW, 406 lines)
- `~/.grok/skills/maintain-ifile/extraction-log.jsonl` (NEW)
- `~/.grok/skills/maintain/__lib/fleet_health.py` (MODIFIED — tip routing)
- `~/.grok/skills/maintain/SKILL.md` (MODIFIED — depends_on, composition table)
- `~/.grok/AGENTS.md` (MODIFIED — batch accounting gate + 269 lines extracted by subagent)
- `P:/.data/wiki/concepts/scatter-gather-for-single-artifact-parallel-analysis.md` (NEW)
- `P:/.data/wiki/concepts/claims-require-receipts-worked-examples.md` (NEW, by subagent)
