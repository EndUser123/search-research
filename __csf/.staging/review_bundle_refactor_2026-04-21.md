# Review Bundle: /refactor Skill

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Generated**: 2026-04-21
- **Scope**: `P:/packages/cc-skills-sdlc/skills/refactor/`
- **File Count**: 24 files (excluding cache/state)
- **Execution Mode**: 2-agent (10-50 files)
- **Version**: 3.0.0

### Domain & Purpose
Multi-file refactoring orchestrator for a solo-developer Claude Code environment. Discovers code issues via 8 parallel analysis agents, deduplicates findings, classifies technical debt, creates TDD-backed refactoring plans, executes changes with AST-based refactoring, and validates via LSP diagnostics and regression testing. Designed to prevent enterprise bloat while maintaining rigorous safety (git-tag checkpoints, constitutional filters, characterization tests).

### Scale Metrics
- ~1,500 LOC across Python scripts
- 9 reference documents (~700 lines)
- 1 SKILL.md (~279 lines, primary orchestration contract)
- 8 dispatched analysis agents per run
- 15-step workflow pipeline

### Your Environment
- **OS**: Windows 11 Pro, Git Bash shell
- **Primary language**: Python 3.14
- **Package type**: Claude Code plugin (`.claude-plugin/` + `core/`)
- **No external dependencies** — all scripts use stdlib only
- **Installed via**: Junction at `P:/.claude/skills/refactor/`

---

## 2. ARCHITECTURE OVERVIEW

```
User invokes /refactor <target>
        |
        v
  [1. DISCOVER] -- 8 staggered agents write findings JSON
        |            Agents: adversarial-compliance, adversarial-performance x2,
        |            adversarial-quality, python-simplifier, zai-glm51, mm-m27, gemini
        v
  [2. DEDUPLICATE] -- scripts/deduplicate.py merges by file+line
        |
  [2.5 EVIDENCE TIER] -- optional verification checkpoint
        |
  [3. CLASSIFY_DEBT] -- label: design/code/test/documentation debt
        |               + code smell -> technique mapping
        v
  [4. PRIORITIZE] -- P0 (bugs) -> P1 (errors) -> P2 (DRY) -> P3 (conventions)
        |
  [5. CONSTITUTIONAL FILTER] -- SoloDevConstitutionalFilter
        |                        --dry-run: stop after plan
        v
  [6. PLAN] -- scripts/refactor_plan.py creates structured plan
        |     + tiny commits breakdown
        |     + out-of-scope section
        |     + scripts/plan_review.py adversarial review
        v
  [7. RED PHASE] -- characterization tests must FAIL
        |
  [8. CHECKPOINT_RED] -- git tag rollback point
        |
  [9. ADVERSARIAL REVIEW] -- 8-perspective stress test on tests
        |
  [10. REFACTOR] -- AST-based code changes (GREEN phase)
        |
  [11. LSP_VALIDATE] -- post-edit type checking
        |
  [12. CHECKPOINT_GREEN] -- git tag rollback point
        |
  [13. REGRESSION] -- full test suite
        |
  [14. CODE SIMPLIFICATION] -- pr-review-toolkit:code-simplifier
        |
  [15. DELETION_METRIC] -- lines_removed - lines_added
```

### Key Subsystems

| Subsystem | Files | Purpose |
|-----------|-------|---------|
| **Orchestration** | `skills/refactor/SKILL.md` | 15-step workflow contract |
| **Deduplication** | `scripts/deduplicate.py` (172 lines) | Merge findings by file+line, assign canonical IDs |
| **Planning** | `scripts/refactor_plan.py` (317 lines) | Create structured plan with risk assessment |
| **Review** | `scripts/plan_review.py` (323 lines) | Adversarial review for regex/batch/rollback risks |
| **Scanning** | `scripts/code_scanner.py` (235 lines) | Detect TODO/FIXME/HACK markers with risk scores |
| **References** | 9 `.md` files in `references/` | TDD, AST, constitutional, evidence, quality docs |

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences
1. User invokes `/refactor <target>` or `/refactor continue`
2. Orchestrator (Claude) reads SKILL.md, follows workflow steps
3. Agents write findings JSON to artifacts dir
4. Python scripts process findings: deduplicate -> plan -> review
5. TDD characterization tests written, verified failing
6. AST-based refactoring applied
7. LSP validation after each edit
8. Regression test suite run
9. Deletion metric calculated

### State Management
- **Artifacts dir**: `P:/.claude/.artifacts/{terminal_id}/refactor/`
- **Findings files**: `{artifacts_dir}/{target}/refactor/findings-{agent-name}.json`
- **Deduplicated output**: `{artifacts_dir}/{target}/refactor/deduplicated.json`
- **Plan output**: `{artifacts_dir}/{target}/refactor/plan-{timestamp}.json`
- **Git tags**: `refactor/red-{target}-{timestamp}`, `refactor/green-{target}-{timestamp}`
- **State files**: `.claude/state/policy_gate/` and `.claude/state/sessions/` (runtime caches)

### Error Handling
- **Agent failure**: Graceful degradation — skip failed agent, continue with remaining
- **Plan review rejection**: CONDITIONAL/ADVISED status triggers revision
- **RED phase failure**: Test must fail; if it passes, behavior isn't characterized
- **GREEN phase failure**: Reset to CHECKPOINT_RED tag
- **Regression failure**: Reset to CHECKPOINT_GREEN tag
- **LSP errors**: Pause, fix, re-validate before next file

---

## 4. COMPONENT INVENTORY

### Core Logic

| Component | Path | Responsibility | Lines |
|-----------|------|---------------|-------|
| `deduplicate_findings()` | `scripts/deduplicate.py:18` | Merge multi-agent findings by file+line, assign canonical IDs | 100 |
| `create_refactor_plan()` | `scripts/refactor_plan.py:16` | Build structured plan from findings, assess risk, suggest rollback | 112 |
| `adversarial_review_plan()` | `scripts/plan_review.py:14` | Review plan for regex/batch/rollback risks | 46 |
| `scan_code_patterns()` | `scripts/code_scanner.py:25` | Scan for TODO/FIXME/HACK markers with risk scoring | 79 |

### Utility Functions

| Function | Path | Purpose |
|----------|------|---------|
| `_tier_for_confidence()` | `scripts/deduplicate.py:121` | Map confidence (0-100) to evidence tier |
| `_assess_change_risk()` | `scripts/refactor_plan.py:131` | HIGH/MEDIUM/LOW risk classification |
| `_suggest_rollback()` | `scripts/refactor_plan.py:162` | Per-change-type rollback strategy |
| `plan_to_markdown()` | `scripts/refactor_plan.py:186` | Plan dict -> readable markdown |
| `review_to_markdown()` | `scripts/plan_review.py:260` | Review dict -> readable markdown |
| `_review_change()` | `scripts/plan_review.py:63` | Single-change risk review |
| `_review_strategy()` | `scripts/plan_review.py:110` | Overall strategy review |
| `_detect_state_impact()` | `scripts/code_scanner.py:218` | Keyword-based state impact detection |

### Configuration
- `skills/refactor/SKILL.md` — YAML frontmatter + workflow contract
- `AGENTS.md` — Package metadata, junction setup
- No `config.json` or settings file — all configuration in SKILL.md

### Reference Documents

| File | Lines | Contents |
|------|-------|----------|
| `references/agent-enhancements.md` | 63 | CC triage thresholds, import hygiene patterns |
| `references/tdd-implementation.md` | 255 | TDD enforcement flow, exemption detection, phase code |
| `references/constitutional-compliance.md` | 42 | Prohibited patterns filter, SoloDevConstitutionalFilter code |
| `references/ast-refactoring.md` | 46 | LibCST requirement, ExtractMethodTransformer example |
| `references/plan-and-review-libraries.md` | 62 | Plan/review API, risk codes (RISK-001, ROLLBACK-001, COMPLEX-001) |
| `references/subagent-routing.md` | 24 | Result envelope format, routing rules |
| `references/evidence-and-validation.md` | 85 | Evidence collection, sequential enforcement, dead code detection |
| `references/aid-integration.md` | 42 | AID workflow for large-scale refactors (50+ files) |
| `references/code-quality-standards.md` | 68 | DRY targets, naming, function design, regex patterns |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
- **Solo-dev constraints**: No enterprise patterns, no team-oriented abstractions
- **TDD mandatory**: Characterization tests before any production code changes
- **AST-first**: All Python refactoring via LibCST, never regex
- **Constitutional filter**: Every recommendation passes SoloDevConstitutionalFilter
- **8-dimension rubric**: Findings scored across Naming, Object Calisthenics, Coupling/Cohesion, Immutability, Domain Integrity, Type System, Simplicity, Performance

### Technology Constraints
- Python stdlib only — no third-party runtime dependencies for scripts
- LibCST required at refactoring time (not imported by scripts)
- All agent output via `Write` tool to JSON files — never inline

### Things That Must NOT Change
- SoloDevConstitutionalFilter cannot be weakened
- AST-based refactoring requirement cannot be bypassed
- Agent staggering (30s apart) to prevent context flooding
- Finding verification requirement (agents must read actual files)
- Git-tag checkpoints for rollback safety

---

## 6. KNOWN ISSUES

### Critical

| # | Issue | Impact | Workaround |
|---|-------|--------|------------|
| 1 | `scripts/__init__.py` imports non-existent `state_manager` module | ImportError on package import | ASSUMPTION: `state_manager.py` was deleted but import not updated. May cause issues if scripts are imported as package. |
| 2 | `scripts/code_scanner.py` references undefined `calculate_risk_score` | NameError at runtime when risk scoring executes | Function was likely part of a shared module that was removed. Scan would fail on any file with markers. |
| 3 | `scripts/code_scanner.py` imports `Path` but never uses it | Dead import | Cosmetic only. |

### Medium

| # | Issue | Impact | Workaround |
|---|-------|--------|------------|
| 4 | LSP_VALIDATE step (11) has no script — relies on Claude running LSP tool | Enforcement is advisory, not hard-gated | Manual discipline or hook required |
| 5 | DELETION_METRIC step (15) has no script — relies on Claude calculating | Metric may be skipped or inaccurate | Could add a `deletion_metric.py` script |
| 6 | CLASSIFY_DEBT step (3) has no script — relies on Claude labeling | Debt labels may be inconsistent across runs | Could add a `classify_debt.py` script |
| 7 | `code_scanner.py` not referenced in SKILL.md workflow | Dead code — scanner exists but no step uses it | Could integrate into DISCOVER phase |

### Low

| # | Issue | Impact | Workaround |
|---|-------|--------|------------|
| 8 | EVIDENCE TIER step (2.5) not in frontmatter `workflow_steps` | Optional checkpoint not tracked in workflow | By design — optional steps excluded from frontmatter |
| 9 | No tests for any script (`deduplicate.py`, `refactor_plan.py`, `plan_review.py`) | Regressions in scripts won't be caught | ASSUMPTION: tested manually during development |
| 10 | `references/ast-refactoring.md` references `P:/packages/refactor/AST_HELPERS_GUIDE.md` | External reference may be stale | Verify path exists before relying on it |

---

## 7. INTEGRATION POINTS

### Skill Invocations
- `/aid` — single-file refactoring analysis (optional `--include-aid` flag)
- `/p` — Python 2025 standards compliance (agent 5)
- `/context7` — fresh library docs for modernize synergy
- `/tdd` — NOT delegated to (RED phase runs inline)
- `/v` — sequential validation pipeline (referenced in evidence docs)

### External Tools
- `ruff` — async bug detection before refactoring
- LibCST — AST-based code transformation
- `adversarial-review` — 8-perspective stress testing
- `pr-review-toolkit:code-simplifier` — post-refactor polish
- LSP server — `textDocument/publishDiagnostics` for type checking

### Data Exchange
- Input: user specifies target path/glob/pattern
- Output: JSON findings files, plan JSON, git tags, deletion metric
- Artifacts: all written to `P:/.claude/.artifacts/{terminal_id}/refactor/`

---

## 8. INPUT/OUTPUT CONTRACT

### Per-Phase Data Flow

| Phase | Reads | Writes | Key Constraint |
|-------|-------|--------|---------------|
| DISCOVER | Source code files via agents | `findings-{agent}.json` | Agents staggered 30s; must verify findings by reading actual files |
| DEDUPLICATE | All `findings-*.json` files | `deduplicated.json` | Must merge by file+line, assign canonical IDs |
| EVIDENCE TIER | `deduplicated.json` | Updated `deduplicated.json` with `[VERIFIED]`/`[UNVERIFIED]` labels | Only runs if findings lack verification |
| CLASSIFY_DEBT | `deduplicated.json` | Debt-type labels on each finding | Maps smell category to technique |
| PRIORITIZE | Labeled findings | Priority assignment (P0-P3) | Strict ordering: bugs > errors > DRY > conventions |
| CONSTITUTIONAL FILTER | Prioritized findings | Filtered findings | Removes enterprise bloat patterns |
| PLAN | Filtered findings | `plan-{timestamp}.json` | Must include tiny commits + out-of-scope section |
| RED PHASE | Source code | Characterization test files | Tests MUST FAIL |
| CHECKPOINT_RED | Git state | Git tag `refactor/red-*` | Rollback point before production code changes |
| REFACTOR | Plan + source code | Modified source files | Must use AST-based refactoring |
| LSP_VALIDATE | Modified files | LSP diagnostic results | Pause-fix-revalidate cycle |
| CHECKPOINT_GREEN | Git state | Git tag `refactor/green-*` | Rollback point after tests pass |
| REGRESSION | Full test suite | Pass/fail results | Must show zero new failures |
| CODE SIMPLIFICATION | Refactored code | Further simplified code | Via `pr-review-toolkit:code-simplifier` |
| DELETION_METRIC | Git diff | `lines_removed - lines_added` count | Positive = success; negative = flag for review |

### Agent Read Sources
- **Agents 1-8**: Read **source** code directly (NOT operator analysis). Each agent independently reads and verifies findings against actual file content.
- **Plan review script** (`plan_review.py`): Reads **analysis** (plan JSON), not source code.
- **Deduplicate script**: Reads **analysis** (findings JSON), not source code.

### Quality Gates

| Gate | Checks | Does NOT Check | When |
|------|--------|----------------|------|
| Finding quality | Non-empty description, file, line, confidence > 0 | Content accuracy, file:line validity | After each agent completes |
| Evidence tier | `[VERIFIED]`/`[UNVERIFIED]` annotation present | Whether verification was correct | After DEDUPLICATE |
| Constitutional filter | No prohibited patterns in recommendations | Whether recommendation is actually good | After PRIORITIZE |
| Plan review | Regex risks, rollback strategy, batch operations | Whether plan achieves goals | After PLAN |
| RED phase | Test FAILS | Whether test correctly characterizes behavior | Before REFACTOR |
| LSP validation | No type errors, undefined refs | Runtime correctness | After each file edit |
| Regression | Zero new test failures | Whether tests cover the change | After REFACTOR |

---

## 9. AGENT DISPATCH DEFINITIONS

### Per-Agent Specification

| Agent | subagent_type | Role | Reads | Output File |
|-------|--------------|------|-------|-------------|
| Agent 1 | `adversarial-compliance` | Bugs/Logic: race conditions, error handling, TOCTOU | Source | `findings-adversarial-compliance.json` |
| Agent 2 | `adversarial-performance` | DRY/Simplicity: duplication, extraction, concurrency | Source | `findings-adversarial-performance.json` |
| Agent 3 | `adversarial-performance` (--focus performance) | Leaks, bottlenecks, N+1, algorithmic improvements | Source | `findings-adversarial-performance-2.json` |
| Agent 4 | `adversarial-quality` | Conventions: type hints, patterns, maintainability | Source | `findings-adversarial-quality.json` |
| Agent 5 | `python-simplifier` | Python 2025 standards, async patterns | Source | `findings-python-simplifier.json` |
| Agent 6 | `/ai-pi-zai-glm51` | Architecture: coupling, boundaries, shared state | Source | `findings-ai-pi-zai-glm51.json` |
| Agent 7 | `/ai-pi-mm-m27` | Testing: coverage gaps, missing scenarios, brittle tests | Source | `findings-ai-pi-mm-m27.json` |
| Agent 8 | `/ai-gemini` | Deep insight: semantic bugs, idiom violations | Source | `findings-ai-gemini.json` |

### Dispatch Order
- **Parallel**: All 8 agents run staggered (30s apart) — not simultaneous
- **Serial after**: DEDUPLICATE, CLASSIFY_DEBT, PRIORITIZE, PLAN run sequentially
- **Serial after**: RED, CHECKPOINT_RED, ADVERSARIAL REVIEW run sequentially
- **Serial after**: REFACTOR, LSP_VALIDATE, CHECKPOINT_GREEN, REGRESSION run sequentially

### Finding JSON Format
Each agent writes:
```json
{
  "agent": "agent-name",
  "target": "target-path",
  "timestamp": "ISO-8601",
  "findings": [
    {
      "id": "unique-id",
      "description": "non-empty description",
      "file": "relative/path.py",
      "line": 42,
      "confidence": 95,
      "priority": "P0|P1|P2|P3",
      "debt_type": "design_debt|code_debt|test_debt|documentation_debt",
      "smell_category": "Bloaters|OO Abusers|Change Preventers|Couplers|Dispensables",
      "verification": "[VERIFIED]|[UNVERIFIED]",
      "rubric_scores": {
        "naming": 0-10,
        "object_calisthenics": 0-10,
        "coupling_cohesion": 0-10,
        "immutability": 0-10,
        "domain_integrity": 0-10,
        "type_system": 0-10,
        "simplicity": 0-10,
        "performance": 0-10
      }
    }
  ]
}
```

---

## 10. FAILURE SCENARIOS

### Verified Failure: `__init__.py` ImportError
1. **Trigger**: Any code does `from refactor.scripts import ...` or `import refactor.scripts`
2. **Propagation**: `__init__.py` runs `from .state_manager import RefactorState, StateManager, cleanup_stale_state_files` -> `ModuleNotFoundError`
3. **Detection point**: Immediate on import
4. **Root cause**: `state_manager.py` was deleted but `__init__.py` not updated
5. **Fix**: Remove the import from `__init__.py`, or restore `state_manager.py`

### Verified Failure: `code_scanner.py` NameError
1. **Trigger**: `scan_code_patterns()` processes any file containing TODO/FIXME/HACK markers
2. **Propagation**: `_build_todo_item()` calls `calculate_risk_score()` -> `NameError`
3. **Detection point**: At runtime when markers found
4. **Root cause**: `calculate_risk_score` was part of a shared module that was removed
5. **Fix**: Implement inline risk scoring or restore the shared function

### Hypothetical Failure: Agent Cascading
1. **Trigger**: One agent produces a bad finding (wrong file, stale line reference)
2. **Propagation**: DEDUPLICATE merges it; CLASSIFY_DEBT labels it; PLAN schedules changes for it
3. **Detection point**: RED phase (test targets wrong code) or REFACTOR (edits wrong location)
4. **Root cause**: Agent didn't verify finding by reading actual file
5. **Mitigation**: Verification requirement in DISCOVER step + evidence tier checkpoint

### Hypothetical Failure: Scope Creep
1. **Trigger**: REFACTOR phase touches files not in plan
2. **Propagation**: More files changed = larger blast radius, harder rollback
3. **Detection point**: DELETION_METRIC shows unexpected additions; REGRESSION catches unrelated breakage
4. **Root cause**: No hard enforcement of plan boundaries
5. **Mitigation**: "Out of Scope" section requirement in PLAN step

### Failure Pattern: 8 Agents Reporting Same False Positive
1. **Trigger**: All agents independently flag a pattern that looks like a bug but isn't
2. **Propagation**: DEDUPLICATE merges into high-confidence canonical finding; PLAN treats as P0
3. **Detection point**: ADVERSARIAL REVIEW should catch, or RED phase fails (can't write failing test for non-bug)
4. **Root cause**: Shared false premise from codebase structure
5. **Mitigation**: Evidence tier verification + adversarial review meta-critique

---

## 11. APPENDIX: FILE TREE

```
P:/packages/cc-skills-sdlc/skills/refactor/
|-- AGENTS.md                              # Package metadata
|-- CHANGELOG.md                           # Version history
|-- CONTRIBUTING.md                        # Contribution guide
|-- LICENSE                                # License
|-- README.md                              # Overview
|-- .gitignore
|-- .claude/
|   |-- state/
|       |-- policy_gate/                   # Analysis caches
|       |-- sessions/                      # Session state
|-- docs/
|   |-- planning/
|       |-- plan.md                        # Planning docs
|-- references/
|   |-- agent-enhancements.md              # CC triage, import hygiene
|   |-- aid-integration.md                 # AID workflow for large refactors
|   |-- ast-refactoring.md                 # LibCST requirement
|   |-- changelog.md                       # Reference changelog
|   |-- code-quality-standards.md          # DRY, naming, function design
|   |-- constitutional-compliance.md       # Prohibited patterns filter
|   |-- evidence-and-validation.md         # Evidence collection, dead code
|   |-- plan-and-review-libraries.md       # Plan/review API, risk codes
|   |-- subagent-routing.md                # Result envelope, routing
|   |-- tdd-implementation.md              # TDD enforcement, exemptions
|-- scripts/
|   |-- __init__.py                        # BROKEN: imports missing state_manager
|   |-- code_scanner.py                    # BROKEN: references missing calculate_risk_score
|   |-- deduplicate.py                     # Findings deduplication (working)
|   |-- plan_review.py                     # Adversarial plan review (working)
|   |-- refactor_plan.py                   # Plan creation (working)
|-- skills/
    |-- refactor/
        |-- SKILL.md                       # Primary orchestration contract (v3.0.0)
```
