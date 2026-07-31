---
thread_id: 019fa8f8-www-phase2b-skip
parent_handoff_path: none
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: grok-main
produced_at: 2026-07-31T10:00:00-06:00
status: open
handoff_type: investigation
accurate_as_of_head: 5755e5d
---

# Handoff: /www Phase 2b (practitioner signal) skipped — enforcement gap

## 1. Objective

Fix the /www skill so the mandatory practitioner signal pass (Phase 2b: Reddit, HN, YouTube, GitHub Issues) cannot be silently skipped during research runs.

## 2. Status

OPEN — not started. The operator caught the skip during the model routing /www run this session.

## 3. Producing context

During the final /www run of session 20260730/31 (model routing research), the operator asked "did we check reddit, youtube, hackernews, etc?" The answer was no — Phase 2b was skipped despite being labeled "mandatory" in /www SKILL.md. This is a recurring behavioral compliance failure: the skill says mandatory, the LLM skips it under session length/time pressure.

## 4. Read-first list

1. `~/.grok/skills/www/SKILL.md` — Phase 2b section (lines ~283-350)
2. `P:/.data/wiki/concepts/research-quality-principle-efficiency-not-censorship.md` — the principle Phase 2b serves
3. `P:/.data/wiki/concepts/agentic-harness-seven-components-2026.md` — system prompt is the only component that regresses alone; behavioral "mandatory" without mechanical enforcement is noise

## 5. Verified facts

- [FACT] /www SKILL.md Phase 2b says "mandatory, default ON" and lists HN Algolia + Reddit + GitHub Issues + YouTube as required sources (session 20260730, SKILL.md read)
- [FACT] Phase 2b was skipped in at least 2 /www runs this session (model routing research, quota API discovery)
- [FACT] The /www copyable checklist includes Phase 2b as a tickbox, but the LLM didn't tick it
- [FACT] The agentic harness paper (arXiv 2604.25850) confirms: "discipline without machinery is noise" — behavioral "mandatory" labels don't produce compliance

## 6. Current state

Phase 2b is documented as mandatory but has no mechanical enforcement. The LLM skips it when the session is long or the operator hasn't explicitly asked for practitioner signal. The operator catches it after the fact, which costs a turn.

## 7. Task packets

### WWW-P2B-01: Add mechanical enforcement for Phase 2b
- **goal:** prevent /www from completing Phase 3 (persist) without evidence that Phase 2b ran
- **in scope:** /www SKILL.md; optionally a wiki_write pre-check that scans for [PRACTITIONER] tags
- **out of scope:** changing which sources Phase 2b uses
- **files / anchors:** `~/.grok/skills/www/SKILL.md` Phase 2b section; Phase 3 persist section
- **acceptance:** a fresh /www run cannot reach wiki write without either (a) producing practitioner-tagged findings, or (b) explicitly disclosing "Phase 2b skipped: <reason>" in the output
- **falsifier:** if a /www run completes with a wiki concept but no [PRACTITIONER] findings and no skip disclosure, the enforcement failed
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** 30 min

**Options for enforcement:**
1. Add a validation step to the wiki write pipeline (like `validate_disconfirmation.py`) that checks for practitioner signal
2. Make Phase 2b a structural checkpoint that blocks Phase 3 if not completed
3. Add a /www-specific PostToolUse or Stop hook that checks for [PRACTITIONER] tags before allowing wiki write

## 8. Open decisions

None — investigation first, implementation decision after reading the skill.

## 9. Hard constraints

- Do NOT change Phase 2b sources (Reddit, HN, GitHub Issues, YouTube are correct)
- Do NOT remove the "mandatory" label — fix the enforcement, not the documentation

## 10. Cross-reference couplings

- `P:/.data/wiki/concepts/research-quality-principle-efficiency-not-censorship.md` — Phase 2b serves this principle
- `~/.grok/skills/www/SKILL.md` Phase 3 — the persist step that should gate on Phase 2b completion

## 11. Other outstanding streams

- Red-team /design skill → `P:/docs/handoffs/design-skill-red-team-20260730/HANDOFF.md`
- Research lane design → `P:/docs/handoffs/session-observations-20260731/HANDOFF.md`

## 12. Explicit non-goals

- Do NOT rewrite the /www skill
- Do NOT change the sources Phase 2b uses
- Do NOT make Phase 2b optional — fix enforcement, not the requirement

## 13. Resumption protocol

1. Read /www SKILL.md Phase 2b section
2. Decide enforcement mechanism (validation script, structural checkpoint, or hook)
3. Implement
4. Test with a real /www run

## 14. Suggested next invocation

```
/go add mechanical enforcement to /www Phase 2b so the practitioner signal pass cannot be silently skipped during research runs. See P:/docs/handoffs/www-phase2b-enforcement-20260731/HANDOFF.md for details.
```

## 15. Last user message (verbatim)

> "did we check reddit, youtube, hackernews, etc?"

## 16. Epistemic labels

- Phase 2b skipped: [FACT] — operator caught it
- Recurring pattern: [INFERENCE] — happened at least twice this session, may have happened in prior sessions
- Enforcement approach: [UNKNOWN] — the right mechanism needs investigation
