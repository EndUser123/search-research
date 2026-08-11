---
title: "Tool-evidence gap — HTTP code generation success does not certify agent-harness tool-loop capability"
created: 2026-08-11
source: session-019fdf47
tags: [tool-evidence, pool-test, pi-dispatch, http-vs-agent, model-certification, r5g, nemotron]
summary: >
  Empirical confirmation that a model scoring 18/18 on code generation via
  direct HTTP API can score 0/18 via the PI agent harness. The agent harness
  changes output format (prose-prefixed code vs bare function definitions),
  causing 50% wrong_format failures. This validates the R5g tool-evidence
  requirement: tool-loop capability requires method-specific evidence.
agent: grok
host: grok
cognitive_load: 2
verification: observed
---

# Tool-evidence gap — HTTP ≠ agent-harness

## Decision context

The fleet needed to certify models for tool-loop capability (coding under an agent harness). The question: does a high HTTP code-generation score certify the model for production tool-loop use? If yes, HTTP-only testing is sufficient. If no, every tool-loop model needs PI/opencode method testing.

## Empirical evidence

**Model:** `nvidia/nemotron-3-super-120b-a12b`

| Method | Score | Dominant failure | Latency |
|--------|-------|-----------------|---------|
| HTTP (direct API) | **18/18 (100%)** | — | avg 15s/problem |
| PI (agent harness) | **0/18 (0%)** | 9× wrong_format, 4× wrong_logic, 3× timeout | avg 180s/problem |

The PI agent harness wraps the model in a system prompt with tool schemas, thinking mode (`--thinking medium`), and session management. This changes the model's output format: instead of returning a bare function definition, the model returns prose-prefixed code ("I've created a simple Python program...") that the scorer can't parse.

## Root cause of the format gap

The PI harness adds:
1. **System prompt** — instructs the model to be helpful/conversational
2. **Tool schemas** — JSON tool definitions that change the model's attention
3. **Thinking mode** — `--thinking medium` generates reasoning tokens before output
4. **Session context** — PI wraps each call in an agent session

The HTTP path sends a bare user message + system prompt directly to the completion endpoint. No tools, no session, no thinking mode. The model outputs exactly what's asked.

## What this means for our workspace

**HTTP scores overestimate tool-loop capability.** A model promoted to `active` for coding based on HTTP evidence alone may fail 100% of production tool-loop tasks.

The fleet promotion pipeline now has two evidence cohorts:
- **HTTP cohort** (calibration-tool-loop): standalone code generation — fast, cheap, sufficient for "can this model write code?"
- **PI/opencode cohort** (calibration-tool-loop with method=pi): agent-harness code generation — slow, expensive, required for "can this model work in an agent loop?"

**The R5g contract (shared with Codex) requires method-specific evidence for tool-loop promotion.** HTTP evidence alone cannot clear a thinking-enabled quality gate. See `docs/designs/2026-08-08-common-model-selection-policy-for-codex-and-grok.md` § "Tool-evidence requirement for tool-loop capability."

## Falsifier

This finding is wrong if:
- The 0/18 PI score was entirely infrastructure failure (binary resolution, timeout) rather than format mismatch. **Partially falsified:** 3/18 were timeouts, but 13/18 were format/logic failures — the model produced output, just in the wrong shape. The format gap is real.
- A prompt engineering fix (e.g., "return ONLY the function, no explanation") closes the gap. If adding output format instructions to the PI system prompt brings PI scores to ≥15/18, the gap is prompt-fixable, not a capability gap.

## What to do next

1. **Test the prompt-fix hypothesis** — add "Return ONLY the Python function definition. No explanation, no prose." to the PI system prompt and re-run. If scores improve to ≥15/18, the gap is prompt-level.
2. **Score the scorer** — verify the sandboxed scorer correctly extracts code from markdown fences when they ARE present (some PI outputs may have ```python blocks that the scorer misses).
3. **Method-aware promotion gate** — add a check in `promote_models.py` that requires at least 5 PI/opencode verified successes for tool-loop lane promotion, not just HTTP evidence.

## Receipts

- HTTP evidence: `pool_test.py --provider nvidia --capability tool-loop` (18/18, commit `260c63e`)
- PI evidence: `pool_test.py --model nvidia-nemotron-3-super-120b --capability tool-loop --method pi` (0/18, this session)
- Failure breakdown: 9× wrong_format, 4× wrong_logic, 3× pi_timeout, 1× syntax_error, 1× empty
- R5g contract: `P:/docs/designs/2026-08-08-common-model-selection-policy-for-codex-and-grok.md` § "Tool-evidence requirement"

Related: [[shared-dispatch-component-deep-module-pattern]], [[diagnostic-logging-by-default-in-fleet-tooling]], [[model-tool-calling-capability-matrix]]

## Auto-related

- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[skill-catalog]]
- [[claude-code-skills-and-mcp-integration]]
- [[context-management-in-claude-code]]

