---
name: sqa-orchestrator
description: Unified SQA Orchestrator — 7-layer sequential quality model (Syntactic→Semantic→Structural→Requirements→Security→Performance→Operational→Meta-Synthesis)
version: 1.0.0
status: stable
category: quality
triggers:
  - /sqa
  - /sqa-orchestrate
entry_type: skill
requires_target: true

# /sqa — Unified SQA Orchestrator

Execute a 7-layer sequential quality analysis pipeline against a target codebase.

## Usage

```
/sqa <target-path>
/sqa-orchestrate <target-path>
```

## Layers

| Layer | Name | Tool | Hard Dependency |
|-------|------|------|----------------|
| 1 | SYNTACTIC | ruff, mypy, AI Distiller | — |
| 2 | SEMANTIC | verify (pytest), diagnose | — |
| 3 | STRUCTURAL | meta-review, harden, apply_safety_patterns | — |
| 4 | REQUIREMENTS | gto, spec-compliance | Layer 2 |
| 5 | SECURITY | adversarial-security, path traversal check, data-safety-vcs | — |
| 6 | PERFORMANCE | perf, adversarial-performance | — |
| 7 | OPERATIONAL | verify (hook chain), hook-audit, hook-inventory, recursive_failure_detector | — |
| META | META-SYNTHESIS | consensus detection, blind-spot detection, evidence quality | All |

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

### Meta-Synthesis
Consensus detection (2+ layers agree on same file:line:category).
Blind-spot detection (no coverage for a quality category when layer WAS available but found nothing — NOT when layer was skipped via D5).
Evidence quality check per `evidence-tiers`.

## Examples

```bash
/sqa P:/packages/my-package
/sqa-orchestrate ./src
```
