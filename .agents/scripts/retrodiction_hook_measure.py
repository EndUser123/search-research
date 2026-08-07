#!/usr/bin/env python3
"""Retrodiction harness: measure a detection hook's FP/TP rate over historical
session transcripts BEFORE shipping (or before promoting advisory → blocking).

TECHNIQUE: import the hook's detection function, run it over real assistant
turns from ~/.grok/sessions/, and report each fire for manual TP/FP labeling.
This converts "wait weeks for live data" into "know the FP rate in 5 minutes."

USAGE:
    1. Set HOOK_SCAN_IMPORT and HOOK_SCAN_FUNC below to match your hook.
    2. python retrodiction_hook_measure.py [N sessions]  (default: 40)
    3. Label each fire as TP (real catch) or FP (false alarm).

See: [[keyword-detection-recommendations-falsified-67percent-fp]] for the
case study that validated this technique.

ADAPT FOR YOUR HOOK: replace the HOOK_SCAN_IMPORT / HOOK_SCAN_FUNC below with
your hook's scan function. The function must take (text: str) and return a
list of findings (each a dict with at least a 'sentence' key).
"""
import json
import re
import sys
import textwrap
from pathlib import Path

# === ADAPT THIS SECTION FOR YOUR HOOK ===
# Example: a Stop hook with a scan_message(text) function
# Uncomment and modify for your specific hook:
#
# HOOK_DIR = Path(r"C:\Users\brsth\.grok\hooks")
# sys.path.insert(0, str(HOOK_DIR))
# from YourStopHook import scan_message as hook_scan
#
# For demonstration, use a no-op that finds nothing:
def hook_scan(text: str) -> list:
    """Placeholder — replace with your hook's scan function."""
    return []
# ========================================

SESSIONS_ROOT = Path(r"C:\Users\brsth\.grok\sessions\P%3A%5C")


def extract_assistant_text(msg):
    """Extract text from a message content (string or array)."""
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return ""


def main():
    n_sessions = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    sessions = sorted(
        SESSIONS_ROOT.glob("*/chat_history.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:n_sessions]

    print(f"# Retrodiction over {len(sessions)} most recent sessions\n", file=sys.stderr)

    fires = []  # (session_id, turn_idx, sentence, reason)
    total_turns = 0

    for sp in sessions:
        sid = sp.parent.name
        try:
            with open(sp, "r", encoding="utf-8") as f:
                turn_idx = 0
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if msg.get("type") != "assistant":
                        continue
                    text = extract_assistant_text(msg)
                    if not text or len(text) < 50:
                        continue
                    total_turns += 1
                    turn_idx += 1
                    findings = hook_scan(text)
                    for fnd in findings:
                        fires.append((sid[:8], turn_idx, fnd["sentence"], fnd["reason"]))
        except Exception as e:
            print(f"WARN {sid}: {e}", file=sys.stderr)

    print(f"# Scanned {total_turns} assistant turns across {len(sessions)} sessions", file=sys.stderr)
    print(f"# Fires: {len(fires)}\n", file=sys.stderr)

    # Output for labeling
    print(f"Retrodiction: {len(fires)} advisory fires across {total_turns} turns in {len(sessions)} sessions")
    print(f"Fire rate: {len(fires)/total_turns*100:.1f}% of turns would have received advisory feedback\n")

    for i, (sid, turn, sentence, reason) in enumerate(fires, 1):
        sent_display = textwrap.shorten(sentence, width=180, placeholder="...")
        print(f"--- FIRE {i} [{sid}:{turn}] ---")
        print(f"  sentence: {sent_display}")
        print(f"  reason:   {reason}")
        print()


if __name__ == "__main__":
    main()
