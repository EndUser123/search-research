---
title: "Close verification evidence is scope-specific, not a universal stale-read"
created: 2026-07-25
source: session-019f96f5
tags: [skill-design, close-scanner, stale-read, subagent-transcript-visibility, verification, false-gap, cross-host]
summary: >
  When /close runs after /check, the close scanner (close_accounting.py)
  reports a verification gap even when /check verifier receipts exist. The
  original gap was scope-limited: the scanner inspected parent-transcript
  command evidence, while child verifier commands were recorded in durable
  check-state artifacts. The same session also had a real test-suite gap:
  its six verifiers performed static/git/citation checks, not pytest. The
  corrected rule is therefore: /check PASS proves only the verifier concerns
  covered by that receipt; it does not prove tests or live acceptance. The
  current close scanner reads both parent-transcript evidence and
  session-bound check-state.md receipts, then leaves static-vs-live
  interpretation to the close gate.
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
sources:
  - session-019f96f5 (close run 1 + run 2, both at P:\.artifacts\console_9f93f0d3-0b5b-4985-b779-6a2c\grok-check\)
  - C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py (scanner implementation — greps parent transcript)
  - P:\.grok\skills\check\SKILL.md (Step 0.5: "signals are observations, not verdicts")
relations:
  - target: wiki/concepts/check-vs-review-complementary-not-redundant.md
    type: related — both involve /check's verifier transcripts being invisible to other systems
  - target: wiki/concepts/close-auto-invokes-aar.md
    type: related — both about /close scanner limitations (that one: missing dirty_age check; this one: missing /check receipts)
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build.md
    type: complements — both about the gap between "scanner reports" and "ground truth"
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md
    type: documented-by — source inspection is required before making this mechanism claim durable
---

# Close verification evidence is scope-specific, not a universal stale-read

## Decision context

## Receipts

- `C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py` — `scan_check_receipts()` and `_scan_implicit_verification()`.
- `P:\.artifacts\console_9f93f0d3-0b5b-4985-b779-6a2c\grok-check\20260725-143315-606\check-state.md` — `CHECK PASS (3/3 verifiers PASS)`.
- `P:\.artifacts\console_9f93f0d3-0b5b-4985-b779-6a2c\grok-check\20260725-145841-524\check-state.md` — `CHECK PASS (3/3 verifiers PASS)`.

**Receipts for this concept's mechanism claim (verified 2026-07-25 after operator pushback):**
- `C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py`: `_scan_implicit_verification()` reads the parent `chat_history.jsonl`; `scan_check_receipts()` reads session-bound `/check` state files.
- The parent-transcript patterns are test/validation commands and edit-then-verify; they do **not** include `git show`, `Select-String`, or `qmd`.
- The mechanism claim in this concept ("scanner can't see /check subagent transcripts") is therefore VERIFIED, not inferred.

**Receipts for the worked example (session 019f96f5):**
- Both `/check` run dirs exist with `check-state.md` files: `P:\.artifacts\console_9f93f0d3-0b5b-4985-b779-6a2c\grok-check\20260725-143315-606\` and `...20260725-145841-524\`
- Verifier command receipts: `git show --stat`, `Select-String`, `Compare-Object` (body diff), `qmd search`, transcript greps
- **Honest limitation:** no verifier ran `pytest` — see the worked-example section's caveat.

**Why this concept was needed:** session 019f96f5 ran `/check` twice (6 verifier subagents total, 6/6 PASS), then `/close`. The close scanner reported `VERIFICATION_GAP: code modified but no verification command run (52 commits)`. The operator pushed back — "explain this clearly" — because the gap contradicts the receipts from the two /check runs.

The explanation surfaced a structural evidence boundary: the parent transcript and child-verifier receipts are different evidence sources. The current scanner joins the durable `/check` receipt, but the close gate still must distinguish static verifier coverage from test-suite and live/runtime acceptance.

## The mechanism

### What the close scanner checks

`close_accounting.py` detects parent-transcript verification from test/validation command tokens and edit-then-verify structure. It does not infer verification from prose or from a `/check` invocation alone.

It separately reads `P:\.artifacts\<terminal>\grok-check\**\check-state.md`, matches the current session ID, and records `/check` PASS/FAIL and verifier counts. That receipt is scope evidence, not a blanket test or live-runtime receipt.

### What /check actually does

`/check` spawns verifier subagents with `capability_mode: "execute"`:

```
spawn_subagent(
    description="Verify: <concern>",
    subagent_type="general-purpose",
    capability_mode="execute",
    background=True,
    prompt=<verifier prompt>,
)
```

The verifiers run their own commands (e.g., `git show`, `Select-String`, body-diff, `qmd search`, and where the concern is code correctness, `pytest`/`ruff`/`pyright`) — but **inside their own subagent transcripts**, not the parent's.

### What the parent transcript records

The parent transcript shows only:
1. The `spawn_subagent(...)` tool call
2. The final returned verdict (PASS/FAIL) when `get_command_or_subagent_output` resolves

It does NOT show the verifier's actual command receipts. Those live in the subagent transcript, which the close scanner does not traverse.

### The consequence

Before the receipt integration, `/check` child work was invisible to the parent-transcript scan. After the integration, `/close` can see the verifier verdict, but it still cannot assume that a PASS covered pytest or live behavior. The correct interpretation is evidence-by-scope, not "all verification happened" or "no verification happened."

## Worked example — session 019f96f5

| Run | Run dir | Verifiers spawned | Verdicts |
|-----|---------|-------------------|----------|
| `/check` run 1 | `P:\.artifacts\console_9f93f0d3-0b5b-4985-b779-6a2c\grok-check\20260725-143315-606\` | 3 (/why v2 fidelity, /why-old archive, git scope) | 3/3 PASS |
| `/check` run 2 | `P:\.artifacts\console_9f93f0d3-0b5b-4985-b779-6a2c\grok-check\20260725-145841-524\` | 3 (/www research, /wiki concept, /why v3 citation) | 3/3 PASS |

Total: 6 verifier subagents returned PASS with documented receipts (git show, Select-String, body diff, qmd search). The close scanner still reported `VERIFICATION_GAP` because it could not see the verifier command histories.

**Honest caveat about what was actually verified:** the 6 verifiers in this session ran git inspection, body-diff, qmd discoverability, and citation cross-referencing — **none of them ran `pytest`**. The session's "273 passed" test result came from a self-report in a prior turn (the agent ran the test suite before spawning any verifier), not from a `/check` verifier. So the close scanner's `VERIFICATION_GAP` is partially accurate: it correctly flags that no pytest run is visible in the parent transcript this session-window, AND it cannot see that the verifiers did run git/static verification. The general mechanism (subagent transcripts invisible to the scanner) is still real; this worked example just shouldn't be read as "tests were run and the scanner missed them." The verifiers verified structurally; the test-suite verification was a separate event outside the verifier scope.

## How a cold-start LLM should read this

When a close summary or scanner output reports `VERIFICATION_GAP`, run this checklist before treating it as real:

1. **Did `/check` run in the same session?** Search the session transcript or artifacts for `/check` run dirs:
   ```powershell
   Get-ChildItem P:\.artifacts\<terminal>\grok-check\ -Directory
   ```
2. **If /check ran, read the check-state.md:**
   ```powershell
   Get-Content P:\.artifacts\<terminal>\grok-check\*\check-state.md
   ```
   The state file documents which verifiers ran, what they verified, and the verdicts.
3. **Classify by scope.** A `/check` PASS is static/verifier evidence; inspect
   the receipt's concern scope before deciding whether tests or live behavior
   remain unverified. Do not treat either the scanner gap or `/check` PASS as a
   blanket verdict.

## The general principle

**Scanner output is observation, not verdict.** This is already stated in the `/check` SKILL.md Step 0.5 for its own preprocessor:

> "signals are observations, not verdicts. The verifier decides severity in context."

The same principle applies to the close scanner when `/check` subagents are the actual verification mechanism. A `VERIFICATION_GAP` signal from the close scanner is **necessary but not sufficient** evidence that verification didn't happen. The sufficient evidence is whether `/check` ran and what its verifiers returned.

## Current implementation status

The scanner now performs the cheap durable join through `check-state.md` rather than traversing child transcripts. This preserves the session boundary and avoids assuming that a verifier PASS covers unrelated tests or runtime behavior. Persistence checks are also captured as structured cross-repo receipts.

The remaining limitation is intentional: `/close` does not rerun expensive `/check`. It reports the available verifier scope and requires the LLM to classify any remaining live/runtime gap.

This is the same class of "scanner limitation" as the dirty_age gap that motivated `/close` auto-invoking `/aar` (see `close-auto-invokes-aar`): the scanner counts something but does not run a deeper analysis; the LLM reading the output is expected to know when the count is incomplete.

## Falsifier

This concept is wrong if:
- **The close scanner stops reading check-state receipts** or accepts a PASS without session binding — in that case the evidence join has regressed.
- **`/check` does not actually run command receipts in subagent transcripts** (verifiers only do LLM reasoning, no shell) — in that case the gap is real, not stale. The /check SKILL.md Step 3 mandates `capability_mode: "execute"` specifically because verifiers must run commands, so this falsifier does not currently fire.
- **The /check runs fail silently** (subagents crash, no verdict returned) and the parent reports the spawn succeeded — in that case the gap is real even though /check "ran." Cold-start LLM must read the actual check-state.md verdicts, not assume PASS from run-dir existence.

## Cold-start protocol

```powershell
# 1. List /check run dirs from this session
Get-ChildItem P:\.artifacts\<terminal>\grok-check\ -Directory -ErrorAction SilentlyContinue

# 2. Read each check-state.md
Get-Content P:\.artifacts\<terminal>\grok-check\*\check-state.md

# 3. If /check ran AND returned PASS — report static verifier PASS with its scope
# 4. Separately determine whether tests/live acceptance ran; do not infer that from CHECK PASS
# 5. If /check did NOT run OR returned FAIL — treat the corresponding verification gap as real
```

## Related concepts

- [[check-vs-review-complementary-not-redundant]] — both /check's verifier transcripts are invisible to /review (cross-skill) and to /close (cross-tool); same structural invisibility
- [[close-auto-invokes-aar]] — the other known /close scanner limitation; /close was extended to auto-invoke /aar to cover the dirty_age gap. The verification-gap is a different limitation with a different fix (read-time interpretation, not scanner extension).
- [[best-practices-enforcement-mechanism-grok-build]] — the general principle that scanner reports ≠ ground truth

## Application

This pattern applies whenever a scanner greps the parent transcript but verification happens in spawned subagents:

- `/close` scanner vs `/check` verifiers (the documented case)
- `/close` scanner vs `/red-team` specialist subagents (if they run commands)
- `/close` scanner vs `/review` specialists that run tests as part of their review
- Any future skill that spawns execute-capable subagents for verification work

The principle is the same: **check the durable verifier receipt and its scope before treating the parent-transcript signal as a full verdict.**
