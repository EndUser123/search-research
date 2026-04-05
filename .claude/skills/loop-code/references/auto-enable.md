# Ralph Loop Auto-Enable Integration

The `/loop-code` skill integrates with Core Plan v1's task type detection to automatically enable or disable Ralph Loop based on the nature of the work.

## Task Type Detection

Before starting the loop, the system analyzes the plan to detect whether the work consists primarily of:
- **Implementation tasks**: Feature development, bug fixes, code changes (-> Ralph Loop enabled)
- **Research tasks**: Investigation, documentation, analysis (-> Ralph Loop disabled)

## Detection API

```python
from lib.task_detector import detect_task_type, log_detection_decision

# Detect task type from plan content
result = detect_task_type(plan_content)

# Result contains:
# - task_type: TaskType.IMPLEMENTATION or TaskType.RESEARCH
# - enable_ralph_loop: True for implementation, False for research
# - confidence: Float 0.0-1.0
# - reasoning: String explaining the detection

# Log detection decision to evidence
log_detection_decision(
    result=result,
    query=plan_content,
    project_root=project_root
)
```

## Automatic Behavior

**Default behavior (no flags)**:
- Implementation plans -> Ralph Loop **enabled** (autonomous execution)
- Research plans -> Ralph Loop **disabled** (manual guidance)

**Example detection results**:
- "Implement user authentication" -> `enable_ralph_loop: true` (implementation)
- "Research authentication patterns" -> `enable_ralph_loop: false` (research)
- "Fix login bug" -> `enable_ralph_loop: true` (implementation)
- "Analyze performance issues" -> `enable_ralph_loop: false` (research)

## Override Flags

**Force Ralph Loop enable**:
```bash
/loop-code plan.md --ralph-enable
```
- Enables Ralph Loop regardless of task type detection
- Use for: Implementation work that detector misclassifies as research

**Force Ralph Loop disable**:
```bash
/loop-code plan.md --ralph-disable
```
- Disables Ralph Loop regardless of task type detection
- Use for: Research work that detector misclassifies as implementation

## Detection Logging

Task type detection results are logged to evidence for traceability:

**Evidence file**: `.evidence/ralph_auto_detection.md`

**Content**:
```markdown
# Ralph Loop Auto-Detection

## Detection Result
- **Task Type**: IMPLEMENTATION
- **Ralph Loop**: ENABLED
- **Confidence**: 0.85
- **Timestamp**: 2026-03-15T14:30:00Z

## Detection Reasoning
Plan contains implementation keywords: "implement", "create", "add"
Task breakdown suggests feature development work
No research-only patterns detected

## Original Query
[Plan content excerpt]
```

## Integration Workflow

```
Plan File -> Task Type Detection -> Decision
                                    |-- Implementation -> Ralph Loop ENABLED (autonomous)
                                    +-- Research -> Ralph Loop DISABLED (manual)

User can override with --ralph-enable or --ralph-disable flags
Detection logged to .evidence/ralph_auto_detection.md
```

## Configuration

Task type detection is configured in `.claude/loop/config.yaml`:

```yaml
task_detection:
  enabled: true                        # Enable auto-detection (default)
  confidence_threshold: 0.6            # Minimum confidence for auto-detection
  override_flags:                      # User override flags
    ralph_enable: "--ralph-enable"     # Force enable
    ralph_disable: "--ralph-disable"   # Force disable
```

## Exit Policy Interaction

Ralph Loop auto-enable interacts with exit policy:

| Task Type | Ralph Loop | Exit Policy | Use Case |
|-----------|------------|-------------|----------|
| Implementation | Enabled | Full policy | Autonomous feature development |
| Research | Disabled | Minimal policy | Manual investigation and analysis |
| Mixed (override) | User choice | User choice | Ambiguous or hybrid work |

When Ralph Loop is **disabled** for research tasks:
- `enforcement.enabled: false` (minimal policy) is recommended
- Faster iteration cycle with fewer exit requirements
- User provides guidance on each task

When Ralph Loop is **enabled** for implementation:
- `enforcement.enabled: true` (full policy) is recommended
- Stricter quality control before exit
- Autonomous execution with state tracking

## Changelog

**Version 0.4.0 (2026-03-15)**:
- **NEW**: Ralph Loop auto-enable integration with task type detection
- **NEW**: `--ralph-enable` and `--ralph-disable` override flags
- **NEW**: Detection logging to `.evidence/ralph_auto_detection.md`
- **NEW**: Task type detection API from `lib.task_detector`
