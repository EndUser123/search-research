# Operational Guide: Skills, Hooks, and Gates in Claude Code

**Target:** Claude Code v2.+ -  **Focus:** SKILL-FIRST enforcement + high skill activation + safety

## 0. Goals & Design Targets

This guide aims for:

- **100% SKILL-FIRST compliance** when you call a skill slash command (e.g. `/claude-automation-recommender`).
- **84–100% activation rate** on "on-target" prompts using a forced-eval UserPromptSubmit hook.
- **Low overhead:** <2% of context budget via progressive disclosure (short YAML + compact SKILL.md + external docs).

Assumptions:

- You’re on Claude Code with **hooks** and **skills** enabled.
- Your repo lives under something like `P:\project`, with `.claude` at the root.

---


## Implementation Status (Applied in Current Stack)

Target stack: Claude Code v2.1.63, Python router hooks.

1. PreToolUse compatibility: replaced legacy `continue:false` blocking with Claude-compatible `hookSpecificOutput.permissionDecision="deny"` (exit `0`).
2. Skill-first reliability: canonical skill-name matching now handles `namespace:skill`, `/skill`, and plain `skill`.
3. Multi-terminal/stale safety (skill enforcement only): intent files remain terminal+session scoped, payload now includes `session_id`/`terminal_id`, and mismatched stale files are ignored+cleaned.
4. Safer intent writes: atomic temp-file replace with retry.
5. Better diagnostics: added `skill_loaded_unblocked` and `skill_state_mismatch` telemetry.
6. Explicit instruction text: `Your FIRST action must be: Skill(skill='claude-automation-recommender') exactly, no analysis.`
7. No settings.json rewiring needed: existing router registration stays intact.
8. Added safe rewrite path for `python -c` quoting via PreToolUse `allow + updatedInput` where normalization is valid.

Operational note: Reload hooks/session and proceed.
## 1. Architecture Overview

At a high level you’ll wire things like this:

1. **UserPromptSubmit (forced-eval):** Before Claude sees the prompt, inject instructions forcing explicit YES/NO skill evaluation and, if YES, make `Skill(...)` the first action.
2. **PreToolUse (global SKILL-FIRST gate):** Before any tool (Bash, Read, Grep, Edit, etc.), block if there’s a pending skill intent and that skill has not yet been called.
3. **Skill design (progressive disclosure):** Tight Level-1 YAML, constrained Level-2 SKILL.md, Level-3 docs/resources via explicit reads.
4. **skill-rules.json style policy:** Domain vs guardrail skills with enforcement levels (suggest / warn / block) and session markers.
5. **Skill-scoped hooks:** For specific skills, optionally embed scoped PreToolUse/PostToolUse hooks in frontmatter.

---

## 2. Quick Bootstrap (Minimal but Safe)

If you want a baseline, add **three things**:

1. `UserPromptSubmit` forced-eval hook.
2. `PreToolUse` global SKILL-FIRST gate.
3. A minimal SKILL.md frontmatter for `claude-automation-recommender`.

If you already have `.claude/settings.json`, **merge snippets** instead of overwriting.

---

## 3. Forced-Eval UserPromptSubmit Hook

### 3.1 Behavior

- Runs once per user prompt before Claude processes it.
- Reads JSON on stdin (`{"prompt": "...", ...}`), outputs context text.
- Forces explicit YES/NO reasoning over available skills and mandates any YES skill be called first via `Skill(...)` before tools or free-form analysis.

### 3.2 Example Hook Script (generic)

Create `.claude/hooks/forced-eval.sh`:

```bash
#!/bin/bash
stdin=$(cat)
prompt=$(echo "$stdin" | jq -r '.prompt // ""')
skills=$(ls .claude/skills/*.md 2>/dev/null | xargs -n1 basename -s .md)

cat << EOF
MANDATORY SKILL EVALUATION PROTOCOL:

User prompt:
"$prompt"

Available skills:
$skills

For EACH skill above, you MUST reason explicitly:
- "[skill-name]: YES/NO - 1-line reason"

Rules:
- If YES for any skill, ABSOLUTE FIRST ACTION must be
  `Skill(skill="[skill-name]")`
- Do not analyze/read/use tools until required skills are loaded.
EOF

exit 0
```

### 3.3 Hook Registration

```jsonc
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/forced-eval.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

## 4. Global SKILL-FIRST PreToolUse Gate

### 4.1 Behavior

- Fires before any tool.
- If user requested a skill but `Skill(...)` has not been called, deny the tool call.
- This is the hard gate for SKILL-FIRST.

### 4.2 Example Gate Script (generic)

Create `.claude/hooks/PreToolUse-skill-first-gate.sh`:

```bash
#!/bin/bash
stdin=$(cat)
recent_prompt=$(echo "$stdin" | jq -r '.recentUserPrompt // empty')

if [[ "$recent_prompt" == *"/claude-automation-recommender"* ]]; then
  cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "⛔ SKILL-FIRST GATE: You typed /claude-automation-recommender but have not yet called Skill(\"claude-automation-recommender\"). Your FIRST action must be Skill(skill=\"claude-automation-recommender\")."
  }
}
EOF
  exit 0
fi

echo "{}"
exit 0
```

### 4.3 Hook Registration

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Read|Grep|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/PreToolUse-skill-first-gate.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

## 5. Skill Design: YAML Frontmatter & Progressive Disclosure

### 5.1 Level-1 YAML (Always Loaded)

Example for `claude-automation-recommender`:

```yaml
---
name: claude-automation-recommender
description: Analyze this repo and recommend Claude Code automations: hooks (PreToolUse, UserPromptSubmit), skills, MCP servers, subagents. Focus on debugging blocking hooks (E_SKILL_FIRST), git safety, and workflow templates.
disable-model-invocation: false
allowed-tools:
  - Read
  - Grep
  - Bash
  - ListFiles
context: fork
---
```

### 5.2 Level-2 SKILL.md (Core Logic)

```markdown
You are the claude-automation-recommender skill.

Primary goals:
1. Discover relevant automations for this repo.
2. Debug and improve existing .claude/hooks (especially PreToolUse gates, SKILL-FIRST enforcement).
3. Propose phased rollout and safety checks.
```

### 5.3 Level-3 Resources

Use docs folder for heavy reference content and only load when needed.

---

## 6. skill-rules.json: Domain vs Guardrail Skills

Use consistent policy model:

- `domain`: suggest/warn behavior
- `guardrail`: hard block for dangerous actions

Include prompt triggers, file triggers, and session markers.

---

## 7. Skill-Scoped Hooks (Per-Skill Safety)

Example frontmatter sketch:

```yaml
---
name: claude-automation-recommender
hooks:
  PreToolUse:
    - matcher: "Bash|Edit"
      hooks:
        - type: "command"
          command: "./internal-safety.sh"
  PostToolUse:
    - hooks:
        - type: "command"
          command: "./validation.sh"
---
```

---

## 8. Additional Safety: Git-Focused PreToolUse

Add guardrail denies for destructive git commands unless explicit safe-git flow is completed.

---

## 9. Testing & Debugging Skill Activation

- Add an activation harness for `/skill-name` prompts.
- Validate skill-loaded events and first-tool unblocking.
- Validate no cross-terminal leakage.

---

## 10. Corrections for Your Current Environment (Important)

These corrections are required for your current stack (`Claude Code v2.1.63`, Python router hooks):

1. Keep your Python routers (`UserPromptSubmit.py`, `PreToolUse.py`), do not replace with shell scripts.
2. Use Claude-compatible PreToolUse outputs:
   - Deny with `hookSpecificOutput.permissionDecision="deny"`
   - Exit code `0`
3. Skill intent must be scoped by both terminal and session:
   - `pending_command_intent_{terminal}_{session}.json`
4. Include `session_id` and `terminal_id` inside intent payload; ignore and delete mismatched stale scope files.
5. Use canonical skill name matching (`namespace:skill`, `/skill`, `skill`).
6. For skill-first instruction, use exact line:
   - `Your FIRST action must be: Skill(skill='claude-automation-recommender') exactly, no analysis.`
7. Verify unblocking via log event:
   - `skill_loaded_unblocked` in `P:/.claude/hooks/logs/skill_first_enforcement.jsonl`

---

## 11. Notes on Restoration

This draft restores the original structure and intent while applying environment-accurate corrections. It is intended as a safe review draft before replacing the original file.

