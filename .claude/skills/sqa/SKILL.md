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
enforcement: strict
# Extensions to SKILL_SCHEMA (not enumerated in schema):
#   version: skill version string
#   status: stable|experimental|deprecated
#   entry_type: skill|agent|hook
#   requires_target: true|false (auto-detect behavior)
#   enforcement: strict|advisory|none
---

# /sqa — Unified SQA Orchestrator

Execute an 8-layer sequential quality analysis pipeline against a target codebase.

For workflow infrastructure, SQA must certify contract integrity, resume integrity, and stale-data immunity, not just generic quality.

## Usage

```
/sqa <target-path>               # explicit target
/sqa                             # auto-detect target via semantic intent resolution
/sqa --layer=N                   # run specific layer only (0-7, META)
/sqa --focus <lens>              # apply focus lens (see Focus Lenses below)
/sqa --halt-on <severity>        # halt after layer if findings exceed threshold (default: HIGH)
/sqa --fix                       # auto-fix safe issues in L1/L2 (formatting, imports, lint)
/sqa --dry-run                   # detection-only: report what would run without executing
/sqa --evidence                  # write structured JSON results to terminal-isolated path
/sqa --quick                     # only analyze files from current session context
```

**`--halt-on` severity threshold:**
| Value | Behavior |
|-------|----------|
| `HIGH` | **(default)** Halt after a layer if any HIGH or CRITICAL findings exist |
| `CRITICAL` | Halt only on CRITICAL findings |
| `MEDIUM` | Halt on MEDIUM, HIGH, or CRITICAL |
| `NONE` | Run all layers regardless — collect all findings |

**Focus lenses** (same as `/p` `--focus`):
| Lens | Effect |
|------|--------|
| `risk` | Pre-mortem failure mode analysis |
| `gaps` | Completeness check — missing items, unhandled cases |
| `opportunities` | Optimization and value identification |
| `security` | Prioritize adversarial-security and path traversal |
| `complexity` | Flag high-cyclomatic-complexity functions |
| `duplicates` | Run duplicate detection |
| `quality` | Emphasize code smells and conventions |
| `performance` | Run with profiling awareness |
| `architecture` | Architectural perspective and cross-module deps |
| `test` | Focus on test quality and coverage gaps |
| `library` | Dependency analysis and CVE checks |
| `comprehensive` | ALL lenses elevated to blocking |

### Auto-Detect Target (if no argument provided)

Resolve target via semantic intent, not archaeology:

1. **Named outputs** (highest priority): If user references a named output from conversation (e.g., "sqa the hook system we built") → use that
2. **Active task context**: If `/code` or `/planning` was recently running → the feature/plan they were working on
3. **Conversation semantic**: What were we discussing when `/sqa` was invoked? What was just implemented or modified?
4. **Recent changes as fallback**: Files modified in last 5-10 turns — weight by semantic relevance, not recency alone
5. **Only ask if genuinely ambiguous**: When >3 semantically-distinct targets exist with no clear intent signal

State assumption: "Certifying [X] — assumption based on [signal]. Correct?" Only prompt for confirmation if intent is unclear.

**Phase/State Detection** (optional smart routing — implement if needed):

| Signal | Layer |
|--------|-------|
| No tests or tests failing | L1 SYNTACTIC + L2 SEMANTIC |
| Tests pass, never reviewed | L3 STRUCTURAL |
| Reviewed, files changed since | L3 STRUCTURAL (re-review) |
| Reviewed, never validated | L7 OPERATIONAL |
| All complete, no changes | Report "Ready" |

**Focus lenses** propagate to Agent-based layers (L0, L5, L6) adjusting agent priority and confidence thresholds.

## Layers

| Layer | Name | Tool | Dispatch | Hard Dependency |
|-------|------|------|---------|----------------|
| 0 | PREDICTIVE | adversarial-logic, adversarial-quality, adversarial-io-validation, adversarial-security, adversarial-performance, adversarial-testing, adversarial-state-machine | **Agent** (skill-level dispatch only — Python layer returns empty list) | — |
| 1 | SYNTACTIC | ruff, mypy, AI Distiller | Python/CLI | — |
| 2 | SEMANTIC | verify (pytest), diagnose | Python/CLI | — |
| 3 | STRUCTURAL | meta-review, harden, apply_safety_patterns | Python/CLI | — |
| 4 | REQUIREMENTS | gto, spec-compliance | Python/CLI | Layer 2 |
| 5 | SECURITY | adversarial-security, path traversal check, data-safety-vcs | **Agent** + Python/CLI (dispatch via Agent tool, not subprocess) | — |
| 6 | PERFORMANCE | perf, adversarial-performance | **Agent** + CLI (dispatch via Agent tool, not subprocess) | — |
| 7 | OPERATIONAL | verify (hook chain), hook-audit, hook-inventory, recursive_failure_detector | Python/CLI | — |
| META | META-SYNTHESIS | consensus detection, blind-spot detection, evidence quality | Python | All |

### Execution Model

**The LLM is the conductor.** SKILL.md is the score — I execute the workflow by:

1. **Validate target** via `_validate_target()` utility
2. **Dispatch Agent-based layers** via Agent tool (file-based handoff, not inline findings):
   - L0 (PREDICTIVE): Dispatch 7 specialists in parallel via Agent tool (run_in_background=True), each writing JSON to session file. After all complete, dispatch `adversarial-critic` for synthesis.
   - L5 (SECURITY): Dispatch `Agent('adversarial-security')` with file output; run path traversal check via Python utility
   - L6 (PERFORMANCE): Dispatch `Agent('adversarial-performance')` with file output; run perf checks via Python utility
3. **Run Python/CLI layers** via Bash subprocess:
   - L1 (SYNTACTIC): `ruff check`, `mypy`
   - L2 (SEMANTIC): `verify` (pytest), `diagnose`
   - L3 (STRUCTURAL): `meta-review`, `harden`, `apply_safety_patterns`
   - L4 (REQUIREMENTS): `gto`, `spec-compliance` — SKIP if L2 had failures
   - L7 (OPERATIONAL): `hook-audit`, `hook-inventory`, `recursive_failure_detector`
4. **Synthesize META** — consensus detection, blind-spot detection, evidence quality

**Orchestrator.py** is a **pure utilities module** — it provides `_validate_target`, `_atomic_write`, `L2State`, `SQAReport`, `save_report`. It contains **no orchestration logic**. Do not run `orchestrator.py` directly.

## Your Workflow

When /sqa is invoked:

### Step 0: Validate Target
Run `_validate_target()` utility to ensure path exists, is not symlink, within allowed roots.
Initialize state: `from sqa_state_tracker import init_state; state = init_state(target, halt_on="HIGH")`

### Step 1: PREDICTIVE (Optional - skip for fast-path)

**Phase 1a: Parallel specialist dispatch via Task tool**

Create session directory and dispatch manifest, then launch 7 specialists in parallel via `Task` tool:

```python
import uuid, json
from pathlib import Path

session_id = uuid.uuid4().hex[:8]
sqa_dir = Path(f"P:/.claude/.evidence/sqa/{session_id}")
sqa_dir.mkdir(parents=True, exist_ok=True)
(sqa_dir / "specialists").mkdir(exist_ok=True)

# Dispatch manifest (idempotent — re-run skips already-dispatched specialists)
manifest_path = sqa_dir / "specialists" / "dispatch_manifest.json"

specialists = [
    "adversarial-logic",
    "adversarial-quality",
    "adversarial-io-validation",
    "adversarial-security",
    "adversarial-performance",
    "adversarial-testing",
    "adversarial-state-machine",
]

# Load prior dispatched from any interrupted run
dispatched = []
if manifest_path.exists():
    dispatched = json.loads(manifest_path.read_text()).get("dispatched", [])

# Dispatch specialists in parallel (sequential calls = concurrent execution)
for specialist in specialists:
    if specialist not in dispatched:
        Task(
            subagent_type="general-purpose",
            description=f"L0 {specialist} analysis",
            prompt=f"Read P:/.claude/agents/{specialist}.md and follow its instructions to review <target>. Write JSON findings to: {sqa_dir}/specialists/{specialist}-findings.json. Return ONLY the file path."
        )
        dispatched.append(specialist)
        manifest_path.write_text(json.dumps({"dispatched": dispatched, "session_id": session_id}))
```

**Each specialist:**
- Reads its agent definition from `P:/.claude/agents/{specialist}.md`
- Writes JSON findings to `{sqa_dir}/specialists/{specialist}-findings.json`
- Returns ONLY the file path (not inline findings)

**Phase 1b: Idempotent completion check**

After launching all specialists, check for JSON availability:

```python
available = []
for specialist in dispatched:
    json_path = sqa_dir / "specialists" / f"{specialist}-findings.json"
    if json_path.exists():
        try:
            json.loads(json_path.read_text())
            available.append(specialist)
        except (json.JSONDecodeError, OSError):
            pass  # Incomplete file, will re-dispatch on re-run

if len(available) == len(dispatched) and available:
    print("All specialist JSONs available — proceeding to synthesis.")
else:
    print(f"Partial: {available}. Re-run /sqa to continue — manifest skips dispatched agents.")
```

**Phase 1c: Failure-mode prompts (internal)**

Before synthesizing, run this internal check against the specialist findings:

```
Internal failure-mode check:
- What is the most plausible way this target still fails even if the happy path passes?
- What am I treating as safe because the producer succeeds, even though the consumer could still fail?
- What hidden assumption would most likely break under stale data, workflow interruption, or multi-terminal use?
- What blind spot is shared across multiple specialists rather than isolated to one agent?
- What risk am I underweighting because it is operational, temporal, or only appears on resume/handoff?
```

**Phase 1d: Explicit completion gate**

Verify ALL specialist JSONs exist and are valid before proceeding:
```python
import json
from pathlib import Path

missing = []
for specialist in dispatched:
    json_path = sqa_dir / "specialists" / f"{specialist}-findings.json"
    if not json_path.exists():
        missing.append(specialist)
        continue
    try:
        json.loads(json_path.read_text())
    except (json.JSONDecodeError, OSError):
        missing.append(specialist)

if missing:
    print(f"[GATE FAILED] Missing or invalid: {missing}")
    print("Re-run /sqa — manifest skips already-dispatched agents.")
    sys.exit(1)
print("[GATE PASSED] All specialist JSONs available — proceeding to synthesis.")
```

**Phase 1e: Critic synthesis**

After all specialist JSONs are available, dispatch `adversarial-critic` to synthesize:

```python
Agent('adversarial-critic', prompt=f"Read all 7 specialist JSONs in {sqa_dir}/specialists/. Synthesize into a unified L0 findings list: dedupe by (file, line, category), resolve severity conflicts, detect consensus (2+ specialists agree). Write synthesis to {sqa_dir}/L0_synthesis.json.")
```

**Phase 1f: Record L0 completion**

Count findings from `L0_synthesis.json` and record:
```python
from sqa_state_tracker import record_layer_complete
synthesis = json.loads((sqa_dir / "L0_synthesis.json").read_text())
record_layer_complete("L0", findings=len(synthesis.get("findings", [])))
```

If fast-path: `record_layer_complete("L0", skipped=True, reason="fast-path")`

### [HALT CHECK] After Step 1
If any findings at or above `--halt-on` threshold (default: HIGH): EMIT `[HALT]`, run `record_halt("L0")`, and stop. Otherwise continue.

### Step 2: SYNTACTIC
Run via Bash subprocess:
- `ruff check <target>`
- `mypy <target>` (if Python)

**Exit validation:** Verify exit codes are 0. If not, this is a FAIL even if findings are below halt threshold.

Record completion: `record_layer_complete("L1", findings=N)`

### [HALT CHECK] After Step 2
If findings at or above `--halt-on` threshold (default: HIGH):
1. EMIT `[HALT] Layer L1 completed with X finding(s) exceeding --halt-on threshold`
2. If `--fix`: attempt Layer 1 fixes (ruff --fix), retry up to 3 times
3. If still failing: **BLOCKED** — must use `/sqa --halt-on NONE` to override
4. If no `--fix`: **BLOCKED** — must use `/sqa --fix` or `/sqa --halt-on NONE`

### Step 3: SEMANTIC
Run via Bash subprocess:
- `verify <target>` (pytest)
- `diagnose` (if failures detected)

Record completion: `record_layer_complete("L2", findings=N)`

### [HALT CHECK] After Step 3
If any findings at or above `--halt-on` threshold (default: HIGH): EMIT `[HALT]`, run `record_halt("L2")`, and stop. Otherwise continue.

### Step 4: STRUCTURAL
Run via Bash subprocess:
- `meta-review --analyze=imports <target>` (circular deps)
- `harden --check=guards <target>` (assertion guards)
- `apply_safety_patterns --verify <target>` (safety patterns)

Record completion: `record_layer_complete("L3", findings=N)`

### [HALT CHECK] After Step 4
If any findings at or above `--halt-on` threshold (default: HIGH): EMIT `[HALT]`, run `record_halt("L3")`, and stop. Otherwise continue.

### Step 5: REQUIREMENTS (skip if L2 had failures)
Run via Bash subprocess:
- `gto <target>`
- `spec-compliance <target>`

Record completion: `record_layer_complete("L4", findings=N)` (or `skipped=True, reason="L2 had failures"` if skipped)

### [HALT CHECK] After Step 5
If any findings at or above `--halt-on` threshold (default: HIGH): EMIT `[HALT]`, run `record_halt("L4")`, and stop. Otherwise continue.

### Step 6: SECURITY
1. Dispatch `Agent('adversarial-security')` via Agent tool
2. Run path traversal check via Python utility
3. Run `data-safety-vcs` for anti-bleed gates

Record completion: `record_layer_complete("L5", findings=N)`

### [HALT CHECK] After Step 6
If any findings at or above `--halt-on` threshold (default: HIGH): EMIT `[HALT]`, run `record_halt("L5")`, and stop. Otherwise continue.

### Step 7: PERFORMANCE
1. Dispatch `Agent('adversarial-performance')` via Agent tool
2. Run `perf` for ThreadPoolExecutor tracing

Record completion: `record_layer_complete("L6", findings=N)`

### [HALT CHECK] After Step 7
If any findings at or above `--halt-on` threshold (default: HIGH): EMIT `[HALT]`, run `record_halt("L6")`, and stop. Otherwise continue.

### Step 8: OPERATIONAL
Run via Bash subprocess:
- `verify --tier=2 <target>` (hook chain + router)
- `hook-audit <target>`
- `hook-inventory <target>`
- `recursive_failure_detector.py <target>`

Record completion: `record_layer_complete("L7", findings=N)`

### [HALT CHECK] After Step 8
If any findings at or above `--halt-on` threshold (default: HIGH): EMIT `[HALT]`, run `record_halt("L7")`, and stop. Otherwise continue.

### Step 9: META-SYNTHESIS
- Consensus detection (2+ layers agree on same file:line:category)
- Blind-spot detection
- Evidence quality check per `evidence-tiers`

Record completion: `record_layer_complete("META", findings=N)`

### Step 10: P6 SECURITY CERTIFICATION
Run explicit security certification gate:

**Security Certification Checklist:**
- [ ] L5 adversarial-security findings: NONE at CRITICAL/HIGH
- [ ] Path traversal check: PASS
- [ ] Anti-bleed gates: VERIFIED
- [ ] Data safety VCS: CLEAN

```python
security_check_pass = (
    l5_critical_high_count == 0 and
    path_traversal_check_passed and
    anti_bleed_gates_verified
)
if not security_check_pass:
    print("[P6 SECURITY CERTIFICATION FAILED]")
    print("Blocking certification until security issues resolved.")
    sys.exit(1)
print("[P6 SECURITY CERTIFICATION PASSED]")
```

### Step 11: P5 QUALITY CERTIFICATION
Issue final quality certification based on health score:

**Certification Thresholds:**
| Health Score | Certification |
|--------------|---------------|
| ≥80 | **CERTIFIED** — Excellent quality |
| 60-79 | **CONDITIONAL** — Address HIGH items |
| 40-59 | **UNSTABLE** — Major issues must be fixed |
| <40 | **REJECTED** — Unsafe for production use |

```python
if health_score >= 80:
    cert = "CERTIFIED"
elif health_score >= 60:
    cert = "CONDITIONAL"
elif health_score >= 40:
    cert = "UNSTABLE"
else:
    cert = "REJECTED"

print(f"[P5 QUALITY CERTIFICATION: {cert}]")
print(f"Health Score: {health_score}")
print(f"Layers Completed: {layers_completed}")

# Final verdict
if cert == "CERTIFIED":
    print("Package is production-ready.")
elif cert == "CONDITIONAL":
    print("Package is usable with known limitations.")
else:
    print("Package requires fixes before use.")
    sys.exit(1)
```

### FINAL [HALT CHECK] After Step 11
Report final certification status and layers completed.

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
health_score = max(-100, 100 - Σ(severity_weight × evidence_tier_factor))
```

Where:
- **Severity weights**: CRITICAL=20, HIGH=10, MEDIUM=5, LOW=2
- **Evidence tier factors**: T1=1.0x, T2=0.75x, T3=0.5x, T4=0.25x
- **Deduplication key**: (file, line, category, title) — keeping highest severity per key before scoring

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

## Exit Criteria Validation (Step 4.5 Pattern)

After EVERY layer, run actual verification commands BEFORE trusting self-reported results. This prevents layers from incorrectly reporting PASS when they actually failed.

| Layer | What to Validate |
|-------|------------------|
| L0 | All 7 specialist JSONs exist and parse |
| L1 | ruff/mypy exit codes are 0 |
| L2 | pytest exit code is 0 |
| L3 | All 3 tools (meta-review, harden, apply_safety_patterns) exit 0 |
| L4 | gto, spec-compliance exit 0 |
| L5 | adversarial-security JSON + path traversal check |
| L6 | adversarial-performance JSON + perf output |
| L7 | verify --tier=2, hook-audit, hook-inventory all pass |

**Validation command pattern:**
```python
import subprocess
result = subprocess.run(cmd, shell=True, capture_output=True)
if result.returncode != 0:
    print(f"[EXIT VALIDATION FAILED] {layer}: {cmd}")
    print(f"stdout: {result.stdout.decode()[:500]}")
    print(f"stderr: {result.stderr.decode()[:500]}")
    # HALT - do not proceed
```

**Bypass:** If layer was run with `--dry-run`, skip validation.

## Halt-on-Impact

Severity-based layer halting stops execution after a layer when findings at or above the threshold make continuing pointless.

**How it works:**
- After each layer completes, the conductor checks: "do raw (non-deduplicated) findings at or above `--halt-on` threshold make continuing pointless?"
- **HIGH** (default): Halt on any HIGH or CRITICAL findings
- **CRITICAL**: Halt only on CRITICAL findings
- **MEDIUM**: Halt on MEDIUM, HIGH, or CRITICAL
- **NONE**: Run all layers — collect all findings regardless

**Key distinction from health score:**
- Health score uses **deduplicated** counts (D4 consensus removes duplicates before scoring)
- Halt-on-impact uses **raw** counts (any CRITICAL/HIGH finding triggers halt, even if another layer also found it)

**Halt behavior (enforcement: strict):**
1. Surface all findings from current layer with file:line locations
2. Emit `[HALT] Layer N completed with X finding(s) exceeding --halt-on threshold`
3. Report health score based on deduplicated counts
4. **BLOCKED** — cannot proceed past this layer without explicit override
5. Override only with: `/sqa --halt-on NONE` (proceed with risk) or `/sqa --fix` (attempt auto-fix)

**--fix auto-fix loop (opt-in):**
When `/sqa --fix` halts, attempt Layer 1/2/3 fixes before retry:

| Layer | Confidence | Fix Type | Examples |
|-------|------------|----------|---------|
| Layer 1 | HIGH | Imports, style, formatting | `ruff check --fix`, `autoflake`, `pyupgrade` |
| Layer 2 | MEDIUM | LLM with findings + context | Generate fix patches, apply safest first |
| Layer 3 | LOW | Final LLM attempt | Architectural refactor recommendations |

**Fix loop:**
```
if --fix and halt_triggered:
    for attempt in range(1, 4):
        print(f"[FIX ATTEMPT {attempt}/3]")
        Layer_1_fixes()  # ruff --fix, etc.
        re-run layer
        if passes: break
        Layer_2_fixes()  # LLM with context
        re-run layer
        if passes: break
        Layer_3_fixes()  # Final LLM attempt
        re-run layer
        if passes: break
    if still failing:
        print("[FIX FAILED] Manual intervention required")
        print("Run `/sqa --halt-on NONE` to proceed anyway")
        sys.exit(1)
```

**When halting is NOT triggered:**
- `--halt-on HIGH`: MEDIUM and LOW findings alone do not halt
- L4 (REQUIREMENTS) still skips if L2 had pytest failures (hard dependency, no flag override)
- L7 findings at any severity do not halt (OPERATIONAL is the final actionable layer)

If a layer's tool is unavailable and it is NOT a hard dependency for a subsequent layer, skip with warning and continue.

## Graceful Degradation

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

**Two-Sided Enforcement Principle:**

Both write-time (producer) AND consume-time (consumer) validation are required for durable correctness:
- **Write-time without consume-time**: Stale artifacts survive contract changes. A hook validated at creation time may still be consumed after the contract drifted.
- **Consume-time without write-time**: Bad artifacts accumulate upstream. Consumers keep rejecting the same malformed inputs that were never caught at the source.

Layer 7 must verify that **both** sides exist at every critical boundary — not only that the producer ran successfully.

**Implementation note:** The verification check for both-sided enforcement is not yet implemented in the SQA orchestrator. Until then, flag "one-sided enforcement at boundary {name}" as a HIGH finding in Layer 7 reviews.

### Meta-Synthesis
Consensus detection (2+ layers agree on same file:line:category).
Blind-spot detection (no coverage for a quality category when layer WAS available but found nothing — NOT when layer was skipped via D5).
Evidence quality check per `evidence-tiers`.
Flag when a packet exists but is ignored, when prose and packet disagree, or when a packet is too underspecified to certify.

## Auto-Fix Mode

**`--fix`**: Auto-fix safe issues in L1/L2:
- Formatting (`ruff format`)
- Unused imports (`ruff --fix`)
- Lint violations (`ruff --fix`)

**Excluded from auto-fix**: logic errors, security issues, type mismatches, architectural changes.

**`--fix-all`** (iterative fix loop):
```
WHILE MEDIUM+ findings exist (max 5 iterations):
  1. /sqa runs detection (layers)
  2. /sqa parses findings by severity
  3. IF MEDIUM+ findings exist:
     - /sqa invokes /code with SPECIFIC issues to fix
     - /code fixes ONLY those specific issues
     - Record fixes applied
  4. ELSE: EXIT LOOP — quality threshold met
  5. SAFETY: Max 5 iterations
```

**Convergence criteria**: 0 CRITICAL, 0 HIGH, 0 MEDIUM findings (LOW ignored).

**Division of labor**: `/sqa` does detection; `/code` does fixing.

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
