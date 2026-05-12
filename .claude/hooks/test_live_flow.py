#!/usr/bin/env python3
"""Simulate the Stop.py epistemic flow to verify guidance marker trigger."""
import sys, os, json, time, re
sys.path.insert(0, 'P:/.claude/hooks')

from epistemic_validator import validate, EpistemicConfig, build_local_summary_guidance
from pathlib import Path

# Mock tool_events (simulating what would come from the hook payload)
tool_events = [
    {'name': 'Bash', 'output': 'pytest output: 15 passed in 0.58s'},
]

# Assemble tool_transcript (Stop.py lines 504-512)
parts = []
for event in tool_events[-5:]:
    output = event.get('output', '')
    if output and isinstance(output, str):
        parts.append(output[:500])
tool_transcript = '\n'.join(parts)
print(f'tool_transcript: {tool_transcript!r}')

cfg = EpistemicConfig()
cfg.tool_transcript = tool_transcript

# A response that summarizes without citation or link phrase
# Must be analytical type to avoid grounded_status_confirmation bypass
response = 'The test suite shows comprehensive validation of the local summary guidance system.'
verdict = validate(response, cfg)
print(f'verdict.decision: {verdict.decision}')
print(f'verdict.issues: {[(i.type, i.message) for i in verdict.issues]}')

# Check if we should write guidance marker
block_issues = {i.type for i in verdict.issues}
citation_fail = (
    'unsupported_fact' in block_issues
    or ('format' in block_issues and not cfg.tool_transcript)
)
print(f'citation_fail: {citation_fail}')

if verdict.decision == 'block' and cfg.tool_transcript and citation_fail:
    tool_name = tool_events[-1].get('name', 'the tool') if tool_events else 'the tool'
    guidance = build_local_summary_guidance(tool_name, cfg.tool_transcript)
    print(f'guidance: {guidance!r}')

    # Write marker
    session_id = 'live-test-session'
    terminal_id = 'live-test-terminal'
    safe_session = re.sub(r'[^a-zA-Z0-9_.-]+', '_', str(session_id))
    safe_terminal = re.sub(r'[^a-zA-Z0-9_.-]+', '_', str(terminal_id))
    state_dir = Path('P:/.claude/hooks/state/local_summary_guidance')
    state_dir.mkdir(parents=True, exist_ok=True)
    marker_path = state_dir / f'guidance__{safe_session}__{safe_terminal}.json'
    marker_data = {
        'session_id': str(session_id),
        'terminal_id': str(terminal_id),
        'timestamp': time.time(),
        'guidance': guidance,
    }
    marker_path.write_text(json.dumps(marker_data), encoding='utf-8')
    print(f'Marker written: {marker_path}')
    print(f'Marker contents preview: {guidance[:200]}...')
else:
    print('No guidance marker would be written')
