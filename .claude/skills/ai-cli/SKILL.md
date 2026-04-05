---
name: ai-cli
version: "1.4.0"
status: stable
description: Parallel Multi-LLM Command - Run qwen, gemini, codex, vibe, opencode CLI tools in parallel
category: ai-llm
enforcement: strict
triggers:
  - /ai-cli
---

# /ai-cli

**Renamed March 2026:** `/ai-cli` -> `/ai-cli` for consistent naming as AI-based CLI tool.

## EXECUTION DIRECTIVE

**When invoked, check query type first:**

- If query is `"config"` (case-insensitive): Skip to Step 5
- Otherwise: Continue with Steps 1-4

**Step 1:** Run the CLI:
```bash
python "P:\.claude\skills\ai-cli\ai_cli.py" "{{user_query}}" {{options}}
```

**Step 2:** Wait for ALL model outputs to complete

**Step 3:** Report the aggregated CLI outputs verbatim

**Step 4:** Dispatch `adversarial-critic` on `P:/__csf/temp/cli_results/` (skip if `--no-critic` used)

**Step 5 (config query):** Read `P:/.claude/ai-cli-recipe.json` and display:
```
Active CLIs:
  Default:
    <cli1>
    <cli2>
    ...
  Aux / Enh:
    <cli> (<model>, failover to <failover>)
    ...
```
If no config file exists, display: `No saved configuration found`

**DO NOT:**
- Provide your own analysis instead of running the command
- Summarize this skill documentation
- Substitute your capabilities for the external LLM CLIs
- Consider the task complete until bash command output is captured
- Read files and analyze them yourself when user wants multi-LLM perspective

**DEFAULT (no arguments):**
```bash
python "P:\.claude\skills\ai-cli\ai_cli.py" --help
```

**If execution fails:** Report exact error message. Do NOT fabricate results or provide your own analysis as substitute.

---

## Quick Reference

| Option | Description |
|--------|-------------|
| `"<query>"` | Question or task (required, quoted) |
| `--context FILE` | File path to embed (RECOMMENDED for file analysis) |
| `--target FILE` | Target file to investigate (filters session context by relevance) |
| `--summary` | Brief key answers only |
| `--aggregate` | Consensus view showing agreement/disagreement |
| `--complete` | Full raw outputs |
| `--diff` | Show differences between CLI responses |
| `--quality-gate` | Apply 4-Layer Filter System Layer 4 (filters findings by confidence >= 80%) |
| `--output-format json` | Machine-readable JSON output |
| `--timeout N` | Max wait in seconds (default: auto-calculated) |
| `--qwen-only` | Run only qwen-cli |
| `--gemini-only` | Run only gemini-cli |
| `--codex-only` | Run only codex-cli |
| `--vibe-only` | Run only vibe |
| `--opencode-only` | Run only opencode (DeepSeek V3) |
| `--opencode-model MODEL` | OpenCode model or alias (kimi, minimax) |
| `--route` | Use rule-based routing (from llm-route) to select CLI by task keywords |
| `--doc-review` | Use document review prompt (from llm-doc_review) - prepends review questions |
| `--hide-prompt` | Suppress the enhanced prompt display (which is shown by default) |
| `--no-critic` | Skip the adversarial critic analysis after JSON output |
| `-bash` | Show bash commands instead of executing (debug) |

---

## Critical Rules

1. **File context MUST use --context flag** - Piped stdin is ignored when auto-context detected
2. **Timeout protection:** Default auto-calculated (180s base + 1s per MB context)
3. **Individual failures don't abort others** - Report which CLIs succeeded/failed
4. **Empty responses are flagged as errors** - Don't silently accept blank output

---

## Output Display

For clean output format when using "config" query, see [references/output-template.md](references/output-template.md).

## References

| Topic | File |
|-------|------|
| Example invocations (basic, output modes, specific LLMs, advanced) | `references/examples.md` |
| 4-Layer Filter System / Quality Gate integration | `references/quality-gate.md` |
| Context handling best practices and auto-detection | `references/context-handling.md` |
| CLI characteristics, OpenCode models, setup, health check, limitations | `references/cli-reference.md` |
| Troubleshooting (errors, causes, fixes) | `references/troubleshooting.md` |
