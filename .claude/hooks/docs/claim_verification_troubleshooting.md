# Claim Verification Hooks - Troubleshooting Guide

**Location:** `P:\.claude\hooks\docs\claim_verification_troubleshooting.md`
**Created:** 2025-01-28
**Related Hooks:** `assumption_audit_v2.py`, `Stop_historical_claims_gate.py`

---

## Why These Hooks Exist

### The Original Bug (2025-01-28)

Claude claimed: *"SessionStart_janitor.py was NOT in that list. You just deleted it now."*

This was false. The file had been deleted earlier. Claude made a confident temporal attribution claim without checking `git log`. Existing hooks didn't catch it because:

1. **Old logic:** "Claims present + ANY tool used = Verified"
2. **What happened:** Tools were used for unrelated work (dead code cleanup)
3. **Result:** False claim passed verification

### The Fix: Two-Layer Defense

| Hook | Catches | Mechanism |
|------|---------|-----------|
| `Stop_historical_claims_gate.py` v3.0 | "You just deleted it now" | Temporal + operational word detection |
| `assumption_audit_v2.py` v2.3.1 | Claims about file A when only file B was read | Entity extraction + scope overlap |

---

## Block Message Reference

### "SCOPE_MISMATCH" (assumption_audit_v2)

**Meaning:** Your response mentions specific files/functions, but your evidence (tool usage) covers DIFFERENT files/functions.

**Example:**
- Claim mentions: `SessionStart_janitor.py`
- Evidence covers: `file1.py`, `file2.py`
- Result: BLOCKED

**Resolution:**
1. Read/verify the SPECIFIC files mentioned in your claim
2. Or rephrase to only claim about files you actually verified
3. Or mark unverified portions with `[UNVERIFIED]`

### "NO_EVIDENCE" (assumption_audit_v2)

**Meaning:** Response contains factual claims but no observation tools (Read, Bash, Grep, etc.) were used.

**Resolution:**
1. Use a tool to verify before claiming
2. Show tool output as evidence

### "HISTORICAL_CLAIM" (Stop_historical_claims_gate)

**Meaning:** Response claims WHEN something happened (deleted, modified, created) or WHAT was checked ("I ran tests") without citing evidence like `git log` or tool output in the session ledger.

**Resolution:**
1. Run `git log --all -- <filename>` to verify timing
2. Run the actual tool (e.g. `pytest`, `which gh`) to verify the check
3. Or use uncertain language: "I'm not sure when this was deleted"
4. Or cite the evidence: "According to git log, this was deleted in commit abc123"

### "FAKE_STATE_TRANSITION" (Stop_historical_claims_gate)

**Meaning:** Response claims a state changed (was true before, now not) without PAIRED evidence (one success + one failure) in the session ledger.

**Resolution:**
1. Run discovery commands (e.g. `which gh`) to establish current state.
2. Do not fabricate a "path changed" narrative if you don't have proof it worked earlier in this session.
3. Admit honestly: "I see [tool] fails in this environment; you report it works in your shell. This is likely a PATH mismatch."

---

## Configuration

### Environment Variables

```powershell
# Disable scope checking (rollback to v2.2 behavior)
$env:CLAIM_SCOPE_CHECK_ENABLED = "false"

# Adjust coverage threshold (default 0.5 = 50%)
$env:CLAIM_COVERAGE_THRESHOLD = "0.3"  # More permissive

# Enable debug logging
$env:ASSUMPTION_AUDIT_V2_DEBUG = "true"
$env:HISTORICAL_CLAIMS_DEBUG = "true"

# Proactive preflight guidance before response generation
$env:EMPIRICAL_CLAIMS_PRECHECK_ENABLED = "true"

# Unparseable command mutation mode
# warn  -> warning with rewrite guidance
# block -> hard block opaque python -c file/config mutations
$env:UNPARSEABLE_MUTATION_MODE = "warn"

# Disable hooks entirely (emergency)
$env:ASSUMPTION_AUDIT_V2_ENABLED = "false"
$env:HISTORICAL_CLAIMS_ENABLED = "false"
```

### Logs

```
P:\.claude\hooks\logs\assumption_audit_v2.jsonl
P:\.claude\hooks\logs\historical_claims_gate.jsonl
```

---

## False Positive Troubleshooting

### "I verified the file but still got blocked"

**Check 1:** Did entity extraction find your file?
```powershell
$env:ASSUMPTION_AUDIT_V2_DEBUG = "true"
# Re-run, check stderr for "Claim entities:" and "Evidence entities:"
```

**Check 2:** Is the filename in COMMON_WORDS filter?
- Words like "test", "file", "config" alone may be filtered
- Full filenames like `test.py` should NOT be filtered

**Check 3:** Path normalization mismatch?
- `P:\hooks\file.py` vs `P:/hooks/file.py` should match
- Check if mixed slashes are causing issues

### "Legitimate historical context is blocked"

The Tier 2 LLM classification should allow legitimate context. If it's still blocking:

1. Check if response cites evidence (git log, documentation)
2. Add explicit uncertainty: "Based on the commit history..." or "I'd need to verify with git log..."

### "Too many false positives - need to disable"

```powershell
# Temporary disable (current session)
$env:CLAIM_SCOPE_CHECK_ENABLED = "false"

# Or lower threshold
$env:CLAIM_COVERAGE_THRESHOLD = "0.3"

# Keep Stop blocks active but reduce pre-generation pressure
$env:EMPIRICAL_CLAIMS_PRECHECK_ENABLED = "false"
```

**Report:** Note the response text and expected behavior for tuning.

---

## Monitoring (First Week)

### Check Block Rate

```powershell
# Count blocks vs allows in last 24h
$logs = Get-Content "P:\.claude\hooks\logs\assumption_audit_v2.jsonl" | 
    ConvertFrom-Json | 
    Where-Object { $_.timestamp -gt (Get-Date).AddDays(-1).ToString("o") }

$blocks = ($logs | Where-Object { $_.event -eq "block" }).Count
$allows = ($logs | Where-Object { $_.event -eq "allow" }).Count
$rate = $blocks / ($blocks + $allows) * 100

Write-Host "Block rate: $rate% ($blocks blocks, $allows allows)"
```

**Alert threshold:** If block rate > 15%, threshold may be too aggressive.

### Review Recent Blocks

```powershell
Get-Content "P:\.claude\hooks\logs\assumption_audit_v2.jsonl" | 
    ConvertFrom-Json | 
    Where-Object { $_.event -eq "block" } | 
    Select-Object -Last 10 | 
    ForEach-Object { 
        Write-Host "---"
        Write-Host "Time: $($_.timestamp)"
        Write-Host "Reason: $($_.reason)"
        Write-Host "Claims: $($_.claims -join ', ')"
        Write-Host "Uncovered: $($_.uncovered -join ', ')"
    }
```

---

## Architecture Reference

```
User Response
     │
     ▼
┌─────────────────────────────┐
│ UserPromptSubmit precheck   │ ◄── Proactive structure reminder
│ - Observed / Inferred /     │     for evidence-bound claims
│   Unknown                    │
└─────────────────────────────┘
     │
     ▼
┌─────────────────────────────┐
│ Stop_historical_claims_gate │ ◄── Catches temporal attribution
│ (Tier 1: keywords)          │     "You just deleted it now"
│ (Tier 2: LLM classification)│
└─────────────────────────────┘
     │ (if not blocked)
     ▼
┌─────────────────────────────┐
│ assumption_audit_v2         │ ◄── Catches scope mismatch
│ - Detect claims             │     "Claims about A, evidence about B"
│ - Extract claim entities    │
│ - Extract evidence entities │
│ - Check overlap (≥50%)      │
└─────────────────────────────┘
     │
     ▼
   Response delivered (or blocked)
```

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| Documentation update | 2026-02-11 | Added proactive precheck + mutation mode config |
| assumption_audit_v2.py v2.3.1 | 2025-01-28 | Common word filtering, configurable threshold |
| assumption_audit_v2.py v2.3.0 | 2025-01-28 | Claim-scope verification |
| Stop_historical_claims_gate.py v3.0 | 2025-01-28 | Operational attribution detection |

---

## Contact / Escalation

If these hooks are causing significant workflow disruption:

1. **Immediate:** Disable with env vars (see Configuration above)
2. **Document:** Note the false positive case
3. **Review:** Check this file + hook source code
4. **Tune:** Adjust thresholds or word lists

**Source files:**
- `P:\.claude\hooks\assumption_audit_v2.py`
- `P:\.claude\hooks\Stop_historical_claims_gate.py`
- `P:\.claude\hooks\tests\test_assumption_audit_v2_scope.py`
- `P:\.claude\hooks\tests\test_stop_historical_claims.py`
