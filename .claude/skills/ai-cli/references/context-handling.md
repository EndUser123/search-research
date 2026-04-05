# Context Handling Best Practices

## Smart Auto-Context Detection

The system automatically detects context from your query using multiple strategies:

1. **File path extraction**: Query mentions a file (e.g., "review ai_cli.py", "check SKILL.md")
2. **Git changed files**: Uses most recently modified file in git repo
3. **Session activity**: Falls back to WT_SESSION (recent session context)
4. **No context**: Runs query without context when nothing is detected

## Recommended Patterns

**DO - Use natural language with file references:**
```bash
# GOOD: File reference in query (auto-detected)
/ai-cli "review ai_cli.py for bugs"

# GOOD: Explicit file path
/ai-cli "investigate the bypass in P:\.claude\skills\v\hooks\PreToolUse_v_stage_enforcer.py"

# GOOD: Still works with explicit --context flag
/ai-cli "investigate this issue" --context hook.py
```

**AVOID - Completely ambiguous queries:**
```bash
# MAY BE PROBLEMATIC: No file reference, no git changes, what should be investigated?
/ai-cli "investigate this"

# MAY BE PROBLEMATIC: No target specified
/ai-cli "do the investigation"
```

## Detection Feedback

**When smart detection finds context:**
```
[Auto-detected file from query: ai_cli.py]
[Context loaded: 12345 characters]
```

**When smart detection uses git changed files:**
```
[Auto-detected git changed file: .claude/hooks/Stop.py]
[Context loaded: 2345 characters]
```

**When nothing is detected, use explicit context:**
```bash
# Fallback: Specify explicitly if auto-detection misses
/ai-cli "investigate this issue" --context path/to/file.py
```
