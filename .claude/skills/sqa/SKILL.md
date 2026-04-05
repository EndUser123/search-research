---
name: sqa
description: Unified SQA Orchestrator — 8-layer sequential quality model (Predictive→Syntactic→Semantic→Structural→Requirements→Security→Performance→Operational→Meta-Synthesis) with contract-integrity, Contract Authority Packet alignment, and resume-integrity certification
version: 1.4.0
status: stable
category: quality
triggers:
  - /sqa
entry_type: skill
requires_target: false
enforcement: none
---

# /sqa — Unified SQA Orchestrator

Execute an 8-layer sequential quality analysis pipeline against a target codebase.

For workflow infrastructure, SQA must certify contract integrity, resume integrity, and stale-data immunity, not just generic quality.

## Usage

```
/sqa <target-path>   # explicit target
/sqa                 # auto-detect target via semantic intent resolution
```

### Auto-Detect Target (if no argument provided)

Resolve target via semantic intent, not archaeology:

1. **Named outputs** (highest priority): If user references a named output from conversation (e.g., "sqa the hook system we built") → use that
2. **Active task context**: If `/code` or `/planning` was recently running → the feature/plan they were working on
3. **Conversation semantic**: What were we discussing when `/sqa` was invoked? What was just implemented or modified?
4. **Recent changes as fallback**: Files modified in last 5-10 turns — weight by semantic relevance, not recency alone
5. **Only ask if genuinely ambiguous**: When >3 semantically-distinct targets exist with no clear intent signal

State assumption: "Certifying [X] — assumption based on [signal]. Correct?" Only prompt for confirmation if intent is unclear.

## Layers

| Layer | Name | Tool | Dispatch | Hard Dependency |
|-------|------|------|---------|----------------|
| 0 | PREDICTIVE | adversarial-logic, adversarial-quality, adversarial-io-validation, adversarial-security, adversarial-performance, adversarial-testing, adversarial-state-machine | **Agent** | — |
| 1 | SYNTACTIC | ruff, mypy, AI Distiller | Python/CLI | — |
| 2 | SEMANTIC | verify (pytest), diagnose | Python/CLI | — |
| 3 | STRUCTURAL | meta-review, harden, apply_safety_patterns | Python/CLI | — |
| 4 | REQUIREMENTS | gto, spec-compliance | Python/CLI | Layer 2 |
| 5 | SECURITY | adversarial-security, path traversal check, data-safety-vcs | **Agent** + Python/CLI | — |
| 6 | PERFORMANCE | perf, adversarial-performance | **Agent** + CLI | — |
| 7 | OPERATIONAL | verify (hook chain), hook-audit, hook-inventory, recursive_failure_detector | Python/CLI | — |
| META | META-SYNTHESIS | consensus detection, blind-spot detection, evidence quality | Python | All |

### Execution Model

**The LLM is the conductor.** SKILL.md is the score — I execute the workflow by:

1. **Validate target** via `_validate_target()` utility
2. **Dispatch Agent-based layers** via `Agent` tool:
   - L0 (PREDICTIVE): Dispatch `adversarial-logic`, `adversarial-quality`, `adversarial-io-validation`, `adversarial-security`, `adversarial-performance`, `adversarial-testing`, `adversarial-state-machine` agents in parallel
   - L5 (SECURITY): Dispatch `adversarial-security` agent; run path traversal check via Python utility
   - L6 (PERFORMANCE): Dispatch `adversarial-performance` agent; run perf checks via Python utility
3. **Run Python/CLI layers** via Bash subprocess:
   - L1 (SYNTACTIC): `ruff check`, `mypy`
   - L2 (SEMANTIC): `verify` (pytest), `diagnose`
   - L3 (STRUCTURAL): `meta-review`, `harden`, `apply_safety_patterns`
   - L4 (REQUIREMENTS): `gto`, `spec-compliance` — SKIP if L2 had failures
   - L7 (OPERATIONAL): `hook-audit`, `hook-inventory`, `recursive_failure_detector`
4. **Synthesize META** — consensus detection, blind-spot detection, evidence quality

**Orchestrator.py** is a **pure utilities module** — it provides `_validate_target`, `_atomic_write`, `L2State`, `SQAReport`, `save_report`. It contains **no orchestration logic**. Do not run `orchestrator.py` directly.

## Target Validation (SEC-001)

Before any subprocess call, the target path is validated:

```python
from pathlib import Path
import os

def _validate_target(target: str) -> Path:
    resolved = Path(os.path.realpath(target))
    assert resolved.exists() and resolved.is_dir(), f"Target {target} does not exist or is not a directory"
    assert not resolved.is_symlink(), f"Target {target} is a symlink"
    allowed_roots = [Path.cwd()]
    assert any(resolved.is_relative_to(r) for r in allowed_roots), f"Target {target} outside allowed roots"
    return resolved
```

## Findings Model

Every finding includes:
- `finding_id`: Unique ID (e.g., `L1-001`)
- `severity`: CRITICAL, HIGH, MEDIUM, LOW
- `layer`: L1–L7, META
- `title`: Short description
- `description`: Detailed explanation
- `location`: `file:line` when applicable
- `evidence_tier`: 1–4
- `consensus`: Number of layers that found this issue (default 1)
- `category`: quality category

## Health Score

```
health_score = max(-100, 100 - unique_CRITICAL*20 - unique_HIGH*10 - unique_MEDIUM*5 - unique_LOW*2)
```

Uses **deduplicated** severity counts (D4 deduplication removes consensus duplicates before scoring). Negative scores preserved for catastrophic severity differentiation.

## Output

`SQAReport` dataclass containing:
- `findings: List[Finding]` — all findings from all layers
- `health_score: int` — overall health score
- `layers_completed: List[str]` — completed layer names
- `audit_trail: List[AuditEntry]` — all skill invocations with timestamp, skill, exit code, finding count
- `target: str` — validated target path

Reports are saved with `chmod 600` (owner-read-write only). Findings do NOT include exact `file:line` in shared/exported output — only category and severity. A redaction option strips all `location` fields before export.

## Hard Dependencies

**Layer 2 → Layer 4**: If Layer 2 (SEMANTIC) reports failures, Layer 4 (REQUIREMENTS) **MUST NOT** execute. Skip with warning.

## Graceful Degradation

If a layer's tool is unavailable and it is NOT a hard dependency for a subsequent layer, skip with warning and continue.

**ALL-tools-unavailable behavior**: If ALL tools for a layer are unavailable, log `ERROR: All tools unavailable for Layer N — cannot proceed` and skip all remaining layers.

## Resource Bounds

- `file_count <= 10_000`
- `total_size <= 100MB`

Reject oversized targets early with `Target exceeds resource limits`.

## Layer Details

### Layer 1 — SYNTACTIC
Runs: `ruff check`, `mypy` (if Python), AI Distiller structure analysis.
Non-Python files skip both tools gracefully.

### Layer 2 — SEMANTIC
Runs: `verify` Tier 1 (pytest) and Tier 3 (e2e) via subprocess.
If failures detected, runs `diagnose` structured hypothesis protocol.
Checks `test_*.py` files exist.

**Framework Syntax Verification (Context7):**
When diagnosing test failures or verifying pytest/Django/vitest assertions, invoke `/context7` to confirm framework-specific syntax is correct. Test diagnostics often surface outdated patterns (e.g., deprecated `assertEquals`, wrong `pytest.raises`签名).

**Query expansion pattern:**
| Scenario | Query Expansion |
|----------|-----------------|
| pytest failure | "pytest assert statement syntax for exception testing with raises" |
| Django test | "Django test assert methods status codes and JSON responses" |
| vitest failure | "vitest expect assertions for async functions with examples" |

**Mode:** `code_only` (familiar frameworks); `full` (unfamiliar or ambiguous failures)

### Layer 3 — STRUCTURAL
AST import graph analysis for circular deps (reuse `meta-review` ImportGraphAnalyzer).
Assertion guard and parameter validation scans (reuse `harden`).
Safety pattern verification (reuse `apply_safety_patterns`).

### Layer 4 — REQUIREMENTS
Runs: `gto` gap analysis, `spec-compliance` protocol check.
Checks artifact status (PRD/ARD/CHANGELOG/README sync).
HARD DEPENDENCY: Layer 4 MUST NOT execute if Layer 2 reported failures.

### Layer 5 — SECURITY
Path traversal check (reuse `meta-review` PathTraversalAnalyzer).
`adversarial-security` subagent.
Anti-bleed gates verification (reuse `data-safety-vcs`).
External skill calls use `ALLOWED_COMMANDS` allowlist.

### Layer 6 — PERFORMANCE
`perf` tracing for nested ThreadPoolExecutors and thread-to-CPU mismatches.
`adversarial-performance` bottleneck analysis.

### Layer 7 — OPERATIONAL
`verify` Tier 2 (hook chain + router).
`hook-audit`, `hook-inventory`.
`recursive_failure_detector.py` hook.

Layer 7 must also verify:

- contract validators exist at critical boundaries
- required `Contract Authority Packet` artifacts exist at contract-sensitive boundaries
- downstream validators and proofs consume packet semantics rather than contradictory prose
- multi-terminal isolation holds
- stale-data invalidation is defined and reachable
- compact/resume path does not proceed on partial state
- producer success is not mistaken for consumer success

### Meta-Synthesis
Consensus detection (2+ layers agree on same file:line:category).
Blind-spot detection (no coverage for a quality category when layer WAS available but found nothing — NOT when layer was skipped via D5).
Evidence quality check per `evidence-tiers`.
Flag when a packet exists but is ignored, when prose and packet disagree, or when a packet is too underspecified to certify.

## Routing Behavior

`/sqa` certifies the system and should route findings to owning skills:

- `/arch` for architecture and contract-model failures
- `/planning` for plan/readiness and artifact-shape failures
- `/verify` for missing or insufficient proof
- `/code` for concrete implementation defects
- `/pre-mortem` for high-risk unresolved failure patterns

`/sqa` should not directly absorb those responsibilities.

## Examples

```bash
/sqa P:/packages/my-package
/sqa P:/hooks  # sqa the hook system
/sqa           # auto-detect target
```

**Do not run `orchestrator.py` directly** — it is a utilities module only.
