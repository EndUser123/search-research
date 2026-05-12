"""
Runtime claim types and artifact-layer mapping.

Distinguishes runtime/mechanism claims from generic FACTUAL/CAUSAL claims.
Each runtime claim type maps to an authoritative artifact source and a
verification strategy.

Layer map:
  STOP_GATE_FIRING    → Stop gate telemetry  (stop_gate_telemetry.jsonl)
  UPS_HOOK_CO_FIRE    → UPS execution trace   (ups_execution_trace.jsonl)
  AGE_GUARD_RUNTIME   → Worker/benchmark logs (worker logs / age guard logs)
  BENCHMARK_RUN_EVENT → Worker/benchmark logs (benchmark summary / events)

Verification rules (deterministic, no LLM):
  - artifact_missing     → block/warn (depends on gate policy) with exact message
  - artifact_present_no_match → block/warn with layer-specific message
  - artifact_present_match → allow (or warn-only if other issues)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# === Runtime claim type enum ===

class RuntimeClaimType(Enum):
    """Runtime claim subclasses that require specific artifact verification."""
    STOP_GATE_FIRING = "stop_gate_firing"       # "<gate> fired/blocked/warned N times"
    UPS_HOOK_CO_FIRE = "ups_hook_co_fire"       # "hooks X and Y co-fired"
    AGE_GUARD_RUNTIME = "age_guard_runtime"    # "age guard fired/blocked this run"
    BENCHMARK_RUN_EVENT = "benchmark_run_event" # "rotation happened", "checkpoint resumed"
    UNKNOWN = "unknown"


# === Artifact source configuration ===

class ArtifactSource(Enum):
    """Authoritative artifact layers for runtime claims."""
    STOP_TELEMETRY = "stop_telemetry"   # .state/stop_gate_telemetry.jsonl
    UPS_TRACE = "ups_trace"              # logs/diagnostics/ups_execution_trace.jsonl
    WORKER_LOG = "worker_log"           # worker / benchmark log files
    BENCHMARK_SUMMARY = "benchmark_summary"  # benchmark summary artifact
    NONE = "none"                        # No artifact required / generic


@dataclass(frozen=True)
class RuntimeClaimConfig:
    """Single-source definition for a runtime claim type."""
    claim_type: RuntimeClaimType
    artifact_source: ArtifactSource
    evidence_check: str  # Human-readable description of how to verify
    log_glob_pattern: str | None = None  # Glob pattern for log file discovery
    required_event_fields: tuple[str, ...] = ()  # Fields that must be present for match


@dataclass(frozen=True)
class ArtifactLookupResult:
    """Result of looking up an artifact source."""
    found: bool
    artifact_source: ArtifactSource
    log_path: Path | None = None
    records: list[dict[str, Any]] | None = None
    error: str | None = None  # If found=False with error, describe it


# === Claim → Artifact layer map ===

_RUNTIME_CLAIM_MAP: dict[RuntimeClaimType, RuntimeClaimConfig] = {
    RuntimeClaimType.STOP_GATE_FIRING: RuntimeClaimConfig(
        claim_type=RuntimeClaimType.STOP_GATE_FIRING,
        artifact_source=ArtifactSource.STOP_TELEMETRY,
        evidence_check='grep for gate name with decision=block/warn/allow in stop_gate_telemetry.jsonl',
        log_glob_pattern="**/stop_gate_telemetry.jsonl",
        required_event_fields=("gate", "decision"),
    ),
    RuntimeClaimType.UPS_HOOK_CO_FIRE: RuntimeClaimConfig(
        claim_type=RuntimeClaimType.UPS_HOOK_CO_FIRE,
        artifact_source=ArtifactSource.UPS_TRACE,
        evidence_check="search for both hook names with same turn_id or event_id in ups_execution_trace.jsonl",
        log_glob_pattern="**/ups_execution_trace.jsonl",
        required_event_fields=("hook_name", "turn_id"),
    ),
    RuntimeClaimType.AGE_GUARD_RUNTIME: RuntimeClaimConfig(
        claim_type=RuntimeClaimType.AGE_GUARD_RUNTIME,
        artifact_source=ArtifactSource.WORKER_LOG,
        evidence_check="search for 'age_guard' with decision=block/allow in worker/age logs",
        log_glob_pattern="**/age_guard*.jsonl",
        required_event_fields=("guard_name", "decision"),
    ),
    RuntimeClaimType.BENCHMARK_RUN_EVENT: RuntimeClaimConfig(
        claim_type=RuntimeClaimType.BENCHMARK_RUN_EVENT,
        artifact_source=ArtifactSource.BENCHMARK_SUMMARY,
        evidence_check="search for rotation/resume checkpoint event in benchmark summary or worker logs",
        log_glob_pattern="**/benchmark*.jsonl",
        required_event_fields=("event_type",),
    ),
}


# === Runtime claim detection from text ===

# Patterns that trigger runtime claim classification
_RUNTIME_CLAIM_PATTERNS: dict[RuntimeClaimType, list[re.Pattern[str]]] = {
    RuntimeClaimType.STOP_GATE_FIRING: [
        re.compile(r"\b(\w+_gate|\w+_guard|\w+_contract|\w+_validator)\s+(?:fired|blocked|warned|triggered|skipped)\b", re.IGNORECASE),
        re.compile(r"\b(epistemic_contract|safety_gate|unverified_stance|lazy_workaround)\s+(?:fired|blocked|warned)\b", re.IGNORECASE),
        re.compile(r"\bthe\s+(\w+)\s+gate\s+(?:fired|blocked|warned)\b", re.IGNORECASE),
    ],
    RuntimeClaimType.UPS_HOOK_CO_FIRE: [
        re.compile(r"\b(\w+)\s+and\s+(\w+)\s+(?:co-?fire|co-?ran|run\s+together)\b", re.IGNORECASE),
        re.compile(r"\boperatingrules\s+and\s+behaviorcontract\s+(?:co-?fire|run\s+together)\b", re.IGNORECASE),
        re.compile(r"\bhooks?\s+(\w+)\s+(?:and|with)\s+(\w+)\s+(?:co-?fire|ran\s+together)\b", re.IGNORECASE),
    ],
    RuntimeClaimType.AGE_GUARD_RUNTIME: [
        re.compile(r"\b(age\s+guard|age_guard)\s+(?:fired|blocked|triggered)\b", re.IGNORECASE),
        re.compile(r"\bthe\s+age\s+guard\s+(?:fired|blocked)\b", re.IGNORECASE),
    ],
    RuntimeClaimType.BENCHMARK_RUN_EVENT: [
        re.compile(r"\b(rotation|rotated)\s+(?:happened|occurred)\b", re.IGNORECASE),
        re.compile(r"\b(checkpoint|resume)\s+(?:resumed|fired)\b", re.IGNORECASE),
        re.compile(r"\bbenchmark\s+(?:rotation|checkpoint)\s+(?:happened|resumed)\b", re.IGNORECASE),
    ],
}


def classify_runtime_claim(response: str) -> list[RuntimeClaimType]:
    """Detect runtime claim types in response text. Returns list (may have multiple)."""
    if not response:
        return []
    found: list[RuntimeClaimType] = []
    for claim_type, patterns in _RUNTIME_CLAIM_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(response):
                if claim_type not in found:
                    found.append(claim_type)
    return found


# === Artifact lookup ===

def _find_log_file(root: Path, pattern: str) -> Path | None:
    """Find first log file matching glob pattern, relative to root."""
    try:
        matches = list(root.glob(pattern))
        if matches:
            return matches[0]
    except (OSError, ValueError):
        pass
    return None


def lookup_artifact(
    claim_type: RuntimeClaimType,
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> ArtifactLookupResult:
    """Locate the relevant log file(s) for a runtime claim type.

    Args:
        claim_type: The type of runtime claim being verified.
        session_id: Session context (used for path scoping).
        terminal_id: Terminal context (used for path scoping).

    Returns:
        ArtifactLookupResult with found status, log_path, records, and error.
    """
    config = _RUNTIME_CLAIM_MAP.get(claim_type)
    if not config:
        return ArtifactLookupResult(
            found=False,
            artifact_source=ArtifactSource.NONE,
            error=f"Unknown runtime claim type: {claim_type.value}",
        )

    # Determine search root — prefer session-scoped paths
    if session_id or terminal_id:
        # Look in .state/ scoped by session/terminal
        base = Path.cwd() / ".state"
    else:
        base = Path.cwd()

    # Build search paths based on artifact source
    search_paths: list[tuple[str, Path]] = []

    if config.artifact_source == ArtifactSource.STOP_TELEMETRY:
        for pattern in ("stop_gate_telemetry.jsonl", "**/stop_gate_telemetry.jsonl"):
            p = _find_log_file(base, pattern)
            if p:
                search_paths.append(("stop_telemetry", p))
                break

    elif config.artifact_source == ArtifactSource.UPS_TRACE:
        for pattern in ("logs/diagnostics/ups_execution_trace.jsonl",
                        "**/ups_execution_trace.jsonl"):
            p = _find_log_file(base, pattern)
            if p:
                search_paths.append(("ups_trace", p))
                break

    elif config.artifact_source in (ArtifactSource.WORKER_LOG, ArtifactSource.BENCHMARK_SUMMARY):
        for pattern in ("**/age_guard*.jsonl", "**/benchmark*.jsonl", "**/worker*.jsonl"):
            p = _find_log_file(base, pattern)
            if p:
                search_paths.append((config.artifact_source.value, p))
                break

    if not search_paths:
        return ArtifactLookupResult(
            found=False,
            artifact_source=config.artifact_source,
            error=f"No log file found for {config.artifact_source.value} "
                  f"(pattern: {config.log_glob_pattern})",
        )

    # Read records from found path
    source_name, log_path = search_paths[0]
    try:
        records: list[dict[str, Any]] = []
        with open(log_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return ArtifactLookupResult(
            found=True,
            artifact_source=config.artifact_source,
            log_path=log_path,
            records=records,
        )
    except (OSError, UnicodeDecodeError) as e:
        return ArtifactLookupResult(
            found=False,
            artifact_source=config.artifact_source,
            error=f"Could not read {log_path}: {e}",
        )


def verify_runtime_claim(
    claim_type: RuntimeClaimType,
    response: str,
    session_id: str | None = None,
    terminal_id: str | None = None,
) -> tuple[bool, str]:
    """Verify a runtime claim against artifact source.

    Returns (verified, message):
      verified=True: artifact found and claim matches
      verified=False: message explains why (missing/incorrect/matched)

    Args:
        claim_type: Type of runtime claim to verify.
        response: Full response text containing the claim.
        session_id: Session context.
        terminal_id: Terminal context.

    Returns:
        Tuple of (claim_verified, explanation_message).
    """
    result = lookup_artifact(claim_type, session_id, terminal_id)

    if not result.found:
        return False, (
            f"RUNTIME CLAIM VERIFICATION FAILED: "
            f"Required artifact source '{result.artifact_source.value}' was not found. "
            f"Cannot verify {claim_type.value} claim. "
            + (f"Error: {result.error}" if result.error else "")
        )

    if not result.records:
        return False, (
            f"RUNTIME CLAIM VERIFICATION FAILED: "
            f"Artifact '{result.artifact_source.value}' found at {result.log_path} "
            f"but contains no records. Cannot verify {claim_type.value} claim."
        )

    # Check for matching events based on claim type
    config = _RUNTIME_CLAIM_MAP[claim_type]
    matched = False

    for record in result.records:
        # Check required fields
        if not all(f in record for f in config.required_event_fields):
            continue

        # Claim-specific matching
        if claim_type == RuntimeClaimType.STOP_GATE_FIRING:
            gate_name = record.get("gate", "")
            # Check if any gate name from response appears in telemetry
            import re as _re
            gate_patterns = [
                r"\b(\w+_gate|\w+_guard|\w+_contract|\w+_validator)\b",
                r"\b(epistemic_contract|safety_gate|unverified_stance|lazy_workaround)\b",
            ]
            for pat in gate_patterns:
                for m in _re.finditer(pat, response, _re.IGNORECASE):
                    found_gate = m.group(1).lower()
                    if found_gate in gate_name.lower() or gate_name.lower() in found_gate:
                        matched = True
                        break
            if matched:
                break

        elif claim_type == RuntimeClaimType.UPS_HOOK_CO_FIRE:
            # Check for co-firing: same turn_id with multiple hooks
            hook_names = [record.get("hook_name", "")]
            turn_id = record.get("turn_id", "")
            # Look for other records with same turn_id
            for other in result.records:
                if other.get("turn_id") == turn_id and other.get("hook_name") != hook_names[0]:
                    matched = True
                    break
            if matched:
                break

        elif claim_type == RuntimeClaimType.AGE_GUARD_RUNTIME:
            guard_name = record.get("guard_name", "")
            if "age_guard" in guard_name.lower() or "age" in guard_name.lower():
                matched = True
                break

        elif claim_type == RuntimeClaimType.BENCHMARK_RUN_EVENT:
            event_type = record.get("event_type", "")
            if any(kw in event_type.lower() for kw in ("rotation", "checkpoint", "resume")):
                matched = True
                break

    if not matched:
        return False, (
            f"RUNTIME CLAIM VERIFICATION FAILED: "
            f"Artifact '{result.artifact_source.value}' at {result.log_path} "
            f"contains {len(result.records)} records but none match {claim_type.value}. "
            f"Claim cannot be verified against this artifact layer."
        )

    return True, f"Verified: {claim_type.value} claim confirmed via {result.artifact_source.value} at {result.log_path}"


# === Self-test ===

if __name__ == "__main__":
    # Test runtime claim detection
    test_cases = [
        ("The epistemic_contract gate fired three times.", [RuntimeClaimType.STOP_GATE_FIRING]),
        ("operatingrules and behaviorcontract co-fire in this turn.", [RuntimeClaimType.UPS_HOOK_CO_FIRE]),
        ("The age guard fired and blocked the request.", [RuntimeClaimType.AGE_GUARD_RUNTIME]),
        ("A rotation happened mid-benchmark.", [RuntimeClaimType.BENCHMARK_RUN_EVENT]),
        ("The root cause is that the import is missing.", []),  # causal, not runtime
        ("Yes, the fix is in place.", []),  # simple answer, not runtime
    ]

    print("Runtime claim detection tests:")
    failed = 0
    for text, expected in test_cases:
        actual = classify_runtime_claim(text)
        status = "PASS" if actual == expected else "FAIL"
        if status == "FAIL":
            failed += 1
        print(f"  [{status}] {text[:60]!r}")
        print(f"         expected={[e.value for e in expected]}, got={[e.value for e in actual]}")
    print(f"\n{len(test_cases) - failed}/{len(test_cases)} passed")