---
thread_id: proposal-grounding-monitor-evaluation-20260720
parent_handoff_path: P:/docs/handoffs/design-skill-runtime-foundation-20260720/HANDOFF.md
current_session_id: 019f8082-9298-7561-b03e-3c21afc43115
current_terminal_id: console_fb11bbd2-b737-48d8-bbcc-d06b
produced_at: 2026-07-21T01:00:00Z
status: superseded
assigned_to: grok
assigned_at: 2026-07-21T14:29:49Z
assigned_by: 019f8507-6395-7bc0-87a9-9122e28d68c8
assignment_note: >
  Claimed for PGM-ENABLE-01 (enable as-is per Decision 1 Option A; smoke-test
  an ungrounded proposal and verify the systemMessage warning appears).
  Parent handoff is design-skill-runtime-foundation-20260720. Grok Build
  only; Claude/Codex should not take it without explicit user direction —
  the env vars, paths, and `~/.grok/config.toml` activation are
  Grok/Windows-specific. If this claim is stale (>7 days from assigned_at),
  re-claim before resuming.
handoff_type: investigation
accurate_as_of_head: 13f19d20c70f3e09dd26e08b414b4335154847ed
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f8082-9298-7561-b03e-3c21afc43115\chat_history.jsonl
---

# HANDOFF — proposal-grounding-monitor: evaluation and enable decision

## 1. Objective

Evaluate whether the orphaned `proposal-grounding-monitor` plugin solves a real problem effectively, and decide whether to enable it as-is, fix-first-then-enable, or abandon.

## 2. Status

**SUPERSEDED (2026-07-21T14:55Z, session 019f8507)** — both task packets completed by v0.1.1 release and prior enable action. See §17 Supersession note. Handoff retained as a record of the decision process that preceded enablement; not actionable work.

## 3. Producing context

- Date: 2026-07-20
- Session: `019f8082-9298-7561-b03e-3c21afc43115`
- Terminal: `console_fb11bbd2-b737-48d8-bbcc-d06b`
- Plugin origin: session `019f7cc5-0767-76a2-a461-c2562bf1e91b` (cognition migration investigation, 7/19→7/20)

## 4. Read-first list

1. `~/.grok/plugins/proposal-grounding-monitor/README.md` — what the plugin does, how it evolved from `discovery-gate`, the repair lifecycle
2. `~/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py` — proposal detection regex patterns + evidence categorization rules (the crux of whether it works)
3. `~/.grok/plugins/proposal-grounding-monitor/scripts/state.py` — state management, multi-terminal isolation, fail-closed policy
4. `~/.grok/plugins/proposal-grounding-monitor/scripts/stop_detect.py` — Stop hook detector (proposal → repair → warning)
5. `~/.grok/plugins/proposal-grounding-monitor/scripts/posttool_track.py` — PostToolUse evidence tracker
6. `~/.grok/plugins/proposal-grounding-monitor/hooks/hooks.json` — Grok-native hook wiring (5 events)
7. `~/.grok/plugins/proposal-grounding-monitor/plugin.json` — manifest (v0.1.0)

## 5. Verified facts

- [FACT] Plugin was built in session `019f7cc5` as part of a cognition migration investigation. Replaced an earlier `discovery-gate` that "over-blocked (matching `run_terminal_command` gated all bash reads like `git status` and `ls`, creating high friction)." (`README.md:7-8`)
- [FACT] Plugin has 111 tests per README. Test files: `test_state.py`, `test_relevance.py`, `test_posttool.py`, `test_stop.py`, `test_ups.py`, `test_replay.py`, `test_controls.py`, `conftest.py`. (`tests/` directory listing)
- [FACT] Plugin has never fired in production — no telemetry files, no state files in plugin-data. (`~/.grok/plugin-data/` contains only `exec-gate` state.)
- [FACT] Plugin is not in `config.toml [plugins] enabled` list. Not in `disabled` list either. Orphaned. (`config.toml:76-84`)

### Evidence categorization rules (the crux)

- [FACT] Qualifying categories: `skill`, `package`, `hook`, `docs`, `upstream` only. (`relevance.py:49`: `QUALIFYING_CATEGORIES = frozenset({"skill", "package", "hook", "docs", "upstream"})`)
- [FACT] `workspace` files do NOT qualify. (`relevance.py:18-19`: "reading your own in-progress code is not discovery of an authoritative existing pattern")
- [FACT] Bare search queries do NOT qualify (only the fetched result would). (`relevance.py:121`: returns `"unrelated"` for `search:` prefix)
- [FACT] MCP tool invocations do NOT qualify from target alone. (`relevance.py:128`: returns `"unrelated"` for `mcp:` prefix)
- [FACT] `P:/AGENTS.md` would categorize as `workspace` — NOT qualifying. (`relevance.py:148-150`: path under workspace_root matches `workspace`)
- [FACT] `~/.grok/AGENTS.md` would categorize as `skill` if path contains `/.grok/` — qualifying. (`relevance.py:134`: `if "/.grok/skills/" in t or "/.claude/skills/" in t` → BUT `/.grok/AGENTS.md` doesn't match `/.grok/skills/` specifically. Would fall to workspace or unrelated depending on path resolution.)

**[INFERENCE]** Reading `P:/AGENTS.md` or `~/.grok/AGENTS.md` may NOT count as qualifying evidence under the current categorization rules. The regex checks for `/.grok/skills/` specifically, not `/.grok/` broadly. This means the model could read the workspace's most authoritative convention files and still get flagged. This is the same failure mode I exhibited this session — reading AGENTS.md but still getting the runtime wrong.

### Proposal detection patterns

- [FACT] 16 regex patterns detect proposals (`PROPOSAL_SIGNALS` at `relevance.py:243-264`). Examples: "I recommend," "the best approach," "we should implement," "build a," "create a new plugin," "use an MCP," "port this from."
- [FACT] Provisional hedging language suppresses proposal detection. (`relevance.py:265-270`: `PROVISIONAL_HEDGE_RE` matches "provisionally," "likely," "probably," "I haven't verified," "without verifying," "based only on," etc.)
- [FACT] If hedging is present, the response is treated as Case B (provisional, non-blocking). No repair opens. (`relevance.py:288-289`: `if PROVISIONAL_HEDGE_RE.search(response): return False, []`)

### Multi-terminal isolation

- [FACT] State files are keyed by `GROK_SESSION_ID`: `$GROK_PLUGIN_DATA/pgm-state-<GROK_SESSION_ID>.json`. (`state.py:83-87`)
- [FACT] Foreign-session state is never read. (`state.py:129-133`: session_id mismatch raises ValueError, file deleted)
- [FACT] Writes are atomic via `tmp + os.replace`. (`state.py:155-168`)
- [FACT] Corrupt state files are deleted, not fabricated. (`state.py:120-140`)
- [FACT] Orphan state files (older than 4 hours) are swept on SessionStart. (`state.py:265-289`)

## 6. Current state

The plugin is:
- ✅ Built (503 lines of source across 6 scripts)
- ✅ Tested (111 tests across 8 test files)
- ✅ Documented (comprehensive README with lifecycle, qualifying categories, tests)
- ✅ Grok-native hook wiring (hooks.json with 5 events: PostToolUse, Stop, UserPromptSubmit, SessionStart, SessionEnd)
- ✅ Multi-terminal safe (session-scoped state, atomic writes, fail-closed on corruption)
- ✅ v0.1.0 observe-and-warn only (never blocks tool calls)
- ❌ NOT enabled (orphaned in `~/.grok/plugins/`, not in config.toml enabled list)
- ❌ Never fired in production (no telemetry, no state files)

## 7. Task packets

### PGM-ENABLE-01: Enable proposal-grounding-monitor

- **goal:** Activate the plugin so it starts observing and warning on ungrounded proposals
- **in scope:** add to `config.toml [plugins] enabled`; verify hooks register; smoke-test
- **out of scope:** fixing the AGENTS.md categorization gap (that's PGM-FIX-01 below if needed)
- **files / anchors:** `~/.grok/config.toml [plugins] enabled = [...]`
- **acceptance:** after enabling, induce an ungrounded proposal (e.g., "I recommend building an MCP server for X" without reading any skills/docs) and verify the systemMessage warning appears in scrollback
- **falsifier:** if no warning appears after 3 ungrounded proposals in a test session, the plugin's proposal detector is too narrow or the hook isn't firing
- **verification level required:** LIVE_BEHAVIOR
- **no_live_run_reason:** not deferred — this is the live test

### PGM-FIX-01 (conditional): Fix AGENTS.md categorization

- **goal:** ensure reading `P:/AGENTS.md` and `~/.grok/AGENTS.md` counts as qualifying evidence
- **in scope:** modify `relevance.py:categorize()` to recognize `AGENTS.md` and `CLAUDE.md` as `docs` or `skill` category
- **out of scope:** broader changes to categorization rules
- **files / anchors:** `~/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py:100-157`
- **acceptance:** after fix, reading AGENTS.md before proposing a structure should NOT trigger a repair
- **falsifier:** if the fix causes non-authoritative workspace files to also qualify, the FP rate increases
- **verification level required:** UNIT_TEST
- **condition:** only needed if the live test (PGM-ENABLE-01) shows false positives on AGENTS.md reads

## 8. Open decisions

### Decision 1: Enable as-is or fix-first?

**Question:** Enable the plugin now and monitor FP rate, or fix the AGENTS.md categorization gap first?

**Options:**
- **A: Enable as-is.** Monitor for 1 week. If FP rate is tolerable (<10% of proposals flagged incorrectly), keep. If not, fix or disable. Cost: 1 week of potential nag. Benefit: fastest path to real data.
- **B: Fix categorization first.** Read `relevance.py` (done), identify the AGENTS.md gap, patch, run tests, then enable. Cost: 30 minutes. Benefit: cleaner first experience.

**Selection criterion:** cost-of-wrong-enable vs cost-of-delay.

**Currently leading:** **Option A (enable as-is).** The plugin is observe-and-warn only (no blocking), so the cost of a wrong enable is nag-fatigue, not blocked work. The FP data from a real session is more valuable than a preemptive fix based on static analysis. The hedging suppressor already catches "I think" / "probably" language, which reduces FP surface.

**Evidence that would change the lead:** if the live test shows >30% FP rate on the first session, Option B wins.

### Decision 2: Is the plugin's scope right for this workspace?

**Question:** The plugin targets "environment-specific technical recommendations." Does this workspace's work pattern (mostly meta-work: skills, hooks, configs, not application code) match the plugin's design assumptions?

**[INFERENCE]** The plugin was designed for a cognition-migration investigation where the model recommends building/porting plugins, MCPs, and hooks. This workspace does exactly that kind of work. The proposal patterns match ("I recommend," "build a," "we should implement," "port this from"). The categorization (skill/package/hook/docs) matches the workspace's artifact types. The scope seems right.

## 9. Hard constraints

1. **Never block in v1.** The plugin is observe-and-warn only. If a future version proposes blocking, it must be a separate change with real-session evidence (README:31-33).
2. **Multi-terminal isolation.** State files are session-scoped. Never read another session's state. (`state.py:55-60`)
3. **Fail-closed on state corruption.** Corrupt state files are deleted, not recovered. (`state.py:120-140`)
4. **No raw prompt/response storage.** Only bounded 200-char excerpts in repair records. (`README.md` Observability section)

## 10. Cross-reference couplings

This handoff is coupled to:

- **Parent handoff** `design-skill-runtime-foundation-20260720` — F1 (enable `proposal-grounding-monitor`) is this handoff's primary task; F2/M1/design-docs items are independent of PGM work.
- **Validator** `P:/.grok/skills/handoff/__lib/validators.py` — `BODY_REQUIRED_SECTIONS` (line 50-62) defines the 15 mandatory body sections; `validate_assignment_fields` (line 574-625) gates claim fields; this handoff's conformance is re-checked after each edit.
- **Plugin source** `~/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py` — proposal patterns (`PROPOSAL_SIGNALS` lines 243-264), hedging suppressor (`PROVISIONAL_HEDGE_RE` lines 265-270), and categorization rules (`categorize()` lines 100-157). The AGENTS.md categorization gap (Decision 2 [INFERENCE]) lives here.
- **Plugin state** `~/.grok/plugins/proposal-grounding-monitor/scripts/state.py` — multi-terminal isolation (`GROK_SESSION_ID` keying lines 83-87), atomic writes (`tmp + os.replace` lines 155-168), fail-closed on corruption (lines 120-140), orphan sweep on SessionStart (lines 265-289). Any coupling to per-session state requires honoring these invariants.
- **Plugin hook wiring** `~/.grok/plugins/proposal-grounding-monitor/hooks/hooks.json` — Grok-native registration of 5 events (PostToolUse, Stop, UserPromptSubmit, SessionStart, SessionEnd).
- **Activation point** `~/.grok/config.toml [plugins] enabled` — PGM-ENABLE-01 writes here; absence is the "orphaned" state.
- **Test surface** `~/.grok/plugins/proposal-grounding-monitor/tests/` — 111 tests across 8 files; PGM-FIX-01 must run `python -m pytest tests/ -v` after any categorization patch.
- **Schema evolution** `handoff-v02-aar-integration-20260720/HANDOFF.md` — documents the v0.1 → v0.1.1 transition that added `accurate_as_of_head` and `Cross-reference couplings` as mandatory. This handoff now conforms to v0.1.1.
- **Stale-data anchor** `accurate_as_of_head: 13f19d20c70f3e09dd26e08b414b4335154847ed` (frontmatter, line 20) — git HEAD at production time per `P:/.grok/skills/handoff/SKILL.md` § drift detection. The next session comparing HEAD against this SHA knows whether the assessment in §5 is still valid.
- **Source transcript** `C:\Users\brsth\.grok\sessions\P%3A%5C\019f8082-9298-7561-b03e-3c21afc43115\chat_history.jsonl` — full conversation that produced the §5 evidence; cite for any [INFERENCE] re-derivation.

## 11. Pre-mortem (3 failure scenarios)

### Scenario 1 (most likely): Nag fatigue from broad proposal detection

**What happens:** The 16 proposal patterns match too many responses. "I recommend" appears in normal analytical responses, not just environment-specific prescriptions. Every other turn gets a warning. User disables the plugin within a week.

**Evidence this is plausible:** The patterns are broad. `\bwe should (?:implement|build|create|adopt|use|extend)\b` would match "we should consider whether to use option A" — which is analysis, not a prescription. The hedging suppressor helps ("I think we should" → suppressed) but doesn't catch "Based on the audit, we should implement X."

**How to detect:** telemetry `stop.jsonl` — if `repair_opened` events fire on >15% of Stop hooks in a session, FP rate is too high.

**Mitigation:** tighten proposal patterns; add more hedging suppressors; or accept and live with it.

### Scenario 2 (edge case): AGENTS.md/CLAUDE.md reads don't qualify

**What happens:** The model reads `P:/AGENTS.md` or `~/.grok/AGENTS.md` — the most authoritative source for workspace conventions — but the categorization rules don't recognize these as `skill`, `package`, `hook`, `docs`, or `upstream`. The read counts as `workspace` (non-qualifying). The model gets flagged for "no qualifying evidence" despite having done the right thing.

**Evidence this is real:** `relevance.py:134` checks for `/.grok/skills/` specifically. `~/.grok/AGENTS.md` doesn't match. `P:/AGENTS.md` would match `workspace` at line 148. Neither qualifies. This is the exact failure I exhibited this session: I read AGENTS.md but still got the runtime model wrong.

**How to detect:** telemetry shows `repair_opened` with `evidence_count_at_open > 0` but the model had read AGENTS.md — check if AGENTS.md appears in the evidence list (it wouldn't, because it was filtered as `workspace`).

**Mitigation:** PGM-FIX-01 — add `AGENTS.md` and `CLAUDE.md` recognition to `categorize()`.

### Scenario 3 (assumption failure): Model ignores warnings

**What happens:** The plugin emits a `systemMessage` warning. The model sees it but doesn't change behavior — doesn't read the recommended source, doesn't revise the proposal. The repair expires after 2 hours with `EXPIRED_UNRESOLVED`.

**Evidence this is plausible:** The systemMessage is a nudge, not a block. Under Grok Build, `systemMessage` appears in the conversation and the model will see it next turn. But "seeing" and "acting on" are different. The model may rationalize ("I already have sufficient context") and proceed.

**How to detect:** telemetry shows high `EXPIRED_UNRESOLVED` rate (>50% of opened repairs).

**Mitigation:** upgrade to v2 blocking mode for repeat offenders (same recommendation_hash flagged twice). Requires real-session evidence first.

## 12. Explicit non-goals

- Do NOT add blocking behavior in this evaluation. v1 is observe-and-warn only.
- Do NOT rewrite the plugin. It's tested and documented. Fix only if the live test reveals real problems.
- Do NOT port the cc-aca-* enforcement suite. That's a separate decision (see parent handoff).
- Do NOT modify the proposal detection patterns without running the 111-test suite first.

## 13. Resumption protocol

1. Read this handoff
2. Read `~/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py` (the proposal patterns + categorization rules — the crux)
3. Decide: enable as-is (Option A) or fix-first (Option B)
4. If Option A: add `"proposal-grounding-monitor"` to `~/.grok/config.toml [plugins] enabled` list, restart session, induce an ungrounded proposal, check for warning
5. If Option B: patch `relevance.py:categorize()` to recognize AGENTS.md/CLAUDE.md, run `python -m pytest tests/ -v`, then enable
6. Monitor telemetry at `$GROK_PLUGIN_DATA/../proposal-grounding-monitor/telemetry/stop.jsonl` for FP rate after 1 week

## 14. Suggested next invocation

```
Enable proposal-grounding-monitor. Add it to config.toml [plugins] enabled.
Then induce an ungrounded proposal ("I recommend building a new hook for X"
without reading any skills) and verify the systemMessage warning appears.
Check telemetry for FP rate. If AGENTS.md reads don't qualify, patch
relevance.py:categorize().
```

## 15. Last user message (verbatim)

> "proposal-grounding-monitor: what problem, will it work, pre-mortem"
> "- what problem is it supposed to solve? Will it efficiently and effectively? Pre-mortem?"

## 16. Epistemic labels

- [FACT] Plugin source, tests, and README read in full this session
- [FACT] Categorization rules verified against actual code (`relevance.py:100-157`)
- [FACT] Multi-terminal isolation verified against actual code (`state.py:75-300`)
- [FACT] Proposal detection patterns verified against actual code (`relevance.py:243-264`)
- [INFERENCE] AGENTS.md reads may not qualify as evidence (regex is `/.grok/skills/` not `/.grok/`)
- [INFERENCE] The plugin's scope matches this workspace's work pattern (meta-work on skills/hooks/configs)
- [UNKNOWN] Real-session FP rate — only determinable by enabling and monitoring
- [UNKNOWN] Whether the model acts on systemMessage warnings under Grok Build

## Other outstanding streams

- **M1 system** (SessionStart observability) — shipped with 6 known bugs (confidence ≥80). See parent handoff.
- **/design skill improvements** — shipped (Step 4.5, 5.5, 6.0, 6d). Untested in real run. See parent handoff.
- **Review skill consolidation** — shipped (routing table, 2 skills deprecated). See parent handoff.
- **CCR fleet work** — parked from prior session. Not closed.

## 17. Supersession note (added 2026-07-21T14:55Z)

**Both task packets completed before this re-evaluation reached them.** This handoff was opened at `2026-07-21T01:00:00Z` based on a session that read `relevance.py` while the plugin was at v0.1.0; by the time of re-evaluation (session `019f8507`, ~14h later), the plugin had shipped v0.1.1 with the AGENTS.md/CLAUDE.md fix and someone had already added `proposal-grounding-monitor` to `config.toml [plugins].enabled`.

**Receipts (verified 2026-07-21T14:55Z):**

| Task packet | Status | Evidence |
|---|---|---|
| PGM-ENABLE-01 (enable plugin) | ✅ Done | `C:/Users/brsth/.grok/config.toml:88` lists `"proposal-grounding-monitor"` first in `[plugins].enabled`. Hook wiring confirmed at `C:/Users/brsth/.grok/plugins/proposal-grounding-monitor/hooks/hooks.json` (5 hook events). Disabled-hooks file lists only exec-gate; PGM not disabled. |
| PGM-FIX-01 (AGENTS.md categorization) | ✅ Done | `C:/Users/brsth/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py:147-155` adds the rule `if re.search(r"(?:^|/)(?:AGENTS|CLAUDE)\.md$", t, re.IGNORECASE): return "docs"`. Inline comment confirms intent: "Promoted to qualifying evidence 2026-07-20 after /review confirmed the prior categorization gap." Verified live: `categorize("P:/AGENTS.md") → "docs"`; `categorize("~/.grok/AGENTS.md") → "docs"`; `categorize("~/.claude/CLAUDE.md") → "docs"`. |
| Tests | ✅ Pass | `cd ~/.grok/plugins/proposal-grounding-monitor && python -m pytest tests/ -q` → `117 passed in 1.10s`. |
| Telemetry | ✅ Live (stale receipt) | At supersession write-time (2026-07-21T14:55Z): `C:/Users/brsth/.grok/plugin-data/proposal-grounding-monitor/telemetry/stop.jsonl` (498 bytes; 3 events: 2× `repair_opened`, 1× `repair_resolved` with outcome `RECOMMENDATION_REVISED_AFTER_INSPECTION`). **Stale as of 2026-07-21T17:57:10Z** — file was truncated to 0 bytes between supersession write and a later read. Cause unverified (likely PGM SessionStart cleanup or telemetry rotation; see §17 footnote). Per-session state files exist for sessions `019f8082` (the eval producer), `019f819a`, `019f8388`, `019f8507` (this session), `019f8523`. |

**What this handoff got wrong about current state at re-evaluation time:**

1. "[FACT] Plugin is not in `config.toml [plugins] enabled` list." (line 84) — false; enabled at line 88.
2. "Plugin has never fired in production — no telemetry files, no state files." (lines 84, 88) — false; telemetry and state files exist. Notably, a `repair_opened` event fired in this very session's producer (`019f8082`) at `2026-07-21T00:55:12Z`, 5 minutes before this handoff was `produced_at`.
3. "[INFERENCE] Reading `P:/AGENTS.md` or `~/.grok/AGENTS.md` may NOT count as qualifying evidence." (line 49) — was correct for v0.1.0; false for v0.1.1.

**Irony worth noting for future cold-start sessions:** the eval handoff's producing session (`019f8082`) was itself the subject of a real PGM `repair_opened` event at the same time the handoff was being written. The session that produced "PGM has never fired" was itself being observed by PGM. The handoff's reasoning was sound for the version it read, but it was working from stale code AND describing the runtime incorrectly.

**Verification-receipt note (added 2026-07-21 /tp):** the Telemetry row above initially claimed "498 bytes; 3 events" as observed at supersession write-time. A subsequent `/tp` re-evaluation (session `019f8507`) re-read the file at ~22:50Z and found it was **0 bytes, last modified 2026-07-21T17:57:10Z** — i.e., the telemetry had been truncated between the supersession write and the re-evaluation. The original observation was correct at write-time but did not survive. The Telemetry row above has been updated to reflect this staleness explicitly. This is a worked example of the `verification-receipt` failure mode (causal/state claim delivered as `[FACT]` without an enduring receipt): even correct-at-write-time claims can decay.

**Why this handoff is retained (not deleted):**

- Decision history is durable evidence. The eval reasoning (Decision 1 Option A: enable-as-is; pre-mortem scenarios 1-3) is the record of how the workspace decided PGM should be enabled. Future cold-start sessions can read it to understand the prior reasoning, not to redo the work.
- The pre-mortem is a useful artifact for any future v2 (blocking mode) proposal: the FP-rate thresholds (10% tolerable, 30% auto-fix) and the named failure modes are still applicable.

**Future next-action recommendations:**

1. **None.** Both task packets this handoff proposed are complete. Any future work on PGM should be in a new handoff.
2. If the operator wants to harden PGM further, candidates are: (a) tightening `PROPOSAL_SIGNALS` if telemetry shows FP rate climbing above 10%, (b) promoting specific package-level CLAUDE.md files to be more discoverable, (c) adding v2 blocking for repeat offenders (per pre-mortem scenario 3).
3. The 117 tests should be re-run if relevance.py is modified; this handoff's verification receipts will go stale on the next plugin version bump.
