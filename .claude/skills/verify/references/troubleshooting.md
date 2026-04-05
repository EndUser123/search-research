# Troubleshooting Post-Hoc Verification

## Issue: "ImportError: No module named 'plan_visualizer'"

**Cause**: /plan-workflow skill is not available or lib path is incorrect

**Solution**:
1. Verify /plan-workflow skill exists at `P:/.claude/skills/plan-workflow/`
2. Check that `lib/plan_visualizer.py` exists
3. Verify import path in `tiers/post_hoc_analyzer.py`:
   ```python
   plan_workflow_path = Path("P:/.claude/skills/plan-workflow/lib")
   if str(plan_workflow_path) not in sys.path:
       sys.path.insert(0, str(plan_workflow_path))
   ```

**Alternative**: Run post-hoc verification from plan-workflow directory

## Issue: "TSR is 0% but tasks are complete"

**Cause**: Evidence ledger not provided or path is incorrect

**Solution**:
1. Verify `--evidence-ledger` argument is provided
2. Check evidence ledger file exists at specified path
3. Validate ledger JSON structure matches expected schema
4. Check that task IDs in ledger match task IDs in plan

**Example**:
```bash
# Correct
/verify --post-hoc --plan .claude/plans/plan-example.md --evidence-ledger .claude/state/code_evidence_terminal.json

# Wrong (missing ledger)
/verify --post-hoc --plan .claude/plans/plan-example.md
# TSR will be 0% with note: "No evidence ledger provided"
```

## Issue: "Requirements coverage < 100% but plan is complete"

**Cause**: Keyword matching algorithm didn't map all requirements to tasks

**Diagnosis**:
1. Run `/verify --post-hoc` to see RTM report
2. Check "orphan requirements" in findings
3. Review requirement text vs task titles for keyword overlap

**Solutions**:
- **Option A**: Modify task titles to include requirement keywords
- **Option B**: Add acceptance criteria to orphan requirements
- **Option C**: Split vague requirements into specific requirements

**Example**:
```
Requirement: "The system needs comprehensive verification reporting"
Tasks:
- TASK-001: RTM generation from plan artifacts
- TASK-002: TSR calculation from evidence ledgers

Problem: No task mentions "verification reporting"
Solution: Add TASK-003: "Add comprehensive verification reporting"
```

## Issue: "Overall score is high but TSR is low"

**Cause**: Weighted scoring (30% requirements + 50% tasks + 20% evidence) masks low TSR

**Diagnosis**:
```python
# If requirements_coverage = 100% and evidence_quality = 100%
# But task_completion (TSR) = 50%
overall_score = (100 * 0.3) + (50 * 0.5) + (100 * 0.2)
# overall_score = 30 + 25 + 20 = 75%
# Status: FAIL (TSR < 95% overrides other scores)
```

**Solution**: Focus on completing failed/blocked tasks to achieve TSR >= 95%
- Complete missing TDD evidence types (GREEN, REFACTOR, VERIFY)
- Unblocked tasks by starting RED phase
- Re-run verification after TSR improves

## Issue: "Plan file not found or invalid format"

**Cause**: Plan path is incorrect or plan doesn't follow expected structure

**Solution**:
1. Verify plan file exists: `ls -la .claude/plans/`
2. Check plan has required sections:
   - Problem Statement
   - Implementation Plan (with TASK-XXX definitions)
3. Validate task format matches expected pattern:
   ```markdown
   **TASK-001**: Task title
   - File: `path/to/file.py`
   - Action: Description
   - Points: 5
   - Acceptance: Criteria
   ```

**Alternative**: Create plan with `/plan-workflow "create plan for X"`

## Issue: "Evidence ledger has wrong schema"

**Cause**: Ledger JSON structure doesn't match expected format

**Expected schema**:
```json
{
  "version": "1.0",
  "terminal_id": "string",
  "tasks": {
    "TASK-XXX": {
      "description": "string",
      "evidence": {
        "RED": {"completed": true, "timestamp": "ISO-8601"},
        "GREEN": {"completed": true, "timestamp": "ISO-8601"},
        "REFACTOR": {"completed": true, "timestamp": "ISO-8601"},
        "VERIFY": {"completed": true, "timestamp": "ISO-8601"}
      },
      "done": true,
      "done_at": "ISO-8601"
    }
  }
}
```

**Common errors**:
- Missing `version` field
- Missing `tasks` object
- Missing `evidence` object in task
- Missing `done` boolean
- Timestamps not in ISO-8601 format
- Task ID mismatch between plan and ledger

**Solution**: Regenerate ledger or fix schema errors

## Issue: "Post-hoc verification times out"

**Cause**: Plan is too large or evidence ledger is very large

**Symptoms**:
- Analysis takes > 60 seconds
- Memory usage spikes
- Context limit exceeded

**Solutions**:
- **Option A**: Split large plan into sub-plans
- **Option B**: Run verification incrementally (per phase)
- **Option C**: Exclude transcript if not needed: `--transcript` (optional)

**Example incremental verification**:
```bash
# Phase 1 only
/verify --post-hoc --plan .claude/plans/plan-phase1.md

# Phase 2 only
/verify --post-hoc --plan .claude/plans/plan-phase2.md
```
