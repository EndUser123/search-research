---
title: "Fail-open masking: error collapsed to clean verdict by missing exit-code check"
created: 2026-08-09
source: session-019fe403 (secret-scan JSONDecodeError collapsed to PASS)
tags: [failure-pattern, fail-open, error-masking, exit-code, ship-py, bug-class]
host: grok
agent: grok
verification: observed
relations:
  - target: wiki/concepts/rag-apr-evidence-retrieval-augmented-generation-improves-llm-bug-repair.md
    type: supports — fills gap in wiki failure-pattern coverage for /why-in-fix
summary: >
  When a subprocess returns non-zero exit code but its stdout can't be parsed
  as JSON, the error collapses to empty findings → clean verdict (PASS). The
  exit code is recorded but never consulted. Fix: consult BOTH parsed findings
  AND exit code. Exit 1 with empty findings (parse failure) should WARN, not
  PASS. Exit 2+ (tool error) should WARN.
---

# Fail-open masking: error collapsed to clean verdict

## The pattern

```
Subprocess runs → returns exit code 1 (error)
  ↓
stdout is not valid JSON (or empty)
  ↓
JSONDecodeError → findings = []
  ↓
verdict = "PASS" if not findings else "BLOCK"
  ↓
Error silently masked as clean scan
```

## Evidence

**ship-py secret-scan bug (session 019fe403):** When gitleaks returned exit
code 1 (leaks found) but stdout wasn't valid JSON (parse error or truncated
output), the code collapsed to `findings = []` and set verdict to "PASS."
A broken config or non-JSON gitleaks output masked the scan as clean.

The exit code was recorded in `state["secret_scan_findings"]["exit_code"]`
but never consulted for the verdict decision.

## How to detect this bug class

- **Symptom:** a tool failure is reported as "clean" or "pass" in pipeline output
- **Diagnostic:** check whether the verdict logic only inspects parsed findings,
  ignoring the exit code
- **Code pattern:** `findings = []; try: parse() except: findings = []; verdict = PASS if not findings`

## Structural fix

```python
if findings:
    verdict = "BLOCK"
elif result.returncode == 0:
    verdict = "PASS"
elif result.returncode == 1:
    verdict = "WARN"  # exit says problem, but couldn't parse findings
else:
    verdict = "WARN"  # tool error
```

Consult BOTH the parsed findings AND the exit code. Never derive a PASS
verdict from an empty-findings state when the exit code indicates an error.

## Why /why-in-fix would benefit from this concept

When the fix agent encounters "scan reports clean but tool returned error,"
querying the wiki for "fail-open masking" would surface this pattern and
the fix (consult exit code alongside parsed findings).
