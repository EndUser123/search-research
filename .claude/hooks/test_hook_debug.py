import sys

# Simulate stdin input
test_json = {"tool_name": "Bash", "tool_input": {"command": "python -c \"print({=*60})\""}}

print(f"DEBUG: tool_name = {test_json.get('tool_name')}", file=sys.stderr)
print(f"DEBUG: command = {test_json.get('tool_input', {}).get('command')}", file=sys.stderr)

# Import the hook
import PreToolUse_python_c_validator as validator

import logging as _li
_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)



print(f"DEBUG: Pattern exists = {hasattr(validator, 'PYTHON_C_PATTERN')}", file=sys.stderr)
            _logger.debug(f"DEBUG: Pattern = {validator.PYTHON_C_PATTERN.pattern}",)
# Test the pattern
command = test_json.get('tool_input', {}).get('command', '')
match = validator.PYTHON_C_PATTERN.search(command)
if match:
    print(f"DEBUG: Pattern matched! Groups = {match.groups()}", file=sys.stderr)
    print(f"DEBUG: Code to validate: {match.group(2)}", file=sys.stderr)
else:
            _logger.debug('DEBUG: Pattern did NOT match',)