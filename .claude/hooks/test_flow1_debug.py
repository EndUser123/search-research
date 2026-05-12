#!/usr/bin/env python3
"""Debug why Flow 1 response got 'allow'."""
import sys; sys.path.insert(0, 'P:/.claude/hooks')

from epistemic_validator import (
    validate, EpistemicConfig, _is_grounded_status_confirmation,
    _is_direct_answer_to_question, _has_inference_marker,
    _has_citation_markers, _classify_response_type,
    _is_locally_grounded_summary, is_status_summary_response,
)

RESPONSE = 'All tests passed in 0.58 seconds.'
TRANSCRIPT = 'pytest output: 15 passed in 0.58s'

print(f'Response: {RESPONSE!r}')
print(f'Word count: {len(RESPONSE.split())}')
print(f'_classify_response_type: {_classify_response_type(RESPONSE)}')
print(f'_has_citation_markers: {_has_citation_markers(RESPONSE)}')
print(f'_has_inference_marker: {_has_inference_marker(RESPONSE)}')
print(f'_is_direct_answer_to_question: {_is_direct_answer_to_question(RESPONSE)}')
print(f'_is_grounded_status_confirmation: {_is_grounded_status_confirmation(RESPONSE)}')
print(f'is_status_summary_response: {is_status_summary_response(RESPONSE)}')

# Check locally grounded
cfg = EpistemicConfig()
cfg.tool_transcript = TRANSCRIPT
print(f'_is_locally_grounded_summary: {_is_locally_grounded_summary(RESPONSE, TRANSCRIPT, len(RESPONSE.split()))}')

# Validate
cfg.tool_transcript = TRANSCRIPT
verdict = validate(RESPONSE, cfg)
print(f'Final verdict: {verdict.decision}')
print(f'Issues: {[(i.type, i.section, i.message[:80]) for i in verdict.issues]}')
