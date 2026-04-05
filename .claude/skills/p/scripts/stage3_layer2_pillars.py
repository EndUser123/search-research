#!/usr/bin/env python3
"""
Stage 3 Layer 2: Architectural Pillar Enforcer + Constitutional Filter

Filters findings against:
1. Architectural pillars (CSF)
2. Solo-dev constitutional constraints (enterprise bloat detection)

Usage:
    python stage3_layer2_pillars.py <findings.json>

Output:
    Writes to P:/.claude/state/layer2-{terminal}-{timestamp}.json
    Prints output file path to stdout for chaining
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

STATE_DIR = Path("P:/.claude/state")

# Constitutional patterns from /refactor (bloat_guard_extended.py)
CONSTITUTIONAL_PATTERNS = [
    (r'\b(?:daemon|background\s+(?:service|process|worker))\b', 'background_service'),
    (r'\b(?:continuous|real-?time)\s+monitoring\b', 'continuous_monitoring'),
    (r'\babstract\s+factory\b', 'abstract_factory'),
    (r'\bdependency\s+injection\s+container\b', 'di_container'),
    (r'\bservice\s+mesh\b', 'service_mesh'),
    (r'\benterprise[_-]?grade\b', 'enterprise_grade'),
    (r'\b(?:service\s+)?(?:discovery|registry)\b', 'service_discovery'),
    (r'\bmicro(?:service)?s?\b', 'microservices'),
    (r'\b(?:circuit\s+breaker|bulkhead|retry\s+pattern)\b', 'enterprise_patterns'),
    (r'\b(?:event\s+(?:bus|broker|queue)|message\s+queue)\b', 'messaging_infrastructure'),
    (r'\b(?:read|write)\s+replica\b', 'database_replication'),
    (r'\bsharding\b', 'database_sharding'),
    (r'\b(?:api\s+)?gateway\b', 'api_gateway'),
]


def get_terminal_id() -> str:
    """Get terminal identifier for multi-terminal isolation."""
    for env_var in ['CLAUDE_TERMINAL_ID', 'WINDOWID', 'TERM_SESSION_ID', 'WT_SESSION']:
        value = os.environ.get(env_var)
        if value:
            return value[-8:] if len(value) > 8 else value
    return str(os.getppid())


def check_constitutional_compliance(finding: dict) -> tuple[bool, str | None]:
    """Check if a finding violates solo-dev constitutional constraints.

    Returns:
        (is_compliant, violation_reason)
        - True, None: Finding is compliant
        - False, reason: Finding violates constitutional constraint
    """
    # Extract text to check from finding
    text_to_check = ' '.join([
        str(finding.get('title', '')),
        str(finding.get('description', '')),
        str(finding.get('recommendation', ''))
    ]).lower()

    # Check each constitutional pattern
    for pattern, category in CONSTITUTIONAL_PATTERNS:
        if re.search(pattern, text_to_check, re.IGNORECASE):
            return False, f"Constitutional violation: {category} (solo-dev constraint)"

    return True, None


def write_state_file(layer: int, result: dict) -> Path:
    """Write result to state file with terminal isolation."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    terminal_id = get_terminal_id()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"layer{layer}-{terminal_id}-{timestamp}.json"
    output_path = STATE_DIR / filename
    result['_meta'] = {
        'terminal_id': terminal_id,
        'timestamp': timestamp,
        'output_file': str(output_path)
    }
    output_path.write_text(json.dumps(result, indent=2))
    return output_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('findings', help='Path to findings JSON file (output from layer 1)')
    args = parser.parse_args()

    # Load findings
    findings_path = Path(args.findings)
    if not findings_path.exists():
        print(json.dumps({'error': 'Findings file not found', 'filtered': []}))
        sys.exit(1)

    data = json.loads(findings_path.read_text())
    findings = data.get('filtered', data.get('findings', []))
    input_count = len(findings)

    # Try to import CSF module for architectural pillar filtering
    try:
        sys.path.insert(0, 'P:/__csf/src')
        from orchestration.architectural_pillar_enforcer import ArchitecturalPillarEnforcer, SubagentFeedback

        enforcer = ArchitecturalPillarEnforcer()
        feedback = SubagentFeedback(
            suggestions=findings,
            context_available=True
        )

        result_obj = enforcer.validate_subagent_feedback(feedback, data.get('changed_files', []))
        filtered = result_obj.validated_suggestions
        pillar_rejected = result_obj.rejected_suggestions

    except ImportError:
        # CSF not available - pass through all findings
        filtered = findings
        pillar_rejected = []
    except AttributeError:
        # Module exists but interface different
        filtered = findings
        pillar_rejected = []

    # Apply constitutional filtering (from /refactor SoloDevConstitutionalFilter)
    constitutionally_compliant = []
    constitutionally_rejected = []

    for finding in filtered:
        is_compliant, violation_reason = check_constitutional_compliance(finding)
        if is_compliant:
            constitutionally_compliant.append(finding)
        else:
            constitutionally_rejected.append({
                **finding,
                'rejection_reason': violation_reason,
                'filter_type': 'constitutional'
            })

    # Combine rejection reasons
    all_rejected = []
    all_rejected.extend(pillar_rejected)
    all_rejected.extend(constitutionally_rejected)

    result = {
        'layer': 2,
        'name': 'architectural_pillar_enforcer_plus_constitutional',
        'input_count': input_count,
        'output_count': len(constitutionally_compliant),
        'rejected_count': len(all_rejected),
        'pillar_filtered_count': len(pillar_rejected),
        'constitutional_filtered_count': len(constitutionally_rejected),
        'filtered': constitutionally_compliant,
        'rejected': all_rejected
    }

    # Write to state file and print path for chaining
    output_path = write_state_file(2, result)
    print(str(output_path))


if __name__ == '__main__':
    main()
