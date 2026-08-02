---
title: "Right-But-Insufficient: The Hidden Output Quality Failure"
created: 2026-08-02
source: session-019fbdfb
tags: [thought-partnership, quality, behavioral-pattern, meta-improvement]
summary: >
  The agent produces output that is technically correct but misses something
  the operator would have caught. This is a different failure mode from wrong
  output — it's "right but insufficient." The output passes all mechanical
  checks (tests, lint, receipt gates) but fails the operator's judgment check.
  No rule currently fires for sufficiency, only for correctness. The pattern
  manifests as: curated recommendations (completeness-over-curation), skipped
  process steps (ship Phase 1), dead-zone writes, and "good enough" output
  that the operator had to sharpen manually.
agent: grok
host: grok
cognitive_load: 2
verification: observed-verified
sources:
  - session-019fbdfb (2026-08-01): curated to top-2, skipped Phase 1, wrote to dead zone
  - session-019f9aff AAR (2026-07-26): 3 corrections in one session
relations:
  - target: wiki/concepts/completeness-over-curation-recommendation-discipline.md
    type: extends
  - target: wiki/concepts/ship-phase-log-enforcement-design.md
    type: extends
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
  - target: wiki/concepts/trust-over-believability.md
    type: related
---

# Right-But-Insufficient: The Hidden Output Quality Failure

## Decision context

**The problem:** The agent produces output that is technically correct but misses something. The output passes all mechanical checks (tests pass, lint clean, receipts valid) but fails the operator's judgment check. The operator catches the gap manually — every time.

This is a different failure mode from wrong output. Wrong output is detectable by tests, hooks, and validators. Right-but-insufficient output is only detectable by the operator reading between the lines.

## Manifestations from session 019fbdfb

1. **Curated recommendations** — agent listed 2 of 20 ideas. Technically correct (the 2 were good), but insufficient (18 more had positive ROI). Fixed by completeness-over-curation rule.

2. **Skipped Phase 1 review** — agent ran Phase 3 receipt (passed), filled in LLM fields, emitted SHIP DONE. Technically correct (receipt passed), but insufficient (Phase 1 was never run). Fixed by phase-log enforcement.

3. **Dead-zone write** — agent wrote improvement backlog to docs/plans/. Technically correct (file was written, committed), but insufficient (no skill scans docs/plans/). Fixed by dead-zone guard hook.

4. **Short /tp recommendation list** — agent's first /tp session output had 2 items. Technically correct (both were valid), but insufficient (15+ items had positive ROI). Fixed by completeness-over-curation rule + completeness counter.

## The meta-pattern

Each instance was "right but insufficient." The agent didn't produce wrong output — it produced output that was technically defensible but missed the operator's standard. No mechanical check catches this because:
- Tests check correctness, not sufficiency
- Hooks check process compliance, not output quality
- Validators check format, not content depth

The only detector is the operator's judgment — which means the failure recurs until the operator catches it and adds a rule.

## What this means for our workspace

This extends the [[completeness-over-curation-recommendation-discipline]] and [[ship-phase-log-enforcement-design]] concepts by naming the meta-pattern they're instances of. The [[mechanical-enforcement-over-behavioral-reminder]] principle applies: each instance was eventually fixed by a mechanical guard (rule, hook, counter), not by prose reminders.

The pattern connects to [[trust-over-believability]]: right-but-insufficient output erodes trust because the operator has to constantly verify not just correctness but completeness. "Did the agent do everything, or just enough to pass?"

**The structural fix is a two-layer quality gate:**
1. Mechanical layer (existing): tests, hooks, validators check correctness
2. Sufficiency layer (emerging): completeness counters, phase-logs, chronicity tags, "not captured" sections check whether the output is complete, not just correct

The sufficiency layer is what this session built — the completeness counter in /tp, the phase-log in /ship, the dead-zone guard, the "not captured" section in /capture. Each is a structural guard against right-but-insufficient output.

## Falsifier

If the sufficiency layer (counters, phase-logs, dead-zone guards, "not captured" sections) eliminates the right-but-insufficient pattern, this concept is proven. If the pattern persists despite these guards, the guards are insufficient and a deeper structural fix is needed (e.g., a hook that checks output completeness against a session-scope estimate).

## Sources

- Session 019fbdfb (2026-08-01/02): 4 instances of right-but-insufficient output
- Session 019f9aff AAR (2026-07-26): 3 corrections, all right-but-insufficient class
- AGENTS.md § "Completeness over curation" — the rule that addresses manifestation #1 and #4
- `ship-phase-log-enforcement-design.md` — the enforcement that addresses manifestation #2
- `dead_zone_guard.py` — the hook that addresses manifestation #3

## Receipts

- AGENTS.md line 1041: "Completeness over curation" rule
- `C:/Users/brsth/.grok/hooks/scripts/dead_zone_guard.py` — PreToolUse hook blocking dead-zone writes
- `C:/Users/brsth/.grok/skills/go/__lib/ship_receipt.py` `validate_phase_log()` — phase-log enforcement
- `C:/Users/brsth/.grok/skills/tp/SKILL.md` completeness counter: `findings_total: N, omitted: 0`

## Auto-related

- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[hook-fleet-io-failure-modes-cascade-amplification]]
- [[claude-code-external-tool-integration-via-mcp]]
- [[research-quality-principle-efficiency-not-censorship]]
- [[visible-output-contracts-for-behavioral-skill-steps]]

