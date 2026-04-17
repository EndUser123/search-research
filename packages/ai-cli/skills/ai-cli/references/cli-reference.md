# CLI Reference

## CLI Characteristics

| CLI | Speed | Best For |
|-----|-------|----------|
| qwen | Fastest (~63s) | Code gen, debugging |
| gemini | Medium (~160s) | Concise answers |
| codex | Fast | Code reviews |
| vibe | Fast | Python tasks |
| opencode | Fast | Alternative perspectives |
| glm-4.7-flash | Fast (~60s API) | Additional perspective (requires ZAI_API_KEY) |

## OpenCode Zen Models

OpenCode Zen provides access to specialized models via model aliases:

| Alias | Model | Use Case |
|-------|-------|----------|
| `kimi` | Kimi K2.5 TEE | Long context (256K), multimodal, agent swarm, large codebase analysis |
| `minimax` | MiniMax M2.1 TEE | SOTA coding (74% SWE-bench), code generation, debugging, optimization |

**Usage:**
```bash
# Use alias instead of full model ID
/ai-cli "analyze this large codebase" --opencode-model kimi

# Full model ID also works
/ai-cli "review this code" --opencode-model "chutes/MiniMaxAI/MiniMax-M2.1-TEE"

# Note: Model IDs use exact case from chutes provider:
# - kimi: chutes/moonshotai/Kimi-K2.5-TEE (lowercase moonshotai)
# - minimax: chutes/MiniMaxAI/MiniMax-M2.1-TEE (uppercase MiniMaxAI)
```

**Model Details:**
- **Kimi K2.5**: 256K context, native multimodal, tool calling, free open-weight
- **MiniMax M2.1**: 74% SWE-bench Verified, multilingual coding, agentic workflows

## Setup

**External CLIs** (install separately):
```bash
npm install -g qwen-code gemini-cli @openai/codex opencode-ai @mistralai/vibe
```

**Environment Variables:**
- `CHUTES_API_KEY` - Required for opencode
- `ZAI_API_KEY` - Optional, enables glm-4.7-flash in default execution

## Health Check CLI

```bash
# Check CLI tool availability
python "P:\.claude\skills\ai-cli\scripts\cli.py" list

# Check with sanity test (runs actual CLI commands)
python "P:\.claude\skills\ai-cli\scripts\cli.py" health --sanity

# Check specific CLI
python "P:\.claude\skills\ai-cli\scripts\cli.py" health --cli qwen
```

**Health checks:**
- Environment variables (CHUTES_API_KEY, ZAI_API_KEY)
- CLI installations (qwen-code, gemini-cli, codex-cli, vibe, opencode-ai)
- Optional sanity test (runs actual CLI with --version flag)

**Exit codes:** `0` = healthy, `1` = failed

## Known Limitations

**OpenCode Very Large Models (MiroThinker 235B, Nemotron Nano 30B):**

These models may return `[No output]` when invoked through `/ai-cli` due to:
- Extremely slow response times (5+ minutes for simple queries)
- Output streaming behavior that doesn't interact well with Python async subprocess PIPE on Windows

**Workaround:** Invoke these models directly via the opencode CLI:
```bash
opencode run -m "chutes/miromind-ai/MiroThinker-v1.5-235B" "your query here"
```

**Affected models:**
- `miro` (MiroThinker v1.5 235B)
- `nano` (NVIDIA Nemotron 3 Nano 30B)

**Unaffected models:** kimi, minimax, and all other CLIs work correctly through `/ai-cli`.

---

## Workflow Patterns

These patterns encode multi-agent orchestration techniques drawn from adversarial debate and autonomous loop research.

### Pattern 1: Adversarial Debate

Run multiple CLIs in parallel to surface disagreement between models — useful when you need to identify which approach has flaws.

```bash
/ai-cli "should I refactor X or replace it?" --aggregate --diff
```

**How it works:** `--aggregate` pools all CLI outputs; `--diff` highlights where CLIs disagree. Disagreement flags a decision point, not a bug.

**Use when:** Unclear which approach is correct, multiple reasonable options exist, or you want to catch subtle flaws before committing.

**Example:** "architectural decision: event-driven vs polling" → CLAs disagree → you investigate the disagreement.

### Pattern 2: Ralph-Loop (Autonomous Refinement)

Iterative CLI calls that feed output back as next input, bounded by timeout. Terminates when CLIs converge or timeout fires.

```bash
/ai-cli "fix the bug" --timeout 60
# Output becomes context for next call
/ai-cli "now apply that pattern to the other files" --timeout 60
```

**How it works:** Each iteration refines the output. Use `--summary` for faster iterations, `--complete` when you need full detail.

**Use when:** Large refactor across many files, architectural migration, or iterative improvement where each step builds on the last.

**Integration:** For stateful autonomous loops (Ralph pattern), see `/ralph` skill — it handles exit detection, state management, and loop bounding.

### Pattern 3: TDD Cycle (Red-Green-Refactor)

Use quality-gated output as a red-phase signal, then validate with a fresh prompt.

```bash
# Red: Get test failures via quality gate
/ai-cli "what tests will fail if I rename this function?" --quality-gate --summary

# Green: Apply the change, then verify
/ai-cli "I made the change. Which tests now pass?" --aggregate

# Refactor: If both pass, proceed
/ai-cli "the tests pass. Suggest cleanups that don't change behavior."
```

**How it works:** `--quality-gate` filters to high-confidence findings (confidence >= 80%). This reduces noise in the red phase.

**Use when:** Risky refactors, API changes, or any situation where you want test coverage before committing to a change.

---

## Cross-Skill References

| Pattern | Supporting Skill |
|---------|----------------|
| Autonomous loop state management | `/ralph` |
| Adversarial debate (multi-agent) | `/ai-cli --aggregate --diff` |
| TDD cycle (test-first) | `/ai-cli --quality-gate` |
| Codex single-task forwarder | `codex:codex-rescue` |
| Multi-provider API orchestration | `/ai-api` |
