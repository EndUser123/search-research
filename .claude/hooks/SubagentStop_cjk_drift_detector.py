"""SubagentStop CJK drift gate — delegates to cc-aca-observability plugin.

Migrated 2026-06-15 from cc-aca-observability plugin hooks.json (subprocess) to
local in-process dispatch (split-dispatch consolidation). Imports detect_cjk()
from the canonical plugin posttool module; registered in settings.json SubagentStop.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_POSTTOOL = Path("P:/packages/cc-aca-observability/hooks/posttool")
if not _POSTTOOL.exists():
    _POSTTOOL = Path(
        "P:/packages/.claude-marketplace/plugins/cc-aca-observability/hooks/posttool"
    )
if _POSTTOOL.exists() and str(_POSTTOOL) not in sys.path:
    sys.path.insert(0, str(_POSTTOOL))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    from cjk_drift_detector import detect_cjk  # noqa: PLC0415

    text = event.get("response", "")
    sample = detect_cjk(text)
    if not sample:
        return 0

    msg = (
        f"[CJK drift detected] Output contains non-English characters "
        f'(sample: "{sample}"). The underlying model drifted from English. '
        f"Respond in English only - no Chinese, Japanese, or Korean under any "
        f"circumstances, even when source content contains them."
    )
    print(msg, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
