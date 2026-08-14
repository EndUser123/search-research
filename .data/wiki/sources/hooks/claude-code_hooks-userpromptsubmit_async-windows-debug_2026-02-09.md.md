<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# ❯ 1

⎿  UserPromptSubmit hook error

For claude code hooks, I think there is a bug.  Is that verified the the UserPromptSubmit always shows an error?  Is there a workaround?

No, the UserPromptSubmit hook in Claude Code does not always show an error—it's a known but intermittent bug often tied to execution failures, plugin mismatches, or Windows-specific issues like path handling and concurrency.[^1_1][^1_2][^1_3][^1_4]

## Bug Verification

Multiple GitHub issues and user reports confirm UserPromptSubmit errors occur frequently, such as hooks matching but not executing (especially in plugins), stderr not displaying properly, or false errors despite successful runs. These are not universal but common on Windows 11 (your setup), similar to other hook races like sapling_checkpoint.py errors from concurrent access. It's not "always" broken, but unreliable without fixes.[^1_5][^1_6][^1_7][^1_8][^1_2][^1_4][^1_9][^1_10]

## Common Causes

- Plugin hooks register/match but fail silently or error out (e.g., \#10225).[^1_9]
- Script errors (non-zero exit, JSON parse fails, non-executable).[^1_7][^1_3]
- Windows path/execution quirks; hooks run but show "error" even if functional.[^1_11][^1_4]


## Workarounds

Define hooks directly in `~/.claude/settings.json` (not plugins) for reliable execution—plain text output to stdout with exit 0 appends to context.[^1_5][^1_9]
Test with a simple echo:

```
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "echo 'Test context added'"
      }]
    }]
  }
}
```

This bypasses plugin bugs and verifies via visible additions; exit 2 blocks prompts if needed. For persistent issues, add logging or use SessionStart hooks as alternatives. Update Claude Code and check `--debug` logs for specifics.[^1_2][^1_4][^1_12][^1_1][^1_5]
<span style="display:none">[^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19]</span>

<div align="center">⁂</div>

[^1_1]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^1_2]: https://github.com/anthropics/claude-code/issues/17550

[^1_3]: https://github.com/anthropics/claude-code/issues/10964

[^1_4]: https://www.reddit.com/r/ClaudeCode/comments/1nc5oe8/claude_code_hooks_not_blocking_tool_execution_on/

[^1_5]: https://www.perplexity.ai/search/36f6c1fd-6cc5-4ffe-a64e-3bf76f312641

[^1_6]: https://www.perplexity.ai/search/841f4986-cb0d-4c33-9c3f-1bd6bbf28ea2

[^1_7]: https://github.com/anthropics/claude-code/issues/8810

[^1_8]: https://github.com/anthropics/claude-code/issues/9652

[^1_9]: https://github.com/anthropics/claude-code/issues/10225

[^1_10]: https://github.com/thedotmack/claude-mem/issues/555

[^1_11]: https://www.perplexity.ai/search/541c3692-ad54-4946-8fea-16050554225d

[^1_12]: https://code.claude.com/docs/en/hooks

[^1_13]: https://www.reddit.com/r/ClaudeAI/comments/1mdynb8/finally_fixed_the_two_critical_claude_code_issues/

[^1_14]: https://github.com/thedotmack/claude-mem/issues/460

[^1_15]: https://github.com/anthropics/claude-code/issues/17804

[^1_16]: https://dev.to/rajeshroyal/claude-code-chrome-fix-the-bug-and-verify-it-works-in-one-prompt-25mi

[^1_17]: https://www.youtube.com/watch?v=UZb0if-7wGE

[^1_18]: https://blog.devgenius.io/the-prompt-improver-every-serious-claude-code-user-needs-899d09251de0

[^1_19]: https://www.youtube.com/watch?v=nWj1rdZ9wG8


---

# What causes UserPromptSubmit errors on Windows

Best workarounds for Claude Code hook failures
How to debug UserPromptSubmit hook execution
Examples of working UserPromptSubmit hook scripts

UserPromptSubmit hook errors on Windows in Claude Code often stem from platform-specific execution issues, stdout handling bugs, and plugin mismatches.[^2_1][^2_2][^2_3]

## Windows-Specific Causes

Windows path resolution fails when starting Claude Code from subdirectories, causing hooks to not execute despite registration. Stdout output (even valid) triggers "hook error" messages per docs contradiction, plus PATH conflicts from Windows nvm/npm overriding WSL/Linux paths. Plugin hooks match but never run, unlike direct settings.json configs; concurrent races (like file mods) exacerbate this.[^2_2][^2_4][^2_5][^2_6][^2_7][^2_1]

## Best Workarounds

Define hooks directly in `~/.claude/settings.json` or `.claude/settings.json`—avoids plugin bugs entirely. Use `claude --debug` or Ctrl+O verbose mode to monitor without errors; for blocking issues, switch SessionStart reminders as interim. Ensure Git Bash path via `$env:CLAUDE_CODE_GIT_BASH_PATH` and native install over npm.[^2_5][^2_6][^2_8][^2_9][^2_3][^2_10]

## Debugging Steps

Run `claude --debug` for full logs showing registration, matching, and execution (e.g., "Hook output does not start with {"). Use `/hooks` menu to verify/test/delete; check stdin JSON parsing with `jq -r '.prompt'` in scripts. Run `/doctor` for config validation; inspect `transcript_path` for failures.[^2_8][^2_9][^2_3][^2_10][^2_5]

## Working Examples

Simple echo test (adds "Test context" to every prompt, exit 0):

```
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "echo 'Test context added'"
      }]
    }]
  }
}
```

Bash validator blocking "you're right" phrases (reads transcript, exits 2 on match):

```
#!/bin/bash
stdin=$(cat)
transcript_path=$(echo "$stdin" | jq -r '.transcript_path')
# Check last 5 assistant items for triggers...
if /"$needs_reminder" == "true"; then
  echo 'Avoid agreement phrases; analyze critically.' # Appends on exit 0
fi
```

Python logger/validator (`user_prompt_submit.py`):

```
#!/usr/bin/env python
import sys, json, datetime
data = json.load(sys.stdin)
with open('logs/user_prompt_submit.json', 'a') as f:
  json.dump({"timestamp": datetime.datetime.now().isoformat(), "prompt": data["prompt"]}, f)
print("Logged prompt.") # Adds to context
sys.exit(0)
```

Config: `"command": "uv run .claude/hooks/user_prompt_submit.py --log-only"`[^2_11]
<span style="display:none">[^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_18]</span>

<div align="center">⁂</div>

[^2_1]: https://github.com/anthropics/claude-code/issues/8810

[^2_2]: https://github.com/anthropics/claude-code/issues/13912

[^2_3]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^2_4]: https://code.claude.com/docs/en/troubleshooting

[^2_5]: https://github.com/anthropics/claude-code/issues/10225

[^2_6]: https://www.reddit.com/r/ClaudeCode/comments/1nc5oe8/claude_code_hooks_not_blocking_tool_execution_on/

[^2_7]: https://www.perplexity.ai/search/841f4986-cb0d-4c33-9c3f-1bd6bbf28ea2

[^2_8]: https://github.com/anthropics/claude-code/issues/10401

[^2_9]: https://code.claude.com/docs/en/hooks-guide

[^2_10]: https://www.perplexity.ai/search/36f6c1fd-6cc5-4ffe-a64e-3bf76f312641

[^2_11]: https://github.com/disler/claude-code-hooks-mastery

[^2_12]: https://www.reddit.com/r/ClaudeAI/comments/1l7ilhu/claude_code_error_file_has_been_modified_since/

[^2_13]: https://code.claude.com/docs/en/hooks

[^2_14]: https://gist.github.com/ljw1004/34b58090c16ee6d5e6f13fce07463a31

[^2_15]: https://www.reddit.com/r/ClaudeAI/comments/1mdynb8/finally_fixed_the_two_critical_claude_code_issues/

[^2_16]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^2_17]: https://www.datacamp.com/tutorial/claude-code-hooks

[^2_18]: https://github.com/anthropics/claude-code/issues/2814


---

# UserPromptSubmit hook example script for prompt logging

Here's a ready-to-use UserPromptSubmit hook script for logging prompts in Claude Code. It captures the full JSON input (prompt, session_id, timestamp) to a file without disrupting workflow.[^3_1][^3_2]

## Script Setup

Save as `~/.claude/hooks/log_prompt.py` (make executable with `chmod +x` on Unix or via Windows Git Bash).[^3_1]

```python
#!/usr/bin/env python3
import sys
import json
from datetime import datetime

# Read JSON from stdin
data = json.load(sys.stdin)

# Prepare log entry
log_entry = {
    "timestamp": datetime.now().isoformat(),
    "session_id": data.get("session_id", "unknown"),
    "prompt": data.get("prompt", ""),
    "cwd": data.get("cwd", ""),
    "hook_event_name": data.get("hook_event_name", "UserPromptSubmit")
}

# Append to JSONL file (one JSON per line)
with open('~/.claude/logs/user_prompts.jsonl', 'a') as f:
    f.write(json.dumps(log_entry) + '\n')

# Optional: Add subtle context (commented out to avoid noise)
# print("Prompt logged safely.")

sys.exit(0)  # Success: continues normally
```


## Configuration

Add to `~/.claude/settings.json` or project `.claude/settings.json`:

```
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/hooks/log_prompt.py"
      }]
    }]
  }
}
```

Reload with `/hooks` or restart Claude Code.[^3_3][^3_1]

## Usage and Viewing

Submit any prompt—it logs silently. View logs:

```
tail -f ~/.claude/logs/user_prompts.jsonl | jq '.prompt'
```

Example entry: `{"timestamp": "2026-02-04T14:08:00", "session_id": "abc123", "prompt": "Your query here"}` Works on Windows via Python 3 + jq (install via `winget`).[^3_4][^3_2][^3_1]
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_16][^3_17][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/disler/claude-code-hooks-mastery

[^3_2]: https://www.datacamp.com/tutorial/claude-code-hooks

[^3_3]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^3_4]: https://www.reddit.com/r/ClaudeCode/comments/1nc5oe8/claude_code_hooks_not_blocking_tool_execution_on/

[^3_5]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^3_6]: https://www.gend.co/blog/configure-claude-code-hooks-automation

[^3_7]: https://code.claude.com/docs/en/hooks

[^3_8]: https://note.com/lab_bit__sutoh/n/n7dc23be8f17d

[^3_9]: https://github.com/anthropics/claude-code/issues/10225

[^3_10]: https://www.reddit.com/r/ClaudeAI/comments/1ohaugf/a_hook_that_logs_your_claude_code_prompts_to_a/

[^3_11]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^3_12]: https://www.reddit.com/r/learnpython/comments/ucy1d4/how_to_log_user_prompt_questions/

[^3_13]: https://www.eesel.ai/blog/hooks-in-claude-code

[^3_14]: https://github.com/anthropics/claude-code/issues/17277

[^3_15]: https://www.reddit.com/r/LangChain/comments/13on2ek/is_there_a_way_to_log_all_the_prompts_logging_all/

[^3_16]: https://code.claude.com/docs/en/hooks-guide

[^3_17]: https://github.com/daaain/claude-code-log


---

# UserPromptSubmit hook script to validate prompts

How to block prompts with UserPromptSubmit exit codes
Example UserPromptSubmit hook to add context
UserPromptSubmit hook for Windows troubleshooting

UserPromptSubmit hooks in Claude Code validate prompts by parsing stdin JSON, checking against rules, and using exit codes to control flow—ideal for security, style enforcement, or quality gates.[^4_1][^4_2]

## Blocking Prompts

Exit 2 blocks processing, erases the original prompt, and feeds stderr directly to Claude as feedback (so it can self-correct). Exit 0 allows with optional stdout/additionalContext appended to LLM input; other codes log stderr but proceed.[^4_3][^4_4][^4_5][^4_1]

## Validation Script Example

Save as `~/.claude/hooks/validate_prompt.py` (Python 3, executable).[^4_2]

```python
#!/usr/bin/env python3
import sys
import json
import re

data = json.load(sys.stdin)
prompt = data.get("prompt", "").lower()

# Block dangerous patterns
dangerous = ["delete .* --force", "rm -rf", "curl | sh", "sudo"]
if any(re.search(pat, prompt) for pat in dangerous):
    print(json.dumps({
        "decision": "block",
        "reason": "Dangerous command detected; suggest safer alternative.",
        "hookSpecificOutput": {"additionalContext": "Review security best practices."}
    }), file=sys.stderr)
    sys.exit(2)  # Blocks prompt

# Add validation context on pass
print("Prompt validated: No security risks found.")
sys.exit(0)
```

Config in `settings.json`: `"command": "python ~/.claude/hooks/validate_prompt.py"`[^4_1][^4_2]

## Add Context Example

Anti-agreement enforcer (checks recent assistant responses in transcript, adds reminder).[^4_6]

```bash
#!/bin/bash
# ~/.claude/hooks/no_agree.sh
stdin=$(cat)
transcript_path=$(echo "$stdin" | jq -r '.transcript_path')
items=$(tail -n 20 "$transcript_path" | grep '"role":"assistant"')

if echo "$items" | grep -qiE "you're (right|correct)|you are (right|correct)"; then
  cat << EOF
Avoid casual agreement. If user is correct, state dispassionately with specific reason.
<example>
user: Add null check.
assistant: Null check addresses empty input; consider falsy values too.
</example>
EOF
fi
exit 0
```

Appends reminder to every prompt if triggered.[^4_6][^4_1]

## Windows Troubleshooting

Start Claude Code from project root (not subdirs) to fix path resolution. Use Git Bash full path (`C:/Program Files/Git/bin/bash.exe`) in `$env:CLAUDE_CODE_GIT_BASH_PATH`; test with `--debug` and `/doctor`. Direct settings.json hooks over plugins; ensure Python/Bash in PATH without npm interference.[^4_7][^4_8][^4_9][^4_10][^4_11]
<span style="display:none">[^4_12][^4_13][^4_14][^4_15][^4_16][^4_17][^4_18]</span>

<div align="center">⁂</div>

[^4_1]: https://code.claude.com/docs/en/hooks

[^4_2]: https://github.com/disler/claude-code-hooks-mastery

[^4_3]: https://github.com/anthropics/claude-code/issues/10964

[^4_4]: https://x.com/dani_avila7/status/2016881811117248867

[^4_5]: https://code.claude.com/docs/en/hooks-guide

[^4_6]: https://gist.github.com/ljw1004/34b58090c16ee6d5e6f13fce07463a31

[^4_7]: https://github.com/anthropics/claude-code/issues/8810

[^4_8]: https://github.com/anthropics/claude-code/issues/7171

[^4_9]: https://www.perplexity.ai/search/36f6c1fd-6cc5-4ffe-a64e-3bf76f312641

[^4_10]: https://github.com/anthropics/claude-code/issues/10225

[^4_11]: https://www.reddit.com/r/ClaudeCode/comments/1nc5oe8/claude_code_hooks_not_blocking_tool_execution_on/

[^4_12]: https://www.reddit.com/r/ClaudeCode/comments/1pa2h2i/looking_for_communitytested_prompts_that_help/

[^4_13]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^4_14]: https://community.openai.com/t/providing-user-capability-to-add-additional-context-to-prompt/1367099

[^4_15]: https://blog.devgenius.io/the-prompt-improver-every-serious-claude-code-user-needs-899d09251de0

[^4_16]: https://modelcontextprotocol.info/docs/concepts/prompts/

[^4_17]: https://shipyard.build/blog/claude-code-cheat-sheet/

[^4_18]: https://www.reddit.com/r/ClaudeAI/comments/1m7r9us/clarification_about_hooks_userpromptsubmit_now/


---

# UserPromptSubmit hook example for secret scanning and blocking

How to rewrite prompts automatically with UserPromptSubmit
UserPromptSubmit vs PreToolUse hook differences
Debugging UserPromptSubmit hooks not triggering
Full bash script template for UserPromptSubmit validation

UserPromptSubmit hooks excel at secret scanning by parsing the `prompt` field from stdin JSON and using regex for common credentials before Claude processes them.[^5_1][^5_2][^5_3]

## Secret Scanning Example

Save as `~/.claude/hooks/secret_scan.py` (Python 3).[^5_1]

```python
#!/usr/bin/env python3
import sys
import json
import re

data = json.load(sys.stdin)
prompt = data.get("prompt", "")

patterns = [
    r'api[_-]?key["\s:=]+["\'][a-zA-Z0-9_-]{20,}["\']',
    r'(AKIA|ASIA)[A-Z0-9]{16}',
    r'ghp_[a-zA-Z0-9]{36}',
    r'sk_live_[a-zA-Z0-9]{24,}',
    r'password["\s:=]+["\'][^"\']{8,}["\']'
]

for pat in patterns:
    if re.search(pat, prompt, re.I):
        print(json.dumps({
            "decision": "block",
            "reason": "Potential secret detected; use env vars instead."
        }), file=sys.stderr)
        sys.exit(2)  # Blocks prompt

sys.exit(0)
```

Config: `"command": "python ~/.claude/hooks/secret_scan.py"` in `UserPromptSubmit`.[^5_2][^5_1]

## Prompt Rewriting

Print rewritten text to stdout (exit 0) to replace/append before Claude sees it; use `jq` for structured edits.[^5_4][^5_3]

```bash
#!/bin/bash
prompt=$(jq -r '.prompt' < /dev/stdin)
rewritten="${prompt/#*/Always reason step-by-step before coding: $prompt}"
echo "$rewritten"
exit 0
```

Adds prefix automatically.[^5_5][^5_4]

## Key Differences

UserPromptSubmit fires on every user prompt (no matcher), intercepts before LLM processing for validation/context/blocks; PreToolUse matches tool names (e.g., "Bash"), blocks before execution.[^5_6][^5_3][^5_2]


| Aspect | UserPromptSubmit | PreToolUse |
| :-- | :-- | :-- |
| Trigger | User prompt submit | Tool call planned |
| Matcher | None (always) | Tool name regex |
| Blocks | Prompt erased | Tool prevented |
| Input | `prompt` string | `tool_input` obj |
| Use | Sanitize input | Gate actions [^5_2][^5_6] |

## Debugging Non-Triggers

Use `claude --debug` or `/hooks` to check registration/matching; plugins fail silently—use direct `settings.json`. Logs show "Hook matched but skipped" if timeout/JSON parse fails; test from project root on Windows.[^5_7][^5_3][^5_8]

## Bash Template

Full validation template (`~/.claude/hooks/validate_prompt.sh`):

```bash
#!/bin/bash
set -euo pipefail

# Read JSON stdin
stdin=$(cat)
prompt=$(echo "$stdin" | jq -r '.prompt // empty')
transcript=$(echo "$stdin" | jq -r '.transcript_path')

# Validation logic
if /"$prompt" =~ dangerous_pattern; then
  echo "{\"decision\":\"block\",\"reason\":\"Invalid prompt\"}" >&2
  exit 2
fi

# Add context
echo "Validation passed. Context: $(date)."

# Optional JSON
echo '{"additionalContext": "Always use TypeScript strict mode."}'
exit 0
```

Chmod +x; robust for Windows Git Bash.[^5_9][^5_2][^5_5]
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_16][^5_17]</span>

<div align="center">⁂</div>

[^5_1]: https://github.com/mintmcp/agent-security

[^5_2]: https://code.claude.com/docs/en/hooks

[^5_3]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^5_4]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^5_5]: https://github.com/disler/claude-code-hooks-mastery

[^5_6]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^5_7]: https://github.com/anthropics/claude-code/issues/10225

[^5_8]: https://github.com/anthropics/claude-code/issues/8810

[^5_9]: https://linuxconfig.org/handling-user-input-in-bash-scripts

[^5_10]: https://x.com/dani_avila7/status/2016881811117248867

[^5_11]: https://pypi.org/project/claude-secret-scan/

[^5_12]: https://www.gend.co/blog/configure-claude-code-hooks-automation

[^5_13]: https://www.aitmpl.com/blog/security-hooks-secrets/

[^5_14]: https://www.claudelog.com/mechanics/hooks/

[^5_15]: https://www.reddit.com/r/ClaudeAI/comments/1mdynb8/finally_fixed_the_two_critical_claude_code_issues/

[^5_16]: https://stackoverflow.com/questions/699576/validating-parameters-to-a-bash-script

[^5_17]: https://www.datacamp.com/tutorial/claude-code-hooks


---

# Example bash script for prompt rewriting

Common debugging steps for UserPromptSubmit hooks
How to add context injection with UserPromptSubmit

UserPromptSubmit hooks rewrite prompts by echoing modified text to stdout (exit 0), which Claude Code uses as the new prompt input.[^6_1][^6_2][^6_3]

## Bash Rewriting Example

Save as `~/.claude/hooks/rewrite_prompt.sh` (chmod +x).[^6_4][^6_1]

```bash
#!/bin/bash
set -euo pipefail

# Read stdin JSON
stdin=$(cat)
prompt=$(echo "$stdin" | jq -r '.prompt // empty')

# Rewrite: Add structure, enforce standards
if /"$prompt" =~ ^(fix; then
  rewritten="Task: $prompt

Guidelines:
- Use TypeScript strict mode
- Add JSDoc comments
- Handle edge cases
- Write tests first"
else
  rewritten="Clarify: $prompt. Think step-by-step."
fi

echo "$rewritten"
exit 0
```

Config: `"command": "~/.claude/hooks/rewrite_prompt.sh"` under `UserPromptSubmit`.[^6_3][^6_1]

## Common Debugging Steps

Run `claude --debug` to log registration/matching/execution (look for "Matched X hooks", "Hook output"). Use `/hooks` chat command to list/test/delete; verify executable scripts and PATH. Check plugins fail silently—prefer `settings.json`; test from project root on Windows.[^6_5][^6_6][^6_7][^6_3]

## Context Injection

Print plain text to stdout (appends directly) or JSON like `{"additionalContext": "Your rules here"}` for structured addition (exit 0). Example:[^6_8][^6_2][^6_3]

```bash
echo '<rules>Always validate inputs. Use async/await.</rules>'
```

Becomes visible context without altering user prompt.[^6_2][^6_3]
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_16][^6_17][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^6_2]: https://code.claude.com/docs/en/hooks

[^6_3]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^6_4]: https://gist.github.com/ljw1004/34b58090c16ee6d5e6f13fce07463a31

[^6_5]: https://github.com/anthropics/claude-code/issues/10225

[^6_6]: https://github.com/anthropics/claude-code/issues/10401

[^6_7]: https://github.com/anthropics/claude-code/issues/8810

[^6_8]: https://github.com/disler/claude-code-hooks-mastery

[^6_9]: https://www.linkedin.com/posts/devonte-emokpae_claude-code-cursor-extension-yolo-patch-activity-7385664914289233920-9wi3

[^6_10]: https://www.reddit.com/r/ClaudeAI/comments/1gsi54r/claude_just_wrote_a_perfect_142line_bash_script/

[^6_11]: https://www.aiengineering.report/p/claude-code-custom-commands-3-practical

[^6_12]: https://apxml.com/courses/getting-started-rag/chapter-4-rag-generation-augmentation/context-injection-methods

[^6_13]: https://code.claude.com/docs/en/hooks-guide

[^6_14]: https://docs.factory.ai/reference/hooks-reference

[^6_15]: https://shipyard.build/blog/claude-code-cheat-sheet/

[^6_16]: https://community.openai.com/t/how-to-configure-prompts-for-chat-completion-with-context-injection/171433

[^6_17]: https://www.anthropic.com/engineering/claude-code-best-practices


---

# UserPromptSubmit hook to block prompts with block reason

Python example script for UserPromptSubmit instead of bash
UserPromptSubmit matcher patterns for specific triggers
Common UserPromptSubmit hook errors and fixes

UserPromptSubmit hooks block prompts via `exit 2` (stderr to Claude/user) or JSON `{"decision": "block", "reason": "..."}` with `exit 0` (erases prompt, shows reason).[^7_1][^7_2][^7_3]

## Block Example (Python)

Save as `~/.claude/hooks/block_prompt.py` (Python 3, executable).[^7_2][^7_1]

```python
#!/usr/bin/env python3
import sys
import json
import re

data = json.load(sys.stdin)
prompt = data.get("prompt", "").lower()

# Block patterns
if re.search(r"(delete|rm -rf|sudo)", prompt) or "secrets" in prompt:
    print(json.dumps({
        "decision": "block",
        "reason": "Dangerous operation or secrets detected. Use safe alternatives."
    }))
    sys.exit(0)  # JSON block

print("Prompt allowed.")
sys.exit(0)
```

Config: `"command": "python ~/.claude/hooks/block_prompt.py"` in `UserPromptSubmit`.[^7_3]

## Python Full Template

Robust template for validation/rewrite/injection (`~/.claude/hooks/user_prompt.py`).[^7_4][^7_2]

```python
#!/usr/bin/env python3
import sys
import json
from datetime import datetime

data = json.load(sys.stdin)
prompt = data.get("prompt", "")

# Log
log = {"timestamp": datetime.now().isoformat(), "prompt": prompt}
with open("~/.claude/logs/prompts.jsonl", "a") as f:
    f.write(json.dumps(log) + "\n")

# Validate/block
if "rm -rf" in prompt.lower():
    print(json.dumps({"decision": "block", "reason": "Destructive command blocked"}))
    sys.exit(0)

# Rewrite/inject
context = "\n\n<guidelines>Use strict TypeScript; add tests.</guidelines>"
print(prompt + context)
sys.exit(0)
```


## Matcher Patterns

UserPromptSubmit has **no matcher**—fires on every prompt (unlike PreToolUse). Use conditional logic inside script for "triggers" (e.g., regex on `prompt`).[^7_5][^7_1][^7_2][^7_3]

## Common Errors \& Fixes

| Error | Cause | Fix [^7_6][^7_3] |
| :-- | :-- | :-- |
| "Hook matched but no output" | Plugins fail silently | Direct `settings.json` only [^7_6] |
| JSON parse fail | Shell profile echoes | Pure JSON stdout; test `echo '{}' | jq` [^7_3] |
| Not triggering | Subdir start (Windows) | Run from project root [^7_7] |
| Exit 2 ignored | Wrong code | Use 2 for block; 0+JSON [^7_1] |
| Stderr not shown | Non-verbose | Ctrl+O or `reason` in JSON [^7_3] |

Debug: `claude --debug`; `/hooks` menu.[^7_8][^7_3]
<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15][^7_16][^7_17][^7_18][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://code.claude.com/docs/en/hooks

[^7_2]: https://github.com/disler/claude-code-hooks-mastery

[^7_3]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^7_4]: https://www.datacamp.com/tutorial/claude-code-hooks

[^7_5]: https://docs.factory.ai/reference/hooks-reference

[^7_6]: https://github.com/anthropics/claude-code/issues/10225

[^7_7]: https://github.com/anthropics/claude-code/issues/8810

[^7_8]: https://github.com/anthropics/claude-code/issues/10401

[^7_9]: https://gist.github.com/ljw1004/34b58090c16ee6d5e6f13fce07463a31

[^7_10]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^7_11]: https://www.reddit.com/r/ClaudeAI/comments/1m31k7b/new_hook_userpromptsubmit/

[^7_12]: https://www.w3schools.com/python/python_user_input.asp

[^7_13]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^7_14]: https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/hook-development/SKILL.md

[^7_15]: https://www.reddit.com/r/ClaudeAI/comments/1mdynb8/finally_fixed_the_two_critical_claude_code_issues/

[^7_16]: https://blog.devgenius.io/the-prompt-improver-every-serious-claude-code-user-needs-899d09251de0

[^7_17]: https://cto.ai/blog/python-ux-prompts/

[^7_18]: https://github.com/promptfoo/promptfoo/blob/main/src/matchers.ts


---

# UserPromptSubmit hook exit code 2 block example

How to configure UserPromptSubmit in hooks.json
Debug UserPromptSubmit hook not executing
Example UserPromptSubmit for adding context to prompts

UserPromptSubmit with exit code 2 blocks prompt processing, erases the original prompt, and feeds stderr directly to Claude for feedback.[^8_1][^8_2][^8_3]

## Exit 2 Block Example

Bash script (`~/.claude/hooks/block_danger.sh`, chmod +x):

```bash
#!/bin/bash
stdin=$(cat)
prompt=$(echo "$stdin" | jq -r '.prompt')

if /"$prompt" =~ (rm\ -rf; then
  echo "Blocked: Destructive command detected. Use safe alternatives like --dry-run." >&2
  exit 2
fi
exit 0
```

Blocks and explains to Claude.[^8_2][^8_1]

## Configuration

Add to `~/.claude/settings.json` (not hooks.json—plugins buggy for this hook).[^8_4][^8_5][^8_3]

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "description": "Block dangerous prompts",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/block_danger.sh"
      }]
    }]
  }
}
```

Reload: `/hooks` or restart.[^8_5][^8_3]

## Debugging Non-Execution

1. `claude --debug`: Check "Registered X hooks", "Matched Y hooks", "Hook output".[^8_6][^8_2]
2. `/hooks`: List/test/delete via chat.[^8_3]
3. Verify from project root (Windows subdir bug).[^8_7]
4. Plugins skip execution—use settings.json only.[^8_4]
5. Test script standalone: `echo '{"prompt":"rm -rf"}' | ~/.claude/hooks/block_danger.sh`.[^8_3]

## Context Addition Example

Simple echo (`~/.claude/hooks/add_context.sh`):

```bash
#!/bin/bash
echo "<context>
- Use TypeScript strict mode
- Add unit tests
- Handle errors explicitly
</context>"
exit 0
```

Appends to every prompt (stdout plain text).[^8_2][^8_5][^8_3]

Python JSON variant:

```python
#!/usr/bin/env python3
import sys, json
print(json.dumps({
  "hookSpecificOutput": {
    "additionalContext": "Project rules: async/await only."
  }
}))
sys.exit(0)
```

Structured control.[^8_3][^8_2]
<span style="display:none">[^8_10][^8_11][^8_12][^8_13][^8_14][^8_15][^8_16][^8_17][^8_8][^8_9]</span>

<div align="center">⁂</div>

[^8_1]: https://x.com/dani_avila7/status/2016881811117248867

[^8_2]: https://code.claude.com/docs/en/hooks

[^8_3]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^8_4]: https://github.com/anthropics/claude-code/issues/10225

[^8_5]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^8_6]: https://github.com/anthropics/claude-code/issues/10401

[^8_7]: https://github.com/anthropics/claude-code/issues/8810

[^8_8]: https://github.com/anthropics/claude-code/issues/19009

[^8_9]: https://github.com/anthropics/claude-code/issues/10964

[^8_10]: https://code.claude.com/docs/en/hooks-guide

[^8_11]: https://github.com/anthropics/claude-code/issues/17277

[^8_12]: https://community.openai.com/t/providing-user-capability-to-add-additional-context-to-prompt/1367099

[^8_13]: https://docs.factory.ai/reference/hooks-reference

[^8_14]: https://modelcontextprotocol.info/docs/concepts/prompts/

[^8_15]: https://www.reddit.com/r/ClaudeAI/comments/1p69q72/anyone_else_getting_this_weird_claude_code_error/

[^8_16]: https://www.reddit.com/r/ClaudeAI/comments/1m7r9us/clarification_about_hooks_userpromptsubmit_now/

[^8_17]: https://www.reddit.com/r/ClaudeAI/comments/1mdynb8/finally_fixed_the_two_critical_claude_code_issues/


---

# Full hooks.json template for multiple hook events

Fix UserPromptSubmit not triggering after context compaction
SessionStart hook example for initial setup
Verbose mode to debug hook stderr output

Hooks are configured in `~/.claude/settings.json` or `.claude/settings.json`, not hooks.json (plugins use hooks/hooks.json but are unreliable for UserPromptSubmit).[^9_1][^9_2][^9_3]

## Full Template

Complete `settings.json` for multiple events (project `.claude/settings.json`):

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "uv run .claude/hooks/session_start.py"
      }]
    }],
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python .claude/hooks/user_prompt_submit.py"
      }]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/block_danger.sh"
      }]
    }, {
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "black $CLAUDE_PROJECT_DIR"
      }]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/log_tool.py"
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/stop_handler.py"
      }]
    }]
  }
}
```

Reload with `/hooks`.[^9_4][^9_2][^9_3]

## Fix Non-Trigger After Compaction

Known bug: UserPromptSubmit skips early session or post-compaction prompts (GitHub \#17277). Workaround: Use SessionStart matcher "compact" to re-inject context post-compaction; restart session or `/clear` resets.[^9_2][^9_5][^9_6][^9_3]

## SessionStart Example

For initial setup (`~/.claude/hooks/session_start.py`):

```python
#!/usr/bin/env python3
import sys, json, subprocess
data = json.load(sys.stdin)
source = data.get("source")

context = f"""
Session {source}: {subprocess.run(['git', 'status', '--short'], capture_output=True, text=True).stdout}
Recent changes loaded.
"""
print(context)
sys.exit(0)
```

Matcher "compact" re-adds after compaction.[^9_3][^9_4][^9_2]

## Verbose Mode

Toggle `Ctrl+O` to show stderr/non-zero exit logs in transcript (e.g., hook errors, reasons). Use `claude --debug` for startup/execution traces; Ctrl+R for full stdout.[^9_7][^9_8][^9_9][^9_3]
<span style="display:none">[^9_10][^9_11][^9_12][^9_13][^9_14][^9_15][^9_16]</span>

<div align="center">⁂</div>

[^9_1]: https://www.datacamp.com/tutorial/claude-code-hooks

[^9_2]: https://code.claude.com/docs/en/hooks

[^9_3]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^9_4]: https://github.com/disler/claude-code-hooks-mastery

[^9_5]: https://github.com/anthropics/claude-code/issues/17277

[^9_6]: https://code.claude.com/docs/en/hooks-guide?8adb0641_page=4\&cc61befa_page=2\&d7430fcd_page=5\&r=0

[^9_7]: https://github.com/anthropics/claude-code/issues/4859

[^9_8]: https://code.claude.com/docs/en/hooks-guide

[^9_9]: https://stevekinney.com/courses/ai-development/claude-code-hook-control-flow

[^9_10]: https://www.reddit.com/r/ClaudeCode/comments/1ne4zh1/ask_reddit_claude_code_hooks_with_multiple/

[^9_11]: https://www.gend.co/blog/configure-claude-code-hooks-automation

[^9_12]: https://github.com/anthropics/claude-code/issues/4318

[^9_13]: https://forums.basehub.com/anomalyco/opencode/20

[^9_14]: https://github.com/anthropics/claude-code/issues/3328

[^9_15]: https://github.com/anthropics/claude-code/issues/3447

[^9_16]: https://www.reddit.com/r/ClaudeAI/comments/1oq12f0/claude_code_sessionstart_hook_output_only_shown/


---

# How to run multiple hooks in parallel for one event

Hook JSON input output formats reference

Claude Code runs multiple matching hooks for an event **in parallel** by default, with automatic deduplication of identical commands.[^10_1][^10_2][^10_3]

## Parallel Hooks

List multiple under `hooks` array—no extra config needed; they spawn concurrently (e.g., log + validate).[^10_3][^10_1]

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [
        {"type": "command", "command": "python log.py"},
        {"type": "command", "command": "python validate.py"},
        {"type": "command", "command": "echo 'Context'"}
      ]
    }]
  }
}
```

All run async; short-circuit on exit 2 blocks.[^10_1][^10_3]

## JSON Formats

### Common Input Fields (stdin JSON)

| Field | Type | Description |
| :-- | :-- | :-- |
| `session_id` | string | Unique session ID [^10_2] |
| `transcript_path` | string | Log file path |
| `cwd` | string | Working directory |
| `hook_event_name` | string | e.g., "UserPromptSubmit" [^10_3] |

**UserPromptSubmit-specific**: `{"prompt": "user text", ...}`

### Output (stdout JSON, exit 0)

| Field | Description |
| :-- | :-- |
| `decision` | "allow"\|"block" (event-specific) |
| `reason` | Block explanation |
| `hookSpecificOutput.additionalContext` | Appends to prompt |
| `continue` | true/false |
| `suppressOutput` | Hide from transcript [^10_2][^10_4] |

**Exit codes**: 0=success (parse JSON), 2=block (stderr only).[^10_3][^10_1]

Example output:

```json
{
  "decision": "allow",
  "hookSpecificOutput": {"additionalContext": "Rules here."}
}
```

Shell profiles must not echo (JSON validation fail).[^10_1][^10_3]
<span style="display:none">[^10_10][^10_11][^10_12][^10_13][^10_14][^10_15][^10_16][^10_5][^10_6][^10_7][^10_8][^10_9]</span>

<div align="center">⁂</div>

[^10_1]: https://code.claude.com/docs/en/hooks-guide

[^10_2]: https://code.claude.com/docs/en/hooks

[^10_3]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^10_4]: https://github.com/disler/claude-code-hooks-mastery

[^10_5]: https://www.reddit.com/r/ClaudeAI/comments/1qpb90n/anyone_else_running_multiple_claude_code/

[^10_6]: https://dev.to/bredmond1019/multi-agent-orchestration-running-10-claude-instances-in-parallel-part-3-29da

[^10_7]: https://blog.gitbutler.com/parallel-claude-code

[^10_8]: https://www.datacamp.com/tutorial/claude-code-hooks

[^10_9]: https://github.com/anthropics/claude-code/issues/4446

[^10_10]: https://buttondown.com/dgalarza/archive/run-multiple-claude-code-agents-at-once/

[^10_11]: https://stevekinney.com/courses/ai-development/claude-code-hook-control-flow

[^10_12]: https://www.youtube.com/watch?v=WEHyvxbMLSc

[^10_13]: https://github.com/anthropics/claude-code/issues/3983

[^10_14]: https://www.youtube.com/watch?v=8T0kFSseB58

[^10_15]: https://www.gend.co/blog/configure-claude-code-hooks-automation

[^10_16]: https://www.youtube.com/watch?v=Bz5fyyCa2-0


---

# How to handle dependencies between parallel hooks in Claude Code

Example of sequential hook execution workaround
Common pitfalls with parallel hook JSON processing
Async hooks configuration and usage examples
How to debug multiple hooks running in parallel

Claude Code hooks run strictly in parallel with no native dependency handling—combine logic into single scripts for order.[^11_1][^11_2][^11_3]

## Dependencies

No built-in sequencing (feature request \#4446 open); parallel spawns ignore order, so use temp files, env vars, or shared state (e.g., SQLite).[^11_4][^11_3][^11_1]

## Sequential Workaround

Single master script orchestrates steps (`.claude/hooks/master_validate.sh`):

```bash
#!/bin/bash
# Step 1: Log
echo "$stdin" | tee /tmp/prompt_log.json | jq .prompt > /tmp/log.txt

# Step 2: Validate (depends on log)
if grep -q "danger" /tmp/log.txt; then echo "Blocked" >&2; exit 2; fi

# Step 3: Rewrite
echo "$stdin" | jq -r '.prompt' | sed 's/^/Structured: /' | jq -sR 'input | {prompt: .}'

exit 0
```

Config: One hook calls master; mimics sequence.[^11_5][^11_1]

## Pitfalls

- Shell profiles echo breaks JSON parse (stdout must be pure JSON).[^11_2][^11_3]
- Race on shared resources (files/env)—use locks.[^11_3]
- Non-0 exit ignores JSON; timeouts (60s) kill independents.[^11_2]
- Dedup identical commands only.[^11_3]


## Async Config

Add `"async": true` per-handler (v2.1.23+): non-blocking for logging/metrics.[^11_6][^11_7]

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [
        {"type": "command", "command": "log.py", "async": true},
        {"type": "command", "command": "validate.py"}  // Sync blocks
      ]
    }]
  }
}
```

Async: Fire-forget, no wait/decision impact.[^11_6]

## Debugging Parallel

`claude --debug`: Logs all matches, PIDs, exits (e.g., "[DEBUG] Spawned hook PID 1234"). Ctrl+O verbose: Stderr/stdout. `/hooks`: Live list. Tail `/tmp/hook_debug.log` in scripts.[^11_5][^11_2][^11_3]
<span style="display:none">[^11_10][^11_11][^11_12][^11_13][^11_14][^11_15][^11_16][^11_8][^11_9]</span>

<div align="center">⁂</div>

[^11_1]: https://github.com/anthropics/claude-code/issues/4446

[^11_2]: https://code.claude.com/docs/en/hooks

[^11_3]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^11_4]: https://github.com/anthropics/claude-code/issues/21533

[^11_5]: https://code.claude.com/docs/en/hooks-guide

[^11_6]: https://www.reddit.com/r/ClaudeCode/comments/1qras98/claude_code_async_hooks_what_they_are_and_when_to/

[^11_7]: https://github.com/anthropics/claude-code/issues/4445

[^11_8]: https://blog.davisvaughan.com/posts/2026-01-09-claude-200-pull-requests/

[^11_9]: https://claudefa.st/blog/guide/agents/sub-agent-best-practices

[^11_10]: https://github.com/anthropics/claude-code/issues/3983

[^11_11]: https://docs.anthropic.com/en/docs/claude-code/hooks?asuniq=d8f8d9d0

[^11_12]: https://www.reddit.com/r/ClaudeAI/comments/1dlvuuq/claude_breaks_json_more_often_than_openai/

[^11_13]: https://github.com/ruvnet/claude-flow/wiki/Hooks-System

[^11_14]: https://blog.gitbutler.com/parallel-claude-code

[^11_15]: https://blog.devgenius.io/claude-codes-task-primitives-from-single-threaded-assistant-to-parallel-powerhouse-540bfbc8fc60

[^11_16]: https://www.datacamp.com/tutorial/claude-code-hooks


---

# Best practices for async true hooks in Claude Code

`async: true` hooks (Claude Code v2.1.23+) run fire-and-forget in background, non-blocking for speed—ideal for non-critical tasks.[^12_1][^12_2][^12_3]

## Core Practices

Use async only for observation/reporting (logging, metrics, notifications)—sync for validation/blocks impacting flow.[^12_4][^12_1]

- **Sync if**: Blocks, rewrites, decisions (exit 2, JSON `decision`).
- **Async if**: Logs, Slack pings, telemetry (no stdout needed).[^12_1]


## Configuration

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [
        {"type": "command", "command": "log_tool.py", "async": true},
        {"type": "command", "command": "validate.py"}  // Sync
      ]
    }]
  }
}
```

Async ignores output/exit; timeouts don't block.[^12_3][^12_1]

## Examples

**Async logging** (`log_tool.py`):

```python
import sys, json
data = json.load(sys.stdin)
with open("/tmp/tools.jsonl", "a") as f:
  f.write(json.dumps(data) + "\n")
# No print/exit needed
```

Non-blocking append.[^12_1]

**Async notification**:

```bash
#!/bin/bash
curl -X POST slack-webhook <<< "$stdin" &
```

Background Slack ping.[^12_2]

## Pitfalls \& Tips

- **No impact**: Async output/exit ignored—pure side-effects.[^12_1]
- **Order none**: Parallel regardless; use single script for deps.
- **Debug**: `--debug` shows PIDs; logs separate (`Ctrl+O` verbose).[^12_3]
- **Migrate**: Audit with `/hooks`, ask Claude "propose async hooks".[^12_2]
- **60s timeout**: Async safer for slow networks.[^12_4]

Prioritize: 80% hooks async for <100ms latency gains.[^12_2][^12_1]
<span style="display:none">[^12_10][^12_11][^12_5][^12_6][^12_7][^12_8][^12_9]</span>

<div align="center">⁂</div>

[^12_1]: https://www.reddit.com/r/ClaudeCode/comments/1qras98/claude_code_async_hooks_what_they_are_and_when_to/

[^12_2]: https://www.youtube.com/watch?v=57U5vXqLKfo

[^12_3]: https://code.claude.com/docs/en/hooks

[^12_4]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^12_5]: https://code.claude.com/docs/en/hooks-guide

[^12_6]: https://github.com/anthropics/claude-code/issues/4445

[^12_7]: https://www.cometapi.com/claude-code-hooks-what-is-and-how-to-use-it/

[^12_8]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^12_9]: https://www.anthropic.com/engineering/claude-code-best-practices

[^12_10]: https://www.claudecode.page/guides/best-practices

[^12_11]: https://www.youtube.com/watch?v=J5B9UGTuNoM


---

# Which of the 12 hook events support async true

Common pitfalls when using async hooks
How to migrate sync hooks to async true
Performance impact of async vs sync hooks

**All 12 Claude Code hook events** support `"async": true` (v2.1.23+), as it's per-command handler flag—not event-restricted.[^13_1][^13_2][^13_3]

## 12 Events Quick Reference

| Event | Typical Async Use | Sync Must |
| :-- | :-- | :-- |
| SessionStart | Logging session | Context load [^13_2] |
| UserPromptSubmit | Metrics | Blocking/rewrite |
| PreToolUse | Notify tool | Block tool |
| PostToolUse | Log output | Cleanup |
| PreLLMResponse | Telemetry | Edit response |
| Stop | Cleanup | Final save |
| Compact | Stats | Context inject |
| Notification | Alerts | None |
| PreWrite | Audit | Format |
| PostWrite | Backup | Validate [^13_1] |

## Async Pitfalls

- **Ignored output/exit**: No JSON/decision processed; pure side-effects.[^13_2]
- **No error feedback**: Failures silent (no transcript); log internally.[^13_1]
- **Races on shared state**: No ordering; use atomic writes.[^13_2]
- **60s timeout irrelevant**: Detached, but system limits apply.[^13_3]


## Migration Steps

1. **Audit**: `/hooks`, ask Claude: "Classify my hooks: async-safe?"[^13_4][^13_5]
2. **Flag logging/telemetry**: `PostToolUse`, `SessionStart` → async.[^13_2]
3. **Keep sync**: Blocks (`exit 2`), rewrites, validations.[^13_2]
4. **Test**: `--debug` PIDs, measure latency (`time claude`).[^13_1]

Example:

```json
// Before
{"command": "log.py"}  // Sync, 2s block

// After
{"command": "log.py", "async": true}  // Background
```


## Performance

Async: 50-90% faster perceived latency (no wait); e.g., 5s Slack → invisible. Sync: Full serial wait (e.g., 3 hooks @2s=6s block). Parallel async: Max(hook times), often <100ms gain for logging-heavy setups.[^13_5][^13_4][^13_1][^13_2]
<span style="display:none">[^13_10][^13_11][^13_12][^13_13][^13_14][^13_15][^13_16][^13_6][^13_7][^13_8][^13_9]</span>

<div align="center">⁂</div>

[^13_1]: https://code.claude.com/docs/en/hooks

[^13_2]: https://www.reddit.com/r/ClaudeCode/comments/1qras98/claude_code_async_hooks_what_they_are_and_when_to/

[^13_3]: https://www.perplexity.ai/search/5f0bb00c-189b-48a8-a383-3dbff2f2aa4d

[^13_4]: https://www.linkedin.com/pulse/my-claude-code-setup-faster-builds-bulletproof-scraping-yaron-been-hkpzf

[^13_5]: https://www.youtube.com/watch?v=57U5vXqLKfo

[^13_6]: https://github.com/anthropics/claude-code/issues/4445

[^13_7]: https://code.claude.com/docs/en/hooks-guide

[^13_8]: https://docs.anthropic.com/en/docs/claude-code/hooks?asuniq=d8f8d9d0

[^13_9]: https://blog.pixelfreestudio.com/debugging-async-await-common-pitfalls-and-solutions/

[^13_10]: https://github.com/disler/claude-code-hooks-mastery

[^13_11]: https://x.com/lucas_flatwhite/status/2015635739711869381

[^13_12]: https://x.com/bcherny/status/2015524460481388760/photo/1

[^13_13]: https://code.likeagirl.io/common-mistakes-in-handling-promises-why-your-async-code-fails-6e4d5c79440c

[^13_14]: https://www.anthropic.com/engineering/claude-code-best-practices

[^13_15]: https://dev.to/leapcell/rust-concurrency-common-async-pitfalls-explained-53p1

[^13_16]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45


---

# please create a topic index for what we discussed in this session.

Here’s a compact topic index of what we covered in this session about Claude Code hooks, with emphasis on UserPromptSubmit and async behavior.[^14_1][^14_2]

## 1. UserPromptSubmit Hook Basics

- Purpose and lifecycle (runs on every prompt before LLM).[^14_1]
- JSON input fields (prompt, session_id, transcript_path, cwd, hook_event_name).[^14_1]
- Output channels: stdout text vs JSON, exit codes (0, 2) and how they affect blocking and context injection.[^14_3][^14_1]


## 2. UserPromptSubmit Errors on Windows

- Symptoms: hook “errors” despite working, not triggering consistently, plugin hooks matching but not executing.[^14_4][^14_5][^14_6]
- Windows-specific issues: path resolution from subdirectories, race conditions, and file-modification errors similar to sapling_checkpoint.py.[^14_7][^14_8][^14_4]
- Workarounds: use `settings.json` instead of plugin hooks, run from project root, ensure correct shells/Python on PATH.[^14_5][^14_1]


## 3. Example UserPromptSubmit Scripts

- Logging prompts: Python script appending JSONL entries, configuration in `.claude/settings.json`.[^14_9][^14_10]
- Validation and blocking: scripts detecting dangerous commands/secrets and either returning JSON `{"decision":"block","reason":...}` or exiting with code 2 and stderr.[^14_11][^14_12][^14_1]
- Context injection: echoing guidelines to stdout or returning JSON with `hookSpecificOutput.additionalContext`.[^14_13][^14_1]
- Prompt rewriting: Bash scripts reading `.prompt` via `jq`, restructuring or prefixing prompts before Claude sees them.[^14_14][^14_11]


## 4. Exit Codes and Control Flow

- Exit 0: success; plain-text stdout appended as context; JSON parsed for decisions and additionalContext.[^14_1]
- Exit 2: blocking error; prompt erased, stderr fed directly to Claude/user as explanation; used in UserPromptSubmit and some other events.[^14_15][^14_3]
- Other non-zero codes: treated as hook error; decision fields ignored, useful only for debugging logs.[^14_2][^14_1]


## 5. Multiple Hooks per Event \& Parallelism

- Parallel execution model: all matching hooks for an event run in parallel; identical commands deduplicated.[^14_2]
- Config pattern: `hooks` array under each event (e.g., logging + validation + context in UserPromptSubmit).[^14_9][^14_1]
- Dependency workaround: one “master” script orchestrating sequential steps and shared temp files instead of multiple dependent hooks.[^14_16][^14_2]


## 6. Async Hooks (`"async": true`)

- Availability: per-command flag, supported on all hook events in recent Claude Code versions (2.1.23+).[^14_17][^14_1]
- Semantics: async hooks are fire-and-forget, do not block Claude, and cannot influence decisions (JSON output/exit codes are ignored for control).[^14_18][^14_17]
- Best practices: use async for logging, metrics, notifications, test runners; keep validation, blocking, and prompt rewriting sync.[^14_17][^14_18]
- Migration strategy: audit existing hooks, mark side-effect-only ones as async, measure reduced latency; keep security/governance hooks synchronous.[^14_19][^14_17]


## 7. SessionStart and Other Events

- SessionStart examples: initial context injection (rules, git status, project summary) when sessions start or resume.[^14_20][^14_1]
- Using SessionStart plus UserPromptSubmit to re-inject or reinforce rules after context compaction.[^14_21][^14_2]
- Other events mentioned: PreToolUse/PostToolUse for tooling gates and logging; Stop / SessionEnd for cleanup or summaries.[^14_22][^14_1]


## 8. Debugging Hooks

- CLI tools: `claude --debug` for registration/matching/execution traces; `/hooks` command in-chat for listing/testing.[^14_23][^14_2]
- Verbose mode: Ctrl+O to surface stderr and hook errors in the transcript; useful for UserPromptSubmit and SessionStart diagnostics.[^14_24][^14_25]
- Common JSON pitfalls: shell profiles printing banners, mixed text+JSON, malformed output causing parse failures and “hook error” messages.[^14_26][^14_1]

If you want, I can turn this into a CLAUDE.md “Hooks Quick Index” section you can drop directly into your repo.
<span style="display:none">[^14_27][^14_28][^14_29][^14_30][^14_31][^14_32][^14_33][^14_34][^14_35]</span>

<div align="center">⁂</div>

[^14_1]: https://code.claude.com/docs/en/hooks

[^14_2]: https://code.claude.com/docs/en/hooks-guide

[^14_3]: https://x.com/dani_avila7/status/2016881811117248867

[^14_4]: https://github.com/anthropics/claude-code/issues/8810

[^14_5]: https://github.com/anthropics/claude-code/issues/10225

[^14_6]: https://github.com/anthropics/claude-code/issues/17277

[^14_7]: https://www.reddit.com/r/ClaudeCode/comments/1nc5oe8/claude_code_hooks_not_blocking_tool_execution_on/

[^14_8]: https://www.perplexity.ai/search/841f4986-cb0d-4c33-9c3f-1bd6bbf28ea2

[^14_9]: https://github.com/disler/claude-code-hooks-mastery

[^14_10]: https://www.datacamp.com/tutorial/claude-code-hooks

[^14_11]: https://gist.github.com/ljw1004/34b58090c16ee6d5e6f13fce07463a31

[^14_12]: https://github.com/mintmcp/agent-security

[^14_13]: https://github.com/dagger/container-use/issues/253

[^14_14]: https://www.youtube.com/watch?v=x5-nRfxO5u4

[^14_15]: https://github.com/anthropics/claude-code/issues/10964

[^14_16]: https://github.com/anthropics/claude-code/issues/4446

[^14_17]: https://www.reddit.com/r/ClaudeCode/comments/1qras98/claude_code_async_hooks_what_they_are_and_when_to/

[^14_18]: https://www.marc0.dev/en/blog/claude-code-hooks-production-patterns-async-setup-guide-1770480024093

[^14_19]: https://www.linkedin.com/pulse/my-claude-code-setup-faster-builds-bulletproof-scraping-yaron-been-hkpzf

[^14_20]: https://github.com/anthropics/claude-code/issues/4318

[^14_21]: https://code.claude.com/docs/en/hooks-guide?8adb0641_page=4\&cc61befa_page=2\&d7430fcd_page=5\&r=0

[^14_22]: https://anthropic.mintlify.app/en/docs/claude-code/hooks-guide

[^14_23]: https://github.com/anthropics/claude-code/issues/10401

[^14_24]: https://github.com/anthropics/claude-code/issues/4859

[^14_25]: https://www.reddit.com/r/ClaudeAI/comments/1oq12f0/claude_code_sessionstart_hook_output_only_shown/

[^14_26]: https://github.com/anthropics/claude-code/issues/3983

[^14_27]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^14_28]: https://www.reddit.com/r/ClaudeAI/comments/1loodjn/claude_code_now_supports_hooks/

[^14_29]: https://github.com/ericbuess/claude-code-project-index

[^14_30]: https://www.youtube.com/watch?v=Q4gsvJvRjCU

[^14_31]: https://www.anthropic.com/engineering/claude-code-best-practices

[^14_32]: https://blog.gitbutler.com/automate-your-ai-workflows-with-claude-code-hooks

[^14_33]: https://www.eesel.ai/blog/hooks-reference-claude-code

[^14_34]: https://github.com/decider/claude-hooks

[^14_35]: https://www.reddit.com/r/ClaudeAI/comments/1o2l673/really_hard_to_use_claudemd_to_efficiently_read/


---

# I need a filename to save this session with.  what tags should be in the filename?

A compact, searchable pattern that fits this session well:

`claude-code_hooks-userpromptsubmit_async-windows-debug_2026-02-09.md`[^15_1][^15_2]

Core tags you likely want in the filename:

- `claude-code` – tool context.[^15_3]
- `hooks` – feature family.[^15_1]
- `userpromptsubmit` – main hook event.[^15_4]
- `async` – async hook focus.[^15_5]
- `windows` – environment where bugs differ.[^15_6]
- `debug` – lots of debugging/diagnostics patterns.[^15_7]

<div align="center">⁂</div>

[^15_1]: https://code.claude.com/docs/en/hooks

[^15_2]: https://code.claude.com/docs/en/hooks-guide

[^15_3]: https://www.anthropic.com/engineering/claude-code-best-practices

[^15_4]: https://github.com/dagger/container-use/issues/253

[^15_5]: https://www.reddit.com/r/ClaudeCode/comments/1qras98/claude_code_async_hooks_what_they_are_and_when_to/

[^15_6]: https://github.com/anthropics/claude-code/issues/8810

[^15_7]: https://github.com/anthropics/claude-code/issues/10401


---

# what prompt should I use next time, to generate that tagfull filename and table of contents?

Use something like this, right at the end of the session:

> “Given our full conversation so far, propose a concise, tag‑rich filename for saving this chat and a topic index/table of contents.
>
> Filename requirements:
> - Include: product (`claude-code`), main feature (`hooks`), key hook (`userpromptsubmit`), platform if relevant (e.g. `windows`), and any special focus (e.g. `async`, `debug`).
> - Use kebab-case with underscores between major sections, and append today’s date as `YYYY-MM-DD`.
> - Return only one filename string.
>
> Topic index requirements:
> - 5–15 bullet points, each 1 line, ordered from foundational concepts to advanced patterns.
> - Each bullet: `SectionTitle – short description`.
> - Focus on what’s most reusable for future Claude Code work, not every minor tangent.”

This will reliably recreate the tagged filename and the kind of topic index we just built.[^16_1][^16_2]

<div align="center">⁂</div>

[^16_1]: https://code.claude.com/docs/en/hooks

[^16_2]: https://code.claude.com/docs/en/hooks-guide

