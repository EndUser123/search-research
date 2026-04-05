# Review Bundle: /catch-22-detection Skill
**Generated**: 2026-03-26T18:55:00Z
**Scope**: P:/.claude/skills/catch-22-detection/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: catch-22-detection
- **Description**: Detect and respond to Catch-22 situations where fixing X requires tools that depend on X
- **Category**: troubleshooting
- **Trigger**: hook blocked, file has been modified, permission denied, cannot proceed, recursive failure
- **Aliases**: `/catch-22`

### Domain & Purpose
Detects and handles Catch-22 situations in Claude Code where fixing a system requires tools that depend on that same system functioning. Prevents wasted effort on recursive fix attempts.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Markdown
- **Key Integration**: Hook system, file operations

---

## 2. ARCHITECTURE OVERVIEW

```
         ┌─────────────────────────────────────────────┐
         │         /catch-22-detection                   │
         │   (Activated when recursive failure detected)│
         └──────────────────┬──────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Detection Trigger│ │ Pattern Matching │ │ User Options    │
│ Same error 2+   │ │ Hook→hook deps  │ │ 1. Disable hooks│
│ Same tool fails │ │ File modified    │ │ 2. Manual repair│
└─────────────────┘ └─────────────────┘ │ 3. Abandon      │
                                        └─────────────────┘
```

---

## 3. DETECTION TRIGGERS

- Same tool fails 2+ times with similar error pattern
- Attempting to repair hooks using commands that trigger those hooks
- Error message references the system being modified
- Each "fix attempt" produces the same or similar failure

---

## 4. RESPONSE FORMAT

When detected, present:
```
⚠️ CATCH-22 DETECTED

Loop: [describe the recursive dependency]
Blocked by: [specific obstacle]
Attempts made: [list what was tried]

Options for user:
1. Disable hooks via `/hooks off` → I repair → `/hooks on`
2. User performs manual repair:
   - File: [exact path]
   - Change: [exact modification needed]
3. Abandon this approach, try: [alternative strategy]
```

---

## 5. PROHIBITED BEHAVIORS

- Attempting increasingly creative workarounds (each adds noise, wastes tokens)
- Assuming the next variation will work when 2+ have failed
- Blaming environment/timing without evidence of external change

---

## 6. EXIT CONDITIONS

User provides one of three options, OR provides new information that breaks the loop.

---

## 7. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Error Handling | GOOD | Clear detection and response |
| Documentation | GOOD | 68-line SKILL.md with clear format |
| Hook Integration | N/A | Detection skill |

### SQA Relevance
- **MEDIUM** — Detection skill for testing patterns
- Helps identify when test infrastructure itself has issues
- Prevents wasted debugging effort
