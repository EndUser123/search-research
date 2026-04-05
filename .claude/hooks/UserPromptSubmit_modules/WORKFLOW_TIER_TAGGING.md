# Workflow Step Header System

**Status**: Implemented 2026-03-11
**Purpose**: Self-documenting enforcement for PROCEDURE skills

## Problem Addressed

**Original issue**: How do we ensure documented workflows in SKILL.md are actually followed, not just read?

**Previous approach**: Breadcrumb enforcement system (skill writes to state file, Stop hook verifies)
- Problem: External compliance check, opaque to user
- Problem: Doesn't make output self-documenting

**New approach**: Step header tagging via UserPromptSubmit hook
- Model reads workflow_steps from frontmatter
- Hook injects directive requesting step headers in output
- Output itself becomes evidence of methodology compliance

## Important Clarification

**Tier 1/2/3 = Breadcrumb audit completeness**, NOT workflow steps

The breadcrumb system has its own tier system (from `skill-guard`):
- **Tier 1**: Basic breadcrumb tracking (step completed yes/no)
- **Tier 2**: Enhanced breadcrumb tracking (with timestamps, evidence links)
- **Tier 3**: Full breadcrumb auditing (verification that steps actually did what they claimed)

This is **separate** from workflow step progression. Workflow steps should use their actual names, not tier numbers.

## Implementation

### Files Created

1. **`UserPromptSubmit_modules/workflow_tier_tagging.py`**
   - Priority 3.0 (early execution)
   - Reads workflow_steps from skill frontmatter
   - Generates step header directive
   - Injects directive into user prompt

2. **`UserPromptSubmit_modules/tests/test_workflow_tier_tagging.py`**
   - 8 tests, all passing
   - Tests path resolution, directive generation, hook behavior

3. **`P:\.claude\skills\debugRCA\SKILL.md`** (updated)
   - Added workflow_steps to frontmatter:
     ```yaml
     workflow_steps:
       - diagnose_with_evidence
       - recommend_fix_with_verification
       - complete_root_cause_analysis
       - tier_evidence_tagging
       - documentation_completion
     enforcement_level: STRICT
     ```

4. **`UserPromptSubmit_modules/registry.py`** (updated)
   - Added "workflow_tier_tagging" to core_hook_modules

### How It Works

When a PROCEDURE skill is invoked via Skill() tool:

1. **UserPromptSubmit event fires**
2. **Hook detects Skill() invocation** (tool_name == "Skill")
3. **Hook checks if skill is in PROCEDURE_SKILLS set** (debugRCA, p, arch, ...)
4. **Hook reads skill's SKILL.md frontmatter** for workflow_steps
5. **Hook generates step header directive**:
   ```
   **METHODOLOGY COMPLIANCE FOR debugRCA**:
   This skill has 5 documented workflow steps that must be completed:
     [DIAGNOSE_WITH_EVIDENCE]
     [RECOMMEND_FIX_WITH_VERIFICATION]
     [COMPLETE_ROOT_CAUSE_ANALYSIS]
     [TIER_EVIDENCE_TAGGING]
     [DOCUMENTATION_COMPLETION]

   **Required**: As you complete each workflow step, mark it with a section header using the exact step name above.
   **Completion**: Only use [COMPLETE] after ALL workflow steps are documented in your output.
   **Self-Audit**: Before finalizing, verify your output contains ALL 5 workflow step headers.
   ```
6. **Directive is injected into user prompt**
7. **Model outputs responses with step headers** as it completes steps
8. **Output itself is evidence** of methodology compliance

## Benefits

### vs Breadcrumb Enforcement

| Aspect | Breadcrumbs | Step Headers |
|--------|-------------|--------------|
| **Evidence location** | State file (hidden) | In output (visible) |
| **User visibility** | Hidden | Self-documenting |
| **Compliance method** | External check | Self-reporting |
| **Output quality** | Opaque | Transparent |
| **Debugging** | Check state file | Read output headers |

### Key Advantages

1. **Self-documenting output**: Presence of `[STEP_NAME]` headers proves step was completed
2. **No hidden state**: Evidence is in the output, not a separate state file
3. **User-visible**: Users can see which steps were completed
4. **Simpler**: No need for set_breadcrumb() calls or Stop hook verification
5. **Generic**: Works for any skill that declares workflow_steps

## Adding New Skills

To add step headers to a new PROCEDURE skill:

1. **Add workflow_steps to SKILL.md frontmatter**:
   ```yaml
   workflow_steps:
     - step_one_name
     - step_two_name
     - step_three_name
   enforcement_level: STRICT  # optional
   ```

2. **Add skill to PROCEDURE_SKILLS set** in `workflow_tier_tagging.py`:
   ```python
   PROCEDURE_SKILLS = {
       "debugRCA",
       "p",
       "arch",
       "your_new_skill",  # Add here
   }
   ```

3. **Test**: Invoke the skill and verify step headers appear in output

## Current PROCEDURE Skills

- **debugRCA**: Root cause analysis (5 steps)
- **p**: Code maturation pipeline (not yet configured)
- **arch**: Architecture advisor (not yet configured)

## Example Output

When `/debugRCA investigate hook failure` is invoked:

```
[DIAGNOSE_WITH_EVIDENCE]
I've identified the issue: hook is returning exit code 2.
Evidence: Hook output shows {"allow": false, "reason": "..."}

[RECOMMEND_FIX_WITH_VERIFICATION]
Fix: Update hook to return {"allow": true} when condition passes.
Verification plan: Run pytest to verify fix.

[COMPLETE_ROOT_CAUSE_ANALYSIS]
Root cause: Hook logic error in condition check.
Mechanism: Code review shows inverted boolean.

[TIER_EVIDENCE_TAGGING]
All claims tagged with evidence tiers:
- [Tier 2] Hook exits early (code review + runtime)

[DOCUMENTATION_COMPLETION]
Updated SKILL.md with troubleshooting section.

[COMPLETE]
```

The presence of all 5 step headers proves the methodology was followed.

## Related Systems

- **Breadcrumb enforcement**: Alternative approach using state files (with Tier 1/2/3 audit levels)
- **StopHook verification**: External compliance checking (superseded for PROCEDURE skills)
- **GENERIC_PROTOCOL.md**: Debugging protocol with evidence tiers (different use case)

## Future Work

1. Add workflow_steps to other PROCEDURE skills (p, arch)
2. Create Stop hook that verifies step headers are present (optional)
3. Add step header detection to completion claim verification
4. Integrate with breadcrumb Tier 1/2/3 audit system
