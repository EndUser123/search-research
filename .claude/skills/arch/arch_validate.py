#!/usr/bin/env python3
"""Validate contract-sensitive ADRs produced by /arch.

This keeps the authoritative Contract Authority Packet honest by validating the
packet shape, required boundary fields, and a small set of cross-skill contract
alignment rules that must not drift.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# DEPTH RULE: When skills/ layer is added, increment parents[N] by 1.
# e.g. from arch/: parents[3]→[4] (sdlc/ is 4 levels up from arch/)
_ROOT = Path(__file__).resolve()
_CONTRACT_PRIMITIVES_SRC = _ROOT.parents[4] / "contract-primitives" / "src"
if str(_CONTRACT_PRIMITIVES_SRC) not in sys.path:
    sys.path.insert(0, str(_CONTRACT_PRIMITIVES_SRC))

from contract_primitives import (  # noqa: E402
    ACTIVE_PLAN_ARTIFACT_FAILURE_BEHAVIOR,
    REQUIRED_BOUNDARY_FIELDS,
    parse_contract_authority_packet,
)


def validate_adr(path: str) -> dict[str, object]:
    adr_path = Path(path)
    if not adr_path.exists():
        return {
            "status": "BLOCKED",
            "findings": [
                {
                    "id": "ADR-001",
                    "priority": "HIGH",
                    "title": f"ADR file not found: {path}",
                }
            ],
        }

    text = adr_path.read_text(encoding="utf-8")
    packet = parse_contract_authority_packet(text)
    findings: list[dict[str, object]] = []

    if not packet.boundaries:
        findings.append(
            {
                "id": "ADR-002",
                "priority": "HIGH",
                "title": "Missing Contract Authority Packet boundaries",
                "description": "Contract-sensitive ADRs must emit a parseable contract_authority_packet.",
            }
        )
    for boundary_id, boundary in packet.boundaries.items():
        missing = []
        for field_name in REQUIRED_BOUNDARY_FIELDS:
            if field_name == "schema.id" and not boundary.schema_id:
                missing.append(field_name)
            elif field_name == "schema.version" and not boundary.schema_version:
                missing.append(field_name)
            elif field_name == "required_fields" and not boundary.required_fields:
                missing.append(field_name)
            elif field_name == "producer" and not boundary.producer:
                missing.append(field_name)
            elif field_name == "consumer" and not boundary.consumer:
                missing.append(field_name)
            elif field_name == "freshness_authority" and not boundary.freshness_authority:
                missing.append(field_name)
            elif field_name == "invalidation_trigger" and not boundary.invalidation_trigger:
                missing.append(field_name)
            elif field_name == "precedence_rule" and not boundary.precedence_rule:
                missing.append(field_name)
            elif field_name == "failure_behavior" and not boundary.failure_behavior:
                missing.append(field_name)
            elif field_name == "validator_owner" and not boundary.validator_owner:
                missing.append(field_name)
            elif field_name == "proof_owner" and not boundary.proof_owner:
                missing.append(field_name)

        if missing:
            findings.append(
                {
                    "id": f"ADR-{boundary_id}-MISSING",
                    "priority": "HIGH",
                    "title": f"Boundary '{boundary_id}' is missing required contract fields",
                    "description": ", ".join(missing),
                }
            )

        if "not yet specified" in boundary.validator_owner.lower():
            findings.append(
                {
                    "id": f"ADR-{boundary_id}-VALIDATOR",
                    "priority": "HIGH",
                    "title": f"Boundary '{boundary_id}' leaves validator ownership unresolved",
                    "description": "validator_owner cannot remain 'not yet specified' in a closed packet.",
                }
            )

        if boundary_id == "plan-artifact":
            behavior = boundary.failure_behavior.lower()
            if "/planning" not in behavior or "blocking" not in behavior:
                findings.append(
                    {
                        "id": "ADR-PLAN-001",
                        "priority": "HIGH",
                        "title": "plan-artifact boundary drifts from active /planning contract",
                        "description": (
                            "The packet must reflect the active planning contract, which blocks "
                            "before implementation-ready when packet consumption is missing or contradicted."
                        ),
                        "expected_failure_behavior": ACTIVE_PLAN_ARTIFACT_FAILURE_BEHAVIOR,
                        "actual_failure_behavior": boundary.failure_behavior,
                    }
                )

    return {
        "status": "READY" if not findings else "BLOCKED",
        "packet_version": packet.packet_version,
        "boundary_count": len(packet.boundaries),
        "findings": findings,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(json.dumps({"status": "BLOCKED", "error": "usage: arch_validate.py <adr_path>"}))
        return 2
    result = validate_adr(argv[1])
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
