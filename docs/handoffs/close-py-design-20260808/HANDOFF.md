# HANDOFF: close-py design — Python-orchestrated session close

## Status
OPEN — design needed

## Objective
Design close-py: a Python-orchestrated session close skill analogous to ship-py for publish-readiness. The operator stated this is planned.

## Context
- ship-py (at `~/.grok/skills/ship-py/`) is the existing Python-orchestrated verify-and-publish pipeline
- `/close` (at `~/.grok/skills/close/`) is the existing prose-based session close skill
- close-py would be the Python-controlled version of `/close`, applying the same anti-fabrication architecture developed for ship-py this session

## Key design questions
1. **What does close-py control that /close doesn't?** /close already has a scanner, accounting, and gate resolution. close-py would add: Python-controlled phase ordering, polling loop at judgment phases, anti-fabrication gates (suspicion gates, transition chain).
2. **Ship-py integration:** close-py should consume ship-py's verdict (SHIP DONE / SHIP VERIFIED / SHIP BLOCKED) as a signal. If ship-py was never invoked, close-py should note that but not require it.
3. **Shared anti-fabrication patterns:** the tamper-evident chain, suspicion gates, and polling loop pattern are reusable. Consider extracting to a shared `__lib/__anti_fabrication__` module that both ship-py and close-py import.
4. **What phases does close-py have?** Candidates: handoff-scan → wiki-capture → git-push-check → session-accounting → close-verdict.

## Acceptance criteria
- Design document produced via `/design`
- Reuses ship-py's polling loop and anti-fabrication patterns
- Consumes ship-py state as input
- Documents the integration contract between ship-py and close-py

## Suggested next invocation
```
/design close-py: Python-orchestrated session close consuming ship-py verdict, with anti-fabrication architecture
```

## References
- `~/.grok/skills/ship-py/` — existing pipeline to model after
- `~/.grok/skills/close/` — existing prose-based close skill
- `P:/.data/wiki/concepts/making-llm-agents-honestly-execute-skills-solution-stack.md` — anti-fabrication architecture
- `P:/.data/wiki/concepts/specification-gaming-in-llm-agent-pipelines.md` — specification gaming diagnosis
