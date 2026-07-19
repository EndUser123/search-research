# Red-team plugin — full source-authority investigation

| Field | Value |
|---|---|
| **Date** | 2026-07-19 |
| **Trigger** | User: "do a full investigation of what we are working with. how can we safely add/remove features? what are the 2nd order effects on files?" |
| **Skill invoked** | `source-authority-discovery` (`P:/.agents/skills/source-authority-discovery/SKILL.md`) |
| **Audit script** | `discovery_audit.py` started but killed at 245s on broad scope (`--max-files 50000` across 5 roots); manual map below is more targeted and complete |
| **Status** | Investigation complete. Findings + safe-add/remove playbook below. No changes made. |

---

## 1. What we are working with — the inventory

### 1.1 Canonical source (single root)

`P:/packages/.claude-marketplace/plugins/red-team/` — 25 files:

| Path | Role |
|---|---|
| `.claude-plugin/plugin.json` | Manifest, version `0.2.18` |
| `CLAUDE.md` | Package-local instructions |
| `commands/red-team.md` | **Orchestrator entry point + dispatch loop + verdict format** (~470 lines). This is the file the previous review's "Priority 1" should have targeted. |
| `agents/red-team-{planner,claim-refuter,critic,gate-reviewer,workflow-reviewer,security,performance,logic,state,failure-modes,plugin,testing}.md` | 12 specialist/critic agent prompts |
| `__lib/findings_schema.py` | Pure-logic schema validator for specialist output |
| `__lib/telemetry.py` | Telemetry writer CLI (`commit`, `recent`) |
| `__lib/telemetry_schema.py` | Schema validators for telemetry + incidents |
| `__lib/incidents.py` | Incident writer CLI (`add`, `list`, `resolve`, `convert`) |
| `tests/{conftest,test_claim_refute_schema,test_enablement,test_findings_schema,test_incidents,test_smoke_resolution,test_telemetry}.py` | 6 test files |

### 1.2 Registration layers (4 distinct surfaces)

| Layer | Path | Value | Verified |
|---|---|---|---|
| Plugin manifest | `plugins/red-team/.claude-plugin/plugin.json` | `version: "0.2.18"` | ✓ |
| Marketplace registry | `P:/packages/.claude-marketplace/marketplace.json:324-331` | `version: "0.2.17"` ← **drift** | ✓ |
| User enablement | `C:/Users/brsth/.claude/settings.json:363` | `"red-team@local": true` | ✓ |
| Version-keyed cache | `C:/Users/brsth/.claude/plugins/cache/local/red-team/0.2.18/` | 25 files mirroring source | ✓ |

**Drift finding:** marketplace.json is one version behind the manifest. Not functionally broken (cache is keyed off the manifest version, not marketplace), but the marketplace description is stale.

### 1.3 Runtime state (written by the plugin, never edited by hand)

| Path | Writer | Reader |
|---|---|---|
| `P:/.claude/state/red-team/telemetry.jsonl` | `telemetry.py commit` | `telemetry.py recent`; Phase 3b improvement workflow (unbuilt) |
| `P:/.claude/state/red-team/incidents.jsonl` | `incidents.py add` | `incidents.py list`; Phase 3b |
| `P:/.claude/.artifacts/{session_id}/red-team/{YYYYMMDD-HHMMSS}/` | Orchestrator (creates run_dir) | Critic, telemetry, incidents |
| Per-run files: `_run.json`, `proposal.md`, `prospect.md`, `claims.json`, `{specialist}.json`, `critic.json` | Respective agent | Next-stage agent / critic |

### 1.4 Cross-references — who depends on red-team

This is the most important table for safe-add/remove decisions. Every entry below reads or invokes red-team in some way.

| Consumer | Path | Dependency | Strength |
|---|---|---|---|
| **`/debrief` chain mode** | `cc-skills-analysis/skills/debrief/` | Pipeline step: `recap→gaps→friction→**red-team**→rns→SCORES` | Strong — chain mode invokes `/red-team` as a stage |
| **`/rns`** | (referenced in compactions) | Self-describes as "red-teamed next steps" | Weak — naming only |
| **`/improve external-second-opinion`** | `improve-partner/` | Planned backend is `/red-team adversarial` (PENDING tasks #872-874) | Future-tense — not yet wired |
| **`/risks`** | `cc-skills-sdlc/skills/risks/` | Documents its own boundary; escalates to `/red-team` | Documentation only |
| **`/check`** | `cc-skills-lab/` | Documented escalation path `/check → /risks → /red-team` | Documentation only |
| **`promotion_opportunity.schema.json`** | `P:/packages/.claude-marketplace/shared/schemas/` | `source_workflow` enum includes `"red-team"` | Strong — schema contract |
| **`completion-evidence-contract.md`** | `P:/.data/wiki/concepts/` | Names `/red-team` Pre-check 0 as the runtime BLOCK authority | Documentation |
| **Adjacent: `/adversarial-review` agent** | `P:/.claude/agents/adversarial-review.md` | Different shape (file:line code review); **not** the same as `/red-team adversarial` mode | Distinct — do not confuse |
| **Adjacent: `/code-review`** | claude-plugins-official | Routine code review; `/red-team` documents the boundary | Distinct |
| **Docs (8 files)** | `P:/docs/{sdlc-experience-refactor-design,consolidation-acceptance-checklist,sdlc-target-operating-model,sdlc-audit-final-corrected-packet,research-run-v1-phase1-multicaller-rollout,next-workstream-evaluation,HANDOFF-mechanism-manifest-202607-04,external-reviewer-preamble}.md` | Cite `/red-team` in command-set rosters and escalation tables | Documentation only |
| **Competing plan** | `P:/docs/superpowers/plans/2026-07-12-lazy-provenance-and-evidence-pipeline.md` Task 4 Step 4 | **Wants to modify `commands/red-team.md`** to treat unsupported "tested/validated" claims as findings | **Active overlap** — must reconcile before editing red-team.md |

### 1.5 Worktrees (none red-team-specific)

13 worktrees exist under `P:\worktrees\` and `P:\.claude\worktrees\`. None are named for red-team work; none were created this session. Safe to ignore for red-team changes.

### 1.6 Grok-side copies

**None.** Searched `C:/Users/brsth/.grok/skills/` and `installed-plugins/` for `*red-team*`: zero hits. Unlike the `/wiki` skill (which has dual Grok+Claude sources — see prior critic.json WRF-001), `/red-team` is single-source. This is good: no dual-edit hazard.

---

## 2. Contracts and invariants (what must not break)

These are the load-bearing contracts. Any feature add/remove must preserve them.

### 2.1 Disk-backed handoff (the central invariant)

- Orchestrator holds **only file paths**, never findings content.
- Specialists write `{run_dir}/{specialist}.json` per the findings schema.
- Critic globs `{run_dir}/*.json`, reads each, aggregates.
- **Why:** keeps the long-lived orchestrator context small. Documented as "non-negotiable" in `plugins/red-team/CLAUDE.md:20` and `commands/red-team.md:111`.

### 2.2 Findings schema (codified)

From `__lib/findings_schema.py`:

```python
REQUIRED_FINDING_FIELDS = ("id", "severity", "location", "title", "detail", "evidence", "fix")
VALID_SEVERITIES = ("BLOCK", "REVISE", "NIT")
VALID_CLAIM_TYPES = ("existence", "static-shape", "behavior", "non-code", "scope-completeness")
```

The schema validator reads the `findings` array (line 38): `findings_obj.get("findings")`.

### 2.3 Verdict gate (exhaustive)

`agents/red-team-critic.md` Step 4 — every severity combination maps to exactly one of PROCEED / REVISE / BLOCK. FM-3 makes empty input → BLOCK (no self-approval).

### 2.4 Cache-freshness invariant (test-enforced)

`tests/test_smoke_resolution.py` asserts the cache at `~/.claude/plugins/cache/local/red-team/*/commands/red-team.md` exists. `tests/test_enablement.py` asserts `red-team@local: true` is in settings.json. Any source edit must be followed by version-bump + cache refresh, or these tests fail on next run.

### 2.5 Self-review mode (3 hard requirements)

When the target is the orchestrator's own prior output: claim-refute is mandatory, every scope-completeness claim needs repo-wide grep, and `gate-reviewer` + `workflow-reviewer` cannot be DEFERRED.

### 2.6 Read-only-`/red-team` constraint

Two independent docs (`superpowers/plans/2026-07-12-lazy-provenance-and-evidence-pipeline.md:15,148` and `consolidation-acceptance-checklist.md`) declare `/red-team` must remain read-only — it must not create project files outside its own `run_dir` / state paths.

---

## 3. Bugs and drift discovered during this investigation

### 3.1 BLOCK-class — producer/consumer schema drift (counts always or sometimes 0)

**The full picture (deeper than the prior handoff's diagnosis):**

| Layer | Field name used | Source |
|---|---|---|
| Specialist writer contract | `findings` | `commands/red-team.md:122` schema doc |
| Schema validator | `findings` | `findings_schema.py:38` |
| Telemetry parser | `findings` | `telemetry.py:94` |
| Test fixtures | `findings` | `test_telemetry.py:82-89`, `test_findings_schema.py:18` |
| **Critic output** | **`verified_findings`** | `critic.json` (this run + pattern in others) |

The critic prompt's "Output format" section (`agents/red-team-critic.md:70-82`) uses a heading "**### Verified findings**" — the critic naturally serializes this as `verified_findings`. Every consumer expects `findings`. Result: `counts` is silently `{}` for any critic.json that follows the prompt's heading naming.

**Why some prior runs have correct counts** (e.g. `20260708-193119` showed `BLOCK:2, REVISE:11`): those critics happened to use `findings` as the field name. The prompt doesn't pin the field name; the critic picks one version or the other per run. Intermittent, not universal.

**Two fix options:**
- **Option α (producer-side, root cause):** edit `agents/red-team-critic.md` to specify the JSON field name as `findings`. Existing critic.json files in the field stay readable only if the parser is also tolerant.
- **Option β (consumer-side, tolerant):** change `telemetry.py:94` and `findings_schema.py:38` to `obj.get("findings") or obj.get("verified_findings") or []`. Backward-compatible with every existing critic.json.

**Recommendation:** Option β first (one-line, backward-compatible, unblocks telemetry clustering), then Option α as a follow-up to standardize. Doing α alone orphans every existing critic.json.

### 3.2 REVISE — stale doc: "Project-local specialists (under `P:/.claude/agents/`)"

`commands/red-team.md:168` says specialists live at `P:/.claude/agents/`. Verified: **no `red-team-*` files exist there**. The 12 specialists live in the plugin's own `agents/` directory. The `P:/.claude/agents/adversarial-*` files are the older `/adv-review` agent set, distinct from red-team specialists.

**Fix:** one-line edit to `commands/red-team.md:168` to point at the plugin's own `agents/`.

### 3.3 REVISE — marketplace.json version drift

`marketplace.json:326` declares `0.2.17`; `plugin.json` declares `0.2.18`. Functional impact: none (cache is keyed off plugin.json). Hygiene impact: marketplace UI/description lags.

**Fix:** bump marketplace.json to `0.2.18` (or current) at next version-bump cycle.

### 3.4 NIT — ad-hoc `post_run_correction` field in telemetry

The latest telemetry row carries a `post_run_correction` field not present in `telemetry_schema.py`. The handoff author added it ad-hoc. It validates because `validate_telemetry` only checks required fields + types of known fields; unknown fields pass through.

**Fix:** either add `post_run_correction` to the schema formally, or strip it from the row.

### 3.5 Competing plan overlap (BLOCK-class for safe editing)

`P:/docs/superpowers/plans/2026-07-12-lazy-provenance-and-evidence-pipeline.md` Task 4 Step 4 says:

> Modify `P:/packages/.claude-marketplace/plugins/red-team/commands/red-team.md`: treat unsupported "tested," "accepted," "validated," or "deployed" claims as findings.

Reading the current `commands/red-team.md` §"Knowledge and validation provenance" (lines 72-86): **this is already implemented.** The plan's Step 4 may be stale, or may want stronger language. Either way, this plan owns an edit to the same file any new fix would touch. Reconcile before editing.

---

## 4. Safe-add / safe-remove playbook

### 4.1 Safe-add — what's cheap and reversible

| Change | Reversibility | Required steps |
|---|---|---|
| New specialist agent (e.g. `red-team-observability`) | High — additive | (1) Create `agents/red-team-<name>.md` following `red-team-state.md` pattern. (2) Add dispatch row in `commands/red-team.md` §"### 2. Specialists". (3) Bump `plugin.json` version. (4) Run `plugin-audit-and-fix.py --bump red-team`. (5) Run `pytest tests/`. (6) Smoke-test `/red-team:red-team` resolves. |
| New `__lib/*.py` helper | High | Create file + unit test in `tests/`. Version bump + cache refresh. No registration changes if it's called only from existing files. |
| New telemetry field | Medium — schema change | (1) Add to `telemetry_schema.py` validators. (2) Update `commit()` writer. (3) Update tests. (4) Decide on backfill for prior rows (default: leave as absent — readers must tolerate missing field). |
| New incident category | Medium | Add to `VALID_INCIDENT_CATEGORIES` in `telemetry_schema.py`. Update tests. Document in `commands/red-team.md` §"Override-pattern incident capture". |
| New CLI subcommand on telemetry/incidents | High | Add subparser in `main()`. Add tests. |

### 4.2 Safe-remove — what's expensive and what's not

| Change | Reversibility | Cascade |
|---|---|---|
| Drop a specialist agent (e.g. retire `red-team-plugin`) | Medium | (1) Remove dispatch row in `commands/red-team.md`. (2) Delete `agents/red-team-<name>.md`. (3) Search for cross-references in docs (no consumer reads specialist files directly except the critic via glob — glob is permissive). (4) Existing run_dirs that invoked the specialist still parse; their `{specialist}.json` files become orphans. |
| Drop telemetry/incidents entirely | Low — loses state history | Touches `commands/red-team.md` §"Self-Improvement Directive", `CLAUDE.md`, the `__lib/` Python files, the tests, and the schema references. Also orphans `P:/.claude/state/red-team/` data. |
| Drop a mode (`pre-mortem`, `adversarial`) | Medium | Each mode has documented absorption history. Removing `pre-mortem` mode breaks `/pre-mortem`'s deprecation-stub routing (it currently routes into `/red-team pre-mortem`). Removing `adversarial` mode orphans tasks #872-874 and the `/improve external-second-opinion` planned backend. |
| Drop the plugin entirely | Very low | Removes a node from the documented SDLC command set (`consolidation-acceptance-checklist.md:55` declares the command set fixed). Breaks `/debrief chain`. Breaks `promotion_opportunity.schema.json` enum. Breaks ≥8 docs that reference `/red-team` in escalation tables. |

### 4.3 Universal edit protocol (the Plugin Mutation Checklist, condensed)

Any edit to any file under `plugins/red-team/`:

1. **Source edit** — modify only files under `plugins/red-team/`.
2. **Version bump** — increment `plugins/red-team/.claude-plugin/plugin.json` version.
3. **Cache rebuild** — run `python P:/packages/.claude-marketplace/plugins/cc-skills-utils/scripts/plugin-audit-and-fix.py --bump red-team` (with `--marketplace-root P:/packages/.claude-marketplace` if detection fails).
4. **Verify cache** — confirm `~/.claude/plugins/cache/local/red-team/<new-version>/` exists and mirrors source.
5. **Run tests** — `pytest plugins/red-team/tests/`.
6. **Marketplace sync** — if manifest version changed, update `marketplace.json` row to match.
7. **Reload** — `/reload-plugins` (or restart) before smoke-testing the slash command.

Steps 1-6 are mandatory and enforced by tests (`test_smoke_resolution.py`, `test_enablement.py`).

---

## 5. Second-order effects — the dependency graph

For each common edit, what else must change:

```
EDIT: commands/red-team.md
  ├─ triggers: version bump + cache refresh (mandatory)
  ├─ readers: every /red-team invocation (runtime)
  ├─ cross-refs: superpowers plan 2026-07-12 wants to edit this file (reconcile first)
  └─ tests: test_smoke_resolution.py asserts cache freshness

EDIT: agents/red-team-*.md (any specialist)
  ├─ triggers: version bump + cache refresh
  ├─ readers: only the dispatch loop in commands/red-team.md
  └─ schema: prompts must keep producing findings with REQUIRED_FINDING_FIELDS

EDIT: agents/red-team-critic.md
  ├─ triggers: version bump + cache refresh
  ├─ readers: only the dispatch loop
  ├─ producer-of: critic.json (consumed by telemetry.py derive_from_critic)
  └─ BUG: changing "### Verified findings" heading to "### Findings" fixes counts drift (§3.1)

EDIT: __lib/telemetry.py
  ├─ triggers: version bump + cache refresh
  ├─ readers: orchestrator (calls `commit`), Phase 3b workflow (unbuilt, calls `recent`)
  ├─ producer-of: telemetry.jsonl rows
  └─ tests: test_telemetry.py — fixture field name 'findings' must align with parser

EDIT: __lib/findings_schema.py
  ├─ triggers: version bump + cache refresh
  ├─ readers: critic agent (validates each specialist file)
  └─ tests: test_findings_schema.py

EDIT: __lib/incidents.py
  ├─ triggers: version bump + cache refresh
  ├─ readers: orchestrator (incident-capture CLI), Phase 3b
  └─ tests: test_incidents.py

EDIT: __lib/telemetry_schema.py (e.g. add VALID_INCIDENT_CATEGORIES entry)
  ├─ triggers: version bump + cache refresh
  ├─ readers: incidents.py, telemetry.py
  └─ tests: test_incidents.py, test_telemetry.py

EDIT: plugin.json (version bump)
  ├─ triggers: cache refresh (mandatory, test-enforced)
  ├─ readers: cache builder, marketplace.json (should mirror)
  └─ tests: none direct; smoke_resolution checks cache dir matches

EDIT: marketplace.json
  ├─ triggers: none functional (display only)
  └─ drift: currently behind plugin.json by 1 version

ADD: tests/test_*.py
  ├─ triggers: none (tests don't run from cache)
  └─ verify: pytest must pass before commit
```

---

## 6. Concrete recommendations (decision-ready)

Ranked by reversibility-per-correctness:

### R1. Fix the counts drift (one-line + test fix) — cheapest high-impact win

- Edit `__lib/telemetry.py:94` → `findings = critic.get("findings") or critic.get("verified_findings") or []`
- Edit `__lib/findings_schema.py:38` similarly (defensive).
- Update `tests/test_telemetry.py` fixtures to include both shapes (one fixture with `findings`, one with `verified_findings`) — proves the parser handles both.
- Optional follow-up: standardize the critic prompt's "### Verified findings" heading to "### Findings (verified)" and pin the JSON field name.

**Effort:** ~10 lines. **Risk:** very low (parser becomes more tolerant).

### R2. Fix the stale specialist-path doc

- Edit `commands/red-team.md:168` to point at the plugin's own `agents/` directory, not `P:/.claude/agents/`.

**Effort:** one line. **Risk:** zero.

### R3. Reconcile with the competing plan

- Read `superpowers/plans/2026-07-12-lazy-provenance-and-evidence-pipeline.md` Task 4 Step 4. Either:
  - Mark it DONE (the §"Knowledge and validation provenance" already implements the requested behavior), or
  - Identify what gap remains and decide whether to close it.

**Effort:** 15 min investigation. **Risk:** zero (no edit yet).

### R4. Implement the post-dispatch `Test-Path` verification (the original handoff's Priority 1, corrected)

- Edit `commands/red-team.md` §"### 2. Specialists" — add a step between specialist dispatch and critic invocation:
  > After each specialist returns, verify `{run_dir}/{specialist}.json` exists. If absent, mark the specialist `DEFERRED — specialist-miss (no file written)` in the dispatch manifest, run `incidents.py add --category specialist-miss ...`, and continue. Do not abort.
- Compose with the existing FM-1 (`_run.json` status) and PERF-5 (specialist timeout) pattern — same file, same section.
- Retry policy: see Open Question 3 in the original handoff. Default recommendation: auto-retry once with stronger "you MUST invoke the write tool" framing; surface as incident if retry fails.

**Effort:** ~30 lines in one file. **Risk:** low; the existing DEFERRED pattern absorbs the change.

### R5. Add the agent-side honesty rule (Priority 2 from the original handoff, unchanged)

- Edit each `agents/red-team-*.md` to add: *"If your write tool call failed or returned an error, do NOT report the path; instead respond `WRITE_FAILED: <reason>` on a single line."*

**Effort:** ~5 lines × 12 files = 60 lines. **Risk:** zero.

### R6. Demote the original handoff's Priority 4 (new CLI subcommands)

- The handoff proposed `set-outcome`, `counts-recompute`, `status` subcommands.
- `set-outcome` is unnecessary once R1 lands — telemetry rows will have correct counts at write time; manual `operator_outcome` patching is rare and acceptable as JSON edit.
- `counts-recompute` is unnecessary — R1 prevents the bug.
- `status` (triage view) is genuinely useful but lower-leverage than R1-R5.

**Recommendation:** defer all three until R1-R5 land and a real recurring need is observed.

---

## 7. What this investigation did NOT verify (unknowns)

- **U1.** Did not run `pytest plugins/red-team/tests/` end-to-end. The schema-drift bug is diagnosed from static reads of parser + fixture + real critic.json. Running tests is the falsifier — predicted: tests pass today because the fixture uses `findings` (matching the parser); after R1 they should still pass because R1 only adds tolerance.
- **U2.** Did not check whether prior critic.json files (other than this run's) actually used `verified_findings` vs `findings`. The hypothesis is "critic prompt doesn't pin the field name; critic picks per run." Verifying requires reading 5-10 prior `critic.json` files.
- **U3.** Did not read `tests/test_claim_refute_schema.py` — likely the same pattern as the other schema tests.
- **U4.** Did not check the `/debrief chain` mode's actual coupling strength — does it literally invoke `/red-team` or just namecheck it? If literal invocation, removing `/red-team` breaks `/debrief chain`; if namecheck only, it's documentation.
- **U5.** Did not run `plugin-audit-and-fix.py` to confirm the cache rebuild flow works on this plugin. The test (`test_smoke_resolution.py`) proves the cache currently exists; the rebuild flow is documented but not exercised here.

---

## 8. Source map for this investigation

| Artifact read | Purpose |
|---|---|
| `P:/packages/.claude-marketplace/plugins/red-team/` (full `list_dir`) | Source inventory |
| `commands/red-team.md` (470 lines, full read) | Dispatch loop, contracts, schema doc |
| `agents/red-team-{failure-modes,critic}.md` | Producer-side prompt contracts |
| `__lib/{telemetry,incidents,telemetry_schema,findings_schema}.py` | Consumer-side parsers and schemas |
| `tests/{test_telemetry,test_incidents,test_findings_schema,test_smoke_resolution,test_enablement}.py` | Test coverage and codified contracts |
| `CLAUDE.md` (plugin) | Package-local instructions |
| `P:/packages/.claude-marketplace/marketplace.json:324-331` | Registration |
| `C:/Users/brsth/.claude/settings.json:363` | Enablement |
| `C:/Users/brsth/.claude/plugins/cache/local/red-team/0.2.18/` (full `list_dir`) | Cache state |
| `P:/packages/.claude-marketplace/shared/schemas/promotion_opportunity.schema.json` | Schema enum dependency |
| `P:/docs/superpowers/plans/2026-07-12-lazy-provenance-and-evidence-pipeline.md` | Competing plan |
| `P:/.claude/agents/` (full `list_dir`) | Stale-doc verification (no red-team-* files) |
| `P:/.claude/state/red-team/{telemetry,incidents}.jsonl` | Runtime state |
| `P:/.claude/.artifacts/019f7a64-.../critic.json` | Producer-side field name evidence |
| grep across `P:/packages/.claude-marketplace`, `C:/Users/brsth/.grok`, `P:/docs`, `P:/.data/wiki` | Cross-reference mapping |

---

*End of investigation.*
