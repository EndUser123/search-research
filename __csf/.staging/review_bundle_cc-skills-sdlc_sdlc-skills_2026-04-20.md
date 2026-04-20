# Review Bundle: cc-skills-sdlc — code, design_v1.1, planning, refactor

**Generated:** 2026-04-20
**Scope:** `P:/packages/cc-skills-sdlc/skills/{code_v3.0,design_v1.1,planning,refactor}`
**File Count:** 204 files (4-agent parallel scan)
**Execution Mode:** 4-agents (parallel: Explorer + Core Reader + Config Reader + Dependency Scanner)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Generated:** 2026-04-20
- **Scope:** 4 SDLC skills (code, design_v1.1, planning, refactor)
- **File Count:** 204 files across 4 skill directories
- **Execution Mode:** 4-agents (parallel scan)

### Domain & Purpose

These 4 skills form the core SDLC (Software Development Life Cycle) workflow engine for a Claude Code plugin system. They cover the full lifecycle: planning → design → code → refactor, with each skill enforcing strict phase gating, evidence collection, and constitutional compliance. They are invoked by users via slash commands (`/planning`, `/design_v1.1`, `/code`, `/refactor`) and delegate to sub-agents for adversarial analysis.

### Scale Metrics

| Skill | Version | Status | Phases | Test Files | Enforcement |
|-------|---------|--------|--------|-----------|-------------|
| `code_v3.0` | 3.0.0 | stable | 11 phases | 70+ test modules | advisory |
| `design_v1.1` | 1.1 | stable | 4-step NTP | 2 test modules | **strict** |
| `planning` | 5.5.2 | accepted | 12+ steps | 6 test modules | advisory |
| `refactor` | 2.0.0 | stable | 10 steps | 0 dedicated | advisory |

### Environment

- **OS:** Windows 11 Pro (10.0.26200) with drive letter `P:/`
- **Shell:** Bash (Git Bash / WSL)
- **Primary Language:** Python 3.12+
- **Package Managers:** No per-skill requirements files — deps managed at `cc-skills-sdlc` package level
- **Build/Test Tools:** pytest

---

## 2. ARCHITECTURE OVERVIEW

```
User invokes /planning | /design_v1.1 | /code | /refactor
        │
        ▼
┌─────────────────────────────────────────────────────┐
│              SLAVE SKILL DISPATCH LAYER              │
│  (hooks route queries; skills own the workflow)      │
└─────────────────────────────────────────────────────┘
        │
        ├──────────────────────────────────────────┐
        ▼                    ▼                    ▼
  /planning            /design_v1.1          /code
  ├─ auto_verify.py    ├─ generate_context.py ├─ lib/checklist.py
  ├─ auto_fix.py       ├─ validate_design.py  ├─ utils/phase_state.py
  ├─ adversarial_review│─ schemas.py           ├─ utils/evidence.py
  │  (6 sub-agents)   └─ hooks/              ├─ utils/got_planner.py
  └─ arch_handoff_    /planning invokes /design when blockers found
    state.py          (nested resume protocol)
        │
        ▼
  /refactor
  ├─ scripts/deduplicate.py   → canonical IDs
  ├─ scripts/refactor_plan.py → structured plan
  ├─ scripts/plan_review.py   → adversarial review
  └─ 8 staggered Task agents  → DISCOVER phase
```

### Skill Interaction Diagram

```
/planning
  └─► /design_v1.1  (nested, blocking, architecture blockers only)
          └─► ADR saved to docs/architecture/

/code
  ├─► /search       (depends_on_skills)
  ├─► Context7 MCP  (library docs + breaking change detection)
  └─► hooks         (breadcrumb tracking, plan consumer gate)

/refactor
  └─► 8 staggered Task agents → findings → deduplicate → plan → TDD RED → refactor
```

---

## 3. EXECUTION AND DATA FLOW

### /code (code_v3.0) — 11-Phase Workflow

| Phase | Entry Point | Key Action |
|-------|-----------|------------|
| 1. pre_execution_checklist | `lib/checklist.py` | 5-question validation |
| 2. analyze_query_intent | `lib/task_detector.py` | Ralph Loop auto-enable |
| 3. select_execution_model | — | Route to fast/full/continuous |
| 4. resolve_plan_state | `utils/tdd_resume.py` | Restore from compaction |
| 5. initialize_resume_ledger | `utils/evidence.py` | EvidenceManager init |
| 6. requirements_clarity_check | — | — |
| 7. preflight_context_validation | — | — |
| 8. explore_codebase | — | — |
| 9. design_solution | — | — |
| 10. consumer_contract_precheck | — | Contract Authority Packet |
| 11. tdd_implementation | — | RED/GREEN/REFACTOR |
| 12. smoke_validation | — | — |
| 13. full_test_suite | — | pytest |
| 14. tier0_checklist_verification | — | `/qr`, `/sqa` |
| 15. audit_quality_checks | — | — |
| 16. critique_agent_review | — | Sub-agent dispatch |
| 17. trace_manual_verification | — | TRACE checklist |
| 18. producer_consumer_trace_verification | — | Handshake proof |
| 19. done_final_certification | `utils/evidence.py` | `can_mark_done()` |

### /design_v1.1 — Native Tool-Gated Protocol (NTP)

```
1. Generate RUN_ID → set DESIGN_RUN_ID env var
2. Run generate_context.py → AST summary + SOP
3. Draft design_draft_{RUN_ID}.json (DesignPayload schema)
4. Run validate_design.py → schema + logic validation
   └─ Max 3 attempts (tracked via .attempt_{RUN_ID} file)
   └─ SUCCESS → .verified_{RUN_ID} flag + ADR → docs/architecture/
5. pre_response hook: stop_if_unverified.py
   └─ Blocks response if .verified_{RUN_ID} missing
```

### /planning — 12-Step Workflow

```
1. detect_topic        — Infer from conversation history
2. draft_plan          — Concrete content only
3. discover_existing   — Search codebase (catch duplicates)
4. auto_verify.py      — 22+ deterministic checks
5. contract_boundary_check — CAP/artifact/handoff validation
6. remediate_blockers  — Route to /design if architecture blockers
7. auto_fix.py         — Non-semantic repairs only
8. adversarial_review.py — 6 agents (5 parallel + 1 critic series)
9. synthesize          — Rewrite plan with accepted findings
10. integration_trace  — Walk TASK outputs through all consumers
11. recommended_next_steps — Emit RNS if blocked/routed
12. present_results    — Status header + plan path
13. cleanup_artifacts  — Remove stale review files (>7 days)
```

### /refactor — 10-Step Workflow

```
1. DISCOVER          — 8 staggered Task agents (30s apart)
2. DEDUPLICATE        — Merge by file+line → canonical IDs (COMP/DRY/CONC/PY/QUAL)
3. PRIORITIZE         — P0 (bugs/race) → P1 (error) → P2 (DRY) → P3 (conventions)
4. CONSTITUTIONAL_FILTER — SoloDevConstitutionalFilter
5. PLAN               — create_refactor_plan() → structured plan
6. RED_PHASE         — Characterization tests (MUST fail first)
7. ADVERSARIAL_REVIEW — plan_review.py stress test
8. REFACTOR           — AST-based changes (LibCST)
9. REGRESSION         — Full test suite
10. CODE_SIMPLIFICATION — pr-review-toolkit:code-simplifier
```

### State Management

| Skill | State Store | Location | Isolation |
|-------|------------|----------|-----------|
| `code_v3.0` | JSON files per terminal | `P:/.claude/state/code_evidence_{terminal_id}.json` | Terminal-scoped |
| `design_v1.1` | Flag files + ADR | `{skills/design/}.verified_{RUN_ID}`, `docs/architecture/` | Per RUN_ID |
| `planning` | v2 envelope receipts | `P:/.claude/plans/adversarial/` | Terminal-scoped, TTL=20min |
| `refactor` | JSON findings | `P:/.claude/.artifacts/{terminal_id}/refactor/` | Terminal-scoped |

### Error Handling

- **code_v3.0**: Checksum + rollback on state write failure; `CODE_NO_CHECKLIST` bypass; git hash rollback detection
- **design_v1.1**: Max 3 attempts per RUN_ID; FAIL blocks response via hook
- **planning**: Architecture blocker → nested `/design` invoke + resume; `auto_fix.py` only non-semantic repairs
- **refactor**: TDD RED phase enforced (characterization tests must fail); rollback via git state capture

---

## 4. COMPONENT INVENTORY

### Core Logic

#### `code_v3.0`
| File | Key Functions/Classes | Responsibility |
|------|---------------------|----------------|
| `lib/checklist.py` | `validate_checklist()`, `log_checklist_answers()`, `CHECKLIST_QUESTIONS` | 5 pre-execution questions |
| `lib/state_encryption.py` | `StateEncryption`, `PBKDF2_ITERATIONS=480000` | Fernet encryption, GDPR compliance |
| `lib/task_detector.py` | `TaskDetector`, `detect_impl_vs_research()` | Ralph Loop auto-enable |
| `lib/gap_loader.py` | `load_test_gaps()`, `format_gap_summary()` | Gap analysis from `/t` discovery |
| `utils/evidence.py` | `EvidenceManager` | TDD ledger: RED/GREEN/REFACTOR/VERIFY |
| `utils/phase_state.py` | `PhaseStateManager` | Phase completion + git rollback detection |
| `utils/plan_updater.py` | `PlanUpdater` | In-place plan.md updates with locking |
| `utils/got_planner.py` | `GotPlanner`, `GotEdgeAnalyzer` | Graph-of-Thought node extraction |
| `utils/tot_tracer.py` | `BranchGenerator` | Tree-of-Thought branch scoring |
| `utils/context7_client.py` | `Context7Resolver`, `BreakingChangeDetector` | Context7 API + exponential backoff |
| `utils/context7_rate_limiter.py` | `Context7RateLimiter`, `_SharedState` | 60 qpm singleton rate limiter |
| `utils/library_scanner.py` | `scan_imports()` | AST-based Python import scanning |
| `utils/priority_scorer.py` | `score_priority()` | P0/P1/P2 confidence scoring |
| `utils/tdd_resume.py` | TDD context restoration | Compaction resume support |

#### `design_v1.1`
| File | Key Functions/Classes | Responsibility |
|------|---------------------|----------------|
| `design/schemas.py` | `DesignPayload`, `ContractAuthorityPacket`, `ContractBoundary`, `CriticFinding` | Data models |
| `design/template_routing.py` | `route_template()` | (mode, scope) → TemplateProfile |
| `design/generate_context.py` | `_ast_summary()` | AST walker (skips venv/stdlib) |
| `design/validate_design.py` | `validate()` | Schema + logic validation, ADR save |

#### `planning`
| File | Key Functions/Classes | Responsibility |
|------|---------------------|----------------|
| `__lib/auto_verify.py` | `main()`, `verify_plan()` | 22+ readiness checks |
| `__lib/auto_fix.py` | `fix_plan()` | Non-semantic repairs only |
| `__lib/adversarial_review.py` | `AdversarialReviewContext`, `build_dispatch_specs()`, `collect_findings_status()` | 6-agent dispatch (5 parallel + critic) |
| `__lib/arch_handoff_state.py` | `find_pending_arch_handoff_receipt()`, `mark_arch_handoff_consumed()` | Architecture receipt tracking, TTL=20min |

#### `refactor`
| File | Key Functions/Classes | Responsibility |
|------|---------------------|----------------|
| `scripts/deduplicate.py` | `deduplicate_findings()` | Merge by file+line → canonical IDs |
| `scripts/refactor_plan.py` | `create_refactor_plan()` | Structured plan from findings |
| `scripts/plan_review.py` | `adversarial_review_plan()` | Risk analysis of refactor plan |
| `scripts/code_scanner.py` | `scan_code_patterns()` | TODO/FIXME/HACK/XXX/NOTE markers |

### Hooks

| Skill | Hook File | Trigger | Action |
|-------|-----------|---------|--------|
| `code_v3.0` | `hooks/PostToolUse_breadcrumb_tracker.py` | PostToolUse | Track workflow step completion |
| `code_v3.0` | `hooks/PreToolUse_plan_consumer_gate.py` | PreToolUse (Edit/Write) | Validates plan before edits |
| `code_v3.0` | `hooks/SessionStart_breadcrumb_init.py` | SessionStart | Breadcrumb initialization |
| `code_v3.0` | `hooks/detect_continuous_mode.py` | UserPromptSubmit | Sets CODE_CONTINUOUS_MODE |
| `design_v1.1` | `hooks/stop_if_unverified.py` | pre_response | Blocks response if `.verified_{RUN_ID}` missing |
| `design_v1.1` | `hooks/preflight_require_design.py` | preflight | Routes design-style queries into NTP |

### Utilities / Helpers

| Skill | File | Purpose |
|-------|------|---------|
| `code_v3.0` | `utils/normalize_paths.py` | Git Bash → Windows path normalization |
| `code_v3.0` | `utils/version_comparator.py` | Semantic version parsing |
| `code_v3.0` | `utils/user_optout_handler.py` | Modernization opt-out detection |
| `code_v3.0` | `scripts/behavior_gates_checker.py` | Behavior gate pattern matching |
| `code_v3.0` | `scripts/validate_done_claim.py` | Done claim verification |
| `refactor` | `scripts/state_manager.py` | `RefactorState`, `StateManager`, `cleanup_stale_state_files` |

### Configuration

| Skill | File | Purpose |
|-------|------|---------|
| `code_v3.0` | `behavior_gates_config.json` | Behavior gate patterns |
| `code_v3.0` | `coverage.json` | Coverage data (71%) |
| `code_v3.0` | `.test_profiles.json` | Test profile configs |
| `planning` | `io-validation-findings.json` | Adversarial I/O findings schema |
| `planning` | `references/deepseek-adversarial-schema.json` | DeepSeek V3.2 findings schema |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Terminal isolation**: All state files scoped to `CLAUDE_TERMINAL_ID` to support multi-terminal concurrency
2. **Evidence ledger**: TDD phases must produce verifiable evidence (test files, commands, output)
3. **Hook-gated execution**: PreToolUse/PreResponse hooks enforce phase ordering
4. **Solo-dev constitutional filter**: Enterprise patterns (service extraction, factory patterns) auto-filtered
5. **Consumer handshake proof**: No done claim until consumer contract precheck passes
6. **Strict mode for design**: design_v1.1 is the only skill with `strict` (not advisory) enforcement

### Technology Constraints

- **Python 3.12+** with type hints required
- **No per-skill requirements.txt** — dependencies managed at `cc-skills-sdlc` package level
- **Windows-first paths** (`P:/` drive letter) but `pathlib.Path` for cross-platform in most files
- **Context7 MCP** for library docs (code_v3.0 only)
- **`contract_primitives`** internal package (planning only, dynamic import with fallback)

### Things That MUST NOT Change

| Skill | Constraint | Why |
|-------|-----------|-----|
| `code_v3.0` | TRACE mandatory — no exemptions | Audit trail for solo-dev accountability |
| `code_v3.0` | TDD compliance required | Evidence-based quality gate |
| `code_v3.0` | Resume ledger required | Compaction survival |
| `design_v1.1` | `.verified_{RUN_ID}` flag gates response | Prevents unvalidated ADRs |
| `design_v1.1` | Max 3 validation attempts per RUN_ID | Prevents infinite loops |
| `planning` | auto_fix.py is non-semantic only | Cannot insert content or generate tasks |
| `planning` | Raw adversarial findings cannot be merged | Findings must be synthesized |
| `refactor` | RED phase characterization tests must fail | Proves current behavior before changing |
| `refactor` | Canonical IDs must follow COMP/DRY/CONC/PY/QUAL prefix | Deduplication schema |

---

## 6. KNOWN ISSUES

*(No verified known issues reported from agent scans. The following are inferred from architecture analysis.)*

| Issue | Skill | Impact | Workaround |
|-------|-------|--------|-----------|
| `contract_primitives` dynamic import fallback | `planning` | If package absent, arch handoff receipts fail silently | Ensure `contract_primitives` in Python path |
| Windows path hardcoded as `P:/` default | `code_v3.0`, `planning` | Non-portable across environments | Override via env vars |
| Context7 rate limit (60 qpm) shared across tracks | `code_v3.0` | EXPLORE track can exhaust budget for other tracks | `EXPLORE` track never blocks, falls back gracefully |
| Max 3 validation attempts per design RUN_ID | `design_v1.1` | Legitimate designs rejected after 3 failures | New RUN_ID required |
| Staggered 30s agent delay in refactor DISCOVER | `refactor` | Slow for large codebases | `--agents N` override |

---

## 7. INTEGRATION POINTS

### Skill Invocation Entry Points

| Skill | Slash Command | Aliases |
|-------|-------------|---------|
| `code_v3.0` | `/code` | `code feature`, `build feature`, `implement feature` |
| `design_v1.1` | `/design_v1.1` | — |
| `planning` | `/planning` | `/planning-v2`, `create a plan for`, `break this down` |
| `refactor` | `/refactor` | — |

### Inter-Skill Handoffs

```
/planning ──────────────────────► /design_v1.1
  (architecture blockers)           (returns CAP or Planning Handoff Packet)
                                         ▲
                                         │ nested resume
                                         │
                                 /planning continues after packet receipt

/code ───────────────────────────► /search
  (depends_on_skills)                 (context discovery)

/refactor ───────────────────────► pr-review-toolkit:code-simplifier
                                      (code simplification phase)
```

### Environment Variables Consumed

| Variable | Consumed By | Purpose |
|----------|-----------|---------|
| `TDD_STATE_DIR` | code_v3.0 | TDD state directory |
| `TDD_EVIDENCE_DIR` | code_v3.0 | Evidence directory |
| `CLAUDE_TERMINAL_ID` | code_v3.0, planning, refactor | Terminal isolation |
| `CLAUDE_SESSION_ID` | code_v3.0, planning | Session tracking |
| `CLAUDE_PROJECT_DIR` | code_v3.0 | Project root |
| `CLAUDE_HOOKS_DIR` | code_v3.0, planning | Hooks directory |
| `CODE_NO_CHECKLIST` | code_v3.0 | Bypass checklist |
| `CODE_CONTINUOUS_MODE` | code_v3.0 | Continuous mode flag |
| `CODE_NO_GOT` / `CODE_NO_TOT` | code_v3.0 | Disable GoT/ToT |
| `RALPH_LOOP_AUTO_DETECT` | code_v3.0 | Auto detect Ralph loops |
| `DESIGN_RUN_ID` | design_v1.1 | Design run identifier |
| `PLANNING_ARCH_HANDOFF_STATE_DIR` | planning | Architecture handoff state |
| `PLANNING_ARCH_HANDOFF_TTL_SECONDS` | planning | Handoff TTL (default 1200s) |
| `SDLC_MULTI_LLM` | planning | Multi-LLM mode (default 0) |

### Artifact Storage Convention

All runtime artifacts write to: `{CLAIREC_CODE_ARTIFACTS_DIR}` (env var, falls back to `.claude/.artifacts/`)

---

## 8. INPUT/OUTPUT CONTRACT

### Per-Phase Data Flow

#### /planning (multi-phase adversarial review)

| Phase | Reads | Writes | Constraint |
|-------|-------|--------|-----------|
| draft_plan | conversation history | `plan.md` | Concrete content only |
| auto_verify.py | `plan.md` | stderr errors | 22+ checks |
| auto_fix.py | `plan.md` | fixed `plan.md` | Non-semantic only |
| adversarial_review phase1 | `plan.md` | `findings-{agent}.json` | 5 agents parallel |
| adversarial_review critic | findings JSONs | `findings-critic.json` | Serial after phase1 |
| synthesize | plan + findings | rewritten `plan.md` | Only accepted findings |
| integration_trace | `plan.md` | trace results | Only 3+ TASKS plans |

#### /design_v1.1 (NTP)

| Phase | Reads | Writes | Constraint |
|-------|-------|--------|-----------|
| generate_context.py | workspace AST | stdout summary | Skips venv/__pycache__ |
| validate_design.py | `design_draft_{RUN_ID}.json` | `.verified_{RUN_ID}` | Max 3 attempts |
| stop_if_unverified hook | filesystem | — | Blocks if flag missing |

#### /code (11-phase)

| Phase | Reads | Writes | Constraint |
|-------|-------|--------|-----------|
| PhaseStateManager | git state | state JSON | Git hash rollback detection |
| EvidenceManager | test outputs | evidence ledger | Must verify file existence |
| PlanUpdater | plan.md | plan.md | Checksum + rollback |

#### /refactor (10-step)

| Step | Reads | Writes | Constraint |
|------|-------|--------|-----------|
| DISCOVER | target code | `findings-{agent}.json` | 8 agents staggered 30s |
| DEDUPLICATE | findings JSONs | `deduplicated.json` | Canonical IDs by file+line |
| CREATE PLAN | deduplicated.json | `refactor_plan.json` | Risk-level strategy |
| RED PHASE | refactor_plan | characterization tests | Must FAIL before changes |

### Quality Gates

| Skill | Gate | Checks | Does NOT Check |
|-------|------|--------|----------------|
| `design_v1.1` | `stop_if_unverified.py` hook | `.verified_{RUN_ID}` flag exists | JSON schema correctness |
| `planning` | auto_verify.py | Section headers, placeholders, blockers | Content accuracy |
| `code_v3.0` | `can_mark_done()` | 4 evidence types + file existence | Test passing |
| `refactor` | RED phase enforcement | Characterization tests FAIL | Test correctness |

---

## 9. AGENT DISPATCH DEFINITIONS

### /planning — adversarial_review.py

**Phase 1 (parallel — 5 agents):**

| Agent | subagent_type | Findings File |
|-------|--------------|---------------|
| compliance | `adversarial-compliance` | `findings-compliance.json` |
| logic | `adversarial-logic` | `findings-logic.json` |
| testing | `adversarial-testing` | `findings-testing.json` |
| security | `adversarial-security` | `findings-security.json` |
| failure-modes | `adversarial-failure-modes` | `findings-failure-modes.json` |

**Phase 2 (serial — 1 critic):**

| Agent | subagent_type | Findings File |
|-------|--------------|---------------|
| critic | `adversarial-critic` | `findings-critic.json` |

**Reference prompt file:** `references/adversarial-agent-prompts.md`

### /refactor — DISCOVER phase (staggered Task agents)

| Agent | subagent_type | Stagger | Focus |
|-------|--------------|---------|-------|
| 1 | `adversarial-compliance` | 0s | Bugs/Logic (race, error handling) |
| 2 | `adversarial-performance` | 30s | DRY/Simplicity (duplication) |
| 3 | `adversarial-performance` (tuned) | 60s | Leaks/Bottlenecks/N+1 |
| 4 | `adversarial-quality` | 90s | Conventions (type hints) |
| 5 | `python-simplifier` | 120s | Python 2025 standards |
| 6 | `/ai-pi-zai-glm51` | 150s | Architecture (cross-module coupling) |
| 7 | `/ai-pi-mm-m27` | 180s | Testing (coverage gaps) |
| 8 | `/ai-gemini` | 210s | Deep insight (semantic bugs) |

### /code — critique_agent_review

Uses `adversarial-review` parallel agent dispatch for quality gate.

---

## 10. FAILURE SCENARIOS

### F1: planning → design handoff infinite loop

**Trigger:** Architecture blocker found in plan → `/design` invoked → nested `/planning` call after packet receipt

**Propagation:** If `arch_handoff_state.py` receipt is stale (TTL expired) or terminal ID mismatch, `find_pending_arch_handoff_receipt()` returns None → plan remains blocked

**Detection:** Step 6 `remediate_blockers` shows "pending architecture handoff" but never resolves

**Actual vs expected:** Expected: blocker resolved in ≤20min. Actual: receipt expired silently

**Root cause:** `PLANNING_ARCH_HANDOFF_TTL_SECONDS=1200` is hardcoded; no renewal on active session

---

### F2: design_v1.1 blocked response after failed validation

**Trigger:** User runs `/design_v1.1` but JSON fails validation at step 4 (e.g., missing CAP boundaries)

**Propagation:** `validate_design.py` prints errors → user fixes → reruns → if 3rd attempt fails → RUN_ID exhausted → user must start new RUN_ID

**Detection:** Hook `stop_if_unverified.py` blocks every response until `.verified_{RUN_ID}` exists

**Actual vs expected:** Expected: feedback loop until valid. Actual: hard cap at 3 attempts forces new RUN_ID

**Root cause:** `.attempt_{RUN_ID}` counter increments on every validation run (including fix-retry), not just failed attempts

---

### F3: refactor RED phase skipped for P0 crash bugs

**Trigger:** P0 crash bug found → characterization tests skipped (TDD exemption for "it crashes")

**Propagation:** Refactor applied → regression suite runs → but P0 crash bug behavior wasn't characterized

**Detection:** PR review or production incident

**Actual vs expected:** Expected: characterization not needed for crash. Actual: no regression test for the crash path

**Root cause:** TDD exemption in SKILL.md: "P0: Crash bugs — NO (behavior is 'it crashes')"

---

### F4: code_v3.0 evidence ledger drift

**Trigger:** `EvidenceManager.record_red()` called but test file not yet written to disk

**Propagation:** `can_mark_done()` checks file existence → returns False even though RED phase started

**Detection:** User sees "cannot mark done" despite completing RED phase

**Root cause:** `record_red()` records the intent but doesn't atomic-write the test file first

---

## 11. APPENDIX: KEY CONSTANTS

### Hardcoded Values by Skill

| Skill | Constant | Value | File |
|-------|----------|-------|------|
| `code_v3.0` | `PBKDF2_ITERATIONS` | 480000 | `lib/state_encryption.py:150` |
| `code_v3.0` | `DEFAULT_QUERIES_PER_MINUTE` | 60 | `utils/context7_rate_limiter.py:19` |
| `code_v3.0` | `DEFAULT_WINDOW_SECONDS` | 60 | `utils/context7_rate_limiter.py:20` |
| `code_v3.0` | `DEFAULT_BATCH_WINDOW_MS` | 100 | `utils/context7_rate_limiter.py:21` |
| `code_v3.0` | `DEFAULT_MAX_RETRIES` | 3 | `utils/context7_client.py:16` |
| `code_v3.0` | `DEFAULT_INITIAL_BACKOFF` | 1.0 | `utils/context7_client.py:17` |
| `code_v3.0` | `_HOME_CLAUDE_STATE` | `~/.claude/.state/code` | `utils/phase_state.py:17` |
| `code_v3.0` | `_DEFAULT_EVIDENCE_DIR` | `P:/.claude/state` | `utils/evidence.py:15` |
| `planning` | `PLANNING_ARCH_HANDOFF_TTL_SECONDS` | 1200 | `__lib/arch_handoff_state.py:26` |
| `planning` | `CANONICAL_SECTION_ORDER` | 7 sections | `__lib/auto_fix.py:30-38` |
| `design_v1.1` | `MAX_ATTEMPTS` | 3 | `design/validate_design.py:25` |
| `design_v1.1` | `SKIP_DIRS` | venv, env, .venv, .env, __pycache__, .git, .ruff_cache, .mypy_cache | `design/generate_context.py:15` |
| `refactor` | Evidence tier: VERIFIED | confidence ≥ 90 | `deduplicate.py` |
| `refactor` | Evidence tier: UNVERIFIED | confidence ≥ 80 | `deduplicate.py` |
| `refactor` | Evidence tier: INFERRED | confidence < 80 | `deduplicate.py` |
| `refactor` | `AGENT_STAGGER_DELAY` | 30 seconds | SKILL.md |

---

## SKILL COMPARISON TABLE

| Aspect | `/code` | `/design_v1.1` | `/planning` | `/refactor` |
|--------|---------|----------------|-------------|-------------|
| **Phases** | 19 (11+ phases) | 4-step NTP | 13 steps | 10 steps |
| **Validation** | Checklist + evidence ledger | Schema + logic (max 3 attempts) | auto_verify.py (22+ checks) | TDD RED phase |
| **State** | JSON per terminal | Flag files + ADR | v2 envelope receipts | Findings JSON |
| **Multi-terminal** | PhaseStateManager + EvidenceManager | Per RUN_ID | arch_handoff_state | Terminal-scoped artifacts |
| **Rate limiting** | Context7RateLimiter (60 qpm) | None | None | None |
| **Encryption** | Fernet + PBKDF2 | None | None | None |
| **Hooks** | PreToolUse + PostToolUse + SessionStart | pre_response + preflight | None | None |
| **Sub-agents** | critique_agent_review | None | 6 adversarial agents | 8 staggered Task agents |
| **Inter-skill** | → /search | None | → /design (nested) | → pr-review-toolkit |
| **Evidence tier** | N/A | N/A | N/A | VERIFIED/UNVERIFIED/INFERRED |
| **Canonical IDs** | N/A | N/A | N/A | COMP/DRY/CONC/PY/QUAL |
