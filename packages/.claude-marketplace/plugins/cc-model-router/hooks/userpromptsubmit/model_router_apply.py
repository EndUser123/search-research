#!/usr/bin/env python3
"""UserPromptSubmit hook: consume a stale autoswitch recommendation and switch
the model BEFORE the next response is generated.

The old post-response autoswitch path forced a wasted turn + manual
"press Up Enter" resend. This hook runs on UserPromptSubmit — before
generation — so the new model is in effect for the *current* turn. This is
the only autoswitch path.

States:
  - no recommendation.json          -> no-op
  - recommendation expired (>300s)   -> no-op
  - recommendation already consumed -> no-op
  - action_mode != autoswitch       -> no-op (warn path is owned by classify)
  - recommended == current          -> no-op
  - dry_run env var set             -> audit row only, no rewrite
  - else                            -> atomic settings.json write + audit row

Exit codes:
  0  always. We must NOT block the user prompt.

Env vars:
  MODEL_ROUTER_APPLY_DRY_RUN=1  -> audit only, no settings.json write.
"""

import json
import os
import pathlib
import sys
from datetime import datetime

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(PLUGIN_ROOT / "__lib") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "__lib"))

from settings_writer import read_settings, write_settings  # type: ignore[import-not-found]  # noqa: E402

TTL_SECONDS = 300


def get_state_path(terminal_id: str, session_id: str) -> pathlib.Path:
    return (
        pathlib.Path(os.environ.get("CSF_STATE_DIR") or str(pathlib.Path("P:/") / ".claude" / "state"))
        / "model-router"
        / terminal_id
        / session_id
    )


def load_recommendation(state_path: pathlib.Path) -> dict | None:
    p = state_path / "recommendation.json"
    if not p.exists():
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def is_expired(rec: dict, ttl: int = TTL_SECONDS) -> bool:
    written = rec.get("written_at", "")
    if not written:
        return True
    try:
        age = (datetime.now() - datetime.fromisoformat(written)).total_seconds()
    except Exception:
        return True
    return age > ttl


def mark_consumed(state_path: pathlib.Path) -> None:
    p = state_path / "recommendation.json"
    if not p.exists():
        return
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        data["consumed"] = True
        data["consumed_at"] = datetime.now().isoformat()
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def append_audit(state_path: pathlib.Path, row: dict) -> None:
    audit = state_path.parent.parent / "apply_audit.jsonl"
    try:
        audit.parent.mkdir(parents=True, exist_ok=True)
        with open(audit, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
    except Exception:
        pass


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    terminal_id = data.get("terminal_id", "default")
    session_id = data.get("session_id", "default")
    state_path = get_state_path(terminal_id, session_id)

    rec = load_recommendation(state_path)
    if not rec:
        sys.exit(0)

    if is_expired(rec):
        sys.exit(0)

    if rec.get("consumed"):
        sys.exit(0)

    if rec.get("action_mode") != "autoswitch":
        sys.exit(0)

    recommended = rec.get("recommended_model", "")
    current = rec.get("current_model", "")
    if not recommended or recommended == current:
        sys.exit(0)

    dry_run = os.environ.get("MODEL_ROUTER_APPLY_DRY_RUN") == "1"

    base_recommended = recommended.split("[")[0]
    base_current = current.split("[")[0]
    if base_recommended == base_current:
        # Suffix-only change (e.g. reasoning effort) is also a no-op.
        sys.exit(0)

    ts = datetime.now().isoformat()
    if not dry_run:
        settings = read_settings()
        settings["model"] = recommended
        try:
            write_settings(settings)
        except Exception as e:
            append_audit(
                state_path,
                {
                    "ts": ts,
                    "action_taken": "error",
                    "current_model": current,
                    "new_model": recommended,
                    "error": str(e),
                    "terminal_id": terminal_id,
                    "session_id": session_id,
                },
            )
            sys.exit(0)

    # Signal to any harness / child process that the new model is intended.
    os.environ["ANTHROPIC_MODEL"] = recommended

    mark_consumed(state_path)

    append_audit(
        state_path,
        {
            "ts": ts,
            "action_taken": "would_have_applied" if dry_run else "applied",
            "current_model": current,
            "new_model": recommended,
            "env_var_set": recommended,
            "terminal_id": terminal_id,
            "session_id": session_id,
            "dry_run": dry_run,
        },
    )

    print(
        f"[model-router-apply] model={current} -> {recommended} "
        f"(in effect for current turn; dry_run={dry_run})",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
