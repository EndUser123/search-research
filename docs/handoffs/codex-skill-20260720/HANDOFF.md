---
current_session_id: 019f7e24-0513-7773-875d-5a3e3051dc8f
parent_handoff_path: none
status: CLOSED
work_status: "Architecture decided, implementation deferred. v0.1 estimated 2-3 hours."
created: 2026-07-20
---

# Handoff: Codex-from-Grok-Build skill

**Status:** architecture decided, implementation deferred.
**Last active:** 2026-07-20.
**Originating session:** Grok Build, `P:\` workspace. Session 019f7e24.

## Goal (one sentence)

Let Grok Build invoke Codex (GPT-5.6 Soul) for second opinions, code review, and bounded delegation — using the local `codex` binary's OAuth login, no API key — by creating a `/codex` skill modeled on the proven `/agy` pattern.

## Why it stalled

The session pivoted to building a guardrail (`proposal-grounding-monitor`) after I proposed an MCP server and a packet-runner extension *before* reading `/agy` and `openai/codex-plugin-cc`. The guardrail work is complete (111 tests passing, plugin at `C:\Users\brsth\.grok\plugins\proposal-grounding-monitor\`). The actual `/codex` skill was never written.

---

## Verified facts (run these again on resume — they may have drifted)

1. **`codex` binary present, v0.144.1.** `codex --version` returned `codex-cli 0.144.1`.
2. **OAuth state present.** `~/.codex/auth.json` exists; no API key needed.
3. **Headless mode exists.** `codex exec --help` confirmed:
   - `codex exec [PROMPT]` — non-interactive; reads prompt from arg or stdin
   - `-s, --sandbox {read-only, workspace-write, danger-full-access}` — maps 1:1 to a `mode` field
   - `-m, --model <MODEL>` — e.g. `gpt-5.6-sol`
   - `-C, --cd <DIR>` — working root
   - `--add-dir <DIR>` (repeatable) — additional writable dirs
   - `--json` — JSONL event stream on stdout
   - `--ephemeral` — no session persistence (good for one-shot)
   - `--output-schema <FILE>` — JSON Schema for structured final response
   - `-o, --output-last-message <FILE>` — write final message to file
4. **`codex review` subcommand exists.** `codex review --uncommitted`, `--base <ref>`, `--commit <sha>`.
5. **Grok Build hooks documented.** `~/.grok/docs/user-guide/10-hooks.md` — `command` and `http` hook types; 5s default timeout; `PreToolUse` is the only blocking event; all others passive.

## Architecture decision (do not re-litigate without new evidence)

**Build a `/codex` skill at `C:\Users\brsth\.grok\skills\codex\SKILL.md`, modeled on `/agy`.**

- The skill teaches Grok to construct `codex exec` / `codex review` commands and invoke them via `run_terminal_command`.
- No new binary, no MCP server, no packet runner, no daemon.
- Reuses the entire `/agy` conductor framework (assignment adequacy, proportional confirmation, outcome labeling, run record).

### Rejected alternatives (with reasons)

| Alternative | Why rejected |
|---|---|
| MCP server wrapping `codex` | More work; less autonomous (model has to construct MCP calls); Grok Build MCP surface is already crowded |
| Extend `codex-external-delegation` with a `codex` worker | Packet/runner pattern is parent-agnostic but adds ceremony; `/agy` proves direct shell-out is sufficient |
| Port `openai/codex-plugin-cc` directly | Claude-Code-specific (subagents, Stop hook review gate, `/codex:rescue` agent). Core idea — wrap `codex exec` — is portable; the plugin scaffolding is not. |

### What to borrow from each reference

| Source | What to lift |
|---|---|
| `C:\Users\brsth\.grok\skills\agy\SKILL.md` | Entire conductor framework: assignment adequacy (5 dimensions), proportional confirmation, outcome labels (INVOCATION_FAILED / UNRELIABLE / MATERIAL_DELTA / USEFUL_DISAGREEMENT / CONFIDENCE_GAIN / DUPLICATES_BASELINE / LOW_SIGNAL), run record schema, retry policy |
| `openai/codex-plugin-cc` (github.com/openai/codex-plugin-cc) | The three operation modes (review / exec read-only / exec write-capable), the flag knowledge, structured-output via `--output-schema` |
| `P:\packages\codex-external-delegation\` | Safety contract language (`mode`, `allowed_paths`, `forbidden_actions`, `verification.commands`); adapt to skill prose rather than packet JSON |

---

## Open design questions (resolve before writing the skill)

1. **Default model.** `gpt-5.6-sol` as default, or leave unspecified (let codex pick)? Lean: specify `gpt-5.6-sol` as default, allow override.
2. **Scope of v0.1.** Three modes (read-only review, read-only task, write-capable task) matching the rejected proposal, or start with just review? Lean: three modes — `/agy` ships all of them.
3. **Session resume.** Include `codex exec resume` for multi-turn delegation in v0.1, or defer? Lean: defer; `--ephemeral` is simpler.
4. **Structured output.** Use `--output-schema` for the run record, or let the skill prose describe the expected JSON shape and let codex free-form it? Lean: start free-form, add schema if reliability is poor.

---

## Concrete flag mapping (verified against `codex exec --help`)

| Operation | Command |
|---|---|
| Read-only review (uncommitted) | `codex review --uncommitted` |
| Read-only review (vs base) | `codex review --base <ref>` |
| Read-only review (specific commit) | `codex review --commit <sha>` |
| Read-only task | `codex exec --json --ephemeral -s read-only -m <model> "<prompt>"` |
| Write-capable task (in worktree) | `codex exec --json -s workspace-write -C <worktree> -m <model> "<prompt>"` |
| Structured final response | add `--output-schema <file>` and/or `-o <last-msg-file>` |

---

## Files to read before resuming

- `C:\Users\brsth\.grok\skills\agy\SKILL.md` — the pattern to mirror
- `C:\Users\brsth\.grok\plugins\proposal-grounding-monitor\scripts\relevance.py` — the guardrail that will flag this skill's work if discovery is skipped (read this so you know what the monitor expects)
- `P:\packages\codex-external-delegation\skill\SKILL.md` — the existing delegation safety contract (for prose reuse, not for the runner)
- `P:\packages\codex-external-delegation\src\commands.mjs` — the flag-to-codex mapping already worked out (lines around the `codex` branch)

## Files to create

- `C:\Users\brsth\.grok\skills\codex\SKILL.md` — the skill itself

No scripts, no `__lib`, no companion binary. The skill is pure conductor prose plus verified flag knowledge, exactly like `/agy`.

---

## Resumption protocol

1. Re-run `codex --version` and `codex exec --help` to confirm flags haven't drifted.
2. Read `/agy/SKILL.md` end-to-end.
3. Read `openai/codex-plugin-cc` README for the three operation modes.
4. Write `C:\Users\brsth\.grok\skills\codex\SKILL.md` by adapting `/agy`'s structure: same frontmatter, same conductor sections, same outcome taxonomy, with `agy -p ...` replaced by `codex exec ...` / `codex review ...`.
5. Smoke-test: invoke `/codex` on a real review task in a fresh Grok session.
6. If the `proposal-grounding-monitor` plugin is enabled, expect it to require you to read `/agy` and `codex-plugin-cc` before the skill is considered grounded — that's the guardrail working as intended.

## Estimated effort

~2-3 hours for v0.1 (three modes, no resume, no structured output schema). The `/agy` skill is ~410 lines; expect similar length.
