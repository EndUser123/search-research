import json, sys
TARGET = r"P:\packages\search-research\skills\chs\scripts\chs_cli.py"
DATA = r"P:\packages\search-research\skills\chs\scripts\_edit_data.json"
with open(DATA, "r", encoding="utf-8") as f:
    data = json.load(f)
with open(TARGET, "r", encoding="utf-8") as f:
    lines = f.readlines()
# EDIT 1: Replace _resolve_from_identity
ri = None
for i, line in enumerate(lines):
    if "    def _resolve_from_identity(self)" in line:
        ri = i
        break
assert ri is not None, "_resolve_from_identity not found"
# Find end: next blank line before a def
rend = None
for i in range(ri + 3, len(lines)):
    if lines[i].strip() == "" and i+1 < len(lines) and "    def " in lines[i+1]:
        rend = i
        break
assert rend is not None
print("Replacing _resolve_from_identity at lines " + str(ri) + "-" + str(rend))
lines[ri:rend] = data["resolve"].splitlines(True)
# EDIT 2: Insert before get_current_session_id
gcsi = None
for i, line in enumerate(lines):
    if "    def get_current_session_id(self)" in line:
        gcsi = i
        break
assert gcsi is not None, "get_current_session_id not found"
insert = (data["session_path"] + data["compaction"]).splitlines(True)
lines[gcsi:gcsi] = insert
print("Inserted " + str(len(insert)) + " lines before get_current_session_id")
# EDIT 3: Replace export_chain
eci = None
for i, line in enumerate(lines):
    if "    def export_chain(" in line:
        eci = i
        break
assert eci is not None, "export_chain not found"
ece = None
for i in range(eci + 5, len(lines)):
    if lines[i].strip() == "" and i+1 < len(lines) and "    def " in lines[i+1]:
        ece = i
        break
assert ece is not None, "export_chain end not found"
print("Replacing export_chain at lines " + str(eci) + "-" + str(ece))
lines[eci:ece+1] = data["export"].splitlines(True)
with open(TARGET, "w", encoding="utf-8") as f:
    f.writelines(lines)
print("All edits applied successfully")
print("Total lines: " + str(len(lines)))
