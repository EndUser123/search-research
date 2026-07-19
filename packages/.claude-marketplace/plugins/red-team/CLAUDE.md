# red-team plugin

Multi-agent adversarial review pipeline. Invoked as `/red-team:red-team`.

## Layout (current)

- `commands/red-team.md` — orchestrator entry. Single source of truth for `run_dir`, disk-backed findings schema, agent flow, verdict format.
- `agents/red-team-{role}.md` — planner, critic, and specialists (gate-reviewer, workflow-reviewer, security, performance, logic, state, failure-modes, plugin, testing).
- `__lib/findings_schema.py` — pure-logic schema validator (unit-tested via `tests/`).
- `tests/` — schema unit tests + enablement/smoke integration tests.

## Pending

- `__lib/orchestrator.py` — deterministic Python orchestrator (Phase 1, pending).
- `tests/test_orchestrator.py` — orchestrator tests (Phase 1, pending).
- `RED_TEAM_ORCHESTRATION.md` — persisted spec (Phase 3, pending).

## Disk-backed handoff (non-negotiable)

The orchestrator holds only file paths; specialist findings load into the critic's ephemeral context. The canonical `run_dir` spec lives in `commands/red-team.md` → "Findings handoff" — read it there rather than re-stating the path here (a stale literal in this file caused a three-way contradiction between the skill body, this file, and the runtime). Per-specialist: `{run_dir}/{specialist}.json`.

## Invocation cost

Promoting this to a plugin changed invocation from `/red-team` (standalone) to `/red-team:red-team` (namespaced). Agents resolve as `red-team:red-team-{role}`.

## Modes (Phase 4 absorption)

`commands/red-team.md` exposes three review depths behind one entry point:

- **default** (`/red-team <proposal>`) — planner → specialists → critic → PROCEED/REVISE/BLOCK. The flow documented in this file.
- **pre-mortem** (`/red-team pre-mortem <target>`) — selects the 3-phase adaptive critique engine at `cc-skills-sdlc/skills/pre-mortem/` (Health Score + RNS + blinded consumer-contract review). The standalone `/pre-mortem` is now a deprecation stub.
- **adversarial** (`/red-team adversarial <response>`) — **PENDING (#872/#873/#874):** the adv-review runner (`runner.py`, `calibrate.py`, `harness_registry.py`) is not yet implemented, so this mode currently routes to an unbuilt engine and emits an inline fallback rather than dispatching. When built, it will select the external-LLM harness roster at `cc-skills-ai-api/skills/adv-review/` (agy / glm-5.2 / MiniMax-M3 / kimi-k2.7-code; calibration mode `--cases <corpus>`). The standalone `/adv-review` is now a deprecation stub. Planned backend for `/improve external-second-opinion` (which already has its own fallback).

`/red-team` routes; it does not vendor. The two engine directories remain the source of truth for their phase prompts / harness schema.

## Adjacent systems (do not duplicate)

- `/code-review` — routine code review (file:line shaped).
- `/adversarial-review` agent — parallel code review (file:line shaped). Distinct from `/red-team adversarial` mode, which dispatches to **external LLM harnesses** for B-class divergence, not internal agents.

## Host applicability (read this before editing)

This plugin is **host-agnostic source**. It runs unchanged under both Claude
Code and Grok Build. The contracts above (disk-backed handoff, findings schema,
verdict gate, telemetry/incident writers) must stay host-neutral — no
host-specific paths, tool names, or dispatch assumptions in any file under this
plugin.

**Grok-specific overlays live in `~/.grok/AGENTS.md`**, not here. Examples of
what belongs in the Grok overlay (NOT in this plugin):

- Web-search tool preference order (`minimax-search` > `web-search-prime` >
  built-in `web_search`). Claude Code has a different search-tool surface.
- Async-dispatch notification handling (Grok Build's `background: true` model).
- Host-specific CLI fallbacks.

**Why this matters:** the `/wiki` skill is currently forked across Grok
(309 lines) and Claude Code (531 lines), creating a dual-source-of-truth hazard
(BLOCK finding WRF-001 in run 20260719-133433). `/red-team` must NOT repeat
that pattern. One source, host-neutral; host-specific behavior overlays in the
host's own config directory.

If you find yourself wanting to add a Grok-only or Claude-only behavior to a
file in this plugin, stop. Add it to the host's overlay instead
(`~/.grok/AGENTS.md` for Grok; `~/.claude/CLAUDE.md` or `~/.claude/rules/` for
Claude Code), and reference it from the plugin only as a pointer
("see `<host-overlay-path>` for host-specific configuration").
