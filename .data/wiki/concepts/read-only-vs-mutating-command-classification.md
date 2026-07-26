---
title: "Read-only vs mutating command classification — three solutions for the exec-gate friction problem"
created: 2026-07-22
source: session-2026-07-22 (via /www)
agent: grok
tags: [exec-gate, permissions, command-classification, bash-classify, grok-native, design]
summary: >
  Three solutions to the "PreToolUse matcher can't distinguish read-only from mutating
  bash commands" problem: (1) AST-based classification via bash-classify (tree-sitter
  parser + YAML database), (2) command-prefix allowlist (simple, catches 90%), (3)
  Grok's native permission system (already exists, already classifies, we ignored it).
  The third solution is the right answer for this host.
cognitive_load: 2
---

## Summary

The exec-gate plugin's matcher-based approach (`search_replace|write|run_terminal_command|
spawn_subagent`) over-blocks because `run_terminal_command` covers both `ls` and `rm -rf`.
Three solutions exist; the third (Grok native) is the one we should use.

## Solution 1: AST-based classification (bash-classify)

[fprochazka/bash-classify](https://github.com/fprochazka/bash-classify) parses bash
expressions via tree-sitter into an AST and classifies each command against a YAML
database. Five levels: `READONLY`, `LOCAL_EFFECTS`, `EXTERNAL_EFFECTS`, `DANGEROUS`,
`UNKNOWN`.

**How it solves the problem:** classification happens on parsed structure, not regex
against prose. `git reset --hard` → DANGEROUS via option override. `git status` →
READONLY via subcommand match. `rm -rf /tmp` → DANGEROUS but `rm -rf /tmp/*` is
READONLY via temp-path exception.

**Goodhart resistance:** strong. The classifier reads actual command structure. It
can't be gamed by rephrasing — the AST is the AST.

**Limitations:**
- No variable resolution (`$DIR`, `$(cmd)` → UNKNOWN — conservative)
- Doesn't analyze awk/sed/perl embedded scripts
- Requires tree-sitter-bash Python dependency
- Ship-with database covers git, kubectl, find, xargs, sudo, env, sh — extensible
  via YAML for other commands

**Fit for exec-gate:** the hook would call `echo "$CMD" | bash-classify` and check
the `classification` field. If `READONLY`, allow. Otherwise check `/exec` flag. This
works but adds a Python dependency and parsing latency (~50ms per call).

Source: [github.com/fprochazka/bash-classify](https://github.com/fprochazka/bash-classify/blob/master/SPEC.md)

## Solution 2: Command-prefix allowlist (OpenCode's pattern)

OpenCode maintains a safe command-prefix allowlist: `git status*`, `ls*`, `cat*`,
`grep*`. Grok already has the same concept in `22-permissions-and-safety.md` L42-68.

**How it solves the problem:** most commands' mutation status is determined by the
first 1-2 tokens. Prefix matching catches 90% of cases with 10% of the complexity.

**Goodhart resistance:** weak. A prefix allowlist doesn't catch option-driven
mutations (`git push --force` is prefix-allowed by `git push*` if you allowlist that).
But Grok's native [dangerous commands list](https://docs.x.ai/build/features/permissions-and-safety)
(`rm`, `git push`, `chmod`, `chown`, `pkill`, `kill`, `killall`) prompts regardless
of any allowlist.

**Limitations:** misses option-driven edge cases. Requires maintaining the allowlist
manually.

**Fit for exec-gate:** hook could parse `toolInput.command` for first 1-2 tokens and
check against allowlist. Simple, fast, but duplicates work Grok already does.

Source: [opencode.ai/docs/permissions](https://opencode.ai/docs/permissions/),
local `~/.grok/docs/user-guide/22-permissions-and-safety.md` L42-68.

## Solution 3: Grok's native permission system (the right answer for this host)

Grok already has the entire read-only/mutating classifier built in:

- **Read-only tools auto-approved:** `read_file`, `list_dir`, `grep`, `web_search`,
  `todo_write` (per `22-permissions-and-safety.md` L42-44)
- **Read-only shell commands auto-approved:** `ls`, `cat`, `pwd`, `date`, `whoami`,
  `ps`, `head`, `tail`, `wc`, `sort`, `uniq`, `tr`, `cut`; `git status`, `git branch`,
  `git log`, `git diff`, `git ls-files`, `git show`, `git rev-parse`; `grep`, `rg`;
  `cargo check`; `kubectl get/logs/describe` (per L48-68)
- **Dangerous commands always prompt:** `rm`, `chmod`, `chown`, `chgrp`, `chattr`,
  `pkill`, `kill`, `killall`, `git push` (per L259-262)
- **`defaultMode: dontAsk`** in `~/.grok/config.toml` denies everything without an
  explicit `allow` rule
- **`ask` rules** for per-call approval on specific patterns
- **`allow` rules** for narrow authorization (e.g., `Bash(git commit*)` for the
  implementation wave)

**How it solves the problem:** the classifier already exists, is already tested, and
already handles the edge cases (dangerous command list catches `rm -rf` even when
the prefix would allow it; read-only command list catches `ls` even in `dontAsk` mode).

**Goodhart resistance:** strong. Grok's classifier is built into the binary; the
model cannot influence it via prompt content.

**Fit for exec-gate:** don't use a hook at all. Use:
1. `defaultMode: dontAsk` for the structural default (everything denied without allow rule)
2. `allow` rules for the specific mutating commands you want pre-authorized
3. User toggles plan mode (Shift+Tab) for dialogue-only turns
4. For the "release for N minutes" UX, operator can flip mode via `/always-approve`
   for the implementation wave, then back to `default` for dialogue

**Limitations:** no session-scoped TTL (authorization is sticky until manually
revoked). No automatic re-lock. But neither of these is actually needed if the
operator uses plan mode as the dialogue-mode gate — plan mode is already one-keypress.

Source: `~/.grok/docs/user-guide/22-permissions-and-safety.md`,
`~/.grok/docs/user-guide/19-plan-mode.md`.

## Why we missed Solution 3 the first time

The original session (2026-07-18) was anchored on "structural enforcement via PreToolUse
hook" as the only viable mechanism. The anchor came from the dialogue-vs-execution
problem framing ("prose rules don't bind under momentum → need structural enforcement
→ PreToolUse is the only structural surface"). That syllogism is correct about prose
vs structure, but wrong about which structural surface to use. Grok's native permission
system IS structural enforcement — it just doesn't live in a hook.

The missed step: before building a hook-based gate, ask "does the host already have a
permission system that classifies commands?" Grok does. We didn't check.

## Recommended path forward

**For the dialogue-vs-execution problem on Grok Build:**

1. **Use native plan mode** (Shift+Tab) as the dialogue-mode gate. Zero friction on
   read-only tools; structural rejection of edits. Already works.
2. **Use `defaultMode: dontAsk` + narrow allowlist** in `~/.grok/config.toml` for the
   "implementation wave authorized" state. Operator flips mode for the wave.
3. **Keep the exec-gate plugin as a reference implementation** of the hook-based pattern
   for hosts that don't have a native permission system. Don't enable it on Grok.
4. **If finer-grained bash command classification is needed later** (e.g., to allow
   `git status` but deny `git push` without toggling modes), use `bash-classify` as a
   PreToolUse hook payload inspector — not the matcher-based approach.

## Related

- [[grok-pretooluse-deny-contract-verified]]
- [[hook-failure-mode-taxonomy]]
- [[grok-per-hook-disable-layer-silent-suppression]]

## Auto-related

- [[non-regex-hook-optimizations]]

## Sources

- [github.com/fprochazka/bash-classify SPEC.md](https://github.com/fprochazka/bash-classify/blob/master/SPEC.md) — full AST classifier specification
- [github.com/anthropics/claude-code#13067](https://github.com/anthropics/claude-code/issues/13067) — plan-mode read-only allowlist feature request (same exact problem on Claude Code)
- [opencode.ai/docs/permissions](https://opencode.ai/docs/permissions/) — command-prefix allowlist pattern
- `~/.grok/docs/user-guide/22-permissions-and-safety.md` L42-68 (Grok read-only command list), L70-90 (permission modes), L259-262 (dangerous commands)
- `~/.grok/docs/user-guide/19-plan-mode.md` (native plan mode as structural gate)
