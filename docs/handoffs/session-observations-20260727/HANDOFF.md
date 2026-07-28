---
title: session-observations-20260727
current_session_id: 019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9
parent_handoff_path: none
status: open
created: 2026-07-27
---

# Session observations — 2026-07-27

Session `019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9` (spans 2026-07-26 to 2026-07-27,
compacted once). Multi-stream effort: close_runner BUG-03 fix, /notice v1→v2,
/why Step 0.5+4b, /skill-dev v1.0→v1.2, DBR English-only hooks, index_skills
--full-body, /tp exploration directives, per-turn thought-partner protocol,
/red-team hardening, nemotron routing fix.

## Observations worth capturing

### 1. Exploration belongs in /tp, not a standalone skill
- **Source:** operator decision 2026-07-27: "the answer is 'rarely' (exploration
  usually leads to something that needs challenging) → keep it in /tp"
- **Implication:** exploration (decompose, abstract, counterfactual, analogical)
  naturally feeds into critique. A standalone /insights skill would create a
  pipeline where output isn't challenged. /tp's composition interface (commit
  558daba) documents how other skills call /tp.
- **For next session:** if someone proposes an /insights skill, point at this
  decision. The architecture is: explore within /tp, let the critique phase
  challenge the exploration output.

### 2. /tp flip pattern — the model agreed then immediately reversed without new evidence
- **Source:** operator caught: "/tp you just flipped. Now I don't actually know
  what's best."
- **Pattern:** proposed /insights standalone → agreed → flipped to /tp explore
  → no new evidence cited for the reversal.
- **Fix already shipped:** single-pass deliberation rule in AGENTS.md. But the
  pattern recurred despite the rule existing. The rule needs to be checked
  BEFORE flipping, not cited after being caught.

### 3. Compaction-inherited diagnosis carried wrong root cause across session boundary
- **Source:** post-compaction, session inherited "scanner limitation" diagnosis
  from the summary. /why Step 0.5 didn't query handoffs. Actual cause was
  close_runner gate-state contract (BUG-03).
- **Fix shipped:** /why Step 0.5 now queries handoffs; Step 4b labels
  compaction summaries as Tier 4. Wiki concept:
  [[compaction-inherited-diagnosis-unverified-propagation]].
- **For next session:** compaction summaries are NOT receipts. Any diagnostic
  claim inherited from a compaction summary must be re-verified before acting.

### 4. Nemotron routing policy: PI for spawns, opencode for tool-rich investigation
- **Source:** nemotron broken via serde in spawn_subagent. AGENTS.md updated but
  /go/reference/model-routing.md still had the old slug. Operator caught the
  propagation gap.
- **Policy:** PI preferred for model-routing spawns (~200 token system prompt).
  opencode for tool-rich investigation (~10K token overhead). nvidia-nemotron-3-ultra
  never via spawn_subagent.
- **For next session:** when changing a routing policy, grep ALL files for the
  old value, not just the obvious ones.

### 5. /notice v2.0: content-triggered detection > fixed-rate cooldown
- **Source:** operator: "'/notice' doesn't need to remain completely mechanical.
  good skills are adaptive."
- **Design:** replaced fixed 1/10-turn cooldown with content-triggered detection
  + motivation scoring (8 heuristics from Inner Thoughts framework).
- **For next session:** the adaptive calibration (threshold adjusts based on
  operator response) is untested at runtime. Needs observation over several
  sessions to validate the calibration loop.

### 6. Per-turn thought-partner protocol consolidated 8 behavioral rules into one checklist
- **Source:** operator: "What makes a session great is hard to quantify. You
  would need to consistently be a thought partner..."
- **The protocol:** 8 items across 3 phases (before/while/before-finishing).
- **For next session:** the protocol is in AGENTS.md but has no mechanical
  enforcement. It relies on the model checking itself each turn. Effectiveness
  depends on whether the model actually runs the checklist or just knows it
  exists.

### 7. Behavioral correction tracking — rule exists, mechanism doesn't
- **Source:** multiple operator corrections this session (didn't query wiki,
  invented heuristics, overrode instructions, didn't propagate changes).
- **Gap:** AGENTS.md has the rule for tracking behavioral corrections, but no
  state file or scan script implements it. The Layer 2 measurement loop is
  documented but not built.
- **For next session:** this is chronic (recurs across sessions). Either build
  the tracking mechanism or write a handoff for it.

### 8. /skill-dev Mode 2 runtime gate still unresolved
- **Source:** held-out validation is self-judged; needs temp-copy + /grok-verify
  protocol.
- **Gap:** the "improve" mode proposes changes but can't validate them at
  runtime without a protocol for testing skill modifications in isolation.
- **For next session:** the temp-copy + /grok-verify approach is documented in
  the /skill-dev handoff but not implemented.
