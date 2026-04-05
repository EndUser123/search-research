# Output Format & Confidence Tags

## Confidence Tag Requirement (MANDATORY in v2.6)

**All hypothesis statements, conclusions, and claims MUST include confidence tags:**

**Format**: `(Tier [0-4], [0-100]%)`

### Tier Definitions

| Tier | Evidence Type | Max Confidence | Max Claim Allowed | Example Phrasing |
|------|---------------|----------------|-------------------|------------------|
| Tier 0 | Intuition, comments, docs, memory | 50% | "Possible direction" | "This might be related to X (Tier 0, 40%)" |
| Tier 1 | Code/config inspection | 75% | "Plausible cause" | "Code shows X likely causes Y (Tier 1, 70%)" |
| Tier 2 | Local/synthetic reproduction (unit tests) | 75% | "Working hypothesis" | "Local test confirms X behavior (Tier 2, 75%)" |
| Tier 3a | Runtime state only (files, env, intent JSON) | 80% | "Probable cause" | "State files show X condition (Tier 3a, 80%)" |
| Tier 3b | Runtime state + hook logs / tool-pipeline logs | 85% | "Strong evidence" | "Hook logs confirm X execution (Tier 3b, 85%)" |
| Tier 4 | End-to-end observed behavior | 95% | "Confirmed" | "Observed X working end-to-end (Tier 4, 95%)" |

**Rules**:
- No "root cause identified" below Tier 3a
- No "fixed/works" below Tier 4
- Confidence cannot exceed tier ceiling
- Makes overclaiming visually obvious
- Explicitly state Tier 3a vs 3b when using runtime evidence

---

## Required RCA Structure

**MANDATORY: Executed-Path-First Workflow**

1. **FIRST**: Show Executed Path (what code actually ran this turn)
2. **THEN**: Identify Root Cause (must name something in the Executed Path)
3. **DO NOT**: Name a function/file as root cause without first proving it appears in Executed Path

**Time-Scope Labels** (REQUIRED on all evidence citations):
- `[current-state]` -- Evidence from current runtime (files, logs, process state)
- `[transcript-time]` -- Evidence from chat history or prior turns
- `[inference]` -- Logical derivation from evidence (must be labeled as such)

**Reachability Proof**: Before naming a function as root cause:
1. Grep for call-sites: `grep -r "funcName(" --include="*.py"`
2. Verify function has callers (not dead code with 0 callers)
3. Confirm call-site is reachable from Executed Path

### Template

```markdown
## RCA: [One-line root cause summary]

**Confidence:** [Score]% (Tier [1-4])
**Evidence Tier:** [Highest tier used]

### Symptom

[Observable error/behavior - what the user saw, not your hypothesis]

### Evidence

[Cite >=1 current-turn tool observation: Read on X, Grep found Y, Bash showed Z]
[MUST include time-scope label: current-state, transcript-time, or inference]

### Executed Path

[Functions/files that actually ran this turn, reachable via current-turn evidence]
[Must show call chain: entry point -> ... -> failure point]
[Dead code (0 callers) CANNOT be the root cause]

### Alternative Hypothesis

[Competing explanation - must exist even if brief]

### Falsifier

[Evidence that refutes the Alternative Hypothesis]
[Must show WHY alternative is wrong, not just that it exists]

### Root Cause

[File/symbol/path that appears in Executed Path above]
[Must have reachability proof: grep call-sites + confirm callers exist]

**Technical:** [What broke - file, line, mechanism] (Tier [0-4], [0-100]%)

**Systemic:** [Why it was possible - missing test, unclear interface, process gap] (Tier [0-4], [0-100]%)

### Fix

[Specific code change - file edit, config change, etc.]
[Must be concrete action, not "investigate more" or "check logs"]

**Files:**
- [file]: [what changes]

**Reversibility:** [Score 1.0-2.0]

### Verification

- [ ] [How to verify fix works - specific test or command]
- [ ] [Regression check]
- [ ] [Confirm dead code was not incorrectly named as cause]
```

---

## Block Triggers

**Do not complete RCA without these:**
- No Executed Path shown -> block
- Root Cause names function not in Executed Path -> block
- Root Cause is dead code (0 callers) -> block
- No Alternative Hypothesis -> block
- No Falsifier (or doesn't refute alternative) -> block
- Evidence lacks time-scope label -> block
- Fix is vague ("test it", "verify") -> block

### Action Graph (include in output)

| Step | Action | Expected | Actual | Divergence? | Lesson |
|------|--------|----------|--------|-------------|--------|
| 1 | ... | ... | ... | ... | ... |
