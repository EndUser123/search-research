---
name: aar
description: >
  Evidence-grounded continual-improvement system: reconstructs sessions,
  performs value accounting, identifies the opportunity landscape, and
  governs continual improvement via lifecycle-tracked dispositions. Not
  just incident review. Does not implement changes unless authorized. Use
  for /aar, after-action review, debrief, post-mortem, retro, what went
  wrong, what worked, what to improve, what to reuse, session review.
when-to-use: >
  /aar, after-action review, post-mortem, retro, what went wrong,
  what worked, what to improve, what to reuse, session review, lessons learned
argument-hint: "[target | session | <path> | --lite]"
effort: high
metadata:
  short-description: "Lean continual-improvement AAR with conditional references"
---

# /aar — Lean continual-improvement review (Phase 1 lean-hybrid core)

You are the **AAR orchestrator**. Your job: use the complete session
evidence to determine what should be **learned, preserved, improved,
simplified, expanded, retired, tested, reused, or newly enabled** so future
outcomes become more effective, efficient, reliable, and valuable. You
analyze, discover opportunities, and route. You do **not** implement.

**Lean-hybrid design (Phase 1):** This SKILL.md is the always-loaded
**lean core**. Detailed guidance lives in `references/*.md` and is loaded
**only when an explicit trigger fires** (see §triggers below). The default
invocation loads zero references. Use `__lib/reference_loader.py` to
resolve which references apply.

**Core principle:** an opportunity does not require a failure. A successful
session still reveals unnecessary effort, missed leverage, reusable
capabilities, and unrealized combinations.

**Product rule:** `/aar` must not optimize for finding count, artifact
length, or performative self-criticism. `NO_CHANGE_PRESERVE`, `PRESERVE`,
`REJECT`, `NOT_WORTH_DOING`, and an empty pass are all valid outcomes when
the evidence supports them.

---

## Step 0 — Run directory + evidence resolution

### 0.1 Terminal-scoped run directory

**Use Python, not PowerShell.** The PowerShell snippet below was the
original spec but proved fragile in practice: when invoked through
`run_terminal_command`, short PowerShell variable names (e.g. `$term`)
get stripped by shell tokenization, leaving empty values. The fix is
to call the preprocessor directly via Python — it creates the run dir
itself.

**Recommended pattern** — one Python call that does Step 0.1 + Step 0.5
together. Write to a file first to avoid heredoc tokenization:

```python
# P:/tmp/aar_step0.py
import sys, os, json
from datetime import datetime
from pathlib import Path

session_id = sys.argv[1]                       # e.g. "019f8148-..."
workspace_encoded = sys.argv[2]               # e.g. "P%3A%5C"
out_dir_arg = sys.argv[3]                       # e.g. "P:/.artifacts/.../grok-aar"

# Terminal isolation: pick a stable per-terminal id without PowerShell
term = (
    os.environ.get("CLAUDE_TERMINAL_ID")
    or os.environ.get("WT_SESSION")
    or os.environ.get("TERMINAL_ID")
    or "noterm"
)
term_clean = "".join(c for c in term if c.isalnum() or c in "_-")[:36]
out_dir = Path(out_dir_arg)
run_dir = out_dir.parent / f"console_{term_clean}" / out_dir.name
run_dir.mkdir(parents=True, exist_ok=True)
(run_dir / "packets").mkdir(exist_ok=True)

(run_dir / "_run.json").write_text(json.dumps({
    "status": "started",
    "started_at": datetime.now().isoformat(),
    "skill": "aar",
    "terminal_id": term_clean,
    "session_id": session_id,
    "head": "session-AAR",
}, indent=2))

# Run the preprocessor immediately; it reads _run.json + writes the
# full packet to run_dir/preprocess/
sys.path.insert(0, "P:/.grok/skills/aar/__lib")
from full_preprocessor import run_full_preprocessor
r = run_full_preprocessor(
    session_id=session_id,
    workspace_encoded=workspace_encoded,
    run_dir=str(run_dir),
)
print("ok:", r.ok, "status:", r.status_label,
      "events:", r.events_total,
      "signals:", r.signals_total,
      "packet:", r.packet_dir)
```

Then call:

```bash
python P:/tmp/aar_step0.py <session_id> <workspace_encoded> <out_dir_base>
```

For example, with the current session:

```bash
python P:/tmp/aar_step0.py 019f8148-3e72-79d2-a933-4bf432d435ec P%3A%5C P:/.artifacts/grok-aar/20260720-150000
```

**Why this works**: no shell tokenization, no PowerShell, the preprocessor
does Step 0.1 + Step 0.5 in one call, and the output is captured cleanly.

**Cross-host behavior**: the script is host-agnostic. It accepts env vars
from both Grok Build (`GROK_TERMINAL_ID`, `GROK_SESSION_ID`) and Claude
Code (`CLAUDE_TERMINAL_ID`, `CLAUDE_SESSION_ID`), with fallback chain
`GROK → CLAUDE → WT_SESSION → TERMINAL_ID → TERM_SESSION_ID` for
terminal id. The preprocessor path defaults to
`P:/.grok/skills/aar/__lib/` (Grok Build) but can be overridden via
`AAR_PREPROCESSOR_PATH` env var for Claude Code or other installations.
The caller passes the full `out_dir` path including the terminal id —
the script does NOT auto-insert a terminal prefix (that caused a
double-prefix bug in an earlier draft).

**Immunity to stale data** (mandatory contract):

1. **Per-run freshness**: every invocation creates a new timestamped
   run_dir and writes a fresh `_run.json`. There is no cache or
   memoization across runs. A new AAR always sees the current session
   state, not a snapshot from N hours ago.
2. **Packet is authoritative**: the preprocessor emits a `snapshot_cutoff`
   in `preprocess-summary.md`. The orchestrator cites events only from
   the current packet. If `source_status` is `SOURCE_UNVERIFIED` or
   `SOURCE_UNSUPPORTED`, the script exits with code 4 and a warning —
   the orchestrator must not proceed with a degraded packet.
3. **State file is advisory only**: the state file at
   `P:/.artifacts/<term>/<pkg>-state.md` carries history across AARs
   but is never a source of evidence for the current report. Treat it
   as a TODO list, not a fact store.
4. **Env var fallback is greedy**: the first non-empty env var in the
   chain wins. If both `GROK_TERMINAL_ID` and `CLAUDE_TERMINAL_ID`
   are set in the same shell, the Grok one wins. This is deliberate
   (this skill is Grok-canonical) but documented so a Claude Code user
   with both env vars set gets a predictable answer.

**Exit codes** (for automation callers):

| code | meaning |
|---|---|
| 0 | packet generated successfully |
| 1 | preprocessor returned a non-OK status |
| 2 | missing required argument or session id |
| 3 | preprocessor not found at the configured path |
| 4 | source_status is `SOURCE_UNVERIFIED` or `SOURCE_UNSUPPORTED` (stale data risk) |

**If you must use PowerShell** (e.g., a hook forces it): write the script
to a file FIRST (`Set-Content -Path foo.ps1 -Value $script`), then call
`powershell -NoProfile -File foo.ps1`. Do not pass PowerShell as
heredoc inline content to `run_terminal_command` — that's the case
where `$term` and other short variables get stripped.

**Fallback (if Python is unavailable)**: run the PowerShell snippet by
saving it to a `.ps1` file first and invoking with `powershell -NoProfile
-File foo.ps1`. Verify the output contains the expected `$runDir` value
before proceeding.

### 0.2 Evidence resolution

| Target | Evidence source |
|--------|----------------|
| Current session | Full session directory at `~/.grok/sessions/<encoded-cwd>/<session-id>/` — run preprocessor (Step 0.5) |
| Exported transcript | User-supplied path |
| Implementation/PR | `git diff` / `git log` + tests + review artifacts |
| Incident | Incident report + logs + timeline |
| Skill execution | SKILL.md + run artifacts + state file |

Source status values (earned through reconciliation, never inferred from file existence):

- `SOURCE_COMPLETE` — identity verified, full active history, counts reconcile, no material gaps
- `SOURCE_COMPLETE_WITH_LIMITATIONS` — complete with caveats
- `SOURCE_PARTIAL` — material raw records missing; must not claim exhaustive coverage
- `SOURCE_UNVERIFIED` — binding not verified
- `SOURCE_UNSUPPORTED` — formats cannot be parsed safely

### 0.3 Resume state (terminal-scoped)

Read `P:/.artifacts/<termSafe>/<pkg>-state.md` if it exists. **Never read another terminal's state file.**

---

## Step 0.5 — Deterministic preprocessing (mandatory)

The orchestrator runs the deterministic preprocessor over the verified current session. Code handles facts, counts, ordering, branching, mechanically detectable signals; the LLM handles causal interpretation.

### 0.5.1 Resolve and verify session id

Priority order:
1. Skill-supplied id (authoritative)
2. `$GROK_SESSION_ID` env var (forward compat; currently unset)
3. Stop with `SESSION_IDENTITY_UNVERIFIED` — never select newest session dir

Cross-validate against `summary.json.info.id` and `events.jsonl turn_started.session_id`.

### 0.5.2 Run the preprocessor

**Same Python call as Step 0.1** — the preprocessor takes care of both.
The CLI form is:

```python
from full_preprocessor import run_full_preprocessor
r = run_full_preprocessor(
    session_id=session_id,
    workspace_encoded="P%3A%5C",
    run_dir=run_dir,
)
```

If invoking via subprocess:

```bash
python P:/.grok/skills/aar/__lib/full_preprocessor.py \
  --session-id <verified-session-id> \
  --workspace-encoded P%3A%5C \
  --run-dir <run_dir>
```

### 0.5.3 Packet artifacts (under `$runDir/preprocess/`)

source-manifest.json · canonical-events.jsonl · active-timeline.json · superseded-events.jsonl · event-index.json · signals.json · claim-evidence.json · parser-warnings.json · timeline.md · preprocess-summary.md · context-selection.json

### 0.5.4 Source authority hierarchy

| Role | Source | Use for |
|------|--------|---------|
| Primary | `chat_history.jsonl` | User/assistant messages, tool calls/results |
| Metadata | `summary.json` | Cross-check id/counts/model |
| Operational | `events.jsonl` | Timestamps, durations, lifecycle |
| Branch | `rewind_points.jsonl` | Detect rewind+replay; label SUPERSEDED_HISTORY |
| Recovery | `compaction_checkpoints/*.json` | Pre-compaction context |
| Navigation only | `compaction/INDEX.md`, `segment_*.md` | Phase labels — never primary evidence |

### 0.5.5 Consume the packet, not the raw session

- Read `preprocess-summary.md`, `context-selection.json`, `signals.json` for initial context
- Cite `event_id` values from `canonical-events.jsonl` (format: `chat_history-L<line>-S<seq>`)
- Respect `source_status` from the manifest — never upgrade completeness
- Label superseded evidence with `from_superseded_history: true`
- Include `snapshot_cutoff` in the report's `evidence_scope`

### 0.5.6 Failure handling

| Outcome | Action |
|---------|--------|
| `SESSION_IDENTITY_UNVERIFIED` | Stop. Report reasons. |
| `SOURCE_UNSUPPORTED` | Stop. Surface parser-warnings. |
| `SOURCE_PARTIAL` | Proceed; constrain completeness claims. |
| `SOURCE_UNVERIFIED` | Stop unless user authorizes analysis-with-caveats. |
| Snapshot drift detected | Proceed with captured copy; report cutoff. |
| **Silent failure** (preprocessor exits 0 but produces no packet) | **The preprocessor MUST write a `_preprocessor_status.json` file even on failure**, with `status: "failed"`, `reason: "<specific error or 'no output produced'>"`, and `packet_path: null`. The orchestrator checks this file before deciding to fall back to LLM-only analysis. If the file is missing, the orchestrator reports "preprocessor status unknown — proceeding with LLM-only analysis with caveats" and sets `source_status: SOURCE_COMPLETE_WITH_LIMITATIONS`. Silent failure without a status file is itself a bug in the preprocessor. |

### 0.5.7 Output validation (mandatory before reporting)

```python
from output_validator import validate_aar_report_with_packet
result = validate_aar_report_with_packet(report_path, packet_dir)
if not result.passed: ...  # Fix blockers before reporting.
```

---

## Phase 1 — Contract reconstruction + terminal outcome

| Element | Source | If absent |
|---------|--------|-----------|
| Intended goal | User's original request + follow-ups | "goal inferred from context" |
| **Terminal outcome** | What the user was actually trying to accomplish (NOT the artifact) | "terminal outcome inferred from context" |
| Approved scope | What the user explicitly authorized | "scope not explicitly bounded" |
| Constraints | AGENTS.md, package rules, user instructions | List applicable |
| Success criteria | User's definition of done | "not explicitly stated" |
| Authority boundaries | What the agent was/wasn't allowed to change | Infer from AGENTS.md |
| Changes in intent | Where the user redirected mid-session | Trace through conversation |

### Terminal outcome reconstruction (mandatory for substantial AAR)

```text
user_terminal_outcome     — what the user was actually trying to accomplish
success_conditions        — what would constitute success for the user
explicit_constraints      — constraints the user named
implicit_operational_need — constraints implied by context
actual_outcome            — what the session actually delivered
degree_of_completion      — complete | partial | abandoned | substitute
```

If `degree_of_completion` is `substitute` (polished artifact that did not advance the terminal outcome), emit a `TERMINAL_OUTCOME_DRIFT` finding concept.

---

## Phase 2 — Typed episode ledger

Every meaningful episode receives **exactly one type**:

| Type | Definition |
|------|-----------|
| `validated_success` | Goal achieved with evidence; mechanism understood |
| `resolved_incident` | Problem occurred AND was fixed within scope |
| `open_defect` | Problem exists, not fixed, needs action |
| `process_weakness` | Worked but fragile, inefficient, or error-prone |
| `pending_decision` | User needs to decide; not a defect |
| `opportunity_candidate` | Gap that could improve outcomes if addressed |
| `observation` | Noteworthy but not actionable |
| `unknown` | Cannot determine with available evidence |

Each episode MUST include: `id`, `type`, `event`, `evidence`, `evidence_event_ids` (canonical ids from packet), `impact`, `status`, `from_superseded_history`. For material episodes `evidence_event_ids` is mandatory and verified by the output validator.

**Resolved incidents stay in the record but do NOT automatically become open actions.** A resolved incident is evidence of recovery, not a pending task.

---

## Phase 3 — Decision history

| Type | Definition |
|------|-----------|
| `DECISION` | A choice was made and acted on |
| `ASSUMPTION` | Something was assumed without verification |
| `CORRECTION` | The user or agent corrected a wrong direction |
| `REVERSAL` | A prior decision was reversed |
| `USER_OVERRIDE` | User overrode the agent's recommendation |
| `DEFERRED_DECISION` | A decision was explicitly postponed |

Each `CORRECTION` or `REVERSAL` must identify **what it supersedes**.

---

## Phase 4 — Pattern synthesis + layered root-cause

Cluster related episodes. A recurring pattern requires ≥2 supporting episodes unless one event is severe enough to justify immediate action.

Cluster types: `shared_root_cause` · `repeated_symptom` · `downstream_consequence` · `one_off_coincidence` · `user_correction` · `external_limitation`.

### Layered root-cause (mandatory for material failures)

```text
OBSERVED_FAILURE         — what actually happened
IMMEDIATE_TRIGGER        — what set the failure in motion
PROXIMATE_CAUSE          — what the agent directly did wrong
CONTRIBUTING_CONDITIONS  — what made the failure likely
SYSTEMIC_REUSABLE_CAUSE  — what systemic cause best explains the pattern
COMPETING_EXPLANATION    — alternative hypotheses (REQUIRED, even if "none identified")
```

**Detailed calibration** (4-dim confidence, full cross-field invariants) lives in `references/epistemic-calibration.md` and is loaded only when a trigger fires (see §triggers).

---

## Phase 5 — Value accounting

| Category | What goes here |
|----------|----------------|
| `VALUE_CREATED` | New capability, insight, artifact, decision, or outcome produced |
| `VALUE_PRESERVED` | Existing capability or correct behavior that should survive refactoring |
| `VALUE_RECOVERED` | Value restored after error, omission, or premature rejection |
| `VALUE_UNREALIZED` | Evidence-supported value that was available but not captured |
| `VALUE_DEFERRED` | Potential value intentionally postponed |
| `VALUE_DESTROYED_OR_COST` | Rework, delay, confusion, wasted calls, unnecessary artifacts, maintenance burden |
| `VALUE_COMPOUNDED` | A lesson/detector/tool improvement that benefits multiple future sessions |

Do not force every category to contain an item — an empty category is honest.

**Success amplification (8 questions)** — for each material success, ask all eight:
1. What specifically produced the value?
2. Was it intentional, repeatable, or accidental?
3. Can it be made easier or more reliable?
4. Can it be reused elsewhere?
5. Can it be scaled or automated?
6. Does it expose a capability the system did not know it had?
7. What would prevent this success from recurring?
8. Does it invalidate an existing workflow or assumption?

---

## Phase 6 — Opportunity discovery (conditional)

**An opportunity does not require a failure.** An opportunity is any
evidence-grounded possibility to improve future value, effectiveness,
efficiency, reliability, usability, learning, or optionality.

**Default:** the simple AAR uses the §ten-questions synthesis and does not
emit formal opportunities. **Promote to full opportunity-discovery** when
any trigger in §triggers fires (especially `full_mode_promoted`,
`successful_efficiency_session`, or `user_asked_opportunity_landscape`).

**When promoted**, load `references/opportunity-discovery.md` and emit
opportunities per its schema. Dispositions: `ACT_NOW`, `BOUNDED_EXPERIMENT`,
`INVESTIGATE`, `MONITOR`, `REUSE_EXISTING`, `SIMPLIFY_OR_REMOVE`,
`PRESERVE` (formerly `STANDARDIZE`), `DEFER`, `REJECT`, `NOT_WORTH_DOING`.

## Phase 7 — Continual-improvement governance (conditional)

**Default:** the simple AAR routes findings without lifecycle tracking.
**When promoted** (any trigger in §triggers fires), apply the lifecycle
block, opportunity-cost, rejection-ledger, and promotion-challenge rules
in `references/opportunity-discovery.md`.

**Always-loaded rule:** a single session should rarely produce durable
policy. `MONITOR` / `INVESTIGATE` / `BOUNDED_EXPERIMENT` / `DEFER`
require a lifecycle block. Promotion to durable policy requires
cross-session evidence or authorised aggregation.

## §triggers — Conditional-reference promotion gate

**This is the single authoritative trigger list.** The loader
(`__lib/reference_loader.py`) reads this contract.

A reference loads when any of its triggers fire. A trigger fires when:
- the user explicitly asks for the relevant kind of analysis, OR
- a detector signal at the appropriate severity threshold fires, OR
- a structural condition is observed in the packet.

**A weak detector signal alone is NOT a trigger.** The orchestrator
decides whether a signal rises to trigger threshold based on severity,
repetition, and outcome impact.

### Reference: opportunity-discovery
Loads when: full_mode_promoted · user_asked_opportunity_landscape · successful_efficiency_session

### Reference: interaction-quality
Loads when: user_correction_high · objective_drift_any · correction_propagation_failure_any · procedure_saturation_any · user_repeated_goal_restoration · user_asked_what_went_wrong

### Reference: epistemic-calibration
Loads when: architectural_change_proposed · durable_rule_promotion_claimed · high_severity_defect · cross_session_aggregation_claim · headline_makes_comparative_claim · user_asked_deep_root_cause

### Reference: operational-safety
Loads when: destructive_write_signal · tool_result_secret_exposure_signal · user_paste_secret_warning_signal · file_edit_reversal_high · active_incident_reported

### Reference: external-insight
Loads when: user_asked_external_research · reusable_failure_class_revealed · root_cause_benefits_from_external_evidence · platform_capabilities_may_have_changed · improvement_may_exist_elsewhere · local_evidence_supports_competing_explanations · cross_domain_analogies_relevant · full_mode_promoted

### Reference: handoff-and-temporal
Loads when: handoff_document_present · prior_session_state_referenced · recommendation_revision_aggregate_high · stale_state_risk_material

### Full-mode promotion (loads opportunity-discovery + external-insight)
Promote to full continual-improvement mode when ANY of these is **material**:
- repeated user goal restoration (≥2 corrections of same objective)
- multiple avoidable corrections (user doing the agent's work)
- defensive resistance (agent re-asserts a corrected claim)
- large artifact or tool cost without terminal outcome advancement
- instruction conflict or combination pathology
- recommendation reversals with downstream effects
- evidence misuse affecting material decisions
- high user debugging burden
- repeated sessions showing similar patterns
- explicit user request for deep root-cause or continual-improvement analysis

**Do not promote merely because the session is long.**

### §ten-questions — Default synthesis (always loaded)

The default simple AAR synthesizes around these ten questions. They are NOT visible report headings — just guidance.

1. What did the user ultimately need?
2. Did the session deliver it?
3. What created value?
4. What materially reduced value?
5. What did the user have to correct or reason through?
6. Was evidence sufficient, misused, abandoned, or pursued too long?
7. Did process, artifacts, tools, or instructions displace judgment?
8. What was the best earlier stop, reframe, or recovery point?
9. What are the strongest causal explanations and alternatives?
10. What smallest justified improvement, simplification, or no-change decision follows?

---

## Phase 8 — Routing

`/aar` analyzes and routes. It must **not silently implement**.

| Route | When |
|-------|------|
| `/go` | User explicitly authorizes implementation of an `ACT_NOW` item |
| `/review` | Quality review of existing code/artifacts |
| `/check` | Verify specific claims from the AAR |
| `/red-team` | Adversarial evaluation of a high-risk finding |
| `/improve` | Process or skill improvement recommendation |
| User decision | `pending_decision` or `BLOCKED` items |

Do not create `aar-redteam`, `aar-implement`, or any AAR-specific companion skill. Use existing skills.

---

## Phase 9 — Report

Write to `$runDir/aar-report.md` and optionally to `<package>/docs/operations/aar-YYYY-MM-DD.md` when `--durable`.

### Lesson Calibration Gate (mandatory for all synthesized lessons)

For each lesson, provide these fields (Title Case labels are canonical;
snake_case is acceptable in structured output):

- **Supporting episodes** — exact episode or pattern IDs
- **Direct observation** — what was actually observed, without causal interpretation
- **Causal interpretation** — the narrowest causal explanation supported by the evidence
- **Competing explanations** — at least one plausible alternative, or explicit "none identified"
- **Comparison status** — `NO_COMPARISON` / `INFORMAL_COMPARISON` / `CONTROLLED_COMPARISON` / `EXTERNAL_EVIDENCE`
- **Scope** — `SESSION_SPECIFIC` / `PROBLEM_CLASS` / `GENERAL` (general requires stronger evidence)
- **Counterexample or boundary** — when would this lesson NOT apply?
- **Confidence** — `OBSERVED` / `INFERRED` / `SPECULATIVE`
- **Unsupported extension** — explicitly state what the evidence does NOT establish

### Compressed calibration invariants (always loaded — the 3-line core)

1. `NO_COMPARISON` cannot support "more reliable than" / "better than" / "superior to".
2. `SOURCE_PARTIAL` cannot support exhaustive coverage or "all gaps found."
3. `LOW` or `UNKNOWN` causal confidence cannot directly support `DURABLE_POLICY` or irreversible structural change.

A minor observation may retain a compact evidence label without the full calibration schema (see `references/epistemic-calibration.md` for the full schema, loaded on trigger).

### Comparative-claim rule (mandatory)

Do not claim one intervention class (rules, hooks, validators, state machines) is more reliable/effective/appropriate than another unless the evidence includes a meaningful comparison OR credible external evidence. Specific rejected proposals do not establish that the entire proposal category is inferior.

### Intervention selection sequence

```
Observed failure → verified causal mechanism → problem-class classification
→ intervention requirements → smallest sufficient intervention → bounded lesson
```

The AAR must not rank intervention classes before the failure class is established.

### Required report format

```markdown
# AAR: <target>

## Verdict
Did the work achieve the intended outcome, and what is the most important lesson?

## Findings  ← always emitted; this is the headline view
Plain-language summary of what was found, ordered by severity. The user reads this section first; if they stop here, they have the headline.

For each finding:
  - **Severity tag** (CRITICAL | HIGH | MEDIUM | LOW) — derived from the corresponding episode severity, opportunity disposition, or lesson calibration
  - **One-line title** — concrete, not generic; rejected per the same generic-phrase blocklist as opportunities
  - **What happened** — observed evidence in plain language, citing the canonical event_id or signal index
  - **Why it matters** — the impact, in terms of the user's terminal outcome or downstream consequence
  - **What to do** — the action, in plain language; if ACT_NOW, name the containment step first
  - **Where in this report** — cross-ref to the §Material episodes, §Headline lessons, §Opportunity landscape, or §Open work section that contains the full evidence

Example entry:
  ### HIGH — Three live credentials exposed at event 118
  - **What happened:** Reading `P:/.env` to verify API-key availability echoed SERPAPI_KEY, SERPER_KEY, GITHUB_TOKEN into tool output. They are now in `chat_history.jsonl` and `canonical-events.jsonl`.
  - **Why it matters:** Future sessions that read this transcript inherit the exposed keys. The agent's working context also contains them this session.
  - **What to do:** Rotate the 3 keys via each provider's console. Then decide whether to retain or delete the transcript files containing them.
  - **Where in this report:** §Material episodes E1; §Opportunity landscape O1 (ACT_NOW).

The Findings section is **synthesized from** the detailed sections below — it is not a replacement for them. Empty Findings is valid (a session with no material findings should still produce this section, with a single explicit "no material findings" entry).

## Evidence scope
Sources, boundaries, completeness, repository/worktree, harness, shell, snapshot_cutoff.

## Intended versus actual
Goal, constraints, success criteria, actual result, scope changes.

## Session outcome
What the session accomplished and failed to accomplish.

## Value accounting
The seven-category value ledger. Empty categories are honest.

## Material episodes
Failures, decisions, corrections, successes, discoveries, changes.

## What created value
Actions, tools, reasoning, or interactions that improved the outcome.

## Decisions and reversals
Current decisions, superseded assumptions, corrections, user overrides.
Each revised recommendation carries a RevisionClassification.

## Recurring patterns (conditional — emit only if ≥1 pattern with ≥2 episodes)

## Opportunity landscape (conditional — load reference on trigger)

## Prioritized opportunity portfolio (conditional)

## Continual-improvement candidates (conditional)

## Rejected or deferred opportunities

## Validated successes

## Open work and decisions

## Recommended routing

## Headline lessons

## Accounting
N episodes → N validated successes, N resolved incidents, N open defects,
N process weaknesses, N pending decisions, N opportunity candidates,
N unknowns, N actions promoted
N opportunities → N ACT_NOW, N BOUNDED_EXPERIMENT, N INVESTIGATE,
N MONITOR, N REUSE_EXISTING, N SIMPLIFY_OR_REMOVE, N PRESERVE,
N DEFER, N REJECT, N NOT_WORTH_DOING
```

### Accounting reconciliation (mandatory)

```
total_episodes = validated_success + resolved_incident + open_defect
               + process_weakness + pending_decision + opportunity_candidate
               + observation + unknown
```

If counts don't add up, the AAR is incomplete. **Accounting disclaimer:** reconciled accounting proves only arithmetic consistency.

### State file update

Update `P:/.artifacts/<termSafe>/<pkg>-state.md`: Last AAR, Open items, Recommended next.

---

## Source-fidelity rules (always loaded)

**Principle:** A detector may not emit greater confidence or severity than the source representation supports.

**Classifications:**
- `LINKAGE_PROVEN` — source format preserves the structural relationship
- `LINKAGE_INFERRED` — relationship can be reconstructed but not guaranteed
- `LINKAGE_UNAVAILABLE` — source format loses the relationship

Detector-specific severity caps:
- `detect_orphaned_tool_results` MUST NOT exceed LOW when linkage is unavailable.

---

## Windows, PowerShell, and isolation

| Requirement | Rule |
|-------------|------|
| Shell detection | Read `$PSVersionTable` at start |
| PowerShell | Use `pwsh` syntax |
| Path handling | Quote all paths; forward slashes in JSON/scripts |
| Terminal isolation | Run dir under `.artifacts/<term>/`; never read foreign state |
| No mutable global pointers | No `LATEST-*` heuristics or newest-timestamp discovery |
| Durable artifacts | Must define: writer, storage path, reader, authority, freshness, isolation, failure behavior |

---

## Rules (always loaded)

1. **Analyze and route only.** Do not implement without explicit authorization.
2. **Typed episodes are mandatory.** No generic "finding" bucket.
3. **`PRESERVE` and `NOT_WORTH_DOING` are valid and desirable.** Do not pad the report with unnecessary actions.
3a. **Severity asymmetry.** Destructive mutation, data loss, secret exposure, and unsafe recommendations are categorically more severe than CSS defects, variable-count errors, or cosmetic issues. The highest-impact findings must dominate the summary and dispositions. Use the `destructive_write_without_read`, `tool_result_secret_exposure`, and `user_paste_secret_warning` HIGH-severity signals as forcing functions — if any fires, it is the headline finding until explicitly displaced by evidence. (Detail: `references/operational-safety.md`, loaded on trigger.)
3b. **Containment vs recovery vs prevention.** When the session involves an active incident, the report must distinguish: **Containment** (rotate credential, invalidate dependent output, verify no persistent leak), **Recovery** (reconstruct .env, restore deleted files), **Prevention** (read-before-write preflight, secret-safe diagnostic output). `ACT_NOW` covers containment and recovery. Do NOT turn an active incident into only a future improvement candidate. (Detail: `references/operational-safety.md`.)
4. **Opportunity discovery is a first-class objective.** An opportunity does not require a failure. (Detail: `references/opportunity-discovery.md`, loaded on trigger.)
5. **Opportunity ≠ gap.** Observed evidence and interpretation must differ.
6. **Every opportunity carries the full schema** when one is emitted. (Schema: `references/opportunity-discovery.md`.)
7. **Generic opportunities are rejected.** Concrete target required.
7a. **Every opportunity must declare a `prevention_mechanism`.** Valid values: `rule` (AGENTS.md/config), `hook` (runtime gate), `metric` (observability/telemetry), `skill_edit` (changes skill behavior), `config` (changes default behavior), `wiki_only` (documentation only — advisory, does not change runtime behavior). If `wiki_only`, the opportunity is `advisory_only` and MUST be separated from actionable opportunities in the report. The user should see at a glance which opportunities change behavior vs which are just documentation.
7b. **Advisory-only validation.** Before emitting an opportunity whose `prevention_mechanism` is `wiki_only`, ask: "does this change runtime behavior?" If no, flag it as `advisory_only` in the report and explain what structural change WOULD make it actionable (e.g., "to make this actionable, add a metric field to fetch_completed that surfaces NLM path success rate"). Observations are valid; dressing them up as actionable opportunities is not.
8. **Accounting must reconcile.** Episode counts and opportunity dispositions both.
9. **Evidence is mandatory.** Every claim cites a canonical event_id from the packet.
10. **Minimal sufficient intervention.** AGENTS.md rule > skill edit > new skill > hook > config. `NO_CHANGE_PRESERVE` is a valid mechanism.
11. **Continual improvement, not durable policy from one session.** Lifecycle blocks required for MONITOR / INVESTIGATE / BOUNDED_EXPERIMENT / DEFER.
12. **Opportunity cost is mandatory for major recommendations.**
13. **Rejection ledger prevents re-proposal.**
14. **Cross-session candidates are emission-only.** Never auto-consume.
15. **Run Step 0.5 before Phase 1** for any current-session AAR. Consume the packet, never the raw session dir.
16. **Cite canonical event_ids** for every material episode and opportunity.
17. **Never upgrade `source_status`** beyond what the reconciler earned.
18. **Label superseded evidence** with `from_superseded_history: true`.
19. **Include `snapshot_cutoff`** in the report's `evidence_scope`.
20. **Bind to the verified session only.**
21. This skill at `P:/.grok/skills/aar/SKILL.md` is canonical for Grok.

---

## Examples

| User says | Behavior |
|---|---|
| `/aar` | Resolve current session (Step 0.5); lean core + triggered references |
| `/aar session` | Same as above (explicit) |
| `/aar --session-id <uuid>` | Explicit session binding (highest authority) |
| `/aar P:/path/to/transcript.md` | Analyze supplied transcript (skips Step 0.5) |
| `/aar --lite` | Skip opportunities; episodes + decisions only |
| `/aar` after `/go` implement | Verify intended outcomes were achieved; route gaps |
