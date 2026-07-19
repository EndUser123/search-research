# SDLC Skill Topology Audit — Final Corrected Evidence Packet

**Date:** 2026-07-13
**Repository:** `P:/packages/.claude-marketplace/plugins/cc-skills-analysis`
**Branch:** `main`
**HEAD:** `6807a6710277a1db2d897631ce74e55084c5b0cf`
**Repository state:** Clean, synchronized with `origin/main`. No staged or unstaged changes.

---

## 1. Proven Current-State Facts

### 1.1 Inventory — Exact Repository Paths and Status

All paths relative to `P:/packages/.claude-marketplace/plugins/cc-skills-analysis/`.

| Surface | SKILL.md path | Type | Git-tracked | Cache match |
|---|---|---|---|---|
| `/recap` | `skills/recap/SKILL.md` | Script + LLM | Yes | MATCH (1.0.121) |
| `/debrief` | `skills/debrief/SKILL.md` | Engine + Hook + LLM | Yes | MATCH (1.0.121) |
| `/rns` | `skills/rns/SKILL.md` | Pure LLM (no runtime) | Yes | MATCH (1.0.121) |
| `/why` | `skills/why/SKILL.md` | LLM with search | Yes | MATCH (1.0.121) |
| `/friction` | `skills/friction/SKILL.md` | Pure LLM | Yes | MATCH (1.0.121) |
| `/behave` | `skills/behave/SKILL.md` | Pure LLM | Yes | MATCH (1.0.121) |
| `/retro` | `skills/retro/SKILL.md` | Deprecated stub | Yes | MATCH (1.0.121) |
| `/top-problems` | `skills/top-problems/SKILL.md` | Deprecated stub | Yes | MATCH (1.0.121) |

### 1.2 Shared Runtime Dependencies

| Mechanism | Path | Used by |
|---|---|---|
| `session_chain.walk_session_chain()` | `search-research/core/session_chain.py` | `/recap`, `/debrief`, `/why` |
| `debrief_core` state machine | `skills/debrief/__lib/debrief_core.py` | `/debrief` all modes |
| `gap_engine_adapter` | `skills/debrief/__lib/gap_engine_adapter.py` | `/debrief gaps` mode |
| `gap_engine.__lib` (runtime) | `skills/debrief/gap_engine/__lib/` | Used by adapter; **not by hooks** |
| `__lib/render_rns.py` | `skills/recap/__lib/render_rns.py` | Recap handoff formatting only |
| Plugin router | `__lib/router.py` | SessionEnd → debrief reflect hook only |

### 1.3 Hook Registration State (Inspected Mechanisms)

Four inspected registration mechanisms:

| Mechanism | Found gap_engine registration? |
|---|---|
| SKILL.md frontmatter `hooks:` field (`/debrief` has none) | No |
| Plugin `__lib/router.py` (only routes SessionEnd) | No |
| `skills/debrief/hooks/hooks.json` (only routes SessionEnd) | No |
| `settings.json` (all hook entries) | No |

Hook files at `skills/debrief/gap_engine/hooks/` (6 files) and `skills/debrief/gap_engine/tests/test_write_hook_output.py`:

- **Git-tracked** — `git ls-files --stage` confirms all 7 files in index with committed blob hashes
- **Not gitignored** — `git check-ignore -v` exits 1 (no rule applies)
- **Clean** — `git status` shows no modifications from HEAD
- **Present in HEAD** — blob hashes match the committed versions

**Classification:** `TRACKED_DORMANT_IMPLEMENTATION — PURPOSE_AND_INCREMENTAL_VALUE_UNPROVEN`

These are committed source files implementing `run(data)` hook entry points. They are syntactically valid Python but are not wired to any runtime event through any inspected registration mechanism. Their purpose relative to the active debrief evidence lifecycle (`debrief_core` + gap_engine adapter + gap_engine `__lib`) has not been established. Neither deletion nor activation is justified without that capability analysis.

### 1.4 Recap SKILL.md Documentation Fix

The renderer path in `skills/recap/SKILL.md` was corrected from the non-existent `skills/rns/scripts/core/render.py` to the actual `recap/__lib/render_rns.py`, matching the runtime import in `recap_v2.py:1569`. Committed in `388425f` (ancestor of HEAD) alongside other recap changes. Repository is clean.

### 1.5 Handoff Authority Model

Two artifacts, different authority:

| Artifact | Writer | Storage | Authority | Freshness |
|---|---|---|---|---|
| JSON handoff | Snapshot plugin | `~/.claude/state/handoff/console_*_handoff.json` | Chain reconstruction only (session_id, transcript_path) | ≤5 min |
| Markdown handoff | `/recap` LLM synthesis | Conversational (chat output) | Advisory "Resume Here" summary | Lossy on compaction |

The transcript (`.jsonl`) is the only authoritative source. Neither handoff artifact binds work-authority decisions.

---

## 2. Retracted Findings

| Prior claim | Reason for retraction |
|---|---|
| Hook files were dead code proven safe to delete | They are Git-tracked committed source. "Not registered" ≠ "dead." |
| Hook files were untracked workspace artifacts | `git ls-files --stage` confirms all 6 files in index with committed blob hashes. |
| Hook files were intentionally Git-ignored | `git check-ignore -v` exits 1 — no ignore rule applies. Earlier false positive was from wrong repository root. |
| Hook files existed only in cache | They exist in HEAD at Git blob hashes matching cache copies. Cache restore was a redundant write. |
| All registration mechanisms comprehensively searched before deletion | SKILL.md frontmatter `hooks:` field was not searched. This is the canonical registration surface for skill-level hooks (used by `/go`). |
| `DOC_FIX_COMMITTED_ISOLATED` | The SKILL.md fix was committed in `388425f` alongside other recap changes (risk_calculator, tests, `__init__.py`). Not isolated. |
| Earlier "DEPRECATE" verdicts applying to hook deletion | Retracted. Correct classification is `TRACKED_DORMANT_IMPLEMENTATION — PURPOSE_AND_INCREMENTAL_VALUE_UNPROVEN`. |

---

## 3. Source-Level Risks or Ambiguities

**R1 — `/rns` backend dissolution comments are ambiguous.** `__lib/render_rns.py:5` and `recap_v2.py:1561` refer to "rns skill (which is being dissolved)" but the `/rns` skill is live at cache 1.0.121. The comments refer to the Python backend only. No behavioral impact. LOW risk.

**R2 — Two handoff artifacts with different authority models.** By-design and documented. The transcript remains authoritative. LOW risk.

**R3 — `/debrief chain` internal artifact flow is undocumented.** Chain mode (recap→gaps→friction→red-team→rns→SCORES) is entirely LLM-driven. By-design for a model-driven system. LOW risk.

**R4 — Three distinct hook registration mechanisms exist.** settings.json→router.py (plugin), SKILL.md frontmatter (skill), hooks.json (skill). No single source of truth for "all registered hooks." MEDIUM risk — could cause dangling registrations during refactoring.

---

## 4. Live-Behavior Findings

**F1 — Recap produces normative output despite descriptive intent.** `recap_v2.py:1557-1576` renders RNS-format "Recommended Next Steps." By-design — the local `__lib/render_rns.py` exists because the RNS Python backend was removed. No programmatic consumer. **Status:** by-design.

**F2 — `/rns` has zero machine-readable output.** Pure LLM skill with no scripts, no `__lib`, no runtime. `<selection>` block is terminal-display markdown. No automation consumes it. **Status:** by-design.

**F3 — `/go` does not consume RNs output.** Zero references to `rns`, `RNS`, or `<selection>` in any `/go` code. `/go` does its own task selection via queue. **Status:** by-design.

**F4 — Readiness checking has five surfaces with no enforced hierarchy.** `/recap check`, `/risks`, `/check`, `/red-team`, `/epistemic-check`. Each has documented scope. No enforcement prevents running multiple on the same decision. **Status:** by-design; no evidence of real failures from overlaps.

---

## 5. Decisions Requiring Further Evidence

| Decision | Prerequisite | Verdict |
|---|---|---|
| Activate or delete gap_engine hook files | Capability comparison with active debrief evidence lifecycle. What do these hooks provide that `debrief_core` + adapter does not? | `BLOCKED_EVIDENCE_INSUFFICIENT` |
| Formalize DecisionRecord schema | Identify a real consumer or recurring demand. None found in this audit. | `BLOCKED_EVIDENCE_INSUFFICIENT` |
| Build ImpactAssessment surface | Prove recurring unmet need for pre-change blast-radius analysis. Not found. | `BLOCKED_EVIDENCE_INSUFFICIENT` |
| Build OutcomeReport surface | Prove recurring unmet need for post-implementation audit. Not found. | `BLOCKED_EVIDENCE_INSUFFICIENT` |
| Merge `/friction` and `/behave` into `/debrief` | Prove user confusion or wasted compute from duplicate mining. Not found. | `BLOCKED_EVIDENCE_INSUFFICIENT` |
| Document readiness escalation hierarchy | Prove that missing documentation causes routing failures. Not found. | `BLOCKED_EVIDENCE_INSUFFICIENT` |
| Create shared routing reference | Establish canonical owner, update authority, and consumer first. | `BLOCKED_EVIDENCE_INSUFFICIENT` |
| Formalize artifact-contract tests | No enforcement harness exists. Premature without proven boundary. | `BLOCKED_EVIDENCE_INSUFFICIENT` |

---

## 6. Safe No-Change Conclusions

| Claim | Verdict | Rationale |
|---|---|---|
| Remove RNs section from `/recap` | `NO_CHANGE` | Advisory chat output only; no consumer collision |
| Fold `/risks` into `/check` | `NO_CHANGE` | Incompatible execution models |
| Fold `/recap check` into `/check` | `NO_CHANGE` | Incompatible input domains |
| Deprecate `/recap check` | `NO_CHANGE` | Valid role as pre-handoff gate; no overlap |
| Delete gap_engine hook files | `NO_CHANGE` | Tracked committed source; not dead code |
| Fix recap SKILL.md renderer path | **ALREADY COMMITTED** (`388425f`) | Documentation now matches runtime code |
| Document `/debrief chain` artifact flow | `NO_CHANGE` | Chain mode is LLM-driven; no code to document |
| Handoff authority model | `NO_CHANGE` | By-design; two artifacts, different purposes |

---

## 7. Recommended Next Workstream

### Capability-first `/debrief` evidence-lifecycle investigation

The most productive next step is a **reading investigation** of the dormant hook implementations vs the active debrief lifecycle. No code changes, no registrations, no deletions.

**Scope:** Read `skills/debrief/gap_engine/hooks/*.py` (~15KB) and map each `run(data)` entry point to the lifecycle events it handles. Compare against what `debrief_core` + gap_engine adapter + gap_engine `__lib` already provide.

**Deliverable:** A two-column capability comparison answering:

1. What does the active lifecycle (`debrief_core` state machine → adapter → gap_engine `__lib` → task creation → close gate) cover?
2. What does each dormant hook file (`pretooluse.py`, `posttooluse.py`, `sessionstart.py`, `stop.py`) check?
3. What is the delta? Any capability present in the hooks but absent from the active lifecycle?
4. If delta is zero → label `CANDIDATE_CONSOLIDATION_OR_RETIREMENT` (no urgency).
5. If delta is positive → the hooks contain developed-but-unwired functionality. Decide whether to register via SKILL.md `hooks:` block or reimplement within the active lifecycle.

**Constraint:** No edits to hooks, registration, cache logic, ignore rules, skill contracts, or existing functionality. Reading only.

---

## Evidence Sources Index

| Fact | Verification command | Result |
|---|---|---|
| HEAD revision | `git rev-parse HEAD` | `6807a6710277a1db2d897631ce74e55084c5b0cf` |
| Branch | `git rev-parse --abbrev-ref HEAD` | `main` |
| Repository clean | `git status --short --branch` | `## main...origin/main` |
| Hook files in index | `git ls-files --stage skills/debrief/gap_engine/hooks/` | 6 files, `100644` mode |
| Hook files not gitignored | `git check-ignore -v skills/debrief/gap_engine/hooks/` | Exit 1 (no rule) |
| Hook files match HEAD | `git hash-object skills/debrief/gap_engine/hooks/stop.py` matches HEAD blob | `0cb07f07` |
| Test file in index | `git ls-files skills/debrief/gap_engine/tests/test_write_hook_output.py` | `100644 6a90e501` |
| SKILL.md fix committed | `git log --oneline -1 -- skills/recap/SKILL.md` | `388425f feat: update SKILL documentation` |
| `/debrief` has no `hooks:` frontmatter | `head -50 skills/debrief/SKILL.md` | No `hooks:` key |
| `/go` has `hooks:` frontmatter | `head -40 ../../cc-skills-sdlc/skills/go/SKILL.md` | Lines 25-37 |
| Plugin router scope | `__lib/router.py` | Only SessionEnd (line 24) |
| settings.json gap_engine | `grep "gap_engine" .claude/settings.json` | No matches |
| Post-restore tests pass | `python -m pytest skills/debrief/gap_engine/tests/ -q` | 99 passed |

---

`AUDIT_CORRECTED_NO_FURTHER_CHANGES`
