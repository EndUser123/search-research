---
title: "Review packet: AAR Golden Circle / learning-loop proposal"
created: 2026-07-25
status: review-only
owner: next cold-start LLM
source: current Codex session, 2026-07-25
parent_session: none
current_session_id: 019f8b39-95e3-7121-a8de-4e3f117e511a
last_updated_by: 019f8b39-95e3-7121-a8de-4e3f117e511a
last_updated_at: 2026-07-26T22:02:40.921048
---

# Review packet: AAR Golden Circle / learning-loop proposal

## Instruction to the reviewing LLM

This is a review task, not an implementation request. Do not edit production
skills, validators, wiki files, or configuration. Inspect the canonical source
files listed below, challenge the proposal, and return a concise evidence-backed
review with one of these dispositions:

- `ACCEPT` — proposal is sound as written.
- `ACCEPT_WITH_CHANGES` — direction is sound, but specific changes are needed.
- `REJECT` — proposal would reduce quality, duplicate existing behavior, or
  solve the wrong problem.

Separate verified facts, inferences, hypotheses, and recommendations. Do not
assume that a model-generated retrospective is correct merely because it is
well organized.

## Review objective

Assess whether `/aar` should become the single canonical session learning and
closure-analysis workflow, replacing `/debrief`, and whether its expensive
reflection/refinement stages can be made faster without losing coverage of:

- completed, partial, deferred, and unstarted work;
- non-closed work and continuation candidates;
- decisions and rationale;
- failures, friction, and wasted effort;
- reusable insights and patterns;
- verification gaps and unresolved risks;
- handoff, wiki, experiment, and next-action routing.

## Current context

`/close` invokes a subagent because some closure judgments cannot be derived
mechanically. The current close design already has a scanner and variants:

- `/close` standard: broad accounting and safety gates;
- `/close --quick`: skips some knowledge-capture gates;
- `/close --deep`: adds deeper consolidation work;
- `/close --no-loop`: avoids a second scan after gate resolution.

The current `/close` skill says that a missing retrospective should auto-invoke
the full `/aar` workflow. The concern is latency and token cost, not whether
closure analysis should happen.

The key correction from the preceding discussion is:

> Do not replace full AAR breadth with a lightweight summary. Full breadth is
> required because AAR is supposed to capture non-closed work, insights,
> learning, decisions, friction, and handoff needs. Optimize redundant
> rereading, expensive synthesis, and repeated execution instead.

## Proposal under review

Make AAR the canonical workflow and treat `/debrief` as an alias or migration
path, not a second independent analysis system.

Preserve a mandatory full-breadth AAR inventory:

```text
AAR
├─ Evidence inventory
│  ├─ completed work
│  ├─ non-closed work
│  ├─ decisions
│  ├─ failures/friction
│  ├─ insights
│  └─ verification gaps
├─ Learning extraction
│  └─ concise evidence-backed lessons
├─ Refinement proposals
│  └─ candidate skill/rule/tool/workflow changes
├─ Adversarial filter
│  └─ what would falsify each lesson?
└─ Routing
   ├─ transient note
   ├─ handoff
   ├─ wiki concept
   ├─ experiment
   └─ proposed skill change
```

Then reduce cost through these mechanisms:

1. Generate the AAR preprocessor packet once and pass that packet to the
   subagent instead of making it reread the raw transcript.
2. Run mechanical close scanning and AAR packet generation in parallel where
   their inputs permit it.
3. Keep the full breadth inventory, but load expensive AAR reference material
   only when its trigger fires.
4. Make cross-model critique conditional on material triggers: corrections or
   reversals, security/privacy incidents, repeated failure, costly dead ends,
   major architectural decisions, or an explicit deep-analysis request.
5. Cache AAR results by session ID plus an evidence/transcript fingerprint so
   repeated `/close` calls do not regenerate unchanged analysis.
6. Avoid repeating full scans during close loops; rerun only gates affected by
   the action just taken.
7. Require each proposed lesson to carry:
   - evidence receipt;
   - observed failure or opportunity;
   - generalizable lesson;
   - proposed behavior change;
   - confidence;
   - falsifier;
   - disposition: preserve, monitor, experiment, defer, or reject.

The intended optimization is therefore:

> one complete AAR breadth pass, with expensive refinement and cross-model
> analysis only where justified.

## Known risks to challenge

1. **“Full breadth” may still be incomplete in practice.** Determine whether
   the current AAR contract explicitly requires every inventory category or
   merely recommends them.
2. **Conditional deep analysis may hide important lessons.** Identify whether
   the proposed triggers are sufficient and what false negatives look like.
3. **AAR and DEBRIEF may not be functionally redundant.** Inspect both skills,
   their scripts, artifacts, and callers before recommending aliasing or
   removal.
4. **Caching can become stale-read.** A fingerprint must include the evidence
   sources that matter, not only the parent transcript timestamp.
5. **Parallelism can create races.** Confirm that packet generation does not
   read artifacts while the scanner or another skill is still writing them.
6. **Model substitution can reduce quality.** A cheaper model is acceptable
   only if it preserves the structured contract and evidence discipline.
7. **A polished lesson can still be false.** The review must distinguish an
   evidence-backed observation from an inferred causal mechanism.
8. **Automatic promotion can pollute durable policy.** One session should not
   silently turn an unreplicated insight into an AGENTS rule or permanent skill
   behavior.

## Required source inspection

Inspect the active source of truth, not caches or old handoffs:

- `C:\Users\brsth\.grok\skills\aar\SKILL.md`
- `C:\Users\brsth\.grok\skills\close\SKILL.md`
- `C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py`
- `C:\Users\brsth\.grok\skills\close\__lib\validate_close_receipt.py`
- `C:\Users\brsth\.grok\skills\debrief\SKILL.md` (if present)
- `P:\docs\handoffs\aar-*\HANDOFF.md`
- `P:\docs\handoffs\debrief-*\HANDOFF.md` (if present)
- relevant AAR/DEBRIEF scripts and generated run artifacts under
  `P:\.artifacts\` and `C:\Users\brsth\.grok\`.

Use `rg.exe --files` and source inspection before making absence claims.

## Research signals informing the proposal

These are supporting signals, not proof that the proposal is correct:

- Anthropic’s evaluator-optimizer guidance says iterative evaluation is most
  useful when criteria are clear and improvement is demonstrable; it also
  recommends simpler composable workflows and conditional complexity:
  <https://www.anthropic.com/engineering/building-effective-agents>
- Anthropic’s eval guidance emphasizes multiple graders, complete traces, and
  measuring behavior rather than relying on a single self-assessment:
  <https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents>
- Microsoft Research describes reflection as useful when it is tied to a
  revised attempt and feedback, not reflection in isolation:
  <https://www.microsoft.com/en-us/research/articles/experiential-reinforcement-learning/>
- A recent reflection benchmark argues that reflection quality and future
  failure avoidance should be evaluated separately:
  <https://arxiv.org/abs/2605.29225>
- Practitioner discussions repeatedly criticize feeding full histories back
  into agents, generic lessons, skillbook bloat, and self-critique without an
  external check:
  <https://www.reddit.com/r/LLMDevs/comments/1t09uei/lessons_learned_building_agents_in_production/>
  <https://www.reddit.com/r/ClaudeWorkflows/comments/1td2qac/workflow_agent_selfimprovement_skill_for_claude/>

The research supports the general direction—ground reflection, preserve
actionable memory, and make expensive loops conditional—but it does not prove
that the current AAR/DEBRIEF implementation satisfies those properties.

## Review deliverable

Return:

1. `ACCEPT`, `ACCEPT_WITH_CHANGES`, or `REJECT`.
2. A compact claim ledger:

   | Claim | Type | Evidence | Confidence | Falsifier | Action |
   |---|---|---|---|---|---|

3. The actual overlap and differences between AAR and DEBRIEF.
4. The minimum safe architecture for reducing latency/token cost.
5. Which stages must remain mandatory for every substantive close.
6. Which stages may be conditional, cached, parallelized, or delegated to a
   cheaper model.
7. A proposed acceptance test using at least three representative sessions:
   - a clean completed session;
   - a session with deferred/non-closed work;
   - a session with a correction, failure, or verification dispute.
8. Any changes that should be made to `/close`, `/aar`, `/debrief`, or their
   artifacts—but do not implement them during this review.

## Decision boundary

Do not recommend removing DEBRIEF merely because AAR sounds broader. Confirm
the source-level behavior and artifact contracts first. If AAR is the canonical
replacement, recommend a compatibility alias and migration period rather than
silently deleting historical DEBRIEF artifacts.
## Embedded source bundle

The following are the active source definitions copied into this packet so a
cold-start reviewer can review the proposal without access to the original
workspace. Snapshot date: 2026-07-25. Paths identify the source of truth from
which each block was copied.

### AAR — `C:\Users\brsth\.grok\skills\aar\SKILL.md`

```text
Exit code: 0
Wall time: 0.4 seconds
Total output lines: 950
Output:
Active code page: 65001
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

source-manifest.json · canonical-events.jsonl · active-timeline.json · superseded-events.jsonl · event-index.json · signals.json · aggregates.json · claim-evidence.json · parser-warnings.json · timeline.md · preprocess-summary.md · context-selection.json

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

- Read `preprocess-summary.md`, `context-selection.json`, `signals.json`, `aggregates.json` for initial context
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

### Double-loop analysis (mandatory when a CORRECTION or REVERSAL was identified)

Single-loop learning asks "what went wrong and how to fix it." Double-loop
learning asks "why did we believe this was the right thing to do?" — it
challenges the governing assumption, not just the action. Source: Chris
Argyris (1976); Esther Derby ("Promoting Double Loop Learning in
Retrospectives").

For each significant CORRECTION or REVERSAL in the session:

```text
1. GOVERNING_ASSUMPTION — what did we believe was true when we made the original decision?
2. ASSUMPTION_ORIGIN    — where did this belief come from? (training prior? prose rule? prior session? inference?)
3. ASSUMPTION_VALIDITY  — is the assumption still valid? If not, what changed?
4. COUNTERFACTUAL       — what would we have done differently if we'd known then what we know now?
5. EARLY_WARNING_SIGNAL — what signal would have alerted us to the wrong assumption earlier?
```

This block is mandatory when the Decision History (Phase 3) contains any
CORRECTION or REVERSAL. Skip if no corrections occurred (a clean session
has no governing assumptions to challenge).

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
(`__lib/refer…2003 tokens truncated…hon P:/.agents/scripts/dirty_age.py
   ```
   Or equivalent inline: for each file in `git status --short`, check
   its filesystem mtime. Flag any dirty file older than 7 days as a
   must-clean-before-close. These accumulate when other sessions modify
   files but never commit at the parent level (submodule pointers,
   deleted files, stale logs). The operator should not have to discover
   these weeks later — the AAR surfaces them proactively.

   Categories of stale dirty files to handle (after 7 days, all are
   abandoned — commit regardless of session ownership):
   - **Submodule dirty working tree** (`m` second-column status): commit
     the changes inside the submodule, then advance the parent pointer
   - **Submodule pointer moved** (`M` first-column status): commit the
     new pointer at the parent level
   - **Deleted files never removed** (`D` status): `git rm` them
   - **Modified tracked files** (`M` status): commit them
   - **Untracked files** (`??` status): evaluate whether to add or
     `.gitignore` them

### Output (appended to the report's §Open work section)

```markdown
## Session-close triage

### Must do before close (data loss / state risk)
- [ ] Commit uncommitted changes: <list of files>
- [ ] Write handoff for: <workstream name>
- [ ] Wait for / abandon subagent: <subagent_id>

### Properly handed off (safe to defer)
- <workstream> — handoff at <path>
- <workstream> — handoff at <path>

### No action needed
- All work committed and pushed
- All open workstreams have handoffs
- No dangling intent-to-write
```

### When this step finds nothing

If everything is committed, handed off, and no subagents are running,
emit: "Session-close triage: all clear. Work is committed, open
workstreams are handed off, no in-flight subagents."

### Why this step exists

Session 2026-07-24: the operator asked "what do you think I would want
to finish before closing this session?" mid-AAR. The answer (commit
uncommitted work + add two AGENTS.md pointers) was obvious to the
operator but not surfaced by the AAR skill itself. The skill was
producing a retrospective report without checking whether the session's
artifacts were actually safe to leave uncommitted. This step makes the
safety check structural, not dependent on the operator remembering to ask.

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

## Uncaptured knowledge (conditional — emit only when question 11 produces non-empty output)
Tacit knowledge from this session not preserved in any artifact, handoff, wiki
concept, or commit — that would be expensive to rediscover. This section is
**adversarial to the report's own accounting**: it targets what nobody noticed,
not what was noticed but deferred. This is NOT §Open work (which tracks known
unfinished tasks). This section tracks tacit knowledge that was never flagged as
a task at all. Apply value-triage: "what would a reviewer 3 months from now wish
had been captured?" Discard items that are trivially rediscoverable or already
preserved. **Cross-model note:** if the AAR synthesis is same-model, tacit gaps
rooted in model-family blind spots may be invisible here. The `cross-model-audit`
reference (now default-on) mandates a `/agy` or `/codex` pass on the
preprocessor packet (NOT the raw transcript — ~8-15KB compressed) for "what
did the primary model miss?" — see `references/cross-model-audit.md`.

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

## Phase 9.5 — Automatic wiki promotion of headline lessons

**This step runs automatically after the AAR report is written.** No user
intervention needed. The operator should not have to remember to run
`/wiki` after `/aar` — lessons that survive the calibration gate are
durable findings the wiki should capture.

### Which lessons qualify

Promote lessons that meet ALL of:

- **Scope:** `PROBLEM_CLASS` or `GENERAL` (not `SESSION_SPECIFIC` — too
  narrow for the wiki)
- **Confidence:** `OBSERVED` or `INFERRED` (not `SPECULATIVE` — the
  wiki should not store untested hypotheses)
- **Not already in the wiki:** run the retirement check (search for
  related concepts via `qmd search`; if a concept already covers the
  lesson, refine it instead of creating a duplicate)

`SESSION_SPECIFIC` lessons stay in the AAR report only. They are valuable
for the session record but not durable enough for the wiki.

### Procedure

For each qualifying lesson:

1. **Retirement check.** Search `qmd search --collection wiki "<lesson
   title>" --limit 10`. For each result in `concepts/`:
   - If the existing concept **supersedes** the lesson → skip (already
     documented)
   - If the existing concept **contradicts** the lesson → flag in the
     AAR report; do not auto-write (needs operator resolution)
   - If the existing concept is **refined** by the lesson → add a
     `relations` entry to the existing concept pointing to the lesson,
     and add a cross-reference from the lesson to the existing concept

2. **Write the wiki concept.** If no existing concept covers the lesson,
   write `P:/.data/wiki/concepts/<slug>.md` with:
   - Frontmatter per SCHEMA.md §2-3 (including `host:`, `agent:`,
     `verification:`, `cognitive_load:`)
   - Body: the lesson's direct observation, causal interpretation,
     competing explanations, scope, counterexample, and confidence
   - Source citation: the AAR run_dir path + session ID

3. **Run the wiki post-write pipeline.**

   ```bash
   python P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/wiki_ingest.py \
     --post-write "<concept-path>" \
     --notes "AAR auto-promoted lesson from session <session-id>" \
     --session-id "<session-id>"
   ```

   This handles auto-link, contradiction scan, qmd update, and log append
   in one call.

4. **Report which lessons were promoted.** In the AAR report, add a
   "Wiki promotion" subsection listing:
   - Each promoted lesson's wiki path
   - Each skipped lesson with reason (`SESSION_SPECIFIC`, already in wiki,
     `SPECULATIVE`, etc.)
   - Each refined concept with the `relations` entry added

### When to skip Phase 9.5

- `--lite` mode: skip wiki promotion (lessons stay in the report only)
- No headline lessons in the report: skip (nothing to promote)
- All lessons are `SESSION_SPECIFIC`: skip (none qualify)
- Operator explicitly says "don't wiki": skip (respect user override)

### Falsifier

If the wiki promotion creates a concept that a future session cannot find
via `qmd search`, the promotion failed. If it creates a duplicate of an
existing concept, the retirement check failed. Either failure requires
iterating this section.

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

   **Secret exposure severity triage (mandatory before assigning CRITICAL/HIGH to a `secret_exposure_in_tool_output` signal):**
   Before escalating a secret-exposure signal to CRITICAL or HIGH, the orchestrator MUST verify the actual exposure surface by checking:
   1. **Is the file containing the secret tracked in any git repo?** Run `git ls-files --error-unmatch <path>` in the repo root. If the file is NOT tracked (gitignored or outside any repo), the secret did not reach any remote.
   2. **Is the transcript/session dir tracked or synced?** Run `git ls-files` against the session directory's parent. Session transcripts at `~/.grok/sessions/` are typically gitignored.
   3. **Is the containing repo public or private?** If the repo is private and the file is gitignored, the exposure is local-only.

   If the secret is in a gitignored file in a private repo (local-only exposure), downgrade the severity from CRITICAL/HIGH to **LOW** with the note: "local-only exposure; secret is in gitignored file; no remote exposure detected." Still recommend prevention (filter reads of config files) but do not treat as an active incident requiring key rotation.

   If the secret IS tracked in git, or the repo is public, or the file was pushed, keep CRITICAL and follow the containment protocol (rule 3b).

   **Why this exists:** Session 019f8507 (2026-07-21) had a `secret_exposure_in_tool_output` signal for an API key in `~/.grok/config.toml`. The AAR elevated it to CRITICAL. The key was in a gitignored file in a private repo — local-only exposure. The CRITICAL rating was a false positive that wasted operator attention on key rotation that wasn't needed.
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
```

### DEBRIEF — `C:\Users\brsth\.grok\skills\debrief\SKILL.md`

```text
Exit code: 0
Wall time: 0.5 seconds
Output:
Active code page: 65001
---
name: debrief
description: >
  Smart session retrospective. Scans the current session for actionable improvements
  across 5 lenses: root causes, code quality, workflow friction, knowledge gaps, and
  patterns. Uses model-tier-aware subagent fan-out (5 parallel lens subagents +
  verifier + critic) with automatic model fallback when primary models are out of
  quota or unreachable. Produces ranked, evidence-cited findings with suggested actions.
  Use when: the user says /debrief, "what should we learn", "retrospective", "what went
  wrong", "improve from this session", "what patterns do you see", or at the end of a long
  session.
metadata:
  short-description: "Session retrospective: 5-lens fan-out, model-tier-aware, self-verifying"
---

# /debrief — Adaptive Multi-Phase Session Retrospective

## Purpose

Mine the current session for actionable improvements with **the highest accuracy possible**. Don't just summarize — find durable lessons, root causes, and friction points that will make the next session better.

The skill uses a **5-phase adaptive pipeline** with **model-tier-aware subagent fan-out**. Different lenses run on different models optimized for the task. Models are health-checked before use and fall back automatically if quota is exhausted or unreachable.

---

## Model Selection Strategy

The skill picks the **best model per task** with explicit fallback chains. Before spawning any subagent, the parent **probes** the primary model; if unhealthy, it walks the fallback chain.

### Selection Priority

| Source | Reliability | Cost | When to prefer |
|--------|-------------|------|----------------|
| **Direct providers** (MiniMax, Z.ai, Mistral) | Highest (your keys, your quota) | Token-priced | Always first choice |
| **Subscription pool** (OpenCode Go) | Medium (quota caps) | Subscription | When direct isn't specialized enough |
| **Aggregator free** (OpenRouter `:free`, Zen free) | Variable | Free | Last resort; rate-limited |
| **Native** (grok-4.5) | High | Token | When subagent features are gated |

### Per-Lens Model Chains

Each lens has a primary model and explicit fallbacks. The skill **probes** the first model, then falls back if the probe fails.

#### Lens 1: Root Causes (deep causal reasoning)
1. `glm-5-2` — direct Z.ai, strong reasoning, 1M ctx
2. `minimax-m3` — direct, your workhorse
3. `grok-4.5` — native, high effort
4. `or-hy3-free` — free, fresh perspective

#### Lens 2: Code & Config Quality (code specialist)
1. `go-kimi-k2-7-code` — code-specialist training
2. `go-deepseek-v4-flash` — fast code worker
3. `or-qwen3-coder-free` — coding-shaped free
4. `minimax-m3` — fallback if Go quota exhausted

#### Lens 3: Workflow Friction (general reasoning)
1. `minimax-m3` — workhorse
2. `glm-5-2` — reasoning-heavy
3. `grok-4.5` — native
4. `zen-big-pickle` — stealth free alternative

#### Lens 4: Knowledge Gaps (fresh perspective)
1. `mistral-medium-latest` — different model, fresh eyes
2. `or-hy3-free` — free, different family
3. `minimax-m3` — fallback
4. `glm-5-2` — reasoning

#### Lens 5: Patterns (cross-cutting analysis)
1. `glm-5-2` — best at abstraction
2. `minimax-m3` — general
3. `grok-4.5` — native
4. `zen-big-pickle` — stealth alternative

#### Verifier (Phase 3, code/config findings only)
1. `go-kimi-k2-7-code` — primary
2. `or-qwen3-coder-free` — fallback
3. `minimax-m3` — last resort

#### Critic (Phase 4, self-quality meta-check)
1. `mistral-medium-latest` — different from analysis model
2. `or-hy3-free` — free different family
3. `minimax-m3` — fallback

**Always pick a model different from the one that produced the finding for critic/verifier** — diversity catches blind spots.

---

## Pre-Flight: Model Health Probing

Before spawning any subagent, **probe** the primary model with a tiny request. A probe is:
- `max_tokens: 8` (or `max_completion_tokens: 8` for OpenAI-compatible)
- prompt: `"Reply OK only."`
- timeout: 30s
- treat any non-2xx as failure

**Probe procedure** (in shell, before `spawn_subagent`):

```bash
# Pseudocode - the actual probing is done in the parent's shell
for model in chain; do
  result=$(curl ... -d '{"model":"'$model'","max_tokens":8,"messages":[...]}')
  if [ $? -eq 0 ]; then
    SELECTED_MODEL=$model
    break
  fi
  # Log failure for transparency
done
```

**Optimization: cache probe results** for the session duration. A model that responded once is likely still healthy. Only re-probe after a subagent failure.

**Adaptive probe skipping:** if `grok models` failed earlier in this session for a model, skip probing it.

---

## The 5-Phase Pipeline

### Phase 0: Discovery (parent, fast)

Before analyzing, gather context:

1. **Read `P:/.data/wiki/log.md`** to see what's already persisted (avoid duplication)
2. **Scan `~/.grok/config.toml`** for the current model catalog (know what's actually reachable)
3. **Count session turns** to choose mode:
   - ≤20 turns → use **Light mode** (no subagents, single model)
   - 21-100 turns → **Standard mode** (5 lens subagents, no critic)
   - >100 turns → **Deep mode** (5 lens + verifier + critic)
4. **Note recent wiki pages** — flag findings that overlap existing concepts for dedup

**Step 0.5: Pattern-library query (NEW 2026-07-25, mandatory before Phase 1)**

Query the wiki for prior debrief findings matching this session's shape. Turns `/debrief` from a one-shot retrospective into a cumulative-knowledge system — each retrospective builds on prior ones instead of re-deriving.

```powershell
# Query the local wiki for prior friction/root-cause patterns
qmd search --collection wiki --query "<session-shape keywords from Phase 0 scan>" --top-k 5
# Fallback: grep wiki concepts directly for tags matching the session domain
```

**What to look for:**
- A wiki concept whose `summary:` describes the same friction pattern, root cause, or workflow gap
- A concept whose `tags:` match (e.g., `closure-pressure`, `model-bypass`, `context-momentum`, `friction-detection`)

**If a known pattern matches:**
1. State the match in the Discovery output: "Prior pattern found: [[<concept-slug>]] (confidence: high/medium/low)"
2. Provide the matching concept(s) to each Phase 1 lens subagent as prior context — they should verify or disconfirm against current session evidence, NOT re-derive from scratch
3. If disconfirmed, note it (this is itself a finding — the prior pattern didn't apply)

**If no match:** proceed normally. The absence of a prior pattern means novel findings are likely — flag for Phase 5 wiki-save.

**Reference:** `/why` Step 0.5; wiki concept `wiki-integrated-skills-query-save-pattern`. This is the closed-loop complement to Phase 5's save step (below).

**Output:** a brief "discovery report" the parent uses internally, now including prior-pattern matches (or "no match — candidate new pattern").

### Phase 1: Parallel Lens Analysis (subagent fan-out)

For each lens, spawn a subagent with the **probed-healthy primary model** (or first healthy in fallback chain):

```python
# Conceptual pseudocode for the parent
for lens in [root_causes, code_config, workflow, knowledge, patterns]:
    model = select_healthy_model(lens.chain)  # probe + fallback
    spawn_subagent(
        subagent_type="explore",
        model=model,
        capability_mode="read-only",
        prompt=f"""
You are analyzing session {session_id} for the '{lens.name}' lens.
Session conversation: <read via tools>
Findings schema: {{title, symptom, root_cause, naive_assumption, evidence, action, structural_fix, falsifier}}
Return ONLY the structured findings, max 5 per lens, ranked by priority.
"""
    )
```

**Why parallel:** 5x faster than sequential, no cross-contamination, diversity across models.

**Failure handling:** if a subagent fails (model down, timeout, auth error), retry with next model in chain. If all fail for that lens, note "Lens X: all models exhausted, skipped" in the final report.

### Phase 2: Cross-Lens Synthesis (parent)

Parent reads the 5 lens outputs and:

1. **Deduplicate** findings that span lenses (a root cause that's also a pattern)
2. **Detect cross-cutting patterns** — highest-leverage findings often appear in 2-3 lenses
3. **Rank** using the rubric:
   - 🔴 **Critical** (max 3): root cause that will recur, structural fix exists, high blast radius
   - 🟡 **Important**: cost significant time, easy fix
   - 🟢 **Nice-to-have**: minor improvement
   - ⚪ **Skip**: already documented, already fixed, or too speculative
4. **Flag wiki candidates** (dedup against `log.md` and recent concepts/)

### Phase 3: Verification (subagent for 🔴 Critical findings)

For each 🔴 Critical finding, spawn a verifier subagent:

```python
# For code/config findings, verify against source
if finding.category in ["code", "config"]:
    verifier_model = select_healthy_model(VERIFIER_CHAIN)
    spawn_subagent(
        subagent_type="explore",
        model=verifier_model,
        capability_mode="read-only",
        prompt=f"""
Verify this finding against actual source:
  Finding: {finding}
  Cited evidence: {finding.evidence}
Read the cited files/tools and confirm or refute.
"""
    )
```

**Adaptive:** only verify 🔴 Critical, not all findings. Skip verification if Critical findings have no citable evidence (just subjective observations).

### Phase 4: Self-Quality Meta-Check (critic subagent)

Spawn a critic on a **different model** from the analysis models:

```python
critic_model = select_healthy_model(CRITIC_CHAIN)
# Pick a model that wasn't used in Phase 1
if all(used_models) and critic_model in used_models:
    critic_model = pick_unused(critic_chain)

spawn_subagent(
    subagent_type="explore",
    model=critic_model,
    capability_mode="read-only",
    prompt=f"""
Review this retrospective for quality:
  Findings: <all>
  Format: 🔴 max 3, 🟡 next 5, 🟢 rest
  
Questions:
1. Are 🔴 findings actually critical, or inflated?
2. Are claims evidence-cited (specific tool calls, files, turns)?
3. Are any obvious patterns missed?
4. Did any lens return zero findings? Is that suspicious?
5. Any claims that contradict established docs/code?

Return: AGREE / DISAGREE with specific feedback per finding.
"""
)
```

If the critic disagrees, parent re-reviews before presenting.

### Phase 5: Present + Offer + Auto-save wiki-worthy findings

Standard output format (unchanged from prior version), then:

**Step 5a: Auto-save wiki-worthy findings (NEW 2026-07-25)**

Per wiki concept `wiki-integrated-skills-query-save-pattern`, systemic findings should auto-save to the wiki (not just be offered as `/wiki` ingest). The mechanical gate decides which findings qualify — model self-assessment under closure pressure is not the gate.

A finding is wiki-worthy ONLY if ALL of:
1. **Classification is structural** (root cause with a structural fix, OR a cross-session pattern) — not session-specific one-offs
2. **Has a falsifier** (the finding section produced a meaningful test, not a tautology)
3. **Has evidence citation** (specific tool call, file, or turn — not narrative)
4. **Named abstractly** (slug describes the PATTERN, not the incident — e.g., `closure-pressure-manufactures-bypass` not `2026-07-25-close-skip`)
5. **Cross-session reusable** (would apply to a future session in a different subsystem)
6. **Not already in the wiki** (Phase 0.5 query would have surfaced it; if it did, refine instead of duplicate)

If all 6 pass: write to `P:/.data/wiki/concepts/<slug>.md` per `P:/.data/wiki/SCHEMA.md` frontmatter, then log via `append_log.py`.

If any fails: keep the finding in the debrief output only; do NOT write to wiki.

**Reference:** `/why` Step 15 mechanical gate; wiki concept `wiki-integrated-skills-query-save-pattern`. This closes the loop with Phase 0.5 — future retrospectives query and find these patterns.

**Step 5b: Offer remaining actions**

1. Fix top Critical now?
2. Create tasks?

(The `/debrief --wiki` flag becomes redundant — auto-save is now the default for qualifying findings. The flag remains as a manual override for cases where the operator wants explicit control.)

---

## Adaptive Modes

User can override mode via flag, or auto-detect:

| Mode | Subagents | Use when |
|------|-----------|----------|
| `/debrief` (auto) | Based on turn count | Default |
| `/debrief --light` | 1 (single model, sequential) | Short sessions, quick scan |
| `/debrief --standard` | 5 lens (no critic, no verifier) | Routine end-of-session |
| `/debrief --deep` | 5 lens + verifier + critic | Major debugging, pre-release |
| `/debrief --wiki` | Standard + auto-ingest wiki candidates | After debrief, persist findings |
| `/debrief --quick` | Lens 1 + Lens 5 only | Fast root-cause + pattern scan |

**Auto-detection rules:**
- ≤20 turns → light
- 21-100 turns → standard
- >100 turns OR user says "deep" → deep
- User says "quick" → quick

---

## Output Format

```markdown
# Session Debrief — <YYYY-MM-DD>

## Discovery
- Session turns: <N>
- Mode: <auto-detected | light | standard | deep>
- Wiki log entries this month: <N>
- Models used: <list per phase>

## 🔴 Critical (fix these first)

### 1. <finding title>
- **Lens:** Root Cause | Code | Workflow | Knowledge | Pattern
- **Model used:** <model id>
- **What:** <concise description>
- **Evidence:** <tool call / file / turn>
- **Action:** <specific next step>
- **Structural fix:** <what prevents this class of problem>
- **Falsifier:** <what would prove this finding wrong>
- **Verified:** ✅ by <verifier-model> | ⚠️ unverified | N/A

### 2. ...

## 🟡 Important (next 5)

### 3. ...

## 🟢 Nice-to-have

### 4. ...

## Patterns Observed
- <pattern>: <evidence>

## Wiki Candidates
- <finding>: worth saving? [Y/N]

## Model Usage Report
| Phase | Model | Status | Notes |
|-------|-------|--------|-------|
| Lens 1 | glm-5-2 | ✅ healthy | primary |
| Lens 2 | go-kimi-k2-7-code | ⚠️ fallback | primary exhausted, used go-deepseek-v4-flash |
| ... | | | |

## Nothing Found
- Lens X: no findings this session (explicit)
```

---

## Quality Gates

### Anti-patterns

- ❌ **Vague summaries** — be specific
- ❌ **Blame the user** — findings are about systems
- ❌ **No evidence** — every finding cites a tool call, file, or turn
- ❌ **Too many findings** — max 3 Critical
- ❌ **No structural fix** — name the mechanism
- ❌ **Same model for analysis and verification** — diversity is the point
- ❌ **Skip mode detection** — auto-pick based on session length

### Trust Boundaries

- **Probes can lie** — a 200 OK doesn't guarantee the next call works. The first subagent failure should re-probe.
- **Subagent outputs are untrusted** — parent must verify against actual session tool calls, not just trust the subagent's summary
- **The skill itself can fail** — if `spawn_subagent` is unavailable, fall back to single-model sequential mode in the parent context

---

## Failure Recovery

| Failure | Recovery |
|---------|----------|
| `spawn_subagent` unavailable | Fall back to single-model sequential analysis in parent context |
| All models in a chain fail for one lens | Skip that lens, note "exhausted" in report |
| Probe returns 200 but real call fails | First subagent failure → re-probe, retry with next in chain |
| Critic subagent returns empty | Skip critic, present without meta-check, flag in output |
| Wiki write fails during `/wiki` ingest | Surface the error, don't fail the entire debrief |

---

## Integration with Other Grok Skills

| Follow-up | When |
|-----------|------|
| `/wiki` | After debrief, to persist durable findings to the shared vault |
| `/review` | If code findings need verified review against source (debrief's verifier is usually enough) |
| `/check-work` | If findings suggest the current work needs verification |

Debrief finds. Wiki persists. Review verifies.

---

## Implementation Notes

The skill is **prompt + structure**, not code. The parent session orchestrates:

1. **Phase 0**: a few tool calls (read log.md, scan config, count turns)
2. **Phase 1**: 5 `spawn_subagent` calls (parallel where possible)
3. **Phase 2**: parent's own reasoning to synthesize
4. **Phase 3**: 0-3 more subagent calls for verification (only 🔴 Critical)
5. **Phase 4**: 1 critic subagent call
6. **Phase 5**: parent's output formatting + offer to user

**Token budget:** ~2.5x single-model in Standard mode, ~4x in Deep mode. Acceptable because retrospective runs occasionally, not on every turn.
```

### CLOSE — `C:\Users\brsth\.grok\skills\close\SKILL.md`

```text
Exit code: 0
Wall time: 0.4 seconds
Output:
Active code page: 65001
---
name: close
description: >
  Session close-out orchestrator. Runs close_accounting.py to scan handoffs,
  wiki, git commits, temp files, git status, and AAR artifacts — resolving
  all gates mechanically. Emits a summary template with pre-computed gate
  states. The final report is organized for human scanning: status first,
  open risks next, then completed work and supporting detail.
  Loops only when a concrete gap is detected. Use for /close, session end,
  wrapping up, "anything left?".
argument-hint: "[--quick|--deep] [--no-loop]"
user-invocable: true
host: grok
---

# /close — session close-out orchestrator

## Principle

**The scanner thinks; the LLM judges.** `close_accounting.py` scans all
evidence sources, resolves every gate to a state, computes the loop decision,
and emits a summary template. The LLM reads the output and fills in only the
judgment fields.

## Division of labor

| Task | Mechanism | Why |
|------|-----------|-----|
| Scanning handoffs/wiki/git/AAR | **Code** | Mechanical; same logic every time |
| Gate resolution (14 gates) | **Code** | Deterministic rules on scan results |
| Loop decision | **Code** | Derived from gate states |
| Summary template | **Code** | String formatting from scan results |
| ACCOUNTING buckets (done/partial/not-started) | **Prompting** | LLM judgment from session context |
| "Not verified yet" assessment | **Prompting** | Requires understanding what was claimed |
| "Next safe action" | **Prompting** | Requires session-context judgment |
| Running /wiki, /aar, /handoff, /check | **Agent** | Each is a full skill with own SKILL.md |

---

## SDLC stage

**Stage:** SHIP/CLOSE — session close-out, knowledge persistence, handoff completion (terminal stage)
**Control plane:** tasks (operator-assigned) + handoffs (`P:\docs\handoffs\<topic>-<date>\HANDOFF.md`)

### Entry state — work is ready when
- Session is ending ("are we done?", "wrapping up", "anything left?", "what are we forgetting?")
- Or: a coverage question surfaces mid-session (fires at any point, not just close)
- Substantive work was done this session

### Better fit — route out when
- Mid-task check-in ("how's it going?") → status update, not close
- Retrospective is the goal (not close) → `/aar` or `/debrief`
- Work isn't done → `/go` to continue

### Exit transitions (at SESSION CLOSED)
| Outcome | Recommend |
|---|---|
| Close clean, all gates satisfied | next session reads handoffs + wiki |
| Open handoffs remaining | next session: `/handoff list`, pick up `status: open` |
| AAR produced opportunities | operator triages OPP-N items into future tasks |

Reference: `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md` (lifecycle mapping) and `trust-escalation-ladder-autonomous-agent-work.md` (close is the shipping boundary).

---

## Step 1 — Resolve identity and run scanner

```powershell
# Resolve the current session ID. On Grok Build, GROK_SESSION_ID and
# CLAUDE_SESSION_ID are NOT exported to shell subprocesses — they are
# empty in the shell. The LLM knows its own session ID from system
# context (it appears in the prompt file path, compaction segment
# paths, and the session directory). Inject it as a literal here.
# Example: $sess = "019f94c9-43c1-7b31-87c4-980fdd3047e8"
$sess = $env:GROK_SESSION_ID; if (-not $sess) { $sess = $env:CLAUDE_SESSION_ID }
if (-not $sess) { $sess = "LLM_FILL_FROM_CONTEXT" }  # replace with actual UUID
```

Then run the scanner (one tool call):

```powershell
python ~/.grok/skills/close/__lib/close_accounting.py --session $sess --variant standard --format compact
```

**Use `--format compact` (the default)** for the scanner — it shows outstanding items first and collapses satisfied gates to a count. The scanner output is input to the close workflow, not the final user-facing report. Use `--format summary` for verbose gate-by-gate debugging. Use `--format json` for programmatic consumption.

## Step 2 — Read gate states and act

Each gate has one of four states:

| State | Action | Output |
|-------|--------|--------|
| `pre_satisfied` | **Nothing.** Mechanical evidence confirms the gate is met. | One line in summary |
| `needs_attention` | **Resolve the gap** using the tier system below. | Gate finding + resolution |
| `needs_llm_check` | **Check conversation context.** Emit one-sentence verdict. | One line in summary |
| `skip` | **Nothing.** Gate not applicable. | Omit from summary |

**Critical:** do NOT walk through `pre_satisfied` or `skip` gates step-by-step.
One line each in the summary. No paragraphs.

### Tier system (how to resolve `needs_attention` gates)

| Tier | Auto-resolve? | Examples |
|---|---|---|
| **Tier 1 — local, reversible** | **Yes — just do it.** No operator prompt. | Copy durable temp files to `P:/docs/`; reindex skill catalog; append wiki log; write session-observations handoff |
| **Tier 2 — shared state, reversible** | **Yes with one-word confirmation.** Single prompt, not a menu. | Stage this-session changes for manual review; promote a wiki concept that touches shared frontmatter |
| **Tier 3 — irreversible or external** | **Recommend only.** Surface the finding + a verb-based recommendation. Operator decides. | Delete temp files; push commits; modify other sessions' work |

**Principle:** if the action is local and reversible, doing it is cheaper than asking about it. The close summary lists every Tier-1 action taken so the operator can audit.

**Never auto:** delete files, push to remote, commit other sessions' work.

### Gate-specific guidance

**Wiki** (`needs_attention`): session did substantive work but has 0 wiki concepts.
Ask: "Run /wiki to distill findings?" If operator declines, note it and proceed.

**Retrospective** (`needs_attention` when substantive work happened and no AAR artifact exists): **auto-invoke `/aar` — do not recommend it, run it.** When this gate is `needs_attention`, load and execute the full `/aar` SKILL.md workflow (`C:\Users\brsth\.grok\skills\aar\SKILL.md`) against the current session. The AAR is a mandatory close-time step, not an optional recommendation. It includes critical session-close safety checks (Phase 8.5: stale dirty files >7 days, uncommitted work, dangling intent-to-write, in-flight subagents, unhanded-off work) that must fire before the session is declared closed. The close orchestrator runs the AAR, incorporates its findings into the close summary, then continues resolving remaining gates.

**Session observations** (`needs_attention`): no session-observations handoff from
this session. Write one only if the session produced observations worth capturing —
patterns noticed, ideas for future work, workflow insights, meta-observations,
brainstormed ideas not yet developed into tasks.

Write to `P:\docs\handoffs\session-observations-<YYYYMMDD>\HANDOFF.md` with
standard handoff chain header (`current_session_id` matching this session).

Each item gets a one-sentence description and source reference (session ID +
context). Include anything the operator flagged as "worth capturing."

What does NOT go here:
- Concrete tasks with file paths → regular handoff
- Verified findings → wiki concept
- Decisions → decisions gate auto-promotion
- Failures/friction → `/aar` opportunity landscape

If there are genuinely no observations this session, do not write an empty
handoff. Instead, note in the close summary: "No observations this session
(unusual — most substantive sessions produce at least one)." The absence of
observations is worth surfacing because it is unusual, not because it needs
a file.

**Handoffs** (`needs_attention`): the handoff gate is now **coverage-aware**.
Having handoffs no longer automatically satisfies the gate. The scanner runs
the continuation coverage system (`continuation_coverage.py`) which extracts
continuation candidates from AAR artifacts, session transcript goals, and
session-observations seeds, then reconciles each against existing handoffs.
If material candidates are uncovered, the gate forces `needs_attention`.

**How to resolve:** read the coverage ledger at the path shown in the gate
detail. For each uncovered material candidate, assign a terminal disposition:
`COMPLETED`, `EXISTING_HANDOFF`, `HANDOFF_UPDATE`, `NEW_HANDOFF`,
`MERGED_INTO_PARENT`, `WIKI_ONLY`, `MONITOR`, `REJECTED`, `NOT_WORTH_DOING`,
`INTENTIONALLY_DROPPED`, or `NEEDS_USER_DECISION`. Update the ledger file.
Re-run the scanner to verify coverage is now complete.

**Tier rules for coverage gaps:**
- Clear, local, reversible handoff creation/update → **Tier 1** (just do it)
- Ambiguous split/merge decision → **Tier 2** (one concise operator question with recommendation)
- `NEEDS_USER_DECISION` → blocks only that candidate, not the entire close

**Continuation coverage** (separate gate): reports coverage status explicitly.
`pre_satisfied` when all material candidates have defensible dispositions.
`needs_attention` when material candidates are uncovered. `needs_llm_check`
when AAR is unavailable (degraded mode — manual coverage check needed).

**Key invariant:** artifact persistence ≠ continuation coverage. Committed
handoff files prove artifacts were preserved; they do not prove every material
goal, unresolved question, enabling capability, or continuation opportunity
received a durable disposition.

**Verify** (`needs_llm_check`): scanner checks both the parent transcript and durable
`P:/.artifacts/<term>/grok-check/**/check-state.md` receipts bound to the current
session. A `/check` receipt is authoritative evidence for the verifier concerns
it covers, even though the child verifiers' commands are absent from the parent
transcript. It is not proof that every live/runtime acceptance test ran. Report
the two facts separately: `static /check: PASS (N/N verifiers)` and
`live/runtime: <PASS, GAP, or not applicable>`. If neither source has evidence,
emit `no verification evidence found`. **Do not emit "Verify: PASS" here** —
that determination is made in Step 4.1's receipt check, which cross-references
the "Not verified yet" field.

**Temp files** (`needs_attention`): scanner found files in `P:/tmp/` or `%TEMP%/grok-*`
produced this session. These are at risk of OS reaping (Storage Sense, reboot).

**Never auto-delete.** Deletion is Tier 3 (irreversible). Instead, emit a
**structured temp-file table** and let the operator decide with a one-word
response. The table groups files by pattern, shows count + total size, and
gives a recommendation per group. The operator can say "delete all",
"delete groups 1-3", "keep all", or anything in between.

**Build the table by classifying each file into a group:**

| Group | Pattern | Recommendation | Rationale |
|-------|---------|----------------|-----------|
| **Disposable** | `check_*.py`, `inspect_*.py`, `verify_*.py`, `debug_*.py`, `trace_*.py`, `*_probe*.py`, `patch_*.py`, `trial*.py`, `commit-msg-*.txt`, `measure_*.py` | Safe to delete | One-off scripts and commit-message temp files with no reuse value |
| **Output captures** | `err.json`, `out.json`, `*_stderr.txt`, `*_stdout.txt`, `*.log` | Safe to delete | Captured command output; the source command is reproducible |
| **Design runs** | `grok-design-*`, `qmd-clean-*` | Leave alone | Self-contained dirs with their own lifecycle |
| **Durable value** | source-discovery JSONs, audit reports, evidence packets >10KB that don't match disposable patterns | **Tier 1: copy to `P:/docs/tmp-preserved-<YYYYMMDD>/`** before offering deletion | Contains evidence or analysis that would be costly to reproduce |
| **Uncertain** | files that don't match any pattern above | Ask per-file | <5% of files typically |

**Emit as a compact table in the close summary:**

```text
Temp files (59 files, 4994 KB):
  [DELETE]     14 disposable scripts (check_*, inspect_*, verify_*, etc.) — 28 KB
  [DELETE]      3 output captures (err.json, out.json, *.log) — 5 KB
  [KEEP]        1 design run dir (grok-design-*) — 4096 KB
  [PRESERVE]    1 evidence packet (preflight-quality-gate.json) — 202 KB → copied to P:/docs/tmp-preserved-20260724/
  [?]           0 uncertain
  → Delete disposable + output captures? (28 KB) Reply: yes / no / keep all
```

**Rules:**
- Always preserve durable-value files first (Tier 1), THEN offer deletion of the rest.
- State total size per group so the operator can see the disk impact at a glance.
- One question, not per-file. The operator can scope their answer ("delete groups 1-2 only").
- If operator says "yes": delete the disposable + output-capture groups only.
  Do NOT delete uncertain files without explicit per-file confirmation.
- If operator doesn't respond: leave all files. No silent deletion.

**Git state** (`needs_attention` if >10 files remain after auto-commit, `pre_satisfied` if auto-commit succeeded, `needs_llm_check` otherwise): the scanner extracts this session's write-paths from `chat_history.jsonl` tool-call history and **auto-commits them** (Tier-1, no confirmation). The scanner handles staging and committing; the gate reports what was committed.

If auto-commit succeeded: gate is `pre_satisfied` with commit SHA and file list. The remaining uncommitted files (from other sessions) are surfaced as a count only.

If auto-commit failed (e.g., git error, no write-paths found): the gate falls back to `needs_attention` with the full uncommitted count. The LLM should then recommend manual review.

**The scanner does NOT ask for confirmation.** Committing this-session files is reversible (`git reset`). The protection of committing outweighs the risk of committing an unwanted change.

**Cross-repo verification (runs regardless of whether auto-commit had files to commit).** The scanner's auto-commit only covers `P:\`. Sessions that also edit `~/.grok` (skills, config) or commit inside submodules leave state the scanner cannot see — even when auto-commit has nothing to commit (pre_satisfied with 0 files). `close_accounting.py` now runs both read-only checks and attaches their exit codes/output to the `git_state` gate:
```bash
python P:/.agents/scripts/git_state_check.py
```
Also run the stale-file check (runs in ALL variants including --quick, because --quick skips the retrospective gate which is the other path to dirty_age.py):
```bash
python P:/.agents/scripts/dirty_age.py
```
These check `P:\`, `~/.grok`, and submodule pointer/stale-file consistency. **Read the structured receipts and act on them before proceeding.** If either reports files matching this session's edits, commit and push them before declaring the git_state gate `pre_satisfied`. Do not dismiss output as "other sessions' work" without verifying that claim against the session's actual file edits. If output reports only genuinely other sessions' files, the gate remains a manual review item until that ownership judgment is recorded. **The completion claim is "the scripts ran clean," not "the scripts exist."**

**Background tasks** (`needs_llm_check`): scanner can't mechanically verify task completion.
Check the conversation: did any `spawn_subagent(background=true)` tasks start and not return?
If yes, either wait for them or note them as orphaned in the close summary.

**Decisions** (`needs_llm_check`): the scanner flags when substantive work was done but can't
identify decisions mechanically. The LLM identifies decisions from conversation context and
**auto-promotes** them — do NOT prompt the operator for routine decisions.

**Auto-promotion protocol (the core rule):**

1. Scan the conversation for decisions: architectural choices, option selections, convention
   adoptions, "we chose X over Y because Z" moments, design decisions from `/design` loops.

2. For each decision, classify the escalation level:

   | Signal | Action |
   |---|---|
   | Tactical/operational decision (reversible, low-stakes, obvious choice) | **Auto-promote** as a wiki Concept at `P:/.data/wiki/concepts/<slug>.md`. Write it directly. Do not ask. |
   | Architectural decision (hard to reverse, multi-month consequences) BUT format is clear (ADR vs Concept is obvious from context) | **Auto-promote** in the right format. Do not ask. |
   | Architectural decision AND format is ambiguous (could be either Concept or ADR) | **Escalate to operator**: "Should [decision] be a Concept or ADR?" One question, with a recommendation. |
   | Decision is already in a handoff or wiki concept | Skip — already captured. |

3. The escalation threshold is HIGH. Only escalate when:
   - The decision is architecturally significant (hard to reverse, multi-system impact), AND
   - The promotion format (Concept vs ADR vs nothing) is genuinely ambiguous, AND
   - You are <80% confident the operator would approve your auto-choice

   If all three conditions aren't met, auto-promote and note it in the close summary.

4. What to write for auto-promoted decisions:
   - **Concept**: decision + one-sentence rationale + alternatives rejected (one line each) + falsifier. Lightweight.
   - **ADR**: full solo-ADR format per `P:/.data/wiki/concepts/solo_operator_adr_best_practices.md` — adds shelf life, assumptions at risk, known failure modes, revert path.

5. Note every auto-promoted decision in the close summary: "Decisions promoted: [list]".

**Constraints sub-check (within the decisions gate):** when scanning the conversation for
decisions, ALSO scan for constraints — limitations discovered, compatibility issues, rate
limits, library breakages, "X doesn't work because Y" moments. Constraints are distinct from
decisions (you didn't choose them; they were imposed by reality). For each constraint:
- Wiki-worthy (general, reusable) → auto-promote as a wiki Concept
- Task-specific (only matters for this work stream) → note in the handoff
- Already in a wiki concept or handoff → skip

**Chain integrity** (`needs_attention`): scanner found handoffs with `parent_handoff_path`
pointing at files that don't exist. Fix the reference or mark as `none`. This prevents the
next session from following a dead pointer into wasted context reconstruction.

**Quota** (`pre_satisfied` always — informational only): scanner reads xAI billing usage from
`unified.jsonl`. This is NOT fleet quota — it's one provider's billing metric. The scanner
surfaces it in the summary as a rough signal. For authoritative fleet quota state (all 7+
providers), the operator should run `cc-ccr -Test`. This gate never blocks and never triggers
the loop.

**Wiki lifecycle** (`needs_attention`): scanner detected that wiki concepts were written this
session but the skill catalog (`index_skills.py`) hasn't been re-run. Run it:
`python P:/.data/wiki/scripts/index_skills.py`. This ensures the new concepts are findable
by semantic search next session. Per `P:/AGENTS.md` skill lifecycle maintenance rule.

**Referenced files** (`needs_attention`): scanner found file paths mentioned in handoffs that
don't exist on disk. This catches the "I said I'd write X but never did" failure mode — stated
intent to persist that was silently lost to conversation drift. For each missing file: either
write it now (if the content was supposed to be created this session) or remove the reference
(if the path was aspirational). Never leave dangling file references in handoffs — a fresh
session will try to read them and fail.

## Step 3 — Loop (only when scanner says needed)

```json
"loop": {"needed": true, "attention_gates": ["wiki", "handoffs"]}
```

If `loop.needed == true`:
1. Resolve each gate in `attention_gates` (ask operator or auto-resolve)
2. Re-run the scanner
3. Check if gates are now resolved
4. Max 2 iterations. If gap persists after iteration 2, note it and proceed.

If `loop.needed == false`: **skip to Step 4.** No ceremony.

`--no-loop` flag: resolve each gate once, never re-scan. Use when confident.

## Step 4 — Emit close summary

**Before filling in the summary, run `/tp session`** (session-end opportunity review).
This catches what the close gates miss: unversioned files, unresolved risks, unvalidated
assumptions, and blind spots the gate system doesn't cover. Run the NOW/NEXT/LATER/FILTER
protocol inline (session-state, no subagent spawn). Surface findings in the close summary's
"Not verified yet" or "Next safe action" fields. This is mandatory — the close gates are
mechanical and miss the "what should I care about?" question that `/tp session` answers.

Read the `summary` array from the scanner output. Fill in the `<LLM>` fields:

- **ACCOUNTING**: classify session work into done/partial/not-started from the
  `evidence.handoffs` list and session context. Each work item lands in exactly
  one bucket.
- **Not verified yet**: specific gaps (e.g. "spawn_subagent untested post-config-fix")
  or "none". Never "everything should work".
- **Actions taken**: Tier-1 actions completed during close (copied files, reindexed
  catalog, wrote session-observations). If none, omit.
- **Next safe action**: Tier-2/Tier-3 items the operator should handle. If all
  Tier-1/2 resolved, state "none — all resolved."
- **Persistence**: explicit answer to "is anything at risk of being lost?" State
  "all work committed/durable" when git_state, referenced_files, and handoffs gates
  are all satisfied. If any uncommitted work remains, list it. This field exists
  because operators consistently ask "what's at risk?" after close — the answer
  should be in the summary, not inferred from gate states.

### Step 4.1 — Receipt check (mandatory before emitting)

Before emitting the summary, verify each filled-in field against evidence:

1. **ACCOUNTING buckets** — each work item in "done" must cite what was produced (commit SHA, test count, file written). Each "partial" must cite what remains. Each "not-started" must explain why it wasn't started. If you can't cite evidence for a classification, it's `[INFERENCE]`, not a fact.
2. **Verify field** — distinguish static `/check` evidence from live/runtime
   acceptance. A `/check PASS` may be reported as `static PASS` even when
   `Not verified yet` contains a live gap. The overall field must say
   `GAP: <specifics>` whenever any live/runtime gap remains; do not erase the
   static PASS, but do not promote it to full verification either. This avoids
   both the old false gap (child receipts ignored) and the old false PASS
   (unverified work hidden).
3. **Retrospective field** — if friction occurred and `/aar` was not run, the field must say `SKIPPED (friction documented elsewhere)` or `DEFERRED`, not imply it was done. Do not write "none" when friction occurred.
4. **Decisions promoted** — if the session made substantive choices, "none" requires justification (e.g., "all decisions already in prior wiki concepts"). Don't skip the auto-promotion step silently.
5. **Status accuracy** — "not-started" means the work wasn't attempted. If it was attempted and blocked, the status is "BLOCKED: <reason>", not "not-started." Red-team blocks, failing tests, and missing dependencies are BLOCKED, not not-started.
6. **Cross-repo git state** — both `git_state_check.py` and `dirty_age.py` must
   have structured receipts. They must report clean, or any nonzero result
   must be explicitly classified as another session's work or resolved,
   before Persistence can say "all work committed/durable." If either script
   was unavailable or not run, Persistence must say `GAP: cross-repo check not run`.

**Why this check exists:** the 2026-07-22 session produced a close summary that said "Verify: PASS" while listing two unverified items, labeled red-team-BLOCKED work as "not-started," and skipped `/aar` despite documented friction. Each error passed because the summary fields were filled by judgment without a verification gate. The receipt check is that gate.

**Mechanical enforcement (mandatory).** After filling in the summary fields,
run the receipt validator before emitting:

```bash
python "$env:USERPROFILE/.grok/skills/close/__lib/validate_close_receipt.py" --close-summary "<summary_text>"
```

If the validator fails (exit code 1), the summary has contradictory fields
(e.g., Verify: PASS + non-empty "Not verified yet", or Persistence: "all
committed" without cross-repo check evidence). Fix the contradiction before
emitting. Do not override the validator — it catches the closure-pressure
minimization pattern mechanically (observed 2026-07-24: model declared
PROCEED while own findings listed open gaps).

**If the operator challenges the summary:** do not fold or defend. Re-verify each specific claim they challenge against the scanner output and session evidence. State which claims survive verification and which don't. Agreement without verification is the same failure as disagreement without verification — both assert without checking.

Final output shape (adapt from the template — do NOT emit the raw template or
a flat list of colon-delimited fields):

```markdown
# ✅ SESSION CLOSED — <short status>

<One sentence: what is complete, what remains, and whether the operator needs to act.>

## Open items

- **Verify:** <static /check PASS: N/N verifiers; overall GAP: specific live/unverified item>
- **Not verified yet:** <specific gaps or `none`>
- **Continuation:** <complete, degraded, or N candidates with N uncovered>
- **Next safe action:** <one concrete operator action, or `none — all resolved`>

If there are no open items, write `None.` under this heading. Do not make the
reader infer open work from a gate count.

## Work summary

### Completed

- <human-readable work item> — <evidence: commit, test, or artifact>

### Deferred or incomplete

- <work item> — <why it remains and where it is handed off>

If a bucket is empty, write `None.` Keep each item on its own line; do not pack
an entire session into one comma-separated sentence.

## Close checks

- **ACCOUNTING:** <N done, M partial/deferred, K not-started>
- **Persistence:** <all work committed/durable, or exact items at risk>
- **Runtime verification:** <what was actually observed; distinguish static tests from live behavior>
- **Wiki / retrospective / handoffs:** <counts and status in one readable sentence>
- **Decisions promoted:** <list, or `none — <reason>`>
- **Actions taken:** <Tier-1 actions, or `none`>

## Session details

- **Session:** <date> <full session-id>
- **Commits:** <count and relevant SHAs>
- **Gates:** <N/N satisfied; list only gates needing attention or manual review>
- **Loop iterations:** <N>
```

Formatting rules:

- Put the headline and one-sentence status before any inventory.
- Put unfinished work before completed work.
- Use headings, bullets, and short sentences. Use tables only for genuinely
  repeated structured data, such as a temp-file group summary.
- Preserve the exact field labels `Verify`, `Not verified yet`, and
  `Persistence` somewhere in the report so the receipt validator can inspect
  them. Prefer them as bullet labels, as shown above.
- Never emit `Gates:` followed by all 14 gate names as one line in the human
  report. Summarize satisfied gates and list only exceptions.
- Never repeat the same fact in `ACCOUNTING`, `Work summary`, and `Gates`.
- The detailed `=== GATES ===` format remains available only through
  `--format summary` for debugging.

**Other sessions' uncommitted work** is surfaced as a count in the git_state gate detail (e.g., "997 other uncommitted files remain"), not as a peer accounting bucket. Mixing other sessions' work into this session's accounting inflates the summary and makes the session's real work look smaller.

## Step 5 — Write state file

The scanner automatically writes the machine-derived evidence ledger to
`P:/.artifacts/close-evidence/<session-id>.json`. Treat this as the source for
gate/check/persistence receipts; it is separate from the LLM-authored close
state. Then write the human continuation state to
`P:/.artifacts/<termSafe>/close-state.md`. One spot-check: verify the most
important handoff is readable with correct `current_session_id` binding.

---

## Variant routing

| Invocation | Scanner variant | What changes |
|------------|----------------|-------------|
| `/close` | `--variant standard` | All 14 gates checked (wiki, retrospective, session_observations, handoffs, continuation_coverage, verify, temp files, git state, background tasks, decisions, chain integrity, quota, wiki lifecycle, referenced files) |
| `/close --quick` | `--variant quick` | Wiki, retrospective, decisions, session_observations gates skipped. Temp files, git state, background tasks, verify still checked (these are operational safety, not optional) |
| `/close --deep` | `--variant deep` | All 13 gates + consolidation check (duplicate wiki concepts) |
| `/close --no-loop` | `--variant standard` | All 13 gates, resolve each once, no re-scan |

## Hard constraints

1. **Multi-terminal isolation.** Only account for this session. The scanner
   filters by `current_session_id == $sess`.
2. **No stale-read.** Re-scan if >5 tool calls since last scan.
3. **Idempotency is session-scoped.** Track via gate states, not file existence.
4. **No gap between finding and action.** Every `needs_attention` gate resolves
   via the tier system: Tier-1 (local, reversible) → just do it; Tier-2 (shared
   state, reversible) → one-word confirm; Tier-3 (irreversible/external) → verb-based
   recommendation. "Noted", "flagged", or "acknowledged" are NOT valid resolutions.
   The close summary distinguishes "Actions taken" (Tier-1) from "Next safe action"
   (Tier-2/3) so the operator can audit what was done vs. what they need to decide.

## Output efficiency rules

| Situation | Output |
|-----------|--------|
| All gates pre_satisfied or skip | Short structured report. No gate walkthrough. |
| 1-2 gates need attention | Gate resolution + summary |
| Multiple gaps + loop | Step-by-step + loop + summary |

**Do not produce paragraph-length explanations for pre_satisfied gates.**
The fast path exists because most sessions where the operator invokes /close
after doing /wiki, /aar, and writing handoffs will have all gates pre-satisfied.

## Falsifier

This skill is wrong if:
- The fast path fires when it shouldn't (gates wrongly pre_satisfied) → tighten gate rules in close_accounting.py
- The scan misses work → fix the scanner
- Operators consistently skip /close because output is too verbose → enforce efficiency rules
- The loop never fires (genuinely never needed) → remove the loop

## Provenance

**Structural prompting patterns:** this skill implements terminal disposition
requirements (§5), receipt-first framing (§6), and failure-mode pre-specification
(§9) from `P:/.data/wiki/concepts/prompting-patterns-for-ai-agent-control.md`.

v1: all-prose with hand-written PowerShell. v2: close_accounting.py for scanning +
fast-path collapse. v3: scanner resolves all gates, computes loop decision,
emits summary template — LLM only fills judgment fields. Derived from /tp critique
of v2 ("4 of 5 gates were 'already done' but each still got a paragraph").
v4 (this): continuation coverage system replaces binary handoff-count gate.
`continuation_coverage.py` extracts goals/opportunities and reconciles against
handoffs — handoff existence no longer equals coverage. Proven failure: a session
with 11 handoffs and an AAR reported "persistence complete" while omitting 7+
material continuation workstreams. Root cause: `len(handoffs_mine) > 0` satisfied
the gate regardless of what those handoffs covered.
```
### Implementation excerpts

The skill definitions above are complete. The following implementation excerpts
cover the code paths most relevant to the latency, caching, orchestration, and
receipt questions.

#### close_accounting.py — scan/evidence and persistence excerpts

```text
Exit code: 0
Wall time: 1 seconds
Total output lines: 1836
Output:
Active code page: 65001
--- C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py selected excerpt ---
    """Run all scan functions and return bundled evidence.

    This is the scan layer of the pipeline. Adding a new scan source means
    adding a field to Evidence + one call here — not 5 touch points.
    """
    my_handoffs, other_handoffs = scan_handoffs(session_id)
    my_open_handoffs = [h for h in my_handoffs if h["is_open"]]
    wiki = scan_wiki(session_date)
    commits = scan_commits(since)
    retrospective = scan_retrospective(session_id)
    temp_files = scan_temp_files(session_date)
    git_status = scan_git_status()
    chain_dangling = scan_chain_integrity(my_handoffs)
    quota = scan_quota()
    wiki_lifecycle = scan_wiki_lifecycle(wiki)
    referenced_missing = scan_referenced_files(my_handoffs)
    check_receipts = scan_check_receipts(session_id)

    # Continuation coverage scan — goal/opportunity-to-handoff coverage
    # Pass both mine (for session-observations extraction) and all (for
    # reconciliation matching against explicitly referenced durable artifacts).
    try:
        coverage_result = scan_continuation_coverage(
            session_id, my_handoffs, retrospective,
            all_handoffs=my_handoffs + other_handoffs,
        )
    except Exception as e:
        coverage_result = {
            "coverage_complete": False, "candidate_count": 0,
            "material_uncovered": 0, "degraded": True,
            "extraction_error": str(e), "candidates": [],
            "coverage": {}, "ledger_path": "",
        }

    return Evidence(
        handoffs_mine=my_handoffs,
        handoffs_open=my_open_handoffs,
        handoffs_other=other_handoffs,
        wiki=wiki,
        commits=commits,
        retrospective=retrospective,
        temp_files=temp_files,
        git_status=git_status,
        chain_dangling=chain_dangling,
        quota=quota,
        wiki_lifecycle=wiki_lifecycle,
        referenced_missing=referenced_missing,
        continuation_coverage=coverage_result,
        check_receipts=check_receipts,
        persistence_checks=None,
    )
PARTIAL_KEYWORDS = {"partial", "in progress", "in-progress", "wip", "not started", "not-started", "open", "reviewed", "drafted"}
OPEN_KEYWORDS = {"open", "not started", "not-started", "new"}


# ---------------------------------------------------------------------------
# Session date resolution
# ---------------------------------------------------------------------------

def resolve_session_date(session_id: str) -> str | None:
    """Try to find the session directory and read its creation date."""
    encoded_cwd = quote("P:\\", safe="")
    session_dir = SESSIONS_ROOT / encoded_cwd / session_id
    summary_path = session_dir / "summary.json"
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            started = summary.get("started_at") or summary.get("info", {}).get("started_at")
            if started:
                return started[:10]  # YYYY-MM-DD
        except (json.JSONDecodeError, KeyError):
            pass
    # Fallback: use directory creation time
    if session_dir.exists():
        return datetime.fromtimestamp(session_dir.stat().st_ctime).strftime("%Y-%m-%d")
    return None


# ---------------------------------------------------------------------------
# Handoff scanning
# ---------------------------------------------------------------------------

def _extract_work_status(content: str) -> str:
    """Extract the leading keyword from the Status section."""
    for pattern in [
        r"(?ms)## Status\s*\n\s*\*?\*?([A-Z][^\n*]{0,80})",
        r"(?ms)## 2\.\s*Status\s*\n\s*\*?\*?([A-Z][^\n*]{0,80})",
    ]:
        m = re.search(pattern, content)
        if m:
            return m.group(1).strip().rstrip("*").strip()
    return "?"


def _extract_objective(content: str) -> str:
    """Extract the first substantive line from the Objective section."""
    for pattern in [
        r"(?ms)## Objective\s*\n(.+?)(?:\n\n|\n##|\Z)",
        r"(?ms)## 1\.\s*Objective\s*\n(.+?)(?:\n\n|\n##|\Z)",
        r"(?ms)## HANDOFF\s*[^\n]*\n(.+?)(?:\n\n|\n##|\Z)",  # fallback: first paragraph
    ]:
        m = re.search(pattern, content)
        if m:
            lines = [l.strip() for l in m.group(1).strip().splitlines() if l.strip()]
            if lines:
                return lines[0][:120]
    return ""


def _classify_handoff(yaml_status: str, work_status: str) -> str:
    """
    Classify a handoff into done | partial | not_started | blocked.

    YAML status is authoritative: if closed/done, it's done regardless of
    sub-task wording. If open, use work_status keywords to distinguish
    partial/not_started/blocked. Uses word-boundary matching to avoid
    substring false positives (e.g. "awaiting" matching "waiting").
    """
    yaml_lower = yaml_status.lower().strip()
    combined = f"{yaml_status} {work_status}".lower()

    # YAML status is authoritative for done
    if yaml_lower in ("closed", "done", "complete", "completed"):
        return "done"

    # Word-boundary keyword matching helper
    def has_keyword(text: str, keywords) -> bool:
        return bool(re.search(r"\b(?:" + "|".join(re.escape(k) for k in keywords) + r")\b", text))

    # For open handoffs, classify by work_status keywords
    if has_keyword(combined, BLOCKED_KEYWORDS):
        return "blocked"

    # Explicit "not started" signals
    not_started_signals = ("not started", "not-started", "neither", "nothing")
    if has_keyword(combined, not_started_signals):
        return "not_started"

    # Default for open handoffs: partial (work was started but not finished)
    return "partial"


def scan_handoffs(session_id: str) -> tuple[list[dict], list[dict]]:
    """Scan handoffs; return (this_session, other_sessions)."""
    mine = []
    others = []
    if not HANDOFFS_DIR.exists():
        return mine, others

    for d in sorted(HANDOFFS_DIR.iterdir()):
        if not d.is_dir():
            continue
        handoff_path = d / "HANDOFF.md"
        if not handoff_path.exists():
            continue
        try:
            content = handoff_path.read_text(encoding="utf-8")
        except Exception:
            continue

        # Extract current_session_id from YAML frontmatter
        m = re.search(r"current_session_id:\s*(.+)", content)
        sid = m.group(1).strip() if m else ""

        # Extract status from YAML
        m_status = re.search(r"^status:\s*(.+)", content, re.MULTILINE)
        yaml_status = m_status.group(1).strip() if m_status else "?"

        work_status = _extract_work_status(content)
        objective = _extract_objective(content)
--- C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py selected excerpt ---
    """Find durable /check verdicts for this session.

    /check verifiers run in child contexts, so their test commands do not
    appear in the parent chat transcript.  The authoritative handoff is the
    session-bound ``grok-check/**/check-state.md`` receipt under P:/.artifacts.
    This scanner records verdicts without treating a PASS as proof that live
    runtime acceptance was tested.
    """
    result = {
        "detected": False,
        "passed_runs": 0,
        "failed_runs": 0,
        "verifier_passes": 0,
        "verifier_total": 0,
        "run_paths": [],
        "details": [],
    }
    if not ARTIFACTS_DIR.exists():
        return result

    session_re = re.compile(r"^\*\*Session:\*\*\s*([^\s]+)", re.I | re.M)
    verdict_re = re.compile(
        r"^\*\*Verdict:\*\*\s*CHECK\s+(PASS|FAIL)\b(?:\s*\((\d+)\s*/\s*(\d+)[^)]*\))?",
        re.I | re.M,
    )
    for state_path in ARTIFACTS_DIR.rglob("check-state.md"):
        try:
            text = state_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        session_match = session_re.search(text)
        if not session_match or session_match.group(1) != session_id:
            continue
        verdict_match = verdict_re.search(text)
        if not verdict_match:
            continue

        result["detected"] = True
        passed = verdict_match.group(1).upper() == "PASS"
        result["passed_runs"] += int(passed)
        result["failed_runs"] += int(not passed)
        verifier_passes = int(verdict_match.group(2) or 0)
        verifier_total = int(verdict_match.group(3) or 0)
        result["verifier_passes"] += verifier_passes
        result["verifier_total"] += verifier_total
        result["run_paths"].append(str(state_path))
        result["details"].append(
            f"CHECK {'PASS' if passed else 'FAIL'} ({verifier_passes}/{verifier_total} verifiers)"
        )

    return result


@lru_cache(maxsize=1)
def _run_persistence_checks() -> dict:
    """Run the read-only cross-repo persistence checks and retain receipts.

    The close skill historically instructed the LLM to run these scripts and
    interpret their console output.  That left Persistence dependent on a
    prose step.  Capture the result in the gate so a close summary can cite
    exactly what ran, its exit code, and the relevant counts.
    """
    checks = {}
    for name, script in (("git_state_check", GIT_STATE_CHECK), ("dirty_age", DIRTY_AGE_CHECK)):
        check = {
            "path": str(script),
            "ran": False,
            "exit_code": None,
            "status": "unavailable",
            "output": "",
        }
        if not script.exists():
            checks[name] = check
            continue
        try:
            completed = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                cwd=str(WORKSPACE),
                timeout=30,
                creationflags=_CREATE_NO_WINDOW,
            )
            output = (completed.stdout or "")
            if completed.stderr:
                output += ("\n" if output else "") + completed.stderr
            check["ran"] = True
            check["exit_code"] = completed.returncode
            check["status"] = "clean" if completed.returncode == 0 else "attention"
            check["output"] = output[-2000:].strip()
            if name == "dirty_age":
                for label, key in (("Total dirty files", "dirty_files"), ("Older than 7 days", "stale_7d")):
                    match = re.search(rf"{re.escape(label)}:\s*(\d+)", output)
                    if match:
                        check[key] = int(match.group(1))
        except (OSError, subprocess.SubprocessError) as exc:
            check["status"] = "error"
            check["output"] = f"{type(exc).__name__}: {exc}"
        checks[name] = check

    return {
        "checks": checks,
        "all_ran": all(c["ran"] for c in checks.values()),
        "all_clean": all(c["status"] == "clean" for c in checks.values()),
    }


def write_evidence_ledger(
    session_id: str,
    variant: str,
    gates: dict,
    counts: dict,
    check_receipts: dict,
    persistence_checks: dict,
) -> str:
    """Persist the machine-derived close evidence for cold-start inspection."""
    CLOSE_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    safe_session = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)
    target = CLOSE_EVIDENCE_DIR / f"{safe_session}.json"
    payload = {
        "schema_version": 1,
        "session_id": session_id,
        "variant": variant,
        "generated_at": datetime.now().isoformat(),
        "counts": counts,
        "gates": gates,
        "check_receipts": check_receipts,
        "persistence_checks": persistence_checks,
    }
    temp = target.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temp, target)
    return str(target)

# Patterns that indicate the session ran tests or verification commands.
# Matched against tool-call payloads in chat_history.jsonl (case-insensitive).
_IMPLICIT_VERIFY_PATTERNS = [
    re.compile(r"pytest", re.I),
    re.compile(r"python\s+-m\s+pytest", re.I),
    re.compile(r"python\s+-m\s+unittest", re.I),
    re.compile(r"\bnpm\s+test\b", re.I),
    re.compile(r"\bcargo\s+test\b", re.I),
    re.compile(r"\bgo\s+test\b", re.I),
    re.compile(r"\bruby\s+-Itest\b", re.I),
    re.compile(r"\bmvn\s+test\b", re.I),
    re.compile(r"python\s+test_\w+\.py", re.I),
    re.compile(r"python\s+\S*verify_\w+\.py", re.I),
    re.compile(r"python\s+\S*validate_\w+\.py", re.I),
    re.compile(r"python\s+\S*check_\w+\.py", re.I),
    # Edit-then-verify: read_file within _EDIT_THEN_VERIFY_WINDOW_LINES of a
    # write/search_replace is detected structurally in the scanner, not by pattern.
]


def _scan_implicit_verification(session_id: str) -> dict:
    """Scan chat_history.jsonl for evidence of implicit verification.

    Returns:
        {
            "found": bool,
            "evidence": list[str],  # human-readable evidence lines
            "count": int,           # number of matching tool calls
        }
    """
    encoded_cwd = quote("P:\\", safe="")
    chat_path = SESSIONS_ROOT / encoded_cwd / session_id / "chat_history.jsonl"
    if not chat_path.exists():
        return {"found": False, "evidence": [], "count": 0}

    evidence: list[str] = []
    match_count = 0
    # Track edit-then-verify: record positions of write/edit calls,
    # then check if a read_file follows within 3 calls.
    recent_writes: list[int] = []  # line numbers of recent write/edit calls
    edit_then_verify_count = 0

    try:
        with chat_path.open("r", encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Extract tool-call text for pattern matching.
                # Match ONLY against tool_use inputs — not raw JSONL lines or
                # text-block prose. This prevents false positives from the
                # assistant *discussing* pytest in prose (e.g., a tool
                # description mentioning "pytest") from matching as if the
                # test was actually run.
                tool_text = ""
                content = event.get("content", "")

                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            if block.get("type") == "tool_use":
                                tool_name = block.get("name", "")
                                tool_input = block.get("input", {})
                                if isinstance(tool_input, dict):
                                    tool_text = json.dumps(tool_input)
                                if tool_name in ("write", "search_replace", "edit"):
                                    recent_writes.append(line_no)
                                elif tool_name in ("read_file", "read") and recent_writes:
                                    if line_no - recent_writes[-1] <= _EDIT_THEN_VERIFY_WINDOW_LINES:
                                        edit_then_verify_count += 1
                                        evidence.append(
                                            f"edit-then-verify at line {line_no} "
                                            f"(read after write at {recent_writes[-1]})"
                                        )
                                    recent_writes = []

                # Check for test/verify command patterns in tool_use inputs only.
                for pattern in _IMPLICIT_VERIFY_PATTERNS:
                    if pattern.search(tool_text):
                        match_count += 1
                        # Extract a short snippet around the match for evidence.
                        m = pattern.search(tool_text)
                        if m:
                            start = max(0, m.start() - 30)
                            end = min(len(tool_text), m.end() + 30)
                            snippet = tool_text[start:end].replace("\n", " ")
                            evidence.append(f"line {line_no}: ...{snippet}...")
                        break  # one match per line is enough

    except Exception:
        return {"found": False, "evidence": [], "count": 0}

    # Cap evidence list to avoid flooding the gate output.
    if len(evidence) > 8:
        evidence = evidence[:8] + [f"... and {len(evidence) - 8} more"]

    return {
        "found": match_count > 0 or edit_then_verify_count > 0,
        "evidence": evidence,
        "count": match_count + edit_then_verify_count,
    }


# ---------------------------------------------------------------------------
# Session write-path extraction (Track 1: authoritative session ownership)
# ---------------------------------------------------------------------------

# Tools that write/edit files via the file_path input field.
_FILE_WRITE_TOOLS = {"write", "search_replace", "edit", "multiedit"}

# Regex for extracting paths from run_terminal_command write-like commands.
# Windows absolute path: drive letter + backslash/forward slash
_WIN_PATH_RE = re.compile(r'[A-Za-z]:(?:[\\/][^\s"\';<>|]*)+')


def _extract_session_write_paths(session_id: str) -> list[str]:
    """Extract every file path this session wrote or edited.

    Reads chat_history.jsonl and finds all tool calls that modify files:
    - write/search_replace/edit/multiedit (input.file_path)
    - run_terminal_command with write-like commands (Set-Content, Copy-Item,
      python -c with write_text, redirect operators)

    Returns a deduplicated list of absolute or workspace-relative paths.
    """
    # Start with paths from _extract_session_write_ops (search_replace/write tools)
    ops = _extract_session_write_ops(session_id)
    paths: set[str] = set(ops.keys()) if ops else set()

    # Also extract paths from run_terminal_command write-like operations
    # Read updates.jsonl (Grok Build format)
    encoded_cwd = quote("P:\\", safe="")
    session_dir = SESSIONS_ROOT / encoded_cwd / session_id

    raw_tool_calls: list[tuple[str, dict]] = []  # (tool_name, tool_input)

    updates_path = session_dir / "updates.jsonl"
    if updates_path.exists():
        try:
            with updates_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    update = event.get("params", {}).get("update", {})
                    if isinstance(update, dict) and update.get("sessionUpdate") == "tool_call":
                        name = update.get("title", "")
                        raw_input = update.get("rawInput", {})
                        if isinstance(raw_input, dict):
                            raw_tool_calls.append((name, raw_input))
        except Exception:
            pass

    # Process tool calls for run_terminal_command write-like ops
    write_indicators = [
        "set-content", "add-content", "copy-item",
        "write_text", "write_bytes", "out-file",
        "new-item", "tee-object",
    ]
    for tool_name, tool_input in raw_tool_calls:
        if tool_name == "run_terminal…9901 tokens truncated…e changed implementation")
    elif has_incomplete:
        action = ("REQUIRED", f"complete the {partial_count} partial and {not_started_count} not-started items")
    else:
        action = ("OPTIONAL", "none — all work complete and verified")

    lines.append(f"## Next action")
    lines.append("")
    lines.append(f"**{action[0]}:** {action[1]}.")
    lines.append("")

    # --- Details (metadata at bottom) ---
    lines.append("## Details")
    # Extract session ID from summary_lines
    for sl in summary_lines:
        if sl.startswith("SESSION:"):
            lines.append(f"- {sl}")
            break
    for sl in summary_lines:
        if sl.startswith("Evidence ledger:"):
            lines.append(f"- {sl}")
            break
    lines.append(f"- Gates: {satisfied_count}/{len(gates)} satisfied")
    if temp_gate.get("count", 0) > 0:
        lines.append(f"- Temp files: {temp_gate['count']} at risk")
    if loop.get("needed"):
        lines.append(f"- Loop iterations needed: {', '.join(loop.get('attention_gates', []))}")
    lines.append(f"- Commits: {counts.get('commits', 0)}")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
--- C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py selected excerpt ---
                        help="Output format: compact (default, operator-facing), summary (verbose gate-by-gate), json")
    args = parser.parse_args()

    # Resolve session date for wiki scanning and git since
    session_date = resolve_session_date(args.session)
    since = args.since or session_date

    # Scan all evidence sources → Evidence dataclass
    ev = scan_all(args.session, session_date, since)

    # Counts derived from evidence (single source — no re-enumeration)
    counts = ev.counts

    # Resolve gates from evidence
    gates = resolve_gates(ev, args.session, session_date, args.variant)

    # Compute loop decision
    loop = compute_loop(gates)

    # Consolidation check for --deep variant
    consolidation = None
    if args.variant == "deep" and len(ev.wiki) > 0:
        consolidation = _check_consolidation(ev.wiki)

    # Generate summary template
    summary_lines = generate_summary(
        args.session, session_date, counts, gates, loop, ev.handoffs_mine, ev.retrospective, ev.quota
    )
    evidence_ledger = write_evidence_ledger(
        args.session,
        args.variant,
        gates,
        counts,
        ev.check_receipts,
        gates.get("git_state", {}).get("persistence_checks", {}),
    )
    summary_lines.append(f"Evidence ledger: {evidence_ledger}")

    # Emit
    output = {
        "session_id": args.session,
        "session_date": session_date,
        "variant": args.variant,
        "scanned_at": datetime.now().isoformat(),

        "evidence": {
            "handoffs": ev.handoffs_mine,
            "handoffs_open": ev.handoffs_open,
            "handoffs_other": ev.handoffs_other,
            "wiki": ev.wiki,
            "commits": ev.commits,
            "retrospective": ev.retrospective,
            "temp_files": ev.temp_files,
            "git_status": ev.git_status,
            "chain_dangling": ev.chain_dangling,
            "quota": ev.quota,
            "wiki_lifecycle": ev.wiki_lifecycle,
            "referenced_missing": ev.referenced_missing,
            "continuation_coverage": ev.continuation_coverage,
            "check_receipts": ev.check_receipts,
        },

        "counts": counts,
        "gates": gates,
        "loop": loop,
        "consolidation": consolidation,
        "evidence_ledger": evidence_ledger,

        "summary": summary_lines,
    }

    if args.format == "json":
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(format_output(gates, loop, summary_lines, counts, ev.handoffs_mine, args.format))


def format_output(
    gates: dict,
    loop: dict,
    summary_lines: list[str],
    counts: dict,
    handoffs_mine: list[dict],
    style: str = "summary",
) -> str:
    """Format close scanner output for human consumption.

    Pure function — takes resolved gates + evidence, returns text.
    No side effects. This is the format layer of the scan → resolve → format
    pipeline. Adding a new output format means adding a branch here, not
    editing main() or resolve_gates().

    Styles:
        "summary" — detailed gate-by-gate output (verbose, for debugging)
        "compact" — operator-facing: SHIPPED / OUTSTANDING / NEXT / Gates
                    (the default for /close)
    """
    if style == "summary":
        return _format_summary_detailed(gates, loop, summary_lines)
    elif style == "compact":
        return _format_compact(gates, loop, summary_lines, counts, handoffs_mine)
    else:
        # Unknown style — fall back to summary
        return _format_summary_detailed(gates, loop, summary_lines)


def _format_summary_detailed(gates: dict, loop: dict, summary_lines: list[str]) -> str:
    """Detailed gate-by-gate output (verbose — for debugging or --format json)."""
    _SUMMARY_OMIT = {"state", "detail"}
    lines = ["=== GATES ==="]
    for name, info in gates.items():
        state = info.get("state", "?")
        detail = info.get("detail", "")[:120]
        lines.append(f"  {name}: {state} - {detail}")
        for key, val in info.items():
            if key in _SUMMARY_OMIT:
                continue
            val_str = str(val)
            if len(val_str) > 80:
                val_str = val_str[:77] + "..."
            lines.append(f"    {key}: {val_str}")
    lines.append("")
    lines.append("=== LOOP ===")
    if loop.get("needed"):
        lines.append(f"  Needed: {', '.join(loop.get('attention_gates', []))}")
    else:
        lines.append("  Not needed")
    lines.append("")
    lines.append("=== SUMMARY ===")
    lines.extend(summary_lines)
    return "\n".join(lines)


def _format_compact(
    gates: dict,
    loop: dict,
    summary_lines: list[str],
    counts: dict,
    handoffs_mine: list[dict],
) -> str:
    """Operator-facing answer-first output: headline → needs-attention → handoffs → successes → verdict → action.

    Redesigned so the worst material state is immediately visible, not buried
    below success counts. Optimized for scanning in under 10 seconds by a
    tired operator managing concurrent sessions.

    Reuses all existing gate state, counts, and summary_lines — no parallel state.
    """
    lines: list[str] = []

    # --- Extract gate states ---
    attention_gates = []
    satisfied_count = 0
    llm_check_gates = []
    for name, info in gates.items():
        state = info.get("state", "?")
        if state in ("pre_satisfied", "skip"):
            satisfied_count += 1
        elif state == "needs_attention":
            attention_gates.append((name, info))
        elif state == "needs_llm_check":
            llm_check_gates.append((name, info))

    # --- Classify work ---
    done_count = sum(1 for h in handoffs_mine if h.get("classification") == "done")
    partial_count = sum(1 for h in handoffs_mine if h.get("classification") in ("partial", "blocked"))
    not_started_count = sum(1 for h in handoffs_mine if h.get("classification") == "not_started")
    open_handoffs = [h for h in handoffs_mine if h.get("classification") in ("partial", "blocked", "not_started")]

    # --- Gate details for report ---
    verify_gate = gates.get("verify", {})
    git_gate = gates.get("git_state", {})
    temp_gate = gates.get("temp_files", {})
    cov_gate = gates.get("continuation_coverage", {})
    retro_gate = gates.get("retrospective", {})

    # --- Determine headline (worst material state wins) ---
    has_blocked = any(
        h.get("classification") == "blocked" for h in handoffs_mine
    ) or any(
        "block" in info.get("detail", "").lower() and name != "temp_files"
        for name, info in attention_gates
    )
    has_not_evaluated = (
        verify_gate.get("state") == "needs_llm_check"
        and "not evaluated" in verify_gate.get("detail", "").lower()
    ) or partial_count == 0 and not_started_count == 0 and not attention_gates and not open_handoffs and verify_gate.get("state") not in ("pre_satisfied", "skip")

    has_incomplete = partial_count > 0 or not_started_count > 0
    has_verify_gap = verify_gate.get("state") in ("needs_attention", "needs_llm_check")
    has_uncovered = cov_gate.get("state") == "needs_attention"
    has_open_handoffs = len(open_handoffs) > 0

    cov_complete = cov_gate.get("state") == "pre_satisfied"

    # Headline precedence (worst first):
    # 1. blocked; 2. not evaluated; 3. incomplete work; 4. verify gap;
    # 5. complete with authorized deferrals; 6. complete and verified
    if has_blocked:
        headline = "⚠️ SESSION ENDED — REQUIRED WORK BLOCKED"
    elif has_not_evaluated:
        headline = "❓ SESSION CLOSED — IMPLEMENTATION COMPLETENESS NOT EVALUATED"
    elif has_incomplete and has_open_handoffs and cov_complete:
        headline = "📋 SESSION CLOSED — IMPLEMENTATION INCOMPLETE, CONTINUATION COVERED"
    elif has_incomplete:
        headline = "⚠️ SESSION CLOSED — IMPLEMENTATION INCOMPLETE"
    elif has_verify_gap and has_open_handoffs:
        headline = "📋 SESSION CLOSED — NOT FULLY EVALUATED; OPEN WORK HANDED OFF"
    elif has_verify_gap:
        headline = "⚠️ SESSION CLOSED — VERIFICATION INCOMPLETE"
    elif has_uncovered:
        headline = "⚠️ SESSION CLOSED — UNCOVERED CONTINUATION WORK"
    else:
        headline = "✅ SESSION CLOSED — COMPLETE"

    # --- One-sentence status ---
    parts = []
    if has_blocked:
        parts.append("material work is blocked")
    if has_not_evaluated:
        parts.append("implementation completeness was not evaluated")
    if has_incomplete:
        parts.append(f"implementation is incomplete ({partial_count} partial, {not_started_count} not started)")
    if has_verify_gap:
        vdetail = verify_gate.get("detail", "")
        parts.append(f"verification is incomplete ({vdetail[:50]})" if vdetail else "verification is incomplete")
    if has_open_handoffs:
        parts.append(f"{len(open_handoffs)} open handoffs remain")
    if cov_complete and has_open_handoffs:
        parts.append("all unfinished work is accounted for")
    if not parts:
        parts.append("all work is complete and verified")

    status_sentence = "The session " + ", ".join(parts) + "."
    # Fix grammar for list
    status_sentence = status_sentence.replace("The session material", "Material")
    if not status_sentence.startswith("Material"):
        status_sentence = status_sentence[0].upper() + status_sentence[1:]

    # --- Render ---
    lines.append(f"# {headline}")
    lines.append("")
    lines.append(status_sentence)
    lines.append("")

    # --- Needs-attention table (before successes) ---
    needs_rows: list[tuple[str, str, str]] = []

    if has_blocked:
        for name, info in attention_gates:
            if "block" in info.get("detail", "").lower() and name != "temp_files":
                needs_rows.append((name, "⛔ Blocked", info.get("detail", "")[:60]))
    if has_not_evaluated:
        needs_rows.append(("Implementation", "❓ Not evaluated", "completeness was not assessed"))
    if has_incomplete:
        # Merge partial + not-started into one row when both exist
        if partial_count and not_started_count:
            needs_rows.append(("Planned work", "🟡 Incomplete", f"{partial_count} partial, {not_started_count} not started"))
        elif partial_count:
            needs_rows.append(("Planned work", "🟡 Incomplete", f"{partial_count} partial items"))
        elif not_started_count:
            needs_rows.append(("Planned work", "⚪ Not started", f"{not_started_count} not started"))
    if has_verify_gap:
        needs_rows.append(("Verification", "🟡 Gap", verify_gate.get("detail", "verification incomplete")[:60]))
    if has_uncovered:
        needs_rows.append(("Continuation", "⚠️ Uncovered", cov_gate.get("detail", "")[:60]))
    for name, info in attention_gates:
        if name not in ("verify", "continuation_coverage", "git_state", "temp_files"):
            needs_rows.append((name, "⚠️ Attention", info.get("detail", "")[:60]))
    for name, info in llm_check_gates:
        if name not in ("verify",):
            needs_rows.append((name, "? Check", info.get("detail", "")[:60]))

    if needs_rows:
        lines.append("## Needs attention")
        lines.append("")
        lines.append("| Area | Status | What is missing |")
        lines.append("|------|--------|-----------------|")
        for area, status, missing in needs_rows:
            lines.append(f"| {area} | {status} | {missing} |")
        lines.append("")

    # --- Open handoffs (explicitly labeled as unfinished) ---
    if open_handoffs:
        lines.append("## Open handoffs")
        lines.append("")
        lines.append(f"**{len(open_handoffs)} open handoffs remain. These are unfinished continuation items, not completed work.**")
        lines.append("")
        for h in open_handoffs[:8]:
            path = h.get("path", h.get("dir", "?"))
            short = Path(path).name if path and path != "?" else "?"
            cls = h.get("classification", "?")
            # Humanize the classification label
            cls_display = {
                "not_started": "not started",
                "in_progress": "in progress",
            }.get(cls, cls.replace("_", " "))
            lines.append(f"- `{short}` ({cls_display})")
        if len(open_handoffs) > 8:
            lines.append(f"- ... and {len(open_handoffs) - 8} more")
        if cov_complete:
            lines.append("")
            lines.append("✅ All unfinished work is accounted for.")
            lines.append("This means nothing was lost; it does not mean the implementation is complete.")
        lines.append("")

    # --- Completed and verified (after needs-attention) ---
    lines.append("## Completed and verified")
    lines.append("")
    lines.append("| Dimension             | Result                                           |")
    lines.append("|-----------------------|--------------------------------------------------|")

    # Implementation dimension
    if done_count and not has_incomplete:
        lines.append(f"| {'Implementation':<21} | ✅ {str(done_count) + ' completed':<45} |")
    elif has_incomplete:
        impl_text = f"{done_count} done, {partial_count} partial, {not_started_count} not started"
        lines.append(f"| {'Implementation':<21} | 🟡 {impl_text[:45]:<45} |")
    else:
        lines.append(f"| {'Implementation':<21} | ❓ {'Not evaluated':<45} |")

    # Verification dimension
    vcount = verify_gate.get("count", 0)
    if verify_gate.get("state") == "pre_satisfied":
        vtext = f"{vcount} verification matches" if vcount else "Verified"
        lines.append(f"| {'Verification':<21} | ✅ {vtext[:45]:<45} |")
    elif has_verify_gap:
        lines.append(f"| {'Verification':<21} | 🟡 {verify_gate.get('detail', 'gap')[:45]:<45} |")
    else:
        lines.append(f"| {'Verification':<21} | ⚪ {'N/A':<45} |")

    # Persistence dimension
    git_state_val = git_gate.get("state", "?")
    git_detail_short = git_gate.get("detail", "")[:45]
    if git_state_val == "pre_satisfied":
        lines.append(f"| {'Persistence':<21} | ✅ {git_detail_short:<45} |")
    elif git_state_val == "needs_attention":
        lines.append(f"| {'Persistence':<21} | 🟡 {git_detail_short:<45} |")
    else:
        lines.append(f"| {'Persistence':<21} | ?  {git_detail_short:<45} |")

    # Runtime activation
    # (Derived from verify gate or git_state having "receipt" or "hook" in detail)
    runtime_marker = "⚪"
    runtime_text = "not assessed"
    for gname in ("verify", "git_state"):
        gdetail = gates.get(gname, {}).get("detail", "").lower()
        if "hook" in gdetail or "receipt" in gdetail or "mutation" in gdetail:
            runtime_marker = "✅"
            runtime_text = "hooks observed firing"
            break
    lines.append(f"| Runtime activation   | {runtime_marker} {runtime_text:<45} |")

    # Continuation accounting
    if cov_complete:
        cov_detail = cov_gate.get("detail", "complete")
        lines.append(f"| Continuation         | ✅ {cov_detail[:45]:<45} |")
    elif has_uncovered:
        lines.append(f"| Continuation         | ⚠️ {cov_gate.get('detail', '')[:45]:<45} |")
    else:
        lines.append(f"| Continuation         | ⚪ {'N/A':<45} |")

    # Other dimensions from gates
    def _dim_line(label, gate):
        state = gate.get("state", "?")
        detail = gate.get("detail", "")[:45]
        marker = "✅" if state in ("pre_satisfied", "skip") else "⚠️"
        return f"| {label:<21} | {marker} {detail:<45} |"

    lines.append(_dim_line("Decisions", gates.get("decisions", {})))
    lines.append(_dim_line("Wiki", gates.get("wiki", {})))
    lines.append(_dim_line("Retrospective", retro_gate))

    lines.append("")

    # --- Verification verdict ---
    if verify_gate.get("state") == "pre_satisfied" and not has_verify_gap:
        verdict = "VERIFIED"
    elif has_verify_gap and vcount > 0:
        verdict = "UNIT_PASS_LIVE_GAP"
    elif has_verify_gap:
        verdict = "VERIFICATION_GAP"
    else:
        verdict = "NOT_APPLICABLE"

    lines.append(f"## Verification verdict: {verdict}")
    lines.append("")
    if verdict == "VERIFIED":
        lines.append("- All verification gates satisfied.")
    elif verdict == "UNIT_PASS_LIVE_GAP":
        lines.append("- Unit-level verification passed.")
        lines.append("- End-to-end or live acceptance may be incomplete.")
    elif verdict == "VERIFICATION_GAP":
        lines.append(f"- {verify_gate.get('detail', 'verification gap')}")
    lines.append("")

    # --- Required next action ---
    if has_blocked:
        action = ("REQUIRED", "resolve the blocked work item before proceeding")
    elif has_not_evaluated:
        action = ("REQUIRED", "evaluate implementation completeness in a fresh session")
    elif has_uncovered:
        action = ("REQUIRED", "assign dispositions to uncovered continuation candidates")
    elif has_verify_gap and not has_incomplete:
        action = ("REQUIRED", "complete end-to-end verification of the changed implementation")
    elif has_incomplete:
        action = ("REQUIRED", f"complete the {partial_count} partial and {not_started_count} not-started items")
    else:
        action = ("OPTIONAL", "none — all work complete and verified")

    lines.append(f"## Next action")
    lines.append("")
    lines.append(f"**{action[0]}:** {action[1]}.")
    lines.append("")

    # --- Details (metadata at bottom) ---
    lines.append("## Details")
    # Extract session ID from summary_lines
    for sl in summary_lines:
        if sl.startswith("SESSION:"):
            lines.append(f"- {sl}")
            break
    for sl in summary_lines:
        if sl.startswith("Evidence ledger:"):
            lines.append(f"- {sl}")
            break
    lines.append(f"- Gates: {satisfied_count}/{len(gates)} satisfied")
    if temp_gate.get("count", 0) > 0:
        lines.append(f"- Temp files: {temp_gate['count']} at risk")
    if loop.get("needed"):
        lines.append(f"- Loop iterations needed: {', '.join(loop.get('attention_gates', []))}")
    lines.append(f"- Commits: {counts.get('commits', 0)}")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
```

#### validate_close_receipt.py — complete

```text
Exit code: 0
Wall time: 0.9 seconds
Output:
Active code page: 65001
--- C:\Users\brsth\.grok\skills\close\__lib\validate_close_receipt.py complete snapshot ---
#!/usr/bin/env python3
"""Validate /close summary layout and field-level receipt consistency.

The /close Step 4.1 receipt check is prose-enforced: "Verify field cannot
say PASS if any item in 'Not verified yet' is non-empty." Under closure
pressure, the model ignored this rule. This validator catches the
contradiction mechanically — the same class of enforcement as
validate_disconfirmation.py and validate_verdict_consistency.py. It also
rejects unsupported static-verification and persistence claims.

Usage:
    python validate_close_receipt.py --close-summary <text-or-file>

Exit codes:
    0 = pass (fields consistent)
    1 = fail (contradictory fields detected)
    2 = error (bad arguments)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Field extractors
# ---------------------------------------------------------------------------

def _extract_field(text: str, field_name: str) -> str | None:
    """Extract a field value from the close summary format.

    Looks for patterns like:
        Verify: PASS
        Not verified yet: none
        Not verified yet: specific gaps here
    """
    pattern = re.compile(
        rf"{re.escape(field_name)}\s*:\s*(.+?)(?:\n|$)",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_close_receipt(output_text: str) -> tuple[bool, list[str]]:
    """Check /close summary for field-level contradictions.

    Returns (passed, issues).
    """
    issues: list[str] = []

    # Check 0: enforce the human-readable report contract. The old flat
    # colon-delimited dump was easy to emit but hard to audit.
    required_sections = ("## Open items", "## Work summary", "## Close checks")
    if "SESSION CLOSED" in output_text:
        missing_sections = [
            section for section in required_sections
            if section.lower() not in output_text.lower()
        ]
        if missing_sections:
            issues.append(
                "Close summary is missing required human-readable sections: "
                + ", ".join(missing_sections)
            )

    # Check 1: Verify:PASS + non-empty "Not verified yet"
    verify_field = _extract_field(output_text, "Verify")
    not_verified = _extract_field(output_text, "Not verified yet")

    if verify_field and not_verified:
        verify_is_pass = "pass" in verify_field.lower() and "gap" not in verify_field.lower()
        not_verified_has_content = (
            not_verified.lower().strip() not in ("none", "n/a", "")
        )

        if verify_is_pass and not_verified_has_content:
            issues.append(
                "Verify field says PASS but 'Not verified yet' lists open "
                f"items ('{not_verified[:80]}'). Per Step 4.1 receipt check "
                "item 2: if open verification gaps exist, Verify must say "
                "'GAP: <specifics>', not PASS."
            )

    # Check 3: static /check claims require a durable check-state receipt.
    static_check_claim = bool(re.search(
        r"(?:static\s+)?/check\s*:?\s*PASS|static\s+verification\s*:?\s*PASS",
        output_text,
        re.IGNORECASE,
    ))
    if static_check_claim and not re.search(
        r"check-state\.md|CHECK\s+PASS\s*\(\d+\s*/\s*\d+|check receipts?:\s*\d+\s+PASS",
        output_text,
        re.IGNORECASE,
    ):
        issues.append(
            "Summary claims static /check verification passed without a "
            "check-state.md or equivalent verifier-count receipt."
        )

    # Check 2: Persistence claims without cross-repo check evidence
    persistence = _extract_field(output_text, "Persistence")
    if persistence and "all work committed" in persistence.lower():
        has_cross_repo_evidence = bool(
            re.search(r"git_state_check|cross[- ]repo.*(?:clean|run|passed)", output_text, re.IGNORECASE)
        )
        if not has_cross_repo_evidence:
            # Only flag if there were code changes (not pure doc sessions)
            has_commits = bool(re.search(r"Commits:\s*[1-9]", output_text, re.IGNORECASE))
            if has_commits:
                issues.append(
                    "Persistence says 'all work committed/durable' but no "
                    "evidence of cross-repo git_state_check.py being run. "
                    "Per Step 4.1 receipt check item 6: the script must have "
                    "been run before Persistence can claim all work is durable."
                )
        if not re.search(r"dirty_age|older than 7 days|stale dirty", output_text, re.IGNORECASE):
            issues.append(
                "Persistence says 'all work committed/durable' but has no "
                "dirty_age receipt proving stale-dirty state was checked."
            )

    return (len(issues) == 0, issues)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _read_input(arg: str) -> str:
    """Read from stdin (-), file path, or treat as literal text."""
    if arg == "-":
        return sys.stdin.read()
    p = Path(arg)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8")
    return arg


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate /close summary for field-level receipt consistency"
    )
    parser.add_argument(
        "--close-summary",
        action="store_true",
        help="Validate /close summary for contradictory fields",
    )
    parser.add_argument(
        "input",
        help="Summary text to validate (or path to file, or - for stdin)",
    )

    args = parser.parse_args()
    text = _read_input(args.input)

    if args.close_summary:
        passed, issues = validate_close_receipt(text)
    else:
        print("No validation mode selected", file=sys.stderr)
        return 2

    if passed:
        print("PASS: close summary fields consistent")
        return 0
    else:
        print("FAIL: close summary has contradictory fields", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

#### AAR full_preprocessor.py — entrypoint excerpts

```text
Exit code: 0
Wall time: 0.7 seconds
Output:
Active code page: 65001
--- C:\Users\brsth\.grok\skills\aar\__lib\full_preprocessor.py entrypoint snapshot ---
"""Full-session preprocessing runner.

Per spec Section 12: produce the complete evidence-packet artifact set:

    source-manifest.json
    canonical-events.jsonl
    active-timeline.json
    superseded-events.jsonl
    event-index.json
    signals.json
    aggregates.json
    claim-evidence.json
    parser-warnings.json
    timeline.md
    preprocess-summary.md

This module is the orchestrator. It chains: resolve → snapshot → parse →
reconcile → normalize → detect → index → select-context → write everything
to ``P:/.artifacts/<terminal>/grok-aar/<run>/preprocess/``.

The existing :func:`evidence_packet.run_preprocessor` stays for the simple
single-file path; this is the full-session path.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from canonical_model import BranchStatus, CanonicalEvent, CanonicalEventType
from completeness import CompletenessClassification, classify_completeness
from context_selector import ContextSelection, select_initial_context
from aggregators import AggregateSignal, all_aggregates
from detectors import Signal, SignalKind, run_all_detectors
from event_model import Event, Role, Transcript
from evidence_packet import resolve_terminal_id
from indexes import EventIndex, build_indexes
from normalizer import CanonicalStream, normalize_session
from reconciler import (
    BRANCH_RECONCILIATION_PARTIAL,
    ReconciliationReport,
    USEFUL_EVENT_TYPES,
    reconcile_sources,
)
from session_resolver import IdentityStatus, SessionBinding, resolve_session_dir
from source_snapshot import SnapshotResult, snapshot_session_sources
from transcript_parser import parse_transcript

__all__ = [
    "PreprocessResult",
    "FullPreprocessError",
    "run_full_preprocessor",
    "PREPROCESS_ARTIFACTS",
]

#: All artifact files written by run_full_preprocessor (spec Section 12).
PREPROCESS_ARTIFACTS: tuple[str, ...] = (
    "source-manifest.json",
    "canonical-events.jsonl",
    "active-timeline.json",
    "superseded-events.jsonl",
    "event-index.json",
    "signals.json",
    "aggregates.json",
    "claim-evidence.json",
    "parser-warnings.json",
    "timeline.md",
    "preprocess-summary.md",
    # Supporting artifacts (not in the spec list but required for the AAR
    # skill to consume the packet):
    "context-selection.json",
    "snapshot-manifest.json",  # mirrored from source-snapshot/
)


class FullPreprocessError(Exception):
    """Raised when full preprocessing cannot proceed (e.g. UNVERIFIED identity)."""


@dataclass(frozen=True)
class PreprocessResult:
    """Outcome of the full preprocessing run.

    ``packet_dir`` is the directory the LLM-facing artifacts live in.
    ``source_status`` is the earned completeness classification.
    """

    ok: bool
    status_label: str  #: 'OK' | 'SESSION_IDENTITY_UNVERIFIED' | 'ERROR'
    packet_dir: str | None
    source_status: str  #: one of CompletenessStatus values
    completeness: CompletenessClassification | None
    session_id: str | None
    snapshot_cutoff: str | None
    events_total: int
    active_events: int
    superseded_events: int
    signals_total: int
    warnings: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status_label": self.status_label,
            "packet_dir": self.packet_dir,
            "source_status": self.source_status,
            "completeness": self.completeness.to_dict() if self.completeness else None,
            "session_id": self.session_id,
            "snapshot_cutoff": self.snapshot_cutoff,
            "events_total": self.events_total,
            "active_events": self.active_events,
            "superseded_events": self.superseded_events,
            "signals_total": self.signals_total,
            "warnings": list(self.warnings),
            "reasons": list(self.reasons),
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_full_preprocessor(
    *,
    session_id: str,
    workspace_encoded: str,
    run_dir: str | Path,
    sessions_root: str | Path = "C:/Users/brsth/.grok/sessions",
    env: dict[str, str] | None = None,
    cutoff: str | None = None,
    max_signals: int = 30,
    max_total_events: int = 120,
) -> PreprocessResult:
    """Run the complete full-session preprocessing pipeline.

    Steps:
    1. Resolve + verify session identity (block on UNVERIFIED).
    2. Snapshot all sources atomically under ``<run_dir>/preprocess/source-snapshot/``.
    3. Parse chat_history.jsonl (snapshot copy).
    4. Reconcile against summary.json / events.jsonl / rewind_points.jsonl.
    5. Normalize into canonical stream with branch labels.
    6. Run deterministic detectors.
    7. Build retrieval indexes.
    8. Select bounded LLM context.
    9. Write all 10+ packet artifacts atomically.

    Returns a :class:`PreprocessResult`. Raises :class:`FullPreprocessError`
    only on unrecoverable failure (e.g. session dir missing entirely).
    """
    run_path = Path(run_dir)
    packet_dir = run_path / "preprocess"
    snapshot_root = packet_dir / "source-snapshot"
    packet_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. Resolve identity ---
    binding: SessionBinding = resolve_session_dir(
        session_id=session_id,
        workspace_encoded=workspace_encoded,
        sessions_root=sessions_root,
        env=env,
    )
    if binding.status is not IdentityStatus.VERIFIED:
        return PreprocessResult(
            ok=False,
            status_label="SESSION_IDENTITY_UNVERIFIED",
            packet_dir=str(packet_dir).replace("\\", "/"),
            source_status="SOURCE_UNVERIFIED",
            completeness=None,
            session_id=session_id,
            snapshot_cutoff=cutoff,
            events_total=0,
            active_events=0,
            superseded_events=0,
            signals_total=0,
            warnings=tuple(binding.reasons),
            reasons=tuple(binding.cross_checks) + tuple(binding.reasons),
        )

    # --- 2. Snapshot ---
    snapshot: SnapshotResult = snapshot_session_sources(
        binding.session_dir, snapshot_root, session_id=session_id, cutoff=cutoff
    )

    # --- 3. Parse primary ---
    chat_path = snapshot_root / "chat_history.jsonl"
    if not chat_path.is_file():
        return PreprocessResult(
            ok=False,
            status_label="ERROR",
            packet_dir=str(packet_dir).replace("\\", "/"),
            source_status="SOURCE_UNVERIFIED",
            completeness=None,
            session_id=session_id,
            snapshot_cutoff=snapshot.snapshot_cutoff,
            events_total=0,
            active_events=0,
            superseded_events=0,
            signals_total=0,
            warnings=("chat_history.jsonl missing from snapshot",),
            reasons=("primary source absent",),
        )
    transcript: Transcript = parse_transcript(chat_path)

    # --- 4. Load + filter secondary sources ---
    summary_path = snapshot_root / "summary.json"
    if summary_path.is_file():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            summary = None
    else:
        summary = None

    events: list[dict[str, Any]] = []
    events_path = snapshot_root / "events.jsonl"
    if events_path.is_file():
        with events_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if o.get("type") in USEFUL_EVENT_TYPES:
                    events.append(o)

    rewind: list[dict[str, Any]] = []
    rewind_path = snapshot_root / "rewind_points.jsonl"
    if rewind_path.is_file():
        for line in rewind_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rewind.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # --- 5. Reconcile ---
    reconciliation: ReconciliationReport = reconcile_sources(
        snapshot, transcript, summary=summary, events=events, rewind_points=rewind
    )

    # --- 6. Classify completeness (earned through reconciliation) ---
    completeness: CompletenessClassification = classify_completeness(
        reconciliation.completeness_inputs, snapshot_cutoff=snapshot.snapshot_cutoff
    )

    # --- 7. Normalize ---
    terminal_id, term_warnings = resolve_terminal_id(env=env)
    stream: CanonicalStream = normalize_session(
        transcript,
        reconciliation=reconciliation,
        events=events,
```

#### AAR reference_loader.py — entrypoint excerpts

```text
Exit code: 0
Wall time: 0.8 seconds
Output:
Active code page: 65001
--- C:\Users\brsth\.grok\skills\aar\__lib\reference_loader.py entrypoint snapshot ---
"""Reference loader for the AAR lean-hybrid architecture.

This module implements the physical conditional-loading mechanism introduced
in Phase 1 of the lean-hybrid implementation. The SKILL.md core contains
only the lean synthesis contract plus 1-line trigger definitions; the full
detail lives in ``references/*.md`` files. The loader is the single source
of truth for *which references are loaded given which triggers*.

Design contract
---------------
- ``load_references_for_triggers(fired_triggers)`` returns a dict of
  ``{reference_name: file_path}`` for every reference that should load.
- A reference loads **only** when at least one of its declared triggers is
  in ``fired_triggers``.
- The loader never loads all references. The default lean invocation has
  zero triggers fired → zero references loaded.
- A missing reference file raises ``MissingReferenceError`` so the failure
  is visible (per spec: "missing references fail visibly").
- The loader does NOT inspect detector signals directly; the caller passes
  in the set of triggers that have fired. A weak detector signal alone
  must not load a reference — the caller decides whether the signal rises
  to a trigger.

Trigger names are stable strings. Adding a new trigger requires updating
``REFERENCE_TRIGGERS`` below AND the SKILL.md core §triggers section.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REFERENCE_DIR_NAME = "references"
SKILL_DIR = Path(__file__).resolve().parent.parent  # .grok/skills/aar/


class MissingReferenceError(FileNotFoundError):
    """Raised when a trigger fires for a reference file that does not exist."""


@dataclass(frozen=True)
class ReferenceSpec:
    """One conditional reference and the triggers that load it."""

    name: str          # short identifier (e.g. "opportunity-discovery")
    filename: str      # file under references/
    triggers: tuple[str, ...]  # trigger names that load this reference


# Authoritative trigger → reference map.
# Adding a reference requires: (1) entry here, (2) file under references/,
# (3) trigger definition in SKILL.md core.
REFERENCE_TRIGGERS: tuple[ReferenceSpec, ...] = (
    ReferenceSpec(
        name="opportunity-discovery",
        filename="opportunity-discovery.md",
        triggers=(
            "full_mode_promoted",
            "user_asked_opportunity_landscape",
            "successful_efficiency_session",
        ),
    ),
    ReferenceSpec(
        name="interaction-quality",
        filename="interaction-quality.md",
        triggers=(
            "user_correction_high",
            "objective_drift_any",
            "correction_propagation_failure_any",
            "procedure_saturation_any",
            "user_repeated_goal_restoration",
            "user_asked_what_went_wrong",
        ),
    ),
    ReferenceSpec(
        name="epistemic-calibration",
        filename="epistemic-calibration.md",
        triggers=(
            "architectural_change_proposed",
            "durable_rule_promotion_claimed",
            "high_severity_defect",
            "cross_session_aggregation_claim",
            "headline_makes_comparative_claim",
            "user_asked_deep_root_cause",
        ),
    ),
    ReferenceSpec(
        name="operational-safety",
        filename="operational-safety.md",
        triggers=(
            "destructive_write_signal",
            "tool_result_secret_exposure_signal",
            "user_paste_secret_warning_signal",
            "file_edit_reversal_high",
            "active_incident_reported",
        ),
    ),
    ReferenceSpec(
        name="external-insight",
        filename="external-insight.md",
        triggers=(
            "user_asked_external_research",
            "reusable_failure_class_revealed",
            "root_cause_benefits_from_external_evidence",
            "platform_capabilities_may_have_changed",
            "improvement_may_exist_elsewhere",
            "local_evidence_supports_competing_explanations",
            "cross_domain_analogies_relevant",
            "full_mode_promoted",
        ),
    ),
    ReferenceSpec(
        name="handoff-and-temporal",
        filename="handoff-and-temporal.md",
        triggers=(
            "handoff_document_present",
            "prior_session_state_referenced",
            "recommendation_revision_aggregate_high",
            "stale_state_risk_material",
        ),
    ),
    ReferenceSpec(
        name="cross-model-audit",
        filename="cross-model-audit.md",
        triggers=(
            "value_compounded_episode_present",
            "cross_model_audit_requested",
        ),
    ),
)


def all_reference_names() -> tuple[str, ...]:
    """Return the names of every known conditional reference."""
    return tuple(spec.name for spec in REFERENCE_TRIGGERS)


def triggers_for_reference(reference_name: str) -> tuple[str, ...]:
    """Return the triggers declared for a reference (raises KeyError if unknown)."""
    for spec in REFERENCE_TRIGGERS:
        if spec.name == reference_name:
            return spec.triggers
    raise KeyError(f"unknown reference: {reference_name!r}")


def references_for_triggers(
    fired_triggers: Iterable[str],
    *,
    skill_dir: Path | None = None,
    verify_files_exist: bool = True,
) -> dict[str, Path]:
    """Return ``{reference_name: absolute_path}`` for references that should load.

    A reference loads when at least one of its declared triggers appears in
    ``fired_triggers``. Unknown trigger names in ``fired_triggers`` are
    silently ignored (they may be detector signals the caller chose not to
    promote to triggers).

    Parameters
    ----------
    fired_triggers : iterable of str
        Trigger names that have fired for this session.
    skill_dir : Path, optional
        Override the skill root (used in tests). Defaults to the parent of
        the directory containing this module.
    verify_files_exist : bool, default True
        If True, raise MissingReferenceError when a reference that should
        load does not exist on disk.
    """
    fired = set(fired_triggers)
    skill_root = skill_dir or SKILL_DIR
    ref_dir = skill_root / REFERENCE_DIR_NAME
    loaded: dict[str, Path] = {}
    for spec in REFERENCE_TRIGGERS:
        if not any(t in fired for t in spec.triggers):
            continue
        path = ref_dir / spec.filename
        if verify_files_exist and not path.is_file():
            raise MissingReferenceError(
                f"reference {spec.name!r} should load (trigger fired) but "
                f"file {path} does not exist"
            )
        loaded[spec.name] = path
    return loaded


def default_loaded_references() -> dict[str, Path]:
    """Return the references loaded on a default lean invocation.

    The default lean invocation has zero triggers fired → zero references.
    This function exists for tests and for asserting the contract.
    """
    return references_for_triggers(fired_triggers=())


def effective_default_instruction_lines(*, skill_dir: Path | None = None) -> int:
    """Count lines loaded on a default lean invocation.

    This is SKILL.md only. References are not loaded by default.
    Used to verify the Phase 1 size-reduction acceptance criterion.
    """
    skill_root = skill_dir or SKILL_DIR
    skill_md = skill_root / "SKILL.md"
    if not skill_md.is_file():
        raise MissingReferenceError(f"SKILL.md not found at {skill_md}")
    with skill_md.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def full_mode_instruction_lines(*, skill_dir: Path | None = None) -> int:
    """Count lines loaded when all triggers fire (upper bound)."""
    skill_root = skill_dir or SKILL_DIR
    base = effective_default_instruction_lines(skill_dir=skill_root)
    ref_total = 0
    all_refs = references_for_triggers(
        fired_triggers=[t for spec in REFERENCE_TRIGGERS for t in spec.triggers],
        skill_dir=skill_root,
    )
    for path in all_refs.values():
        with path.open("r", encoding="utf-8") as f:
            ref_total += sum(1 for _ in f)
    return base + ref_total
```
## Post-review revision

The attached review identified seven source-level contradictions in the first
proposal: ordinary caching versus AAR freshness, automatic wiki promotion,
cross-model default behavior, duplicated close authority, stale-dirty ownership,
parallelism before snapshot capture, and the absence of a migration boundary.
The following revised proposal supersedes the earlier optimization sketch for
review purposes. It is included verbatim so the next cold-start reviewer can
evaluate the corrected decision packet without relying on the attachment.

# Revised proposal: Canonical AAR with shared evidence and graduated analysis

## Decision requested

Determine whether `/aar` should become the single canonical workflow for session learning and retrospective analysis, with `/debrief` retained temporarily as a compatibility alias.

This review must separately decide:

1.  whether AAR and DEBRIEF have materially overlapping outcomes;
    
2.  which unique DEBRIEF behavior, if any, must be preserved;
    
3.  whether a shared evidence architecture can reduce latency and token cost without reducing finding coverage;
    
4.  whether the change is sufficiently supported to displace the current baseline.
    

Do not implement during this review.

## Goal

Produce one evidence-grounded learning workflow that:

-   accounts for completed, incomplete, deferred, and abandoned work;
    
-   reconstructs important decisions, corrections, and reversals;
    
-   identifies failures, friction, successful mechanisms, missed leverage, and unresolved risks;
    
-   distinguishes observations from causal interpretations;
    
-   routes findings to the appropriate destination;
    
-   avoids rereading the same raw session or rerunning unchanged analysis;
    
-   does not automatically turn one-session inferences into durable behavioral policy.
    

Success is not “one fewer command.” Success is preserving or improving useful finding coverage while reducing duplicated evidence processing, model calls, latency, and contradictory artifacts.

## Non-goals

This proposal does not:

-   weaken the breadth of a substantive AAR;
    
-   replace AAR with a lightweight session summary;
    
-   make `/close` responsible for causal learning;
    
-   make AAR responsible for repository mutation or operational close enforcement;
    
-   assume that multiple model calls improve quality merely because they are diverse;
    
-   authorize automatic edits to skills, AGENTS files, configuration, or durable policy;
    
-   permit one terminal to adopt, modify, or commit another terminal’s work.
    

## Proposed responsibility boundary

### `/close`

`/close` owns operational session disposition:

-   current-session accounting;
    
-   persistence and data-loss risk;
    
-   git and artifact state;
    
-   verification receipts;
    
-   continuation and handoff coverage;
    
-   active background work;
    
-   closure blockers;
    
-   the final close receipt.
    

Its mechanical scanner and validator remain authoritative for these claims.

`/close` may consume a completed AAR receipt, but it must not independently reproduce AAR’s causal analysis, opportunity discovery, or lesson synthesis.

### `/aar`

`/aar` owns evidence-grounded learning:

-   intended versus actual outcome;
    
-   typed episode inventory;
    
-   decisions, corrections, and reversals;
    
-   failures and successful mechanisms;
    
-   causal hypotheses and competing explanations;
    
-   reusable lessons;
    
-   verification gaps and unresolved risks;
    
-   continuation candidates that emerge from analysis;
    
-   routing recommendations.
    

AAR may identify an operational risk, but it should pass that risk to `/close`; it must not become a second close scanner.

### `/debrief`

During migration, `/debrief` becomes a compatibility entry point that invokes the canonical AAR engine with a retrospective-focused presentation mode.

It must not retain:

-   an independent raw-transcript reader;
    
-   a separate artifact schema;
    
-   separate model-routing logic;
    
-   separate wiki promotion;
    
-   an independent finding lifecycle.
    

Any DEBRIEF-only capability must first be shown to improve outcomes on representative sessions. Capabilities are migrated into AAR only when evidence justifies them.

## Canonical evidence path

The architecture should have one evidence producer and multiple bounded consumers.

```
Verified session identity
        ↓
Immutable evidence snapshot
        ↓
Deterministic preprocessing
        ↓
Canonical AAR packet
        ├──→ mandatory breadth inventory
        ├──→ conditional deep analysis
        ├──→ optional independent challenge
        └──→ routing receipt
```

### Producer

The deterministic preprocessor produces the canonical packet.

### Authority

The packet is authoritative for:

-   event identity and ordering;
    
-   active versus superseded history;
    
-   source completeness;
    
-   snapshot cutoff;
    
-   counts and mechanically detectable signals.
    

The LLM remains authoritative only for explicitly labelled interpretation, such as causal hypotheses, relevance, severity, and recommendations.

### Storage

Each packet is stored under a run-scoped immutable directory and identified by:

-   verified session ID;
    
-   snapshot cutoff;
    
-   evidence fingerprint;
    
-   preprocessor schema version.
    

No mutable `latest` pointer or newest-directory heuristic may establish authority.

### Consumption

All AAR analysis stages, including delegated or cross-model stages, consume the packet or a deterministic selection derived from it. They do not independently reread the live transcript.

### Freshness

Before reuse, verify that:

```
current evidence fingerprint
= stored packet fingerprint
```

If they differ, generate a new packet.

If they match, the packet may be reused. Reuse means the evidence is unchanged; it does not imply that every derived analysis remains valid.

### Failure behavior

Stop rather than silently degrade when:

-   session identity is unverified;
    
-   source binding is unverified;
    
-   the packet is structurally incomplete;
    
-   required packet artifacts disagree;
    
-   fingerprint computation fails.
    

A partial source may be analyzed only with explicitly constrained completeness claims.

## Safe reuse model

Do not implement a generic “AAR cache.”

Use two separate layers:

### Layer 1 — Evidence packet reuse

An immutable packet may be reused only when its complete evidence fingerprint matches the current source.

### Layer 2 — Derived-analysis reuse

A previous analysis may be reused only when all of these match:

-   packet fingerprint;
    
-   AAR contract/schema version;
    
-   trigger-policy version;
    
-   analysis mode;
    
-   relevant reference versions;
    
-   material model or prompt contract version.
    

If the packet is unchanged but the AAR contract has changed, rerun synthesis against the existing packet.

Every reused result must state:

-   what was reused;
    
-   the matching identifiers;
    
-   what was rerun;
    
-   why reuse was considered valid.
    

## Mandatory breadth for every substantive AAR

Every substantive AAR must perform one complete inventory covering:

1.  intended terminal outcome and success conditions;
    
2.  actual result and degree of completion;
    
3.  completed work;
    
4.  partial, deferred, abandoned, and unstarted work;
    
5.  decisions, assumptions, corrections, and reversals;
    
6.  failures and friction;
    
7.  successful mechanisms and preserved value;
    
8.  reusable insights and patterns;
    
9.  verification gaps and unresolved risks;
    
10.  continuation, handoff, experiment, and routing candidates.
    

“No material item found” is valid for any category. Omitting the category is not.

This breadth pass should be primarily extractive and classificatory. It must not automatically trigger maximum-depth causal analysis for every item.

## Graduated analysis policy

### Tier 0 — Deterministic extraction

Always run:

-   source reconciliation;
    
-   event ordering;
    
-   superseded-history handling;
    
-   signal extraction;
    
-   accounting checks;
    
-   packet validation.
    

### Tier 1 — Mandatory synthesis

Always run for a substantive AAR:

-   terminal-outcome comparison;
    
-   typed episode ledger;
    
-   decision and correction history;
    
-   value accounting;
    
-   verification-gap inventory;
    
-   concise evidence-backed lessons;
    
-   routing recommendations.
    

### Tier 2 — Triggered deep analysis

Run only for affected findings when one or more material triggers fire:

-   substantive correction or reversal;
    
-   repeated failure pattern;
    
-   security, privacy, destructive-action, or data-loss incident;
    
-   costly dead end or large rework loop;
    
-   unresolved causal dispute;
    
-   major architectural or policy decision;
    
-   high-impact success whose mechanism is not understood;
    
-   evidence that contradicts an existing durable rule;
    
-   explicit deep-analysis request.
    

Tier 2 may include:

-   layered root-cause analysis;
    
-   double-loop analysis;
    
-   formal opportunity portfolio;
    
-   expanded epistemic calibration;
    
-   lifecycle governance;
    
-   targeted external research.
    

### Tier 3 — Independent challenge

Cross-model or independent critique is not default fan-out.

Run it when:

-   Tier 2 produces a high-impact recommendation;
    
-   the recommendation would alter durable behavior;
    
-   the primary analysis has low or disputed causal confidence;
    
-   the session contains a material correction or reversal;
    
-   an existing policy may be superseded;
    
-   the user explicitly requests independent challenge.
    

The challenger receives:

-   the canonical packet or bounded packet selection;
    
-   the candidate claims;
    
-   supporting evidence IDs;
    
-   stated confidence and falsifiers.
    

The challenger’s task is to verify, disconfirm, narrow, or identify omissions—not to generate another unconstrained retrospective.

Failure of the external model is fail-open for the AAR report but fail-closed for automatic promotion of the affected recommendation. Record the unavailable challenge explicitly.

## Lesson contract

Every material lesson must include:

-   supporting episode IDs;
    
-   direct observation;
    
-   narrow causal interpretation;
    
-   competing explanation;
    
-   scope;
    
-   confidence;
    
-   comparison status;
    
-   boundary or counterexample;
    
-   unsupported extension;
    
-   falsifier;
    
-   proposed behavior change;
    
-   disposition.
    

Allowed dispositions:

-   `PRESERVE`
    
-   `MONITOR`
    
-   `INVESTIGATE`
    
-   `BOUNDED_EXPERIMENT`
    
-   `DEFER`
    
-   `REJECT`
    
-   `NOT_WORTH_DOING`
    
-   `PROPOSE_POLICY_CHANGE`
    

A recommendation to change behavior is not itself authorization to make the change.

## Durable-memory and policy boundary

AAR may automatically write only its own run-scoped report and routing receipt.

It must not automatically:

-   change AGENTS files;
    
-   edit skill behavior;
    
-   change configuration;
    
-   create or revise durable policy;
    
-   commit repository changes;
    
-   convert another session’s work into current-session work.
    

### Wiki routing

AAR may:

-   identify an existing wiki concept that appears relevant;
    
-   propose a new concept;
    
-   emit a structured candidate artifact;
    
-   mark duplication or contradiction risk.
    

Automatic publication to the durable wiki requires a separately authorized ingestion policy with independent acceptance criteria.

At minimum, durable behavioral promotion requires one of:

-   replicated evidence across multiple independent sessions;
    
-   controlled or meaningful comparison;
    
-   credible external evidence plus local validation;
    
-   explicit operator approval.
    

A model assigning the label `GENERAL` or `PROBLEM_CLASS` is not sufficient evidence for promotion.

## Isolation and ownership

Session ID is the authority for current-session accounting.

Terminal identifiers may be used only as storage namespaces after live verification; they must not establish session ownership.

Foreign or ambiguous state must:

-   be excluded from current-session accounting;
    
-   be reported as foreign or unbound when it creates risk;
    
-   never be modified, committed, deleted, or adopted automatically.
    

File age does not establish abandonment. A stale file may trigger review, but not mutation.

## Parallelism boundary

Do not generate the packet and scan changing live evidence concurrently.

The safe order is:

1.  verify session identity;
    
2.  capture one immutable evidence snapshot;
    
3.  record its cutoff and fingerprint;
    
4.  derive the canonical packet;
    
5.  validate the packet;
    
6.  run independent consumers in parallel over that packet.
    

After the packet exists, the following may run in parallel when they do not write shared mutable state:

-   mandatory inventory preparation;
    
-   targeted deep-analysis lanes;
    
-   independent challenge;
    
-   existing-wiki similarity search;
    
-   close scanner consumption of the same captured snapshot, if supported.
    

All parallel outputs remain provisional until reconciled by one final AAR assembler and validator.

## Minimum migration plan

### Phase 0 — Measure the baseline

Run current AAR and current DEBRIEF independently on the same representative session set.

Record:

-   findings by category;
    
-   evidence coverage;
    
-   unsupported claims;
    
-   missed material items;
    
-   duplicate findings;
    
-   runtime;
    
-   input and output tokens;
    
-   number of model calls;
    
-   external-model failures;
    
-   operator usefulness assessment.
    

Do not change routing yet.

### Phase 1 — Build a capability crosswalk

For every DEBRIEF stage, identify:

-   equivalent AAR capability;
    
-   genuinely unique behavior;
    
-   duplicated behavior;
    
-   behavior that is expensive but unproven;
    
-   behavior that should be retired.
    

No DEBRIEF capability is preserved merely because it exists.

### Phase 2 — Shared-packet replay

Modify only the experimental path so both workflows consume the same immutable packet.

Compare results against Phase 0 to determine whether raw-transcript rereading contributed useful findings or merely duplicated processing.

### Phase 3 — Canonical AAR candidate

Create a candidate AAR path with:

-   mandatory breadth;
    
-   triggered deep analysis;
    
-   triggered independent challenge;
    
-   no automatic wiki or policy mutation;
    
-   versioned packet and analysis reuse;
    
-   validated routing receipt.
    

### Phase 4 — Compatibility alias

Only after acceptance tests pass:

-   route `/debrief` to the canonical AAR engine;
    
-   preserve `/debrief` command compatibility;
    
-   emit the DEBRIEF-compatible presentation if materially useful;
    
-   mark independent DEBRIEF implementation deprecated;
    
-   retain historical DEBRIEF artifacts unchanged.
    

### Phase 5 — Retirement decision

Remove the independent DEBRIEF engine only after:

-   the migration period has completed;
    
-   no required caller depends on its old artifact contract;
    
-   replay evidence shows no material regression;
    
-   rollback remains straightforward.
    

## Acceptance corpus

Use at least these session classes:

1.  clean, successfully completed session;
    
2.  session with partial or deferred work;
    
3.  session containing a correction, reversal, failure, or verification dispute;
    
4.  successful but inefficient session with no obvious failure;
    
5.  long session with compaction, branching, or superseded history;
    
6.  session containing foreign or ambiguous workspace state;
    
7.  session where an external challenge model is unavailable.
    

At least one session should be evaluated by a human without knowing which workflow produced which report.

## Acceptance criteria

The canonical candidate may displace the baseline only if:

### Coverage

-   It captures every baseline finding judged materially useful, or documents why the finding was invalid, duplicate, or outside scope.
    
-   It does not reduce coverage of incomplete work, decisions, verification gaps, or continuation candidates.
    
-   It correctly identifies active versus superseded evidence.
    

### Claim integrity

-   Every material factual claim resolves to packet evidence.
    
-   Observations and causal interpretations are visibly separated.
    
-   No source-completeness claim exceeds the packet’s source status.
    
-   No one-session inference is silently promoted to durable policy.
    

### Efficiency

Across the representative corpus:

-   raw session parsing occurs once per evidence snapshot;
    
-   unchanged evidence does not trigger redundant preprocessing;
    
-   full-session model rereads are eliminated;
    
-   external critique calls occur only when a documented trigger fires;
    
-   median model calls and input tokens decrease materially;
    
-   no material finding regression is attributable to the reduction.
    

Do not set an arbitrary percentage target before measuring the baseline. Report the observed reduction and its confidence.

### Operational integrity

-   `/close` remains authoritative for closure gates and persistence claims.
    
-   `/aar` remains authoritative for learning analysis.
    
-   foreign session state is never mutated;
    
-   stale analysis is rejected through fingerprint or version mismatch;
    
-   partial external-model failure is visible and does not corrupt the base report;
    
-   outputs reconcile mechanically.
    

### User outcome

A blind reviewer can answer, from the report:

-   What did the user actually accomplish?
    
-   What remains incomplete or unsafe?
    
-   What important decision changed?
    
-   What should be learned or preserved?
    
-   What is the next justified action?
    
-   Which conclusions are observed, inferred, or still uncertain?
    

## Failure and rollback criteria

Do not canonicalize the candidate if:

-   DEBRIEF produces repeatably useful findings that the candidate misses;
    
-   packet compression removes evidence required for correct interpretation;
    
-   trigger rules suppress important deep analysis;
    
-   reuse returns analysis based on changed evidence or changed contracts;
    
-   AAR and `/close` disagree about operational facts without a defined authority rule;
    
-   the alias breaks existing callers or artifact consumers;
    
-   reduced cost comes primarily from reduced coverage.
    

Rollback consists of restoring independent command routing while retaining the shared-packet experiment and collected measurements.

## Required review output

Return:

1.  `ACCEPT`, `ACCEPT_WITH_CHANGES`, or `REJECT`;
    
2.  a source-backed AAR/DEBRIEF capability crosswalk;
    
3.  contradictions found in the current contracts;
    
4.  the smallest safe canonical architecture;
    
5.  mandatory versus triggered stages;
    
6.  exact packet, freshness, reuse, authority, and failure contracts;
    
7.  migration dependencies and affected callers;
    
8.  replay results or the concrete commands needed to obtain them;
    
9.  a recommendation stating whether evidence is sufficient to displace the baseline;
    
10.  unresolved risks and explicit blockers.
    

Do not recommend implementation until the baseline comparison and source-level capability crosswalk have been completed.

The largest conceptual improvement is the separation of **mandatory breadth** from **mandatory depth**. The original proposal was already moving in that direction—one complete inventory with expensive refinement only where justified—but it needed explicit authority, reuse, mutation, and displacement contracts.

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-07-26T22:02 | 019f8b39-95e... | backfilled session_id from transcript scan |
