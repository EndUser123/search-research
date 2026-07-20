# Runtime Enforcement Audit — Grok Build on P:\

**Date:** 2026-07-20
**Runtime:** Grok Build
**Auditor:** Claude (in-session, observed not proposed)
**Scope:** what enforcement is *actually firing* in this runtime, what's wired but inactive, what's orphaned, what depends on what.

---

## Method

Read observed state, not documented intent. Sources: `~/.grok/config.toml`, `~/.grok/settings.json`, `~/.claude/settings.json`, `P:/.claude/settings.json`, `~/.grok/plugins/`, `~/.grok/hooks/`, `~/.grok/plugin-data/`, `~/.grok/disabled-hooks/`, `~/.grok/installed-plugins/`, session terminal logs.

---

## Headline finding

**There is a fully-built Observe-Before-Propose plugin sitting orphaned in `~/.grok/plugins/proposal-grounding-monitor/` — never enabled, never fired.** It implements exactly the behavior I spent this session proposing to build from scratch. I proposed building a thing that already existed because I never observed the active runtime surface.

This audit exists to prevent repeating that failure.

---

## 1. What is actually firing in this runtime

### 1.1 Permissions (via Claude-compat rules path)

**Source:** `~/.grok/config.toml [compat.claude] rules = true` (line 32).
**Authority files:** `~/.claude/settings.json` + `P:/.claude/settings.json`.
**Effective state:**

- `~/.claude/settings.json:permissions.allow` — broad allows for Bash/Skill/Read/Edit on common paths
- `~/.claude/settings.json:permissions.deny` — catastrophic patterns only (`rm -rf /`, `format c:`, `chmod -R 777 /`, etc.)
- `~/.claude/settings.json:permissions.defaultMode = "acceptEdits"`
- `P:/.claude/settings.json:permissions` — additional allows + deny for recursive deletes (`*Remove-Item*-Recurse*-Force*`, `*rd /s*`, etc.) and PowerShell-specific patterns
- **Conflict noted:** the `Remove-Item -Recurse -Force` deny rule is the one that blocked me this session and the one I almost removed wrongly. It IS currently active and IS catching recursive deletes.

### 1.2 Hooks (Grok-native)

**Source:** `~/.grok/config.toml [plugins] enabled = [...]` + plugin `hooks/hooks.json` files.
**Active Grok-native plugins** (config.toml:76-83):

| Plugin | Origin | Purpose | Active? |
|--------|--------|---------|---------|
| `superpowers` | marketplace | Skill suite (brainstorming, TDD, systematic-debugging, etc.) | ✅ skills available |
| `firecrawl` | marketplace | Web scraping | ✅ |
| `superpowers-chrome` | marketplace | Chrome control | ✅ |
| `episodic-memory` | marketplace | Conversation memory | ✅ has `hooks/hooks.json` |
| `glm-plan-usage` | local | GLM quota | ✅ |
| `glm-plan-bug` | local | Bug reporting | ✅ |
| `user/24901107/exec-gate` | user path | Execution gate | ✅ has hooks (PreToolUse, UserPromptSubmit, SessionStart, SessionEnd) |

**Hooks from active plugins (verified by reading their `hooks/hooks.json`):**

- `exec-gate`: PreToolUse on `search_replace|write|run_terminal_command|spawn_subagent` → runs `gate.py`
- `exec-gate`: UserPromptSubmit → runs `authorize.py`
- `exec-gate`: SessionStart/End → runs `cleanup.py`
- `episodic-memory`: (not opened — node-based; trust the file name)

### 1.3 Permission rules in Claude settings (the actually-active set)

The compat path means Grok reads these. **Verified active.** This is what caught my `Remove-Item -Recurse -Force` calls this session.

---

## 2. What is wired but inactive

### 2.1 Claude Code hook dispatch path — DISABLED

**Source:** `~/.grok/config.toml [compat.claude] hooks = false` (line 31).

This means the extensive hooks block in `~/.claude/settings.json` (PreToolUse, Stop, PostToolUse, UserPromptSubmit, SessionStart, SessionEnd — 30+ hook entries wiring `cc-aca-safety`, `cc-aca-investigation`, `cc-aca-epistemic`, `cc-aca-authority`, `cc-aca-reasoning`, `cc-aca-sdlc`, `cc-skills-utils`, `cc-lazy-closure-debt`, `cc-model-router`, `cc-aca-session`, `cc-aca-observability`, `skill-guard`, `snapshot`, `prompt-enhancer`, plus the entire `P:/.claude/hooks/` tree) **is not firing in this runtime**.

That includes:
- `Stop.py` and the 38 in-process Stop gates
- `PreToolUse_bulk_delete_gate.py`
- `PreToolUse_investigation_gate.py`
- `Stop_verification_gate.py`
- `StopHook_cross_validator.py`
- `StopHook_unverified_stance.py`
- `proposal_critique_gate.py`
- All other `cc-aca-*` enforcement

### 2.2 The cc-aca-* plugin suite — DISABLED

**Source:** `~/.grok/config.toml [plugins] disabled = [...]` (lines 45-74).

Disabled plugins (28 entries): `cc-skills-ai-api`, `antigravity`, `cc-aca-authority`, `cc-aca-epistemic`, `cc-skills-analysis`, `cc-aca-investigation`, `cc-aca-observability`, `cc-aca-reasoning`, `cc-aca-safety`, `cc-aca-sdlc`, `cc-aca-session`, `cc-lazy-closure-debt`, `cc-model-router`, `cc-skills-architect`, `cc-skills-media`, `cc-skills-sdlc`, `cc-skills-thinking`, `cc-skills-utils`, `cc-skills-lab`, `codex`, `hookify`, `improve-partner`, `pi`, `ponytail`, `prompt-enhancer`, `quickstop`, `search-research`, `skill-guard`, `snapshot`.

This is a deliberate full disablement. The plugin source files still exist in `P:/packages/.claude-marketplace/plugins/` but they're not loaded.

---

## 3. What is orphaned

### 3.1 `proposal-grounding-monitor` — **the big finding**

**Location:** `~/.grok/plugins/proposal-grounding-monitor/`
**Status:** Not in `config.toml [plugins] enabled = [...]`, not in `disabled = [...]`. Just... sitting there.
**Evidence of never firing:** no telemetry files, no state files in `~/.grok/plugin-data/`, no entries in session logs.

**What it implements (read directly from source):**

| File | Role | Lines |
|------|------|-------|
| `plugin.json` | Manifest; v0.1.0; "v1 observes and warns; never blocks" | 4 |
| `hooks/hooks.json` | Grok-native hook wiring (Stop, PostToolUse, UserPromptSubmit, SessionStart, SessionEnd) | 1 |
| `scripts/posttool_track.py` | Records discovery evidence after `read_file`, `grep`, `list_dir`, `web_search`, `web_fetch`, `search_tool`, `use_tool` | 2 |
| `scripts/stop_detect.py` | Detects ungrounded proposals in assistant responses; opens "grounding repair"; emits `systemMessage` | 9 |
| `scripts/ups_remind.py` | UserPromptSubmit reminder when an open repair exists | 3 |
| `scripts/state.py` | Repair state machine (OPEN_GROUNDING_REPAIR → DISCOVERY_PERFORMED → resolved) | 1 |
| `scripts/relevance.py` | Proposal detection + qualifying-evidence classification | 1 |
| `scripts/cleanup.py` | SessionStart/End state cleanup | 9 |
| `tests/` | 8 test files (test_posttool, test_stop, test_relevance, test_replay, test_state, test_ups, test_controls, conftest) | ~35 |
| `replay/REPLAY_PROTOCOL.md` | Replay testing protocol | 3 |
| `durable-eval/` | (empty placeholder) | 0 |
| `.benchmarks/` | (empty placeholder) | 0 |
| `telemetry/` | (empty — never fired) | 0 |

**This is exactly the Observe-Before-Propose Stop hook** I spent this session proposing to design — and it's more sophisticated than what I was going to build. It has:

- The state machine I was going to invent (OPEN_GROUNDING_REPAIR → DISCOVERY_PERFORMED → resolved with outcome labels)
- The PostToolUse tracker I was going to compose (records `read_file|grep|list_dir|web_search|web_fetch|search_tool|use_tool` as evidence)
- The proposal detector I was going to write (`relevance.detect_proposal(response)`)
- The "v1 observes and warns; never blocks" tier I independently concluded was the right starting point
- The replay protocol I didn't think to add
- Tests I didn't think to write
- Telemetry I didn't think to add

### 3.2 `~/.grok/disabled-hooks/` directory

**Contents:** 1 file, 198 bytes. Not inspected. Likely contains hooks previously disabled via `/hooks` UI.

---

## 4. Dependency map

For each "thing I might want to port," what does it actually depend on?

| Capability | Source file | Requires | Status in Grok |
|------------|-------------|----------|----------------|
| Bulk-delete gate | `P:/packages/.claude-marketplace/plugins/cc-aca-safety/hooks/pretool/PreToolUse_bulk_delete_gate.py` | cc-aca-safety router (disabled), Python | Source exists but router disabled |
| Proposal critique gate | `P:/.claude/hooks/proposal_critique_gate.py` | `P:/.claude/hooks/Stop.py` dispatch chain (Claude-only) | Not wired |
| Stop verification gate | `P:/.claude/hooks/stop/Stop_verification_gate.py` | `P:/.claude/hooks/Stop.py` + `evidence_scope.py` | Not wired |
| Investigation gate | `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/pretool/PreToolUse_investigation_gate.py` | cc-aca-epistemic router (disabled), `state_paths.py`, transcript parser | Not wired |
| **Observe-Before-Propose / proposal grounding** | **`~/.grok/plugins/proposal-grounding-monitor/`** | **Nothing — self-contained, Grok-native shape** | **Orphan; not in enabled list** |
| Cross-validator | `P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/stop/StopHook_cross_validator.py` | cc-aca-epistemic router, evidence store | Not wired |
| Self-verification gate | `P:/.claude/hooks/PostToolUse_self_verification_gate.py` (if exists) | `P:/.claude/hooks/__lib/hook_runner.py` | Not wired |

**The only candidate that is (a) structurally wanted this session and (b) has zero external dependencies in Grok is `proposal-grounding-monitor`.** Everything else requires either re-enabling a disabled plugin suite or porting a hook to a different invocation model.

---

## 5. Active MCP servers

From session metadata: `chrome-devtools`, `minimax-search`, `tasks`, `web-search-prime`. These are the only MCP backends active in this runtime. Other MCP servers referenced in workspace docs (`perplexity`, `brave`, `tavily`, `exa`, `serena`, etc.) are NOT active.

`~/.grok/config.toml:1 disabled_mcp_servers = ["perplexity"]`.

---

## 6. The actual enforcement surface in this runtime, summarized

| Layer | Active in Grok Build? |
|-------|----------------------|
| Permission rules (Claude-compat) | ✅ Yes |
| Catastrophic-deny patterns | ✅ Yes |
| PreToolUse bulk-delete gate | ❌ No |
| Stop verification gates (38 of them) | ❌ No |
| Investigation gate (read-before-edit) | ❌ No |
| Proposal critique gate | ❌ No |
| Cross-validator / unverified-stance / semantic-critic | ❌ No |
| **Proposal-grounding-monitor (the Observe-Before-Propose hook)** | ❌ **No — orphan, never enabled** |
| Grok-native skills (superpowers, etc.) | ✅ Yes |
| Grok-native MCP servers (4) | ✅ Yes |

**This runtime has permission denials and skill dispatch. It does not have any of the verification/enforcement hooks the workspace's documentation describes.** Documentation and runtime diverged at the Claude→Grok migration and the divergence was never reconciled.

---

## 7. Strategic root causes (revised from the tactical list)

The tactical root causes I listed earlier (treating docs as authority, not checking compat flags, etc.) are symptoms. The strategic causes are:

### 7.1 The workspace has a documentation surface that describes a runtime that isn't running

`P:/.claude/CLAUDE.md` describes a constitution with 38 in-process Stop gates. `P:/.claude/hooks/HOOKS_CATALOG_v3.md` enumerates them. The `/check` skill references `preprocessor.py` and the evidence packet. The `/review` skill references specialist dispatch and verify passes. The `/design` SKILL.md (my own edits this session) references `Stop_verification_gate._has_verification_tools_this_turn` as a precedent for Observe-Before-Propose.

**None of those things are firing in this runtime.** The documentation is the artifact of a different runtime (Claude Code). New sessions read the docs, internalize the described enforcement, and propose changes that assume it — exactly as I did.

### 7.2 The migration from Claude Code to Grok Build is incomplete and untracked

`~/.grok/config.toml [compat.claude]` has per-artifact flags: `hooks = false`, `rules = true`, `skills = true`, `agents = true`, `mcps = true`. Each flag represents a migration decision. There's no manifest explaining why each was set the way it was, what's pending, what's deliberate.

The cc-aca-* plugins are ALL disabled — that's a coordinated disablement, not random. Either they were broken under Grok, or they were Claude-Code-specific, or the user hadn't gotten to porting them. I don't know which, and there's no document telling me.

### 7.3 Built-but-unshipped Grok-native work exists and isn't discoverable

`proposal-grounding-monitor` is a complete v1 implementation of the Observe-Before-Propose pattern. It exists in `~/.grok/plugins/`. It's not in the enabled list. There's no signal anywhere that says "this is built, pending activation" or "this is built, decided against" or "this is built, needs validation."

If this audit hadn't been commissioned, I would have built a worse version from scratch.

### 7.4 The runtime has no SessionStart observability artifact

Every session starts cold. The model has to reconstruct "what's firing?" from multiple config files, all of which are flavored toward different runtimes. There's no probe output that says "here is your actual active surface for THIS session."

---

## 8. Recommendations

These are recommendations, not implementations. Each one requires your decision before I act.

### R1 — Decide the disposition of `proposal-grounding-monitor`

The plugin exists, is Grok-native, implements Observe-Before-Propose better than my from-scratch version would have. Options:

- **Enable it as-is** — add to `config.toml [plugins] enabled`. Test by inducing an ungrounded proposal and checking for the `systemMessage` warning.
- **Read it thoroughly first** — I read `stop_detect.py` and `posttool_track.py`; haven't read `state.py`, `relevance.py`, `ups_remind.py`, `cleanup.py`, or any of the 8 test files. Validate quality before enabling.
- **Decide it was superseded** — if you wrote this and abandoned it for a reason, that reason is load-bearing.

I recommend read-thoroughly-then-enable, but I won't do either without your call.

### R2 — Decide whether to maintain the Claude-shape documentation

The workspace's `.claude/CLAUDE.md`, `.claude/hooks/HOOKS_CATALOG_v3.md`, and many SKILL.md files describe enforcement that isn't firing. Three options:

- **Mark as historical** — add a banner: "describes Claude Code enforcement; not active under Grok Build; see [runtime audit]."
- **Port the enforcement** — pick the gates that matter and re-implement them Grok-natively (proposal-grounding-monitor is the proof-of-concept).
- **Leave as-is** — accept that docs and runtime diverge; rely on session-start audits like this one to bridge.

### R3 — Add a SessionStart observability artifact

One file, written once per session by a Grok-native SessionStart hook, that enumerates the active enforcement surface. Format: JSON or markdown, written to `~/.grok/sessions/<id>/active-surface.md`. Contents: enabled plugins, active hooks (per event), active MCP servers, compat flags. The model reads this at session start instead of reconstructing from config files.

`exec-gate` already runs a SessionStart hook (`cleanup.py SessionStart`) — this could be the template.

### R4 — Write a migration manifest

A short document at `P:/.grok/MIGRATION.md` recording: "Active runtime: Grok Build. Compat path: rules only. Ported: X. Pending: Y. Deliberately dropped: Z. Orphan candidates: proposal-grounding-monitor." Future sessions read this first instead of guessing.

### R5 — Don't port any individual hook until R1 is resolved

The pattern of "let's port hook X" assumes we need to build. The reality is we have built-but-orphaned. Resolving orphans first is cheaper than building duplicates.

---

## 9. What I am NOT recommending

- I'm not recommending re-enabling the cc-aca-* suite wholesale. That's 28 plugins. Without knowing why they were disabled, re-enabling is reckless.
- I'm not recommending writing the Observe-Before-Propose hook from scratch. It exists.
- I'm not recommending more AGENTS.md rules right now. Adding rules I won't follow (proven this session) is theater.
- I'm not recommending any specific permissions changes — the deny-rule near-miss this session showed the rules ARE catching things; don't disturb without need.

---

## 10. The meta-finding

This audit was commissioned because I made verification errors while designing enforcement. The audit's biggest finding is that the enforcement I was designing already exists, unbuilt-but-orphaned, in the runtime I was claiming to inspect.

The strategic root cause is not "Claude needs to check more things." It's that the workspace has a runtime/docs gap, an incomplete migration, and undiscovered built work. Fixing those is leverage; adding more rules on top of the gap is decoration.

**Recommended next action: decide R1.** Everything else depends on it.
