CRIT-LOGIC-001 Fix: PreToolUse_skill_pattern_gate.py phantom import fix

TARGET: P:/.claude/hooks/PreToolUse/PreToolUse_skill_pattern_gate.py

WHAT WAS CHANGED:
- Added sys.path setup for skill_guard before importing:
  _skill_guard_path = Path('P:/packages/skill-guard/src')
  if str(_skill_guard_path) not in sys.path:
      sys.path.insert(0, str(_skill_guard_path))
- This fixes the phantom import: from skill_guard.skill_auto_discovery import get_skill_config
  which previously failed silently because P:/packages/skill-guard/src was not in sys.path

ALSO FIXED:
- test_skill_pattern_gate_coverage.py line 565: changed relative path 'PreToolUse'
  to absolute Path(__file__).resolve().parent.parent / 'PreToolUse'

FILES MODIFIED:
1. P:/.claude/hooks/PreToolUse/PreToolUse_skill_pattern_gate.py (lines 60-66)
2. P:/.claude/hooks/tests/test_skill_pattern_gate_coverage.py (line 565)

VERIFICATION:
- Import resolves correctly: from skill_guard.skill_auto_discovery import get_skill_config
- SKILL_EXECUTION_REGISTRY populates with real skills
- All 3 hook coverage tests pass