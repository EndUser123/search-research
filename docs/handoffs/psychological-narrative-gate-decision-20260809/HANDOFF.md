---
title: "Psychological-narrative gate — operator decision required"
status: OPEN
created: 2026-08-09
last_updated_at: 2026-08-09T20:35:00Z
assignee: unassigned
session_origin: 019fdf3d-a0bd-7062-abc4-24dcf064ae49
---

# Psychological-narrative gate: operator decision required

## Context

The psychological-narrative Stop hook (`Stop_psychological_narrative_gate.py`)
was built in session 019fdf3d. It uses phrase-detection regex to catch
psychological self-narratives ("I was defensive", "I got anchored") without
accompanying observable process-failure translation.

## Problems found

1. **Zero dedicated tests** — `pytest -k psychological` collects zero tests. No test file references this hook.
2. **Recall gap** — "I was being defensive" passes (exit 0); should block.
3. **Meta-discussion triggers** — discussing the gate in an audit triggers it.
4. **Mechanism questioned by operator** — operator stated preference for structured `observed_process_failure` field over phrase blacklist.
5. **Behavioral overlap test** — corpus testing proved psych-narrative and narrative-sufficiency gates are DISJOINT (0/18 samples overlapped). They target different surfaces.

## Operator's stated position (prompts 119, 126, 127)

- The direction (structured `observed_process_failure` field) is preferred long-term
- The current mechanism (regex phrase detection) is acceptable-for-now
- "Leave the psychological-narrative hook alone for now"
- Do not expand the regex further

## Decision required

The operator must decide one of:

1. **Keep as-is** — accept the recall gap and meta-discussion triggers; the gate provides partial value
2. **Replace with structured field** — enforce a `root_cause: observed_process_failure:` YAML artifact instead of regex
3. **Remove** — the AGENTS.md prose rule covers the behavior; narrative-sufficiency gate catches the general "plausible story without receipt" pattern
4. **Add tests only** — keep the mechanism but write the missing test suite to catch regressions

## Related

- Hook: `~/.grok/hooks/Stop_psychological_narrative_gate.py`
- Wiki: `[[psychological-narrative-vs-observable-process-failure]]`
- Wiki: `[[obligation-enforcement-vs-justification-detection]]` (the structural-vs-regex principle)
- Behavioral overlap test: `P:/tmp/behavioral_overlap_corpus.py` (temp — results captured in session AAR)
