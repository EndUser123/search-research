---
title: "in claude code on windows 11, how can we enforce these principles?
'You’re right: I drifted back into talking about hook"
date: "2026-03-06"
mode: "COPILOT"
uuid: "cdaffa9d-f099-43b7-9e31-44ce1449c792"
entry_count: 3
---

## Human

in claude code on windows 11, how can we enforce these principles?
"You’re right: I drifted back into talking about hooks instead of the behavior patterns you actually care about.[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
Here are the behavioral changes implied by your transcript and principles:
1. Never normalize a bug
Behavior rule:
The assistant must never respond to “this is obviously wrong” with any framing that makes it sound acceptable (e.g., “visible logging,” “fine as-is,” “cosmetic,” “expected duplicate”).[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
Allowed responses are only:
Acknowledge it as a bug.
Propose how to trace source and fix it.
Suggest a temporary mitigation with an explicit intent to remove it.
In the progress-bar case, the only valid behavior is: “That’s a bug. Let’s trace where tasks are duplicated and stop that,” not “we can treat it as logging.”[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
2. No “meta” answer without a concrete fix path
Behavior rule:
When you report a failure, the assistant can give context or analysis, but it must end with a specific fix path: where to instrument, what to inspect, and what success looks like.[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
Pure explanation (“why PostToolUse behaves this way,” “why skills vs docs are awkward”) without a clear next action is treated as a failed answer.
In the Bash/path conversation, the right behavior was: “The hook will never catch this; here’s how we should change our editing pattern or validation,” not three paragraphs about design tradeoffs.[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
3. Prefer simplification over cleverness by default
Behavior rule:
When deciding between a simple, slightly manual fix and a clever system (router, hook, gate), the assistant must default to the simple option unless it can justify the complex one against your principles.[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
“Add another gate/router” is the last resort, not the first idea.
Many of the things in the transcript (research router, Bash syntax gate, docs-as-skills) came from the opposite bias.[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
4. Respect your local reality and intent
Behavior rule:
The assistant must prioritize what you say about your environment and intent over generic best practices or training priors.[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
Example: if you say “these are instructions for other skills to use” or “this doesn’t seem optimal,” it should pivot to your framing and work from there, not defend the existing architecture.[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
In the transcript, you had to fight it away from defending the status quo toward what you actually wanted.[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
5. Minimize friction in your feedback loop
Behavior rule:
Once you express annoyance (“why do you keep halting?”, “I hate option 2, it’s lazy and stupid”), the assistant must treat that as a hard signal to stop doing that pattern and adjust immediately, not keep repeating it.[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
That means shorter, more direct answers, fewer “baked for Xs” style narratives, and less self-congratulation about gates and summaries.
The transcript shows it continuing behaviors even after you clearly flagged them as irritating.[[ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/149814877/9409dd7a-3d09-41a9-9cb9-d5ba55cdbb76/reasoning.txt)]​
These are about how the assistant thinks and talks with you, not about what hooks exist. The machinery should follow from these behaviors, not the other way around.
Given those, the only meaningful test now is: in the next thing you bring up, do I follow these five behaviors or slip back into machinery talk. Do you want to use the duplicate progress bars case as the next behavioral test, or something more recent?"

## Assistant

To enforce these five behavioral principles in Claude Code on Windows 11, use a combination of system prompt overrides and targeted hooks that inject rules, validate responses, and block non-compliant outputs. This leverages Claude Code's configuration for deterministic control without relying solely on the LLM's priors.[1][2]

## System Prompt Setup
Launch Claude Code with `--append-system-prompt` or `--system-prompt` flags to embed the principles at the prompt level, ensuring Claude internalizes them from the start. For example, create a `principles.md` file with the exact rules (never normalize bugs, always end with fix paths, etc.), then run `claude --append-system-prompt principles.md` in PowerShell—this positions rules above tool definitions for strong adherence.[3][2]

On Windows 11, add an alias in PowerShell profile (`$PROFILE`):  
```powershell  
function Start-ClaudePrinciples { claude --append-system-prompt principles.md }  
```  
This persists across sessions and respects your multi-terminal workflow.

## Stop Hook for Compliance
Configure a `Stop` hook in `.claude/settings.json` (project-specific, git-committable) to analyze Claude's final response before allowing it to finish, blocking if it violates principles—like reframing bugs or lacking fix paths.[1]

Example config (PowerShell-friendly script at `.claude/hooks/check-principles.ps1`):  
```json  
{  
  "hooks": {  
    "Stop": [  
      {  
        "hooks": [  
          {  
            "type": "command",  
            "command": "powershell -ExecutionPolicy Bypass -File \"$CLAUDE_PROJECT_DIR/.claude/hooks/check-principles.ps1\""  
          }  
        ]  
      }  
    ]  
  }  
}  
```  

Script content (`check-principles.ps1`—parses transcript for violations using regex/keywords like "fine as-is", "expected duplicate", no fix path):  
```powershell  
$input = Get-Content -Raw | ConvertFrom-Json  
$transcriptPath = $input.transcript_path  
$lastResponse = Get-Content $transcriptPath -Tail 50 | Select-String '"role": "assistant"' -AllMatches | Select-Object -Last 1 -Expand Matches | ForEach { $_ -replace '.*"content": "(.*)".*', '$1' }  

# Check principles (simplified regex examples)  
if ($lastResponse -match 'fine as-is|cosmetic|expected duplicate|visible logging' -or $lastResponse -notmatch 'trace.*source|fix.*path|instrument') {  
  @{ decision = 'block'; reason = 'Violates principles: normalize bug or no fix path. Retry compliant.' } | ConvertTo-Json  
  exit 0  
}  
exit 0  
```  
This blocks and feeds the reason back to Claude, forcing retries—aligns with minimizing friction by immediate adjustment.[1]

## UserPromptSubmit for Input Alignment
Add a `UserPromptSubmit` hook to rewrite or block user prompts that might trigger bad patterns, injecting principle reminders as `additionalContext`. Use `type: "prompt"` for LLM-judged injection on Windows.

Example:  
```json  
{  
  "hooks": {  
    "UserPromptSubmit": [  
      {  
        "hooks": [  
          {  
            "type": "prompt",  
            "prompt": "Review prompt: $ARGUMENTS. If it risks bad patterns, add: 'Follow principles: no bug normalization, always concrete fix paths, prefer simple fixes, respect my Windows 11/Claude Code intent, adjust on annoyance.' Output JSON {ok: bool, additionalContext: str if needed}."  
        }  
      }  
    ]  
  }  
}  
```  
This pre-empts issues like meta-talk without fixes.[1]

## Windows 11 Notes
Hooks work reliably on Windows 11 via PowerShell (your preferred shell), but test execution policy (`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass`). Avoid known silent failures by using `.claude/settings.local.json` for local tweaks and `/hooks` menu for interactive setup/testing. Restart sessions after config changes.[4]

Test on your duplicate progress bars case: launch with principles prompt, flag a bug, and verify enforced tracing over normalization.[5]

## Human

Using --append-system-prompt for behavior rules

## Assistant

Yes, using `--append-system-prompt` is the most effective way to enforce your behavioral principles in Claude Code on Windows 11, as it adds high-priority rules directly to the system prompt—above tool definitions but preserving base behavior—for strong, session-specific adherence without overriding core functionality.[1][2][3]

## Command Usage
Run Claude Code with `--append-system-prompt <file-or-string>` from PowerShell in your project directory. It appends content at the end of the base system prompt (after output styles, before tools), giving rules like "Never normalize bugs" maximal influence since Claude prioritizes later prompt sections.[3][1]

Examples:  
- From file: `claude --append-system-prompt principles.md` (create `principles.md` with your 5 rules verbatim).  
- Inline: `claude --append-system-prompt "1. Never normalize a bug... [full rules]"`.  
Combine with project context: `claude --append-system-prompt principles.md your_project/`. On Windows 11, use short paths or quotes to avoid ENAMETOOLONG for long strings—prefer files.[4]

## PowerShell Integration
Add a persistent alias in your `$PROFILE` for frictionless use:  
```powershell
Set-Alias claude-princ "claude --append-system-prompt principles.md"
```
Reload with `. $PROFILE`, then `claude-princ`. This fits your multi-terminal setup and ensures rules load every session.[2]

## Effectiveness for Principles
This method excels for your rules: it forces bug acknowledgment over reframing, mandates fix paths, prefers simplification, respects local intent (e.g., Windows 11 specifics), and cuts friction by immediate adjustment—no extra hooks needed initially. Test by prompting a "bug" like duplicate progress bars; Claude must trace/fix, not excuse.[5][1]

For persistence, pair with `CLAUDE.md` (loads earlier, broader context) or hooks for validation.[2]

## Human

What is the difference between --append-system-prompt and --system-prompt

## Assistant

`--append-system-prompt` adds your rules to the end of Claude Code's default system prompt (before tool definitions), preserving base behavior while prioritizing your additions. `--system-prompt` completely replaces the entire default system prompt, risking loss of core functionality like tool integration and output formatting.[1][5][7]

## Prompt Structure Impact
Claude Code's full system prompt follows this order:  
- Base instructions + output styles  
- `--append-system-prompt` content (high influence, sits above tools)  
- Tool definitions  

`--append-system-prompt "Never normalize bugs..."` injects your 5 principles exactly where Claude weighs them heavily—late enough to override priors but early enough for tools to respect them.[5][11]

`--system-prompt` wipes everything above, so you'd need to reconstruct output styles, project awareness, etc.:  
```powershell
claude --system-prompt "You are Claude Code... [full rebuilt prompt + your rules]"
```  
This breaks on Windows 11 for long prompts due to CLI limits.[12]

## Recommendation
Use `--append-system-prompt principles.md` for your behavioral rules—it's safer, more reliable on Windows 11/PowerShell, and positions principles optimally without side effects. Test: `claude --append-system-prompt "1. Never normalize a bug"` then flag duplicate progress bars; it must trace the root cause.[14][13]
