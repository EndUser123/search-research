---
title: "Plausible narratives substitute for verification"
created: 2026-07-20
source: session-2026-07-20
tags: [cognitive-pattern, verification, root-cause, failure-mode, llm-behavior]
summary: >
  When an LLM constructs a plausible narrative for why something can't be done,
  found, or known, the narrative feels like an answer and causes the model to
  stop investigating. The narrative is often wrong. The fix: treat the narrative
  as the signal to read documentation, not as the answer.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/solo_operator_adr_best_practices
    type: related
  - target: wiki/concepts/skill-enforcement-layers
    type: related
---

# Plausible narratives substitute for verification

## The pattern

The model encounters a claim it can't immediately verify. Instead of reading
documentation or searching for evidence, it:

1. Constructs a plausible narrative explaining why the claim is wrong / the
   data doesn't exist / the approach can't work
2. The narrative feels sufficient ("structurally impossible," "the hook fires
   before X")
3. The model presents the narrative as its answer
4. The narrative is wrong, but the model doesn't discover this until the user
   pushes back or external evidence arrives

## Why this is dangerous

The narrative is internally consistent and plausible. It sounds like expertise.
The user has a trust bias and may not catch it. The result: wrong conclusions
shipped with confidence, sometimes causing real damage (e.g., removing
protection that was actually active, or claiming data doesn't exist when it's
in the next file over).

## Observed instances (2026-07-20 session, 5 cases)

| # | Instance | The plausible narrative | The reality |
|---|----------|------------------------|-------------|
| 1 | Claude hooks not firing | "Hooks are wired in settings.json, they must be firing" | `compat.claude.hooks=false` — hooks NOT firing |
| 2 | proposal-grounding-monitor exists | "I'm proposing to build Observe-Before-Propose from scratch" | Already existed, 111 tests, orphaned in `~/.grok/plugins/` |
| 3 | MCP servers not enumerated | "Enumeration is structurally impossible; hook fires before MCP connects" | MCP config IS in `~/.claude.json` and `.mcp.json`, documented at `07-mcp-servers.md:200-213` |
| 4 | Design doc durability (C1/C2) | "Provenance matters, durability is the right answer" | User's wiki already absorbs decisions as concepts; durability was over-engineering |
| 5 | Review skill confusion | "adv-review exists, I don't know why" | Was an unbuilt stub; deleted without checking why it was created |

## Chronic recurrence: MCP config not checked (2026-07-28)

**Instance 3 repeated 8 days later** with the exact same root cause —
checking only one MCP config location (`config.toml`) and fabricating
a "never configured" narrative when the config was actually in
`~/.claude.json` (Claude compat bridge).

| Date | Claim | Reality | Config location not checked |
|------|-------|---------|---------------------------|
| 2026-07-20 | "MCP config doesn't exist in static config" | MCP config IS in `~/.claude.json` | `~/.claude.json` |
| 2026-07-28 | "minimax-search was never configured" | minimax-search IS in `~/.claude.json` via compat bridge | `~/.claude.json` |

Both instances: same file not checked, same fabricated narrative shape
(absence → structural impossibility → confident claim), same wiki concept
already documenting the pattern. The fix in both cases was reading the
file the wiki already names.

**Resolution (2026-07-28):** minimax-search MCP removed entirely (its
capabilities are covered by `mmx search query` and `mmx vision describe` —
native CLI, no compat bridge). web-search-prime migrated from
`~/.claude.json` to native `config.toml`. After migration, `~/.claude.json`
no longer contains any MCP servers that this host depends on — eliminating
the "wrong config file" failure mode for future sessions.

## Root cause

**Plausible narratives override existing rules.** The workspace had rules
that would have prevented each instance (Observe-Before-Propose, Absence
Conclusions, Host runtime verification). The model broke all of them. The
problem isn't missing rules — it's that when a plausible narrative forms,
the model treats it as sufficient and stops applying the rules.

## Structural fix

When you catch yourself constructing a narrative for why something **can't
be done, can't be found, or doesn't exist**:

1. **Stop.** The narrative is a signal, not an answer.
2. **Read the documentation** for the system in question.
3. **Check the obvious config locations** the docs name.
4. **Ask: am I conflating the finding with the fix?** A wrong fix does not
   invalidate a correct finding.
5. **Ask: is my narrative grounded in observed evidence, or inference?**

## Anti-conflation rule

When evaluating an external review or critique, evaluate the finding and the
proposed fix **independently**. The MCP instance: the finding (MCP not
enumerated) was correct; the fix (read `[mcp_servers]`) was wrong because
that section doesn't exist. The model dismissed both because it conflated them.

## Disguise variants (added 2026-07-20)

The pattern has multiple surface disguises. Fixing one instance doesn't
inoculate against the others — the operator's own session-skip incident
documented in [[host-surface-boundary]] is a recurrence in a new disguise
hours after the original page was written.

### Disguise 1 (original): structural impossibility

"I can't enumerate MCP because the hook fires before MCP servers connect."
Narrative substitutes for reading the documentation that names the static
config files. Fix: read the docs.

### Disguise 2 (2026-07-20 addition): infrastructure availability

"I see `Stop_*.py` hooks with a clean dispatch chain. Extending it is the
natural intervention point." Narrative substitutes for verifying the
intervention point applies to the current host. The hooks physically exist
in `P:/.claude/` but don't fire for Grok Build (`compat.claude.hooks=false`).
Fix: treat any cross-tree infrastructure discovery as a signal to verify
host applicability, not as an invitation to edit. See
[[host-surface-boundary]] for the full taxonomy and mechanical fix.

### Disguise 3 (2026-07-20 addition): future-intent storytelling

"Reference material for a capability nobody is currently planning to build."
Narrative fills the gap between what the artifacts show and what someone
plans to do. Fix: report what you can verify; stop where the evidence stops;
label the rest `[UNKNOWN]` or `[INFERENCE]` explicitly. (From the original
AGENTS.md § "Subagent synthesis → report gate" companion rule.)

### Disguise 4 (2026-07-20 addition): unmeasured-frequency storytelling

"This failure mode is rare." Narrative asserts frequency without measurement.
Fix: state the absence of measurement explicitly ("no frequency data
available") rather than narrating a plausible rate.

### Disguise 5 (2026-07-20 addition): metadata-self-report-as-answer

"The handoff says `status: open`, so the work is open." Narrative substitutes
the actor-authored metadata field for verification against current reality.
The field is a *claim by the author*, not evidence about the world — but it
feels like evidence because it's structured data in a file. Triage completes
on the claim without cross-checking whether the work is actually still open,
whether the cited tree paths still exist, or whether a newer session has
already superseded the handoff. This disguise is particularly dangerous
because structured metadata *looks* more authoritative than prose.

**Worked example (2026-07-20):** triaging 8 handoffs, the model propagated
each handoff's self-reported `status: open` into its triage table without
opening the files. 4 of 8 dispositions were wrong: two handoffs' bodies
said "CLOSED" despite `status: open` in YAML; two `[UNKNOWN]` outcomes were
answerable with 30 seconds of file inspection. Forcing proof per item —
"every row needs evidence independent of the handoff's own status field" —
flipped 4 of 8.

**Fix:** treat any actor-authored metadata field as an unverified claim.
The investigation target is external state the author cannot self-certify:
current HEAD vs the handoff's `accurate_as_of_head`, body `## Status` vs
YAML `status`, cited file:line existence against the current tree. See
[[external-state-cross-check-as-structural-fix]] for the design pattern
that makes this verification automatic rather than discipline-dependent.

### Disguise 6 (2026-07-21 addition): time-indexed-claim-as-current

"DeepSeek V4 Flash is SOTA in agentic coding." Narrative treats a
time-stamped benchmark claim as if it were a permanent property of the
model. The claim was true in April 2026 (79.0% SWE-bench Verified, leading
open models). By July 2026 the landscape has moved: Flash-Max variant
shipped, GPT-5.5 and Claude Opus 4.7 entered the comparison, and the
relative ranking is no longer current. But the original claim feels
authoritative because it was verifiably true at publication time.

**Why this is a distinct disguise, not just outdated information:**
outdated information fails when re-checked. This disguise fails *earlier* —
the moment someone treats "was SOTA in April" as "is SOTA today" without
re-checking. The narrative bridges the time gap with a silent assumption
that model rankings are stable, when they turn over in weeks. The fix is
not "update the claim more often"; it's to label every SOTA-tier claim
with its as-of date and treat unlabeled claims as unverified.

**Worked example (2026-07-21):** the model was told DeepSeek V4 Flash was
SOTA. It built a tier taxonomy on that premise. The user corrected:
"depends on the generation." The taxonomy was wrong not because the April
data was wrong, but because the model treated April data as July truth
without checking whether the ranking still held.

**Fix:** when a capability claim has a time dimension (SOTA rankings,
benchmark scores, model availability, pricing), the investigation target
is *current* evidence — a fresh benchmark lookup, a live API probe, a
recent comparison page. Stated criterion: if the claim's truth could have
changed since it was made, the claim is unverified until re-checked
against current sources. This is the same shape as Disguise 5
(actor-authored metadata as current truth) but with *time* as the gap
instead of *author bias*.

### Disguise 7 (2026-07-20 addition): tool-output-as-verification

"The file is 325 lines, verified by direct file inspection." Narrative substitutes
tool output for understanding of what the tool measures. The reviewer ran
`Measure-Object -Line`, got 325, and treated it as "the verified line count."
But `Measure-Object -Line` counts **non-empty lines**, not total lines. The
actual total is 371 (verified by `.Count` and `splitlines()`). The reviewer's
"correction" of the writer's 371 → 325 was itself wrong — it shipped with
confidence because it came from a tool call, but the reviewer didn't understand
what the tool measured.

**Why this is a distinct disguise, not just a wrong number:** the failure is not
"the tool gave bad data." The tool gave correct data for what it measures
(non-empty lines = 325). The failure is that the reviewer **treated tool output
as verification without understanding the tool's semantics**. The number felt
authoritative because it came from a command, not from memory or inference. But
"ran a command" is not the same as "verified the claim" — the command has to
measure what you think it measures.

**Worked example (2026-07-20):** during a design review loop, the writer claimed
`Stop_claim_gap_telemetry_probe.py` is "371 lines." The reviewer "corrected"
this to "325 lines, verified by direct file inspection" using
`(Get-Content | Measure-Object -Line).Lines`. The writer accepted the correction
and updated all references. Both the reviewer's correction and the writer's
acceptance were instances of the anti-pattern: the reviewer didn't understand
that `-Line` counts non-empty lines only; the writer accepted the authority of
the correction without independent verification. The original 371 was correct
all along.

**This disguise is particularly dangerous because it defeats the external-state
cross-check.** The reviewer was supposed to be the external-state cross-check
for the writer (see [[external-state-cross-check-as-structural-fix]]). But the
reviewer's own verification was flawed — they ran a tool, got a number, and
treated it as ground truth without understanding what the tool measured. The
correction mechanism itself was infected by the failure mode it was supposed to
catch.

**Fix:** when a tool produces a number that will be used as a verified claim,
state what the tool measures in the same breath as the number. "325 non-empty
lines (via `Measure-Object -Line`)" is honest; "325 lines, verified" is not.
The investigation target is the **tool's semantics**, not just its output.

### Common shape

All seven disguises share the same structure: the model has gaps (in
documentation, in host-applicability, in future intent, in measurement, in
current-state knowledge, in temporal currency), constructs a plausible
story to fill the gap (or treats an actor-authored or time-stamped field
as filling it), and treats the story as sufficient. The structural fix
from the original page still applies — **treat the narrative as the
signal to investigate, not as the answer** — but the investigation target
differs per disguise:

| Disguise | Investigation target |
|---|---|
| 1. Structural impossibility | Read the docs for the system in question |
| 2. Infrastructure availability | Verify the infrastructure applies to the current host |
| 3. Future-intent | Stop narrating; label `[UNKNOWN]` |
| 4. Unmeasured frequency | State the absence of measurement explicitly |
| 5. Metadata self-report | Cross-check against external state the author cannot self-certify |
| 6. Time-indexed claim | Re-check against current sources; label with as-of date |
| 7. Tool output as verification | State what the tool measures, not just its output; verify tool semantics |

## Related

- `P:/AGENTS.md` "Narrative-as-signal" section — the workspace rule
- `P:/AGENTS.md` "Observe-Before-Propose" section — the predecessor rule
- `P:/docs/handoffs/plausible-narratives-substitute-for-verification-20260720/HANDOFF.md` — full investigation with 5 instances and task packets
- [[external-state-cross-check-as-structural-fix]] — the design pattern for making disguise-5 verification automatic

## Auto-related

- [[optimality-claims-are-completion-claims]]
- [[go-home-narrative-fabricated-session-state-constraints]]
- [[tool-use-protocol-subagent-critical-friend]]
- [[skill-techniques-index]]
- [[external-state-cross-check-as-structural-fix]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
