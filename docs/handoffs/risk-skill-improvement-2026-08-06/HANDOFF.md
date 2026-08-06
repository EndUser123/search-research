---
thread_id: a7b3c1d2-0e5f-4a6b-9c8d-1e2f3a4b5c6d
parent_handoff_path: none
current_session_id: 019fcdd2-e190-7323-9b77-57a1c73dada5
parent_session: none
current_terminal_id: console_019fcdd2
produced_at: 2026-08-06T06:00:00Z
last_updated_by: 019fcdd2-e190-7323-9b77-57a1c73dada5
last_updated_at: 2026-08-06T06:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 0c57435
---

# HANDOFF: /risk skill improvement — test runs done, coverage gap found

## 1. Objective

Improve the `/risk` skill through evidence-driven iteration: run it on real targets to find defects, then fix what the runs surface. The skill was designed through 4 versions of theory-driven iteration with zero execution receipts before this session.

**Scope bounds:** Work scope is the `/risk` skill (`~/.grok/skills/risk/SKILL.md`) and its wiki learning loop. The LAEFS enforcement layer (separate handoff) and skill-ecosystem pattern propagation are out of scope.

## 2. Status

**OPEN** — Phase 1 (cold-start test runs) COMPLETE. Phase 2 (fix coverage gap + seed wiki) NOT STARTED.

## 3. Producing context

- Date: 2026-08-05 through 2026-08-06
- Session: `019fcdd2-e190-7323-9b77-57a1c73dada5`
- Terminal: `console_019fcdd2`
- Host: grok (Grok Build, GLM-5-2)

## 4. Read-first list (ordered, with reasons)

1. `~/.grok/skills/risk/SKILL.md` — the skill under test (506 lines, 6 phases, 7 ensemble patterns)
2. `P:/.data/wiki/concepts/risks-skill-improvement-research-2026.md` — research findings (5 cross-model subagents) with verified/refuted claims from test runs
3. `P:/.data/wiki/concepts/multi-model-ensemble-design-patterns-for-agent-skills.md` — the 7 patterns (P1-P7) propagated to /risk, /review, /tp, /check
4. `P:/.data/wiki/concepts/skill-naming-convention-short-imperative.md` — naming convention (operator corrected /risks → /risk)

## 5. Verified facts (with source paths)

- [FACT] `/risk` passed 3/3 cold-start test runs (Run 1: trivial target, Run 2: known-bad LAEFS target, Run 3: progressive disclosure decision). Results documented in `risks-skill-improvement-research-2026.md` § "Test run results."
- [FACT] The v1 threat-model inflation failure (3/14 adversarial findings on an unreliable-agent target) DID NOT recur in Run 2. P6 (threat-model classification) works. Both critics produced zero adversarial findings. (Source: Run 2 CRITIQUE panel synthesis)
- [FACT] Scan coverage gap: Run 2 scan missed the 2 highest-probability risks (subagent tool-call bypass, false-positive friction). The "decision" risk categories don't include "operator experience" or "coverage gaps." Both cross-model critics independently found these. (Source: Run 2 critic outputs)
- [FACT] Cross-model critics produce decorrelated findings: both critics found the same 2 blind spots the scan missed, plus different additional findings. P2 (max diversity) works. (Source: Run 2 panel)
- [FACT] Wiki grounding step runs correctly but finds 0 risk patterns (cold-start confirmed). The wiki has failure-mode concepts but no structured risk-pattern entries with slug + falsifier format. (Source: grep for `tags:.*risk` in wiki concepts)
- [FACT] SKILL.md is 506 lines, ~6,200 tokens. Phase 4-5 (~150 lines, ~1,800 tokens) fires only on ATTACK escalation. (Source: `wc -l` + char count)
- [FACT] Progressive disclosure research found flat one-level disclosure is optimal (arxiv He et al. Jul 2026). Hierarchical causes 30% accuracy drop. But token savings (1.8%) may be negligible at our context scale. (Source: research concept §2)
- [FACT] Skill naming convention: short imperative names (/brain, /risk, /tp). Operator confirmed. (Source: `skill-naming-convention-short-imperative.md`)

## 6. Current state

**Done:**
- 3 cold-start test runs executed, all passed
- Test results documented in wiki concept with verified/refuted claims
- `/red-team-old` directory deleted (was already disabled)
- All `/red-team` references confirmed as historically accurate provenance
- 7 ensemble design patterns documented in wiki concept
- Patterns propagated to /review (P1,P2,P4,P5,P6,P7), /tp (P1,P2,P4,P6), /check (P1,P7)
- `/brainstorming` → `/brain` rename (user-scope shadow)
- `/risks` → `/risk` rename (246 replacements across 70 files)
- Skill naming convention captured to wiki

**Not done:**
- Scan coverage gap fix (add "operator experience" + "coverage gaps" to decision categories)
- Wiki seeding (5-10 risk patterns from known incidents)
- Warm-state re-test (compare cold-start vs warm-state after seeding)
- Progressive disclosure split (deferred until data justifies)
- `/risk scan` integration into `/go` (deferred until scan quality confirmed)

## 7. Task packets

### TASK-1: Fix scan coverage gap

- **id:** RISK-COVERAGE-01
- **goal:** Add "operator experience" and "coverage gaps" to the decision-type risk categories in Phase 1 SCAN so the scan catches what Run 2 missed
- **in scope:** `~/.grok/skills/risk/SKILL.md` Phase 1 scan category table (around line 88)
- **out of scope:** Phase 4 ATTACK categories, other skills
- **files / anchors:** `risk/SKILL.md` — the section listing risk categories for "decision" target type
- **acceptance:** Re-run `/risk` on the LAEFS target. Scan should find ≥1 of the 2 risks it previously missed (subagent bypass or false-positive friction) without critic help.
- **falsifier:** Scan still produces 0 findings in the "operator experience" or "coverage gaps" categories for a target where those risks demonstrably exist
- **verification level required:** LIVE_BEHAVIOR (run the skill)
- **estimate:** ~5 min edit + ~10 min re-run

### TASK-2: Seed wiki with risk patterns

- **id:** RISK-WIKI-SEED-01
- **goal:** Write 5-10 structured risk-pattern wiki concepts from known incidents to bootstrap the learning loop
- **in scope:** `P:/.data/wiki/concepts/` — new concept files with `tags: [risk-pattern]`
- **out of scope:** Automated mining pipeline (deferred), existing wiki concepts
- **files / anchors:** New files: `risk-pattern-{slug}.md` for each pattern
- **acceptance:** `/risk scan <target>` finds ≥1 relevant pattern via wiki grounding step
- **falsifier:** Wiki grounding step still returns 0 patterns after seeding, OR returns irrelevant patterns
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** ~30 min (5-10 concepts, each ~3-5 min with provenance from known incidents)
- **Candidate patterns to seed:**
  1. Threat-model inflation (from this session's v1 LAEFS run)
  2. Concurrent CDP auth contention (from 2026-07-28 incident)
  3. Replacement-before-investigation (from 2026-07-26 through 2026-08-01 pattern)
  4. Config disabled-list bare-name collision (from 2026-07-28 incident)
  5. Cold-start confound in testing (from this session's /tp critique)

### TASK-3: Warm-state re-test (depends on TASK-2)

- **id:** RISK-WARM-TEST-01
- **goal:** Re-run the 3 test targets after wiki seeding to measure whether wiki grounding improves scan quality
- **in scope:** Run `/risk` on the same 3 targets from Phase 1
- **out of scope:** Skill modifications
- **files / anchors:** No file changes — run-only
- **acceptance:** Compare cold-start vs warm-state results. Wiki grounding should find ≥1 relevant pattern per non-trivial target.
- **falsifier:** No measurable difference between cold-start and warm-state results
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** ~15 min (3 runs, shorter than Phase 1 since the procedure is now exercised)
- **depends_on:** RISK-WIKI-SEED-01

## 8. Open decisions

### Decision 1: Progressive disclosure split — when?

- **Question:** Should Phase 4-5 be split into `references/attack-phase.md` now, or wait for more data?
- **Options:** (A) Split now for modularity (B) Wait until TASK-1+2+3 complete
- **Selection criterion:** Modularity benefit vs. risk of agent failing to load reference
- **Currently leads:** (B) — the /tp critique and Run 3 both reframed the benefit as modularity, not token savings. The infrastructure cost (loader reliability) should be validated first.
- **What would change:** If the aar-style reference loader pattern proves reliable in another skill first, (A) becomes safer.

### Decision 2: /go integration — advisory-only or blocking?

- **Question:** When wiring `/risk scan` into `/go` at reversibility ≥1.75, should it be advisory or blocking?
- **Options:** (A) Advisory-only first, promote to blocking after precision baseline (B) Blocking from start
- **Selection criterion:** Alert fatigue risk vs. enforcement value
- **Currently leads:** (A) — research consensus (SOC data: 90% FP rate). Start conservative.
- **What would change:** If the scan precision is already high after TASK-1 fix, (B) becomes viable sooner.

## 9. Hard constraints

- Cold-start test data must be collected BEFORE wiki seeding (already done ✅)
- The skill naming convention is `/risk` (singular), not `/risks` — do not revert
- The 7 ensemble patterns (P1-P7) are the source of truth in `multi-model-ensemble-design-patterns-for-agent-skills.md`
- All test runs must use cross-model critics (P2: different model families), not parent-inherited Grok

## 10. Cross-reference couplings

- `risks-skill-improvement-research-2026.md` → contains verified/refuted claims from test runs. If the skill is modified (TASK-1), the "test run results" section becomes stale — re-verify.
- `multi-model-ensemble-design-patterns-for-agent-skills.md` → source of truth for P1-P7 patterns propagated to the skill. If patterns change, the skill AND the sibling skills (/review, /tp, /check) need re-propagation.
- `skill-naming-convention-short-imperative.md` → documents why the skill is `/risk` not `/risks`. If this convention is re-litigated, update both.
- `greenfield-enforcement-layer-grok-build-2026-08-04/HANDOFF.md` → the LAEFS handoff. Run 2 used LAEFS as the test target. The risk findings (subagent bypass, false-positive friction) are relevant to LAEFS Phase 2b.

## 11. Other outstanding streams

- **LAEFS enforcement layer** — separate handoff at `greenfield-enforcement-layer-grok-build-2026-08-04/HANDOFF.md`. Phase 2a-2d ready. Open.
- **Pattern propagation gaps** — `/check` missing P2/P6, `/www` missing all patterns, `/go` missing P1/P6. Lower priority. Open.

## 12. Explicit non-goals

- Do NOT build the pattern-propagation Stop hook (designed but not built; ~1 session effort; depends on wiki concept + pattern markers)
- Do NOT add Check 9 to `/skill-dev` (subagent dispatch pattern compliance scanner; separate effort)
- Do NOT batch-rename other skills to short names — do it opportunistically when editing for other reasons
- Do NOT build the automated wiki mining pipeline — manual curation first (TASK-2), then evaluate

## 13. Resumption protocol

1. Read this handoff + `risks-skill-improvement-research-2026.md`
2. **TASK-1 first:** Add "operator experience" and "coverage gaps" categories to `risk/SKILL.md` Phase 1 decision-type scan table
3. Re-run `/risk scan` on the LAEFS target to verify the coverage gap is fixed
4. **TASK-2:** Write 5 risk-pattern wiki concepts from the candidate list
5. **TASK-3:** Re-run all 3 test targets warm-state, compare to cold-start results

## 14. Suggested next invocation

```
/go Fix the /risk scan coverage gap (TASK-1: RISK-COVERAGE-01). Add "operator experience" and "coverage gaps" to the decision-type risk categories in ~/.grok/skills/risk/SKILL.md Phase 1. Then re-run /risk scan on the LAEFS enforcement layer decision to verify the scan now catches subagent bypass or false-positive friction without critic help. Acceptance: scan finds ≥1 of the 2 previously-missed risks.
```

## 15. Last user message (verbatim)

> "/handoff"

## 16. Epistemic labels per claim

- [FACT] 3/3 test runs passed (tool output in session transcript)
- [FACT] P6 threat-model classification works (Run 2: zero adversarial findings from either critic)
- [INFERENCE] The scan coverage gap is the highest-priority fix (both critics independently found the same blind spots; the missing categories are the root cause)
- [INFERENCE] Manual wiki seeding will produce useful patterns (the candidate list is grounded in verified incidents, but the format/applicability for /risk's grounding step is untested)
- [UNKNOWN] Whether warm-state results will differ measurably from cold-start (no data yet)

## 17. Suggested skills for next session

- `/go` — TASK-1 is a concrete edit + verification, ready to execute
- `/wiki` — TASK-2 writes 5+ wiki concepts; the wiki skill's validation + auto-link pipeline applies
- `/check` — after TASK-1+2, verify the skill modifications mechanically
- `/risk` — TASK-3 re-runs the skill on the same targets

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-06T06:00 | 019fcdd2 | created |
