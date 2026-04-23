import ast
import json
import sys


def main():
    try:
        raw_data = sys.stdin.read()
        if not raw_data:
            sys.exit(0)
        data = json.loads(raw_data)
    except Exception:
        sys.exit(0)

    tool_name = data.get("tool_name")
    if tool_name != "Write":
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")

    if not file_path.endswith(".py"):
        sys.exit(0)

    try:
        ast.parse(content)
    except SyntaxError as e:
        filename = file_path.replace("\\", "/").split("/")[-1]
        lineno = e.lineno or "?"
        msg = e.msg or "syntax error"
        print(f"⛔ Python syntax error in {filename}:{lineno} — {msg}", file=sys.stderr)
        if e.text:
            print(f"  → {e.text.strip()}", file=sys.stderr)
        sys.exit(2)
    except Exception as ex:
        print(f"⛔ Python parse error in {file_path}: {ex}", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
