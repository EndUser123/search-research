---
title: "Scatter-gather for single-artifact parallel analysis: temp files as coordination boundary"
created: 2026-08-11
source: session-019fe3ff (/maintain-ifile skill design + operator question on generalizing the pattern)
tags: [parallel-agents, scatter-gather, single-artifact, temp-files, coordination-boundary, serial-writes, map-reduce, concurrency, transferable-pattern]
summary: >
  When multiple workers must analyze the same single file (not independent
  files), worktrees don't solve the concurrency problem — even non-overlapping
  edits shift line numbers and produce broken merges. The scatter-gather
  pattern solves this: parallel read-only analysis writes to temp files, a
  serial gather step merges results and applies changes with correct line
  numbers in one pass. The temp file is the coordination boundary. Applies
  to any skill where N workers analyze one shared artifact and the write
  step is inherently serial.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - "AWS Prescriptive Guidance — Parallelization and scatter-gather patterns (2026)"
  - "Tian Pan — Two Writers, One Working Tree: Concurrency Control for Human-Agent Co-Editing (Jul 2026)"
  - "arXiv 2606.00953 — When Parallelism Pays Off: Cohesion-Aware Task Partitioning (2026)"
relations:
  - target: wiki/concepts/parallelizing-design-doc-generation-what-works.md
    type: refines
  - target: wiki/concepts/agents-md-construction-best-practices.md
    type: related
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: related
  - target: wiki/concepts/multi-terminal-isolation-stale-data-immunity.md
    type: related
---

# Scatter-gather for single-artifact parallel analysis

## Decision context

**Why this was needed:** during `/maintain-ifile` skill design, the question
arose: can classification of AGENTS.md sections run in parallel to speed up
the optimization pipeline? The initial answer was "no — concurrent writes to
AGENTS.md are the #1 documented failure on this host." But that conflated
serial writes (correct) with serial everything (wrong). Classification is
read-only and parallelizes fine. The operator then asked: does this apply to
`/go` and other skills? The answer is yes — it generalizes into a
workspace-level pattern.

## The problem: worktrees don't solve single-file parallel work

Worktrees solve **multi-file** parallelism: each agent touches different
files → clean merge. For a **single continuous file** like AGENTS.md, even
non-overlapping edits conflict because the file structure changes. Extracting
section A shifts all line numbers for section B. Two worktrees extracting
sections A and B will both "succeed" but produce a merge where B's line
references are wrong. The merge is guaranteed to need manual resolution —
which defeats the parallelism.

Source: Tian Pan (Jul 2026) documents this directly: "Two writers touching
the same module will still collide — you are not eliminating conflicts, you
are converting them from data loss into a review step." For multi-file work,
that conversion is acceptable. For single-file work, every conflict is
guaranteed, so the conversion buys nothing.

## The solution: scatter-gather with temp files as coordination boundary

The scatter-gather pattern (AWS Prescriptive Guidance, 2026) separates
analysis from writes:

```
SCATTER (parallel, read-only on the shared artifact):
  Worker 1: analyze aspect A → write to P:/tmp/analysis-1.json
  Worker 2: analyze aspect B → write to P:/tmp/analysis-2.json
  Worker 3: analyze aspect C → write to P:/tmp/analysis-3.json

GATHER (serial, one writer):
  Read all temp files → merge analysis
  Detect cross-section dependencies the partition missed
  Apply changes SERIALLY to the shared artifact
  Verify integrity
```

**Why this works:**
- Analysis is read-only — no concurrent-write hazard
- Workers can't corrupt the shared artifact because they never write to it
- The gather step detects partition errors before any writes happen
- The serial apply step preserves the one-writer invariant
- Temp files provide correct line numbers — the gather step sees the original
  file state, not a mid-edit state

## When this pattern applies (three conditions)

All three must hold:

1. **Multiple workers analyze the same single artifact** (not independent files)
2. **Analysis is read-only** (no writes to the artifact during analysis)
3. **The write step is inherently serial** (one writer, line-number sensitivity)

If only conditions 1-2 hold but writes can be parallelized (different files),
use worktrees instead. If condition 3 doesn't hold (writes are independent),
use fan-out + collect instead.

## The partitioning rule

Two sections can be analyzed by different workers only if neither references
the other. Sections that cross-reference each other must be in the same
partition, or the analysis loses the binding.

Source: arXiv 2606.00953 (2026) — "cohesion-aware task partitioning" shows
that parallelism pays off only when subtasks are independent. For files with
high cross-reference density, partition carefully or fall back to serial.

## Pattern classification (which solution for which problem)

| Problem shape | Solution | Example skills |
|--------------|----------|---------------|
| Parallel work on **different files** | Worktrees | `/go` implementation, `/grok-parallel` |
| Parallel analysis of **same file** | Scatter-gather temp files | `/maintain-ifile`, `/go` discovery, `/review`, `/check` |
| Serial work on **same file** | Lock + serial | `/ship-py` phases, `/close` gates |
| Independent items | Fan-out + collect | `/todo`, `/skill-prune` |

## Skills that already use this pattern (implicitly)

| Skill | How it uses the pattern | What it could improve |
|-------|------------------------|----------------------|
| `/tp` | Fresh subagent writes critique → parent synthesizes | Already correct — temp output = temp file |
| `/review` | Specialists write to FINDINGS.md → synthesizer merges | Already correct — findings = temp files |
| `/maintain` | `fleet_health.py` ThreadPoolExecutor → single findings JSON | Already correct — parallel checks, serial write |
| `/www` | Research subagents → ledger files → synthesis | Already correct — ledger = temp file |

These skills implement the pattern correctly but don't name it or share a
common mechanism. Each reinvents the coordination boundary.

## Skills that would benefit from adopting it

| Skill | Current gap | Opportunity |
|-------|------------|-------------|
| `/go` | Discovery phase (H3-discover) analyzes codebase serially | Scatter-gather: N subagents analyze different aspects of same files → temp findings → serial merge |
| `/refine` | Single-agent analysis of codebase to tighten handoff | Fan out: one agent checks tests, one checks imports, one checks docs — all read-only |
| `/design` | Design-doc reviewer is serial | Reviewer could fan out to N specialists (security, performance, API) each writing to temp files |
| `/check` | Multi-concern verification runs concerns serially | Each concern (tests, scope, runtime, dirty-tree) is independent read-only check on same state |

## What this means for our workspace

1. **Name the pattern.** Skills that implement scatter-gather should reference
   this concept so the pattern is discoverable, not reinvented per skill.

2. **The temp file is the coordination boundary.** All parallel workers write
   to `P:/tmp/<task>-<N>.json`. The gather step reads these files, never the
   shared artifact directly during analysis.

3. **The serial-write invariant is non-negotiable on this host.** The
   multi-terminal isolation rules exist because concurrent writes to shared
   files cause silent corruption (0-byte truncation, sibling-session
   collision). Scatter-gather preserves the invariant by construction — only
   the gather step writes, and it writes serially.

4. **Partition by independence, not by line range.** When partitioning a file
   for parallel analysis, group sections by cross-reference density, not by
   arbitrary line boundaries. Two sections that reference each other must be
   in the same partition.

5. **Worktrees remain correct for multi-file work.** This pattern does NOT
   replace worktrees — it solves a different problem. Use worktrees when
   agents touch different files. Use scatter-gather when agents analyze the
   same file.

## Falsifier

This pattern is wrong if:
- A better coordination mechanism emerges (e.g., real-time collaborative
  editing like Google Docs for code — currently doesn't exist for LLM agents)
- The single-writer invariant is relaxed (e.g., CRDT-based file editing
  proves reliable for code — no evidence this works yet)
- The overhead of temp files + gather exceeds the parallelism speedup for
  all realistic file sizes (measurable: if gather+merge > serial-classify
  time for files under 1000 lines, the pattern doesn't pay off)
- Worktree merge tooling improves to the point where single-file merges are
  reliable (line-number-aware semantic merge — not yet available)

## Sources

- [AWS Prescriptive Guidance — Parallelization and scatter-gather patterns](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/parallelization-and-scatter-gather-patterns.html) (2026) — scatter-gather cognition pattern, agent parallelization architecture
- [Tian Pan — Two Writers, One Working Tree](https://tianpan.co/blog/2026-07-02-two-writers-one-working-tree) (Jul 2026) — concurrency control for human-agent co-editing, worktree limitations for single-file work
- [arXiv 2606.00953 — When Parallelism Pays Off](https://arxiv.org/abs/2606.00953) (2026) — cohesion-aware task partitioning for multi-agent coding
- [[parallelizing-design-doc-generation-what-works]] — related pattern for parallel document generation (different problem: generating content vs analyzing existing content)
- [[code-orchestrates-model-judges-skill-scale]] — fan-out cost overhead and mitigation

## Receipts

- `/maintain-ifile` scatter-gather design: `~/.grok/skills/maintain-ifile/SKILL.md` lines 210-277 (Scatter-gather mode section, added commit `ea3a8fb`)
- `/maintain` ThreadPoolExecutor (existing parallel pattern): `~/.grok/skills/maintain/__lib/fleet_health.py` function `run_all_checks()` (uses `ThreadPoolExecutor` for 15 parallel health checks, writes single findings JSON)
- `/tp` subagent synthesis (existing pattern): `~/.grok/skills/tp/SKILL.md` § "Core insight" — fresh subagent generates critique, parent verifies and integrates
- `/review` specialist findings merge: `~/.grok/skills/review/SKILL.md` — specialists write to FINDINGS.md, synthesizer merges (confirmed by skill description, not line-level inspection)
- Claims that worktrees don't solve single-file parallel work: sourced from Tian Pan article (external URL above), not local implementation — this is a field-level finding, not a local mechanism claim

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[parallelizing-design-doc-generation-what-works]]
- [[tp-parallel-improvement-solution-space]]
- [[agent-reliability-patterns-and-production-validation]]

