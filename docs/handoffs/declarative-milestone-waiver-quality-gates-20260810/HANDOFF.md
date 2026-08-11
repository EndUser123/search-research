# Handoff: Declarative milestone waiver for quality gates

## Status

OPEN — design direction chosen (Option C), ready for implementation

## Design decision (2026-08-11)

After /why → /www → /tp → /design (2 rounds), the chosen direction is **Option C: skill-declared waiver eligibility**. Rationale:

1. The Grok Build Stop hook has NO non-blocking warn mode (verified by /design round 2 against `~/.grok/docs/user-guide/10-hooks.md:254-262`). The break-glass "block→warn" pattern from the field literature is not portable to this host. The only two modes are: block with feedback, or silent allow.
2. Option C follows the break-glass "Approved" property: the skill author (operator) declares `milestone_waiver_allowed: true` during authoring — the approver is the author, not the agent self-authorizing.
3. ~30 lines of code: add the frontmatter field + claim-text marker detection + allow path with audit entry.

The shipped interim mechanism (commits 485a499, fa6fb04, e0a8e9c) is accepted as a partial fix. The 30-min time-bound waiver is the wrong shape per field consensus but works as a stopgap until Option C ships.

Design doc preserved at: `P:/docs/design/waiver-mechanism-quality-gate-20260811/design-doc.md`

## Summary

Extend the existing declarative quality-gates system so skills can declare a `waiver_on_condition` field on their `quality_gates` frontmatter. When the agent's completion claim matches the condition (e.g., contains a milestone marker like "VS-02 of 5"), the gate auto-writes the waiver file instead of blocking. This generalizes the `review-waiver-{session_id}*.json` anti-loop fix beyond the review gate and moves the milestone/ship distinction into the skill's declaration rather than the agent's prompt.

## Context

### Problem

The Stop hook's review quality gate blocks whenever: (a) the agent claims completion, (b) code was modified, (c) no `/review` receipt exists. This is correct for ship claims but excessive for mid-build milestone claims (e.g., "VS-02 done, VS-03/04/05 remain").

Session 019fee63 (2026-08-10) diagnosed this via `/why` + `/www` + `/tp`:
- **Cause A (behavioral):** the agent asked the operator "waive or review?" instead of acting on its derived disposition. Fixed via AGENTS.md trigger case + `waiver_gate.py` helper script (committed this session to `~/.grok`).
- **Cause B (architectural):** the gate has no milestone-vs-ship scope distinction. This handoff addresses Cause B.

### What already exists

| Component | Location | Status |
|-----------|----------|--------|
| Declarative quality-gates frontmatter | `quality_gates_frontmatter.py:774` (`check_quality_gates()`) | Working — skills declare `quality_gates` in SKILL.md |
| General waiver API | `quality_gates_frontmatter.py:619` (`write_waiver()`) | Working — writes `quality-gate-waiver-{session_id}.json`, consumed per-turn |
| Review-gate anti-loop fix | `gate_diagnostics.py:570` (`_quality_gate_check()`) | Working — globs `review-waiver-{session_id}*.json`, persists per-session |
| Helper script | `~/.grok/scripts/waiver_gate.py` | Shipped this session — agent-invocable one-liner |
| AGENTS.md trigger case | `~/.grok/AGENTS.md` § Trigger cases | Shipped this session — documents the behavioral fix |

### What's missing

The anti-loop fix at `gate_diagnostics.py:570` is hardcoded for the review gate:
```python
for wf in waiver_dir.glob(f"review-waiver-{session_id}*.json"):
```

Other gates (check, ship, wiki-persistence) do not have this pattern. A general solution needs:
1. The glob generalized to `{gate}-waiver-{session_id}*.json`
2. Skills declaring waiver eligibility via frontmatter
3. The gate classifying milestone vs ship claims

## Scope

### Design decisions needed

1. **How does the gate classify "milestone" vs "ship"?** Options:
   - (a) Marker in the claim text (e.g., `[milestone]` tag) — fragile (string matching)
   - (b) Structured field in the claim (`claim_scope: milestone`) — requires `_claim_made()` extension
   - (c) Skill-declared condition in frontmatter (`waiver_on_condition: "claim contains 'VS-' and 'of'"`) — flexible but DSL-like
   - (d) External state (handoff or work-packet file that declares remaining sub-units) — most reliable but heaviest

2. **Should the waiver auto-write or should the agent still write it?**
   - Auto-write: the gate detects the condition and writes the waiver itself. Agent doesn't need to know about the API. But this removes agent agency.
   - Agent-write (current approach): the agent invokes `waiver_gate.py` when it derives the disposition. Gate checks for the file. Agent keeps agency but needs discoverability (solved by the AGENTS.md trigger case).

3. **Should this generalize beyond the review gate?**
   - Yes in principle, but other gates may have different semantics (e.g., `/check` is per-turn, not per-ship).

### Acceptance criteria

- [ ] Design decision on milestone-vs-ship classification (options a-d above)
- [ ] `gate_diagnostics.py:570` glob generalized from `review-waiver-` to `{gate}-waiver-` OR a registration mechanism added
- [ ] At least one skill's `quality_gates` frontmatter extended with the new field
- [ ] Test: milestone claim → gate auto-waives → agent continues without operator intervention
- [ ] Test: ship claim → gate still blocks (no regression)
- [ ] Test: milestone claim without the condition field → gate still blocks (opt-in, not default)

### Out of scope

- Redesigning the claim model (boolean → structured) — separate architectural effort
- Removing the review gate entirely — the gate is correct by design
- The behavioral fix (Cause A) — already shipped via `waiver_gate.py` + AGENTS.md

## Files to touch

| File | Change |
|------|--------|
| `~/.grok/hooks/scripts/quality_gate/gate_diagnostics.py:570` | Generalize glob or add condition-check |
| `~/.grok/hooks/scripts/quality_gates_frontmatter.py` | Parse `waiver_on_condition` from frontmatter |
| `~/.grok/skills/review/SKILL.md` | Add `waiver_on_condition` to `quality_gates` |
| `~/.grok/hooks/tests/test_quality_gates_frontmatter.py` | Add milestone-waiver tests |

## Authority

- Source session: 019fee63 (2026-08-10)
- Root cause analysis: `/why` on the Stop-hook block → Cause A (behavioral) + Cause B (architectural)
- External research: `/www` on scoped-claims pattern (Vercel) — mapping was a stretch; the existing waiver mechanism is the right backend
- Fresh-lens critique: `/tp` subagent (53 tool calls, 14 file-grounded findings) — confirmed the /www's recommendation duplicated the existing waiver API

## Provenance

Written from session 019fee63 after `/why` → `/www` → `/tp` chain on the Stop-hook review-gate friction. Cause A fixed in-session (commit 485a499 to `~/.grok`). Cause B deferred to this handoff.
