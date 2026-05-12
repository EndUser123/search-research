#!/usr/bin/env bash
# Contract telemetry shell wrapper
# Usage: source contract-telemetry-queries.sh && dashboard
#   or:  bash contract-telemetry-queries.sh dashboard

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CMD="${1:-dashboard}"
exec python3 "$SCRIPT_DIR/contract-telemetry-queries.py" "$CMD"
