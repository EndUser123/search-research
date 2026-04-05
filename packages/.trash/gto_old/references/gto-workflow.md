# /gto Execution Workflow

Complete workflow for executing /gto gap analysis with health scoring integration.

## Step 1: Detect Gaps with Severity and Type

Analyze the chat history and build a list of gaps.

**Default mode** (no arguments): Read the full transcript for this terminal from `transcript_path`.

**Session mode** (`--session` or `--quick` flag): Analyze the entire session transcript (all conversation from session start to now). The `--quick` flag is a shorthand alias for `--session`. Each gap must have:

```python
gap = {
    "type": "descriptive gap type",  # e.g., "ImportError: No module named 'requests'"
    "severity": "critical|high|medium|low"
}
```

### Severity Guidelines

**Critical** (from `references/error-patterns.md`):
- ImportError, hook failures, data loss risks, security vulnerabilities
- **Impact**: Blocks code execution or breaks system functionality

**High**:
- NameError, TypeError, AttributeError, test failures, repeated user corrections
- **Impact**: Runtime failures or user frustration

**Medium**:
- Warnings that don't break functionality, dropped topics, context switches
- **Impact**: Non-blocking issues

**Low**:
- Style issues, cosmetic problems, minor conversation flow issues
- **Impact**: Code quality or UX polish

### Gap Detection Areas

1. **Error & Warning Detection** (see `references/error-patterns.md`)
   - Python errors: ImportError, NameError, TypeError, AttributeError
   - Hook failures: IMPORT_FAIL, Hook error messages
   - Test failures: FAILED, ERROR, AssertionError

2. **User Feedback Patterns** (see `references/conversation-patterns.md`)
   - Repeated corrections (3+ times same issue)
   - Frustration signals ("that's wrong", "backwards", "still wrong")
   - Explicit redirects ("stop. why don't you...")

3. **Learning Signals**
   - Patterns to document
   - Lessons from corrections

4. **Session Flow Issues** (see `references/conversation-patterns.md`)
   - Dropped topics
   - Context switches
   - Anti-patterns (workaround over root cause)

5. **Task Tracker References**
   - #TASK-XXX mentions
   - Plan status

6. **Plan Status**
   - Active plans
   - Outstanding steps

7. **Cleanup Needs**
   - Temporary files
   - Debug code
   - Git state

8. **Broken Windows**
   - Partial work
   - Incomplete features

9. **Follow-Ups**
   - Research noted but not pursued

10. **Context State**
    - Hooks disabled
    - Config changes
    - Dependencies added

11. **Decisions**
    - Approaches taken
    - Rationale

12. **Common Omissions**
    - Documentation, tests, git commits
    - Breaking changes, performance/security implications

## Step 2: Calculate Health Score

After detecting gaps, calculate the project health score:

```python
from health_scoring import calculate_health_score, format_health_score

# gaps = list of detected gaps from Step 1
health = calculate_health_score(gaps)
```

**Returns**:
- `health.overall_score`: 0-100 aggregate score
- `health.categories`: List[CategoryScore] with breakdowns
- `health.critical_gaps`: Count of critical severity gaps
- `health.high_gaps`: Count of high severity gaps
- `health.recommendation`: Text recommendation

**Score Interpretation** (from SKILL.md):
- **90-100**: Excellent health - no immediate action needed
- **80-89**: Good health - address high-priority gaps when convenient
- **70-79**: Fair health - recommend addressing high-severity gaps soon
- **60-69**: Declining health - critical and high gaps need attention
- **0-59**: Poor health - focus on lowest-scoring category first

## Step 3: Format Output

Include health scoring in your output:

### For Compact Snapshot mode (default):

```markdown
=== GTO SNAPSHOT ===
- Status: [one-line summary with emoji]
- Health: [X/100] - [recommendation text]
- Critical Gaps: [count]
- High Gaps: [count]

**Session Resume**
- Last active work: [task/plan from chat]
- Resume command: [command or TASK-XXX]
- Context budget: [XX% used]

**Status Details**
- 🔴 Critical: [gaps from health categories]
- 🟡 High: [gaps from health categories]
- 🟢 Medium: [gaps from health categories]
- 🔵 Low: [gaps from health categories]

**Implementation**
- [file.py]: [key change]
- [file.py]: [key change]

**Tests:** [summary]

**Notes**
- [Key decision/approach]

**Did You Forget Anything?**
- 🟋 Documentation updates
- 🟋 Tests for new/modified code
- 🟋 Git commits
```

### For Verbose mode (--verbose flag):

Include the full formatted health score from `format_health_score(health)`:

```markdown
**Project Health: 72/100**

**Category Breakdown:**
- Tests: 80/100 (weight: 30%) - 3 gaps (1 critical, 2 high)
- Documentation: 65/100 (weight: 20%) - 4 gaps (2 medium, 2 low)
- Git: 90/100 (weight: 20%) - 1 gap (1 high)
- Dependencies: 60/100 (weight: 15%) - 2 gaps (1 critical, 1 medium)
- Code quality: 75/100 (weight: 15%) - 2 gaps (1 high, 1 low)

**Recommendation**: Fair health - recommend addressing high-severity gaps soon

⚡ 3 high-severity gap(s) should be addressed soon
```

## Integration with Git Context

When git repository is detected, /gto automatically enhances gap analysis with git state awareness (see `references/git-context-integration.md`):

```python
from git_context import get_git_context

git_context = get_git_context(working_directory=".")
# Returns: branch, clean status, recent commits, modified files, etc.

# Can be passed to health scoring for enhanced analysis
health = calculate_health_score(gaps, git_context=git_context)
```

## Output Format Templates

See `references/verbose-mode-templates.md` for complete verbose output templates.

## Example Execution Flow

```python
# Step 1: Detect gaps from chat
gaps = detect_gaps_from_conversation()

# Step 2: Calculate health score
health = calculate_health_score(gaps)

# Step 3: Format output
if verbose_mode:
    output = format_health_score(health)
else:
    output = format_compact_snapshot(health, gaps)

# Step 4: Add recommended next steps
output += generate_recommended_steps(gaps, health)
```

## Related Reference Files

- **`references/error-patterns.md`**: Complete error detection reference with severity classifications
- **`references/conversation-patterns.md`**: User feedback and flow analysis guide
- **`references/git-context-integration.md`**: Git state integration examples
- **`references/verbose-mode-templates.md`**: Verbose output format templates
