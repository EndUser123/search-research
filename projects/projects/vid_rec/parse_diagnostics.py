import json
import sys
from pprint import pprint


def parse_logs(log_path):
    """Parse all database error entries with enhanced diagnostics"""
    errors = []
    with open(log_path) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("event") == "Database operation retry error":
                    errors.append(entry)
                elif entry.get("event") == "Database writer thread error":
                    errors.append(entry)
                elif entry.get("event") == "Unexpected error in database writer thread":
                    errors.append(entry)
            except json.JSONDecodeError:
                continue
    return errors


if __name__ == "__main__":
    log_path = sys.argv[1] if len(sys.argv) > 1 else "logs/vidrec.json"
    error_entries = parse_logs(log_path)

    print(f"Found {len(error_entries)} error entries:")
    for i, entry in enumerate(error_entries, 1):
        print(f"\n--- Error Entry {i} ---")
        print(f"Timestamp: {entry.get('timestamp')}")
        print(f"Event: {entry.get('event')}")
        print(f"Logger: {entry.get('logger')}")
        print(f"Level: {entry.get('level')}")

        # Print all diagnostic fields if available
        diagnostic_fields = [
            "error_code",
            "error_name",
            "extended_code",
            "message",
            "command",
            "args",
            "attempt",
            "max_retries",
            "stack_trace",
            "diagnostics",
            "thread_stack",
        ]

        for field in diagnostic_fields:
            if field in entry:
                print(f"\n{field}:")
                pprint(entry[field])

        print("\nFull entry:")
        pprint(entry)
