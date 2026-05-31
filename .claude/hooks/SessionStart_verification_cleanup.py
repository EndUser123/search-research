import sys
from pathlib import Path
import importlib.util

def _find_hook():
    paths = [
        Path("P:/packages/cc-aca-session/hooks/sessionstart/aca_session_verification_cleanup.py"),
        Path("P:/packages/.claude-marketplace/plugins/cc-aca-session/hooks/sessionstart/aca_session_verification_cleanup.py")
    ]
    for p in paths:
        if p.exists():
            return p
    raise ImportError("aca_session_verification_cleanup.py not found in cc-aca-session plugin")

_hook = _find_hook()

if str(_hook.parent) not in sys.path:
    sys.path.insert(0, str(_hook.parent))
if str(_hook.parent.parent) not in sys.path:
    sys.path.insert(0, str(_hook.parent.parent))
if str(_hook.parent.parent.parent) not in sys.path:
    sys.path.insert(0, str(_hook.parent.parent.parent))

_spec = importlib.util.spec_from_file_location("aca_session_verification_cleanup", _hook)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})

if hasattr(_mod, "main") and __name__ == "__main__":
    _mod.main()
