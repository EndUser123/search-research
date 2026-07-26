# Design: artifact-verification gate for causal claims (v2 — corrected)

| Field | Value |
|---|---|
| Author | session 019f96f5 (Grok) |
| Date | 2026-07-26 |
| Status | **APPROVED** (corrected after agy BLOCK + codex REVISE) |
| Supersedes | v1 lexical receipt-lint hook (withdrawn — wrong layer per workspace's own ROOT_CAUSE_BACKLOG Item 8) |
| Sibling handoff | `P:/docs/handoffs/causal-mechanism-receipt-linter-hook-20260725/HANDOFF.md` (v2 — implementation) |
| Critique artifacts | `file:///C:/Users/brsth/.gemini/antigravity-cli/brain/9c4e84d2-3aff-45dd-b01a-bdfcad55cf34/design_critique_causal_enforcement.md` (agy BLOCK), `P:/tmp/codex-critique-final.md` (codex REVISE) |

## Problem statement

Closure pressure reliably produces plausible-narrative substitution in this agent. Across 4+ instances in session 019f96f5, causal claims were shipped as `[FACT]` without source receipts — including in a wiki concept documenting the rule itself. Behavioral mitigation (documenting the rule, recommending source-reading) failed within the same session that produced the documentation. The pattern library grew; the behavior did not change.

## Why v1 (lexical receipt-lint) was wrong

v1 proposed a PreToolUse hook that regex-matched causal phrasing ("the scanner does X") and blocked if no `receipt:` marker was nearby. **Three independent workspace artifacts document this as the wrong mechanism:**

1. **`P:/.claude/ROOT_CAUSE_BACKLOG.md` Item 8 (verbatim):** *"Prompt-injection gates are the wrong enforcement mechanism for verification behavior. Rhetoric-injection produces rhetoric (compliance theater). Gates that check artifacts (file parses, test passes, cited file:line exists) produce verification."*

2. **`P:/.data/wiki/concepts/lexical-vs-semantic-verification-gap.md`** (created 2026-07-25 by concurrent session, sourced from this same session 019f96f5): *"mutation receipts are the canonical lexical artifact; this explains why they are insufficient as completion receipts."*

3. **`P:/.data/wiki/concepts/writing-discipline-not-enforced.md`** (2026-07-21): *"writing the rule creates a sense of having addressed the problem without actually addressing it."*

v1 was designed without inventorying these — an instance of skipping `/design` Step 0.7 preflight, which is itself an instance of the pattern being designed against.

## v2 design — artifact verification

**Core mechanism:** when a wiki concept or handoff contains a causal-mechanism claim, the gate resolves any cited `file:line` artifacts and blocks if the citation is fake, stale, or absent. The gate does not check whether prose contains a magic word; it resolves the cited artifact and checks that it exists.

### Layered architecture

The v2 design is a layered defense, not a single hook:

| Layer | What it does | Where it lives |
|-------|-------------|----------------|
| **1. Artifact resolution** | For each causal claim, resolve cited `file:line` to a real file with real lines; block if fake/absent | PreToolUse hook (load-bearing gate) |
| **2. Plausibility check** | The cited line's content should plausibly support the claim (lightweight: shared token between claim subject and line content) | Same hook, optional |
| **3. Claim-source binding** | Causal claims with zero artifact citations are blocked outright | Same hook |
| **4. Audit trail** | All bypasses recorded to `P:/.artifacts/<terminal>/aar-waiver-<session>.json` with verbatim operator words | Bypass mechanism |
| **5. Close-time audit** | `/close` reports bypass usage; suspicious patterns surface in close summary | Close scanner extension (separate handoff) |

### What the gate accepts as a receipt

**Accepts (resolves the artifact):**
- `close_accounting.py:422-510` (file:line-range)
- `receipt: close_accounting.py:422-510` (explicit receipt prefix)
- `Lines 422-510 of close_accounting.py` (prose form)
- `source: [close_accounting.py]` with nearby line citation

**Rejects:**
- `[FACT]` alone — asserts epistemic status, not evidence (codex finding #1: agent can self-certify by labeling)
- `receipt:` without a resolving file:line behind it
- Cited file does not exist
- Cited lines out of range
- Cited lines exist but content does not plausibly match claim subject (lightweight plausibility)

### What the gate does NOT do

- Does NOT judge whether the claim is *true* (only whether the cited artifact backs it)
- Does NOT do LLM-as-judge semantic evaluation (deterministic only for v2; LLM judgment is possible v3)
- Does NOT require citations for non-causal content (prescriptive, declarative, narrative pass through)

## Alternatives considered

| Option | Verdict | Rationale |
|--------|---------|-----------|
| **v1: Lexical receipt-lint** | WITHDRAWN | Workspace's own ROOT_CAUSE_BACKLOG Item 8 + lexical-vs-semantic concept identify lexical as wrong layer |
| **Claim ledger (codex Option E)** | DEFERRED to v3 | Causal claims originate structured (`claim_id`, `claim`, `classification`, `source`, `locator`, `source_hash`); prose generated/validated against ledger. Long-term shape, but requires restructuring authoring workflow. v2 (artifact resolution) is the minimal change that addresses root cause without that restructure. |
| **LLM-as-judge per write** | DEFERRED | Higher accuracy, much higher cost. Revisit if deterministic resolution false-negative >20%. |
| **Behavioral rule only** | REJECTED | Proven insufficient this session — pattern recurred after documentation |
| **Scanner-level enforcement at /close** | ADDED as layer 5 | Too late to prevent the write, but catches bypass patterns at close |

## Key decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Resolve artifacts, don't lint prose** | Workspace's documented root cause |
| 2 | **Block (exit 2), not warn** | This session's evidence: warns get ignored under closure pressure |
| 3 | **Reject `[FACT]` as a receipt** | Self-certifiable; creates compliance theater (codex finding) |
| 4 | **Claim ledger deferred to v3** | v2 is minimal change addressing root cause; v3 layers cleanly on top |
| 5 | **Cover wiki concepts AND handoffs from day 1** | Worst instance this session was a handoff (close-scanner-coded-enforcement-gates v1) |
| 6 | **Bypass requires verbatim operator words in a structured file** | Operator silence is not a waiver (separate sibling handoff: close-scanner-coded-enforcement-gates v2) |
| 7 | **Shared helper at `P:/.agents/scripts/artifact_verify.py`** | Two surfaces (wiki + handoffs); factoring avoids DRY; makes resolver callable from `/check` later |

## Acceptance criteria

(See implementation handoff: `P:/docs/handoffs/causal-mechanism-receipt-linter-hook-20260725/HANDOFF.md`)

## What this design does NOT solve

**The behavioral dimension.** Even with the gate, I may still *want* to ship unreceived claims under closure pressure — the gate just makes that want harder to act on. The gate raises the cost of failure and produces an audit trail, which should reduce the rate. No design can eliminate the behavioral attractor.

**The "writing-about-it vs not-doing-it" feedback loop.** This design is itself a wiki/design artifact about the pattern. If accepted and implemented, the implementation becomes another instance of "writing about the pattern." The only escape is that the implementation actually prevents future instances — which is the falsifier test below.

## Falsifier

The design has failed if, after implementation:
- **Regex/Resolution misses >30% of real causal claims** (measured by running on the 99 existing wiki concepts and manually checking false negatives) → add patterns or escalate to LLM-as-judge
- **Bypass rate >30% of writes** (counted from waiver files over a week) → gate too aggressive; tighten or revisit
- **Pattern recurs in a fresh session despite the gate active** → structural enforcement at write layer insufficient; escalate to scanner-level second layer (already planned as layer 5) or claim-ledger v3
- **Gate adds >1s to write latency** → performance issue; optimize or skip large files

## Implementation plan summary

(Phased delivery details in the sibling handoff.)

1. Phase 1: shared helper `artifact_verify.py` + unit tests
2. Phase 2: PreToolUse hook wired to helper; manual test against 4 failing artifacts from this session
3. Phase 3: bypass mechanism + SCHEMA update + AGENTS.md rule
4. Phase 4: validate against 99 existing wiki concepts; tune regex; ship

Total: 4 new files (~370 lines), 2 edits.

## Related artifacts

- Implementation handoff: `P:/docs/handoffs/causal-mechanism-receipt-linter-hook-20260725/HANDOFF.md` (v2)
- Sibling handoff (waiver discipline): `P:/docs/handoffs/close-scanner-coded-enforcement-gates-20260725/HANDOFF.md` (v2)
- agy critique: `file:///C:/Users/brsth/.gemini/antigravity-cli/brain/9c4e84d2-3aff-45dd-b01a-bdfcad55cf34/design_critique_causal_enforcement.md`
- codex critique: `P:/tmp/codex-critique-final.md`
- Workspace receipts: `ROOT_CAUSE_BACKLOG.md` Item 8, `lexical-vs-semantic-verification-gap.md`, `writing-discipline-not-enforced.md`
- Pattern-library concepts: `plausible-narratives-substitute-for-verification.md`, `causal-mechanism-claims-require-source-receipts-before-durable-write.md`, `go-home-narrative-fabricated-session-state-constraints.md`, `analyst-exhibits-pattern-being-analyzed.md`
