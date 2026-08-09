---
title: "Hook failure mode taxonomy — general, Grok-specific, exec-gate-specific"
created: 2026-07-22
source: session-2026-07-22 (via /www)
agent: grok
tags: [hooks, failure-modes, grok, claude-code, debugging, pretooluse, exec-gate, taxonomy]
summary: >
  Taxonomy of hook failure modes organized by scope: universal patterns that apply to
  any AI coding agent (fail-open, Goodhart, exit-code mismatch), Grok-specific patterns
  (per-hook disable, stderr-as-failure, env-var preflight), and exec-gate-specific
  patterns (matcher ambiguity, unverified mutating-tool deny). Use as a debugging
  checklist when a hook doesn't fire or doesn't enforce.
cognitive_load: 3
---

## Summary

Hook failure modes cluster into three scopes. Universal patterns (any harness),
Grok-specific patterns, and design-specific patterns. When debugging a hook that
doesn't fire or doesn't enforce, work through the taxonomy in order — universal first
(most common), then host-specific, then design-specific.

## A. Universal hook failure modes (any AI coding agent)

These apply to Claude Code, Grok, Codex, Cursor, and similar harnesses.

### A1. Fail-open masks bugs
Every major harness designs PreToolUse hooks to fail open: if the hook crashes, times
out, or returns malformed output, the tool call proceeds silently. A broken hook
produces silent pass-through, not loud failure. This is by design (availability over
safety) but means hook correctness must be verified independently — absence of errors
is not evidence of enforcement.

Sources: [speakeasy.com](https://www.speakeasy.com/resources/ai-agent-hooks/), local
`host-surface-boundary.md`.

### A2. Exit-code-2 + deny JSON ignored
Claude Code issue #43407: hooks execute correctly, return `permissionDecision: "deny"`
+ exit 2, and the platform ignores the deny and proceeds. Hook runs, deny visible in
stderr, tool executes anyway. Reported on v2.1.87 across `Bash`, `Edit`, `Write`. Not
confirmed for Grok (canary-E showed deny honored for read_file) but the pattern
exists in at least one major harness — verify on each.

Source: [anthropics/claude-code#43407](https://github.com/anthropics/claude-code/issues/43407).

### A3. Session-level approval caches silent hook skip
Claude Code #62437: once a static `ask` rule for a command pattern gets session-level
approval, subsequent PreToolUse hooks for the same pattern are not invoked. The hook
silently stops firing for the rest of the session. Operators assume the hook is
broken when it's actually being short-circuited by prior approval.

Source: [anthropics/claude-code#62437](https://github.com/anthropics/claude-code/issues/62437).

### A4. Goodhart on regex-based content gates
Any hook that checks prose via regex can be satisfied by surface matching without
satisfying intent. "Disposable: A because wiki-X; Disposable: B because wiki-Y" passes
a count-based check while remaining the same epistemic gap the hook was designed to
catch.

Sources: local `llm-judgment-hooks.md`, red-team synthesis (5+ findings converged on this).

### A5. Silent bypass with no annotation
Claude Code #31250: PreToolUse hooks fail silently and the model bypasses enforcement
with no visible signal in scrollback. Operator has no way to distinguish "hook ran and
allowed" from "hook didn't run at all."

Source: [anthropics/claude-code#31250](https://github.com/anthropics/claude-code/issues/31250).

## B. Grok-specific hook failure modes

These are specific to Grok Build (current as of 0.2.103).

### B1. Per-hook disable via `~/.grok/disabled-hooks`
Grok persists Space-toggled hook decisions in `~/.grok/disabled-hooks`, a JSON-encoded
list of paths like `plugin/<name>/hooks:<event>[N].hooks[N]`. When a hook is disabled,
it shows as "enabled" at the plugin level in `grok inspect` but does not dispatch.
**Undocumented in the official hooks guide.** This is the single most common cause of
"plugin enabled but hooks don't fire" in Grok.

Source: local `grok-per-hook-disable-layer-silent-suppression.md`.

### B2. stderr treated as failure signal
Grok's hook runner treats any stderr output from a command-type hook as a failure
signal, even when exit code is 0 and decision is `allow`. Produces misleading "hook
error" annotations. Hook scripts that use stderr for any purpose (logging, warnings,
debug output) will appear to fail.

Source: local `grok-build-hook-exit-code-1-stderr-as-failure-signal.md`.

### B3. Env-var preflight rejects `${VAR}` that isn't real
Grok validates `${...}` references in the hook command field before spawning. If the
referenced env var isn't set in Grok's environment at spawn time, the hook is not
executed and the TUI shows "required env var(s) not set: ${VAR}." Bites silently when
command strings use shell-native variable syntax (PowerShell `${d}`, `$env:NAME`)
that Grok's preflight mistakes for env-var references.

Source: local `grok-hook-command-env-var-preflight.md`.

### B4. Python vs bash script asymmetry on Windows/MSYS
Bash hook scripts on Windows/MSYS show `GROK_SESSION_ID=<unset>` in their environment
while Python hooks see env vars populated, on the same host, same session. Cause not
cleanly isolated. Practical guidance: prefer Python for Grok hooks that need env vars.

Source: local `grok-hook-python-vs-bash-reliability.md`.

### B5. Decision-format mismatch (historical)
Grok's hook decision format is `{"decision":"allow|deny","reason":"..."}`. But third-
party tools (cmux) historically fell through to Claude-shaped JSON
(`permissionDecision`/`permissionDecisionReason`) instead of Grok-native format.
The cmux issue #6303 documents adding a `grok` branch in `renderAgentDecision` to
fix this. Native Grok hooks using the documented format should be unaffected, but
verify the format is honored for your specific tool class.

Source: [manaflow-ai/cmux#6303](https://github.com/manaflow-ai/cmux/issues/6303).

### B6. Matcher ambiguity between Cursor-style and Grok-native tool names
Grok docs say Claude-style tool names are auto-mapped (`Edit/Write/MultiEdit →
search_replace`, `Bash → run_terminal_command`). But cmux #6303 shows
`isSideEffectingTool` matching `Write`/`Bash` but not Grok-native lowercase names
consistently. If a matcher uses one name form and Grok dispatches with another,
the hook won't fire.

Source: [manaflow-ai/cmux#6303](https://github.com/manaflow-ai/cmux/issues/6303).

### B7. 120s PreToolUse timeout on duplicate hooks
When multiple PreToolUse hooks stack (cmux install + manual fast-path), each waits
120s sequentially. Hooks fail-open after timeout. Not a single-hook issue but a
multi-hook composition issue.

Source: [manaflow-ai/cmux#6303](https://github.com/manaflow-ai/cmux/issues/6303).

## C. exec-gate-specific failure modes (this plugin)

Applying the taxonomy to `~/.grok/plugins/exec-gate/` as built in session 2026-07-18.

### C1. Per-hook disable (CONFIRMED)
All 4 exec-gate hooks disabled in `~/.grok/disabled-hooks`. Confirmed by direct file
read. This is the active failure mode preventing dispatch.

### C2. Matcher ambiguity (UNVERIFIED)
Our matcher is `search_replace|write|run_terminal_command|spawn_subagent`. If Grok
dispatches with different names for the same tools (e.g., `Write` not `write`, or
internal dispatcher names not in the documented alias table), the matcher fails
silently. Cannot rule out until hook fires.

### C3. `${GROK_PLUGIN_ROOT}` expansion (UNVERIFIED)
Docs say always injected for plugin hooks. Canary C's preflight failure showed
`${...}` syntax can fail preflight. `${GROK_PLUGIN_ROOT}` is a real env var so should
expand, but never tested end-to-end. If it fails, hook command is rejected preflight.

### C4. stderr from Python treated as failure (POTENTIAL)
`gate.py`'s `_debug_log` swallows exceptions silently, but any uncaught Python
warning to stderr (e.g., DeprecationWarning) would be treated as failure by Grok's
runner. Mitigation: ensure `python -W ignore` or redirect stderr to /dev/null in
the command.

### C5. Decision-format mismatch (UNVERIFIED for mutating tools)
`gate.py` emits `{"decision": "deny", "reason": "..."}` (Grok-native per docs).
Canary-E test confirmed the format works for `read_file`. But the mutating tools
we're gating (`search_replace`, `write`, `run_terminal_command`, `spawn_subagent`)
were never tested because the hook was disabled before integration testing.

### C6. Session-level approval cache (POSSIBLE)
If the operator (or always-approve mode) approved a mutating tool earlier in the
session, the PreToolUse hook may not be invoked for subsequent calls to the same
tool. Per Claude Code #62437 (Claude-specific; unverified for Grok).

## Diagnostic checklist

When a Grok plugin hook doesn't fire or doesn't enforce, check in this order:

1. **`~/.grok/disabled-hooks`** — grep for the plugin name. (B1, most common)
2. **`grok inspect` Hooks section** — does the hook appear at all? If not, discovery
   failed (check `hooks.json` syntax, plugin enabled state).
3. **TUI scrollback annotations** — errored hooks show annotations; silently-skipped
   hooks show nothing.
4. **`${VAR}` in command field** — does the command reference any `${...}` that isn't
   a documented env var? (B3)
5. **Matcher name form** — does the matcher use the name Grok actually dispatches
   with? Try both Claude-style (`Bash`) and Grok-native (`run_terminal_command`).
   (B6)
6. **stderr output** — does the hook script write anything to stderr? Grok treats
   this as failure. (B2)
7. **Decision format** — does the hook emit `{"decision": "deny", "reason": "..."}`?
   Not Claude-shaped `permissionDecision`. (B5)
8. **Timeout** — is the hook exceeding the configured `timeout`? Default 5s; complex
   hooks may need more. (B7, A1)
9. **Permission mode interaction** — is always-approve or a prior approval
   short-circuiting the hook? (A3, C6)

## Related

- [[grok-per-hook-disable-layer-silent-suppression]]
- [[grok-build-hook-exit-code-1-stderr-as-failure-signal]]
- grok-hook-command-env-var-preflight
- grok-hook-python-vs-bash-reliability
- [[grok-pretooluse-deny-contract-verified]]
- [[grok-pretooluse-matcher-and-readonly-fastpath]]
- [[llm-judgment-hooks]]
- [[host-surface-boundary]]

## Auto-related

- [[skill-catalog]]
- [[grok-build-disabled-hooks-per-hook-layer]]

## Sources

- Claude Code issues: [#43407](https://github.com/anthropics/claude-code/issues/43407), [#35136](https://github.com/anthropics/claude-code/issues/35136), [#62437](https://github.com/anthropics/claude-code/issues/62437), [#31250](https://github.com/anthropics/claude-code/issues/31250), [#45837](https://github.com/anthropics/claude-code/issues/45837)
- cmux issue: [#6303](https://github.com/manaflow-ai/cmux/issues/6303)
- [speakeasy.com: AI agent hooks](https://www.speakeasy.com/resources/ai-agent-hooks/)
- Local wiki: `grok-per-hook-disable-layer-silent-suppression.md`,
  `grok-build-hook-exit-code-1-stderr-as-failure-signal.md`,
  `grok-hook-command-env-var-preflight.md`, `grok-hook-python-vs-bash-reliability.md`,
  `grok-pretooluse-deny-contract-verified.md`, `grok-pretooluse-matcher-and-readonly-fastpath.md`,
  `llm-judgment-hooks.md`, `host-surface-boundary.md`
- Session 2026-07-22 `/www` research pass
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
