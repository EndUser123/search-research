# Handoff: Exploration-failure problem (unsolved)

**Created:** 2026-07-20
**Status:** Problem NOT solved. Rule added as tripwire; underlying drivers remain open.
**Why this exists:** the rule in `~/.grok/AGENTS.md` (lines 100–125, "Subagent synthesis → report gate") catches the failure when applied, but does not fix the conditions that produce it.

## What's been done

A new rule at `C:\Users\brsth\.grok\AGENTS.md` lines 100–125, subsection `### Subagent synthesis → report gate`. Tripwire form: spot-check any subagent synthesis that determines a disposition against evidence already in context before propagating it into a report, decision, or handoff.

The rule names the failure conditions and the actual driver (closure under uncertainty). It does not eliminate them.

## Why the problem is not solved

The rule adds a verification step. It does not change:

1. **Dispatch-shape pressure.** The conditions that made me bundle cc-council with cc-aca-observability (optimizing dispatch count over investigation depth) are unchanged. A future task under time/token pressure will face the same incentive and likely make the same call.

2. **Closure-under-uncertainty driver.** The rule says "label the rest `[UNKNOWN]` or `[INFERENCE]` explicitly" — but the pressure to produce confident-sounding closure is still there. The rule gives the right vocabulary; it doesn't remove the incentive to skip it.

3. **Terminal disposition vocabulary.** `reject`, `stub`, `retain-as-reference` still feel complete and still discourage re-examination. The rule says "spot-check before propagating"; it doesn't change the vocabulary itself.

4. **Single-instance correction does not generalize.** The session is direct evidence: cc-council was corrected, then hours later the same failure recurred as "nobody is planning to build this." The rule is one more instance of correcting the symptom. Whether it prevents recurrence in a future session is unknown and untested.

5. **No measurement.** The rule's falsifier says "if a future synthesis is not spot-checked and contains an error, the rule was violated." That requires someone to detect the violation. No mechanism exists for that — no hook, no audit, no periodic review. The rule depends on the same actor who has the closure pressure also catching their own skip.

## Open work (the actual problem)

These are the candidates for solving the problem, not just tripping it. Each is a separate decision with its own trade-offs — they are not equivalent and should not be bundled:

### Candidate A — Dispatch discipline rule

A rule constraining dispatch shape: "one subagent per architecturally-dense target; never bundle two dense targets for dispatch efficiency." Addresses condition #1 directly. Low effort (one paragraph in AGENTS.md). Risk: adds ceremony to legitimate cases where bundling is fine; the boundary of "dense" is fuzzy.

### Candidate B — Disposition vocabulary reform

Replace terminal dispositions (`reject`, `stub`, `retain-as-reference`) with vocabulary that forces a follow-up: e.g. `reject-subject-to-spot-check`, `stub-with-real-surrounding-system`, `reference-only-until-second-consumer-appears`. Addresses condition #3. Risk: verbose; may not survive contact with habit.

### Candidate C — Hook-based enforcement

A pre-write or pre-commit hook that scans report/handoff files for disposition vocabulary and requires evidence of a spot-check (e.g. a `Verified against:` citation) in the same section. Addresses condition #5. High effort; adds infrastructure to a prose-heavy workflow; false-positive risk on legitimate uses.

### Candidate D — Closure-pressure countermeasure

A rule or practice that makes admitting gaps feel less costly: e.g. normalize `[UNKNOWN]` and `[INFERENCE]` labels in reports the same way `[FACT]` is already normalized in `P:/.claude/rules/epistemic-format.md`. Addresses condition #2 directly. Low effort. Risk: labels become performative (the §6 "performative rigor" failure mode already named in `/tp/SKILL.md`).

### Candidate E — Periodic audit

A recurring review (weekly, or per-N-sessions) that samples past reports/handoffs and checks whether dispositions survived later scrutiny. Detects rule violations after the fact; produces data on whether the tripwire rule is working. Low infrastructure (one script, one review cadence). Addresses condition #5 measurement gap. Risk: review cadence slips; audit becomes ceremony.

### Candidate F — Do nothing additional; rely on the tripwire

Accept that the rule is a partial fix and that user pushback (as in this session) is the actual backstop. Honest position: no additional mechanism is justified until the tripwire rule is shown to fail in a future session. Risk: normalizes the failure as "caught by user" which is exactly the anti-pattern `~/.grok/AGENTS.md` Model-as-orchestrator warns against.

## What I don't know

- Whether the tripwire rule will actually be applied next time. The session that produced it also produced a recurrence of the failure hours after the cc-council correction. Internal discipline has already been shown insufficient within one session.
- Whether any of Candidates A–E would have prevented the cc-council incident specifically. Dispatch discipline (A) probably would have; vocabulary reform (B) might have; the others are less targeted.
- What the user's tolerance is for added ceremony vs. added failure surface. This is a judgment call, not a technical one.

## Resumption protocol

1. Re-read the rule at `~/.grok/AGENTS.md` lines 100–125 and verify it still describes the failure accurately.
2. Decide whether to pursue any of Candidates A–F, or some combination, or a new candidate. This requires user input on tolerance for ceremony vs. failure surface.
3. If pursuing a candidate, design it as a bounded change with a falsifier — same standard the original rule was held to.
4. Do not treat this as polish work. The session produced the same failure twice in one day. The problem is open.

## Reference paths

- The rule: `C:\Users\brsth\.grok\AGENTS.md` lines 100–125
- The cc-council correction (in the report the rule was derived from): `P:\docs\tp-cognition-migration-2026-07-20\FINAL_REPORT.md` — see cc-council sections and the "Corrected facts" narrative
- Sibling hard rules for structural comparison: `~/.grok/AGENTS.md` `### Trust over believability`, `### Inference chains, bare numbers, and destructive-write preflight`, `### Model-as-orchestrator`
- `/tp/SKILL.md` §Drift-correction tools — names "performative rigor" as failure mode #6, relevant to Candidate D risk
- `P:/.claude/rules/epistemic-format.md` — existing `[FACT]/[INFERENCE]/[UNKNOWN]` convention Candidate D would extend

## Estimated effort

Variable by candidate. A or D: ~30 min each (one paragraph in AGENTS.md or one rule file). B: ~1 hour (vocabulary reform across multiple documents). C: ~half-day (hook design + tests). E: ~2 hours setup + recurring review burden. F: zero, but accepts the risk.
