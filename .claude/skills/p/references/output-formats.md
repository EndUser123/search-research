# Output Formats Reference

## HALT Output Format

**When HALT occurs, output this SINGLE format (no duplicate sections):**

```
## Pipeline Status: HALTED

**Status:** HALTED at Phase {phase_number}

**Summary by Category:**
| Category | Count | Severity Breakdown |
|----------|-------|-------------------|
| Security Vulnerabilities | {count} | {CRITICAL}: {n}, {HIGH}: {n}, {MEDIUM}: {n}, {LOW}: {n} |
| Correctness Bugs | {count} | {CRITICAL}: {n}, {HIGH}: {n}, {MEDIUM}: {n}, {LOW}: {n} |
| Performance Issues | {count} | {CRITICAL}: {n}, {HIGH}: {n}, {MEDIUM}: {n}, {LOW}: {n} |
| Concurrency Safety | {count} | {CRITICAL}: {n}, {HIGH}: {n}, {MEDIUM}: {n}, {LOW}: {n} |
| Error Handling Quality | {count} | {CRITICAL}: {n}, {HIGH}: {n}, {MEDIUM}: {n}, {LOW}: {n} |
| Test Coverage Gaps | {count} | {CRITICAL}: {n}, {HIGH}: {n}, {MEDIUM}: {n}, {LOW}: {n} |
| API Design Issues | {count} | {CRITICAL}: {n}, {HIGH}: {n}, {MEDIUM}: {n}, {LOW}: {n} |

**Phase Results:**
- OK/FAIL Phase {N}: {name} - {status}
- HALT Phase {current}: {name} - HALTED
- PENDING Phase {next}: {name} - Pending (halted before this phase)

---

### Blocking Findings by Category

{If CRITICAL/HIGH findings exist, group by semantic category:}

#### Security Vulnerabilities ({count})
1. {ID}: {description} ({severity}) - {file}:{line}

#### Correctness Bugs ({count})
1. {ID}: {description} ({severity}) - {file}:{line}

{Or if no CRITICAL/HIGH:}
No blocking findings. See full results: {path_to_findings_json}

---

**Recommended Next Steps**

{Context-Aware Options based on target type and findings - see references/next-steps-template.md}

After fixing, re-run: `/p`
```

## COMPLETE Output Format

**When pipeline COMPLETES successfully:**

```
## Pipeline Status: COMPLETE

**Status:** ALL PHASES PASSED

**Phase Results:**
- OK Phase 1: Build - PASS
- OK Phase 2: Review - PASS
- OK Phase 3: Validate - PASS
- OK Phase 4: Publish - PASS
- OK Phase 5: Certify - PASS

**Summary:** {Brief summary, e.g., "Code is production-ready"}

**Recommended Next Steps**

1. [Deployment]
   1a. `git commit` - Commit changes
   1b. `git push` - Push to remote

2. [Development]
   2a. Continue development - Add new features or fixes

**0 - Do ALL Recommended Next Steps**
```

## Phase Boundary Markers

**Phase Start Format (emit before running any phase):**
```
[P{N}] Starting {Phase Name}...
```

**Phase Completion Format (emit after phase finishes, before halt check):**
```
[P{N}] Complete: {Phase Name}
   {Brief 1-line summary of results}
```

**Blocking Issue Found and Fixed:**
```
[Phase N] BLOCKING ISSUE FOUND AND FIXED
   Bug: {BLOCKING_FOUND}
   Fix: {FIX_APPLIED}

[Phase N] Complete: {Phase Name}
   {SUMMARY from PHASE_RESULT}
```

## Evidence File Writing (when `--evidence` flag is set)

Write structured JSON after completing the pipeline:

```python
import json
from datetime import datetime

evidence = {
    "package": target,
    "skill": "/p",
    "status": "PASS" if overall_pass else "FAIL",
    "timestamp": datetime.now().isoformat() + "Z",
    "summary": f"{tests_passed} passed, {tests_failed} failed",
    "details": {
        "phase_reached": highest_phase_completed,
        "tests_collected": test_count,
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "findings_critical": critical_count,
        "findings_high": high_count,
        "findings_medium": medium_count,
        "findings_low": low_count,
    },
    "themes": []
}

with open(evidence_path, 'w') as f:
    json.dump(evidence, f, indent=2)
```

**Status determination:**
- `PASS`: Pipeline completed through P5 (Certify) with no blocking issues
- `FAIL`: Pipeline halted at any phase due to blocking issues
- `HALT`: Pipeline stopped early due to critical findings
