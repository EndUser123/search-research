---
title: "/why source-code citation rule: system-behavior claims must cite the code that produces the behavior"
created: 2026-07-27
source: session-019fa39d (/why RCA on why 3/8 findings were wrong)
tags: [skill-design, why-skill, evidence-tiers, source-code-citation, narrative-sufficiency, breadth-pressure, decision, cross-host]
summary: >
  Architectural decision: /why's Step 4b and Step 5 now require that any
  finding explaining WHY a system produced a specific output MUST cite the
  specific source-code location (file:line) that produces that output.
  Reading the system's output text (JSON, log, scanner result) is NOT
  sufficient — the cause lives in the code, not in the output the code
  produces. Without a source-code citation, the finding is automatically
  [INFERENCE], not [FACT]. Additionally, all findings must be emitted as
  [INFERENCE] first and upgraded to [FACT] only after a tool call reads
  the actual code. This prevents "narrative sufficiency under breadth
  pressure" — the pattern where explaining N gates from their JSON output
  feels sufficient but 3/8 findings turn out wrong because the narrative
  was constructed from output text, not source code. Root cause: a /why
  run on 8 close-scanner gates produced 8 findings, of which 3 were
  wrong (verify receipt not found, multi-terminal isolation violation,
  close_runner self-referential block). A fresh-lens /tp critique
  (glm-5-2, 24 tool calls reading code) caught all 3 by reading source.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
sources:
  - "Session 019fa39d /why run on 8 close-scanner gates (3 wrong, 5 correct)"
  - "Fresh-lens /tp critique subagent 019fa5e1-1907-7ea2-8aa4-9fdb8239885f (glm-5-2, 24 tool calls, 256s)"
  - "P:/.data/wiki/concepts/reactive-pattern-matching-and-closure-pressure.md (the behavioral substrate)"
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure
    type: refines — adds the specific breadth-pressure surface form to the general closure-pressure pattern
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: instance-of — this is a specific instance where narratives about system behavior substituted for code reading
  - target: wiki/concepts/workspace-improvement-opportunities-20260727
    type: related — opportunity #2 (workspace-wide evidence tiers) would extend this decision beyond /why
---

# /why source-code citation rule

## Receipts

- **[FACT]** 3 of 8 /why findings were wrong — receipt: /tp fresh-lens
  subagent `019fa5e1-1907-7ea2-8aa4-9fdb8239885f`, 24 tool calls,
  VERDICT: findings_corrected
- **[FACT]** The 3 wrong findings were: #2 (verify gate — scanner regex
  at `close_accounting.py:554` matches the format; no /check ran for
  this session), #7 (multi-terminal isolation — scanner HAS attribution
  at `close_accounting.py:1405-1438`, added in commit af6450f), #8
  (close_runner self-reference — JSON output at `close_accounting.py:2704`
  never contains "CLOSE INCOMPLETE"; line 565 in close_runner.py is dead
  code)
- **[FACT]** The correct root cause was found by the fresh-lens critique
  reading code at: `close_accounting.py:2117-2135` (continuation_coverage
  gate logic), `close_accounting.py:554` (verify regex),
  `close_accounting.py:1405-1438` (temp_files attribution),
  `close_runner.py:565` (dead code check)
- **[FACT]** The 3 fixes were applied at: `why/SKILL.md` Step 5
  (source-code citation rule), Step 4b (`source_code_citation` field),
  Rules section ([INFERENCE]-first protocol) — commit `d85f36c`

## Decision context

**Why this decision was needed.** A /why run analyzing 8 close-scanner
gates produced 8 findings. A /tp fresh-lens critique found 3 were wrong:
the findings narrated plausible causes from scanner JSON output without
reading the actual source code at each cited location. The pattern:
explaining N system behaviors from their output text (which feels
sufficient because the output is internally coherent) instead of reading
the N code locations that produce those outputs.

**The decision.** Add three structural requirements to /why:
1. Source-code citation rule (Step 5): system-output findings must cite
   file:line that produces the output
2. `source_code_citation` field (Step 4b): required for system-behavior
   claims; absent → automatically [INFERENCE]
3. [INFERENCE]-first protocol (Rules): emit each finding as [INFERENCE]
   first; upgrade to [FACT] only after a tool call reads the code

## Steelman (the rejected alternative)

**The prior approach was faster.** Explaining 8 gates from their JSON
output took one turn. Reading 8 code locations would take 8 tool calls
and significantly more time. The prior approach allowed breadth (cover
all N quickly) over depth (verify each N). For simple, obvious failures
where the output text IS the cause (e.g., "exit code 1 → the command
failed"), the prior approach works fine. The source-code citation rule
adds overhead to cases where it's unnecessary.

**Why this steelman loses:** the session proved that when the failure
involves system behavior (not just output), the output text is the
symptom, not the cause. 3/8 findings were wrong because they explained
symptoms. The overhead of code reading is justified by the 37.5% error
rate (3/8) on the prior approach. For obvious failures, --quick mode
skips the fan-out entirely, so the citation rule doesn't add overhead
where it's not needed.

## Falsifier

This decision is wrong if:
- The source-code citation rule is equally gameable as the prior
  approach (the model cites `file.py:42` without reading line 42) —
  would mean the problem is model behavior, not rule design. Mitigated
  by the [INFERENCE]-first protocol: the rule forces a tool call before
  the claim, not just a citation string.
- The rule adds so much overhead that /why runs become impractically
  slow for multi-finding analyses — would mean the trade-off (accuracy
  vs speed) favors speed. Mitigated by --quick mode for trivial cases.
- The rule prevents the model from making correct findings about systems
  it genuinely understands from prior context (e.g., code it wrote
  earlier in the session) — would mean the rule is too strict for
  legitimate cases. Mitigated by allowing [INFERENCE] upgrade to [FACT]
  after ANY code-reading tool call, including re-reads.

## Related

- [[reactive-pattern-matching-and-closure-pressure]] — the behavioral substrate this decision addresses
- [[plausible-narratives-substitute-for-verification]] — the general pattern; this is a specific surface form
- [[workspace-improvement-opportunities-20260727]] — opportunity #2 would extend evidence tiers workspace-wide
