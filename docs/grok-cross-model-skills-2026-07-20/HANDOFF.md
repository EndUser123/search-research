# Handoff: Grok cross-model skill siblings (`/mmx`, `/codex`)

**Created:** 2026-07-20
**Merged from:** `P:\tmp\codex-from-grok-handoff.md` (prior session's `/codex`-only handoff, 2026-07-20)
**Status:** Ready to start. `/codex` architecture is decided and verified; `/mmx` needs the same verification pass.
**Parent investigation:** `P:\docs\tp-cognition-migration-2026-07-20\FINAL_REPORT.md`

## What this is

Create `/mmx` and `/codex` as Grok skills, siblings to `/agy`. Each is a first-class cross-model second-opinion skill with its own conductor, verified CLI flags, fail-open behavior, and result normalization. Pure conductor prose plus verified flag knowledge — exactly like `/agy`. No new binary, no MCP server, no daemon, no packet runner, no `__lib`.

## Why

`/agy` (Antigravity / Gemini) exists as a real skill at `C:\Users\brsth\.grok\skills\agy\SKILL.md`. `/mmx` (MiniMax) and `/codex` (OpenAI) are documented as Grok multi-model CLIs (see `~/.grok/AGENTS.md` Multi-model tool availability section) but are **not** surfaced as skills.

This asymmetry means any Grok skill that wants cross-model independence has exactly one first-class path (`/agy`) and two ad-hoc subprocess paths. The foundational fix is to make all three sibling skills. Then any skill (`/tp`, `/review`, `/red-team`, or the user directly) can lean on them uniformly.

## Architecture decision (from the prior `/codex` handoff — do not re-litigate without new evidence)

**Build each skill at `C:\Users\brsth\.grok\skills\<cli>\SKILL.md`, modeled on `/agy`.**

- The skill teaches Grok to construct the appropriate CLI invocation and execute via `run_terminal_command`.
- No new binary, no MCP server, no packet runner, no daemon.
- Reuses the entire `/agy` conductor framework (assignment adequacy, proportional confirmation, outcome labeling, run record).

### Rejected alternatives (already assessed for `/codex`; same reasoning applies to `/mmx`)

| Alternative | Why rejected |
|---|---|
| MCP server wrapping the CLI | More work; less autonomous (model has to construct MCP calls); Grok Build MCP surface is already crowded |
| Extend `codex-external-delegation` with a `codex` worker | Packet/runner pattern is parent-agnostic but adds ceremony; `/agy` proves direct shell-out is sufficient |
| Port `openai/codex-plugin-cc` directly (for `/codex`) | Claude-Code-specific (subagents, Stop hook review gate, `/codex:rescue` agent). Core idea — wrap `codex exec` — is portable; the plugin scaffolding is not. |

### Decision point not yet resolved

Mirror `/agy` exactly (one skill per CLI, three sibling skills) **or** generalize `/agy` into a shared conductor with three provider backends?
- One-skill-per-CLI is simpler and matches `/agy`'s precedent.
- A shared conductor avoids duplication but adds coupling.
- Per workspace CLAUDE.md: prefer simplicity unless coupling has measured benefit. **Recommendation: start with one-skill-per-CLI; revisit only if a third consumer appears or maintenance pain is observed.**

## `/codex` — verified facts (run again on resume; may have drifted)

These were verified in the prior session on 2026-07-20:

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

### `/codex` concrete flag mapping

| Operation | Command |
|---|---|
| Read-only review (uncommitted) | `codex review --uncommitted` |
| Read-only review (vs base) | `codex review --base <ref>` |
| Read-only review (specific commit) | `codex review --commit <sha>` |
| Read-only task | `codex exec --json --ephemeral -s read-only -m <model> "<prompt>"` |
| Write-capable task (in worktree) | `codex exec --json -s workspace-write -C <worktree> -m <model> "<prompt>"` |
| Structured final response | add `--output-schema <file>` and/or `-o <last-msg-file>` |

### `/codex` open design questions (resolve before writing the skill)

1. **Default model.** `gpt-5.6-sol` as default, or leave unspecified (let codex pick)? Lean: specify `gpt-5.6-sol` as default, allow override.
2. **Scope of v0.1.** Three modes (read-only review, read-only task, write-capable task), or start with just review? Lean: three modes — `/agy` ships all of them.
3. **Session resume.** Include `codex exec resume` for multi-turn delegation in v0.1, or defer? Lean: defer; `--ephemeral` is simpler.
4. **Structured output.** Use `--output-schema` for the run record, or let the skill prose describe the expected JSON shape and let codex free-form it? Lean: start free-form, add schema if reliability is poor.

## `/mmx` — needs the same verification pass

The prior handoff did not cover `/mmx`. Before writing `C:\Users\brsth\.grok\skills\mmx\SKILL.md`, run:

- `mmx --version` (or `mmx --help`) to confirm the binary is present and probe its interface
- `where mmx` to confirm it's on PATH
- Look for OAuth state equivalent to `~/.codex/auth.json` (under `~/.minimax/` or similar — probe)
- Identify the non-interactive invocation equivalent of `codex exec` (if `mmx` has one)
- Identify the equivalent of `codex review` if it exists; otherwise `/mmx` may be exec-only
- Check `mmx auth` / `mmx login` subcommands for credential state

**Do not assume `mmx` mirrors `codex`'s interface.** The MiniMax CLI may be a thin wrapper around their HTTP API with a different flag surface. Probe before designing.

If `mmx` lacks a non-interactive mode entirely (some provider CLIs are chat-only), `/mmx` may not be buildable in the same shape — in which case the skill should document that limitation explicitly and fall back to the HTTP API (via `requests` or similar) with explicit API-key handling, which is a heavier lift than `/agy`'s pattern.

## What to borrow from each reference

| Source | What to lift |
|---|---|
| `C:\Users\brsth\.grok\skills\agy\SKILL.md` | Entire conductor framework: assignment adequacy (5 dimensions), proportional confirmation, outcome labels (`INVOCATION_FAILED` / `UNRELIABLE` / `MATERIAL_DELTA` / `USEFUL_DISAGREEMENT` / `CONFIDENCE_GAIN` / `DUPLICATES_BASELINE` / `LOW_SIGNAL`), run record schema, retry policy |
| `openai/codex-plugin-cc` (github.com/openai/codex-plugin-cc) — for `/codex` only | The three operation modes (review / exec read-only / exec write-capable), the flag knowledge, structured-output via `--output-schema` |
| `P:\packages\codex-external-delegation\skill\SKILL.md` | Safety contract language (`mode`, `allowed_paths`, `forbidden_actions`, `verification.commands`); adapt to skill prose rather than packet JSON |
| `P:\packages\codex-external-delegation\src\commands.mjs` | The flag-to-codex mapping already worked out (around the `codex` branch) |

## Files to read before resuming

- `C:\Users\brsth\.grok\skills\agy\SKILL.md` — the pattern to mirror (read end-to-end)
- `~/.grok/docs/user-guide/10-hooks.md` — Grok Build hook surface (5s default timeout; `PreToolUse` is the only blocking event)
- `C:\Users\brsth\.grok\plugins\proposal-grounding-monitor\scripts\relevance.py` — the guardrail that may flag this skill's work if discovery is skipped (read so you know what the monitor expects)
- `P:\packages\codex-external-delegation\skill\SKILL.md` — existing delegation safety contract (for prose reuse)
- `P:\packages\codex-external-delegation\src\commands.mjs` — flag-to-codex mapping already worked out

## Files to create

- `C:\Users\brsth\.grok\skills\codex\SKILL.md` — the `/codex` skill
- `C:\Users\brsth\.grok\skills\mmx\SKILL.md` — the `/mmx` skill

No scripts, no `__lib`, no companion binary for either skill. Pure conductor prose plus verified flag knowledge.

## Resumption protocol

1. **Verify CLIs first.** Re-run `codex --version` and `codex exec --help`; run `mmx --version` / `mmx --help` / `where mmx` fresh.
2. Read `/agy/SKILL.md` end-to-end.
3. For `/codex`: read `openai/codex-plugin-cc` README for the three operation modes.
4. For `/mmx`: probe whether it has a non-interactive mode at all. If not, scope the skill accordingly.
5. Write each `SKILL.md` by adapting `/agy`'s structure: same frontmatter, same conductor sections, same outcome taxonomy, with the CLI invocations swapped in.
6. Smoke-test each skill on a real review task in a fresh Grok session.
7. If the `proposal-grounding-monitor` plugin is enabled, expect it to require you to read `/agy` (and for `/codex`, `codex-plugin-cc`) before the skill is considered grounded — that's the guardrail working as intended.

## What is explicitly NOT in scope

**`/tp critic` is not in scope.** The parent investigation recommended a `/tp critic` pilot. On review, that framing was wrong:

- The task spec named `/tp` as "the likely user-facing critical-friend interface," which anchored the pilot recommendation on `/tp`.
- But cross-model independence is a **Grok-layer capability**, not a `/tp` feature.
- The investigation's "Gap 1: independent critique" is real as a structural property, but its **frequency in `/tp` sessions was never measured** — only inferred from the eval's methodological limitations (single judge, same-model responders and judges).
- The actual `/tp` failures observed in the naturalistic evaluation (C01, C02) were reasoning-as-substitute-for-tool-use, not framing-blind-spots. The state-grounding edit addressed those.

**Recommendation:** ship `/mmx` and `/codex` first. Revisit whether `/tp` specifically needs a `/tp critic` variant only if observed `/tp` sessions show framing-blind-spot failures that a second model would have caught. If that happens, `/tp critic` becomes a thin variant that invokes `/agy` / `/mmx` / `/codex` uniformly via the skill interface — not its own subprocess machinery.

## Estimated effort

- `/codex`: ~2–3 hours for v0.1 (three modes, no resume, no structured output schema). `/agy` is ~410 lines; expect similar length. Most of the design is already decided above.
- `/mmx`: **unknown** until the CLI is probed. If `mmx` has a clean non-interactive mode, same 2–3 hours. If it's chat-only or requires HTTP API wrapping, scope expands.

## Reference paths

- `/agy` skill (the pattern to mirror): `C:\Users\brsth\.grok\skills\agy\SKILL.md`
- Original investigation report: `P:\docs\tp-cognition-migration-2026-07-20\FINAL_REPORT.md`
- Prior `/codex`-only handoff (superseded by this merged version): `P:\tmp\codex-from-grok-handoff.md`
- Multi-model tool availability: `C:\Users\brsth\.grok\AGENTS.md` (Multi-model tool availability section)

## Cleanup already done

- Removed stale partial design doc (`grok-design-doc-efeac6c6.md`, 31KB) left by a killed `/design` writer subagent at `P:\docs\tp-cognition-migration-2026-07-20\design\`. That dir is now deleted. The parent investigation report at `P:\docs\tp-cognition-migration-2026-07-20\FINAL_REPORT.md` is intact and authoritative.
