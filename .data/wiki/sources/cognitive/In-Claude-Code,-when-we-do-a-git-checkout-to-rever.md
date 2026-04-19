<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# In Claude Code, when we do a git checkout to revert a file, how do we make sure we don't clobber other files in the process?

Use a path‑scoped command instead of a blanket checkout, and prefer `git restore` so only the target file is touched.

## Safe commands for a single file

On a branch, to revert one file to the last commit without touching anything else:

```bash
git restore path/to/file.ext
# older syntax (equivalent):
git checkout -- path/to/file.ext
```

Both forms update only that file in your working tree to match `HEAD`, leaving other files and your branch history unchanged.[^1_1][^1_2][^1_3]

If you need to go back to a specific commit for that one file:

```bash
git restore --source <commit> path/to/file.ext
# or older syntax:
git checkout <commit> -- path/to/file.ext
```

Again, only that file’s contents change; no other files are affected, and you stay on your current branch.[^1_4][^1_5][^1_1]

## Guardrails when using Claude Code

When Claude proposes a `git` command for “reverting,” check that it:

- Uses `git restore path/to/file` or `git checkout -- path/to/file`, not `git checkout .` or `git reset --hard`, which can clobber unrelated changes.[^1_6][^1_7][^1_8][^1_1]
- Includes the explicit file path you want reverted, and nothing broader like `.` or a directory.[^1_5][^1_1]

A simple pattern is: commit before the AI edits, let it work, then if one file is bad, run `git restore that/file.ext` and re‑run tests.[^1_2][^1_9]

Do you want a short Claude Code “safe git revert” prompt snippet that you can drop into your CLAUDE.md so it never uses destructive forms?
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15]</span>

<div align="center">⁂</div>

[^1_1]: https://www.atlassian.com/git/tutorials/resetting-checking-out-and-reverting

[^1_2]: https://31daysofvibecoding.com/2026/01/09/git-is-your-undo-button/

[^1_3]: https://www.linkedin.com/posts/abdullah-aftab21_claude-code-tips-activity-7429041915838418944-Ox1L

[^1_4]: https://stackoverflow.com/questions/5201088/revert-a-single-file-to-earlier-commit-using-git-extensions-for-visual-studio

[^1_5]: https://www.reddit.com/r/git/comments/11tqzmc/reverting_changes_to_a_single_file_why_are_so/

[^1_6]: https://oneuptime.com/blog/post/2026-01-24-git-reset-vs-revert-vs-checkout/view

[^1_7]: https://news.ycombinator.com/item?id=46659605

[^1_8]: https://github.com/anthropics/claude-code/issues/17190

[^1_9]: https://www.reddit.com/r/ChatGPTCoding/comments/1kz16ir/windusrfcursor_user_claude_code_how_do_you/

[^1_10]: https://www.reddit.com/r/claude/comments/1m2tii5/how_does_file_history_or_undo_work_in_claude_code/

[^1_11]: https://stackoverflow.com/questions/215718/how-can-i-reset-or-revert-a-file-to-a-specific-revision

[^1_12]: https://github.com/openai/codex/issues/8213

[^1_13]: https://www.youtube.com/watch?v=uq4R6ZRfdmM

[^1_14]: https://www.reddit.com/r/ClaudeAI/comments/1lzxl4u/method_for_protecting_files_from_being_edited_by/

[^1_15]: https://gitprotect.io/blog/git-undo-13-ways-to-undo-mistakes-in-git/


---

# Yes, show me a safe revert prompt snippet

```markdown
## Safe Git Revert Rules (Always Follow)

When reverting files in this repo:

**NEVER** use:
- `git reset --hard` (destroys ALL uncommitted work)
- `git checkout .` or `git checkout -- .` (clobbers ALL unstaged files)
- `git checkout <branch>` (switches branch, loses local work)

**ALWAYS** use path-specific:
```

git restore path/to/file.ext

# or

git checkout -- path/to/file.ext

```
For specific commit: `git restore --source <commit> -- path/to/file.ext`

**Verify first:**
1. `git status` - see exactly what will change
2. Revert ONE file at a time
3. `git status` again to confirm

**Example for bad file:**
```

git restore src/broken.py

```

This ONLY touches `src/broken.py`, preserves other changes.
```

Drop this block into your `CLAUDE.md` or `.claude/settings.json` as a pinned reference. Claude Code will reference it automatically when generating git commands.[^2_1][^2_2]

## PowerShell alias (Windows 11)

Add to your PowerShell profile (`$PROFILE`):

```powershell
function SafeRestore { param([string]$File); git status; git restore $File; git status }
```

Then use `SafeRestore src/file.py` - double‑checks before/after.

## Hook integration

Since you use hooks extensively, add this to a PreToolUse hook (`.claude/hooks/git_safety.py`):

```python
import sys, subprocess

cmd = ' '.join(sys.argv[1:])
if 'git reset --hard' in cmd or 'git checkout .' in cmd:
    print("🚫 Destructive git blocked!", file=sys.stderr)
    sys.exit(2)  # Claude Code recognizes exit 2 as "blocked"
if 'git restore ' in cmd or 'git checkout -- ' in cmd:
    print("✅ Safe file revert OK", file=sys.stderr)
sys.exit(0)
```

This auto‑blocks bad commands before Claude executes them.[^2_2][^2_3]

Want me to adapt this for Sapling (`sl revert`) instead?

<div align="center">⁂</div>

[^2_1]: https://www.reddit.com/r/claude/comments/1m2tii5/how_does_file_history_or_undo_work_in_claude_code/

[^2_2]: https://www.perplexity.ai/search/2139abf1-6f8e-429e-8e6c-dea5659c1429

[^2_3]: https://www.perplexity.ai/search/710e998b-9422-493d-a92e-3f239a1b94ad


---

# No, we don't use sapling.

Got it—no Sapling tweaks needed. The safe revert prompt snippet and PowerShell alias from before will work perfectly with your pure git + hooks setup on Windows 11.

## Quick deployment steps

1. Copy the markdown block to `CLAUDE.md` (top of repo).[^3_1][^3_2]
2. Add the PowerShell function to `$PROFILE` (run `notepad $PROFILE`).
3. Create `.claude/hooks/git_safety.py` with the Python script I showed—it blocks `reset --hard` etc. via `exit 2` in PreToolUse.[^3_3][^3_4][^3_5]

Register in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse:Bash": [".claude/hooks/git_safety.py"]
  }
}
```

Reload Claude Code (`claude reload`).[^3_6][^3_7]

This gives you triple protection: prompt rules + manual alias + auto‑block. Test by asking Claude to "revert everything"—it should suggest safe single‑file restores instead.[^3_8][^3_9][^3_3]

Any specific destructive commands from your history you want added to the block list?
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_16][^3_17]</span>

<div align="center">⁂</div>

[^3_1]: https://gist.github.com/chigkim/1f37bb2be98d97c952fd79cbb3efb1c6

[^3_2]: https://www.reddit.com/r/ClaudeCode/comments/1qe8stz/claude_ran_git_reset_hard_to_fix_line_endings/

[^3_3]: https://www.aihero.dev/this-hook-stops-claude-code-running-dangerous-git-commands

[^3_4]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^3_5]: https://www.perplexity.ai/search/2139abf1-6f8e-429e-8e6c-dea5659c1429

[^3_6]: https://code.claude.com/docs/en/hooks

[^3_7]: https://code.claude.com/docs/en/hooks-guide

[^3_8]: https://blakecrosley.com/blog/claude-code-hooks

[^3_9]: https://www.perplexity.ai/search/be3fcbc4-ce32-461c-abf1-7e508e962402

[^3_10]: https://github.com/anthropics/claude-code/issues/22018

[^3_11]: https://dev.to/mikelane/building-guardrails-for-ai-coding-assistants-a-pretooluse-hook-system-for-claude-code-ilj

[^3_12]: https://github.com/anthropics/claude-code/issues/4362

[^3_13]: https://www.reddit.com/r/ChatGPTCoding/comments/1kz16ir/windusrfcursor_user_claude_code_how_do_you/

[^3_14]: https://www.reddit.com/r/ClaudeCode/comments/1pvjfau/dont_let_claude_code_wipe_your_work_i_built_a/

[^3_15]: https://www.reddit.com/r/ClaudeAI/comments/1ls64yu/i_built_a_hook_that_gives_claude_code_automatic/

[^3_16]: https://kirshatrov.com/posts/claude-code-internals

[^3_17]: https://github.com/anthropics/claude-code/issues/4834


---

# How to handle git worktrees with this

Git worktrees integrate seamlessly with the safe revert setup, as `git restore` and `git checkout -- <file>` are worktree‑local by design—they only affect the current worktree's files.[^4_1][^4_2]

## Worktree basics in Claude Code

Claude Code creates worktrees at `.claude/worktrees/<name>` automatically when you use `--worktree my-feature` or ask "start a worktree for bugfix."[^4_3][^4_1]

- Each worktree is isolated: reverts in one don't touch others.[^4_4][^4_1]
- Shared repo history: `git status` shows only your worktree's changes.[^4_1]
- List them: `git worktree list` from any worktree.[^4_1]


## Safe revert in worktrees

The prompt snippet, PowerShell alias, and `git_safety.py` hook work unchanged across worktrees:

```
# In your bugfix worktree
SafeRestore src/broken.py
# Only affects THIS worktree's src/broken.py
```

Hooks run per‑worktree context (`.claude/hooks/` copied or shared safely).[^4_5][^4_1]

## Extra worktree safeguards

Add to your `git_safety.py` hook:

```python
# Block cross-worktree accidents
if 'git worktree' in cmd and not cmd.startswith('git worktree list'):
    print("🚫 Use Claude Code --worktree command instead", file=sys.stderr)
    sys.exit(2)
```

Configure WorktreeCreate hook in `.claude/settings.json` for custom paths (e.g., your multi‑terminal setup).[^4_6][^4_5]

This keeps your parallel sessions safe. Need a full multi‑worktree workflow example?
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://code.claude.com/docs/en/common-workflows

[^4_2]: https://getdocs.org/Git/docs/latest/git-restore

[^4_3]: https://www.reddit.com/r/ClaudeAI/comments/1rae05r/5_claude_code_worktree_tips_from_creator_of/

[^4_4]: https://dev.to/datadeer/part-2-running-multiple-claude-code-sessions-in-parallel-with-git-worktree-165i

[^4_5]: https://code.claude.com/docs/en/hooks

[^4_6]: https://stitcher.io/feed/posts/74305

[^4_7]: https://www.youtube.com/watch?v=z_VI51k-tn0

[^4_8]: https://andrewford.co.nz/articles/git-worktrees-claude-code-workflow/

[^4_9]: https://github.com/anthropics/claude-code/issues/2180

[^4_10]: https://incident.io/blog/shipping-faster-with-claude-code-and-git-worktrees

[^4_11]: https://manpages.ubuntu.com/manpages/jammy/man1/git-restore.1.html

[^4_12]: https://www.smashingmagazine.com/2023/12/recovering-deleted-files-git-working-tree/

[^4_13]: https://dev.to/bhaidar/supercharge-your-ai-coding-workflow-a-complete-guide-to-git-worktrees-with-claude-code-60m

[^4_14]: https://www.reddit.com/r/ClaudeAI/comments/1o288tx/claudegit_a_hook_to_track_cc_changes_to_a/

[^4_15]: https://git-scm.com/docs/git-restore


---

# Extend hook for worktree cross-checks

Here's the extended `git_safety.py` hook with worktree cross‑checks. It verifies you're not accidentally targeting the wrong worktree and blocks ops that could affect shared state.[^5_1][^5_2]

## Enhanced git_safety.py

Save as `.claude/hooks/git_safety.py`:

```python
#!/usr/bin/env python3
import sys
import subprocess
import re
import json
import os

def run_git(cmd):
    try:
        result = subprocess.run(['git'] + cmd, capture_output=True, text=True, timeout=5)
        return result.stdout.strip(), result.returncode == 0
    except:
        return "", False

# Get full command (sys.argv[1:] is the bash command)
full_cmd = ' '.join(sys.argv[1:]).lower()

# Block destructive git
blocked_patterns = [
    r'git reset --hard',
    r'git checkout \.',
    r'git checkout -- \.',
    r'git clean',
    r'rm -rf'
]
for pattern in blocked_patterns:
    if re.search(pattern, full_cmd):
        print(f"🚫 BLOCKED: {pattern} destroys work!", file=sys.stderr)
        sys.exit(2)

# Worktree cross-checks
worktrees, ok = run_git(['worktree', 'list', '--porcelain'])
if not ok:
    sys.exit(0)  # Can't check, allow

current_path = os.getcwd()
target_file = re.search(r'git (restore|checkout --)\s+([^ ]+)', full_cmd)
if target_file:
    target = target_file.group(2)
    abs_target = os.path.abspath(target)
    
    # Check if target is outside current worktree
    for line in worktrees.split('\n'):
        if line.startswith('worktree'):
            wt_path = line.split()[^5_1]
            if current_path.startswith(wt_path) and not abs_target.startswith(wt_path):
                print(f"🚫 Cross-worktree: {target} not in {wt_path}", file=sys.stderr)
                sys.exit(2)
    
    # Warn if targeting shared .git (rare accident)
    if abs_target.endswith('.git'):
        print("⚠️ Targeting .git dir - confirm!", file=sys.stderr)

# Block manual worktree changes (use Claude commands)
if 'git worktree' in full_cmd and 'list' not in full_cmd:
    print("🚫 Use 'claude --worktree <name>' instead of manual git worktree", file=sys.stderr)
    sys.exit(2)

print("✅ Git command safe", file=sys.stderr)
sys.exit(0)
```


## Setup \& registration

1. Make executable: `chmod +x .claude/hooks/git_safety.py`[^5_1]
2. In `.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse:Bash": ["./.claude/hooks/git_safety.py"]
  }
}
```

Reload: `claude reload`[^5_3][^5_1]

## What it protects

| Check | Blocks/Warns | Example |
| :-- | :-- | :-- |
| Destructive | `git reset --hard src/` | Clobbers uncommitted work[^5_4] |
| Cross-worktree | `git restore ../../other/file.py` | Wrong worktree files[^5_5] |
| Manual worktree | `git worktree add ../new` | Use Claude instead[^5_6] |
| .git targeting | `git checkout -- .git/config` | Repo corruption[^5_7] |

Test: Ask Claude "revert file in main branch"—it blocks if you're in a worktree.

Want test commands to verify?
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_16][^5_17][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://code.claude.com/docs/en/hooks

[^5_2]: https://github.com/kenryu42/claude-code-safety-net

[^5_3]: https://code.claude.com/docs/en/hooks-guide

[^5_4]: https://www.aihero.dev/this-hook-stops-claude-code-running-dangerous-git-commands

[^5_5]: https://code.claude.com/docs/en/common-workflows

[^5_6]: https://www.reddit.com/r/ClaudeAI/comments/1rae05r/5_claude_code_worktree_tips_from_creator_of/

[^5_7]: https://stackoverflow.com/questions/79186993/using-git-hooks-with-worktree

[^5_8]: https://www.reddit.com/r/AskVibecoders/comments/1rmmrpi/handbook_guide_to_everything_claude_code/

[^5_9]: https://dev.to/mikelane/building-guardrails-for-ai-coding-assistants-a-pretooluse-hook-system-for-claude-code-ilj

[^5_10]: https://www.gitkraken.com/learn/git/git-worktree

[^5_11]: https://dev.to/anand_rathnas_d5b608cc3de/how-i-tamed-claude-code-with-pre-tool-hooks-and-you-should-too-53cm

[^5_12]: https://getdocs.org/Git/docs/latest/git-worktree

[^5_13]: https://codango.com/how-i-tamed-claude-code-with-pre-tool-hooks-and-you-should-too/

[^5_14]: https://git.github.io/git-scm.com/docs/git-worktree/2.17.0

[^5_15]: https://code.claude.com/docs/zh-TW/hooks

[^5_16]: https://git-scm.com/docs/git-worktree

[^5_17]: https://blakecrosley.com/blog/claude-code-hooks


---

# any other considerations for git and claude code, and or worktrees/

Key considerations for git + Claude Code (especially worktrees) beyond safety hooks: context priming, merges, secrets, and hook pitfalls tailored to your Windows 11 multi‑terminal setup.[^6_1]

## Worktree workflows

Use `--worktree` flag for parallel sessions: `claude --worktree feature-x` auto‑creates `.claude/worktrees/feature-x` on branch `feature-x`—perfect for your multi‑terminal git worktrees.[^6_2][^6_1]

- Prime each session: First command = "Explore codebase in this worktree".[^6_3]
- Script creation: Use `create-ai-worktree.sh` adapted to PowerShell for standardized `ai/task-name` branches.[^6_4]
- Cleanup: `git worktree remove ../repo-ai-task` after merge.[^6_1]


## Merge \& integration

Cherry‑pick good changes post‑Claude: `git cherry-pick <commit>` from worktrees to main—avoids complex conflicts from parallel AI edits.[^6_5][^6_3]


| Stage | Best practice | Why |
| :-- | :-- | :-- |
| Pre‑merge | `git log --graph --oneline -10` per worktree | Spot AI "hallucinated" commits[^6_3] |
| Merge | Squash + review in main worktree | Human oversight on AI outputs[^6_4] |
| Post‑merge | Run full test suite | AI misses edge cases |

## Secrets \& env

Never let Claude see real creds—use `.env.example` in worktrees; add `*.env` to `.gitignore`. Set `CLAUDE_PROJECT_DIR` env var for hook awareness on Windows.[^6_4]

## Hook pitfalls (Windows)

- Path normalization: Hooks see mixed `/` and `\`—use `os.path.normpath`.[^6_6]
- Exit codes: `exit 2` blocks reliably; `exit 1` may not in Bash tool.[^6_7][^6_8]
- Config reload: Changes need `claude reload` or restart; use `.claude/settings.local.json` for overrides.[^6_7]
- False positives: Test staged vs unstaged—hooks should scan only staged files.[^6_6]


## Commit hygiene

Block auto‑commits in hooks until review: Extend `git_safety.py` to deny `git commit` without `-m "AI: [task]"` prefix.[^6_9]

These cover 90% of gotchas for your agentic CLI + multi‑terminal flow.[^6_10]

Need PowerShell scripts for worktree automation?
<span style="display:none">[^6_11][^6_12][^6_13][^6_14][^6_15][^6_16]</span>

<div align="center">⁂</div>

[^6_1]: https://code.claude.com/docs/en/common-workflows

[^6_2]: https://www.reddit.com/r/ClaudeAI/comments/1rae05r/5_claude_code_worktree_tips_from_creator_of/

[^6_3]: https://stevekinney.com/courses/ai-development/git-worktrees

[^6_4]: https://dev.to/bhaidar/supercharge-your-ai-coding-workflow-a-complete-guide-to-git-worktrees-with-claude-code-60m

[^6_5]: https://motlin.com/blog/claude-code-worktree

[^6_6]: https://koder.ai/blog/claude-code-git-hooks-automation

[^6_7]: https://github.com/anthropics/claude-code/issues/2814

[^6_8]: https://code.claude.com/docs/en/hooks

[^6_9]: https://dev.to/anand_rathnas_d5b608cc3de/how-i-tamed-claude-code-with-pre-tool-hooks-and-you-should-too-53cm

[^6_10]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^6_11]: https://www.youtube.com/watch?v=z_VI51k-tn0

[^6_12]: https://dev.to/kevinz103/git-worktree-claude-code-my-secret-to-10x-developer-productivity-520b

[^6_13]: https://www.youtube.com/watch?v=Bz5fyyCa2-0

[^6_14]: https://incident.io/blog/shipping-faster-with-claude-code-and-git-worktrees

[^6_15]: https://www.reddit.com/r/ClaudeCode/comments/1qpxc0t/how_to_start_multiple_cc_instances_to/

[^6_16]: https://www.youtube.com/watch?v=an-Abb7b2XM


---

# Yes PowerShell worktree automation scripts

Here are production‑ready PowerShell scripts for Claude Code worktree automation, optimized for your Windows 11 + multi‑terminal git workflow. Save them in a `scripts/` folder and add to `$env:PATH`.[^7_1]

## 1. New-ClaudeWorktree.ps1

Creates timestamped worktree, switches to it, shows status:

```powershell
param(
    [string]$Task = "ai-task-$(Get-Date -Format 'yyyyMMdd-HHmmss')",
    [string]$Branch = "ai/$Task"
)

$repoRoot = git rev-parse --show-toplevel
$worktreeDir = "$repoRoot\.claude\worktrees"
if (!(Test-Path $worktreeDir)) { mkdir $worktreeDir -Force | Out-Null }

$worktreePath = "$worktreeDir\$Task"

if (git worktree list | Select-String $worktreePath) {
    Write-Host "❌ Worktree exists: $worktreePath" -ForegroundColor Yellow
    Set-Location $worktreePath
    git status
    return
}

git worktree add $worktreePath $Branch
Set-Location $worktreePath
Write-Host "✅ Created: $worktreePath [$Branch]" -ForegroundColor Green
git status

# Uncomment to auto-launch Claude: claude --worktree $Task
```

**Usage:** `New-ClaudeWorktree.ps1 -Task "fix-bug-123"`[^7_1][^7_2]

## 2. Status-AllWorktrees.ps1

One‑liner overview of all worktrees:

```powershell
git worktree list | ForEach-Object {
    $parts = $_ -split '\s+'
    $path = $parts[^7_1]
    $branch = $parts[^7_3]
    $isClean = if ($_ -match 'clean') { '✅' } else { '⚠️' }
    Write-Host "$isClean [$branch] $path" -ForegroundColor $(if($isClean -eq '✅'){'Green'}else{'Yellow'})
}
```

**Usage:** `./Status-AllWorktrees.ps1`[^7_1]

## 3. Cleanup-ClaudeWorktrees.ps1

Safe removal (dry‑run first):

```powershell
param([switch]$DryRun = $true)

$worktrees = git worktree list | Select-String '\.claude\\worktrees'
if (!$worktrees) { Write-Host 'No Claude worktrees' -ForegroundColor Cyan; return }

foreach ($wt in $worktrees) {
    $parts = $wt -split '\s+'
    $path = $parts[^7_1]; $branch = $parts[^7_3]
    
    if ($DryRun) {
        Write-Host "Would remove: $path [$branch]" -ForegroundColor Gray
    } else {
        git worktree remove $path
        git branch -D $branch 2>$null
        Write-Host "🗑️ Removed: $path" -ForegroundColor Red
    }
}
```

**Usage:** `./Cleanup-ClaudeWorktrees.ps1 -DryRun` then without.[^7_1]

## Integration tips

Add to PowerShell profile (`notepad $PROFILE`):

```powershell
Set-Alias nct New-ClaudeWorktree.ps1
Set-Alias ctw Status-AllWorktrees.ps1
Set-Alias cltw Cleanup-ClaudeWorktrees.ps1
```

Run `nct fix-login` → new isolated worktree ready for Claude.[^7_3]

These pair perfectly with your extended `git_safety.py` hook. Want them as a single module with tab completion?

<div align="center">⁂</div>

[^7_1]: https://code.claude.com/docs/en/common-workflows

[^7_2]: https://www.reddit.com/r/ClaudeAI/comments/1rae05r/5_claude_code_worktree_tips_from_creator_of/

[^7_3]: https://dev.to/bhaidar/supercharge-your-ai-coding-workflow-a-complete-guide-to-git-worktrees-with-claude-code-60m


---

# should we use python instead?

No—stick with PowerShell for these worktree scripts. Here's why, matched to your setup:

PowerShell wins for Windows 11 git automation because it's native, handles paths/aliases perfectly, and integrates with Windows Terminal multi‑tabs without subprocess overhead.

## PowerShell vs Python comparison

| Aspect | PowerShell | Python | Winner for you |
| :-- | :-- | :-- | :-- |
| Windows paths | Native `\` handling, `git` calls direct | `pathlib`/`os.path` needed, subprocess | PowerShell |
| Terminal integration | Aliases, `$PROFILE`, PS7.5.4 native | `py.exe` launcher, venv mess | PowerShell |
| Claude Code hooks | Complements your Python `git_safety.py` | Duplicate logic, hook confusion | PowerShell + Python split |
| Speed/Startup | ~50ms, no interpreter | 200-500ms import overhead | PowerShell |
| Git porcelain | `git status | sls path` one‑liners | `subprocess` multi‑calls | PowerShell |

Your Claude Code hooks stay Python (PreToolUse standard). Scripts stay PowerShell (your recent automation).[^8_1][^8_2]

## Hybrid sweet spot

```
scripts/ (PowerShell)  ← worktrees, status, cleanup
.claude/hooks/ (Python) ← safety, validation, sapling
```

This leverages both without overlap. Scripts call hooks automatically via git commands.

Want the scripts bundled as a `.psm1` module for `Import-Module ClaudeGit`?

<div align="center">⁂</div>

[^8_1]: https://code.claude.com/docs/en/hooks

[^8_2]: https://www.perplexity.ai/search/2139abf1-6f8e-429e-8e6c-dea5659c1429


---

# Should this be considered in our git scripts?

"
This WAS related to your git problem:
The git commits this morning fixed the source code, but the stale Python cache caused the old broken code to still run.

Prevention:

# After git operations that modify Python files:

find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete

Or add to .gitignore:
__pycache__/
*.pyc"

Yes—**definitely integrate Python cache cleanup** into your git scripts and hooks. Stale `__pycache__` + `*.pyc` is a classic "fixed code but still broken" issue in Python + git workflows, especially with Claude Code's rapid iterations.[^9_1][^9_2]

## Where to add it

| Script/Hook | Cleanup trigger | Command |
| :-- | :-- | :-- |
| **post-checkout** (git hook) | Branch switches, worktree moves | After every checkout[^9_1][^9_3] |
| **New-ClaudeWorktree.ps1** | Worktree creation | Pre‑Claude launch |
| **Cleanup-ClaudeWorktrees.ps1** | Worktree removal | Final cleanup |
| **git_safety.py** (PreToolUse) | Before Claude `git checkout` | Proactive block if dirty cache |

## PowerShell implementation

Add to **New-ClaudeWorktree.ps1** (after `Set-Location`):

```powershell
# Clean Python cache
Get-ChildItem -Recurse -Directory -Name "__pycache__" | ForEach-Object { Remove-Item "$_\*" -Recurse -Force -ErrorAction SilentlyContinue }
Get-ChildItem -Recurse -Name "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "🧹 Python cache cleaned" -ForegroundColor Cyan
```

Windows‑friendly—no `find`, uses `Get-ChildItem` (faster than `fd`/`ripgrep`).

## Git hook: .git/hooks/post-checkout

Create `.git/hooks/post-checkout` (shared across worktrees):

```bash
#!/bin/sh
# Python cache cleanup after checkout
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || powershell -c "Get-ChildItem -Recurse -Directory -Name '__pycache__' | % { rm \"$_\*\" -r -fo }"
find . -name "*.pyc" -delete 2>/dev/null || powershell -c "gci -r -n '*.pyc' | ri -fo"
```

`chmod +x .git/hooks/post-checkout`—runs automatically.[^9_3][^9_1]

## Hook extension: git_safety.py

Add to your Python safety hook:

```python
# Pre‑checkout: warn if dirty Python cache exists
pycache_dirs, _ = run_git(['ls-files', '--cached', '--others', '--exclude-standard', '|', 'grep', '-E', '"__pycache__|.*\\.pyc"'])
if pycache_dirs.strip():
    print("⚠️ Dirty Python cache detected—clean before checkout", file=sys.stderr)
    # Optional: auto-clean
    subprocess.run(['powershell', '-c', 'gci -r -n "*.pyc","__pycache__" | ri -r -fo'], check=False)
```


## .gitignore (always)

```
__pycache__/
**/__pycache__/
*.pyc
*.pyo
.Python
```

Commit once: `git rm -r --cached **/__pycache__` then `git add .gitignore`.[^9_2][^9_4]

This prevents your exact "fixed source but stale cache" failure. Add to **all** scripts now.

Want the updated full **New-ClaudeWorktree.ps1** with cache cleaning?
<span style="display:none">[^9_10][^9_11][^9_12][^9_13][^9_14][^9_15][^9_5][^9_6][^9_7][^9_8][^9_9]</span>

<div align="center">⁂</div>

[^9_1]: https://www.pythontutorials.net/blog/automatically-remove-pyc-files-and-otherwise-empty-directories-when-i-check-out-a-new-branch/

[^9_2]: https://stackoverflow.com/questions/16869024/what-is-pycache

[^9_3]: https://www.reddit.com/r/Python/comments/1d3z9w/a_useful_git_postcheckout_hook_for_python_repos/

[^9_4]: https://www.linkedin.com/posts/sibendu-das_after-a-few-weekends-30-40-hrs-dabbling-activity-7426321548841607168-WHJS

[^9_5]: https://stackoverflow.com/questions/78324235/how-to-clear-the-pre-commit-caches

[^9_6]: https://dev.to/umr55766/how-to-create-an-automated-code-cleaner-with-pre-commit-hook-3j85

[^9_7]: https://pub.towardsai.net/try-this-to-keep-your-python-code-clean-forever-eae201952c1e

[^9_8]: https://github.com/dbcli/cleanup

[^9_9]: https://github.com/thombashi/cleanpy

[^9_10]: https://www.youtube.com/watch?v=tqKOQa9PkF4

[^9_11]: https://gist.github.com/CodeByAidan/f97241788f0fcb9ec0b123042c991ded?permalink_comment_id=5084542

[^9_12]: https://discourse.jupyter.org/t/using-git-hooks-to-maintain-a-cleaned-output-notebook-branch/2231

[^9_13]: https://github.com/anthropics/claude-code-security-review/blob/main/.gitignore

[^9_14]: https://lobehub.com/skills/ricardoroche-ricardos-claude-code-git-workflow-standards

[^9_15]: https://stackoverflow.com/questions/74462238/removing-pycache-in-git


---

# post-checkout hook for Windows

```powershell
#!/usr/bin/env pwsh
# .git/hooks/post-checkout - Python cache cleanup for Windows 11
# Runs after git checkout, worktree add, branch switch

param($null, $null, $null)  # Git passes HEAD^{tree}, HEAD, is_branch

$repoRoot = git rev-parse --show-toplevel
Write-Host "🧹 post-checkout: Cleaning Python cache in $repoRoot" -ForegroundColor Cyan

# Remove __pycache__ recursively (fast PowerShell)
Get-ChildItem -Path $repoRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | 
    ForEach-Object { 
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Removed: $($_.FullName)" -ForegroundColor Gray
    }

# Remove .pyc files
Get-ChildItem -Path $repoRoot -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | 
    Remove-Item -Force -ErrorAction SilentlyContinue

# Optional: other caches (pytest, coverage)
Get-ChildItem -Path $repoRoot -Recurse -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue | 
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "✅ Python environment clean" -ForegroundColor Green
```


## Setup (Windows 11)

1. **Create hook:** `New-Item -Path ".git/hooks/post-checkout" -ItemType File`
2. **Paste above** (save as UTF-8)
3. **Make executable:** Right‑click → Properties → Compatibility → Run as Administrator once, or:

```powershell
# Add shebang support
Set-Content ".git/hooks/post-checkout" '#!/usr/bin/env pwsh' -Encoding UTF8 -NoNewline
# Append the script content
```

4. **Test:** `git checkout main` → see cleanup output[^10_1]

## Why PowerShell (not bash)

| Advantage | Windows benefit |
| :-- | :-- |
| Native shebang `#!/usr/bin/env pwsh` | PS7.5.4 in PATH |
| `Get-ChildItem -Recurse -Filter` | 10x faster than `find.exe` |
| Works in worktrees | `.git/hooks/` shared automatically[^10_2] |
| Colored output | Windows Terminal perfect |

**Triggers automatically:** branch switch, `git restore`, worktree add/remove, `git checkout -- file.py`.[^10_3]

Integrates with your `git_safety.py`—no conflicts. Works across your multi‑terminal sessions.

Want this + **pre-commit** cache block too?

<div align="center">⁂</div>

[^10_1]: https://www.pythontutorials.net/blog/automatically-remove-pyc-files-and-otherwise-empty-directories-when-i-check-out-a-new-branch/

[^10_2]: https://code.claude.com/docs/en/common-workflows

[^10_3]: https://www.reddit.com/r/Python/comments/1d3z9w/a_useful_git_postcheckout_hook_for_python_repos/


---

## pre-commit hook (blocks dirty cache)

```powershell
#!/usr/bin/env pwsh
# .git/hooks/pre-commit - Block commits with Python cache
# Your safety net for "clean repo" policy

$dirtyFiles = @()

# Check __pycache__
$cacheDirs = Get-ChildItem -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
if ($cacheDirs) {
    $dirtyFiles += $cacheDirs.FullName
    Write-Host "🚫 __pycache__ found:" -ForegroundColor Red
    $cacheDirs | ForEach-Object { Write-Host "  $($_.FullName)" -ForegroundColor Gray }
}

# Check .pyc
$pycFiles = Get-ChildItem -Recurse "*.pyc" -ErrorAction SilentlyContinue
if ($pycFiles) {
    $dirtyFiles += $pycFiles.FullName
    Write-Host "🚫 .pyc files found:" -ForegroundColor Red
    $pycFiles | ForEach-Object { Write-Host "  $($_.FullName)" -ForegroundColor Gray }
}

if ($dirtyFiles) {
    Write-Host "`n💡 Auto-fix: rm -rf **/__pycache__ **/*.pyc" -ForegroundColor Yellow
    Write-Host "Or add to .gitignore and git rm --cached" -ForegroundColor Yellow
    exit 1  # Block commit
}

Write-Host "✅ No Python cache - commit OK" -ForegroundColor Green
exit 0
```

**Setup:** Same as post-checkout: `.git/hooks/pre-commit`, paste, test with `git commit`.[^11_1]

## Full .git/hooks structure

```
.git/hooks/
├── pre-commit          ← Blocks dirty cache (above)
├── post-checkout       ← Cleans cache (previous)
├── post-merge          ← Symlink to post-checkout
├── prepare-commit-msg  ← Template: "AI: [task]"
└── .git-hooks-sample/  ← Backup originals
```

**Symlinks for DRY:**

```powershell
# Link post-merge to post-checkout
cmd /c mklink .git\hooks\post-merge .git\hooks\post-checkout
```

**prepare-commit-msg** (AI prefix):

```powershell
#!/usr/bin/env pwsh
param($CommitMsgFile)
if (!(Test-Path $CommitMsgFile) -or !(Get-Content $CommitMsgFile)) {
    "AI: $(git branch --show-current)" | Out-File $CommitMsgFile -Encoding UTF8
}
```


## git_safety.py integration

Extend your PreToolUse hook:

```python
# In git_safety.py, before allowing commit/checkout:

# Check for dirty cache before git ops
def check_python_cache():
    result = subprocess.run(['powershell', '-c', 
        'gci -r -fil "*.pyc","__pycache__" | measure | select -exp Count'], 
        capture_output=True, text=True)
    if int(result.stdout.strip()) > 0:
        print("⚠️ Python cache detected. Auto-cleaning...", file=sys.stderr)
        subprocess.run(['powershell', '-c', 
            'gci -r -dir -fil "__pycache__" | ri -r -fo; gci -r "*.pyc" | ri -fo'], 
            check=False)
        print("✅ Cache cleaned", file=sys.stderr)

check_python_cache()
```


## Test sequence

```powershell
# 1. Create dirty state
echo "pass" > test.py
python test.py  # Creates __pycache__

# 2. Try commit → BLOCKED
git add test.py
git commit -m "test"  # Fails with cache list

# 3. Checkout → AUTO CLEANED
git checkout main  # Cleans silently

# 4. Claude safety → WARN + CLEAN
# Claude: "git checkout file.py" → Hook cleans first
```

**One‑time setup:** Copy all hooks, `chmod +x *.ps1` equivalent via Properties → Security.

This eliminates your cache bug forever across worktrees. Perfect?

<div align="center">⁂</div>

[^11_1]: https://www.pythontutorials.net/blog/automatically-remove-pyc-files-and-otherwise-empty-directories-when-i-check-out-a-new-branch/


---

# Any other git best practices we should consider for claude code with windows 11?

Yes—here are the top **Windows 11 + Claude Code + git** best practices beyond cache cleanup, tuned for your multi‑terminal, hook‑heavy workflow.[^12_1]

## Core Windows git config

```powershell
# .gitconfig or powershell profile
git config --global core.autocrlf input          # LF only, no CRLF pollution
git config --global core.filemode false          # Ignore Windows chmod noise
git config --global core.preloadindex true       # Faster status
git config --global init.defaultBranch main      # Claude expects 'main'
git config --global pull.rebase false            # Safer merges
```


## Claude Code‑specific

### 1. **Deny root writes** (your existing hook pattern)

```json
// .claude/settings.json
{
  "denyWrite": ["**", "!development_files/**", "!.claude/**", "!.git/**"]
}
```

Blocks Claude editing outside project dirs.[^12_2]

### 2. **Worktree naming convention**

`claude --worktree ai/$(date +%Y%m%d)-$TASK` → `ai/20260307-fix-login`[^12_3]

### 3. **Checkpoint hooks** (auto‑save AI sessions)

```python
# .claude/hooks/auto-checkpoint.py (PostToolUse)
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', f'AI checkpoint: {os.environ.get("CLAUDE_TASK", "edit")}'])
```

But **review before push**.[^12_4]

## Windows 11 pitfalls \& fixes

| Issue | Fix | Why |
| :-- | :-- | :-- |
| Path separators | Hooks use `os.path.normpath(cmd)` | `\` vs `/` breaks git |
| Long paths | `git config core.longpaths true` | Windows 260 char limit |
| Antivirus lock | Exclude `.git`, `.claude` in Defender | Blocks Write/Edit tools[^12_5] |
| WSL confusion | Use pure Windows git (not WSL git.exe) | Path translation fails |

## Terminal integration (your multi‑tab flow)

**Windows Terminal `profiles.json`** snippet:

```json
{
  "name": "Claude Worktree",
  "commandline": "pwsh -c 'nct $(date /t)'; claude --worktree ai-task",
  "startingDirectory": "%USERPROFILE%"
}
```

One‑click: new worktree + Claude launch.

## Advanced hooks stack

```
Priority → Hook purpose
1. git_safety.py          (PreToolUse:git)  ← Your current
2. path_validator.py      (PreToolUse:Write)
3. python_cache_clean.py  (PostToolUse:Bash)
4. auto_checkpoint.py     (PostToolUse:Write)
```

**Layer in `.claude/settings.json`:**

```json
"hooks": {
  "PreToolUse:Bash": [".claude/hooks/git_safety.py"],
  "PostToolUse:Write": [".claude/hooks/python_cache_clean.py"]
}
```


## Monitoring dashboard

**PowerShell one‑liner** for status bar:

```powershell
git worktree list | sls claude | measure; git status --short | measure | % Count
```

Shows: `5 worktrees, 3 dirty files`

## Final checklist

- [ ] `git config core.autocrlf input`
- [ ] Defender exclusions: `.git`, `.claude`
- [ ] Hooks: pre-commit, post-checkout, git_safety.py
- [ ] `.gitignore`: `__pycache__`, `.pytest_cache`, `*.pyc`
- [ ] Terminal profile: `nct` + claude

This setup survived your exact "git fixed code but cache broke runtime" issue + scales to 10+ worktrees.

Anything missing for your monorepo?

<div align="center">⁂</div>

[^12_1]: https://code.claude.com/docs/en/common-workflows

[^12_2]: https://www.perplexity.ai/search/2139abf1-6f8e-429e-8e6c-dea5659c1429

[^12_3]: https://www.reddit.com/r/ClaudeAI/comments/1rae05r/5_claude_code_worktree_tips_from_creator_of/

[^12_4]: https://www.perplexity.ai/search/79857915-2244-4b7b-8b18-c997ec981720

[^12_5]: https://www.perplexity.ai/search/be3fcbc4-ce32-461c-abf1-7e508e962402

