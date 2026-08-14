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

DONE — all workstreams shipped. Workstream A (A1-A3 + F1 + F2 + F3) shipped as /why v4 (commit 6b4a819). Workstream B (B1 bridge verified + B2 validator shipped). Workstream C (/rca alias shipped). Workstream D (D1 threshold removed + D2 wiki concept revised). Workstream E (E1 recap bridge shipped). All 11 tasks complete.

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

### WORKSTREAM D — Layer 3 always-fire + speed optimizations (operator decision 2026-08-13)

**Operator decision:** eliminate the ≥3 HIGH/MEDIUM threshold for `/todo` Layer 3 fresh-subagent audit. Layer 3 fires ALWAYS, no magic number. Rationale: the threshold prevented the measurement that would justify or kill it; "the operator can scan manually" contradicts the ADHD-automation principle; one HIGH-severity misclassified drop is exactly the high-cost failure Layer 3 exists to catch.

**Speed optimizations to make always-fire acceptable (from /www research 2026-08-13):**

1. **Content-hash cache.** SHA256 of candidate (title + drop-reason) → cached audit result. Same handoff drop-reason appears every session until the handoff closes — cache hit returns instantly, zero LLM call. Workspace precedent: `www_dedup.py`, crawl4ai SHA256, `coding_agent_session_search` BLAKE3.
2. **Mechanical pre-filter.** Drops with deterministic reasons (`"duplicate"` + citation, `"done"` + commit SHA, `"prose/documentation"` + LOW) classify in <1ms via string check. Only the residual hits the LLM.
3. **Fast model (mechanical lane).** Layer 3's task is binary classification, not deep reasoning. Use `pick_model.py mechanical` — a compact 7B model with no session context catches closure-pressure drops as well as a 70B. Research: AgentForesight (arXiv 2605.08715) — compact 7B outperforms GPT-4.1 on audit; MAV (arXiv 2502.20379) — off-the-shelf LLMs work as verifiers.
4. **Progressive/streaming (never block).** Present Layer 1+2 output immediately; spawn Layer 3 in background; append promotions when they arrive. Research: AWS Agentic AI Lens — "user-facing agent begins streaming as soon as minimum inputs are available."

#### Task D1: Remove the ≥3 threshold from `/todo` SKILL.md Step 1d

- **What:** delete the `if len(high_medium_drops) >= 3:` conditional and the "Skip when" thresholds. Layer 3 spawns unconditionally when there are ANY dropped candidates.
- **Acceptance criteria:**
  1. Step 1d fires on ≥1 drop (any severity)
  2. The four speed optimizations above are documented in the same section
  3. The fail-open contract remains (subagent failure → present without Layer 3)
- **Falsifier:** if the combined optimizations don't bring median latency under 15s (measured over 10 sessions), the always-fire decision needs revisiting — but with a measured number, not a guess.
- **Effort:** S (SKILL.md edit)
- **Confidence:** H (operator decision; techniques are research-backed)

#### Task D2: Revise wiki concept `three-layer-candidate-filtering-regex-llm-fresh-subagent`

- **What:** the concept (created 2026-08-10) documents the ≥3 threshold as the design and its falsifier says "if it's too low, raise it." The operator eliminated the threshold. Update: remove threshold rationale, add the four optimization techniques, update falsifier to measure latency instead of threshold.
- **Acceptance criteria:**
  1. Table row for Layer 3 no longer says "needs ≥3 drops"
  2. "Adaptive firing" section replaced with "Always-fire + speed optimizations"
  3. Four techniques documented with research citations
  4. Falsifier updated: measures cache hit rate + mechanical filter pass rate + median latency
- **Effort:** S-M (concept revision)
- **Confidence:** H

### WORKSTREAM E — `/recap-grok` → `/todo` bridge (operator decision 2026-08-13)

**Operator decision:** `/recap-grok` should invoke `/todo` (or log recommendations to the proven bridge). The "complementary by design" framing was defensive — the display defect proved real information loss. Recap's "Remaining Work" items should reach `/todo` as individual scannable items, not stay buried in handoff prose.

#### Task E1: `/recap-grok` logs actionable items via the proven bridge

- **What:** after writing the recap, log items from "Remaining Work" and "Started but not completed" to `tp-critique-log.jsonl` with `--recommendations` (or a recap-specific structured store that `/todo` scans). The bridge proven working this session (Task B1) carries them automatically.
- **Acceptance criteria:**
  1. Recap items appear in `/todo` as individual items (not compressed to one-line handoff pointers)
  2. The recap's reconstruction layer (causation chains, decisions, quality assessment) stays in the recap — only actionable items cross the bridge
  3. No duplicate items if the same work is already in a handoff + the critique log
- **Falsifier:** if recap items surface in `/todo` but the operator never acts on them (because they prefer reading the recap directly), the bridge is redundant noise.
- **Effort:** M (recap SKILL.md edit + bridge call)
- **Confidence:** M (the bridge works; the question is whether recap items are the right shape for `/todo` consumption)

### WORKSTREAM C — `/rca` alias (ALREADY SHIPPED this session)

- **What:** Add `/rca` as an alias for `/why` (same pattern as `/research`→`/www`, `/redteam`→`/risk`). Keeps `/why` working; adds a more precise name for the ITSM/event-management context.
- **Status:** SHIPPED — `~/.grok/skills/rca/SKILL.md` created this session. Run `index_skills.py` to register.

## Open decisions (for the next session or operator)

1. **Should non-`/tp` skills (`/why`, `/review`, `/risk`) write to the critique log or their own JSONL?** This is the volume question the fresh lens flagged: the 21-entry count is a floor, not a ceiling, because producing skills don't log. Measure over 1-2 weeks: if >10 cross-skill recommendations/week are lost, extend the bridge. If <5, the existing bridge is sufficient. **Decision gate: measurement, not architecture.**

2. **Should maker-checker (Task A2) fire on model-behavior causes too, or only architectural?** Model-behavior mitigations "may decay under pressure" — the checker could verify the mitigation actually fired. But this doubles checker invocations. Defer until A2 ships and measure.

3. **Step 15 feedback-to-wiki loop revival (deferred from Tier 2).** Once A2 (maker-checker) ships, the checker's findings are the input stream for Step 15. Sequence: A2 first, then revive Step 15 to capture what the checker finds. Not in this handoff's scope — separate handoff after A2 validates.

## What was explicitly DEFERRED (now promoted to tasks — operator directive 2026-08-13)

These were previously listed as "deferred." The operator directed: "include them in the workstream effort." They are now tasks F1–F4 with effort estimates and disposition.

#### Task F1: Tier 2/3 `/why` defects (BLOCKED on A2)

- **What:** performative Five Whys (require distinct tool call per "why"), lexical Step 6 trigger (replace word-match with semantic trigger), fan-out floor (raise ≥1 to ≥2-3 tool calls per dimension), `--quick` bypass (keep minimal hypothesis diversification even in quick mode).
- **Dependency:** BLOCKED on A2 (maker-checker). Once the checker ships, it independently catches performative chains and shallow fan-out. F1 is the remaining maker-side hardening the checker doesn't subsume. Sequence: A2 ships → measure what the checker catches vs. misses → fix only the residual in F1.
- **Effort:** M (4 sub-fixes, each S)
- **Confidence:** H (defects are verified; sequencing is the question)

#### Task F2: Step 15 feedback-to-wiki loop revival (BLOCKED on A2)

- **What:** revive `/why`'s dead Step 15 (feedback-to-wiki). The loop currently never fires (0 log entries). Once A2 ships, the checker's findings ARE the systemic patterns Step 15 captures. Lighten the 15a gate or auto-route to handoff when the gate fails.
- **Dependency:** BLOCKED on A2 (checker generates the input stream).
- **Effort:** M
- **Confidence:** M (the gate mechanics need investigation — is 15a too strict, or is the cross-model review too heavy?)

#### Task F3: Volume measurement — start logging (CAN START NOW)

- **What:** instrument `/why`, `/review`, `/risk` to count recommendations produced per invocation. No structured store yet — just append to a measurement log so we have volume data after 1–2 weeks. This resolves Open Decision 1 (whether to extend the bridge to non-`/tp` skills).
- **Dependency:** NONE — can start immediately. This is a logging/instrumentation task, not a skill-design change.
- **Effort:** S (add a one-line log append to each skill's output step)
- **Confidence:** H
- **Decision gate:** after 1–2 weeks of data, if >10 cross-skill recommendations/week are lost → extend the bridge. If <5 → existing bridge sufficient.

#### Task F4: Display defect in `scan_critique_log()` (CAN START NOW)

- **What:** recommendation text lands in the `title` field with `"From critique of <target> re: "` prefix; `text` field is empty. Fix: extract recommendation text to its own field, or strip the prefix from the title.
- **Dependency:** NONE — independent code fix in `workspace_scanners.py`.
- **Effort:** S
- **Confidence:** H

## Background execution plan (operator directive 2026-08-13)

**Operator directive:** "plan non-blocking background activities for the non-A priority. We can do A in the main orchestrator." A runs in the main session via `/skill-dev`. Everything else runs as non-blocking background work — different files, no conflict with A's `/why` edits.

### Wave 1 — fire NOW (independent, no conflict with A or each other)

All touch different files in `~/.grok/skills/` or `P:/.data/` — zero collision risk with `/why` SKILL.md.

| Task | File(s) touched | Effort | Can fire as background subagent? |
|---|---|---|---|
| **B2** — handoff task-packet warning validator | `~/.grok/skills/handoff/SKILL.md`, `__lib/validators.py` | S | ✅ yes |
| **D1** — remove ≥3 threshold from `/todo` Step 1d | `~/.grok/skills/todo/SKILL.md` | S | ✅ yes |
| **F4** — display defect in `scan_critique_log()` | `P:/.data/...` or `~/.grok/skills/todo/__lib/workspace_scanners.py` | S | ✅ yes |
| **F3** — volume measurement instrumentation | `~/.grok/skills/why/SKILL.md` (1 line), `~/.grok/skills/review/SKILL.md`, `~/.grok/skills/risk/SKILL.md` | S | ✅ yes — but touches `/why/SKILL.md` (1 line only; coordinate with A) |

**F3 conflict note:** F3 adds one logging line to `/why/SKILL.md`. If A is editing the same file in the main orchestrator, this is a collision risk. Mitigation: either (a) fire F3 after A completes, or (b) have A include the F3 logging line in its edit pass. Option (b) is cleaner — add it to A's scope.

### Wave 2 — fire AFTER A2 ships (blocked on maker-checker)

| Task | Why blocked | Effort |
|---|---|---|
| **F1** — Tier 2/3 `/why` defects | A2's checker subsumes most; fix only the residual | M |
| **F2** — Step 15 revival | A2 generates the input stream (checker findings) | M |

### Main orchestrator — A (the `/why` reliability fixes)

| Task | What | Effort |
|---|---|---|
| **A1** | Move Step 9a before Step 5 | S-M |
| **A2** | Maker-checker default + behavior contract | M |
| **A3** | Depth signal in default output | S |
| **+ F3 line** | Add volume-measurement logging line to `/why` (folded into A's edit) | S |

### Dependency graph

```
Wave 1 (NOW, parallel):
  B2 ──────────────────────> done
  D1 ──────────────────────> done
  F4 ──────────────────────> done
  [F3 folded into A]

Main orchestrator (A):
  A1 ─┐
  A2 ─┼──> A ships ──> Wave 2:
  A3 ─┘                    F1 (residual Tier 2/3) ──> done
  +F3 line                 F2 (Step 15 revival) ────> done
```

### Total effort

- Wave 1 (background): 3 × S = ~45 min parallelized
- Main (A + F3 line): A1(S-M) + A2(M) + A3(S) + F3-line(S) = ~90 min
- Wave 2 (post-A): F1(M) + F2(M) = ~120 min
- **Grand total: ~4.5 hours of work, but A and Wave 1 run in parallel → wall-clock ~2 hours**

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
