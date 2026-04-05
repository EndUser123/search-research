---
description: "Ralph Loop v2 - bash-free input handling via stdin"
allowed-tools: []
---

# Ralph Loop v2 - Bash-Free

Uses stdin to pass input, avoiding bash quoting issues.

**v8.2 Features:**
- Auto project root detection (pytest.ini, pyproject.toml, tests/ dir)
- Coverage threshold enforcement (--coverage-threshold, default 80%)
- Per-iteration file tracking (iteration_started_at for faster feedback)

**TDD Pattern Library:** See `.data/ralph-tdd-patterns.md` for learned testing patterns.

Usage: pipe your input to Ralph

```bash
echo "1. First task
2. Second task with parens ()
3. Third task" | /ralph
```

Or use a heredoc:

```bash
/ralph << 'EOF'
1. First task
2. Second task with parens ()
3. Third task
EOF
```

Or use a file:

```bash
/ralph < tasks.txt
```

```!
# Read from stdin and pass to Python via temp file
# This avoids bash word-splitting and interpretation of special characters
# Cross-platform temp file handling (Windows + Unix)
if [[ -n "$TEMP" ]]; then
    TEMP_DIR="$TEMP"
elif [[ -n "$TMP" ]]; then
    TEMP_DIR="$TMP"
else
    TEMP_DIR="/tmp"
fi
TEMP_FILE="${TEMP_DIR}/ralph_input_${RANDOM:-$$}.txt"
cat > "$TEMP_FILE"
python "${CLAUDE_PLUGIN_ROOT}/scripts/setup-ralph-loop.py" --input-file "$TEMP_FILE"
rm -f "$TEMP_FILE"
```
