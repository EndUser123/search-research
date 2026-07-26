#!/usr/bin/env python3
"""CLI wrapper for telemetry logging — callable from any skill via run_terminal_command.

Usage (after a spawn_subagent call):
    python P:/.agents/scripts/log_spawn.py \
        --model glm-5-2 --caller /tp --success true \
        --latency 8200 --domain critical-friend --notes "pool pos 2"

Usage (after a direct API call):
    python P:/.agents/scripts/log_call.py \
        --model minimax-m3 --caller /check --success true \
        --latency 3200 --domain code-verification

Exit 0 on success, 1 on error (non-blocking — telemetry failure should not break the skill).
"""
import argparse
import sys
from pathlib import Path

# Import from model-benchmark scripts
sys.path.insert(0, str(Path("C:/Users/brsth/.grok/skills/model-benchmark/scripts")))


def main():
    parser = argparse.ArgumentParser(description="Log a spawn_subagent telemetry record")
    parser.add_argument("--model", required=True, help="Model slug (e.g., glm-5-2, minimax-m3)")
    parser.add_argument("--caller", required=True, help="Which skill (e.g., /tp, /check, /review)")
    parser.add_argument("--success", required=True, choices=["true", "false"], help="Did the call succeed?")
    parser.add_argument("--latency", type=float, default=0, help="Wall-clock latency in ms")
    parser.add_argument("--domain", default="spawn", help="Task domain (e.g., critical-friend, code-verification)")
    parser.add_argument("--notes", default="", help="Free-form notes")
    parser.add_argument("--error-type", default="", help="Error type if failed")
    args = parser.parse_args()

    try:
        from telemetry import log_spawn

        log_spawn(
            model=args.model,
            task_domain=args.domain,
            latency_ms=args.latency,
            success=args.success == "true",
            caller=args.caller,
            notes=args.notes,
        )
    except Exception as e:
        # Non-blocking: telemetry failure should never break a skill
        print(f"telemetry warning: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
