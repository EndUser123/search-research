# Expected evidence sheet — blind replay against session 019f6c3b

**Created before replay.** Based on reading the compaction segment independently of the AAR skill design.

## Validated successes (must appear as `validated_success`, not promoted)

1. Deep `/review yt-is` completed with 3 specialists + independent verify
2. C1+C2 trust floor implemented with 21/21 tests + `/check` PASS
3. Multi-model critique caught proposal flaws (both REVISE)
4. Skill hardening: path-only, terminal isolation, state files across 4 skills

## Resolved incidents (must appear as `resolved_incident`, NOT promoted to actions)

1. Plan mode stuck → resolved with AGENTS.md rule
2. 401 on BYOK subagents → resolved with terminal env loading
3. Inline paste → resolved with path-only protocol
4. Debrief hand-extracted → resolved (AAR replaces it)

## Open defects (must appear as `open_defect`)

1. 40 pre-existing test_nlm_batch.py failures from A1+A2

## Pending decisions (must appear as `pending_decision`, NOT `open_defect`)

1. Merge `trust-floor/phase-1` to main (user's call, not a defect)

## Recurring patterns (must cluster, not produce N separate actions)

1. "Epistemic overconfidence" — 3+ instances of proposing structural fixes without research

## Items that must NOT be promoted

1. Plan mode incident (resolved — no action needed)
2. 401 incident (resolved — no action needed)
3. Inline paste incident (resolved — no action needed)
4. Worktree checkout glitch (observation, resolved — no action needed)
5. State file isolation design choice (NOT a defect — by design)

## Expected accounting

- ~12 episodes total
- ~4 validated_success
- ~3-4 resolved_incident
- ~1-2 process_weakness
- ~1 pending_decision
- ~1 open_defect
- ~1 observation
- 0 unknown (if evidence is sufficient)
- 1-2 promoted actions (merge decision + fix 40 tests)
