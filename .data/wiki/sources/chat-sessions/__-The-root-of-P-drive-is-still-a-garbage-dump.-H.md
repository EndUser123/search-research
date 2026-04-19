<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# "

❯ The root of P drive is still a garbage dump. How can we prevent it? How can we clean it up?

● Bash(cd "P:/" \&\& ls -la)
⎿  total 3013
drwxr-xr-x 1 brsth 197609       0 Jan 31 17:14 \$RECYCLE.BIN/
drwxr-xr-x 1 brsth 197609       0 Feb 26 07:34 ./
… +64 lines (ctrl+o to expand)

● I see the problem. The cleanup tool says "compliant" but there's obvious garbage:

Corrupted filenames (P: prefix):

- P:.claudehooksassumption_audit_v2.py
- P:.claudehooksuserpromptsubmitunified_injector.py
- P:.claudestatequality-stage3.json
- P:__csf.stagingsecurity_review_checkpoint.json

Test files scattered at root (should be in tests/):

- test_*.py (20+ files)
- test_*.md, test_*.txt, test_*.json

Random junk scripts:

- do_update.py, q_context_restore.py, update_memory.py
- redirect, listdisk.txt, temp_write_test.txt
- pytestdebug.log, serena_test_err.log

Weird directories:

- chat-friction-analysis-workspace/, claude/

The heuristics are missing:

1. Files with P: prefix (Windows path corruption)
2. Test files at root level
3. Orphaned scripts not in project structure
4. Log files at root

Want me to enhance the heuristic detection to catch these categories?

❯  Yes, but I also want to know how to prevent these problems from occurring. You would think that our hook system
should know, or at least recognize, what's obviously garbage.

● Good point. The hook system should block garbage as it's being created, not just clean it up later. Let me check what
validation already exists.

● Searched for 1 pattern, read 4 files (ctrl+o to expand)
⎿  Loaded .claude\\hooks\\CLAUDE.md

● Now I see the problem. The policy has blocked_root_patterns for __csf/ (lines 483-624) but the workspace_root (P:/)
section only blocks temp/ and logs/ directories.

Current policy gap:

- csf_nip_directory.blocked_root_patterns: ✅ Blocks test_*.py, *.log, *.py at __csf/ root
- workspace_root.blocked_root_patterns: ❌ Only blocks temp/ and logs/ directories at P:/ root

So test files at P:/test_foo.py are allowed, but at P:/__csf/test_foo.py they're blocked.

Also missing: Detection for Windows path corruption - files like P:.claudehooksassumption_audit_v2.py have P: embedded in
the filename from copy-paste errors.

Two-pronged solution:

1. Prevention (Hook): Add blocked_root_patterns to workspace_root section + add P: prefix corruption check
2. Cleanup (Detection): Enhance heuristics to match the policy"

How do other people handle this garbage situation? What do you recommend?

Others handle root directory clutter in development workspaces through preventive Git hooks (pre-commit and client-side), structured project layouts, and automated PowerShell cleanups on Windows. Claude Code users specifically extend your hook system with PreToolUse scripts to block unwanted file creations at the root.[^1_1][^1_2][^1_3][^1_4]

## Common Approaches

- **Git Hooks for Prevention**: Use pre-commit hooks to fail commits adding test files, logs, or prefixed junk to root; pairs with .gitignore for untracked files.[^1_2][^1_3][^1_5]
- **Config and Folder Organization**: Move tool configs/scripts to dedicated dirs like /config/, /scripts/, or /tests/, referencing them via symlinks or tool flags.[^1_6][^1_7]
- **Automated Cleanup Scripts**: PowerShell scans/deletes old temp/logs/test files by pattern/age; schedule via Task Scheduler.[^1_8][^1_9]
- **Tool-Specific Blocks**: Claude Code hooks (e.g., path_redirector.py style) reject Write tool calls to root matching patterns like "test_*.py" or "P:".[^1_10][^1_1]


## Enhance Your Hooks (Prevention)

Extend `.claude/hooks/CLAUDE.md` workspace_root.blocked_root_patterns with your gaps:

```
workspace_root.blocked_root_patterns:
  - "^test_.*\\.(py|md|txt|json)$"  # Root test files
  - "^P:.*"                       # Path corruption
  - "\\.(log|txt)$"               # Loose logs/txt (non-docs)
  - "^(do_update|q_context|update_memory)\\.py$"  # Orphan scripts
```

Add PreToolUse hook script checking `tool_input.path` against these (exit 2 to block, like protect-files.sh). This stops creation proactively, unlike post-facto cleanup.[^1_1]

## Quick Cleanup Script

Run this PowerShell in P:\ to nuke current garbage (backup first!):

```powershell
$root = "P:/"
$patterns = @("test_*.py", "test_*.md", "test_*.txt", "test_*.json", "*P:*.py", "*P:*.json", "*.log", "do_update.py", "q_context_restore.py", "update_memory.py", "redirect", "listdisk.txt", "temp_write_test.txt", "pytestdebug.log", "serena_test_err.log")
Get-ChildItem $root -File | Where-Object { $patterns | ForEach-Object { if ($_.Name -match $_) { $true } } } | Remove-Item -Force -WhatIf  # Remove -WhatIf to execute
Get-ChildItem $root -Directory | Where-Object { $_.Name -match "^(chat-friction-analysis-workspace|claude)$" } | Remove-Item -Recurse -Force -WhatIf
```

Adapts standard Windows cleaners for your patterns. Integrate into cron/Task Scheduler for recurrence.[^1_9]

## Recommendation

Prioritize **hook prevention** matching your identified gaps—it's zero-overhead and educates Claude Code sessions. Combine with pre-commit for Git hygiene and weekly PowerShell cleanup as fallback. Avoid broad tools like cleanmgr.exe; custom patterns fit your monorepo better. This keeps P:\ surgical for your multi-terminal Claude Code flows.[^1_11][^1_4]
<span style="display:none">[^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30][^1_31][^1_32]</span>

<div align="center">⁂</div>

[^1_1]: projects.tools.claude_code

[^1_2]: https://code.claude.com/docs/en/hooks-guide

[^1_3]: https://adamj.eu/tech/2024/01/24/pre-commit-fail-hook/

[^1_4]: https://www.exam-labs.com/blog/understanding-and-implementing-gitignore-for-cleaner-repositories

[^1_5]: https://paddo.dev/blog/claude-code-hooks-guardrails/

[^1_6]: https://github.com/orgs/community/discussions/165862

[^1_7]: https://www.reddit.com/r/webdev/comments/1m1eab8/how_do_i_avoid_the_config_clutter/

[^1_8]: https://dev.to/carl_max007/best-practices-for-organizing-cloned-github-projects-3l9e

[^1_9]: https://www.reddit.com/r/PowerShell/comments/mmbq9i/cleaning_up_windows_temp_files_and_folders_with/

[^1_10]: https://zecurit.com/script-hub/disk-space-cleanup-powershell-script/

[^1_11]: https://www.perplexity.ai/search/db385ab5-e245-4faf-8826-0d6e76cdd856

[^1_12]: work.dev_environment

[^1_13]: work.dev_environment_issue

[^1_14]: https://learn.microsoft.com/en-us/windows-server/storage/file-server/disk-cleanup

[^1_15]: https://stackoverflow.com/questions/45675673/reduce-file-clutter-in-git-repository

[^1_16]: https://github.com/nodejs/tooling/issues/79

[^1_17]: https://news.ycombinator.com/item?id=24066748

[^1_18]: https://wellarchitected.github.com/library/architecture/recommendations/scaling-git-repositories/large-git-repositories/

[^1_19]: https://www.youtube.com/watch?v=L0cJxwg9Mk0

[^1_20]: https://pre-commit.com

[^1_21]: https://gitprotect.io/blog/mastering-github-issues-best-practices-and-pro-tips/

[^1_22]: https://github.com/ChadSimmons/Scripts/blob/default/Windows/Clean-SystemDiskSpace.ps1

[^1_23]: https://stackoverflow.com/questions/28852786/automate-process-of-disk-cleanup-cleanmgr-exe-without-user-intervention

[^1_24]: https://www.mpca.solutions/wp/knowledgebase/topic/how-to-clean-up-system-volume-information-folder-on-windows/

[^1_25]: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cleanmgr

[^1_26]: https://www.reddit.com/r/git/comments/zkea68/is_there_any_flag_or_setting_that_would_prevent/

[^1_27]: https://prosystech.nl/powershell-clean-up-hard-drive-c/

[^1_28]: https://www.reddit.com/r/windows/comments/bueqr0/tutorial_how_to_run_disk_cleanup_so_itll_clean/

[^1_29]: https://www.youtube.com/watch?v=IAQjwlQtRB0

[^1_30]: https://www.youtube.com/watch?v=vJYzHTRh-pE

[^1_31]: https://www.hanselman.com/blog/guide-to-freeing-up-disk-space-under-windows-7

[^1_32]: https://stackoverflow.com/questions/17176286/prevent-git-committers-from-creating-certain-directories


---

# Are there any repos that deal with this situation? I don't want to use git hooks. I would prefer to use scripts and cloud code hooks.

Yes, several GitHub repos provide Claude Code hooks and PowerShell scripts for blocking root clutter or cleaning workspaces without Git hooks.[^2_1][^2_2]

## Key Repos for Hooks

- **kenryu42/claude-code-safety-net**: Plugin with PreToolUse hooks to catch/block destructive filesystem ops outside project dirs; extend for root patterns like "test_*.py" or "P:".[^2_1]
- **ertan/claude-rm-guard** (from Reddit): Python hook parses Bash commands, blocks rm/unlink if targeting root junk (e.g., via patterns); adaptable to Write tool for prevention.[^2_3]


## PowerShell Cleanup Scripts

- **gbuktenica/Clean-Local-Git-Folder**: Recursively scans paths (e.g., P:/), removes untracked Git junk/temp; run standalone or scheduled—no hooks needed.[^2_4]
- **deadlydog/PowerShell.GitClean**: Invoke-GitClean cmdlet cleans untracked files across repos; targets root clutter like logs/tests.[^2_5]


## Integration Steps

Drop hook examples into `.claude/hooks/` (e.g., block-write-root.py checking `tool_input.path.startswith('P:/') and re.match(r'test_|P:|.*\.log')` then `sys.exit(2)`).[^2_2][^2_6] Schedule PS scripts via Task Scheduler for daily root scans: `Get-ChildItem P:/ | Where { $_.Name -match 'test_|P:|^\w+\.(log|txt)$' } | Remove-Item`.[^2_7] This aligns with your Claude Code + PS workflow.
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://github.com/kenryu42/claude-code-safety-net

[^2_2]: https://code.claude.com/docs/en/hooks-guide

[^2_3]: https://www.reddit.com/r/ClaudeCode/comments/1pig5u0/i_made_a_hook_to_prevent_claude_code_from_ever/

[^2_4]: https://github.com/gbuktenica/Clean-Local-Git-Folder

[^2_5]: https://github.com/deadlydog/PowerShell.GitClean

[^2_6]: https://www.datacamp.com/tutorial/claude-code-hooks

[^2_7]: https://irohastack.com/en/safe-cleanup-garbage-files-en/

[^2_8]: https://github.com/anthropics/claude-code/issues/11226

[^2_9]: https://www.reddit.com/r/ClaudeAI/comments/1lzxl4u/method_for_protecting_files_from_being_edited_by/

[^2_10]: https://github.com/anthropics/claude-code/issues/16733

[^2_11]: https://github.com/anthropics/claude-code/issues/19471

[^2_12]: https://stackoverflow.com/questions/31620763/no-garbage-collection-while-powershell-pipeline-is-executing

[^2_13]: https://code.claude.com/docs/en/hooks

[^2_14]: https://dev.to/holasoymalva/the-ultimate-claude-code-guide-every-hidden-trick-hack-and-power-feature-you-need-to-know-2l45

[^2_15]: https://github.com/MicrosoftDocs/windows-dev-docs/blob/docs/hub/dev-drive/index.md


---

# Anything in those repos that would be interesting?

Yes—especially in `claude-code-safety-net`, there are patterns you can borrow directly for “no garbage at workspace root” with hooks and scripts.

## From claude-code-safety-net

Interesting ideas to reuse in your system:

- **PreToolUse as a hard gate**: They treat hooks as the first line of defense that always runs before permission rules, and they fail closed on anything they can’t confidently parse in strict mode. You can mirror this for any Claude Write/Bash targeting `P:/` with suspicious filenames (`test_*.py`, `*P:*.py`, `*.log` at root, etc.).
- **Semantic command analysis, not just patterns**: Safety Net inspects the full Bash command, normalizes it, and looks for dangerous combinations (e.g., `rm -r -f /`, `git reset --hard`) instead of just naive string matches. You could apply that idea to paths: normalize `tool_input.path` with `Path`, then classify “allowed zones” vs “forbidden root”.
- **Project‑scoped custom rules**: It loads `.safety-net.json` from the repo plus a user config and merges rules, with project rules winning. You could define a `P:/.claude/root-policy.json` describing:
    - allowed root files (README, LICENSE, env, etc.)
    - allowed root dirs (src, tests, __csf.nip, .claude)
    - deny rules for “P:-prefixed”, `test_*.py` at root, loose logs, orphan scripts
- **Silent fallback on config errors**: If custom rules are invalid, it falls back to built‑ins instead of breaking the workflow. For your CLAUDE.md + hooks, that’s a good pattern: if the root-policy file is corrupt, still enforce a minimal hardcoded “no garbage at root” set.
- **Diagnostics and “explain”**: They ship a `doctor` and `explain` mode that:
    - runs self‑tests and shows what’s blocked
    - traces why a command was allowed/blocked step‑by‑step
You could add a `/debug-root-policy` slash command that shows why `P:/test_foo.py` is rejected but `P:/tests/test_foo.py` is allowed.

Concretely, you can adapt their **custom rules** schema to a path‑policy schema, e.g.:

```jsonc
// P:/.claude/root-policy.json
{
  "version": 1,
  "allowedFiles": ["README.md", "LICENSE", ".env", ".gitignore"],
  "allowedDirs": ["src", "tests", "__csf.nip", ".claude"],
  "blockedPatterns": [
    "^test_.*\\.(py|md|txt|json)$",
    "^P:.*",
    ".*\\.(log|tmp)$",
    "^(do_update|q_context_restore|update_memory)\\.py$"
  ]
}
```

Then a PreToolUse hook for Write/Bash checks the target path against this policy and exits 2 if it would touch a disallowed root file.

## From Clean-Local-Git-Folder

This repo is less Claude‑specific, but has a couple of patterns worth stealing:

- **Recursive, parameterized cleanup**: The script walks a root directory and applies cleanup rules (prune branches) across all repos. You can reuse its structure to walk `P:/` and:
    - delete files matching your garbage patterns at root
    - optionally report what would be deleted (`-WhatIf` style)
- **Depth‑limited scanning**: It lets you control how deep to recurse (depth 1 vs 2). For P:, you can explicitly say “only depth 0 for aggressive deletion” and maybe depth 1–2 for just reporting, which avoids nuking things inside real projects.

A small PowerShell script modeled on that could implement:

```powershell
param(
  [string]$Root = "P:/",
  [switch]$WhatIf
)

$blockedPatterns = @(
  '^test_.*\.(py|md|txt|json)$',
  '^P:.*',
  '.*\.(log|tmp)$',
  '^(do_update|q_context_restore|update_memory)\.py$'
)

Get-ChildItem $Root -File | Where-Object {
  $name = $_.Name
  $blockedPatterns | Where-Object { $name -match $_ } | ForEach-Object { return $true }
  $false
} | ForEach-Object {
  if ($WhatIf) { Write-Host "Would remove $($_.FullName)" }
  else { Remove-Item $_.FullName -Force }
}
```

Run that on a schedule as your “sweeper,” while the Claude hooks enforce the **preventive** layer.

If you want, I can sketch a concrete `preToolUse` hook (Python) that reads `root-policy.json` and enforces it on `P:/` for all Write/Bash calls.
<span style="display:none">[^3_1][^3_2]</span>

<div align="center">⁂</div>

[^3_1]: projects.tools.claude_code

[^3_2]: work.dev_environment


---

# Yes, please.

Here’s a concrete, P:\-aware `PreToolUse` hook you can drop in today. It enforces a root policy file and blocks garbage *before* it’s created.[^4_1][^4_2]

***

## 1. Root policy file (P:/.claude/root-policy.json)

Put this near your existing hooks:

```jsonc
{
  "version": 1,
  "rootPath": "P:/",
  "allowedFiles": [
    "README.md",
    "LICENSE",
    ".env",
    ".gitignore",
    ".gitattributes"
  ],
  "allowedDirs": [
    ".git",
    ".claude",
    "__csf.nip",
    "src",
    "tests",
    "docs"
  ],
  "blockedPatterns": [
    "^test_.*\\.(py|md|txt|json)$",
    "^P:.*",
    ".*\\.(log|tmp)$",
    "^(do_update|q_context_restore|update_memory)\\.py$",
    "^(redirect|listdisk\\.txt|temp_write_test\\.txt)$",
    "^(pytestdebug|serena_test_err)\\.log$"
  ]
}
```

You can tune `allowedFiles`, `allowedDirs`, and `blockedPatterns` over time.

***

## 2. Hook wiring in settings.json

Configure a `PreToolUse` hook for `Write`, `Edit`, and `Bash`:

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/pretool_root_policy.py"
          }
        ]
      }
    ]
  }
}
```

This uses the documented `matcher` pattern for PreToolUse.[^4_3][^4_4]

***

## 3. pretool_root_policy.py

Save as `P:/.claude/hooks/pretool_root_policy.py` and make sure your settings.json path matches.

```python
#!/usr/bin/env python
import json
import re
import sys
from pathlib import Path

ROOT_POLICY_PATH = Path("P:/.claude/root-policy.json")

def load_policy():
    try:
        with ROOT_POLICY_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        # Hard‑coded minimal policy if file missing
        return {
            "rootPath": "P:/",
            "allowedFiles": ["README.md", "LICENSE", ".env", ".gitignore"],
            "allowedDirs": [".git", ".claude", "__csf.nip", "src", "tests", "docs"],
            "blockedPatterns": [
                r"^test_.*\.(py|md|txt|json)$",
                r"^P:.*",
                r".*\.(log|tmp)$"
            ],
        }
    except Exception:
        # If policy is corrupt, fail closed but with minimal safe rules
        return {
            "rootPath": "P:/",
            "allowedFiles": [],
            "allowedDirs": [".git", ".claude", "__csf.nip"],
            "blockedPatterns": [
                r".*"  # block everything at root until policy fixed
            ],
        }

    # Normalization
    root = data.get("rootPath", "P:/")
    if not root.endswith(("/", "\\")):
        root = root + "/"
    data["rootPath"] = root

    data["allowedFiles"] = data.get("allowedFiles", [])
    data["allowedDirs"] = data.get("allowedDirs", [])
    data["blockedPatterns"] = data.get("blockedPatterns", [])

    # Pre‑compile regexes
    data["_blockedRegex"] = [re.compile(p) for p in data["blockedPatterns"]]
    return data


def extract_paths(tool_name, tool_input):
    """
    Return a list of candidate paths from tool_input based on tool_name.
    """
    paths = []

    # Write/Edit tools typically use "path"
    if tool_name in ("Write", "Edit"):
        p = tool_input.get("path") or tool_input.get("file_path")
        if isinstance(p, str) and p.strip():
            paths.append(p)

    # Bash: very conservative heuristic (you can expand later)
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        # crude grep for P:/ or P:\\ paths
        tokens = cmd.replace(";", " ").replace("&&", " ").split()
        for t in tokens:
            if "P:/" in t or "P:\\" in t:
                # strip quotes
                t = t.strip("\"'")
                paths.append(t)

    return paths


def classify_path(raw_path: str, policy: dict):
    """
    Return (is_root, is_blocked, reason) for a given raw path string.
    """
    root = policy["rootPath"]
    try:
        p = Path(raw_path)
    except Exception:
        # If it's clearly corrupted with 'P:' prefix inside name, treat as root junk
        if "P:" in raw_path:
            return True, True, f"Path appears corrupted (contains 'P:' in filename): {raw_path}"
        return False, False, ""

    # Normalize to posix style for matching
    # We treat any path whose parent is the root as a "root file"
    # and any top-level directory as "root dir".
    try:
        full = p
        # If path is absolute under P:, fine; if relative, interpret relative to root
        if not p.is_absolute():
            full = Path(root) / p

        # Check if it's under the policy root at all
        try:
            rel = full.relative_to(root)
        except ValueError:
            # Not under root we care about
            return False, False, ""

        parts = rel.parts
        if not parts:
            # directly the root itself
            return False, False, ""

        name = parts[^4_0]
        # root‑level file: no subdirs
        is_root_file = (len(parts) == 1)
        is_root_dir = (len(parts) == 1 and not "." in name)

    except Exception:
        return False, False, ""

    if not (is_root_file or is_root_dir):
        return False, False, ""

    # Allowed root dirs/files
    if is_root_dir and name in policy["allowedDirs"]:
        return True, False, ""
    if is_root_file and name in policy["allowedFiles"]:
        return True, False, ""

    if is_root_file:
        # Apply blockedPatterns to the file name
        for rx in policy["_blockedRegex"]:
            if rx.match(name):
                return True, True, f"Root file '{name}' is blocked by root-policy pattern '{rx.pattern}'."
        # Default: disallow unknown files at root
        return True, True, f"Creating arbitrary files at workspace root is blocked by root-policy (file: '{name}')."

    if is_root_dir:
        # Unknown root dir: allow for now (you can flip this)
        return True, False, ""

    return False, False, ""


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        # If hook can't parse input, don't block anything
        sys.stderr.write(f"[root-policy] Failed to parse hook input: {e}\n")
        sys.exit(0)

    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input", {}) or {}

    if tool_name not in ("Write", "Edit", "Bash"):
        sys.exit(0)

    policy = load_policy()
    paths = extract_paths(tool_name, tool_input)

    blocked_reasons = []
    for raw in paths:
        is_root, is_blocked, reason = classify_path(raw, policy)
        if is_blocked:
            blocked_reasons.append((raw, reason))

    if not blocked_reasons:
        # Let tool proceed
        sys.exit(0)

    # Build a single explanation for Claude
    messages = []
    for raw, reason in blocked_reasons:
        messages.append(f"- {reason} (path: {raw})")
    reason_text = (
        "Root-policy hook blocked this operation because it would create or modify "
        "garbage at the workspace root (P:/).\n"
        "Summary:\n" + "\n".join(messages) +
        "\n\nPlease move tests under tests/, logs under logs/ or __csf.nip/, and avoid "
        "P:-prefixed filenames at root."
    )

    # PreToolUse: use hookSpecificOutput + exit 2 to block and inform Claude.[web:50][web:43]
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason_text
        }
    }
    json.dump(output, sys.stdout)
    sys.stdout.flush()
    # Exit 2 -> block the tool call, feed reason back to Claude.[web:17][web:43][web:60]
    sys.exit(2)


if __name__ == "__main__":
    main()
```

This follows the current Claude Code hook contract for `PreToolUse` (reads JSON from stdin, writes `hookSpecificOutput`, exits 2 to block).[^4_2][^4_5][^4_1]

***

## 4. How this behaves

- Any **Write/Edit** to `P:/test_foo.py`, `P:/pytestdebug.log`, `P:/P:.claudehooks...` is blocked with a clear explanation and suggestions for better locations.
- **Bash** commands containing explicit `P:/something` paths are inspected; if they resolve to bad root files, they are blocked as well.
- If `root-policy.json` is missing, you still get a conservative built‑in policy; if it’s corrupt, the hook fails closed at root until you fix it.

If you paste back your actual `CLAUDE.md` blocked_root_patterns, I can align the Python logic exactly with those rules so the hook and policy are 1:1.
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_15][^4_6][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://code.claude.com/docs/en/hooks

[^4_2]: https://code.claude.com/docs/en/hooks-guide

[^4_3]: https://stevekinney.com/courses/ai-development/claude-code-hook-examples

[^4_4]: https://dev.to/mikelane/building-guardrails-for-ai-coding-assistants-a-pretooluse-hook-system-for-claude-code-ilj

[^4_5]: https://claudefa.st/blog/tools/hooks/hooks-guide

[^4_6]: https://www.reddit.com/r/ClaudeCode/comments/1nc5oe8/claude_code_hooks_not_blocking_tool_execution_on/

[^4_7]: https://github.com/disler/claude-code-hooks-mastery

[^4_8]: https://app.cro-ro.org.br/blog/stop-hook-exit-code-2

[^4_9]: https://www.datacamp.com/tutorial/claude-code-hooks

[^4_10]: https://www.reddit.com/r/ClaudeAI/comments/1n1o29s/python_bash_for_writing_claude_code_hooks_with_4/

[^4_11]: https://www.reddit.com/r/ClaudeAI/comments/1m56ku2/typescript_hooks_to_make_claude_code_understand/

[^4_12]: https://github.com/decider/claude-hooks

[^4_13]: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

[^4_14]: https://stevekinney.com/courses/ai-development/claude-code-hook-control-flow

[^4_15]: https://dev.classmethod.jp/articles/shuntaka-claude-code-hooks-interactive-cli-recursive-fixes/

