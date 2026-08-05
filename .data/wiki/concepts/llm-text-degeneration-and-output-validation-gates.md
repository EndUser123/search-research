---
title: "LLM text degeneration and output validation gates: connecting decoder loop research to our ship-py checkpoint pattern"
created: 2026-08-05
source: session-019fcd47 (/why analysis of architecture agent degeneration + /www research verification)
sources:
  - https://arxiv.org/html/2512.04419v1 (Wang et al. 2025, "Solving LLM Repetition Problem in Production")
  - https://sebastianraschka.com/faq/docs/repetition-loops-generation.html (Raschka, practitioner explanation)
  - https://agentpatterns.ai/security/improper-output-handling-downstream-sinks/ (AgentPatterns.ai, output validation)
  - Holtzman et al. 2020, "The Curious Case of Neural Text Degeneration" (ICLR)
  - Su et al. 2022, arxiv 2206.02369, "Learning to Break the Loop"
tags: [llm-degeneration, decoder-loop, output-validation, agent-failure-modes, ship-py, transferable-pattern, code-orchestrates-model-judges]
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
summary: >
  LLM agents can produce degenerate output (token repetition loops) that
  technically returns exit 0 with non-empty content but contains no usable
  information. This is a well-documented phenomenon called "neural text
  degeneration" or "decoder loop" — caused by self-reinforcement in
  autoregressive generation where repeated tokens increase their own
  future probability. The fix is not at the model level (we don't control
  decoding parameters on Grok Build) but at the orchestration level:
  output validation gates that check for expected artifacts before
  treating agent output as successful. Our ship-py orchestrator already
  implements this pattern (file existence + JSON schema validation at
  lines 189-206). The gap was not missing code — it was the LLM
  skipping the pipeline checkpoint that invokes the validator.
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: complements
  - target: wiki/concepts/transient-model-errors-vs-serde-incompatibility
    type: extends
  - target: wiki/concepts/scanner-regex-scope-discipline
    type: related
  - target: wiki/concepts/replacement-before-investigation-pattern
    type: related
---

# LLM text degeneration and output validation gates

## The phenomenon

LLM agents can enter **decoder loops** — self-reinforcing repetition where
each generated token increases the probability of the same token appearing
again. The output is technically non-empty (the agent "produced content")
but contains no usable information: a single word or phrase repeated until
max_tokens forces termination.

This is not a bug in any specific model. It is a well-studied property of
autoregressive text generation:

- **Holtzman et al. 2020** (ICLR): greedy and beam-search decoding reliably
  enter repetition loops. First documented for GPT-2, applies to all
  autoregressive LLMs.
- **Wang et al. 2025** (arxiv 2512.04419): 75-80% reproduction rate in
  production batch processing. Three identified patterns: business rule
  repetition, method-call repetition, syntax repetition.
- **Raschka**: "every generated token becomes part of the context for the
  next prediction. Once a phrase is repeated, the new context may assign
  even more probability to another copy."

## The mechanism (why it happens)

Per Wang et al.'s Markov model analysis:

1. **Context repetition → probability enhancement**: when context contains
   repeated patterns, the model assigns higher probability to tokens that
   appeared previously (shortcut: copy from recent history).
2. **Self-reinforcement effect**: the probability of repetition increases
   monotonically with the number of historical repetitions. Once the loop
   starts, it gets stronger.
3. **High initial probability reinforcement**: sentences with higher initial
   probability exhibit stronger self-reinforcement.

**Contributing factors** (per Raschka):
- Greedy or highly constrained decoding (low temperature, small top-k)
- Repetitive prompt structure (lists, tables, similar formatting patterns)
- Exposure bias (training on ground-truth tokens, generating on own tokens)

## What we observed (session 019fcd47)

A /ship-py review agent spawned to evaluate /todo skill architecture produced
degenerate output: the word `scope.` repeated hundreds of times inside
`<think>` tags, consuming the output budget. The agent's 14 tool calls
completed normally (read_file, run_terminal_command) — the degeneration
happened only in the final text generation step. The expected JSON output
file was never created.

**Likely contributing factor [INFERENCE]:** the review prompt included
/tp SKILL.md (1,750 lines of repetitive table/section formatting). While
context utilization was only 9%, the *structural repetition* in the input
may have created a local context where self-reinforcement could take hold.
This aligns with Raschka's note: "A prompt ending with an unfinished list
may encourage the model to keep adding similarly shaped items."

## The fix: output validation gates

The fix is not at the model level (we don't control decoding parameters on
Grok Build spawn_subagent). The fix is at the **orchestration level**:
validate that agents produced their expected output before treating them
as successful.

### Industry standard (AgentPatterns.ai)

> "Treat agent output as untrusted input to the next system — every
> downstream sink needs its own per-sink validation gate."

### Our implementation (ship_orchestrator.py lines 189-206)

The ship-py orchestrator already implements this:

```python
# 1. Check file exists
findings_path = Path(args.findings_file)
if not findings_path.exists():
    return error

# 2. Check file is valid JSON
findings = json.loads(findings_path.read_text())

# 3. Check schema (required keys exist)
for required_key in ("bugs", "risks", "suggestions"):
    if required_key not in findings:
        return error
```

This catches all three failure modes:
- Agent produced degenerate output → file never written → gate fires
- Agent produced empty output → file doesn't exist → gate fires
- Agent produced wrong format → JSON parse fails → gate fires

### The gap was not missing code

The validation exists. The gap was that **the LLM (me) skipped the pipeline
checkpoint** — I noted "1/2 agents returned" and moved on, instead of
running `ship_orchestrator.py review --findings-file <path> --agent-count 2
--failed-count 1`. The validator would have caught the missing file
immediately and triggered retry-with-fallback.

This is the [[replacement-before-investigation-pattern]] at the process
level: I claimed "the completion validator doesn't exist in the workspace"
without reading the code that implements it. The fix was already there.

## When this pattern applies

| Scenario | Validation gate |
|----------|----------------|
| Spawned agent expected to write JSON | Check file exists + parseable + schema-valid |
| Spawned agent expected to modify files | Check git diff shows expected changes |
| Spawned agent expected to return text | Check output is non-degenerate (not just non-empty) |
| CLI tool expected to produce stdout | Check exit code + non-empty stdout + parseable format |

## Known solutions (from Wang et al. 2025)

For deployments where you DO control decoding parameters:

| Solution | Scope | Effectiveness |
|----------|-------|---------------|
| Beam Search with `early_stopping=True` | Universal (all repetition types) | 0% repetition rate |
| `presence_penalty=1.2` | Task-specific (business rule repetition) | Effective for one pattern |
| DPO fine-tuning | Universal (model-level) | Effective but costly (15-18 GPU hours) |

On Grok Build, we don't control spawn_subagent decoding parameters, so the
orchestration-level validation gate is our primary defense.

## Process lesson

The real failure this session wasn't the decoder loop — that's a known,
transient, stochastic event. The real failure was:

1. I didn't invoke the existing pipeline checkpoint
2. When asked about the pattern, I claimed it didn't exist without reading
   the code
3. The operator spent 3 turns correcting me

The structural fix: **always invoke the orchestrator's review subcommand
after spawning agents** — don't manually decide "1/2 returned, good enough."
Let the code validate.

## Cross-references

- [[code-orchestrates-model-judges-skill-scale]] — the gate-enforcement principle this applies
- [[transient-model-errors-vs-serde-incompatibility]] — classifying model failures (this is a generation pathology, not a serde error)
- [[replacement-before-investigation-pattern]] — the process failure of claiming absence without checking
- [[scanner-regex-scope-discipline]] — related pattern: mechanical validators must be precise
