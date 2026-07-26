---
title: "On Windows Git Bash, git invokes hooks via shebang line — executable bit not required"
created: 2026-07-21
source: session-2026-07-21 (019f8507-6395-7bc0-87a9-9222e28d68c8)
sources:
  - P:/.git/hooks/pre-push (worked example)
tags: [windows, git-bash, hooks, shebang, ccr-ornith-false-positive, model-reliability]
host: windows
agent: grok
verification: empirical-with-reproduction
cognitive_load: 2
summary: >
  On Windows Git Bash, git invokes hooks via the shebang line, not by checking
  the executable bit. A hook file with mode `-a---` (no executable permission)
  is still invoked normally. The cross-model review tool ccr-ornith flagged
  this as a critical bug; the flag was a false positive caused by reading the
  Windows `Attributes` column as if it were Unix permission bits.
---

# On Windows Git Bash, git invokes hooks via shebang line — executable bit not required

## The misconception

A common automated review finding on Windows: "Hook file is NOT executable — git will never invoke it." The reasoning: the file has mode `-a---`, which in Unix terms means "archive bit only, no execute."

**This is wrong on Windows Git Bash.** Git uses the shebang line (e.g., `#!/usr/bin/env bash`) to determine the interpreter, then runs the script via that interpreter. The file's executable bit is irrelevant.

## How the false positive arose this session

`ccr-ornith` (a local free LLM, 9B parameter model on this host) reviewed the githook fix and produced this finding:

> **Hook file is NOT executable — git will never invoke it**
>
> Severity: Critical
>
> File permissions are `-a---` (read-only, NOT executable). Git hooks MUST be executable to be invoked.
>
> I verified this by running `git commit` with a new file — the hook did NOT fire (no trufflehog scan output, no regression test output). The commit succeeded silently without the security gate executing.

The "verification" was a `git commit`, which fires `pre-commit`, not `pre-push`. The pre-commit hook may or may not have fired (different hook script). The conclusion that the pre-push hook "will never be invoked" was not actually tested against `git push`.

## Empirical refutation

`git push origin <branch>` invokes the pre-push hook. Tested 2026-07-21:

```bash
$ git checkout -b test-pre-push
$ git commit --allow-empty -m "test"
$ git push -u origin test-pre-push
# → "WARNING: trufflehog at /c/Users/brsth/... doesn't support filesystem-scan mode."
# → "Secret scan SKIPPED — push will proceed."
# → ">>> [SMOKE] gate + atomic"
# → "75 passed, 1 warning in 0.71s"
# → "Pre-push: ALL PASSED"
# → "remote: ... main -> main"   ← push succeeded, hook had run
```

The hook fired and ran the full regression test suite. **Push proceeded normally with mode `-a---` on the hook file.**

## Why this misconception is so persistent

1. **On Unix (Linux/macOS), the executable bit IS required.** Git uses the OS `execve()` syscall which checks the bit. A `chmod -x` on a hook makes git skip it.
2. **The "Attributes" column in PowerShell's `Get-Item` Mode output looks like permission bits.** But it's not — it's Windows file attributes (Archive / Hidden / System / ReadOnly / Directory). A `-a---` reading means "Archive bit set, no other attributes" — not "no execute permission."
3. **Cross-model reviews can propagate the misconception.** A local small model (ccr-ornith) saw the `-a---` and applied Unix logic. The parent-model reviewer (minimax-m3) didn't flag it, suggesting it correctly identified this as Windows-specific.

## How to verify whether a hook is actually invoked

```bash
# Method 1: introduce a real change and see if the hook fires
git checkout -b test-hook
# modify a tracked file
git add .
git commit -m "test"
# Look for pre-commit hook output. If absent, pre-commit is broken.
git push origin test-hook
# Look for pre-push hook output. If absent, pre-push is broken.

# Method 2: run the hook directly
bash .git/hooks/pre-push origin <remote-url>
# Tests the script logic, but does NOT test whether git actually invokes it.

# Method 3: add a guaranteed-firing side effect
echo "echo PRE-PUSH-FIRED-$(date) >> /tmp/hook-test.log" >> .git/hooks/pre-push
git push
grep PRE-PUSH-FIRED /tmp/hook-test.log
```

## When the executable bit actually matters

- **On Linux/macOS:** Yes, the bit matters. `chmod +x .git/hooks/pre-push` is required.
- **On Windows native git (cmd.exe, PowerShell):** Bit does not matter; git uses file association / shebang.
- **On Windows Git Bash (this host):** Bit does not matter; git invokes via shebang + bash.

## When ccr-ornith's flag IS valid (and how to fix)

If a hook is genuinely not being invoked, the symptom is: the hook's output never appears in `git commit` / `git push` output, and any side-effects the hook should produce are absent. The fix is to check the hook script's logic (`bash <hook-path>` to run it directly) or the hook's registration (`git config --get core.hooksPath`).

The "fix chmod +x" advice is Unix-specific. On Windows Git Bash, it does nothing useful (the file is already invokable).

## Lesson: cross-model review needs empirical verification

The session that produced this finding was a cross-model review (parent model minimax-m3, local model ccr-ornith) — designed to catch errors the parent model might miss. In this case, **ccr-ornith produced a false positive critical bug** that the parent model correctly avoided. The empirical test (running `git push` and seeing the hook fire) caught it.

Implication: **cross-model lens coverage has value for diversity but not for correctness.** A wrong answer from a different model is still a wrong answer. Always verify cross-model findings with a concrete test, not just by their plausibility.

## Related

- `~/.grok/AGENTS.md` § "Self-review before shipping advice" — recommended verification pattern
- `[[auto-commit-authority-isolation]]` — adjacent concept on multi-agent safety
- The broader rule in AGENTS.md: "verify before done on any write" — applies here (the false positive was a missed verification)

## Auto-related

- [[are-there-repos-or-solutions-to-claude-code-gettin]]

