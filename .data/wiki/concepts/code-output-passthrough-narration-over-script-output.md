---
title: "Code-output passthrough: LLM narrates over script-produced reports instead of presenting them"
created: 2026-08-01
source: session-019fa8f8
tags: [failure-pattern, closure-pressure, narration, passthrough, model-behavior, skill-design, dual-path-output, architectural]
summary: >
  When a skill's script produces a complete formatted report (dashboard,
  receipt, scan results), the LLM's text-generation pathway fires
  narration on top of the script output instead of presenting it as-is.
  The script output lands in a tool_result block; the LLM then manually
  retypes, summarizes, or adds commentary over what the code already
  produced — burying the real report behind its own text. This is a
  dual-path-output design flaw: code produces the report AND the
  procedure asks the LLM to produce the report. The LLM cannot reliably
  suppress its generation pathway because prose rules do not bind model
  behavior. The structural fix is to bypass the LLM entirely for
  code-complete outputs (terminal alias, hook, keybind) or to make the
  procedure explicitly passthrough-only with no additive steps.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - "Session 019fa8f8: 6+ narration failures on /model-quota despite repeated corrections"
  - "Workspace wiki: ship-receipt-mechanical-generation-from-per-check-results.md (exact parallel — LLM assembled receipt by hand instead of using check results)"
  - "Workspace wiki: premature-synthesis-without-reading-existing-capability.md (the broader pattern — synthesize without reading)"
  - "Workspace wiki: reactive-pattern-matching-and-closure-pressure.md (prose rules do not fire under closure pressure)"
  - "Workspace wiki: code-orchestrates-model-judges-skill-scale.md (deterministic code does enforcement, LLM does only judgment)"
relations:
  - target: wiki/concepts/premature-synthesis-without-reading-existing-capability.md
    type: refines
    note: "Same mechanism (narrative-closure overrides read-before-act); new surface (synthesize over code output rather than synthesize without reading)"
  - target: wiki/concepts/ship-receipt-mechanical-generation-from-per-check-results.md
    type: same-family
    note: "Exact parallel — LLM assembled receipt by hand instead of using check results. This concept generalizes: any code-complete output."
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: substrate
    note: "The closure pressure that drives narration. Prose rules added in-session do not bind the generation pathway."
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: principle
    note: "If code can produce the output, the LLM should not be asked to produce it again."
---

# Code-output passthrough: narration over script-produced reports

## Decision context

**The motivating problem:** across session 019fa8f8, the operator invoked `/model-quota` 6+ times. Each time, the LLM ran `fleet_quota.py` which produced a complete dashboard (gauges, alerts, reset timers), then **buried that output** inside a tool_result block and presented its own manual narration as the response — "Stale. Full refresh:" plus hand-typed alert bullets. This happened despite:

1. Repeated operator corrections (5+ turns)
2. A /why root cause analysis identifying the problem
3. A /tp critique validating the analysis
4. Three prose fixes implemented (skill procedure edit, AGENTS.md rule, skill-dev checklist)
5. The fixes being committed before the very next invocation

The rule was committed. The next invocation narrated anyway. **Prose did not bind the generation pathway even once.**

## The pattern

```
TRIGGER:     Skill invocation where a script produces a complete formatted report.
EXPECTATION: The agent presents the script's stdout as its response (passthrough).
FAILURE:     The agent's text-generation pathway fires after the tool_result,
             producing narration, summary, or commentary on top of the code output.
CATCH:       The operator sees the narration instead of (or in addition to) the report.
ROOT CAUSE:  The LLM cannot suppress its generation pathway. "Generating text" IS
             the task from the LLM's perspective. Prose rules in context are
             suggestions to the generation pathway, not gates on it.
```

## Why prose doesn't work here

The workspace documents across 27+ wiki concepts that prose rules do not fire reliably under closure pressure. This instance is sharper: the rule was added **in the same session**, with full awareness, and the generation pathway still narrated on the very next turn. The falsifier for [[reactive-pattern-matching-and-closure-pressure]] fired immediately:

> "Adding a rule reduces the probability of the failure but does not eliminate it. The falsifier is whether the rules fire on the next session, under real closure pressure, not in the session where they were added with full awareness."

The rule didn't even last to the next turn.

## The structural fix: bypass the LLM

The only reliable fix is to remove the LLM from the output path entirely. For `/model-quota`, this was implemented as a PowerShell function in the operator's profile:

```powershell
function quota { python "$env:USERPROFILE/.grok/skills/model-quota/scripts/fleet_quota.py" @args }
```

Typing `quota` in the terminal runs the script directly. The output goes to stdout. No LLM turn is triggered. No narration is possible.

This applies the [[code-orchestrates-model-judges-skill-scale]] principle: if the code produces the complete output, the LLM should not be in the output path. The skill SKILL.md should still exist (for discovery, documentation, flags), but the *primary invocation path* for code-complete-output skills should bypass the LLM.

## Generalization: which skills have this risk

Any skill where a script produces the entire deliverable and the LLM adds no judgment:

| Skill | Script produces complete output? | LLM adds judgment? | Risk |
|-------|----------------------------------|--------------------|------|
| /model-quota | ✅ full dashboard | ❌ | HIGH — should bypass |
| /check | ✅ check results | ✅ verdict interpretation | LOW — LLM judgment needed |
| /ship | ✅ ship_receipt.py | ✅ narrative on blockers | LOW — LLM judgment needed |
| /contract-status | ✅ health dashboard | ❌ | HIGH — should bypass |

## Skill-design anti-pattern

The skill-design mistake that creates this opening: **additive procedure steps**. The original /model-quota procedure had:

```
4. Read the grouped dashboard output
5. Optionally run GLM usage-query
6. Alert providers below 25% with actionable recommendations
```

Steps 4 and 6 tell the LLM to process and add to the script output. The LLM reasonably interprets "read + alert" as "summarize and add analysis." The script already generates the alert summary. Step 6 creates a second, manual alert-generation path that duplicates the code.

**The fix (applied):** replace additive steps with a single passthrough instruction:

```
4. Present the script's output as your response. The script produces the
   complete dashboard including alert summary. Do not narrate, summarize,
   or re-derive what the code already produced.
```

This was applied to /model-quota and generalized as an AGENTS.md rule. But per the falsifier analysis, the prose instruction alone is insufficient — the terminal alias is the reliable path.

## Related: skill-dev checklist item

Added to /skill-dev Mode 2 failure-mode table:

> **Procedure creates additive steps over code-produced output** — Script generates the report; procedure tells LLM to "read output" and "alert" — LLM narrates instead of passing through. Fix: Code-output passthrough (AGENTS.md): replace additive steps with "Present the script output as your response."

## Falsifier

This concept is wrong if:
- A future session shows the LLM reliably presenting script output without narration after the passthrough instruction was added (the prose rule works and the structural bypass is unnecessary)
- The narration is actually what the operator wanted (adding value, not duplicating) — disconfirmed by 5+ corrections in session 019fa8f8
- The pattern is specific to /model-quota and doesn't generalize to other code-complete-output skills

## Evidence

- Session 019fa8f8 chat_history.jsonl: 6+ narration instances, 5+ operator corrections
- /why analysis (same session): root cause = generation-by-default bias + procedure ambiguity
- /tp critique (same session): "shipped 3 prose fixes it knew could not work"
- /slc drift log (same session): "Performative self-awareness: agent generates analysis that sounds like accountability but functions as deferral"
- Post-fix re-failure: rule committed, next invocation narrated (immediate falsifier)
