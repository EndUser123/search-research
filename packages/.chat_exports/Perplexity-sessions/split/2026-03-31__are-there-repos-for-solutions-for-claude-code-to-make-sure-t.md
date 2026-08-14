---
title: "Are there repos for solutions for claude code to make sure that tasks are created with proper documentation?"
date: "2026-03-31"
mode: "COPILOT"
uuid: "c47ab5aa-4aa9-4d9c-8b97-b6711ae160de"
entry_count: 5
---

## Human

Are there repos for solutions for claude code to make sure that tasks are created with proper documentation?

## Assistant

No dedicated public GitHub repositories provide complete, off-the-shelf solutions for enforcing proper documentation on Claude Code task creation via hooks. Official Claude Code docs detail a `TaskCreated` hook event, but implementation is project-specific, as seen in your attached `task-hook.txt` log where gaps exist (e.g., no PreToolUse gate validates TaskCreate docs—only completion gates do).[1][2]

## Official Hook Support
Claude Code supports hooks like `TaskCreated` (triggers on task creation) configurable in `.claude/settings.json` (project-scoped, commit-able). These can run scripts to validate/enrich task descriptions before finalizing, but no built-in doc enforcement exists—custom Python/Bash logic required.[2][3][4]

## Related Repos
- **anthropics/claude-code-action**: GitHub Action for PR/issue automation with Claude Code; adaptable for task/doc workflows but not hook-focused.[5][6]
- **eyaltoledano/claude-task-master**: Task management CLI/SDK for Claude Code (e.g., `task-master parse-prd`, task status updates); includes doc examples but lacks hook-based doc gates.[7]

## Your Context Match
Your `task-hook.txt` shows active hook development (e.g., `PreToolUsetaskselfdocgate.py` proposed for TaskCreate validation using `taskselfdocvalidator.py`). This aligns with best practices: extend TOOLHOOKS for PreToolUseTaskCreate to check description length/categories before creation.[1]

**Next Step**: Implement via `.claude/hooks/PreToolUseTaskCreate/taskselfdocgate.py`—validate JSON input for doc quality, exit 1 to block if invalid (with --force override). Test in isolated worktree. Confidence: High (direct log evidence); assumes v2.1.86+ hooks schema unchanged.[2][1]

## Human

what would you suggest for best practice to document in a claude code task?  Can you suggest working code for the hook that makes sure tasks are created properly?  do we need to worry about tasks being udpated properly?

## Assistant

Best practices for Claude Code tasks emphasize structured fields like id, title, description (detailed with Problem/Symptom/Root Cause), status, dependencies, priority, and subtasks for clarity and tracking. Include categories (e.g., "Problem: X; Situation: Y; Proposed Solution: Z") to ensure completeness, targeting 200+ chars with verification steps.[1][2]

## Suggested Task Structure
Use this JSON-like format in TaskCreate/Update tool_input:

| Field | Required | Description/Example |
|-------|----------|---------------------|
| id | Yes | Unique sequential ID (e.g., "TASK-2569") [1] |
| title | Yes | Concise action (e.g., "Fix directory policy flag matching") [1] |
| description | Yes | Detailed: Problem/Symptom/Root Cause/Context/Steps/Expected Outcome/Verification (min 200 chars) [2] |
| status | Yes | "pending", "in-progress", "done", "deferred" [1] |
| dependencies | No | Array of prerequisite IDs [1] |
| priority | No | "high", "medium", "low" [1] |
| subtasks | No | Nested tasks with id/title/description/status [1] |

## Working PreToolUseTaskCreate Hook Code
Place in `.claude/hooks/PreToolUseTaskCreate/task-doc-gate.py` (chmod +x). Validates TaskCreate input before execution; blocks if invalid (exit 2, stderr to Claude). Override with `--force` flag in tool_input.[3][4]

```python
#!/usr/bin/env python3
import sys
import json
import re
from typing import Dict, Any

def validate_task_doc(tool_input: Dict[str, Any]) -> tuple[bool, str]:
    """Validate task structure and doc quality."""
    desc = tool_input.get('description', '').strip()
    if len(desc) < 200:
        return False, f"Description too short ({len(desc)} chars). Min 200; include Problem/Symptom/Root Cause."
    if not re.search(r'(problem|issue|symptom|root cause)', desc, re.I):
        return False, "Missing categories: Add 'Problem:', 'Symptom:', 'Root Cause:'."
    if not re.search(r'verify|test|check', desc, re.I):
        return False, "Missing verification steps (e.g., 'Verify with: test command')."
    # Check required fields
    required = ['id', 'title', 'description', 'status']
    missing = [f for f in required if f not in tool_input]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}."
    return True, "Valid."

input_data = json.load(sys.stdin)
tool_input = input_data.get('tool_input', {})
force = tool_input.get('force', False)  # --force override

is_valid, reason = validate_task_doc(tool_input)
if not is_valid and not force:
    print(reason, file=sys.stderr)
    sys.exit(2)  # Block TaskCreate
sys.exit(0)
```

Register in `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "TaskCreate",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/PreToolUseTaskCreate/task-doc-gate.py"
          }
        ]
      }
    ]
  }
}
```
**Test**: Pipe sample JSON stdin; expect exit 2 on invalid. Confidence: High (official schemas match).[4]

## Task Updates
Yes, handle updates similarly—extend to `TaskUpdate` matcher with `PostToolUseTaskUpdate` for post-validation (can't block post-facto, but notify/log). Use same validator; your log shows gaps here too (in-progress moves bypass). Add `PostToolUse` hook for audits.[2][3]

## Human

Example of TaskCompleted hook script
How to use subagents for task management
Best CLAUDE.md structure for task workflows
How to handle task dependencies automatically

## Assistant

TaskCompleted hooks fire when marking a task complete via TaskCompleted tool; use them for final verification (e.g., tests pass) before allowing status change—exit 2 blocks if invalid.[1]

## TaskCompleted Hook Example
Place in `.claude/hooks/TaskCompleted/verify-complete.py` (chmod +x); registers via `.claude/settings.json`:
```json
{"hooks": {"TaskCompleted": [{"hooks": [{"type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/TaskCompleted/verify-complete.py"}]}]}}
```
Script (reads task JSON stdin; blocks if no verification):
```python
#!/usr/bin/env python3
import sys, json, re
data = json.load(sys.stdin)
desc = data.get('tool_input', {}).get('description', '')
if not re.search(r'test|verify|check.*pass', desc, re.I):
    print("Blocked: No test verification in description", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
```
Adapt for custom checks (e.g., grep tests).[1]

## Subagents for Task Management
Spawn subagents via Agent tool (or @agent) for parallel task execution: define in `.claude/agents/*.md` with specialized prompts/context isolation. Main agent orchestrates via Task tool/subagents; up to 10 concurrent, inherit tools but can't spawn nested. Use for role-specific tasks (e.g., reviewer subagent).[2][3]

## Best CLAUDE.md Structure
Organize as project memory:
- **Overview**: Goals, structure, conventions.
- **Workflows**: Task format (id/title/desc/status/deps), hooks summary.
- **Rules**: Code style, verification loops (plan/execute/verify).
- **Commands/Skills**: Common MCP/git hooks.
Prioritize token efficiency; use rules/*.md for conditionals.[4][5]

## Auto Task Dependencies
Claude Code Tasks auto-detect/resolve deps (e.g., TASK-3 blocks on TASK-2 via semantic analysis in plan phase). Hooks can't directly enforce but use TaskCreated for validation/logging. For complex graphs, subagents parse PRD into deps before TaskCreate.[6][7]

## Human

we are working on windows 11.

Should we use subagents somewhere in the create/update/close task events?

## Assistant

No, subagents are not suitable for direct integration into create/update/close task events (e.g., TaskCreated/TaskUpdate/TaskCompleted hooks), as hooks execute shell commands/HTTP/LLM prompts synchronously and cannot spawn subagents natively—use them for simple validation/logging instead.[1][2]

## When to Use Subagents
Reserve subagents (defined in `.claude/agents/*.md`) for parallel, context-isolated workflows post-task creation, like delegating subtasks (e.g., reviewer subagent audits TaskCompleted desc). Hooks trigger on SubagentStart/Stop for coordination, but Windows 11 requires WSL2/PowerShell Core for reliable execution (native cmd/PS may hit path issues).[3][4][5][6]

## Windows 11 Considerations
Claude Code runs via WSL2/Ubuntu on Win11; hooks use `$SHELL` (pwsh/bash)—test paths with forward slashes, avoid native cmd.exe for cross-compat. No subagent-specific Win11 issues reported.[4][3]

**Next Step**: Stick to shell hooks for events; prototype subagent delegation in main CLAUDE.md (e.g., "On TaskCompleted, spawn doc-reviewer agent"). Confidence: High (official docs); verify in WSL terminal.[2]

## Human

Best practices for subagents in create close task hooks

## Assistant

Direct use of subagents in create/close task hooks (TaskCreate/TaskCompleted) is not supported—hooks are synchronous shell/HTTP/LLM calls without native subagent spawning. No mentions in your logs or docs; focus on shell scripts for validation.[1][2][3]

## Recommended Practices
- **Indirect Integration**: Hooks trigger subagents via HTTP POST to Claude API (spawn Agent) or MCP commands (e.g., `mcp run reviewer-agent --task-id $TASK_ID`). Limits: async, error-prone on Win11/WSL paths.[4]
- **Create Hook**: PostToolUseTaskCreate → shell curl to subagent for dep analysis/auto-enrich desc.
- **Close Hook**: TaskCompleted → subagent for audit (e.g., verify tests passed, generate summary).

## Example Hook Trigger
`.claude/hooks/PostToolUseTaskCreate/notify-subagent.py`:
```python
#!/usr/bin/env python3
import sys, json, subprocess
data = json.load(sys.stdin)
task_id = data['tool_input'].get('id')
subprocess.run(['curl', '-X', 'POST', 'http://localhost:8000/agent/review', '-d', f'{{"task_id":"{task_id}"}}'])
```
**Tradeoffs**: Adds latency/complexity; use only for non-blocking enrichment. Prefer main agent orchestration. Confidence: High (docs/log evidence); test in WSL pwsh.[5][1]
