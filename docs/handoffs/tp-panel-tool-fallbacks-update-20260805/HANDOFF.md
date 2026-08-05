# Handoff — /tp panel tool-fallbacks update

## Status
OPEN — evidence captured, implementation deferred.

## Objective

Update `[[tool-fallbacks]]` (`P:/.data/wiki/concepts/tool-fallbacks.md`) with
three new failure signatures observed during a `/tp critic` parallel panel run
on 2026-08-05. The panel had a 1/3 return rate — only the OpenRouter fallback
(`or-ling-3-flash-free`) returned a critique; the other two lenses failed with
new failure modes not yet in the fallbacks table.

## Evidence (from session 019fd276)

### Failure 1: DeepSeek serialization error on spawn_subagent

- **Model:** `nim-deepseek-ai-deepseek-v4-flash`
- **Access path:** `spawn_subagent(model="nim-deepseek-ai-deepseek-v4-flash", ...)`
- **Error:** `serialization error: invalid type: null, expected u32 at line 1 column 327`
- **Duration:** 43.5s, 8 tool calls, 2 turns before failure
- **Context:** /tp critique prompt (~113K input tokens including AGENTS.md + skill bodies)
- **Classification:** STRUCTURAL — serde format incompatibility on tool-grounded spawn.
  Same error class as nemotron (`null, expected u32`). The model's tool-call
  response contains a null where the Grok Build deserializer expects a u32.
- **Conflict with existing entry:** the tool-fallbacks table currently says
  this model is "VERIFIED WORKING 2026-08-04" based on a PROBE_OK test.
  The probe was a trivial 1-token no-tool spawn. The /tp prompt was
  tool-grounded (113K tokens, file reads, grep). This is the same
  false-positive class as `[[serde-broken-false-positive-sweep-20260801]]`:
  probes pass, real prompts fail.
- **Workaround:** do not spawn for tool-grounded critique. Use as direct
  API target or CLI invocation. For /tp panels, use `or-ling-3-flash-free`
  as the spawn lens instead.

### Failure 2: Codex 600s timeout on deep preflight

- **Model/CLI:** `codex exec --json --ephemeral -s read-only -m gpt-5.6-luna`
- **Access path:** `codex exec` via `run_terminal_command(background=true)`
- **Symptom:** timed out at 600s (10 min wall clock). Was still running preflight
  (`discovery_audit.py` with 20K file scope) when killed. 480 lines of JSON
  output captured, mostly intermediate tool-call logs — no final critique
  produced.
- **Context:** codex auto-loaded its `review-packet-runner` skill which mandates
  preflight before review. The preflight scope (6 `--scope` args, 8 `--target`
  args, 20K file limit) was appropriate for a full code review but excessive
  for a /tp critique of 2 files.
- **Classification:** TRANSIENT (context-dependent) — codex's own skill triggered
  an expensive preflight that exceeded the timeout. Not a codex bug; a scope
  mismatch between /tp's critique context and codex's review-packet-runner
  defaults.
- **Workaround:** for /tp via codex, either (a) increase timeout to 900s+,
  (b) pass a narrower scope hint in the prompt, or (c) skip codex for /tp
  and rely on spawn + agy.

### Failure 3: AGY headless zero-output (known pattern, recurred)

- **Model/CLI:** `agy "Read P:\tmp\tp-agy-bundle.md and provide the critique specified inside."`
- **Access path:** bare `agy` invocation via `run_terminal_command(background=true)`
- **Symptom:** 0 bytes stdout, 0 bytes stderr, timed out at 600s
- **Context:** the `tp_dispatch.py --cli agy` output WAS generated correctly
  (includes `-p`, `--dangerously-skip-permissions`, `--print-timeout 10m`,
  `--output-format json`), but the orchestrator ran the bare command printed
  in the CMD field instead of constructing it with the mandatory flags.
- **Classification:** STRUCTURAL (already documented) — same as existing entry:
  "Silent 0-output, exit 0, 0 bytes" / Issue #76. This is a recurrence, not
  a new failure. The existing entry says "Run the tp_dispatch.py-printed
  command verbatim" — which was not done.
- **Workaround:** already documented. No new entry needed — this is a
  compliance failure, not a new signature. The operator should know the
  existing entry recurred.

## What to update in tool-fallbacks.md

1. **Add DeepSeek serde entry** to "spawn_subagent exclusions" table. Mark
   as STRUCTURAL. Note the conflict with the existing "VERIFIED WORKING"
   entry — that verification was probe-only, not tool-grounded. Recommend
   re-testing criteria: "Re-test after: Grok Build serde update OR
   deepseek-v4 model revision. Probe is insufficient — must test with
   tool-grounded prompt (≥50K tokens, ≥3 tool calls)."

2. **Add Codex deep-preflight timeout** to a new "CLI context-mismatch"
   subsection (or to the existing "CLI caller errors" table). Mark as
   TRANSIENT (context-dependent). Note: codex's review-packet-runner skill
   triggers expensive preflight that exceeds /tp's 600s timeout. Workaround:
   narrower scope hint or longer timeout.

3. **AGY recurrence:** no new entry needed — already documented. Optionally
   add a note to the existing entry: "Recurred 2026-08-05 when orchestrator
   bypassed tp_dispatch.py output."

4. **Update the "VERIFIED WORKING" DeepSeek entry** to "VERIFIED WORKING
   (probe only) — tool-grounded spawn fails with serde error (2026-08-05)."

## Key files

- `P:/.data/wiki/concepts/tool-fallbacks.md` — the file to update
- `~/.grok/skills/tp/SKILL.md` § Step 2 — the spawn pool table (may need
  DeepSeek removed from the /tp default panel)
- Session transcript: `C:/Users/brsth/.grok/sessions/P%3A%5C/019fd276-ca8e-7e41-a577-3bca37004725/`

## Handoff is wrong if

- The DeepSeek entry is added without noting the probe-vs-tool-grounded distinction
- The Codex entry is classified as STRUCTURAL (it's context-dependent, not a bug)
- The AGY recurrence is treated as a new failure rather than a compliance lapse
