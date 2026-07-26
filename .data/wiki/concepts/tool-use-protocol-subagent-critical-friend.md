---
title: "Tool Use Protocol for Subagent Critical-Friend Critique"
created: 2026-07-21
source: session-2026-07-21
tags: [critical-friend, subagent-design, evidence-chain, two-lens, fresh-prompt, failure-mode, design-pattern]
summary: >
  A fresh-subagent critique that runs without making any tool calls produces only
  an anchor-shared critique — it has no evidence outside the orchestrator's
  framing, so it cannot surface claims that the orchestrator's framing excluded.
  The structural fix: mandate a tool-use protocol that requires the subagent to
  cite file:line evidence for every finding, grounded in independent tool calls
  (read_file, grep, run_terminal_command), with explicit evidence-basis tags
  distinguishing tool-grounded claims from bundle-derived claims.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/external-state-cross-check-as-structural-fix
    type: refines
  - target: wiki/concepts/fabricated-causal-chain-receipt-required
    type: related
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: related
---

## Summary

When a critical-friend subagent runs with **zero tool calls**, every claim it produces is necessarily derived from the orchestrator's bundle — the bundle is the only input it has. This makes the "fresh lens" property an illusion: the subagent's framing is anchored to the orchestrator's, just with different wording. The structural fix is a tool-use protocol that forces independent evidence grounding.

## The failure mode

A two-lens critique architecture (orchestrator + fresh subagent) is structurally better than pure same-agent self-critique — *only if* the subagent actually has independent evidence to work with. If the subagent runs zero tool calls:

- Every claim comes from the orchestrator's bundle (filtered, framed, selected by the orchestrator).
- The subagent's "fresh perspective" is just a re-rendering of the orchestrator's framing.
- Findings that *don't fit* the orchestrator's framing cannot be surfaced — the subagent has no other source.
- The orchestrator's verification synthesis has nothing independent to verify against.

**Observed incident (2026-07-21):** A `/tp` critique was requested; the subagent returned 0 tool calls. The orchestrator's synthesis reported "0-tool-call bundle-only" critique as a structural finding — but couldn't verify whether the bundle had been faithful or what the subagent would have seen with grounding. The critique was either insightfully framing-anchored (useful) or completely faithful to a flawed bundle (waste of tokens). Indistinguishable from inside the same conversation.

## The protocol

When invoking a critical-friend subagent:

1. **Mandate tool access.** The subagent must have `read_file`, `grep`, `list_dir`, `run_terminal_command`, `web_search`, `web_fetch`, etc. — same tool surface as the orchestrator.
2. **Require evidence-basis tags.** Every finding must be tagged with one of:
   - `[from-bundle]` — finding derives only from the orchestrator-provided bundle (inherits orchestrator framing risk)
   - `[from-file-read <path:line>]` — finding grounded in a direct file read
   - `[from-grep <pattern> @ <path>]` — finding grounded in a grep result
   - `[from-command <one-line description>]` — finding grounded in a command output
   - `[from-first-principles]` — pure reasoning, no evidence anchor (label honestly)
3. **Cite file:line for grounded claims.** When the subagent cites a file path, include the line range or section.
4. **Require minimum tool-grounded finding ratio.** ≥ 50% of findings should be `[from-file-read]`, `[from-grep]`, or `[from-command]`. Findings tagged `[from-bundle]` should be flagged as suspect by the orchestrator's synthesis step.
5. **Advisory disclosure when 0 tool calls.** If the subagent returned without tool calls, the orchestrator MUST surface this: "Subagent made 0 tool calls; findings derive solely from bundle; this critique shares my framing."

## Why this works (the mechanism)

`[from-bundle]` claims are anchored to the orchestrator's framing. The orchestrator's framing has blind spots by construction (the very thing the critique is meant to challenge). `[from-file-read]` claims are anchored to the actual file content — independent of any framing. The orchestrator's verification synthesis can weight them differently, treating tool-grounded claims as having higher evidentiary value.

The protocol does not prevent a subagent from "going along" with the orchestrator's framing — but it ensures that, when the subagent has tool-grounded evidence, that evidence is distinguishable from framing-anchored reproduction. Without the protocol, the two are indistinguishable and the architecture is theater.

## Related patterns

- **[[external-state-cross-check-as-structural-fix]]** — the abstract principle: derive signal from state outside the actor's control. Tool-grounded findings are an instance; the actor (subagent) controls the bundle but not the file contents.
- **[[fabricated-causal-chain-receipt-required]]** — same anti-pattern at the claim level: a claim without a receipt is unreliable. Tool-use protocol enforces receipts at the finding level.
- **[[plausible-narratives-substitute-for-verification]]** — the failure mode is a plausible narrative: "the subagent has the bundle, that's enough." The tool-use protocol counters with a structural test, not a rule.

## Adoption

The `/tp` skill (Grok Build home at `~/.grok/skills/tp/SKILL.md`) implements this protocol as the default. The orchestrator spawns the subagent with an explicit "Tool access (use it — the fresh lens is grounded, not assumed)" preamble, with the five evidence-basis tags enumerated and the 0-tool-call advisory disclosure required. The verification synthesis step applies the tags to weight findings.

The protocol is host-agnostic. Any two-lens critique architecture (e.g., Claude Code's `/red-team` adversary mode, Grok Build's `/review` independent-verification step) can adopt it. The cost is one tool-call budget per finding — typically 5–10 additional tool calls per critique. The benefit is the structural distinction between framing-anchored and evidence-grounded claims.

## EVIDENCE_GAP

The ≥ 50% tool-grounded finding threshold is empirical — observed in 1 critique session (2026-07-21). Other thresholds (40%, 60%, 100%) untested. Calibration data needed across more sessions before declaring the threshold canonical.

## Auto-related

- [[skill-development-portfolio]]
- [[skill-catalog]]
- [[multi-agent-correlated-errors]]

