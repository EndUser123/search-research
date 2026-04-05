# Investigation Response Template

**Purpose**: Standardized format for investigative responses to prevent lazy documentation-verification patterns.

**When to use**: Any time you're investigating an issue, debugging, or troubleshooting.

**Anti-patterns prevented**:
- Reading documentation first before verification
- Assuming APIs exist without checking examples
- Inventing parameters that "should" exist
- Jumping to solutions without testing

---

## Template Structure

```markdown
## Investigation: [Brief Title]

### Issue Description
[1-2 sentences describing what you're investigating]

### Discovery Phase
[What you checked FIRST - code, tests, existing patterns]

### Hypothesis Testing
[If investigation required testing]

**Hypothesis**: [What you suspect]
**Test**: [Command or action to disconfirm]
**Result**: [Actual output]
**Conclusion**: [RULED OUT / CONFIRMED]

### Evidence Collected
[Files read, commands run, outputs observed]

### Root Cause
[What's actually happening - backed by evidence]

### Next Action
[What to do next - specific, not "investigate further"]
```

---

## Example 1: Tool Usage Error

### BAD (Documentation Before Verification)

```markdown
I need to use the Agent tool. Let me check the system prompt for the exact parameters...

According to the docs, Agent takes subagent_type and model. Let me try with model="haiku".
```

**Problem**: Reads docs first, assumes parameters work without testing.

### GOOD (Verification First)

```markdown
## Investigation: Agent tool with haiku model

### Issue Description
Previous attempt to use Task tool with model="haiku" failed. Need to spawn subagent with haiku model.

### Discovery Phase
Read tool documentation from system prompt:
- Agent tool: spawns subagents with model selection
- Task tool: creates task list items (no model parameter)

### Evidence Collected
- System prompt confirms: "When calling Agent tool... model is optional"
- Available models: "sonnet", "opus", "haiku"

### Root Cause
Task tool doesn't support model parameter - must use Agent tool instead.

### Next Action
Use Agent tool with subagent_type="general-purpose" and model="haiku"
```

---

## Example 2: API Investigation

### BAD (Assuming APIs Exist)

```markdown
Let me check the pytest documentation for the testmon configuration...

According to pytest docs, we should configure testmon in pyproject.toml like this:
[testmon]
enabled = false
```

**Problem**: Invents config structure without verifying pytest actually uses it.

### GOOD (Verification First)

```markdown
## Investigation: Disable pytest-testmon plugin

### Issue Description
pytest hangs indefinitely. Need to disable testmon plugin.

### Discovery Phase
Read P:\.claude\skills\p\pyproject.toml:
- Line 61: `addopts = "-v --tb=short"`
- No testmon configuration visible

### Hypothesis Testing

**Hypothesis**: testmon plugin is causing hang
**Test**: `pytest tests/ -v -p no:testmon`
**Result**: Tests complete in 0.15s
**Conclusion**: CONFIRMED - testmon is the cause

### Evidence Collected
- pyproject.toml line 61 shows addopts
- Running with `-p no:testmon` fixes the issue
- No testmon-specific config found in file

### Root Cause
pytest-testmon plugin (v2.2.0) causes hanging - disabled via `-p no:testmon` flag.

### Next Action
Update pyproject.toml line 61 to include `-p no:testmon` flag
```

---

## Protocol Checklist

Before submitting investigation response, verify:

- [ ] **Discovery first**: What did you check BEFORE proposing solutions?
- [ ] **Evidence cited**: Specific file:line references, command outputs
- [ ] **No assumptions**: Every claim backed by test output or file read
- [ ] **Next action specific**: Not "investigate" or "look into", but concrete step

---

## Prohibited Patterns

DO NOT:
- "Let me check the documentation" (as first step)
- "According to the docs" (without verification)
- "I think" or "probably" (without test output)
- Invent API names or parameters (verify they exist first)

DO:
- Check existing code FIRST
- Test hypotheses SECOND
- Read documentation ONLY to verify findings
- Cite specific file:line evidence

---

## Integration with MEMORY.md

This template enforces:

**Verification First Protocol**:
- Hypothesis → Test → Document (not "read docs → assume → hope")

**Tool Usage Checklist**:
- Read tool docs (already in system prompt)
- Identify required vs optional parameters
- Check parameter types

**Solution Proposal Gate**:
- Root cause identified? ✓ (evidence required)
- At least 2 hypotheses ruled out? ✓ (if testing)
- Proposed fix tested? ✓ (next action is specific)

---

**Version**: 1.0.0
