---
title: "Tool-failure cascading error modes on retry — when re-running hides the real bug"
created: 2026-08-01
source: session-019fbf02-d3dd-7f72-9ad2-4538790c0a82
tags: [tool-failure, validator, retry, output_validator, reference_loader, error-cascade, debugging]
summary: >
  When a tool fails with a runtime error, retrying it often surfaces a DIFFERENT
  error each pass — and the third error usually has nothing to do with the
  original failure. Observed pattern from session 019fbf02: output_validator
  produced ValueError, then AttributeError on a result-method, then TypeError
  on iterating that method — three different errors, same root cause. The
  lesson: stop retrying after the second distinct error and inspect the
  upstream contract; the validator is not the bug.
agent: grok
host: grok
cognitive_load: 2
verification: observed
tier: warm
relations:
  - target: wiki/concepts/serde-broken-false-positive-sweep-20260801.md
    type: extends
  - target: wiki/concepts/close-runner-json-arg-parsing-bug.md
    type: extends
  - target: wiki/concepts/tool-fallbacks.md
    type: related
  - target: wiki/concepts/harvest-cli-not-on-path.md
    type: related
---

# Tool-failure cascading error modes on retry — when re-running hides the real bug

## Decision context

**Why this concept was needed:** during session 019fbf02 close-check Phase 2, an AAR validation pass against a downstream subagent's output surfaced three different errors across three retries, each seemingly unrelated to the prior:

| Pass | Error | Apparent message |
|---|---|---|
| 1 | `ValueError` | `no structured JSON block found in P:\\.artifacts\\grok-aar\\...\\aar-report.md; expected <!-- AAR_JSON: {...} --> or a ```json fence` |
| 2 | `AttributeError` | `ValidationResult object has no attribute errors` |
| 3 | `TypeError` | `object of type method has no len()` |

The natural operator reaction is "the validator is broken" — but the validator isn't the bug. The actual problem is upstream: the downstream agent produced output in a schema the validator doesn't recognize. The cascading errors are a side-effect of the validator's own defensive code attempting to handle the malformed input.

The same shape appeared in two other tools this session:
- `reference_loader.py --trigger cross_model_audit` → `usage: reference_loader.py [-h] [--trigger TRIGGER] / reference_loader.py: error: unknown trigger(s): cross_model_audit`. The `--trigger` argument was a name not in the SKILL.md trigger table.
- `harvest` → `harvest: The term harvest is not recognized as a name of a cmdlet...`. The CLI was not on PATH; Python module is.

All three are the **same structural failure**: a tool received a contract-violating input, and the failure mode that surfaces is tool-specific (ValueError vs argparse vs PowerShell PATH) but the underlying cause is "caller and callee don't share a contract."

## The pattern

When a tool invocation fails:

1. **First failure**: usually describes the contract violation cleanly (e.g., "no JSON block found," "unknown trigger," "command not found"). The tool has a defensive branch that catches this and raises an informative error.
2. **Second failure (after retry/patch)**: a different error class, often `AttributeError` or `KeyError`. The first retry's fix introduced a new code path that itself has a bug — the validator's defensive code tries to inspect the result and the result doesn't have the expected attribute.
3. **Third failure**: another different class, often `TypeError`. The retry chain has now drifted far enough from the original that the third error is essentially debugging the validator, not the original problem.

The trap is that **the operator can spend hours "fixing" the validator** while the upstream contract violation persists. Each retry that produces a new error makes the original failure less visible in the operator's mind ("now it's a TypeError, was a ValueError before, must be a different bug"), but it's the same bug surfacing through different defensive paths.

## What this means for our workspace

### Detection rule (for operators / future agents)

If a tool invocation produces:
- Error class A, then
- Error class B (different from A), then
- Error class C (different from A and B)

…across three retries, **stop retrying**. The errors are not three bugs; they are three surface forms of one upstream contract violation. The fix is upstream (the caller or the input), not in the tool being retried.

### Fix order

1. **Read the FIRST error carefully.** It almost always names the contract violation directly ("no JSON block," "unknown trigger," "command not found"). The first error is the most informative.
2. **Trace back to the caller.** What did the caller pass? Where did the caller get it? The contract violation happened between caller and callee.
3. **Patch the caller, not the callee.** For `output_validator`, the fix is to teach the downstream agent to emit the expected JSON block (or to make the validator more lenient). For `reference_loader`, the fix is to add the trigger name to the SKILL.md trigger table, OR use one of the existing triggers. For `harvest`, the fix is `python -m harvest.cli` or to add harvest to PATH (see [[harvest-cli-not-on-path]]).
4. **Verify with a clean run, not another retry.** If the third error is opaque, re-invoke from scratch with a known-good input to confirm the tool works correctly when given a contract-conforming argument.

### Pre-flight heuristic (for `/aar` and similar)

Before invoking a downstream validator, run a pre-flight check that the input conforms to the expected schema:

- For `output_validator` → confirm the agent's output contains `<!-- AAR_JSON: {...} -->` or a ` ```json ` fence before invoking the validator.
- For `reference_loader` → grep the SKILL.md for the trigger name first; if not present, the caller is using an outdated or hallucinated trigger.
- For `harvest` → check `where.exe harvest` first; if not on PATH, use `python -m harvest.cli` directly.

This pattern is already documented for one tool (`harvest-cli-not-on-path` § "Structural fix") and should be extended to all CLI validators in the workspace.

## Connections to existing concepts

- **[[serde-broken-false-positive-sweep-20260801]]** — the same shape at the model-routing layer. A tool reports "broken" because of an arg-shape mismatch, not because the tool itself is broken. The validator-failure cascade is the per-tool instance of the broader "tool reports failure when the contract is violated" pattern.
- **[[close-runner-json-arg-parsing-bug]]** — close_runner received a JSON literal as a path string and crashed with `WinError 123`. The runner wasn't broken; the dispatcher violated the contract. Same fix-order rule: patch the caller (dispatcher extracts `session_id` first), not the runner.
- **[[harvest-cli-not-on-path]]** — same structural pattern: caller expects a CLI on PATH, CLI isn't there, surface error is "command not recognized" instead of "PATH missing." Fix-order rule applies: fix the invocation (`python -m`) or fix the environment (add to PATH).
- **[[tool-fallbacks]]** — when a tool is genuinely broken (rate limit, missing model, etc.), the fallback policy applies. But when a tool is "broken" because of a contract violation, the fix is upstream, not a fallback. Distinguish carefully.

## Falsifier

This pattern is wrong if:
- A tool genuinely has a bug that surfaces different errors on different runs (unrelated to input contract) → the cascade is the tool, not the contract. Test: re-invoke with known-good input; if the same cascading errors persist, the tool is broken.
- The first error is uninformative (e.g., `RuntimeError: ` with no message) and the second error is more informative than the first → the cascade is informative, not cascading. Test: read the second error before assuming the first is canonical.
- The caller is reading tool output from a cache (previous run's output) → the contract violation happened in the past, not now. Test: invalidate cache, re-run from clean state.

## Evidence

The specific three-error cascade in session 019fbf02 close-check Phase 2 was captured in chat_history.jsonl lines corresponding to "friction raw evidence" subsection (d, e, f):

- (d) output_validator first pass: `ValueError: no structured JSON block found in P:\\.artifacts\\grok-aar\\...\\aar-report.md; expected <!-- AAR_JSON: {...} --> or a ```json fence`
- (e) output_validator second pass: `AttributeError: ValidationResult object has no attribute errors`
- (f) output_validator third pass: `TypeError: object of type method has no len()`

Reference error in same session:
- `reference_loader.py --trigger cross_model_audit` → `usage: reference_loader.py [-h] [--trigger TRIGGER] / reference_loader.py: error: unknown trigger(s): cross_model_audit`. Trigger name not present in the SKILL.md trigger table at `~/.grok/skills/aar/SKILL.md`.

`harvest` PATH error in same session:
- `where.exe harvest` returned `INFO: Could not find files.` Direct directory inspection confirmed the obligation store is intact at `P:/.data/harvest/{pending,triaged,events,claims}/` but the CLI driver is not on PATH. See [[harvest-cli-not-on-path]] for full context.

The pattern generalizes from these three observations: when a tool surfaces a different error class on each retry, the underlying cause is a contract violation between caller and callee, not three independent bugs.

## Auto-related

- [[router-proxy-tool-calling-normalization-patterns]]
- [[model-tool-calling-capability-matrix]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[skill-catalog]]

