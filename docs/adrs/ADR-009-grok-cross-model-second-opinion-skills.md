# ADR-009: Grok Cross-Model Second-Opinion Skill Siblings (`/codex`, `/mmx`)

**Date:** 2026-07-20
**Status:** Implemented (PR 0–4 shipped 2026-07-20; PR 5 shared-conductor evaluation deferred 1 month post-ship)
**Decider:** Bruce Thomson
**Full design (authoritative):** `~/.grok/design-runs/grok-design-6bf249df/grok-design-doc-6bf249df.md` (~92 KB, 5 review rounds)
**Review provenance:** `~/.grok/design-runs/grok-design-6bf249df/grok-design-review-6bf249df.md` (21 review issues + 6 source-authority-discovery gaps, all addressed)
**Parent investigation:** `P:\docs\tp-cognition-migration-2026-07-20\FINAL_REPORT.md`
**Supersedes:** none

---

## Context and Problem Statement

`~/.grok/AGENTS.md` documents three Grok multi-model CLIs as fallbacks when a built-in tool fails (`agy`, `mmx`, `codex`). Only one — `/agy` (Antigravity / Gemini) — is surfaced as a first-class skill at `~/.grok/skills/agy/SKILL.md`. The other two are ad-hoc subprocess paths with hand-rolled flag knowledge that drifts as the CLIs evolve.

The asymmetry has two concrete costs:

1. **Discovery asymmetry.** Any Grok skill that wants a cross-model second opinion has exactly one first-class path (`/agy`) and two ad-hoc paths. Consumers (`/tp`, `/review`, `/red-team`, or the user directly) cannot treat the three CLIs uniformly.
2. **Outcome labeling drift.** Ad-hoc invocations have no enforced `## <CLI> RESULT` block structure. Cross-model findings lose their provenance and can't be classified into the strict-precedence taxonomy (`INVOCATION_FAILED` / `UNRELIABLE` / `MATERIAL_DELTA` / `USEFUL_DISAGREEMENT` / `CONFIDENCE_GAIN` / `DUPLICATES_BASELINE` / `LOW_SIGNAL`) that `/agy` enforces.

The foundational fix: make all three first-class siblings.

## Source-authority-discovery (the required preflight)

Per `P:\.claude\CLAUDE.md`, this kind of "a capability is missing / unique / safe to replace" claim requires a source-authority-discovery audit before design work. The audit was run against seven scopes (`~/.grok/skills`, `~/.grok/bundled`, `~/.claude/plugins/cache`, `~/.claude/plugins/marketplaces`, `P:\packages\.claude-marketplace\plugins`, `P:\.agents\skills`, `P:\docs`) with nine target tokens (`mmx`, `codex`, `agy`, `antigravity`, `minimax`, `second-opinion`, `cross-model`, `## MMX RESULT`, `## CODEX RESULT`).

Audit artifact: `P:\tmp\source-discovery-mmx-codex-v2.json` (956 matching files; 5 conflicts; `decision: needs_review`).

The audit surfaced **6 gaps** that the original design missed and that the 3-round writer/reviewer loop did not catch (because the loop was internally rigorous but never challenged the framing itself). All six were addressed in design round 3:

| ID | Gap | Severity | Resolution |
|---|---|---|---|
| D1 | `cc-skills-ai-api` plugin ships near-identical sibling set (`/codex`, `/agy`, `/ai-cli`) on the Claude host — unaddressed alternative | major | Rejected: different architecture (subagent dispatch vs shell-out) — not portable across hosts. Hidden anchor named. |
| D2 | `mmx auth login` supports OAuth, not just API key — design assumed API-key-only | major | Auth-method routing branches on `mmx auth status`; OAuth preferred (matches `/agy`, `/codex`); API-key fallback. |
| D3 | Bare `mmx` invocation silently fails on Windows (`.cmd` shim + `CreateProcess`) | major | All `/mmx` runtime invocations use `$mmxCmd` — the node-script resolver from `search-research/core/providers/mmx_backend.py`. Verified `mmx.mjs` exists on this host. |
| D4 | `mmx search query` is a real third capability — design only probed `text chat` | major | `/mmx` v0.1 ships three modes (chat-inline, chat-messages-file, search). |
| D5 | Codex exposes `sandbox_permissions` override, not just `sandbox_mode` | minor | Host preflight reads both keys. |
| D6 | New skill frontmatter must declare `host: grok` per the global AGENTS.md convention | minor | Both `/codex` and `/mmx` frontmatters include `host: grok`. `/agy` retro-tagging is out of scope (pre-convention, per the 2026-07-18 audit's "tag at write time" rule). |

One falsifier was probed and rejected: `--effort` flag for `/codex`. The round-1 review noted `cc-skills-ai-api`'s codex skill exposes it; direct re-probe of `codex exec --help` this session confirmed it is subagent-protocol-only, not on the shell CLI. A shell-out skill legitimately does not expose it.

## Decision

Build **three Grok-host shell-out sibling skills**, one per CLI, modeled on `/agy`:

- `C:\Users\brsth\.grok\skills\codex\SKILL.md` (new, ~410 lines)
- `C:\Users\brsth\.grok\skills\mmx\SKILL.md` (new, ~410 lines)
- `/agy` is unchanged (canonical pattern).

Each is a **conductor prose document plus verified CLI flag knowledge**. No new binary, no MCP server, no daemon, no packet runner, no `__lib`. The conductor constructs the CLI invocation and executes it via `run_terminal_command`, normalizes the result, labels the outcome by strict precedence, and emits a run record.

### Shared conductor framework (lifted from `/agy`, applied to both)

All three skills share verbatim:

- **Five assignment-adequacy dimensions** (target, outcome, context, constraints, evidence) with four classifications (`explicit | grounded-in-session | safely-inferred | blocking`).
- **Four dispositions** (`INVOKE_DIRECTLY | CLARIFICATION_REQUIRED | AUTHORIZATION_REQUIRED | DELEGATION_NOT_WORTHWHILE`).
- **Seven outcome labels** with strict precedence (failures beat disagreements beat agreements).
- **Run record JSON schema** (the only per-skill field is `worker_cli`).
- **Retry policy** (at most one retry; specific correctable defects only; quota never retried).
- **Fail-open contract**: a second-opinion skill must never block the primary workflow on invocation failure.

### Per-skill scope (v0.1)

**`/codex` (three modes)** — codex is a local agent CLI with file access and sandbox:

| Mode | Canonical invocation |
|---|---|
| Read-only review (uncommitted) | `codex exec review --uncommitted -c sandbox_mode=read-only -c approval_policy=on-request -m <model>` |
| Read-only task | `codex exec --json --ephemeral -s read-only -m <model> -C <cwd> "<prompt>"` |
| Write-capable task | `codex exec --json -s workspace-write -C <worktree> -m <model> "<prompt>"` (mandatory dedicated worktree) |

**`/mmx` (three modes)** — mmx is a chat-only HTTP API wrapper with no file access, no sandbox, no review:

| Mode | Canonical invocation |
|---|---|
| Inline-context chat | `& $mmxCmd[0] $mmxCmd[1..] text chat --message "<prompt>" --output json --quiet` |
| Messages-file chat | `& $mmxCmd[0] $mmxCmd[1..] text chat --messages-file <file> --output json --quiet` |
| Web search | `& $mmxCmd[0] $mmxCmd[1..] search query "<query>" --output json --quiet` |

where `$mmxCmd = @("node", "$env:APPDATA\npm\node_modules\mmx-cli\dist\mmx.mjs")` when the node script exists (Windows), else `@("mmx")`.

### Security posture

**`/codex`** — read-only default, write-capable opt-in. Mandatory host preflight reads `~/.codex/config.toml` and injects overrides only when a key is **present and permissive**; absent keys use codex's built-in default (typically `read-only`). Bare `codex review` shortcut is forbidden (inherits `danger-full-access` from config; has no `-s/--sandbox` flag). OAuth at `~/.codex/auth.json` — the conductor never reads this file directly.

**`/mmx`** — auth-method routing:

- **OAuth (preferred):** mirrors `/codex`'s auth story. No API key in any file the conductor reads. `mmx auth status` is the only auth check. `mmx auth refresh` is the retry-on-expiry path.
- **API key (current host state):** plaintext key in `~/.mmx/config.json`. Producer/consumer carve-out: the human implementer reads the file once during PR 0; the runtime conductor never reads it under any conditions. Forbidden operations: `--api-key`, `mmx config show`, `mmx config set`, `mmx config export-schema`, `Get-Content ~/.mmx/config.json` (or any direct read).

## Critical security fix landed during review

The original design's canonical read-only review invocation was `codex review --uncommitted`. Round-1 review discovered `codex review --help` does **not** expose `-s/--sandbox`, and the host's `~/.codex/config.toml` sets `sandbox_mode = "danger-full-access"` — so every "read-only review" would silently run with full filesystem and network access. The threat-model claim that review was read-only was an assertion, not an enforced property.

Fix: canonical review invocation changed to `codex exec review --uncommitted -c sandbox_mode=read-only -c approval_policy=on-request -m <model>` (the `codex exec review` subcommand accepts `-c` overrides). Threaded across 8 references in the design; bare `codex review` documented as the user-facing shortcut the skill forbids.

## Alternatives Considered

### A. MCP server wrapping each CLI (rejected)

More implementation work; less autonomous (the model constructs MCP calls instead of direct shell invocations); the Grok Build MCP surface is already crowded. `/agy` proves direct shell-out is sufficient.

### B. Extend `codex-external-delegation` with a `codex` worker (rejected)

The packet/runner pattern is parent-agnostic but adds ceremony (packet construction, runner lifecycle, result polling). `/agy` proves direct shell-out is sufficient without this machinery.

### C. Port `openai/codex-plugin-cc` directly (rejected for `/codex`)

`~/.claude/plugins/cache/openai-codex/codex/1.0.5/` and `1.0.6/` exist on this host. The plugin is Claude-Code-specific (subagents via `Agent()`, Stop hook review gate, `/codex:rescue` agent). Core idea — wrap `codex exec` — is portable; the plugin scaffolding is not.

### D. One shared skill with provider flag (rejected)

Would force a provider abstraction layer (which flags are universal? how is output normalized? who owns the run record?). Each abstraction is a future bug surface. Duplication is bounded at ~410 lines per skill. Revisit if a third consumer or measured maintenance pain appears.

### E. Partial-share: extract shared conductor prose to `__lib/conductor.md` referenced by all three skills (rejected for v0.1, accepted as v0.2 candidate)

Avoids duplicating the ~410-line conductor framework three times. **Hidden anchor (named during review):** all consolidation options assume coupling cost > duplication cost is a stable claim. Rejected for v0.1 because the three CLIs have fundamentally different shapes (`/agy` and `/codex` are local agents with file/sandbox/review; `/mmx` is a chat-only HTTP wrapper). Partial-share is the right move when the three skills are more alike than different — that's a v0.2 decision with falsifiable criterion.

### F. Port `cc-skills-ai-api`'s cross-model skills (rejected for `/codex`, surfaced in source-authority-discovery — Gap D1)

`P:\packages\.claude-marketplace\plugins\cc-skills-ai-api\skills\` ships a near-identical sibling set on the Claude host: `/codex`, `/agy`, `/ai-cli`, `/adv-review`. Live source is current (verified mid-2026). **Architecture mismatch:** these skills use Claude Code subagent dispatch (`Agent(subagent_type="codex:codex-rescue")`), which has no equivalent on the Grok host. The two are not portable across hosts. Naming this alternative matters because it's the nearest prior art — future readers should not think the design missed it.

## Consequences

**Positive:**
- Three uniform first-class sibling skills. Consumers (`/tp`, `/review`, `/red-team`) can invoke them symmetrically.
- Outcome labels with strict precedence give cross-model findings provenance.
- `/mmx` gains a capability `/agy` and `/codex` lack (web search via a third index) — it's a meaningful sibling, not a weaker chat-only echo.
- Fail-open contract is explicit: second-opinion skills never block the primary workflow.
- `host: grok` provenance tags from day one (per the global convention the user added 2026-07-18).

**Negative:**
- ~410 lines duplicated per skill until v0.2 partial-share refactor (if maintenance pain is observed).
- `/mmx` API-key mode requires a producer/consumer carve-out and a list of forbidden operations — added complexity that goes away if the user switches to OAuth.
- `/codex` host preflight adds a per-invocation step. Without it, the design would silently inherit `danger-full-access` from `~/.codex/config.toml`.

**Neutral:**
- The three skills do not share code with `/agy`. Drift is bounded by reviewer discipline, not by shared imports.
- `/tp critic` (parent investigation's recommendation) is explicitly out of scope. Revisit only if observed `/tp` sessions show framing-blind-spot failures a second model would have caught.

## Open Questions

The design lists 11 open questions with recommended defaults (Q1–Q6 from round 2, Q7–Q11 from round 3). User declined to answer and adopted all defaults. They remain documented in the design's `## Open Questions` section for revisitation:

1. Mirror vs shared conductor (Q1) — default: one skill per CLI.
2. `/codex` default model (Q2) — default: read from `~/.codex/config.toml`.
3. `/codex` v0.1 scope (Q3) — default: three modes.
4. `/codex` session resume (Q4) — default: defer (`--ephemeral` only).
5. `/codex` structured output (Q5) — default: free-form v0.1.
6. `/mmx` API-key enforcement strength (Q6) — default: explicit forbid in prose; permission check is v0.2.
7. `/mmx` auth method target (Q7) — default: OAuth preferred; API-key fallback.
8. `/mmx` search scope (Q8) — default: ship in v0.1.
9. `/mmx` stop_reason handling (Q9) — default: conductor maps `length`→`partial`, `content_filter`→`INVOCATION_FAILED`.
10. `sandbox_permissions` handling (Q10) — default: inject most-restrictive-safe override when permissive.
11. `/agy` retro-tagging with `host: grok` (Q11) — default: out of scope (tag at write time, not read time).

## Verification Plan

The design's PR plan specifies PR 0 (host preflight) before PR 1 can land. The PR 3 smoke-test includes 10 test cases, including:

- **Sandbox-leak regression test:** invoke `codex exec review --uncommitted` *without* the override. Confirm the host's `danger-full-access` default is observable via `codex doctor` during the run, and that the skill's prose would refuse to recommend this form.
- **API-key redaction test:** invoke `/mmx` against a sensitive target; verify the run record contains no plaintext API key.
- **OAuth-token read test:** confirm the conductor never reads `~/.codex/auth.json` directly.
- **Auth-refresh test:** trigger an OAuth token expiry and confirm the conductor runs `codex auth refresh` once before declaring `INVOCATION_FAILED`.
- **Windows `.cmd` shim regression test:** confirm `$mmxCmd` resolves to the node script on this host and that bare `mmx` is not invoked at runtime.
- **Fail-open test:** unset `PATH` for one invocation; confirm the primary workflow continues with `INVOCATION_FAILED`.

PR plan:

| PR | Title | Depends on |
|---|---|---|
| 0 | Host environment preflight (`preflight.md`) | — |
| 1 | `/codex` skill | PR 0 |
| 2 | `/mmx` skill | — |
| 3 | Smoke-test + family-contract validation | PR 1, PR 2 |
| 4 | Update `~/.grok/AGENTS.md` Multi-model tool availability section | PR 1, PR 2 |
| 5 | Optional: shared-conductor evaluation (deferred 1 month post-ship) | PR 1–4 |

## Follow-on work (not in scope for this ADR)

- **Rename `source-authority-discovery` skill to `preflight`** — **DONE 2026-07-20.** Skill directory renamed at both `P:\.agents\skills\preflight\` and `P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\skills\preflight\` (via `git mv`). References updated in: `P:\.claude\CLAUDE.md` (constitution), `P:\packages\.claude-marketplace\plugins\cc-skills-sdlc\CLAUDE.md`, `C:\Users\brsth\.grok\skills\grok-discovery\SKILL.md` + `run_discovery.ps1`, `C:\Users\brsth\.grok\skills\wargame\SKILL.md`, `C:\Users\brsth\.grok\skills\tp\protocol.md`, and `test_skill_contract.py`. Historical artifacts (`.artifacts\source-discovery-*.json`, session state JSONs, the 2026-07-19 red-team investigation doc) were intentionally left as-is — they are point-in-time records whose paths describe what was there at audit time.

## References

- **Authoritative design doc:** `~/.grok/design-runs/grok-design-6bf249df/grok-design-doc-6bf249df.md`
- **Review provenance:** `~/.grok/design-runs/grok-design-6bf249df/grok-design-review-6bf249df.md`
- **Discovery audit artifact:** `P:\tmp\source-discovery-mmx-codex-v2.json`
- **Canonical pattern:** `~/.grok/skills/agy/SKILL.md`
- **Parent investigation:** `P:\docs\tp-cognition-migration-2026-07-20\FINAL_REPORT.md`
- **Handoff (spec):** `P:\docs\grok-cross-model-skills-2026-07-20\HANDOFF.md`
- **Global provenance rule for `host:` tags:** `~/.grok/AGENTS.md` (Skill authoring host provenance section, 2026-07-18 audit)
- **Source-authority-discovery skill (used for this ADR's preflight, now renamed to `preflight`):** `P:\.agents\skills\preflight\SKILL.md`
- ADR-008 — "Compute, never hand-maintain" + "use the platform first" principles (carried into this ADR's "mirror `/agy`, don't reinvent" stance)
- ADR-007 — gate-discipline rule (referenced for any future warn→block rollout of skill enforcement behavior)
