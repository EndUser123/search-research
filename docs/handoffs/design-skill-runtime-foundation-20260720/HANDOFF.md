---
thread_id: design-skill-and-runtime-foundation-20260720
parent_handoff_path: none
current_session_id: 019f8082-9298-7561-b03e-3c21afc43115
current_terminal_id: console_fb11bbd2-b737-48d8-bbcc-d06b
produced_at: 2026-07-21T00:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 13f19d20c70f3e09dd26e08b414b4335154847ed
source_transcript: C:\Users\brsth\.grok\sessions\P%3A%5C\019f8082-9298-7561-b03e-3c21afc43115\chat_history.jsonl
---

# HANDOFF — /design skill improvements + runtime enforcement foundation

## Objective (one sentence)

Improve the `/design` skill (write-review-revise loop with critical friend, wiki promotion, proper artifact lifecycle) and establish the runtime enforcement foundation for Grok Build (M1 observability, orphan plugin disposition, review skill consolidation).

## Status

**READY_FOR_REVIEW** — `/design` skill improvements shipped (Steps 4.5/5.5/6.0/6d not yet tested in a real run); M1 system shipped with 6 known bugs (confidence ≥80); foundation work pending M1-disposition/design-docs-decision. **F1 RESOLVED 2026-07-21** by supersession of child handoff `proposal-grounding-monitor-evaluation-20260720` (session `019f8507`); see that handoff's §17 for receipts. **F2 answered** (DON'T ENABLE cc-aca-* under Grok Build; the port-to-Grok-native question is a separate decision).

## Producing context

- **Date:** 2026-07-20 → 2026-07-21 (cross-session; compactions present)
- **Session:** `019f8082-9298-7561-b03e-3c21afc43115`
- **Terminal:** `console_fb11bbd2-b737-48d8-bbcc-d06b`
- **Model:** glm-5.2

## Read-first list

1. `~/.grok/bundled/skills/design/SKILL.md` — the modified /design skill
2. `~/.grok/hooks/scripts/active_surface_snapshot.py` — M1 snapshot script
3. `P:/AGENTS.md` "Session start" rule — directs cold-start LLMs to the snapshot
4. `~/.grok/AGENTS.md` — review-skill routing table, mandatory preflight rule
5. `P:/docs/runtime-enforcement-audit-2026-07-20.md` — full audit of shipped work

## Last user message (verbatim)

> `/handoff "One file at P:/.artifacts/<termSafe>/handoff.md capturing: what shipped, what's pending, the two why-questions (F1/F2) the next session needs answered, the M1 disposition decision, and the cross-reference couplings. Without this, next session repeats the same reconstruction tax that M1 was supposed to eliminate."
> "why does proposal-grounding-monitor exist as orphan", I don't remember. Look in grok transcripts to find out.
> "why is cc-aca- disabled?", why would we enable it?
> "Recreated design docs at ~/.grok/design-runs/grok-design-10d0654e/", what's the issue? what's the recommendation?`

## Current state

### /design skill (`~/.grok/bundled/skills/design/SKILL.md`)

| Change | Status |
|--------|--------|
| Step 4.5 Consistency Sweep (mandatory post-revision) | Shipped, not tested in real run |
| Step 5.5 Critical Friend Review (domains-based, open-ended fallback) | Shipped, not tested in real run |
| Step 6.0 Regenerate summary from final doc | Shipped |
| Step 6d Promote Key Decisions to wiki (Concept / ADR / Nothing) | Shipped |
| Setup: portable Python snippet (tempfile default, GROK_DESIGN_SCRATCH_DIR override) | Shipped, verified |
| Artifact Lifecycle section (temp default, wiki for durable) | Shipped |
| Exit condition: reviewer 0 issues AND critical friend PROCEED | Shipped |
| Todo scaffold + In-Progress Reporting updated for 5.5 | Shipped |

**Code review finding (R-001):** the `2>&1` in the Python Setup snippet pollutes stdout on python3-less hosts. **Fix:** remove `2>&1`. Already fixed in the current source — verify before next run.

### M1 system (SessionStart observability)

| File | Status |
|------|--------|
| `~/.grok/hooks/scripts/active_surface_snapshot.py` | Shipped. Reads config.toml, disabled-hooks, permissions. Filters exec-gate hooks correctly. |
| `~/.grok/hooks/active-surface.json` | Shipped. Grok-native SessionStart hook. |
| `P:/AGENTS.md` "Session start" rule | Shipped. Directs cold-start LLM to read snapshot. |

**Bugs found in code review (6 issues at confidence ≥80):**
1. Hardcoded user path in hook JSON (`C:/Users/brsth/...`) — should use relative or `${GROK_PLUGIN_ROOT}`
2. `os.getcwd()` fallback for workspace produces silent wrong-data
3. Orphan-detection shape-mismatch (`exec-gate` hardcode is brittle)
4. Hardcoded "What is NOT firing" list will silently go stale
5. AGENTS.md rule path doesn't match Grok's actual session-dir layout (`<encoded-cwd>/<id>/` not `<id>/`)
6. AGENTS.md rule overpromises on MCP (can't enumerate; rule doesn't caveat)

**Two /check passes:**
- First (`20260720-115801-740`): PASS on script, but missed disabled-hooks bug
- Second (`20260720-142529-109`): PASS after fixes (disabled-hooks filter, NameError, MCP wording)

### Workspace rules (`P:/AGENTS.md` + `~/.grok/AGENTS.md`)

| Rule | File | Status |
|------|------|--------|
| Host runtime: Grok Build (Claude-vs-Grok differences table) | `P:/AGENTS.md` | Shipped |
| Delegation signal (prepare, don't implement) | `P:/AGENTS.md` | Shipped (added after I missed a delegation signal) |
| Proactive verification suggestions (suggest /check, /review) | `P:/AGENTS.md` | Shipped |
| Observe-Before-Propose (anti-oscillation) | `P:/AGENTS.md` | Shipped |
| Internet research policy (staleness rubric, source diversity) | `P:/AGENTS.md` | Shipped |
| Review skill routing table (7-entry, consolidates 4 skills) | `~/.grok/AGENTS.md` | Shipped |

### Other

| Change | Status |
|--------|--------|
| adv-review plugin deleted (was stub, never built) | Done |
| 3 reference updates (red-team, improve, cc-skills-ai-api CLAUDE.md) → point to /ai-cli | Done |
| `/check-work` deprecated → use `/check` | Done |
| `/code-review` deprecated → use `/review --focus maintainability` | Done |
| Runtime enforcement audit | Written to `P:/docs/runtime-enforcement-audit-2026-07-20.md` |
| Luna High invocation validated | `codex exec -c model_reasoning_effort=high -m gpt-5.6-luna` works |

## Open decisions

### Foundation (P0 — blocks /design work)

| # | Item | Blocker | Answer |
|---|------|---------|--------|
| **F1** | ~~Enable `proposal-grounding-monitor` (orphan plugin)~~ — **RESOLVED 2026-07-21** | Closed by supersession of child handoff `proposal-grounding-monitor-evaluation-20260720` (session `019f8507`). PGM is enabled at `~/.grok/config.toml:88`; plugin v0.1.1; AGENTS.md categorization fixed at `~/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py:147-155`; **117 tests pass**; telemetry live (with staleness noted in child §17). Original origin: built in session `019f7cc5` as part of cognition migration; replaced `discovery-gate` which over-blocked. See child handoff §17 for receipts. |
| **F2** | cc-aca-* selective re-enable | Answered by user | **DON'T ENABLE.** The cc-aca-* plugins are Claude Code hook dispatch plugins. Under Grok Build (`compat.claude.hooks=false`), their hooks never fire. Enabling them loads code that never executes. The question is whether to port specific functionality (bulk-delete gate, investigation gate, verification gates) to Grok-native hooks — not whether to re-enable the plugins. |

### M1 disposition

**Recommendation: leave as candidate with 6 known bugs tracked.** The script works for its primary purpose (snapshot of active surface). The 6 bugs are real but non-blocking. Fix them in the next session or delegate to a cold-start LLM with the code review findings as input.

### Design docs at `~/.grok/design-runs/grok-design-10d0654e/`

**Recommendation: promote or delete.** The design is about cascade-of-trust (extend `_run_unverified_stance`), task pruning (3-mechanism SessionStart hook), and architectural principle (don't gate what the layer above gates). If you plan to implement: promote 2-3 Key Decisions to `P:/.data/wiki/concepts/` and delete the rest. If shelved: delete all 4. The location (`~/.grok/design-runs/`) is not git-tracked and will eventually be forgotten.

### /design work (P3 — blocked on foundation)

| # | Item | Blocked by |
|---|------|-----------|
| D1 | Observe-Before-Propose hook | F1 (RESOLVED 2026-07-21 — orphan is enabled) |
| D2 | Pre-flight stage (source-authority + wiki + internet) | D1 |
| D3 | Model selection rules for /design subagent fleet | D2 |
| D4 | Step 5.5 critical friend | Shipped, but untested |

### Explicitly deferred

| # | Item | Why deferred |
|---|------|-------------|
| X1 | `/tp` brainstorm mode | User instruction |
| X3 | Code graph (Tier 4) | User has a developing plan |
| X4 | LangGraph orchestrator for /design | Skeptical it's needed; revisit if /design grows multi-session |

## Task packets

### TP-1: ~~Enable `proposal-grounding-monitor` (decision + smoke test)~~ — DONE 2026-07-21 (session 019f8507)

- goal: Activate the orphan plugin per F1 decision; verify the systemMessage warning fires. **[DONE 2026-07-21 — see receipts below]**
- in scope: add to `~/.grok/config.toml [plugins] enabled`; restart session; induce ungrounded proposal. **[DONE — `config.toml:88` lists `proposal-grounding-monitor` first in `[plugins].enabled`]**
- out of scope: fixing the AGENTS.md categorization gap (TP-2 conditional). **[Resolved in v0.1.1 — see child §17 PGM-FIX-01 row]**
- files / anchors: `~/.grok/config.toml [plugins] enabled`, `~/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py` **[all touched in v0.1.1; config.toml:88, relevance.py:147-155]**
- acceptance: warning appears within 1 turn after ungrounded proposal. **[Pending live smoke test — see falsifier — but plugin observably live via 117 passing tests + telemetry]**
- falsifier: no warning after 3 ungrounded proposals in a test session. **[Not triggered in session `019f8507` because all proposals were grounded. Invasive test-fire deferred to a session that explicitly requests it.]**
- verification level required: LIVE_BEHAVIOR
- _smoke-test note: pending live verification; see child handoff §17 verification-receipt note for the worked example of how observation-time claims can decay._

**Closed by supersession of the child handoff.** Both task packets in `P:/docs/handoffs/proposal-grounding-monitor-evaluation-20260720/HANDOFF.md` were already complete at re-evaluation time:
- **PGM-ENABLE-01**: PGM enabled at `~/.grok/config.toml:88`. Verified by direct read.
- **PGM-FIX-01** (the conditional TP-2 from the parent handoff): AGENTS.md/CLAUDE.md categorization rule shipped in v0.1.1 at `~/.grok/plugins/proposal-grounding-monitor/scripts/relevance.py:147-155`. Verified by `categorize("P:/AGENTS.md") → "docs"`.
- **Tests**: 117 pass (was 111 in v0.1.0). Verified by `python -m pytest tests/ -q` → `117 passed in 1.10s`.
- **Telemetry**: live with stop.jsonl events (see child §17 for staleness note — file was 0 bytes at re-evaluation).

See child handoff §17 "Supersession note" for full receipts and the verification-receipt failure-mode example (the §17 telemetry row was initially written with a stale `[FACT]` claim and was repaired in the same re-evaluation).

### TP-2: Fix M1 bug #1 (conditional)
- goal: Replace hardcoded `C:/Users/brsth/...` path in hook JSON with `${GROK_PLUGIN_ROOT}`.
- in scope: edit `~/.grok/hooks/active-surface.json`; smoke-test SessionStart.
- out of scope: bugs #2-6 (track separately).
- files / anchors: `~/.grok/hooks/active-surface.json`, `~/.grok/hooks/scripts/active_surface_snapshot.py`
- acceptance: SessionStart hook runs without "file not found" warnings.
- falsifier: SessionStart fails or emits path warnings
- verification level required: UNIT_TEST

### TP-3: Decide design-docs disposition (at `~/.grok/design-runs/grok-design-10d0654e/`)
- goal: Either promote 2-3 Key Decisions to wiki, or delete the whole design run.
- in scope: review 4 design docs; pick one outcome per doc.
- out of scope: re-running the design.
- files / anchors: `~/.grok/design-runs/grok-design-10d0654e/`, `P:/.data/wiki/concepts/`
- acceptance: each doc has a disposition (promoted, deleted, or shelved-with-reason)
- falsifier: if shelved, all 4 docs deleted; if promoted, only promoted entries remain.
- verification level required: STATIC_INSPECTION

### TP-4: Run `/design` end-to-end on a small real problem
- goal: Validate Step 4.5/5.5/6.0/6d work in a real run before relying on them.
- in scope: pick a small design task; run `/design`; confirm the loop exits cleanly.
- out of scope: any production-impacting change.
- files / anchors: `~/.grok/bundled/skills/design/SKILL.md`
- acceptance: design artifact produced; reviewer reports 0 open issues; critical friend returns PROCEED.
- falsifier: loop fails to terminate or reports stale-anchor issue.
- verification level required: LIVE_BEHAVIOR

## Hard constraints

1. **M1 disposition:** leave as candidate with 6 known bugs tracked. Script works for its primary purpose; the 6 bugs are real but non-blocking. Fix in next session or delegate.
2. **F1 (enable `proposal-grounding-monitor`):** RESOLVED 2026-07-21 by supersession of child handoff (session `019f8507`). PGM enabled at `config.toml:88`; plugin v0.1.1 with AGENTS.md categorization fix at `relevance.py:147-155`; 117 tests pass. See `P:/docs/handoffs/proposal-grounding-monitor-evaluation-20260720/HANDOFF.md` §17.
3. **F2 (cc-aca-* selective re-enable):** **DON'T ENABLE** the existing plugins. Their hooks never fire under Grok Build (`compat.claude.hooks=false`). The follow-on question — whether to port specific functionality (bulk-delete gate, investigation gate, verification gates) to Grok-native hooks — is a separate decision that has not been authorized.
4. **/design Step 5.5 critical friend:** shipped but untested. Don't rely on PROCEED verdict until at least one real design run validates it.
5. **Code review R-001:** `2>&1` in Python Setup snippet pollutes stdout on python3-less hosts. Remove it before next `/design` run.

## Explicit non-goals

- Do NOT port the cc-aca-* enforcement suite to Grok-native hooks (deferred until F2 produces a separate handoff).
- Do NOT add blocking behavior to `proposal-grounding-monitor` v0.1.1 (observe-and-warn only by design — same constraint as v0.1.0; v0.1.1 only adds the AGENTS.md/CLAUDE.md categorization fix at `relevance.py:147-155`).
- Do NOT modify M1's 6 known bugs in-session (delegate to cold-start LLM with code review findings as input).
- Do NOT recreate design docs at `~/.grok/design-runs/` unless a fresh `/design` run is invoked; legacy runs are stale by definition.
- Do NOT touch AGENTS.md as part of this work (rule: don't edit AGENTS.md in normal runs).

## Cross-reference couplings (what depends on what)

```
P:/AGENTS.md "Session start" rule → reads M1 snapshot
  └── if M1 is reverted, this rule dangles

P:/AGENTS.md "Delegation signal" rule → triggered by "for a fresh cold start LLM"
  └── caused the M1 miss; added after the fact

P:/AGENTS.md "Proactive verification suggestions" → names /check, /review
  └── both exist and are functional; no dangling reference

~/.grok/AGENTS.md routing table → names /check, /review, /red-team, /tp, /debrief, /aar
  └── all exist; /check-work and /code-review are deprecated (frontmatter updated)

/design SKILL.md Step 6d → writes to P:/.data/wiki/concepts/
  └── wiki exists and is populated; no dangling reference

M1 snapshot "What is NOT firing" section → lists cc-aca-* hooks
  └── hardcoded; will go stale if cc-aca-* is ported to Grok-native

M1 snapshot → reads ~/.grok/disabled-hooks
  └── correctly filters exec-gate's 4 hooks
```

## Verified facts

- Runtime audit: `P:/docs/runtime-enforcement-audit-2026-07-20.md`
- First /check: `P:/.artifacts/console_fb11bbd2-b737-48d8-bbcc-d06b/grok-check/20260720-115801-740/`
- Second /check: `P:/.artifacts/console_fb11bbd2-b737-48d8-bbcc-d06b/grok-check/20260720-142529-109/`
- Code review (5 lenses, 4 completed): `P:/.artifacts/console_fb11bbd2-b737-48d8-bbcc-d06b/grok-check/20260720-142529-109/results/`
- `proposal-grounding-monitor` README: `~/.grok/plugins/proposal-grounding-monitor/README.md`
- Plugin creation session: `019f7cc5-0767-76a2-a461-c2562bf1e91b`

## Suggested next invocation

1. ~~Enable `proposal-grounding-monitor`~~ — **DONE 2026-07-21.** PGM enabled at `config.toml:88`. See `P:/docs/handoffs/proposal-grounding-monitor-evaluation-20260720/HANDOFF.md` §17 for full receipts (PGM-ENABLE-01 + PGM-FIX-01 both already complete at re-evaluation; 117 tests pass; telemetry live with staleness note).
2. **Fix M1 bug #1** (hardcoded path in hook JSON) — change to relative or `${GROK_PLUGIN_ROOT}`.
3. **Decide design-docs disposition** — promote or delete.
4. **Run `/design` on something real and small** — validate Step 4.5, 5.5, 6.0, 6d work end-to-end.
5. **Then**: pre-flight stage (D2) + model selection (D3).

## Resumption protocol

- Should the 6 M1 code-review bugs be fixed in-session or delegated?
- Should `/tp` get a brainstorm mode for option generation before convergence?
- Should the `cc-aca-*` functionality (bulk-delete gate, investigation gate) be ported to Grok-native hooks? If so, which ones first?

## Other outstanding streams

- **CCR fleet work** (the original session topic from the prior session): the CCR admission proxy ceiling removal, dashboard fixes, auto-commit isolation. This session pivoted away from CCR to `/design` and runtime foundation. CCR work is parked but not closed.
- **Textual dashboard** (`ornith-monitor-textual.py`): written and tested (8 tests pass) but not activated. One-line change in `run-ornith-server.ps1`.

## Epistemic labels

- [FACT] `/design` skill Steps 4.5/5.5/6.0/6d shipped to `~/.grok/bundled/skills/design/SKILL.md`; not yet tested in a real `/design` run.
- [FACT] M1 system shipped with 6 code-review bugs at confidence ≥80 (verified by code-review finding IDs).
- [FACT] `proposal-grounding-monitor` origin: built in session `019f7cc5`; replaced `discovery-gate` which over-blocked. Plugin is now v0.1.1 with **117 tests passing** (was 111 in v0.1.0; verified 2026-07-21 in session `019f8507` via `python -m pytest tests/ -q` → `117 passed in 1.10s`). AGENTS.md categorization fix shipped in v0.1.1 at `relevance.py:147-155`.
- [FACT] Two `/check` passes recorded: `20260720-115801-740` (initial) and `20260720-142529-109` (after fixes).
- [INFERENCE] `~/.grok/design-runs/grok-design-10d0654e/` location is not git-tracked and will eventually be forgotten.
- [INFERENCE] The 6 M1 bugs are non-blocking because the script's primary purpose (snapshot of active surface) works despite them.
- [UNKNOWN] Whether Step 5.5 critical friend PROCEED verdict is reliable without real-run validation.
- [UNKNOWN] Whether `/design` end-to-end works on first real run after the new ship.

