# Q Workflow Details

Reference file for `/q` phase dispatch, boundary markers, and phase-specific logic.

## Phase Boundary Markers

**MANDATORY:** Before starting each phase, emit a clear phase start marker. After completing each phase (and before checking halt conditions), emit a phase completion marker with results summary.

**Phase Start Format (emit before running any phase):**
```
🔄 [Q{N}] Starting {Phase Name}...
```

**Phase Completion Format (emit after phase finishes, before halt check):**
```
✅ [Q{N}] Complete: {Phase Name}
   {Brief 1-line summary of results}
```

**Example:**
```
🔄 [Q2] Starting QuickCollectors...

{collection executes...}

✅ [Q2] Complete: QuickCollectors
   12 findings collected across 3 subtasks
```

**Why:** Provides clear inter-phase feedback so users can see pipeline progress and understand which phase produced which results.

## Phase Dispatch

**Emit phase start marker FIRST (before subagent call):**
```
🔄 [Q{N}] Starting {Phase Name}...
```

**Read the phase file:**
- Q1 → `P:/.claude/skills/q/phases/q1.md`
- Q2 → `P:/.claude/skills/q/phases/q2.md`
- Q3 → `P:/.claude/skills/q/phases/q3.md`
- Q4 → `P:/.claude/skills/q/phases/q4.md`
- Q5 → `P:/.claude/skills/q/phases/q5.md`
- Q6 → `P:/.claude/skills/q/phases/q6.md`

**Explicit --phase=N flag:** Read `phases/qN.md` directly (skip detection).

**Dispatch the phase as an Agent subagent** (`subagent_type: "general-purpose"`):

```
{full content of qN.md}

---
Scope: {scope resolved in Step 2}
Running as: phase subagent dispatched by /q orchestrator.
Execute the phase workflow defined in this file and report results.
```

**Wait for the subagent to complete.** Its full output is shown to the user as it runs.

**Emit phase completion marker AFTER subagent finishes:**
```
✅ [Q{N}] Complete: {Phase Name}
   {Brief summary of results}
```

Then proceed to next phase or report completion.

## Q3: Strategic Analysis

Synthesize findings from all subagents:

1. **Normalize findings** into stable schema: `{id, severity, category, message, file_path, line_number}`
2. **Assess overall strategic health:**
   - **Sound**: 0-1 concerning findings, 0 critical
   - **Concerning**: 2-5 concerning findings OR 1 critical
   - **Critical**: 6+ concerning findings OR 2+ critical
3. **Identify strategic risks** (high-impact concerns)
4. **Generate strategic recommendations**

## Q4: Render Output

Produce strategic assessment report. Structure varies by health level:

**Sound:** Architecture analysis → Design patterns → Technology fit → Opportunities → Next steps

**Concerning:** Strategic risks table → Analysis sections → Recommended actions → Next steps

**Critical:** Critical risks table with impact → All concerns (priority order) → Immediate actions → Next steps

**Required output format** (hooks validate these markers):
1. Phase results: `✅ Q1: ...` or `⚠️ Q2: ...` for each phase
2. `**Summary:**` section with strategic health assessment
3. `## Next Steps` section with concrete actions
4. Final line: `Q Pipeline Status: COMPLETE`

**CRITICAL RULE for Next Steps:** Recommend concrete fixes, then proceed with implementation. NEVER recommend "re-run /q to validate fixes" — that creates validation loops.

## Q5: Persist Findings (ContextSink)

Store strategic findings to CKS using:
```python
from knowledge.systems.cks.learning.findings_helper import q_finding, batch_findings
```

Create `q_finding()` for each strategic finding, then `batch_findings()` to store. If CKS unavailable, skip — findings are already in the report.

## Q6: Meta-Analysis & Handoff

Save strategic handoff to `P:/__csf/.handoffs/q_to_p_handoff.json` for `/p` to consume:
```json
{
  "strategic_health": "concerning",
  "top_risks": [{"id": "Q-ARCH-001", "severity": "critical", "message": "..."}],
  "recommendations": [{"priority": "high", "action": "...", "reason": "..."}]
}
```

Use `shared_libs.handoff.create_handoff()` and `save_handoff()`.

## Report Completion

After each run, report:
- **Strategic health**: Sound/Concerning/Critical
- **Key findings**: Top 3 strategic concerns or opportunities
- **Next steps**: Highest-value concrete action (fix X, then build Y — NOT "re-run /q")
