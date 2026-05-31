import sys
from pathlib import Path
import importlib.util

def _find_hook():
    paths = [
        Path("P:/packages/cc-aca-epistemic/hooks/userpromptsubmit/anti_sycophancy_injector.py"),
        Path("P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/userpromptsubmit/anti_sycophancy_injector.py")
    ]
    for p in paths:
        if p.exists():
            return p
    raise ImportError("anti_sycophancy_injector.py not found in cc-aca-epistemic plugin")

_hook = _find_hook()

# Insert the hook's __lib directory into sys.path
_lib = str(_hook.parent.parent.parent / "__lib")
if _lib not in sys.path:
    sys.path.insert(0, _lib)

_spec = importlib.util.spec_from_file_location("anti_sycophancy_injector", _hook)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})
