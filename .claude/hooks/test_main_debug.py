import io
import os
import sys

# Set up environment
os.environ['PYTHON_C_VALIDATOR_ENABLED'] = 'true'

# Simulate stdin
test_json = '{"tool_name": "Bash", "tool_input": {"command": "python -c \"print({=*60})\""}}'
sys.stdin = io.StringIO(test_json)

# Now import and run the hook's main function
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



print("DEBUG: About to call main()", file=sys.stderr)
            _logger.debug(f"DEBUG: ENABLED = {validator.ENABLED}",)
# This will call main() which should exit with code 2
try:
    validator.main()
    print("DEBUG: main() returned (did not exit)", file=sys.stderr)
except SystemExit as e:
            _logger.debug(f"DEBUG: SystemExit raised with code: {e.code}",)    raise
