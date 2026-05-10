#!/usr/bin/env python3
"""Provenance verifier using external M2.7 LLM.

Standalone script that can be called from PreToolUse.py or other hooks.

Usage:
  python provenance_verifier.py --payload '{"contamination_hits": [...], ...}'
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def verify_with_m2_7(
    contamination_hits: list, proposed_facts: list, file_path: str
) -> dict:
    """Call M2.7 to verify contamination risk."""
    prompt = (
        "You are a code review provenance expert. Analyze whether the following "
        "proposed edit represents adjacent-entry contamination.\n\n"
        f"File: {file_path}\n\n"
        f"Proposed new/changed facts:\n{json.dumps(proposed_facts, indent=2)}\n\n"
        f"Potential adjacent-entry contamination (value matching a neighbor):\n"
        f"{json.dumps(contamination_hits, indent=2)}\n\n"
        "Questions to answer:\n"
        "1. Is the proposed value plausibly copied from a neighboring entry "
        "without entity-specific evidence?\n"
        "2. Could this be coincidental (same quota/version used across multiple providers)?\n"
        "3. How confident are you this is real contamination?\n\n"
        "Respond ONLY with valid JSON:\n"
        '{"contamination_confirmed": true|false, '
        '"confidence": 0.5, "reasoning": "...", "recommendation": "block|allow"}'
    )

    try:
        result = subprocess.run(
            ["ai-pcli", "m2.7", "--json-mode", prompt],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr, "recommendation": "allow"}

    except subprocess.TimeoutExpired:
        return {"error": "timeout", "recommendation": "allow"}
    except Exception as e:
        return {"error": str(e), "recommendation": "allow"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--payload",
        type=str,
        help="JSON payload with contamination_hits, proposed_facts, file_path",
    )
    args = parser.parse_args()

    if args.payload:
        try:
            data = json.loads(args.payload)
            result = verify_with_m2_7(
                data.get("contamination_hits", []),
                data.get("proposed_facts", []),
                data.get("file_path", ""),
            )
            print(json.dumps(result))
        except json.JSONDecodeError as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
    else:
        print("Usage: python provenance_verifier.py --payload '{...}'")
        sys.exit(1)
