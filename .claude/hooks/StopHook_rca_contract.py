import sys
from pathlib import Path
import importlib.util

def _find_hook():
    paths = [
        Path("P:/packages/cc-skills-sdlc/skills/rca/hooks/StopHook_rca_contract.py"),
        Path("P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/rca/hooks/StopHook_rca_contract.py")
    ]
    for p in paths:
        if p.exists():
            return p
    try:
        import json
        installed = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
        if installed.exists():
            data = json.loads(installed.read_text(encoding="utf-8"))
            entries = data.get("plugins", data).get("cc-skills-sdlc@local", [])
            if entries:
                p = Path(entries[0]["installPath"]) / "skills" / "rca" / "hooks" / "StopHook_rca_contract.py"
                if p.exists():
                    return p
    except Exception:
        pass
    raise RuntimeError("StopHook_rca_contract.py not found in cc-skills-sdlc plugin")

_hook = _find_hook()

if str(_hook.parent) not in sys.path:
    sys.path.insert(0, str(_hook.parent))

_spec = importlib.util.spec_from_file_location("StopHook_rca_contract", _hook)
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("__")})

if hasattr(_mod, "main") and __name__ == "__main__":
    _mod.main()