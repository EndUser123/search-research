---
thread_id: design-skill-and-runtime-foundation-20260720
parent_handoff_path: none
current_session_id: 019f8082-9298-7561-b03e-3c21afc43115
current_terminal_id: console_fb11bbd2-b737-48d8-bbcc-d06b
produced_at: 2026-07-21T00:30:00Z
status: open
handoff_type: investigation
---

# HANDOFF — /design skill improvements + runtime enforcement foundation

## Goal (one sentence)

Improve the `/design` skill (write-review-revise loop with critical friend, wiki promotion, proper artifact lifecycle) and establish the runtime enforcement foundation for Grok Build (M1 observability, orphan plugin disposition, review skill consolidation).

## Last user message (verbatim)

> `/handoff "One file at P:/.artifacts/<termSafe>/handoff.md capturing: what shipped, what's pending, the two why-questions (F1/F2) the next session needs answered, the M1 disposition decision, and the cross-reference couplings. Without this, next session repeats the same reconstruction tax that M1 was supposed to eliminate."
> "why does proposal-grounding-monitor exist as orphan", I don't remember. Look in grok transcripts to find out.
> "why is cc-aca- disabled?", why would we enable it?
> "Recreated design docs at ~/.grok/design-runs/grok-design-10d0654e/", what's the issue? what's the recommendation?`

## What shipped (verified on disk)

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

## What's pending

### Foundation (P0 — blocks /design work)

| # | Item | Blocker | Answer |
|---|------|---------|--------|
| **F1** | Enable `proposal-grounding-monitor` (orphan plugin) | None — origin resolved (see below) | **READY TO ENABLE.** Built in session `019f7cc5` as part of cognition migration. Replaced `discovery-gate` (which over-blocked). 111 tests pass. Never enabled because the session ended before the final `/plugins → Space` step. Plugin is v0.1.0 observe-and-warn (never blocks). To enable: add to `~/.grok/config.toml [plugins] enabled` list or use `/plugins` TUI. |
| **F2** | cc-aca-* selective re-enable | Answered by user | **DON'T ENABLE.** The cc-aca-* plugins are Claude Code hook dispatch plugins. Under Grok Build (`compat.claude.hooks=false`), their hooks never fire. Enabling them loads code that never executes. The question is whether to port specific functionality (bulk-delete gate, investigation gate, verification gates) to Grok-native hooks — not whether to re-enable the plugins. |

### M1 disposition

**Recommendation: leave as candidate with 6 known bugs tracked.** The script works for its primary purpose (snapshot of active surface). The 6 bugs are real but non-blocking. Fix them in the next session or delegate to a cold-start LLM with the code review findings as input.

### Design docs at `~/.grok/design-runs/grok-design-10d0654e/`

**Recommendation: promote or delete.** The design is about cascade-of-trust (extend `_run_unverified_stance`), task pruning (3-mechanism SessionStart hook), and architectural principle (don't gate what the layer above gates). If you plan to implement: promote 2-3 Key Decisions to `P:/.data/wiki/concepts/` and delete the rest. If shelved: delete all 4. The location (`~/.grok/design-runs/`) is not git-tracked and will eventually be forgotten.

### /design work (P3 — blocked on foundation)

| # | Item | Blocked by |
|---|------|-----------|
| D1 | Observe-Before-Propose hook | F1 (if orphan is enabled, this is done) |
| D2 | Pre-flight stage (source-authority + wiki + internet) | D1 |
| D3 | Model selection rules for /design subagent fleet | D2 |
| D4 | Step 5.5 critical friend | Shipped, but untested |

### Explicitly deferred

| # | Item | Why deferred |
|---|------|-------------|
| X1 | `/tp` brainstorm mode | User instruction |
| X3 | Code graph (Tier 4) | User has a developing plan |
| X4 | LangGraph orchestrator for /design | Skeptical it's needed; revisit if /design grows multi-session |

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

## Key evidence

- Runtime audit: `P:/docs/runtime-enforcement-audit-2026-07-20.md`
- First /check: `P:/.artifacts/console_fb11bbd2-b737-48d8-bbcc-d06b/grok-check/20260720-115801-740/`
- Second /check: `P:/.artifacts/console_fb11bbd2-b737-48d8-bbcc-d06b/grok-check/20260720-142529-109/`
- Code review (5 lenses, 4 completed): `P:/.artifacts/console_fb11bbd2-b737-48d8-bbcc-d06b/grok-check/20260720-142529-109/results/`
- `proposal-grounding-monitor` README: `~/.grok/plugins/proposal-grounding-monitor/README.md`
- Plugin creation session: `019f7cc5-0767-76a2-a461-c2562bf1e91b`

## Recommended next actions (priority order)

1. **Enable `proposal-grounding-monitor`** — add to `config.toml [plugins] enabled`. Smoke-test by inducing an ungrounded proposal and checking for the systemMessage warning.
2. **Fix M1 bug #1** (hardcoded path in hook JSON) — change to relative or `${GROK_PLUGIN_ROOT}`.
3. **Decide design-docs disposition** — promote or delete.
4. **Run `/design` on something real and small** — validate Step 4.5, 5.5, 6.0, 6d work end-to-end.
5. **Then**: pre-flight stage (D2) + model selection (D3).

## Open questions for next session

- Should the 6 M1 code-review bugs be fixed in-session or delegated?
- Should `/tp` get a brainstorm mode for option generation before convergence?
- Should the `cc-aca-*` functionality (bulk-delete gate, investigation gate) be ported to Grok-native hooks? If so, which ones first?

## Other outstanding streams

- **CCR fleet work** (the original session topic from the prior session): the CCR admission proxy ceiling removal, dashboard fixes, auto-commit isolation. This session pivoted away from CCR to `/design` and runtime foundation. CCR work is parked but not closed.
- **Textual dashboard** (`ornith-monitor-textual.py`): written and tested (8 tests pass) but not activated. One-line change in `run-ornith-server.ps1`.
