import sys

TARGET = r"P:\packages\search-research\skills\chs\scripts\chs_cli.py"

with open(TARGET, "r", encoding="utf-8") as f:
    content = f.read()

print(f"Loaded {len(content)} chars")

# EDIT 1: Replace _resolve_from_identity
old1_start_marker = "    def _resolve_from_identity(self) -> dict | None:"
old1_end_marker = "            return None

    def get_current_session_id"