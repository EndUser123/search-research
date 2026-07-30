---
thread_id: problem-prediction-skills-20260727
parent_handoff_path: none
current_session_id: 019fa276-89c7-7310-b882-096cf67652cf
produced_at: 2026-07-28T02:55:00Z
status: ready-to-implement
handoff_type: investigation
---

# Problem prediction research → 6 actionable skills/improvements

## Objective

The operator asked: "did any of our problem prediction research result in
ideas we could usefully turn into a skill, or a repo, or ideas on how to
improve an existing skill?" The research produced 6 items. The operator said
"do them all." This handoff covers the 4 items that need their own focused
session; 2 items (#3 sensitivity sweep plan, #4 cc-thinking-skills eval)
were started in the originating session.

## The 6 items (priority order)

### Item 1: Build `/fmea` skill — HIGHEST PRIORITY

**What:** a skill that takes a pipeline or system description and produces
a structured FMEA (Failure Modes and Effects Analysis): for each component,
enumerate failure modes, rate severity × occurrence × detection, produce
RPN (Risk Priority Number).

**Why:** our pre-mortem (`/red-team`, `/tp`) catches narrative-level
failures. FMEA catches **component-level** failures the narrative frame
misses. This session's cluster-filter bug is the canonical example:
"cluster_transcripts.py reads from shared directory → failure mode: reads
other notebooks' files → severity: high → occurrence: certain → detection:
low → RPN: high."

**Reference repos:**
- [FMEA Risk Analysis](https://mcpmarket.com/tools/skills/fmea-risk-analysis-1) — Claude Code marketplace skill
- [LLMRiskAnalyzer](https://github.com/YuchenXia/LLMRiskAnalyzer) — FMEA for LLM systems

**Design:** the skill scans the target pipeline's scripts, identifies I/O
boundaries (shared directories, external APIs, state files, caches), and for
each boundary generates the FMEA table. Output is a markdown table with RPN
scores, sorted by priority.

**Scope:** ~200 lines. New skill at `P:/.agents/skills/fmea/SKILL.md` +
`scripts/fmea_scan.py`.

**Acceptance criteria:**
- Given a pipeline path (e.g., `.agents/skills/nlm-to-wiki/scripts/`),
  produces an FMEA table covering each script's I/O boundaries
- Each failure mode has: component, failure mode, cause, effect, severity
  (1-10), occurrence (1-10), detection (1-10), RPN (S×O×D)
- Sorted by RPN descending
- Would have caught the cluster-filter bug (shared directory, no filter)

### Item 2: Per-step receipts in `/www` and `/handoff`

**What:** each skill step writes a receipt with step-specific evidence
(not just "completed: true"). A Stop hook checks the receipt chain.

**Why:** `/www` Phase 3 was skipped twice this session. The Proof-or-Stop
paper (arxiv 2607.14890) proved enforcement is the mechanism: 14 amplified
cells with advisory review vs 2 with enforced gates.

**Design:** per `P:/.data/wiki/concepts/skill-step-receipts-checked-by-hooks.md`
(revised version with Proof-or-Stop evidence):

For `/www`:
- Phase 1 receipt: `{concepts_found: N, gaps: N, assumptions_to_check: N}`
- Phase 2 receipt: `{sources_cited: N, disconfirmation_queries: N}`
- Phase 3 receipt: `{concept_path: "...", validation: "PASS", lines: N}`

For `/handoff`:
- Write receipt: `{handoff_path: "...", bytes_written: N}`
- Gate predicate: `file_exists AND bytes > 500`

**Stop hook extension:** reads `.artifacts/<session>/skill-receipts/`,
evaluates each receipt's gate predicate, blocks on failure.

**Scope:** ~15 lines per skill step (receipt writer) + ~40 lines Stop hook.

**Acceptance criteria:**
- `/www` cannot exit without a Phase 3 receipt showing `validation: "PASS"`
- `/handoff` cannot exit without a write receipt showing `bytes > 500`
- The Stop hook blocks with a specific message naming the missing step
- A "deferred" escape hatch exists (explicit reason field)

### Item 3: Sensitivity sweep — STARTED (plan written)

**Plan:** `docs/handoffs/nlm-to-wiki-v3-refactor-20260727/sensitivity-sweep-plan.md` (recovered from
P:/tmp/ which was deleted; preserved in handoff directory) — 7 parameters × 4 values = 28 runs.
Measurement via existing `report.py --json`. Only the sweep driver
(`sensitivity_sweep.py`, ~100 lines) needs writing.

**When to run:** after the bulk run completes (transcripts cached).

### Item 4: Evaluate `cc-thinking-skills` — EVALUATION PRODUCED (never written to file)

**Status:** the subagent (`019fa6da-b82a-73d3-baae-684d7c44068e`) was dispatched as
`explore` type (read-only, no write tool). It produced the evaluation as a chat response
but could not write the file. **Recovered 2026-07-29** from the subagent's transcript
to `docs/handoffs/problem-prediction-skills-20260727/cc-thinking-skills-evaluation.md`
(17,120 chars).

**Summary of findings:** 28 mental-model frameworks; 14 already have workspace equivalents,
8 missing and worth porting. Prioritized list of 9 framework categories worth porting
(Reference-Class Forecasting, External-Validity Audit, Probabilistic Calibration,
Second-Order Thinking, full ACH matrix, FMEA, Sensitivity Analysis, Inversion-as-default,
Hanlon/Chesterton filters) plus 3 deferral categories.

**Next step:** read the transcript, decide which frameworks to port as
`/tp` domains or `/red-team` specialist lenses.

### Item 5: Tree of Thoughts for adaptive `/red-team`

**What:** ToT (7,900 citations) does deliberate tree search over reasoning
paths. Applied to `/red-team`: instead of 8 fixed specialist lenses,
generate adaptive lenses based on the target's specific failure surface.

**Repo:** [github.com/kyegomez/tree-of-thoughts](https://github.com/kyegomez/tree-of-thoughts)

**Design:** `/red-team --adaptive` mode. For the target diff/plan, the LLM
generates 5 candidate specialist lenses most relevant to this specific
change, self-evaluates each, and dispatches the top 3-5.

**Scope:** ~150 lines as a new mode in the existing `/red-team` skill.

### Item 6: Decision Graph — DEFERRED

**What:** model workspace decisions as first-class graph nodes (owner,
trigger, blockers, evidence) rather than documents.

**Why deferred:** largest scope (new data model). Current document-based
tracking (handoffs + wiki concepts) works for our decision volume. Revisit
when the workspace exceeds ~500 concept pages or when cross-reference
queries become painful.

## Research sources

All findings are in the wiki:
- `systematic-problem-anticipation-methods-and-existing-tools.md` — FMEA/MCTS/LATS survey
- `skill-step-receipts-checked-by-hooks.md` — per-step evidence-gated control (Proof-or-Stop)
- `queue-of-work-pattern-for-nlm-to-wiki.md` — parallel worker architecture
- `shared-directory-contamination-pattern.md` — the bug FMEA would have caught

## Recommended execution order

1. Read the cc-thinking-skills evaluation (Item 4, may be complete)
2. Build `/fmea` skill (Item 1) — highest-value, catches real bugs
3. Implement per-step receipts (Item 2) — proven by Proof-or-Stop ablation
4. Write sensitivity sweep driver (Item 3) — plan exists, just needs code
5. ToT for adaptive red-team (Item 5) — medium-term improvement
6. Decision graph (Item 6) — long-term, defer
