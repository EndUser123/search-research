"""Atomic JSON write with Windows-sharing-violation retry + tier derivation.

Shared by:
  - hooks/sessionstart/model_router_init.py (state file; derive_tier)
  - hooks/userpromptsubmit/model_router_apply.py (recommendation.json; atomic_write_json)

CCR is the sole routing authority — nothing here writes .claude/settings.json.
The legacy settings.json R/W helpers were removed when autoswitch was retired.
"""

from __future__ import annotations

import json
import pathlib
import random
import shutil
import time
from typing import Any


def atomic_write_json(
    path: pathlib.Path | str,
    data: dict[str, Any],
    max_attempts: int = 8,
    base_delay: float = 0.02,
) -> None:
    """Atomically write *data* as JSON to *path*.

    On Windows, os.replace fails with PermissionError (WinError 32) when
    another process holds the target file without FILE_SHARE_DELETE
    (e.g. antivirus, file indexers, or concurrent Claude Code processes
    opening settings.json). The replace is intended to be atomic; the OS
    cannot always deliver that across all share modes, so we retry with
    backoff. POSIX does not need this.

    Final-attempt fallback uses shutil.move (copy+unlink across devices,
    some share modes that os.replace rejects), at the cost of atomicity.
    Raises PermissionError if all attempts fail.
    """
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()

    for attempt in range(max_attempts):
        try:
            tmp.replace(target)
            return
        except PermissionError:
            if attempt == max_attempts - 1:
                try:
                    shutil.move(str(tmp), str(target))
                    return
                except Exception as e:
                    try:
                        tmp.unlink(missing_ok=True)
                    except Exception:
                        pass
                    raise PermissionError(
                        f"Could not replace {target} after {max_attempts} attempts: {e}"
                    ) from e
            delay = min(base_delay * (2 ** attempt), 2.0)
            delay += random.uniform(0, delay * 0.25)
            time.sleep(delay)


def derive_tier(model: str) -> str:
    """Classify a model string into haiku/sonnet/opus/unknown by substring.

    Shared by model_router_init.py (SessionStart snapshot) and
    model_router_apply.py (post-switch state refresh) so both writers of
    current_tier agree on the same classification.
    """
    model_lower = model.lower()
    if "haiku" in model_lower:
        return "haiku"
    if "sonnet" in model_lower:
        return "sonnet"
    if "opus" in model_lower:
        return "opus"
    return "unknown"
