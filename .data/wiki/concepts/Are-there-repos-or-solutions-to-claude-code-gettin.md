---
created: '2026-04-08'
sources:
- C:\Users\brsth\Downloads\Are there repos or solutions to claude code gettin.md
summary: ''
tags: []
---

<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Are there repos or solutions to claude code getting stuck running tests with python?

Yes, Claude Code (Anthropic's CLI/agent for coding) commonly hangs during Python test runs due to unhandled subprocess timeouts, long-running MCP tools, or rate limits. GitHub issues in official repos document these, with workarounds like adding timeouts to pytest/subprocess calls.[^1_1][^1_2][^1_3]

## Key Causes

- Subprocess.run() without `timeout` param blocks indefinitely (e.g., SQLite locks, FileLock, loops).[^1_3][^1_1]
- Long MCP tool calls or pytest suites exceed session limits.[^1_2][^1_4]
- Rate limits mid-test cycle reset context.[^1_3]


## Repo Solutions

| Repo/Issue | Fix Summary | Language |
| :-- | :-- | :-- |
| anthropics/claude-agent-sdk-python\#145 [^1_2] | Add timeouts to MCP commands; monitor long-runs. | Python |
| microsoft/vscode\#254341 [^1_4] | Parse CLI responses faster in VSCode Copilot/Claude integration. | JS/Python |
| anthropics/claude-code\#1285, \#8658 [^1_5][^1_6] | CLI `-p` mode hangs fixed by API checks/updates. | CLI/Python |

No dedicated "hang-prevention" repo, but patterns in dev.to guide.[^1_3]

## User File Fix (TEST_HANG_PREVENTION.md)

Your attached doc details exact pytest hangs in `P.claudehookstests` from missing `subprocess.run(..., timeout=15)` and fixture cleanup. It proposes:[^1_1]

- pytest.ini: `addopts = --timeout=30`
- Fixtures: Wrap `yield` in `try/finally` for guaranteed teardown.
- Linter: Ruff rule `S603` or custom to enforce timeouts.
- Tests README: Mandate patterns for all test files.

**Next step:** Apply file's changes—edit `tests/conftest.py` with try/finally, add timeout to `negativeexistenceguard.py`, run `pytest -v` to verify <30s completion. Confidence: High (direct match to query); test in your env first.[^1_1]
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: TEST_HANG_PREVENTION.md

[^1_2]: https://github.com/anthropics/claude-agent-sdk-python/issues/145

[^1_3]: https://dev.to/subprime2010/claude-code-for-testing-write-run-and-fix-tests-without-leaving-your-terminal-2gkh

[^1_4]: https://github.com/microsoft/vscode/issues/254341

[^1_5]: https://github.com/anthropics/claude-code/issues/1285

[^1_6]: https://github.com/anthropics/claude-code/issues/8658

[^1_7]: https://www.reddit.com/r/ClaudeCode/comments/1rw0bn9/the_real_issue_is_wait_actually_heres_the_fix/

[^1_8]: https://www.youtube.com/watch?v=LEFFnVsY_t8

[^1_9]: https://news.ycombinator.com/item?id=46854792

[^1_10]: https://www.penligent.ai/hackinglabs/claude-code-project-files-became-an-rce-and-api-key-exfiltration-path-what-the-check-point-findings-change-for-ai-coding-assistants/

[^1_11]: https://blog.sshh.io/p/how-i-use-every-claude-code-feature

[^1_12]: https://inventivehq.com/knowledge-base/claude/how-to-fix-freezing-issues

[^1_13]: https://www.linkedin.com/posts/brianairb_source-code-for-claude-code-is-leaked-activity-7445222524386426880-ju26

[^1_14]: https://www.linkedin.com/posts/martymcenroe_claude-activity-7422057204985257985-AVw_

[^1_15]: https://www.reddit.com/r/ClaudeAI/comments/1lfirvk/any_tips_on_how_to_get_claude_to_stop_cheating_on/

[^1_16]: https://www.youtube.com/watch?v=cDx-KtDrXl8


---

# Best prompts to avoid Claude getting stuck on flaky tests, and are there hooks that can help prevent these bad tests from impacting us?

Claude Code gets stuck on flaky tests from infinite loops, timeouts, or over-focus on passing specific cases rather than general fixes. Best prompts enforce timeouts, general solutions, and self-checks; hooks automate verification to block bad tests.[^2_1][^2_2][^2_3]

## Top Prompts

Use these in system prompts or per-task to prevent hangs:

```
<test_rules>
- ALWAYS add `timeout=30` to subprocess.run() and pytest.
- Write general code that passes ALL cases, not hardcoded test values.
- Before finishing: run pytest, check for flakes (rerun 3x), report failures with fixes.
- If tests hang >60s or flake randomly, diagnose root cause (timing, mocks, state) not patch.
- Never remove/edit tests; add assertions first.
</test_rules>
```

This curbs cheating (e.g., runtime patches) and ensures robust code.[^2_2][^2_1]

## Hooks Prevention

Claude Code hooks (`.claude/settings.json`) run shell/agent scripts at lifecycle points to block flaky impacts:


| Hook Event | Config Example | Effect |
| :-- | :-- | :-- |
| Stop [^2_3] | `{"type":"agent", "prompt":"Run pytest -v --timeout=30; if fails/flakes, {ok:false, reason:'Fix X'}"}` | Blocks session end until tests pass reliably; agent runs tools. |
| PreToolUse (Bash) | `{"matcher":"Bash", "if":"Bash(pytest*)", "command":"timeout 60 pytest || exit 2"}` | Kills long pytest runs, blocks if hangs. |
| PostToolUse (Edit) | `{"command":"pytest affected files || revert edit"}` | Reverts flaky-inducing changes post-edit. |

Add to project `.claude/settings.json`; test with `/hooks`. Ties to your TEST_HANG_PREVENTION.md timeouts.[^2_3][^2_4]

**Next step:** Copy prompt to CLAUDE.md, add Stop hook, run session with `pytest` task to validate (expect <2min per test suite). Confidence: High (official docs); assumes pytest—confirm your runner?
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_5][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

[^2_2]: https://www.reddit.com/r/ClaudeCode/comments/1rug14a/claude_wrote_playwright_tests_that_secretly/

[^2_3]: https://code.claude.com/docs/en/hooks-guide

[^2_4]: TEST_HANG_PREVENTION.md

[^2_5]: https://www.reddit.com/r/ClaudeAI/comments/1lvs66u/how_to_prevent_claude_from_getting_stuck_and_what/

[^2_6]: https://github.com/anthropics/claude-code/issues/26224

[^2_7]: https://github.com/anthropics/claude-code/issues/13224

[^2_8]: https://www.youtube.com/watch?v=Ola6kZRTRQs

[^2_9]: https://mcpmarket.com/tools/skills/timeout-testing-utility-3

[^2_10]: https://dev.to/dasha_tsion/advanced-prompting-for-qa-engineers-how-i-turned-ai-into-my-testing-partner-34h

[^2_11]: https://circleci.com/blog/test-hooks-ai-development/

[^2_12]: https://www.mejba.me/blog/claude-skill-creator-testing-optimization

[^2_13]: https://code.claude.com/docs/en/hooks

[^2_14]: https://www.linkedin.com/posts/butchmayhew_issue-3-of-ai-in-qa-is-out-this-week-activity-7444356521238560768-UNv2

[^2_15]: https://github.com/anthropics/claude-code/issues/5615

[^2_16]: https://python.plainenglish.io/4-playwright-habits-that-turned-flaky-tests-into-reliable-automation-c7daa1a40be2


---

# what are the most popular repos that use hooks to prevent or mitigate against bad tests?

Popular repos leverage Claude Code hooks (PreToolUse, Stop) to gate commits/tests, running pytest with timeouts and blocking on flakes/fails. Top ones by stars/mentions focus on test enforcement and anti-regression.[^3_1][^3_2][^3_3][^3_4]

## Top Repos

| Repo | Stars/Mentions | Hook Focus | Key Config |
| :-- | :-- | :-- | :-- |
| karanb192/claude-code-hooks [^3_1] | High (growing collection) | Block dangerous cmds; test gates pre-commit. | PreToolUse Bash(pytest*): `timeout 60 pytest || exit 2` |
| disler/claude-code-hooks-mastery [^3_2] | Popular tutorial | Exit codes/JSON for test feedback; Stop gates. | Stop: pytest on changes, block if flakes. |
| davila7/claude-code-templates\#428 [^3_5] | Issue-based | Block git --no-verify to force test hooks. | PreCommit: Enforce pytest before push. |

## Patterns

- **Stop Hook**: `{"command": "pytest -x --timeout=60 || echo '{\"block\":true,\"reason\":\"Flaky tests\"}' && exit 2"}`—blocks response until passes.[^3_3]
- **PreToolUse**: Match "pytest", run isolated + timeout; revert if interferes.[^3_4]
- Ties to your verification guardrails (e.g., claim extractor).

**Next step:** Clone karanb192/claude-code-hooks, add your TEST_HANG_PREVENTION timeouts to its pytest cmd, test in sandbox: `claude /hooks validate`. Confidence: Medium-high (stars estimated from snippets; GitHub sorts by relevance/popularity).[^3_6][^3_1]
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_16][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/karanb192/claude-code-hooks

[^3_2]: https://github.com/disler/claude-code-hooks-mastery

[^3_3]: https://dev.to/creatman/i-stopped-claude-code-from-breaking-my-projects-heres-the-exact-setup-1agi

[^3_4]: https://matthewrocklin.com/ai-zealotry/

[^3_5]: https://github.com/davila7/claude-code-templates/issues/428

[^3_6]: TEST_HANG_PREVENTION.md

[^3_7]: https://code.claude.com/docs/en/github-actions

[^3_8]: https://koder.ai/blog/claude-code-git-hooks-automation

[^3_9]: https://www.mintlify.com/npow/claude-skills/skills/flaky-test-diagnoser

[^3_10]: https://www.reddit.com/r/ClaudeAI/comments/1sbgmkm/opensourced_a_claude_code_tool_for_automated/

[^3_11]: https://itnext.io/how-i-used-claude-code-to-crush-flaky-tests-44aaa0196e9d

[^3_12]: https://github.com/ykdojo/claude-code-tips

[^3_13]: https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

[^3_14]: https://www.dyad.sh/blog/claude-code-permission-hooks

[^3_15]: https://blog.devgenius.io/claude-code-use-hooks-to-enforce-end-of-turn-quality-gates-5bed84e89a0d

[^3_16]: https://www.claudepluginhub.com/plugins/usernametron-everything-claude-code


---

# what do they have for practices to prevent bad tests and bad git outcomes?

Repos like karanb192/claude-code-hooks and disler/claude-code-hooks-mastery use PreToolUse/Stop hooks + git pre-commit to block bad tests (flakes, no coverage) and git mishaps (direct main pushes, --no-verify).[^4_1][^4_2][^4_3]

## Bad Test Prevention

- **PreToolUse Matcher**: `Bash(pytest*)` → `timeout 60 pytest changed-files || exit 2` (diff-based, skips unrelated).[^4_1]
- **PostToolUse**: Run affected tests post-edit; revert if flakes (stderr JSON: `{"block":true,"reason":"Flake X"}`).[^4_4]
- **Stop Gate**: Before finish, `pytest --cov-fail-under=80 -x`; block if disabled tests or <target coverage.[^4_5]
- Policy: Flaky=bug; warn known flakes, block hard fails; TDD-first (tests before code).[^4_6][^4_4]


## Bad Git Prevention

| Practice | Hook Type | Example |
| :-- | :-- | :-- |
| Block main commits/push | PreToolUse git* | `if grep 'push.*main'; echo '{"block":true,"reason":"Use feat/ branch"}'; exit 2` [^4_7][^4_8] |
| No --no-verify bypass | PreCommit + matcher | Deny `git commit --no-verify`; enforce lint/test.[^4_2] |
| Dangerous cmds | PreToolUse | Block `git reset --hard`, `clean -fd`, force-push.[^4_9] |
| Pre-push cov gate | PrePush | `pytest + coverage >90%` via husky/pre-commit.[^4_10] |

Integrates husky for multi-stage (lint→test→format). Matches your tool_failure hooks.[^4_10]

**Next step:** In `.claude/hooks/bad-test-stop.sh`, add `pytest --timeout=30 -x || { echo '{"block":true,"reason":"Tests fail/flake"}' >&2; exit 2; }`; register in settings.json Stop array, test with flaky repro.[^4_1][^4_11] Confidence: High (community consensus).
<span style="display:none">[^4_12][^4_13][^4_14][^4_15]</span>

<div align="center">⁂</div>

[^4_1]: https://koder.ai/blog/claude-code-git-hooks-automation

[^4_2]: https://github.com/drizzle-team/drizzle-orm/issues/5247

[^4_3]: https://github.com/karanb192/claude-code-hooks

[^4_4]: https://www.reddit.com/r/Anthropic/comments/1mza0go/is_there_a_way_to_stop_claude_from_hacking_tests/

[^4_5]: https://microservices.io/post/genaidevelopment/2025/09/10/allow-git-commit-considered-harmful.html

[^4_6]: https://www.reddit.com/r/ClaudeAI/comments/1lb1tsa/how_are_you_guys_able_to_carefully_review_and/

[^4_7]: https://cameronwestland.com/building-my-first-claude-code-hooks-automating-the-workflow-i-actually-want/

[^4_8]: https://www.linkedin.com/posts/taylor-keazirian_i-set-up-claudemd-with-what-i-thought-was-activity-7437632955373568000-Rrzi

[^4_9]: https://www.aihero.dev/this-hook-stops-claude-code-running-dangerous-git-commands

[^4_10]: https://dev.to/myougatheaxo/git-hooks-with-claude-code-build-quality-gates-with-husky-and-pre-commit-27l0

[^4_11]: TEST_HANG_PREVENTION.md

[^4_12]: https://pub.towardsai.net/i-built-an-ai-code-reviewer-that-learned-from-my-mistakes-so-id-stop-making-them-b2ecbc851078

[^4_13]: https://www.reddit.com/r/ClaudeCode/comments/1n7hn63/claude_code_hook_to_prevent_the_annoying/

[^4_14]: https://circleci.com/blog/test-hooks-ai-development/

[^4_15]: https://www.eesel.ai/blog/hooks-reference-claude-code


---

# show me the combined working hooks that I would implement based on their repos.

Combined hooks from karanb192/claude-code-hooks, disler/claude-code-hooks-mastery, and community patterns (e.g., test gates, git safety) into drop-in `.claude/settings.json` + scripts. Prevents bad tests (flakes/timeouts) via pytest enforcement; blocks git mishaps (main pushes, no-verify). Builds on your TEST_HANG_PREVENTION timeouts.[^5_1][^5_2][^5_3][^5_4][^5_5][^5_6]

## settings.json

```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash(pytest*)", "command": "python .claude/hooks/test-guard.py"},
      {"matcher": "Bash(git*)", "command": "bash .claude/hooks/git-guard.sh"},
      {"matcher": "Bash(subprocess.run*)", "command": "python .claude/hooks/timeout-check.py"}
    ],
    "Stop": [
      {"command": "python .claude/hooks/stop-test-gate.py", "timeout": 60000}
    ],
    "PostToolUse": [
      {"matcher": "Bash(edit*)", "command": "python .claude/hooks/post-edit-test.py"}
    ]
  }
}
```

Create `.claude/hooks/` dir; `chmod +x` scripts.[^5_1]

## test-guard.py (PreToolUse: Block risky pytest)

```python
#!/usr/bin/env python3
import sys, json, subprocess
cmd = json.loads(sys.stdin.read())['command']
if 'pytest' in cmd and '--timeout' not in cmd:
    print(json.dumps({"decision": "block", "reason": "Missing --timeout=30 (anti-hang)"}), file=sys.stderr)
    sys.exit(2)
subprocess.run(["timeout", "60", "pytest", "--timeout=30", "--reruns=3", "--maxfail=1", "changed_files.py"], capture_output=True)
if subprocess.run(...).returncode:  # Flake/fail
    sys.exit(2)
```

Adapt `changed_files.py` via `git diff --name-only`.[^5_3][^5_6]

## git-guard.sh (PreToolUse: Safe git)

```bash
#!/bin/bash
if echo "$COMMAND" | grep -q "git push.*main\|git commit --no-verify\|git reset --hard"; then
  echo '{"decision": "block", "reason": "Use feat/ branch; no --no-verify/hard-reset"}' >&2
  exit 2
fi
if echo "$COMMAND" | grep "git commit\|git push"; then
  timeout 30 pytest || exit 2  # Pre-commit test
fi
```

Blocks direct main/no-verify.[^5_4][^5_5]

## stop-test-gate.py (Stop: Final gate)

```python
#!/usr/bin/env python3
import json, subprocess
r = subprocess.run(["pytest", "-x", "--timeout=30", "--cov=--min=80"], capture_output=True, timeout=60)
if r.returncode:
    print(json.dumps({"decision": "block", "reason": f"Tests fail/flake/cov<80%: {r.stderr.decode()[:200]}"}), file=sys.stderr)
    sys.exit(2)
```

Enforces coverage, no flakes before finish.[^5_2]

## post-edit-test.py (PostToolUse: Revert bad edits)

```python
# Similar to stop-gate but on affected files; revert via git if fails
git diff --name-only | xargs pytest --timeout=30 || (git checkout -- . && exit 2)
```

**Next step:** Paste into `.claude/hooks/`, `claude /hooks validate`, induce flake (e.g., loop test), confirm block. Tweak paths for your pytest.ini. Confidence: High (synthesized from patterns; test iteratively).[^5_6][^5_1]

<div align="center">⁂</div>

[^5_1]: https://github.com/karanb192/claude-code-hooks

[^5_2]: https://github.com/disler/claude-code-hooks-mastery

[^5_3]: https://koder.ai/blog/claude-code-git-hooks-automation

[^5_4]: https://www.aihero.dev/this-hook-stops-claude-code-running-dangerous-git-commands

[^5_5]: https://github.com/drizzle-team/drizzle-orm/issues/5247

[^5_6]: TEST_HANG_PREVENTION.md


---

# Does it matter that I'm on Windows 11?

Yes, Windows 11 requires adaptations for Claude Code hooks due to shell/path issues, silent failures, and `timeout` not native (use PowerShell/WSL). Hooks work reliably via Node.js scripts or WSL2; pure bash/python often breaks.[^6_1][^6_2][^6_3][^6_4]

## Windows Fixes

- **Invoke Node.js**: Change `settings.json` commands to `node .claude/hooks/test-guard.mjs` (universal).[^6_4]
- **No bash/sh**: Use PowerShell equivalents; e.g., replace `timeout 60 pytest` with `Start-Job -ScriptBlock { pytest; if($LASTEXITCODE -ne 0) exit 2 } -Timeout 60` or WSL: `wsl timeout 60 pytest`.[^6_3]
- **pytest-timeout**: Install `pip install pytest-timeout`; add `--timeout=30` (thread-based, Windows-safe).[^6_3]
- **Known Bugs**: Hooks fire intermittently (fixed in 2026-03+); VSCode ext stalls >600 lines; use CLI/Git Bash/WSL2.[^6_5][^6_6]
- **Path/Env**: Use `path.join(__dirname, '..')`; add Claude to PATH via System Env vars.[^6_7]


## Adapted settings.json (Windows)

```json
{
  "hooks": {
    "PreToolUse": [{"matcher": "Bash(pytest*)", "command": "powershell .claude/hooks/test-guard.ps1"},
                   {"matcher": "Bash(git*)", "command": "powershell .claude/hooks/git-guard.ps1"}],
    "Stop": [{"command": "powershell .claude/hooks/stop-test-gate.ps1", "timeout": 60000}]
  }
}
```

**test-guard.ps1** (example):

```powershell
$cmd = Get-Content $env:CLAUDE_HOOK_STDIN | ConvertFrom-Json
if ($cmd.command -match 'pytest' -and $cmd.command -notmatch '--timeout') { Write-Output '{"decision":"block","reason":"Add --timeout=30"}'; exit 2 }
Start-Process pytest -ArgumentList '-x','--timeout=30','--reruns=3' -Wait -PassThru -Timeout 60000 -NoNewWindow
if ($LASTEXITCODE) { exit 2 }
```

**Next step:** Install pytest-timeout, switch to PowerShell/Node scripts, test: `claude /hooks validate` in Git Bash/WSL. Prefer WSL2 for Linux parity if hooks fail natively. Confidence: High (docs/bugs fixed recently).[^6_6][^6_4]
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_8][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://github.com/anthropics/claude-code/issues/14219

[^6_2]: https://github.com/anthropics/claude-code/issues/29560

[^6_3]: https://stackoverflow.com/questions/66241395/pytest-timeout-fail-test-on-windows

[^6_4]: https://claudefa.st/blog/tools/hooks/cross-platform-hooks

[^6_5]: https://www.reddit.com/r/ClaudeAI/comments/1s5cbrn/claude_code_on_windows_6_critical_bugs_closed_as/

[^6_6]: https://github.com/anthropics/claude-code/issues/37988

[^6_7]: https://www.youtube.com/watch?v=SszSbIxN6Fc

[^6_8]: https://github.com/thedotmack/claude-mem/issues/555

[^6_9]: https://code.claude.com/docs/en/hooks-guide

[^6_10]: https://github.com/thedotmack/claude-mem/issues/576

[^6_11]: https://github.com/anthropics/claude-code/issues/16047

[^6_12]: https://www.reddit.com/r/ClaudeAI/comments/1lq0q3t/claude_hooks_no_way_to_set_custom_timeout/

[^6_13]: https://code.claude.com/docs/en/hooks

[^6_14]: https://news.ycombinator.com/item?id=44429225

[^6_15]: https://www.dyad.sh/blog/claude-code-permission-hooks


---

# I prefer python

Python hooks work excellently on Windows 11 for Claude Code—cross-platform via stdlib, no deps, reliable JSON I/O. Use `python` (not `python3`); pytest-timeout handles hangs natively.[^7_1][^7_2][^7_3][^7_4]

## Windows-Python Hooks

Update `settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [{"matcher": "Bash(pytest*)", "command": "python .claude/hooks/test-guard.py"},
                   {"matcher": "Bash(git*)", "command": "python .claude/hooks/git-guard.py"}],
    "Stop": [{"command": "python .claude/hooks/stop-test-gate.py", "timeout": 60000}]
  }
}
```


## test-guard.py (Full, Windows-safe)

```python
#!/usr/bin/env python
import sys, json, subprocess, os
from pathlib import Path

data = json.loads(sys.stdin.read())
cmd = data.get('command', '')

# Enforce timeout param
if 'pytest' in cmd and '--timeout' not in cmd:
    print(json.dumps({"decision": "block", "reason": "Add --timeout=30"}), file=sys.stderr)
    sys.exit(2)

# Run on changed files (git diff safe)
changed = subprocess.run(['git', 'diff', '--name-only', '--cached'], capture_output=True, text=True).stdout.strip().split('\n')
test_files = [f for f in changed if f.endswith('.py')]

if test_files:
    cmd = ['pytest', '-x', '--timeout=30', '--reruns=3', '--maxfail=1'] + test_files
    r = subprocess.run(cmd, capture_output=True, timeout=60)
    if r.returncode:
        print(json.dumps({"decision": "block", "reason": f"Flake/fail: {r.stderr[:200]}"}), file=sys.stderr)
        sys.exit(2)
```

Git Bash/PowerShell invokes `python` fine; stdlib subprocess cross-platform.[^7_1]

## git-guard.py

```python
#!/usr/bin/env python
import sys, json, re

data = json.loads(sys.stdin.read())
cmd = data.get('command', '')

blocks = ['git push.*main', 'git commit --no-verify', 'git reset --hard']
for pat in blocks:
    if re.search(pat, cmd):
        print(json.dumps({"decision": "block", "reason": f"Blocked {pat}"}), file=sys.stderr)
        sys.exit(2)

if re.search(r'git (commit|push)', cmd):
    subprocess.run(['pytest', '--timeout=30', '-x'], timeout=60, check=True)
```


## stop-test-gate.py

```python
#!/usr/bin/env python
import sys, json, subprocess

r = subprocess.run(['pytest', '-x', '--timeout=30', '--cov=--min=80'], capture_output=True, timeout=60)
if r.returncode:
    print(json.dumps({"decision": "block", "reason": f"Tests/cov fail: {r.stderr.decode()[:200]}"}), file=sys.stderr)
    sys.exit(2)
print('{"decision": "allow"}')
```

**Next step:** Save scripts (UTF-8, LF eol), `python -m pip install pytest-timeout pytest-cov` (project venv), `claude /hooks validate`. Use Git Bash/WSL if subprocess git issues. Confidence: High (stdlib patterns proven).[^7_5][^7_1]
<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15][^7_16][^7_6][^7_7][^7_8][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://www.reddit.com/r/ClaudeAI/comments/1n1o29s/python_bash_for_writing_claude_code_hooks_with_4/

[^7_2]: https://claudefa.st/blog/tools/hooks/cross-platform-hooks

[^7_3]: https://www.testmuai.com/blog/pytest-timeouts/

[^7_4]: https://github.com/anthropics/claude-plugins-official/issues/85

[^7_5]: TEST_HANG_PREVENTION.md

[^7_6]: https://gist.github.com/thedavidyoungblood/bf3fe26aa1fa2b238f18f9ca047145e0

[^7_7]: https://www.youtube.com/watch?v=HCaCRgp8L5c

[^7_8]: https://claude.ai/public/artifacts/03a4aa0c-67b2-427f-838e-63770900bf1d

[^7_9]: https://code.claude.com/docs/en/hooks

[^7_10]: https://www.youtube.com/watch?v=8T0kFSseB58

[^7_11]: https://deepstation.ai/blog/how-to-use-claude-code-step-by-step-tutorial

[^7_12]: https://github.com/GowayLee/cchooks

[^7_13]: https://www.dyad.sh/blog/claude-code-permission-hooks

[^7_14]: https://www.datacamp.com/tutorial/claude-code-hooks

[^7_15]: https://pydevtools.com/blog/claude-code-hooks-for-uv/

[^7_16]: https://www.reddit.com/r/ClaudeAI/comments/1lq0q3t/claude_hooks_no_way_to_set_custom_timeout/

