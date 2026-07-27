---
title: "Visible-output contracts for behavioral skill steps"
created: 2026-07-27
source: session-2026-07-27 (/tp on wiki-utilization failure in /why Step 0.5)
tags: [decision, skill-design, behavioral-steps, visible-output, receipt-discipline, anti-skip]
agent: grok
host: both
cognitive_load: 2
verification: observed
summary: >
  Skill steps that are "mandatory" in text but produce no visible output have zero
  friction to skip — the agent can omit the step and nothing surfaces the omission.
  The fix is a visible-output contract: the step must emit a receipt (the actual
  command run + its result) in the output report. This mirrors evidence-tier
  receipt discipline (every claim needs a tool-call citation) applied to the skill's
  own internal steps. Applied to /why Step 0.5 (pattern-library query): the output
  row must cite the actual grep command + hit count. A "no match" without the
  command receipt means the step was skipped. Distinct from hook enforcement:
  behavioral steps cannot be structurally enforced at runtime (the model decides
  whether to run them), so the receipt creates post-hoc accountability instead.
relations:
  - target: wiki/concepts/wiki-integrated-skills-query-save-pattern.md
    type: extends
  - target: wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
    type: related
  - target: wiki/concepts/friction-detection-operator-pushback-as-trigger.md
    type: related
---

# Visible-output contracts for behavioral skill steps

## Decision context

**The problem:** `/why` Step 0.5 (pattern-library query) was labeled "MANDATORY for recurring/systemic signals" in the SKILL.md. In practice, the agent skipped it entirely during session 019fa23d's hook-timeout investigation. The agent ran a full `/why` + `/www` cycle re-deriving the `hook-evidence-collection-cost-vs-timeout-tradeoff.md` pattern that was already documented and one grep away. The operator caught it: "I thought we had this problem before."

The cost of the skip was a full `/why` + `/www` investigation cycle (~10 minutes of agent time) that re-derived a pattern already documented one grep away. The operator's correction was immediate and precise — they didn't need to investigate, they needed to point at the existing documentation. This is the signature of a wiki-utilization failure: the knowledge exists, the discovery mechanism exists, but the discovery step was silently skipped.

**The root cause was not "the agent forgot."** It was structural: Step 0.5 produced no visible output. The step's instructions said "query the wiki" but did not require the query result to appear in the final report. An omitted step leaves no trace; a step that produces output leaves a receipt that is either present or conspicuously absent.

This is the same failure class as the hook timeout itself — [[hook-evidence-collection-cost-vs-timeout-tradeoff]] describes how fail-open hooks silently drop receipts. A skipped behavioral step is the skill-level analog: the step "fails open" (no error, no output, execution continues) and the coverage gap is invisible until an operator catches it or a downstream dependency breaks. The two concepts are duals: one is about runtime hooks producing no evidence; the other is about reasoning steps producing no evidence. Both need the same structural fix: make the absence visible.

## The decision

**Chosen: visible-output contract.** Every behavioral step labeled "mandatory" or "recommended" must emit a receipt in the output report: the actual command run + its result (hit count, file path, exit code). The output template reserves a row for the step that must contain the receipt or an explicit skip reason.

## Key findings

- **Silent steps and fail-open hooks are duals.** Both produce no error signal when skipped/dropped. Both need the same structural fix: make the absence visible. The hook solution is a health monitor; the skill-step solution is a visible-output receipt.
- **The keyword table addresses a second failure mode.** Even when the agent remembers to query, it may not know what to search for. Common failure-shape keywords make the query reflexive rather than dependent on keyword invention under pressure.
- **Post-hoc accountability is the only available enforcement layer for behavioral steps.** Pre-emptive enforcement fails (model skips anyway) or is impossible (no interception point). The receipt creates detectable gaps without requiring runtime control flow.
- **The receipt format matters: command + result, not just "done."** A receipt that says "wiki checked" is fabricatable. A receipt that says `rg "hook timeout" P:/.data/wiki/concepts/ → 1 hit` is auditable — the hit count can be verified by re-running the command. The format enforces honesty through verifiability.

### Selection criterion

**Accountability via traceability over accountability via willpower.** The criterion is: can a reader of the output tell whether the step was run? If no, the step is structurally skippable regardless of how emphatic the "MANDATORY" label is.

### Rationale

1. **Behavioral steps cannot be structurally enforced.** Unlike hooks (which fire at runtime and can block), skill steps are executed by the model's own decision. The model decides whether to run the grep. No runtime mechanism can force it.
2. **Post-hoc accountability is the available enforcement layer.** If the output must contain the receipt, then a missing receipt is visible to the operator and to `/check`. The operator can catch the skip; a future `/check` scanner can flag it mechanically.
3. **This mirrors evidence-tier discipline.** `/why` Step 4b already requires every `[FACT]` claim to cite a tool call. Extending this to the skill's own internal steps is the same principle at a different level: the step's execution is a claim that needs a receipt.
4. **The keyword table reduces discovery friction.** Common failure shapes (hook timeout, closure-pressure, identity confusion) map to known search keywords. This makes the query reflexive — the agent doesn't need to invent keywords under pressure.

### Steelman of the rejected alternatives

**Why "stronger language" was reasonable:** making Step 0.5 "MANDATORY (NON-NEGOTIABLE)" in louder text. This is the default response to a skipped step. It fails because text emphasis has no runtime effect — the model that skipped "MANDATORY" will skip "MANDATORY (NON-NEGOTIABLE)" under the same pressure.

**Why "hook enforcement" was reasonable:** add a PreToolUse or SessionStart hook that forces the wiki query before the skill proceeds. This is the structural ideal. It fails because skill steps run inside the model's reasoning, not as tool calls — there's no runtime interception point between "model reads SKILL.md" and "model decides to grep." Hooks enforce tool use, not reasoning steps.

**Why "remove the step entirely" was reasonable:** if the agent won't run it reliably, maybe it's not worth having. This fails because the step IS valuable when run — the prior session's pattern-library concept would have saved a full `/why` + `/www` cycle. The problem is reliability, not value.

**Why they lose to "visible-output contract":** stronger language doesn't change the structural property (silent steps are skippable). Hook enforcement can't intercept reasoning steps. Removing the step loses the value. The visible-output contract is the only option that preserves the step's value AND creates accountability for running it.

The deeper insight: **the enforcement layer for behavioral steps must be post-hoc, not pre-emptive.** Pre-emptive enforcement (stronger language, hook interception) either fails (model skips anyway) or is impossible (no interception point). Post-hoc enforcement (receipt in output, auditable by `/check`) creates accountability without requiring runtime control flow. This is the same design principle as git commit hooks vs. git commit messages: commit hooks enforce pre-emptively (block the commit); commit messages enforce post-hoc (the message is visible in history and can be audited). Behavioral skill steps need the commit-message model, not the commit-hook model.

## Falsifier

This decision is wrong if:
- **The visible-output contract is itself skipped (the model fills the row from memory).** Then the receipt is performative, not evidential. Mitigation: the contract requires the actual command + hit count, which is harder to fabricate than a vague "I checked the wiki." A fabricated hit count would mismatch the real grep result if audited.
- **The receipt discipline is theater (every row has a receipt but the step still doesn't actually inform the analysis).** Then the contract adds ceremony without value. Mitigation: when a pattern IS found (receipt shows N hits), the analysis must cite the matched concept — a match that's ignored is a separate failure to surface.
- **Steps without visible output are actually fine (the model runs them reliably without enforcement).** This would mean the contract is unnecessary overhead. Refuted by this session: Step 0.5 was skipped despite the "MANDATORY" label.

## Implications

The visible-output contract pattern implies that skill SKILL.md files should be audited for mandatory steps that produce no output. The audit is mechanical: grep each SKILL.md for "MANDATORY" or "must" or "required", then check whether the step's output template includes a receipt row. Steps without a receipt row are structurally skippable and should either get a receipt requirement or be downgraded to "recommended." This is a one-time audit pass across all skills, not an ongoing maintenance burden — once the receipt rows are in the templates, they persist.

## What this means for our workspace

**Generalizes beyond `/why`:** any skill with mandatory behavioral steps (query, verify, check) should adopt the visible-output contract pattern. Candidates:
- `/check` verification steps (must show the test command + result)
- `/review` finding-verification steps (must show the source citation)
- `/handoff` acceptance-criteria steps (must show the criteria check)

**The pattern is: receipt-discipline applied to the skill's own steps, not just to the claims in the output.** This is one level up from evidence tiers: evidence tiers discipline claims about the world; visible-output contracts discipline claims about the skill's own execution. This connects to [[wiki-integrated-skills-query-save-pattern]] — that concept describes the query-at-start / save-at-end architecture; this concept adds the enforcement layer that makes the query-at-start reliable. It also relates to [[hook-evidence-collection-cost-vs-timeout-tradeoff]] — both are about invisible failures (dropped receipts, skipped steps) that produce no error signal. And it complements [[friction-detection-operator-pushback-as-trigger]] — when the visible-output contract is absent, operator pushback is the only detection mechanism, which is exactly what happened here.

As a skill-design decision, this is an instance of [[compound-skill-improvement-patterns]] — a structural improvement that compounds across all future invocations of the skill. It also draws on [[self-improving-agent-systems-techniques-and-workspace-gaps]] (the "Could You Be Wrong?" prompt and receipt-discipline techniques) and follows the decision shape documented in [[inline-conditional-over-dispatch-for-skill-design]]. Skill authors should consult [[skill-authoring-patterns-dos-and-donts]] for the broader pattern: mandatory steps need enforcement, not just emphasis. The receipt format (command + result) is a prompting pattern from [[prompting-patterns-for-ai-agent-control]] — receipt-first framing that makes claims verifiable.

**Why "mandatory" labels fail:** behavioral instructions operate on the model's attention, not on runtime control flow. A label like "MANDATORY" is a token sequence that increases the probability of compliance but provides no guarantee. Under cognitive load (long session, complex investigation, closure pressure), the probability drops. The structural fix is not stronger language but a mechanism that makes non-compliance visible — the receipt creates a detectable gap (missing row, missing command, fabricated hit count).

**The keyword table reduces a second failure mode:** even when the agent remembers to query the wiki, it may not know what keywords to search for. The failure-shape keyword table (hook timeout → `evidence-collection cost`, agent skipped step → `closure-pressure`) makes the query reflexive: the agent reads the failure description, maps to keywords, and runs the grep without needing to invent search terms under pressure. This is the skill-scale equivalent of a lookup table — it trades a small amount of skill verbosity for a large reduction in query-miss rate.

**Operational checklist for any mandatory skill step:**
1. Does the step produce visible output in the report? If no, add a receipt requirement.
2. Does the receipt contain the actual command + result (not a summary)? If no, tighten the format.
3. Is there a keyword/discovery table for the most common query shapes? If no, add one.
4. Does a future `/check` or audit pass know what a valid receipt looks like? If no, document the expected format.

## Receipts

- **"Step 0.5 was skipped in session 019fa23d":** receipt — the `/why` output for the hook-timeout investigation contained no pattern-library query row and no grep command. The agent proceeded directly to timing instrumentation and `/www` research.
- **"The wiki concept was one grep away":** receipt — `rg "hook timeout" P:/.data/wiki/concepts/` returns `hook-evidence-collection-cost-vs-timeout-tradeoff.md` as the first hit.
- **"The visible-output contract was added":** receipt — `/why` SKILL.md line 123, commit `1c3ee80` in ~/.grok.
