# Phase 2: Cross-Agent Meta-Critique

## Your Job

Critique the Phase 1 specialist findings — not the original work. Focus on:
1. Contradictions between specialists
2. Calibration — are severity ratings consistent across agents?
3. Blind spots — what did no specialist catch?
4. Precision vs recall failures

## Input

Read these files:
- **Original Work:** `cat "P:/{session_dir}/work.md"`
- **Phase 1 Findings:** `cat "P:/{session_dir}/p1_findings.md"`
- **Specialist JSON outputs (session-scoped — dynamic glob):**
  - `cat "P:/{session_dir}/specialists/*.json"` — read all specialist JSON files from the session's specialists subdirectory

## Analysis Steps

### Step 1: Pre-Condition Check — Specialist Files Exist

**Kill criterion (COMP-003):** Before reading any specialist JSONs, verify that at least one specialist JSON file exists in `P:/{session_dir}/specialists/`.

- Use a file glob or list check on `P:/{session_dir}/specialists/*.json`
- If **zero specialist files exist**: Write a calibration failure note to `P:/{session_dir}/p2.md` and exit Phase 2 early. The note must state:
  - That zero specialist files were found
  - That this violates the Phase 1 completion gate
  - That Phase 2 cannot proceed without specialist findings
- If **one or more specialist files exist**: proceed to the contradiction check below

**Do NOT silently proceed with empty input. This is a hard kill criterion.**

### Step 2: Check for Contradictions

Look across specialist findings for claims that contradict each other:
- One specialist says X is safe, another says X is risky
- Severity ratings that conflict for similar issues
- Recommendations that conflict

### Step 3: Calibrate Severity

Check if severity is consistent:
- A CRITICAL in one domain vs a LOW in another for equivalent issues = calibration failure
- Flag items where one specialist downplayed an issue another flagged as serious

### Step 4: Find Blind Spots

What did none of the specialists catch?
- Look at the work type: what issues are common for this type but absent?
- Are there systemic patterns the specialists collectively missed?

### Step 5: Distinguish Recall vs Precision

**P1 #7 Precision/Recall distinction:** Separately analyze:
- **Recall failures (missed issues):** What did Phase 1 miss that should have been caught? Look at common issue types for this work type that no specialist flagged.
- **Precision failures (over-criticism):** What did Phase 1 flag that is actually fine, or inflated in severity beyond what the evidence supports?

Flag both types explicitly.

## Output Schema

Write your meta-critique to `P:/{session_dir}/p2.md`:

```
## Cross-Agent Contradictions
1. [contradiction] — Specialist A says X, Specialist B says Y
...

## Severity Calibration Issues
1. [issue] — rated differently by different specialists without justification
...

## Missed Blind Spots
1. [what was missed] — why it matters
...

## Precision Failures
1. [finding from Phase 1] — [why it's too vague/generic/weak]
...

## Improvements to the Phase 1 Findings
1. [specific improvement]
2. [specific improvement]
...
```

## Constraints

- Focus on the quality of the Phase 1 analysis, not re-reviewing the work
- Be specific — cite the finding and why it fails
- Do not be pedantic — flag real failures, not nitpicks
