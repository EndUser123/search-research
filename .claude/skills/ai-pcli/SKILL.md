---
name: ai-pcli
version: "1.6.0"
status: stable
description: Parallel Multi-LLM Command with prompting-toolkit enhancement and cross-agent meta-critique
category: ai-llm
enforcement: strict
triggers:
  - /ai-pcli
workflow_steps:
  - Parse query and options
  - Build context from --context or auto-detection
  - Apply prompt enhancement (built-in or --prompt-toolkit)
  - Run gemini, codex, pi-m27, pi-glm in parallel
  - Aggregate outputs
  - Save results to session file for meta-critique access
  - Run ai-cli-critic unless --no-critic
  - Run cross-agent meta-critique if --meta-critique (Phase 2)
---

# /ai-pcli

**Parallel multi-LLM command with prompting-toolkit:** `/ai-pcli` runs multiple CLI-backed model providers and aggregates their output.

## EXECUTION DIRECTIVE

**When invoked, check query type first:**

- If query is `"config"` (case-insensitive): Skip to Step 6
- Otherwise: Continue with Steps 1-4

**Step 1:** Run the CLI:
```bash
python "P:/packages/cc-skills-ai-cli/skills/ai-pcli/ai_cli.py" "{{user_query}}" {{options}}
```

**Step 2:** Wait for ALL model outputs to complete

**Step 3:** Report the aggregated CLI outputs verbatim

**Step 4:** Save results to session file for meta-critique access:
```bash
python -c "
import sys, json
from pathlib import Path
# Find most recent ai-pcli results
evidence_dir = Path('P:/.claude/.evidence/ai-pcli')
if evidence_dir.exists():
    latest = sorted(evidence_dir.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)
    if latest:
        session_file = latest[0]
        print(session_file)
        sys.exit(0)
print('NO_RESULTS_FILE')
sys.exit(1)
"
```

**Step 5:** Run `ai-cli-critic` on the combined output unless `--no-critic` is set

```text
Task(subagent_type="ai-cli-critic",
     description="Critic pass for /ai-pcli outputs. Review the combined LLM outputs for unsupported claims, contradictions, overconfidence, and missing evidence. Use the saved JSON file if available, otherwise analyze the raw transcript.")
```

**Step 6 (Meta-Critique — Phase 2, if --meta-critique):** Run cross-agent meta-critique to catch contradictions and blind spots across all 4 agents:

```text
Task(subagent_type="general-purpose",
     description="Cross-agent meta-critique for /ai-pcli. Read the results file at {session_file}, the original query, and all 4 agent outputs (gemini, codex, pi-m27, pi-glm). Identify: (1) contradictions between agents, (2) calibration issues where severity ratings differ for similar issues, (3) blind spots — what no agent caught but should have, (4) precision failures — what an agent flagged that is actually fine. Output a concise meta-critique with specific citations to agent names and their outputs.")
```

**Step 7 (config query):** Read `P:/.claude/ai-pcli-recipe.json` and display:
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
python "P:/packages/cc-skills-ai-cli/skills/ai-pcli/ai_cli.py" --help
```

**If execution fails:** Report exact error message. Do NOT fabricate results or provide your own analysis as substitute.

---

## Default Agents

| Agent | CLI | Default |
|-------|-----|---------|
| gemini | gemini-cli | Yes |
| codex | OpenAI Codex | Yes |
| pi-m27 | pi --model minimax/MiniMax-M2.7 | Yes |
| pi-glm | pi --model z-ai/glm-5.1 | Yes |
| qwen | qwen-cli | No |
| opencode | opencode-ai | No |

**Config:** `P:/.claude/ai-pcli-recipe.json`

---

## Quick Reference

| Option | Description |
|--------|-------------|
| `"<query>"` | Question or task (required, quoted) |
| `--context FILE` | File path to embed — passed to pi as `-p @FILE` |
| `--target FILE` | Target file to investigate (filters session context by relevance) |
| `--summary` | Brief key answers only |
| `--aggregate` | Consensus view showing agreement/disagreement |
| `--quality-weighted` | Quality-weighted output with consensus analysis and evidence validation |
| `--complete` | Full raw outputs |
| `--diff` | Show differences between CLI responses |
| `--quality-gate` | Apply 4-Layer Filter System Layer 4 (filters findings by confidence >= 80%) |
| `--output-format json` | Machine-readable JSON output |
| `--timeout N` | Max wait in seconds (default: auto-calculated) |
| `--output-file FILE` | Save JSON output to a datetime-suffixed file |
| `--no-critic` | Skip the post-run ai-cli critic subagent |
| `--meta-critique` | Run cross-agent meta-critique (Phase 2: catch contradictions and blind spots) |
| `--prompt-toolkit` | Use prompting-toolkit AutomaticEnhancementSystem instead of built-in templates |
| `--gemini-only` | Run only gemini-cli |
| `--codex-only` | Run only codex |
| `--pi-m27-only` | Run only pi with minimax/MiniMax-M2.7 |
| `--pi-glm-only` | Run only pi with z-ai/glm-5.1 |
| `--qwen-only` | Run only qwen-cli |
| `--opencode-only` | Run only opencode (DeepSeek V3) |
| `--opencode-model MODEL` | OpenCode model or alias (kimi, minimax) |
| `--route` | Use rule-based routing to select CLI by task keywords |
| `--doc-review` | Use document review prompt — prepends review questions |
| `--hide-prompt` | Suppress the enhanced prompt display |
| `-bash` | Show bash commands instead of executing (debug) |

---

## Two-Phase Workflow

### Phase 1: Parallel Execution
All 4 agents (gemini, codex, pi-m27, pi-glm) run simultaneously, each producing independent analysis.

### Phase 2: Meta-Critique (with --meta-critique)
After Phase 1 results are in, a meta-critique agent reviews all outputs to identify:
1. **Contradictions** — Agent A says X is safe, Agent B says X is risky
2. **Calibration issues** — Similar severity issues rated differently by different agents
3. **Blind spots** — What no agent caught but should have
4. **Precision failures** — What an agent flagged that is actually fine

This mirrors the pre-mortem Phase 2 structure applied to multi-agent LLM output.

---

## Critical Rules

1. **File context MUST use --context flag** — Piped stdin is ignored when auto-context detected
2. **Timeout protection:** Default auto-calculated (180s base + 1s per MB context)
3. **Individual failures don't abort others** — Report which CLIs succeeded/failed
4. **Empty responses are flagged as errors** — Don't silently accept blank output
5. **pi agents use --model provider/model syntax** — e.g., `pi --model minimax/MiniMax-M2.7`

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
| Critic subagent for output sanity checks | `P:/.claude/agents/ai-cli-critic.md` |
