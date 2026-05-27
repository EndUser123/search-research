
import pathlib
target = pathlib.Path(__file__).parent / 'test_guard_false_positive_fixes.py'
target.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
print("noop")
