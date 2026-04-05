# LLM-CLI Parallel Code Editing Workflow

## Overview

Use `/llm-cli` to run 3 LLMs (qwen, gemini, codex) in parallel for code transformation tasks.
Each LLM works on **disjoint files** to avoid merge conflicts.

## Key Success Factors

| Factor | Solution |
|--------|----------|
| **File size** | Keep under 100 lines per request (use AST to extract functions) |
| **Timeout** | Auto-calculated based on context, but override with `--timeout 60` for safety |
| **Response parsing** | Ask for code blocks only, no explanation |
| **Work distribution** | Assign files by directory - one LLM per directory |

## Quick Test

```bash
cd P:/__csf.nip
python src/commands/co/llm_cli.py "Transform: logger.info(f\"x: {y}\") → logger.info(\"x: %s\", y)" --timeout 30
```

## Parallel File Fix Workflow

### Step 1: Identify Issues
```bash
python -m ruff check src/yt_fts/ --select G004 --output-format concise
```

### Step 2: Group by Directory (disjoint files)
```bash
# Group 1: services/
# Group 2: download/
# Group 3: display/, utils/, core/
```

### Step 3: Run Parallel (PowerShell)
```powershell
# Terminal 1 - Qwen (services/)
cd P:/__csf.nip
python src/commands/co/llm_cli.py @"
Fix G004 logging f-strings in these files. Return ONLY complete fixed file contents in ```python``` blocks. NO explanation.

$(Get-Content P:/projects/yt-fts/src/yt_fts/services/channel_service.py -Raw)
"@ --qwen-only --timeout 120 > qwen_result.txt

# Terminal 2 - Gemini (download/)
python src/commands/co/llm_cli.py @"
Fix G004 logging f-strings. Return ONLY fixed code.

$(Get-Content P:/projects/yt-fts/src/yt_fts/download/download_handler.py -Raw)
"@ --gemini-only --timeout 120 > gemini_result.txt

# Terminal 3 - Codex (display/)
python src/commands/co/llm_cli.py @"
Fix G004 logging f-strings. Return ONLY fixed code.

$(Get-Content P:/projects/yt-fts/src/yt_fts/display/discovery.py -Raw)
"@ --codex-only --timeout 120 > codex_result.txt
```

### Step 4: Extract and Apply
```bash
# Extract code blocks from results
# Write to files
# Verify with ruff
```

## Best Practices

1. **Small chunks**: Process one file at a time, not whole directories
2. **Explicit prompts**: "Return ONLY code blocks. NO explanation."
3. **Timeout buffer**: Use `--timeout 120` for files >50 lines
4. **Verify**: Always check with `ruff` after applying changes

## When to Use AST Script Instead

| Scenario | Tool |
|----------|------|
| Simple transformations (f-string → %) | AST script (`fix_g004_ast.py`) |
| Complex logic (needs understanding) | `/llm-cli` |
| Large files (>500 lines) | AST script or split + `/llm-cli` |
| 100+ similar issues | AST script (faster, deterministic) |
| Design decisions needed | `/llm-cli` (get 3 perspectives) |

## Example: Single File Fix

```bash
# Read file, pipe to LLM, apply result
cd P:/__csf.nip
python src/commands/co/llm_cli.py @"
$(Get-Content P:/projects/yt-fts/src/yt_fts/auth.py -Raw)

Transform all logging f-strings to %% formatting:
- logger.info(f\"x: {y}\") → logger.info(\"x: %s\", y)

Return ONLY the complete fixed file contents.
"@ --qwen-only --timeout 60 | Select-String -Pattern '```python' -Context 0,1000
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Timeout" | Increase `--timeout` or reduce file size |
| Empty result | Check prompt - LLM may have refused |
| Wrong transformation | Be more specific in prompt |
| All 3 failed | Check file encoding or path issues |
