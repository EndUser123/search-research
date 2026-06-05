"""Bifrost tier validation probe.

Invoked by cc-bifrost.ps1 Invoke-BifrostValidation. Reads the current
tier->model mapping from argv as JSON (no string interpolation, no
injection surface), probes each tier against the live Bifrost gateway,
prints OK/SKIP/HTTP/ERROR per tier, and exits 0 on all-OK, 1 on any
HTTP failure, 2 on all-skip (no tiers configured), 3 on probe error.

Usage:
    python bifrost_validate.py '<tiers_json>' '<models_json>'

Where:
    tiers_json  = JSON array of tier names, e.g. ["Sonnet","Opus","Haiku"]
    models_json = JSON array of model names in the same order, e.g. ["M3","glm-5.1",null]

Exit codes:
    0 = all configured tiers returned 200
    1 = at least one tier returned non-200
    2 = all tiers are SKIP (no model configured)
    3 = probe crashed (could not reach gateway, etc.)
"""

import json
import sys
import urllib.error
import urllib.request

GATEWAY_URL = "http://localhost:8080/v1/chat/completions"
PROBE_TIMEOUT_SECONDS = 15


def main() -> int:
    # Read JSON from stdin, NOT argv. PowerShell + Windows python launcher
    # splits argv on commas which mangles JSON arrays. Stdin is a single
    # stream that preserves JSON structure.
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"ERROR: invalid JSON on stdin: {e}", file=sys.stderr)
        return 3

    if not isinstance(payload, dict) or "tiers" not in payload or "models" not in payload:
        print("ERROR: stdin JSON must be an object with 'tiers' and 'models' arrays", file=sys.stderr)
        return 3

    tiers = payload["tiers"]
    models = payload["models"]

    if not isinstance(tiers, list) or not isinstance(models, list):
        print("ERROR: tiers and models must be JSON arrays", file=sys.stderr)
        return 3

    if len(tiers) != len(models):
        print(
            f"ERROR: tiers ({len(tiers)}) and models ({len(models)}) length mismatch",
            file=sys.stderr,
        )
        return 3

    results = []
    for tier, model in zip(tiers, models):
        if not model:
            print(f"{tier}: SKIP (no model set)")
            results.append(("skip", tier))
            continue
        try:
            payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
            }).encode()
            req = urllib.request.Request(
                GATEWAY_URL,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=PROBE_TIMEOUT_SECONDS) as resp:
                print(f"{tier} ({model}): OK")
                results.append(("ok", tier))
        except urllib.error.HTTPError as e:
            print(f"{tier} ({model}): HTTP {e.code}")
            results.append(("fail", tier))
        except Exception as e:
            print(f"{tier} ({model}): ERROR - {e}")
            results.append(("fail", tier))

    # All-SKIP is a distinct failure: nothing was actually validated.
    # A silent 0 here would mislead the user into thinking their tiers work
    # when in fact no tiers are configured at all.
    all_skip = all(r[0] == "skip" for r in results)
    if all_skip and results:
        return 2

    if any(r[0] == "fail" for r in results):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
