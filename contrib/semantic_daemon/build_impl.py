from pathlib import Path

p = Path("src/lib/daemons/unified_semantic_daemon.py")
header = p.read_text(encoding="utf-8")
lines = header.split("\\n")
lines[29] = 'PIPE_NAME = r"\\\\.\\\\pipe\\\\csf_semantic"'
# Remove corrupted classes
for i, line in enumerate(lines):
    if line.startswith("class X") or line.startswith("class SemanticClient"):
        lines = lines[:i]
        break
p.write_text("\\n".join(lines), encoding="utf-8")
print("Fixed header")
