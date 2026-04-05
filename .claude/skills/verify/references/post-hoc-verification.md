# Post-Hoc Verification Mode

## What is Post-Hoc Verification?

Post-hoc verification analyzes **completed work** through chat history artifacts using LLM-as-Judge approach. Unlike real-time 4-tier verification (which executes tests), post-hoc verification evaluates **what was actually accomplished**.

## When to Use Post-Hoc Mode

**Use post-hoc verification when**:
- Work is claimed complete (DONE phase)
- You need to verify all requirements were addressed
- You want quantifiable metrics (TSR, RTM coverage)
- Reviewing work from previous sessions
- Certifying feature completeness before deployment

**Do NOT use post-hoc verification when**:
- Verifying code structure (use real-time 4-tier instead)
- Testing integration points (use real-time 4-tier instead)
- Running E2E tests (use real-time 4-tier instead)

## Key Metrics

**RTM (Requirements Traceability Matrix)**:
- Maps requirements -> implementation tasks
- Checks each requirement has >=1 task
- Validates each task has acceptance criteria
- Coverage: (Requirements with tasks / Total requirements) x 100

**TSR (Task Success Rate)**:
- Measures implementation completion
- TSR = (Completed tasks / Total attempted tasks) x 100
- Threshold: TSR >= 95% required for PASS
- Tasks with all 4 TDD evidence types (RED, GREEN, REFACTOR, VERIFY) count as completed

**LLM-as-Judge Evaluation**:
- Analyzes conversation completeness
- Evaluates evidence sufficiency
- Checks requirements addressed
- Provides overall score (0-100)

## Usage Examples

```bash
# Post-hoc verification with plan file
/verify --post-hoc --plan .claude/plans/plan-20260313-example.md

# Post-hoc verification with evidence ledger
/verify --post-hoc --plan .claude/plans/plan-example.md --evidence-ledger .claude/state/code_evidence_terminal.json

# Post-hoc verification with all artifacts
/verify --post-hoc --plan .claude/plans/plan-example.md --evidence-ledger .claude/state/code_evidence_terminal.json --transcript .claude/history/session.jsonl
```

## Post-Hoc Workflow

**Step 1: Load Artifacts**
- Parse plan.md (requirements, tasks, acceptance criteria)
- Load evidence ledger (TDD evidence: RED, GREEN, REFACTOR, VERIFY)
- Load chat transcript (optional, for deeper analysis)

**Step 2: Generate RTM**
- Extract requirements from Problem Statement
- Map requirements to tasks (keyword matching)
- Generate coverage matrix
- Report orphan requirements and tasks

**Step 3: Calculate TSR**
- Read evidence ledger
- Count completed tasks (all 4 evidence types + done=True)
- Count failed/blocked tasks
- Calculate TSR percentage

**Step 4: Evaluate Completeness**
- Check requirements coverage (RTM)
- Check task completion (TSR)
- Check evidence quality (acceptance criteria coverage)
- Generate overall score

**Step 5: Generate Report**
```
## Post-Hoc Verification Report
**Overall Status**: PASS / FAIL
**Overall Score**: 95.5%

### RTM Coverage
**Requirements Coverage**: 100% (3/3 requirements mapped)
**Task Coverage**: 100% (5/5 tasks mapped)
**Acceptance Criteria Coverage**: 100% (5/5 tasks have acceptance criteria)

### TSR Metric
**Task Success Rate**: 95.0%
**Total Attempted**: 20 tasks
**Completed**: 19 tasks
**Failed**: 1 task
**Blocked**: 0 tasks

### Findings
**HIGH**: Task Success Rate is 95.0%, at 95% threshold
**MEDIUM**: None

### Recommendations
- Complete 1 failed task to achieve TSR > 95%
- All requirements addressed
- All tasks have acceptance criteria
```

## Pass/Fail Criteria

**PASS when**:
- TSR >= 95%
- Requirements coverage = 100%
- Acceptance criteria coverage = 100%
- Overall score >= 95

**FAIL when**:
- TSR < 95%
- Any requirement has no mapped task
- Any task missing acceptance criteria
- Overall score < 95

## Integration with Other Skills

- **/plan-workflow**: Generates RTM from plan.md
- **/code**: Tracks TDD evidence in ledger (TSR calculation)
- **/trace**: Deep manual verification (complementary to post-hoc)

## Technical Implementation

**Module**: `tiers/post_hoc_analyzer.py`

**Key Classes**:
- `PostHocAnalyzer`: Main analyzer class
  - `generate_rtm()`: Delegates to PlanVisualizer
  - `calculate_tsr()`: Reads evidence ledger
  - `evaluate_conversation_completeness()`: LLM-as-Judge evaluation
  - `run_analysis()`: Orchestrates complete analysis

**Dependencies**:
- `plan_visualizer.PlanVisualizer` from /plan-workflow
- `evidence.EvidenceManager` from /code
- Chat history artifacts (plan.md, evidence ledger, transcript)
