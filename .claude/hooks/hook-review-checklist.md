# Hook Review Checklist

Run this checklist **weekly** or when hooks cause problems.

## How to Review

```bash
cd P:\.claude\hooks
python analyze_blocks.py
```

## Checklist

### 1. Health Check
- [ ] Are hooks enabled? (`settings.local.json`: `disableAllHooks` should be `false`)
- [ ] Any Python import errors in the output?
- [ ] `hook_tracker.py` present and imports work?

### 2. Pattern Analysis
- [ ] Any patterns triggering >5x per session?
  - **Action:** Consider whitelisting or fixing root cause
- [ ] Any false positives (legitimate actions being flagged)?
  - **Action:** Refine regex patterns in the hook
- [ ] Safe patterns list up to date?
  - **Action:** Add common safe commands to `SAFE_PATTERNS`

### 3. Mode Review
Current modes (as of 2025-01):

| Hook | Mode | Rationale |
|------|------|-----------|
| `shell_complexity_gate.py` | WARNINGS | Complex shell prone to escaping failures |
| `unparseable_command_gate.py` | SELECTIVE | Hard block: eval/exec/$() / Warning: python/bash -c |
| `architecture_evidence_gate.py` | WARNINGS | Logs unverified assumptions |
| `recursive_failure_detector.py` | HARD BLOCK | Catch-22 protection (keeps blocking) |

- [ ] Do these modes still match your workflow?
- [ ] Any hooks should change from WARNINGS to BLOCK (or vice versa)?

### 4. Data Retention
- [ ] Old block logs taking space?
  - **Action:** `rm P:\.claude\hooks\blocks_*.jsonl` (keep recent for analysis)

### 5. Adjustment Log

Record changes here for future reference:

| Date | Hook | Change | Why |
|------|------|--------|-----|
| 2025-01-13 | All | Converted to log-only warnings | Collect data before hard-blocking |
| | | | |
| | | | |

---

**Last updated:** 2025-01-13
**Trigger:** Run after seeing hook warnings, or weekly
