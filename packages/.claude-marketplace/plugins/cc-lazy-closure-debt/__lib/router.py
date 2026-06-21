#!/usr/bin/env python3
"""cc-lazy-closure-debt router — settings-routed dispatch.

Replaces plugin hooks.json dispatch with the fleet-standard router.py +
settings.json registration (see CLAUDE.md dispatch invariant: a plugin uses
EITHER router.py OR hooks.json, never both — so hooks/hooks.json stays
{"hooks": {}} while this router is registered).

Each event maps to a single plugin hook. The router runs it and passes its
stdout through verbatim, so the UserPromptSubmit hook's additionalContext
reaches Claude Code unchanged. An exit-2 block is propagated on both channels
(the harness surfaces stderr only). The debt hooks are advisory and never
block, but the block path is kept generic and safe.

Usage: python router.py <EventName>   (Stop | UserPromptSubmit | PostToolUse)
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = PLUGIN_ROOT / "hooks"

# event -> (phase subdir under hooks/, [hook filenames])
DISPATCH = {
    "Stop": ("stop", ["cc_lazy_closure_debt_Stop.py"]),
    "UserPromptSubmit": ("userpromptsubmit", ["cc_lazy_closure_debt_UserPromptSubmit.py"]),
    "PostToolUse": ("posttooluse", ["cc_lazy_closure_debt_PostToolUse.py"]),
}


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(0)
    event = sys.argv[1]
    entry = DISPATCH.get(event)
    if not entry:
        sys.exit(0)

    phase, hooks = entry
    input_data = sys.stdin.buffer.read()

    for hook_name in hooks:
        hook_path = HOOKS_DIR / phase / hook_name
        if not hook_path.exists():
            continue
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                [sys.executable, str(hook_path)],
                input=input_data,
                capture_output=True,
                timeout=15,
                creationflags=flags,
            )
            # Pass child stdout through verbatim (carries UserPromptSubmit
            # additionalContext). Skip no-op {} so we don't emit empty noise.
            out = result.stdout.decode(errors="replace").strip()
            if out and out != "{}":
                print(out)
            if result.returncode == 2:
                err = result.stderr.decode(errors="replace").strip()
                if err:
                    sys.stderr.write(err + "\n")
                sys.exit(2)
        except subprocess.TimeoutExpired:
            pass  # Fail open — advisory plugin, never block on its own failure
        except Exception:
            pass  # Fail open


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
