# Skill Author's Guide: Execution Requirements Declaration

**Purpose**: Guide for skill authors on how to declare execution requirements in the Skill Pattern Gate system.

**Last Updated**: 2026-03-06

## Overview

The Skill Pattern Gate enforces execution patterns to prevent skill substitution (LLM providing analysis instead of executing skill workflows). To work correctly with this system, skills must declare their execution requirements.

## Key Concepts

### Knowledge Skills vs Execution Skills

**Knowledge Skills** (default):
- Provide consultation, analysis, documentation
- Don't execute code or run commands
- Examples: `/pre-mortem`, `/reflect`, `/ask`, `/s`, `/analyze`, `/discover`
- **State**: No state file written (no validation needed)
- **Required**: No declaration needed (default behavior)

**Execution Skills**:
- Run commands, execute code, perform operations
- Require specific tool patterns
- Examples: `/rca`, `/build`, `/test`, `/research`
- **State**: State file written (enables validation)
- **Required**: Must declare `required_tools` in registry or frontmatter

## How to Declare Execution Requirements

### Method 1: SKILL_EXECUTION_REGISTRY (Preferred for Hooks)

Add your skill to `SKILL_EXECUTION_REGISTRY` in `PreToolUse_skill_pattern_gate.py`:

```python
SKILL_EXECUTION_REGISTRY = {
    "your-skill-name": {
        "tools": ["Bash", "Task"],  # REQUIRED: Tools that count as execution
        "pattern": r"your_pattern_here",  # REQUIRED: Regex that must match in commands
        "hint": "Use /your-skill via ...",  # REQUIRED: User-facing hint when blocked
        "intent_enabled": False,  # OPTIONAL: Use daemon semantic validation
    },
}
```

**Required Fields**:
- `tools`: List of tool names that count as execution (usually `["Bash", "Task"]`)
- `pattern`: Regex pattern that must appear in tool commands
- `hint`: User-facing message explaining correct usage

**Optional Fields**:
- `intent_enabled`: Enable daemon semantic validation (default: False)

### Method 2: Frontmatter Declaration (Recommended for Skills)

Add execution metadata to your skill's `SKILL.md` frontmatter:

```yaml
---
execution_tools: ["Bash", "Task"]
execution_pattern: "your_pattern_here"
execution_hint: "Use /your-skill via ..."
execution_intent_enabled: false
---
```

## Common Patterns

### Pattern 1: CLI Skills (python -m module)

```python
"my-cli": {
    "tools": ["Bash", "Task"],
    "pattern": r"python(\.exe)?\s+(-m\s+)?my_cli\.py|my_cli",
    "hint": "Use /my-cli via python -m my_cli or python my_cli.py",
    "intent_enabled": False,
}
```

### Pattern 2: Python Import Skills

```python
"rca": {
    "tools": ["Bash", "Task"],
    "pattern": r"src\.rca|SimpleRCAEngine|RCAEngine|EnhancementRouter",
    "hint": "Use /rca via src.rca imports (SimpleRCAEngine, EnhancementRouter)",
    "intent_enabled": True,
}
```

### Pattern 3: Knowledge Skills with First-Tool Coherence

Knowledge skills don't need execution requirements, but may declare `allowed_first_tools` for coherence:

```yaml
---
allowed_first_tools: ["Grep", "Glob", "Read", "Task", "WebSearch"]
---
```

This ensures the first non-investigation tool matches the skill's intent (e.g., discovery questions start with Grep/Glob).

## Troubleshooting

### Problem: "My skill is being blocked"

**Symptom**: Commands blocked with "execution pattern mismatch"

**Diagnosis**:
1. Check if your skill is in `SKILL_EXECUTION_REGISTRY`
2. Verify `tools` field is not empty
3. Verify `pattern` matches your actual command syntax

**Fix**: Add proper registry entry or frontmatter declaration

### Problem: "Users bypass the hook for my skill"

**Symptom**: High bypass usage, user complaints

**Diagnosis**:
1. Check if pattern is too restrictive (blocks legitimate usage)
2. Check if hint message is unclear
3. Review block logs at `P:/.claude/logs/skill_execution_gate.jsonl`

**Fix**: Relax pattern or improve hint message

### Problem: "Warning: Skill X has empty required_tools"

**Symptom**: stderr warning when skill loads

**Diagnosis**: Skill is in `SKILL_EXECUTION_REGISTRY` but has empty `tools` field

**Fix**: Add `tools` field to registry entry OR remove from registry if it's a knowledge skill

## Testing Your Declaration

### Test 1: Verify State is Written

```python
from skill_execution_state import set_skill_loaded, read_pending_state

set_skill_loaded("your-skill", required_tools=["Bash"], pattern="your_pattern")
state = read_pending_state()

assert state is not None, "State should be written for execution skills"
assert state["required_tools"] == ["Bash"], "required_tools should match"
```

### Test 2: Verify Pattern Matching

```python
import re

command = "python your_module.py argument"
pattern = r"your_pattern"

assert re.search(pattern, command, re.IGNORECASE), "Pattern should match command"
```

### Test 3: Run Hook Validation

```python
test_input = {
    "tool_name": "Bash",
    "input": {"command": "python your_module.py argument"}
}

result = subprocess.run(
    ["python", "PreToolUse_skill_pattern_gate.py"],
    input=json.dumps(test_input),
    capture_output=True
)

output = json.loads(result.stdout)
assert not output.get("block"), "Command should be allowed"
```

## Migration Checklist

For existing skills, verify:

- [ ] Skill classified correctly (knowledge vs execution)
- [ ] Execution skills have registry entry or frontmatter declaration
- [ ] `required_tools` field matches actual tool usage
- [ ] Pattern matches legitimate command syntax
- [ ] Hint message is clear and actionable
- [ ] Tests pass for both allowed and blocked commands
- [ ] Documentation updated with examples

## Examples

### Example 1: Simple Knowledge Skill (No Declaration Needed)

**Skill**: `/pre-mortem`

**Type**: Knowledge/consultation

**Declaration**: None needed (default behavior)

**Behavior**: No state written, no validation, all tools allowed

### Example 2: Execution Skill with Registry Entry

**Skill**: `/rca`

**Type**: Execution (Python import)

**Registry Entry**:
```python
"rca": {
    "tools": ["Bash", "Task"],
    "pattern": r"src\.rca|SimpleRCAEngine|RCAEngine|EnhancementRouter",
    "hint": "Use /rca via src.rca imports (SimpleRCAEngine, EnhancementRouter)",
    "intent_enabled": True,
}
```

**Behavior**: State written, pattern validation enforced, daemon semantic validation enabled

### Example 3: Knowledge Skill with First-Tool Coherence

**Skill**: `/ask`

**Type**: Knowledge/consultation with first-tool gating

**Frontmatter**:
```yaml
---
allowed_first_tools: ["Grep", "Glob", "Read", "Task", "WebSearch"]
---
```

**Behavior**: State written, first-tool coherence checked (no pattern validation)

## Support

For questions or issues:
- Check logs: `P:/.claude/logs/skill_execution_gate.jsonl`
- Review test suite: `P:\.claude\hooks\tests/test_skill_pattern_gate_coverage.py`
- Read architecture docs: `P:\.claude\hooks\SKILL_PATTERN_GATE_ARCHITECTURAL_FIX.md`

## Version History

- **v3.5.1** (2026-03-06): Inverted default (knowledge skills by default)
- **v3.5** (2025-XX-XX): First-tool coherence for all skills
- **v3.2** (2025-XX-XX): Parallel regex + daemon validation
