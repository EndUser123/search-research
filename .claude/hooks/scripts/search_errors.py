import json
from pathlib import Path

log = Path(r"P:\.claude\hooks\logs\diagnostics\cc_errors.jsonl")
lines = log.read_text().strip().split("\n")

print("=== Searching for PostToolUse and TaskCreate errors ===\n")

found = 0
for i, line in enumerate(lines):
    try:
        d = json.loads(line)
        error_type = d.get("error_type", "")
        if (
            "PostToolUse" in error_type
            or "TaskCreate" in error_type
            or "task_tracker" in error_type
        ):
            found += 1
            ts = d.get("timestamp", "N/A")
            msg = d.get("error_message", "N/A")
            terminal = d.get("terminal_id", "MISSING")
            claude_sess = d.get("claude_session_id", "MISSING")
            prompt = d.get("user_prompt_preview", "MISSING")
            ctx = d.get("context", {})

            print(f"--- Entry {i+1} ---")
            print(f"Timestamp: {ts}")
            print(f"Error Type: {error_type}")
            print(
                f"Error Message: {msg[:150]}..."
                if len(msg) > 150
                else f"Error Message: {msg}"
            )
            print(f"Terminal ID: {terminal}")
            print(f"Claude Session: {claude_sess}")
            print(f"User Prompt: {prompt}")
            print(f"Context: {ctx}")
            print()
    except Exception:
        pass

print(f"Total matching errors found: {found}")
