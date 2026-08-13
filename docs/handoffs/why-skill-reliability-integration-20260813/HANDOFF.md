---
thread_id: 019ffc04-why-reliability-integration
parent_handoff_path: none
current_session_id: 019ffc04-cbca-7372-a622-c31cb9f8f580
current_terminal_id: console_019ffc04
produced_at: 2026-08-13T00:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 5a6cda9f66bb352babcb79b5ad756cc7948a0298
---

# /why reliability fixes + skill-integration adoption gaps

## Objective (one sentence)

Fix `/why`'s root-cause unreliability (verified: 3/8 wrong findings in session 019fa39d) via three structural changes, and address two skill-integration adoption gaps discovered during the diagnosis — all as one bounded `/skill-dev` pass plus two independent quick wins.

## Status

PARTIALLY DONE — Workstream A (design complete, execution deferred to /skill-dev). Task B1 (Option F bridge test) DONE — bridge verified working 2026-08-13. Task B2 (Option G validator) and Workstream A execution remain. This handoff is the executable plan. A fresh session should be able to pick it up and act without re-deriving the analysis.

## Last user message (verbatim)

"Proceed with what you think is best right now."

## Why this exists (the verified problem)

The operator reported: "'/why' is not 100% right all the time. I can't rely on it to find the actual root causes. It sometimes jumps to conclusions or the first plausible reason and doesn't actually dig enough."

This is a documented, named incident, not a vibe. Session `019fa39d` produced 8 findings, 3 of which were wrong (verify receipt not found, multi-terminal isolation violation, close_runner self-referential block). All three were caught only because a separate `/tp` fresh lens (glm-5-2, 24 tool calls reading actual source code) independently verified. The `/why` run self-certified them as correct. Receipt: concept `why-source-code-citation-rule.md` (source: `session-019fa39d (/why RCA on why 3/8 findings were wrong)`).

The diagnosis was verified by a 3/3 lens convergence (inline analysis + gpt-oss-20b fresh subagent + wiki/log evidence). All three independently identified the same root cause: **verification is the model's own job, performed under closure pressure, with no mechanical backstop.**

## Related wiki concepts

- `why-source-code-citation-rule.md` — receipt for the 3/8-wrong incident; source-code citation rule already added
- `convergence-gap-rca-symptom-restatement-toulmin-enforcement.md` — documents that convergence questions are behavioral prompts the LLM answers performatively
- `maker-checker-required-for-enforcement-work.md` — the maker-checker principle already captured for other skills; `/why` hasn't applied it to itself
- `self-reflection-in-llms-fails-without-external-evidence.md` — intrinsic reflection fails; external verification works
- `inter-skill-output-bridges-and-temporal-surfacing-layers.md` — the skill-bridge pattern (already captured)
- `reactive-pattern-matching-and-closure-pressure` — the failure mode `/why` exhibits under pressure
- `mechanical-enforcement-over-behavioral-reminder` — why prose rules don't prevent the problem

## Verified facts (with source paths)

1. **[FACT]** `/why` self-certified 3/8 wrong findings in session 019fa39d. Receipt: `why-source-code-citation-rule.md` frontmatter `source: session-019fa39d`.
2. **[FACT]** The 3 wrong findings were caught only by external `/tp` lens (glm-5-2, 24 tool calls). Receipt: same concept, summary field.
3. **[FACT]** Step 9a (hypothesis diversification) runs AFTER Step 5 fan-out and Step 8 Five Whys (SKILL.md ~lines 280-360). By Step 9a, the model has committed to a causal chain. Receipt: `why/SKILL.md` step ordering.
4. **[FACT]** Default output is a summary table (✅/⚠️/❌/⏭️) with no depth signal (SKILL.md Step 16). A shallow RCA produces the same green-looking table as a deep one. Receipt: `why/SKILL.md` ~line 580+.
5. **[FACT]** The only independent verifier is opt-in `--verify` (SKILL.md ~line 660). Default runs self-certify.
6. **[FACT]** Step 15 feedback-to-wiki loop is effectively dead. `log.md` has zero `/why`-attributed entries across 1,170 concepts. Receipt: `rg -i "why" P:/.data/wiki/log.md` → 0 attributions. `/why` is a pure consumer of the pattern library, never a contributor.
7. **[FACT]** The `/tp`→`/todo` recommendation bridge exists in code (`tp_critique_log.py --recommendations`, added 2026-08-12) but 0 of 21 critique-log entries have recommendations populated. Receipt: fresh-lens subagent (glm-5-1, 15 tool calls) verified `workspace_scanners.py:370-405` reads recommendations; 0 populated.
8. **[FACT]** The handoff schema already carries structured recommendations (task packets: goal, acceptance, falsifier, verification level — `handoff/references/core-fields.md:89-100`; investigation_state for /why: `core-fields.md:214-258`). Only 36% of handoffs use task packets. Receipt: fresh-lens read of core-fields.md.
9. **[FACT]** The session-gate concern (inline Option C) was a phantom problem — the transcript scanner reads `chat_history.jsonl` directly via `--session` flag and catches discussion-only items fine; the session-gate only filters workspace scanners by hunk-log intersection (`todo/SKILL.md:70-82, 89-100`).

## Task packets

### WORKSTREAM A — `/why` reliability fixes (route through `/skill-dev`)

**Why a fresh session:** the `analyst-exhibits-pattern-being-analyzed` risk — editing a skill to fix its own reliability bugs, in the session that diagnosed those bugs under "fix it" pressure, is the same closure-pressure pattern. A fresh session via `/skill-dev` is structurally safer.

#### Task A1: Move Step 9a (hypothesis diversification) to BEFORE Step 5 (fan-out)

- **What:** Reorder so the model generates ≥3 hypotheses before committing to a causal chain and drilling with Five Whys. This prevents the anchoring defense from firing too late (the #1 cause of "jumps to the first plausible reason").
- **Acceptance criteria:**
  1. SKILL.md step order: hypothesis generation precedes fan-out
  2. No internal cross-references break (Step 12 cites Step 9; Step 16 cites all steps; Step 15 cites Step 9 classification) — either keep numbering stable (call the new step "4.5" or "5a") or update all refs
  3. Regression test: re-run the session-019fa39d scenario (8 findings, 3 known wrong) and confirm the fixed `/why` flags or avoids the 3 wrong findings
- **Falsifier:** if a root cause remains correct even when hypotheses are generated first (no change in reported cause across 5 real invocations), the reorder was harmless overhead and can be reverted.
- **Effort:** S (<15 min for the reorder; M if including regression test)
- **Confidence:** H

#### Task A2: Make maker-checker verification the DEFAULT for non-trivial RCAs — WITH a behavior contract

- **What:** For any cause classified architectural/control-plane (Step 9b), or any post-mortem intent, automatically spawn an independent verifier subagent. **The behavior contract (load-bearing — without it, this fix is theater):** the checker does its OWN tool-grounded investigation against the original observation — it does NOT re-read the maker's RCA report and rubber-stamp it. The value in the 3/8 incident came from 24 independent tool calls reading source the maker had only read narratively.
- **Acceptance criteria:**
  1. Checker spawns by default for architectural/post-mortem causes (not opt-in)
  2. Checker prompt explicitly forbids trusting the maker's report; requires independent tool calls
  3. Checker returns VERIFIED / DISPUTED (specific claims wrong) / INCOMPLETE (dimensions missed)
  4. A DISPUTED or INCOMPLETE result blocks the RCA from being reported as final without the dispute surfacing to the operator
- **Behavior contract anti-theater clause:** if the checker makes 0 tool calls and only re-reads the maker's bundle, the verification is invalid — disclose "bundle-only verification, treat as provisional" (mirrors `/tp`'s tool-use disclosure gate).
- **Latency guard:** the trigger is architectural/control-plane classification OR post-mortem, NOT every invocation. Diagnostic intent on implementation/code causes does NOT trigger the checker (keeps quick RCAs fast).
- **Falsifier:** if the checker consistently rubber-stamps (VERIFIED on causes later proven wrong), the contract isn't being enforced — tighten the checker prompt or switch to a stronger cross-family model.
- **Effort:** M (15-60 min)
- **Confidence:** H

#### Task A3: Add a verifiable depth signal to the default output

- **What:** Surface tool-call count per dimension + hypothesis count in the Step 16 summary table. This fixes "I can't tell if it dug enough" — you can distinguish a shallow RCA from a deep one at a glance. The counts are verifiable (the model can't fake them without lying about observable state).
- **Acceptance criteria:**
  1. Default summary table includes a depth row: hypotheses generated, tool calls per dimension, total tool calls
  2. A shallow pass (e.g., 5 tool calls total, 1 hypothesis) is visually distinguishable from a deep pass (20+ calls, 3 hypotheses) in the default output
  3. `--verbose` remains available for full expansion
- **Falsifier:** if the depth signal doesn't correlate with RCA quality (deep-looking runs are as often wrong as shallow-looking ones), the signal is decorative — drop it.
- **Effort:** S
- **Confidence:** H

### WORKSTREAM B — Integration adoption gaps (independent, can ship anytime)

#### Task B1 (Option F): Verify the existing `/tp`→`/todo` recommendation bridge — DONE 2026-08-13

- **STATUS: VERIFIED — bridge works end-to-end.**
- **What was tested:** logged a real critique entry (`26b6f1251aa3`) with 5 `--recommendations` to `tp-critique-log.jsonl`, then ran `scan_functions.py --session <sid> --json` and inspected the output.
- **Result:** all 5 recommendations surfaced as 5 individual `/todo` items with correct severities (3 high, 2 medium). Source field: `tp`. The pipeline `tp_critique_log.py --recommendations` → `scan_critique_log()` → `/todo` items is functional.
- **One display defect found (minor, non-blocking):** the recommendation text is stored in the `title` field prepended with the critique target, producing verbose titles like `"From critique of <target> re: <recommendation text>"` rather than clean one-line items. The text field is empty. This is a formatting issue in `scan_critique_log()` (likely in `workspace_scanners.py`), not a data-loss issue.
- **Resolution of the integration question:** Option A (recommendation ledger) is definitively REJECTED. The existing bridge works. The fix is (1) adoption — more producing skills should emit `--recommendations`; (2) minor display formatting — clean up the title field so recommendation text is the primary scannable line.
- **Remaining from this task:** the display defect is a small code fix in the scanner (extract recommendation text to its own field, or strip the `"From critique of ... re: "` prefix from the title). Optional, non-blocking.

#### Task B2 (Option G): Make handoff task packets a warning-level validator

- **What:** Task packets (field 7: goal, acceptance, falsifier, verification level) already exist in the schema (`core-fields.md:89-100`) and validators exist (`validate_body_sections` in `handoff/SKILL.md:680-730`), but only 36% of handoffs use them. Make task packets a warning-level validator gate (not error — warning, so it surfaces without blocking).
- **Acceptance criteria:**
  1. `validate_body_sections` (or a new validator) warns when a handoff lacks task packets
  2. The warning message names the missing fields
  3. Existing handoffs without task packets trigger the warning (not silently pass)
- **Why this matters:** this is the highest-ROI structural fix for the "thin transfer" problem. The handoff schema already carries the richness; it's just not enforced. One validator change makes the existing persistence layer carry what it's designed for.
- **Falsifier:** if warning-level enforcement doesn't move task-packet adoption above 60% within 2 weeks, escalate to error-level or investigate why authors skip the fields.
- **Effort:** S
- **Confidence:** H

### WORKSTREAM C — `/rca` alias (ALREADY SHIPPED this session)

- **What:** Add `/rca` as an alias for `/why` (same pattern as `/research`→`/www`, `/redteam`→`/risk`). Keeps `/why` working; adds a more precise name for the ITSM/event-management context.
- **Status:** SHIPPED — `~/.grok/skills/rca/SKILL.md` created this session. Run `index_skills.py` to register.

## Open decisions (for the next session or operator)

1. **Should non-`/tp` skills (`/why`, `/review`, `/risk`) write to the critique log or their own JSONL?** This is the volume question the fresh lens flagged: the 21-entry count is a floor, not a ceiling, because producing skills don't log. Measure over 1-2 weeks: if >10 cross-skill recommendations/week are lost, extend the bridge. If <5, the existing bridge is sufficient. **Decision gate: measurement, not architecture.**

2. **Should maker-checker (Task A2) fire on model-behavior causes too, or only architectural?** Model-behavior mitigations "may decay under pressure" — the checker could verify the mitigation actually fired. But this doubles checker invocations. Defer until A2 ships and measure.

3. **Step 15 feedback-to-wiki loop revival (deferred from Tier 2).** Once A2 (maker-checker) ships, the checker's findings are the input stream for Step 15. Sequence: A2 first, then revive Step 15 to capture what the checker finds. Not in this handoff's scope — separate handoff after A2 validates.

## What was explicitly DEFERRED (and why)

- **Tier 2/3 `/why` defects** (performative Five Whys, lexical Step 6 trigger, fan-out floor, `--quick` bypass, Step 14 overload, Step 15 single-reviewer SPOF): once Task A2 (maker-checker) ships, the checker independently catches performative chains and shallow fan-out. Fixing them separately in the maker is redundant. Defer to a follow-up handoff after A2 validates.
- **Option A (recommendation ledger):** rejected as a new build; the bridge exists. Verify first (Task B1), then decide whether to extend to other skills based on measured volume.
- **Options B, C, D, E:** rejected (see "Rejected alternatives" below).

## Rejected alternatives (with rationale)

- **Option B (enhance handoff schema for structured recommendations):** REJECTED — the schema already supports it (`core-fields.md:89-100, 214-258`). Problem is adoption (36%), not schema. Fixed by Task B2.
- **Option C (fix /todo session-gate for discussion-only sessions):** REJECTED — phantom problem. The inline lens conflated the transcript scanner (session-scoped via `--session`, catches discussion items) with the workspace scanner session-gate (hunk-log-based, filters shared-state findings). The transcript scanner already does what Option C proposed. Fresh-lens receipt: `todo/SKILL.md:70-82, 89-100`.
- **Option D (build a discussion-to-handoff bridge skill):** REJECTED — `/todo` already has handoff-spinning (Step 1e, `todo/SKILL.md:393-455`). Another skill to remember is the opposite of reducing cognitive load.
- **Option E (write better handoffs manually):** REJECTED — relies on operator memory; the fix is enforcing existing validators (Task B2), which is structural.
- **Option A as originally proposed (new recommendation_ledger.jsonl):** REJECTED as new build; REPLACED by Task B1 (verify existing bridge) + the measurement-gated decision in Open Decision 1.
- **Replace `/why` wholesale:** REJECTED — the skill's bones are sound (evidence tiers, pattern-library integration, six-layer divergence model). Defects are in enforcement, not methodology. Rip-and-replace loses the 1,170-concept library `/why` consumes at Step 0.5.

## Falsifier for this handoff (what would make it wrong or obsolete)

- If Task A2 (maker-checker) ships and the checker consistently rubber-stamps wrong causes → the contract is unenforced; the fix is theater. Tighten the checker prompt or switch model.
- If Task A1 (step reorder) ships and causes no measurable improvement in RCA quality across 5 real invocations → the anchoring diagnosis was wrong; the reorder was harmless overhead.
- If Task B1 (bridge verification) reveals the bridge is broken in code → the integration problem is real and architectural, not operational; escalate to a design pass.
- If the operator's actual workflow produces <5 cross-skill recommendations/week → Open Decision 1 resolves to "existing bridge sufficient," and no extension work is needed.

## Suggested skills for the next session

- **`/skill-dev`** for Workstream A (the `/why` reliability fixes). This is the native tool for "is this skill earning its keep and how do I make it better." Feed it Tasks A1-A3 + the 3/8 receipt + the behavior contract for A2.
- **`/check`** after A1-A3 ship: verify the regression test (session-019fa39d scenario) passes.
- **`/wiki`** if the maker-checker-for-RCA pattern proves generalizable — capture it as a concept so other analysis skills (`/risk`, `/review`) apply it to themselves.

## Read-first list (for a cold-start session)

- `~/.grok/skills/why/SKILL.md` — the skill being fixed (710 lines, v3)
- `~/.grok/skills/tp/SKILL.md` — the critical-friend skill (for the maker-checker contract model, Step 3 verification synthesis)
- `~/.grok/skills/handoff/references/core-fields.md` — task packet schema (fields 7, investigation_state)
- `~/.grok/skills/handoff/SKILL.md` — validators (`validate_body_sections`, line 680-730)
- `~/.grok/skills/todo/SKILL.md` — scanner architecture (lines 70-82 transcript, 89-100 session-gate, 393-455 handoff-spinning)
- `~/.grok/skills/tp/__lib/tp_critique_log.py` — recommendation bridge (lines 60-98)
- `P:/.data/wiki/concepts/why-source-code-citation-rule.md` — the 3/8 receipt
- `P:/.data/wiki/concepts/maker-checker-required-for-enforcement-work.md` — the principle to apply
- `P:/.data/wiki/concepts/convergence-gap-rca-symptom-restatement-toulmin-enforcement.md` — why self-certification fails
