# Option C Enhanced: Next Step Collaboration

**Purpose**: Intelligent collision detection between template-based next steps and hook-generated menus.

## Problem

Skills with static templates (`/p`, `/arch`, `/s`, `/code`) include numbered "Next Steps" sections. The `Stop_next_step_suggester.py` hook also generates numbered menus. This creates duplicate menus in the same response.

## Solution: Option C Enhanced

Hook and templates collaborate intelligently:

1. **Detect existing next steps** - Regex pattern matches both formats
2. **Classify skill type** - Domain expert vs pipeline
3. **Decide append behavior** - Preserve, enhance, or skip

## Implementation

### Files Modified

- **`P:\.claude\hooks\Stop_next_step_suggester.py`**
  - Added `_response_has_next_steps()` - Detects existing numbered lists
  - Added `_should_append_next_steps()` - Collision detection logic
  - Added `DOMAIN_EXPERT_SKILLS` - Skills that preserve contextual next steps
  - Added `PIPELINE_SKILLS` - Skills that get dynamic enhancements

- **`P:\.claude\hooks\Stop.py`**
  - Modified `_run_advisory()` to call collision detection before appending

### Collision Detection Logic

```python
def _should_append_next_steps(
    response: str, last_command: str | None, hook_options: list[str]
) -> bool:
    # No hook options = nothing valuable to add
    if not hook_options:
        return False

    # Check if response already has next steps
    has_template_next_steps = _response_has_next_steps(response)

    if not has_template_next_steps:
        # No template next steps → hook should add
        return True

    # Template has next steps → check skill type
    if last_command in DOMAIN_EXPERT_SKILLS:
        # Preserve contextual next steps from /arch, /s, /code
        return False

    if last_command in PIPELINE_SKILLS:
        # Add dynamic options from suggest field for /p, /q, /package
        return True

    # Unknown command → default to appending
    return True
```

### Skill Classification

**Domain Expert Skills** (preserve their contextual next steps):
- `/arch` - Architecture decisions need nuance
- `/s` - Strategic context matters
- `/code` - Workflow-specific next steps

**Pipeline Skills** (get dynamic hook enhancements):
- `/p` - Phase progression benefits from suggest graph
- `/q` - Quality gate with dynamic options
- `/package` - Creation workflow with steps
- `/nse` - Next step engine already integrates

## Behavior Matrix

| Skill Type | Template Next Steps | Hook Options | Result |
|------------|-------------------|--------------|--------|
| Domain expert | Yes | Available | **Skip** hook (preserve template) |
| Domain expert | No | Available | **Append** hook (add options) |
| Pipeline | Yes | Available | **Append** hook (add dynamic value) |
| Pipeline | No | Available | **Append** hook (only options) |
| Any | Yes | Empty | **Skip** hook (nothing to add) |
| Any | No | Empty | **Skip** hook (nothing to add) |

## Test Coverage

Run tests with:
```bash
python P:\.claude\hooks\test_next_step_collision.py
```

Tests verify:
- Template format detection (`- 0 — action`)
- Hook format detection (`0 - action`)
- Domain expert preservation
- Pipeline enhancement
- Empty option handling
- Bare response handling

## Examples

### Domain Expert (/arch) - Preserves Template

**Template output:**
```markdown
## Architecture Decision

### Next Steps
Select an action:
- 0 — /arch — Document this decision
- 1 — /p — Implement the solution
```

**Hook behavior:** Skips appending (template already has context)

### Pipeline (/p) - Adds Dynamic Options

**Template output:**
```markdown
## Phase 1 Complete

### Next Steps
Select an action:
- 0 — /p — Continue to P2
```

**Hook appends:**
```markdown
Next Step Options:
0 - /p --phase=2 - Run Review phase
1 - /tdd fix - Fix issues with TDD
```

**Result:** User gets both static template options AND dynamic suggest graph

### No Template (/nse) - Hook Adds All Options

**Response:** "## Analysis complete."

**Hook appends:**
```markdown
Next Step Options:
0 - /p - Continue pipeline
1 - /q - Run quality gate
2 - /r - Remember and refine
```

**Result:** User gets numbered menu when template had none

## Migration Notes

Skills should continue using their template-based next steps as before. The hook automatically detects and collaborates.

No changes needed to individual skill templates.
