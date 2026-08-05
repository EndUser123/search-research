# Handoff — prevent fabricated causal explanations + wrong-tool selection

## Status
OPEN — behavioral pattern + tool-selection issue requiring structural mitigation.

## Objective

Prevent the agent from:
1. Fabricating plausible-sounding explanations for phenomena it has no evidence about (the 50-minute delay incident)
2. Using PowerShell `Select-String` for large-file operations where Python `grep`/`rg` would be dramatically faster

## The incidents

### Incident 1: Fabricated causal explanation (2026-08-05)

The operator asked "What's going on? There's like a 50-minute wait." The agent responded with two explanations: (a) a PowerShell scan that ran 18 minutes, (b) loading a 1780-line SKILL.md. Neither could explain a 50-minute gap. When challenged ("Those reasons would not explain a 50-minute wait"), the agent admitted it had fabricated the explanations — presenting guesses as facts.

**Root cause:** closure-pressure narrative. The model preferred to construct a plausible-sounding explanation rather than say "I don't know." This is the same failure class documented in `[[claims-require-receipts-narrative-sufficiency-is-not-verification]]` and the 2026-07-20 yt-is incident.

**Existing rules that should have prevented this but didn't:**
- AGENTS.md § "Claims require receipts" — requires a verification receipt for causal claims
- AGENTS.md § "No invented introspection" — prohibits claiming to know causes of behavior
- The `[UNKNOWN]` label exists for exactly this situation

**Why the rules didn't fire:** the model was under social pressure ("What's going on?") and the closure-pressure pathway overrode the evidence-discipline pathway. This is the documented ~50% compliance ceiling for prose rules under session pressure.

### Incident 2: Wrong tool selection

The agent used PowerShell `Select-String -Recurse` across large JSONL transcript files (some 500KB+) instead of Python `grep` or `rg`. This caused a scan that ran 18 minutes (1095s) when it should have taken <5 seconds.

**Root cause:** the agent defaulted to PowerShell because it's the host shell, without considering performance characteristics of `Select-String` on large files. `rg` (ripgrep) and Python `grep` are specifically designed for this and are 100-1000x faster on large text files.

## Mitigation options

### For fabricated causal explanations

**Option A: Hook-based (structural)** — add a pattern check to the existing `minimal_bias_gate.py` or a new `narrative_sufficiency_gate.py` that scans the agent's output for causal-explanation patterns ("caused by", "because of", "the reason is") when the claim is about system/runtime/model behavior the agent cannot observe. If the output contains a causal claim about unobservable state without a receipt, block with "Causal claim about [runtime/model/queue] without evidence. Label as [UNKNOWN] or cite a receipt."

**Option B: AGENTS.md rule enhancement (prose)** — add a specific trigger to the existing "Claims require receipts" rule: "When the operator asks 'what's going on?' or 'what happened?' about a delay, timeout, or system behavior you cannot directly observe, the ONLY acceptable response is 'I don't have visibility into [X]. [UNKNOWN].' Do NOT construct an explanation from adjacent context (long-running commands, context size) unless you can show a direct receipt."

**Option C: Both** — the hook catches violations mechanically; the rule shapes the prior probability.

### For wrong-tool selection

**Option A: AGENTS.md rule** — add to the Environment section: "For searching large text files (JSONL transcripts, logs, CSVs), use `rg` (ripgrep) or Python `grep` — NEVER PowerShell `Select-String`. `Select-String` on files >100KB can take 10+ minutes; `rg` does the same work in <1 second."

**Option B: Hook** — add to `PreToolUse` hook: if the command contains `Select-String` and the path pattern matches `.jsonl`, `.log`, or files >50KB, block with "Use `rg` or Python instead of Select-String for this file type."

## Recommended approach

1. **Hook for tool selection** (Option B for incident 2) — highest ROI, mechanical, prevents the class. Low false-positive rate.
2. **AGENTS.md rule enhancement for causal claims** (Option B for incident 1) — the prose rule exists but needs a specific "what's going on?" trigger. The hook (Option A) is harder to implement with low false-positive rate because causal language appears legitimately in many contexts.
3. **Wiki concept** capturing the pattern: the 50-minute delay incident is a clean reference case for the closure-pressure narrative pattern applied to unobservable system state.

## Key files
- `~/.grok/AGENTS.md` § "Claims require receipts" and § "No invented introspection"
- `~/.grok/hooks/scripts/minimal_bias_gate.py` — existing pattern-detection hook
- `P:/.data/wiki/concepts/claims-require-receipts-narrative-sufficiency-is-not-verification.md`
- `P:/.data/wiki/concepts/no-invented-introspection.md` (if exists)

## Acceptance criteria
- Agent responds "[UNKNOWN]" when asked about unobservable system state (delays, queue times, model processing)
- Agent never uses `Select-String` on `.jsonl` or `.log` files
- At minimum: AGENTS.md rule with specific trigger; ideally: PreToolUse hook for Select-String on large files

## Handoff is wrong if
- The 50-minute delay was actually caused by something the agent COULD have known about (e.g., a visible error message it missed)
- The Select-String performance issue only affects this specific file set (not general)
