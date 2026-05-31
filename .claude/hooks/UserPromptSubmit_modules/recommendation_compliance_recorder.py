"""Stop-side shadow recorder for recommendation rubric compliance.

OBSERVE ONLY - this hook NEVER blocks and never returns a blocking decision.

Watches for recommendation-request prompts and logs non-compliant responses to
epistemic_telemetry.jsonl so compliance trends can be measured over time.

Fires at the end of the Stop gate pipeline, after all gates have returned.
Uses the same telemetry schema as _log_epistemic_telemetry for consistency.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent


def _run_recommendation_compliance_recorder(data: dict) -> None:
    """Observe-only recorder: log non-compliant recommendation responses.

    This is NOT a gate - it never returns a dict that could block or warn.
    It only appends a telemetry line to epistemic_telemetry.jsonl.
    """
    try:
        from recommendation_intent import is_recommendation_request, assess_compliance

        prompt = data.get('prompt', '') or ''
        response = data.get('response', '') or ''

        if not is_recommendation_request(prompt):
            return

        assessment = assess_compliance(response)
        if assessment['compliant']:
            return

        log_path = _HOOKS_DIR / 'logs' / 'diagnostics' / 'epistemic_telemetry.jsonl'
        log_path.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            'timestamp': time.time(),
            'gate': 'recommendation_compliance',
            'decision': 'non_compliant',
            'has_options': assessment['has_options'],
            'has_criterion': assessment['has_criterion'],
            'compliant': False,
            'session_id': data.get('session_id', ''),
            'terminal_id': data.get('terminal_id', ''),
            'response_length': len(response),
            'prompt_type': 'recommendation_request',
        }
        with log_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + chr(10))
    except Exception:
        pass