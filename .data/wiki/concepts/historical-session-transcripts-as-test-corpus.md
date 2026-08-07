---
title: "Historical session transcripts as test corpus (operator correction x4)"
created: 2026-08-07
source: session-20260806
tags: [operator-correction, testing, measurement, historical-sessions, transcript, evidence]
summary: >
  The agent has 2,000+ historical session transcripts available at
  ~/.grok/sessions/*/chat_history.jsonl. Before claiming something "requires
  future sessions to measure," scan historical transcripts first. The operator
  corrected this pattern four times in one session — each time the agent said
  "needs future sessions" when 2,000+ sessions of data were immediately
  available. Now a durable rule in AGENTS.md.
agent: grok
host: grok
cognitive_load: 1
verification: observed
relations:
  - target: wiki/concepts/evidence-first-default-and-needless-confirmation.md
    type: extends
  - target: wiki/concepts/check-data-before-deferring.md
    type: extends
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# Historical session transcripts as test corpus

## Decision context

The operator corrected the same pattern four times in one session (2026-08-06):
1. Phase 4 hit-rate measurement for `/risk` — agent said "needs more real runs"
2. Creative-technique miss measurement — agent said "observe for 3-5 sessions"
3. Claim-detection measurement — agent said "needs future sessions"
4. DeepEval Layer 3 justification — agent said "measure for 5 sessions"

Each time, 2,000+ historical session transcripts were immediately available for the exact measurement needed.

## The pattern

The agent defaults to "collect data over time" when historical data already exists. This is the same failure class as `[[check-data-before-deferring]]`: deferring action when the data to act is already on disk. The specific form: "needs future sessions" when past sessions contain the evidence.

## What this means for our workspace

1. **AGENTS.md now has a rule** (added 2026-08-07): "Before claiming 'requires future sessions to measure,' scan historical transcripts first."
2. **`/skill-dev` updated**: the Tier 3 confidence ceiling now points to historical transcripts as the measurement corpus, not "live A/B testing."
3. **The transcript path**: `~/.grok/sessions/<encoded-cwd>/*/chat_history.jsonl` — JSONL format, `{"type":"assistant","content":[{"type":"text","text":"..."}]}`
4. **Scanning is cheap**: Python scripts can scan 200 sessions in ~30 seconds for regex pattern hits, compliance rates, behavioral signal frequencies.

## How to use historical sessions for measurement

```python
# Standard pattern: scan N sessions for a signal
from pathlib import Path
import json, re

SESSIONS_ROOT = Path.home() / ".grok" / "sessions" / "P%3A%5C"
chat_files = sorted(SESSIONS_ROOT.glob("*/chat_history.jsonl"),
                    key=lambda p: p.stat().st_mtime, reverse=True)

for f in chat_files[:200]:  # last 200 sessions
    for line in f.read_text(encoding='utf-8').split('\n'):
        if not line.strip(): continue
        msg = json.loads(line)
        if msg.get('type') != 'assistant': continue
        content = ' '.join(c.get('text','') for c in msg.get('content',[]) if isinstance(c, dict))
        # Check for your pattern here
```

## Falsifier

If a future session needs data that genuinely doesn't exist in historical transcripts (e.g., testing a hook that was just built — no historical session has it firing), then "needs future sessions" is the correct statement. The rule says scan first, not "historical sessions always have the answer."

## Receipts

- Operator correction x4, session 019fcdd2 (2026-08-06): "can't you use our historical session transcripts?" / "why not use them?"
- AGENTS.md rule added: `~/.grok/AGENTS.md` "Historical session transcripts are available for testing and measurement" paragraph
- `/skill-dev` SKILL.md line 496 updated: confidence ceiling now references historical transcripts
- 2,212 session directories verified: `Get-ChildItem "C:\Users\brsth\.grok\sessions\P%3A%5C" -Directory | Measure-Object`

## Related concepts

- [[evidence-first-default-and-needless-confirmation]] — the broader rule: check available evidence before asking
- [[check-data-before-deferring]] — the specific pattern: defer only after checking what's on disk
- [[mechanical-enforcement-over-behavioral-reminder]] — why the AGENTS.md rule alone has a ~50% ceiling; hooks and skill-level pointers are the structural fix

## Auto-related

- [[Are-there-repos-or-solutions-to-claude-code-gettin]]
- [[testing-methodology-both-outcomes-informative]]
- [[test-design-falsification-of-production-components]]
- [[operator-collaboration-style-and-leverage]]
- [[auto-test-stop-hooks-and-property-based-testing]]

