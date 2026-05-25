
import pathlib
content = pathlib.Path(r"P:/.claude/hooks/tests/_veridical_test_content.txt").read_text(encoding="utf-8")
pathlib.Path(r"P:/.claude/hooks/tests/test_veridical_gate.py").write_text(content, encoding="utf-8")
print("Written test file")
