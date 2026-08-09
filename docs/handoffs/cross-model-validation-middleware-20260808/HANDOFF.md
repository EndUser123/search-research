# HANDOFF: Orchestrator-controlled cross-model validation for ship-py

## Status
OPEN — design needed

## Objective
Move the LLM out of the evidence-production path for ship-py's review phase by having the orchestrator spawn a cross-family pool model via direct HTTP or Pi subprocess, capture its output, and write the findings from that output. The LLM never touches the findings file.

## Context
- ship-py now has: polling loop, suspicion gates, transition chain, --verdict removal, path validation, canonical findings paths
- The remaining gap: the LLM writes review-findings.json by hand (or relays fabricated agent output). No gate verifies the findings were produced by a real agent. The suspicion gate catches empty findings, but not plausible-but-fabricated ones.
- This handoff closes that gap by removing the LLM from the evidence-production path entirely.
- Singh execution-reality middleware is a SEPARATE work item (P:/docs/handoffs/singh-execution-reality-middleware-20260808/) — it addresses tool-output fabrication, a different failure mode.

## Key design questions
1. **Where does cross-model validation fit in the pipeline?** After the review phase, before the fix phase? Or as a new phase between review and risk?
2. **Which dispatch path for the validator model?** Three options, all orchestrator-controlled (LLM cannot fabricate):
   - **Direct HTTP API call** (fastest, ~10-30s): `requests.post()` to provider endpoint (Cohere, NIM, OpenRouter). Python captures response directly.
   - **Pi harness** (flexible, ~30-60s): `subprocess.run(["pi", "--model", "<slug>", "<prompt>"])`. Accesses full pool with one CLI.
   - **agy/codex subprocess** (proven but slower, ~60-120s): existing CLI paths via `agy_lens.py` or `codex exec`.
   - **Default recommendation: direct HTTP or Pi** — faster, broader model selection, same fabrication-resistance.
3. **Which model for validation?** Any cross-family pool model works. `cohere-command-a-plus` (reasoning lane, 15/19 available) or `nim-openai-gpt-oss-20b` (critic lane, 3/3 available) are current candidates. The model is selected at runtime via `pick_model.py` — no hardcoding.
4. **Cost:** cross-model validation adds one model call per review phase. With direct HTTP or Pi, this is ~10-30s wall-clock and minimal token cost. Justified for every ship-py run.

## Acceptance criteria
- Design document produced via `/design`
- Cross-model validation wired as a new pipeline phase or sub-step, dispatched by the orchestrator (NOT the LLM) via direct HTTP or Pi subprocess
- The orchestrator calls the validator model, captures the response, and writes findings from that response — the LLM never touches the findings file
- Model selected at runtime via `pick_model.py` — no hardcoded slugs
- Tests covering: (a) orchestrator spawns validator and captures real output, (b) fabricated findings from LLM are detected when they disagree with the validator's independent assessment

## References
- `P:/.data/wiki/concepts/making-llm-agents-honestly-execute-skills-solution-stack.md` — solution families with evidence
- `P:/.data/wiki/concepts/specification-gaming-in-llm-agent-pipelines.md` — diagnosis
- P:/docs/handoffs/singh-execution-reality-middleware-20260808/ — separate work item for tool-output fabrication

## Suggested next invocation
```
/go Read P:/docs/handoffs/cross-model-validation-middleware-20260808/HANDOFF.md and implement it. Start with /design for the cross-model validation phase — the orchestrator spawns a pool model via direct HTTP or Pi subprocess (NOT via the LLM), captures the response, and writes findings from it. This removes the LLM from the evidence-production path. Use pick_model.py for runtime model selection.
```
