from pathlib import Path

content = Path("src/lib/daemons/unified_semantic_daemon.py").read_text(encoding="utf-8")
print(len(content))
