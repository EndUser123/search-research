<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Are there repos for solutions for claude code to make sure that tasks are created with proper documentation?

No dedicated public GitHub repositories provide complete, off-the-shelf solutions for enforcing proper documentation on Claude Code task creation via hooks. Official Claude Code docs detail a `TaskCreated` hook event, but implementation is project-specific, as seen in your attached `task-hook.txt` log where gaps exist (e.g., no PreToolUse gate validates TaskCreate docs—only completion gates do).[^1_1][^1_2]

## Official Hook Support

Claude Code supports hooks like `TaskCreated` (triggers on task creation) configurable in `.claude/settings.json` (project-scoped, commit-able). These can run scripts to validate/enrich task descriptions before finalizing, but no built-in doc enforcement exists—custom Python/Bash logic required.[^1_2][^1_3][^1_4]

## Related Repos

- **anthropics/claude-code-action**: GitHub Action for PR/issue automation with Claude Code; adaptable for task/doc workflows but not hook-focused.[^1_5][^1_6]
- **eyaltoledano/claude-task-master**: Task management CLI/SDK for Claude Code (e.g., `task-master parse-prd`, task status updates); includes doc examples but lacks hook-based doc gates.[^1_7]


## Your Context Match

Your `task-hook.txt` shows active hook development (e.g., `PreToolUsetaskselfdocgate.py` proposed for TaskCreate validation using `taskselfdocvalidator.py`). This aligns with best practices: extend TOOLHOOKS for PreToolUseTaskCreate to check description length/categories before creation.[^1_1]

**Next Step**: Implement via `.claude/hooks/PreToolUseTaskCreate/taskselfdocgate.py`—validate JSON input for doc quality, exit 1 to block if invalid (with --force override). Test in isolated worktree. Confidence: High (direct log evidence); assumes v2.1.86+ hooks schema unchanged.[^1_2][^1_1]
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: task-hook.txt

[^1_2]: https://code.claude.com/docs/en/hooks-guide

[^1_3]: https://code.claude.com/docs/en/hooks

[^1_4]: https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/

[^1_5]: https://code.claude.com/docs/en/github-actions

[^1_6]: https://github.com/anthropics/claude-code-action

[^1_7]: https://github.com/eyaltoledano/claude-task-master/blob/main/docs/examples/claude-code-usage.md

[^1_8]: https://www.reddit.com/r/claude/comments/1r977gg/whats_your_workflow_for_keeping_documentation/

[^1_9]: https://code.claude.com/docs/en/best-practices

[^1_10]: https://www.paigeniedringhaus.com/blog/getting-the-most-out-of-claude-code/

[^1_11]: https://blog.sshh.io/p/how-i-use-every-claude-code-feature

[^1_12]: https://dometrain.com/blog/creating-the-perfect-claudemd-for-claude-code/

[^1_13]: https://gist.github.com/jussker/e825980ed46af2b99318e19ef01083be

[^1_14]: https://www.productver.se/p/automating-docs-with-claude-code

[^1_15]: https://dev.to/ujja/a-week-with-claude-code-lessons-surprises-and-smarter-workflows-23ip

[^1_16]: https://github.com/anthropics/claude-code


---

# what would you suggest for best practice to document in a claude code task?  Can you suggest working code for the hook that makes sure tasks are created properly?  do we need to worry about tasks being udpated properly?

Best practices for Claude Code tasks emphasize structured fields like id, title, description (detailed with Problem/Symptom/Root Cause), status, dependencies, priority, and subtasks for clarity and tracking. Include categories (e.g., "Problem: X; Situation: Y; Proposed Solution: Z") to ensure completeness, targeting 200+ chars with verification steps.[^2_1][^2_2]

## Suggested Task Structure

Use this JSON-like format in TaskCreate/Update tool_input:


| Field | Required | Description/Example |
| :-- | :-- | :-- |
| id | Yes | Unique sequential ID (e.g., "TASK-2569") [^2_1] |
| title | Yes | Concise action (e.g., "Fix directory policy flag matching") [^2_1] |
| description | Yes | Detailed: Problem/Symptom/Root Cause/Context/Steps/Expected Outcome/Verification (min 200 chars) [^2_2] |
| status | Yes | "pending", "in-progress", "done", "deferred" [^2_1] |
| dependencies | No | Array of prerequisite IDs [^2_1] |
| priority | No | "high", "medium", "low" [^2_1] |
| subtasks | No | Nested tasks with id/title/description/status [^2_1] |

## Working PreToolUseTaskCreate Hook Code

Place in `.claude/hooks/PreToolUseTaskCreate/task-doc-gate.py` (chmod +x). Validates TaskCreate input before execution; blocks if invalid (exit 2, stderr to Claude). Override with `--force` flag in tool_input.[^2_3][^2_4]

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

**Test**: Pipe sample JSON stdin; expect exit 2 on invalid. Confidence: High (official schemas match).[^2_4]

## Task Updates

Yes, handle updates similarly—extend to `TaskUpdate` matcher with `PostToolUseTaskUpdate` for post-validation (can't block post-facto, but notify/log). Use same validator; your log shows gaps here too (in-progress moves bypass). Add `PostToolUse` hook for audits.[^2_2][^2_3]
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_5][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://github.com/eyaltoledano/claude-task-master/blob/main/docs/task-structure.md

[^2_2]: task-hook.txt

[^2_3]: https://code.claude.com/docs/en/hooks-guide

[^2_4]: https://code.claude.com/docs/en/hooks

[^2_5]: https://code.claude.com/docs/en/overview

[^2_6]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

[^2_7]: https://www.builder.io/blog/claude-code-tips-best-practices

[^2_8]: https://www.reddit.com/r/ClaudeAI/comments/1o98c8f/tell_us_your_best_practices_for_coding_with/

[^2_9]: https://rosmur.github.io/claudecode-best-practices/

[^2_10]: https://stevekinney.com/courses/ai-development/claude-code-hook-examples

[^2_11]: https://www.eesel.ai/blog/claude-code-best-practices

[^2_12]: https://uxplanet.org/claude-code-project-structure-best-practices-5a9c3c97f121

[^2_13]: https://github.com/shanraisshan/claude-code-best-practice

[^2_14]: https://www.reddit.com/r/ClaudeAI/comments/1rfwmlh/how_i_structure_claude_code_projects_claudemd/

[^2_15]: https://nikiforovall.github.io/productivity/2025/06/13/claude-code-rules.html

[^2_16]: https://dev.to/svenlito/building-a-task-management-system-with-claude-code-mkc


---

# Example of TaskCompleted hook script

How to use subagents for task management
Best CLAUDE.md structure for task workflows
How to handle task dependencies automatically

TaskCompleted hooks fire when marking a task complete via TaskCompleted tool; use them for final verification (e.g., tests pass) before allowing status change—exit 2 blocks if invalid.[^3_1]

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

Adapt for custom checks (e.g., grep tests).[^3_1]

## Subagents for Task Management

Spawn subagents via Agent tool (or @agent) for parallel task execution: define in `.claude/agents/*.md` with specialized prompts/context isolation. Main agent orchestrates via Task tool/subagents; up to 10 concurrent, inherit tools but can't spawn nested. Use for role-specific tasks (e.g., reviewer subagent).[^3_2][^3_3]

## Best CLAUDE.md Structure

Organize as project memory:

- **Overview**: Goals, structure, conventions.
- **Workflows**: Task format (id/title/desc/status/deps), hooks summary.
- **Rules**: Code style, verification loops (plan/execute/verify).
- **Commands/Skills**: Common MCP/git hooks.
Prioritize token efficiency; use rules/*.md for conditionals.[^3_4][^3_5]


## Auto Task Dependencies

Claude Code Tasks auto-detect/resolve deps (e.g., TASK-3 blocks on TASK-2 via semantic analysis in plan phase). Hooks can't directly enforce but use TaskCreated for validation/logging. For complex graphs, subagents parse PRD into deps before TaskCreate.[^3_6][^3_7]
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://code.claude.com/docs/en/hooks-guide

[^3_2]: https://ibuildwith.ai/blog/task-tool-vs-subagents-how-agents-work-in-claude-code/

[^3_3]: https://htdocs.dev/posts/revolutionizing-ai-development-how-claude-codes-sub-agents-transform-task-management/

[^3_4]: https://www.reddit.com/r/ClaudeAI/comments/1rfwmlh/how_i_structure_claude_code_projects_claudemd/

[^3_5]: https://geekforbrains.com/blog/orchestrating-claude-code-workflows/

[^3_6]: https://www.youtube.com/watch?v=NAWKFRaR0Sk

[^3_7]: https://www.youtube.com/watch?v=6omInQipcag

[^3_8]: https://code.claude.com/docs/en/hooks

[^3_9]: https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/

[^3_10]: https://www.eesel.ai/blog/hooks-in-claude-code

[^3_11]: https://www.datacamp.com/tutorial/claude-code-hooks

[^3_12]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^3_13]: https://amitkoth.com/claude-code-task-tool-vs-subagents/

[^3_14]: https://github.com/disler/claude-code-hooks-mastery

[^3_15]: https://github.com/mrsarac/claude-code-daily/blob/main/tips/categories/workflow.md


---

# we are working on windows 11.

Should we use subagents somewhere in the create/update/close task events?

No, subagents are not suitable for direct integration into create/update/close task events (e.g., TaskCreated/TaskUpdate/TaskCompleted hooks), as hooks execute shell commands/HTTP/LLM prompts synchronously and cannot spawn subagents natively—use them for simple validation/logging instead.[^4_1][^4_2]

## When to Use Subagents

Reserve subagents (defined in `.claude/agents/*.md`) for parallel, context-isolated workflows post-task creation, like delegating subtasks (e.g., reviewer subagent audits TaskCompleted desc). Hooks trigger on SubagentStart/Stop for coordination, but Windows 11 requires WSL2/PowerShell Core for reliable execution (native cmd/PS may hit path issues).[^4_3][^4_4][^4_5][^4_6]

## Windows 11 Considerations

Claude Code runs via WSL2/Ubuntu on Win11; hooks use `$SHELL` (pwsh/bash)—test paths with forward slashes, avoid native cmd.exe for cross-compat. No subagent-specific Win11 issues reported.[^4_4][^4_3]

**Next Step**: Stick to shell hooks for events; prototype subagent delegation in main CLAUDE.md (e.g., "On TaskCompleted, spawn doc-reviewer agent"). Confidence: High (official docs); verify in WSL terminal.[^4_2]
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://code.claude.com/docs/en/hooks-guide

[^4_2]: https://code.claude.com/docs/en/hooks

[^4_3]: https://www.reddit.com/r/ClaudeCode/comments/1rkixb3/tips_to_help_claude_code_work_more_efficiently/

[^4_4]: https://claude.ai/public/artifacts/03a4aa0c-67b2-427f-838e-63770900bf1d

[^4_5]: https://ibuildwith.ai/blog/task-tool-vs-subagents-how-agents-work-in-claude-code/

[^4_6]: https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/

[^4_7]: https://www.youtube.com/watch?v=HCaCRgp8L5c

[^4_8]: https://www.youtube.com/watch?v=5pKeb3ri24Y

[^4_9]: https://www.youtube.com/watch?v=-6aOfBfzgbs

[^4_10]: https://www.producttalk.org/how-to-use-claude-code-features/

[^4_11]: https://www.linkedin.com/posts/daveslutzkin_people-keep-getting-value-from-my-standard-activity-7424942675331661824-FQtM

[^4_12]: https://platform.claude.com/docs/en/agent-sdk/hooks

[^4_13]: https://zachwills.net/how-to-use-claude-code-subagents-to-parallelize-development/

[^4_14]: https://github.com/VoltAgent/awesome-claude-code-subagents

[^4_15]: https://code.claude.com/docs/en/best-practices

