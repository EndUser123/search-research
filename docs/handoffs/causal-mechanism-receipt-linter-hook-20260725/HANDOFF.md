---
thread_id: causal-mechanism-receipt-linter-hook-20260725
parent_handoff_path: none
current_session_id: 019f96f5-dc4a-79d0-9e17-396f2a582186
current_terminal_id: console_9f93f0d3-0b5b-4985-b779-6a2c
produced_at: 2026-07-26T01:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: beb1a58
---

# Handoff: artifact-verification gate for causal claims in wiki concepts + handoffs

## Objective

Implement a verification gate that **validates artifact references in causal claims actually resolve** — not a lexical check for receipt markers. When a wiki concept or handoff contains a causal-mechanism claim with a file:line citation, the gate resolves the citation (does the file exist? do the lines exist? does the cited text match the claim?) and blocks the write if the citation is fake, stale, or absent. Structural enforcement for the rule documented in `wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md`, using the mechanism the workspace already documented as correct in `ROOT_CAUSE_BACKLOG.md` Item 8 and `lexical-vs-semantic-verification-gap.md`.

## Why this matters (unchanged from prior version — the problem is real)

The wiki concept documenting this rule was itself written from inference, then corrected after operator pushback ("explain clearly"). The behavioral rule (read source before writing mechanism claim) is fresh in memory now but will decay. Structural enforcement catches what behavior misses.

**Worked example (the incident this would catch):** session 019f96f5 wrote `close-scanner-verification-gap-stale-read.md` claiming "scanner greps only the parent transcript" without reading `close_accounting.py`. Artifact-verification gate would have required a `file:line` citation; the agent would have had to open the file, find the lines, and cite them — at which point the claim would have been receipted correctly the first time, instead of corrected after operator pushback.

## Design correction (what changed from v1 of this handoff)

**v1 proposed a lexical receipt-lint hook** (regex for "the scanner does X" + absence of `receipt:` marker → warn). **v1 is wrong.** Two external critiques (agy BLOCK, codex REVISE) and three workspace artifacts independently established that lexical enforcement is the wrong layer:

- `P:/.claude/ROOT_CAUSE_BACKLOG.md` Item 8 (verbatim): *"Prompt-injection gates are the wrong enforcement mechanism for verification behavior. Rhetoric-injection produces rhetoric (compliance theater). Gates that check artifacts (file parses, test passes, cited file:line exists) produce verification."*
- `P:/.data/wiki/concepts/lexical-vs-semantic-verification-gap.md` (created 2026-07-25 by concurrent session, sourced from this same session 019f96f5): *"mutation receipts are the canonical lexical artifact; this explains why they are insufficient as completion receipts."*
- `P:/.data/wiki/concepts/writing-discipline-not-enforced.md` (2026-07-21): *"writing the rule creates a sense of having addressed the problem without actually addressing it."*

**v2 (this revision) changes the mechanism from lexical to artifact-resolution.** The gate does not check whether the prose contains a magic word; it resolves the cited artifact and checks that it backs the claim. This is the mechanism the workspace already documented as correct. v1 ignored that documentation — which is itself an instance of the pattern this handoff addresses (designed without inventorying existing solutions; skipped `/design` Step 0.7 preflight).

## Scope

### What the gate does

For each wiki concept or handoff write containing causal-mechanism phrasing (regex-detected, same trigger phrases as v1):

1. **Extract cited artifacts.** Parse `file:line` patterns, `receipt: <path>:<lines>` fields, `Lines N-M of <file>` patterns from the content.
2. **Resolve each cited artifact.** Open the file. Confirm the lines exist. Optionally: confirm the cited text plausibly supports the claim (lightweight — does the line contain a token from the claim, or is it in a function whose name matches the claim's subject?).
3. **Block if any cited artifact fails to resolve.** Exit 2 with stderr naming the failing citation: "Citation `close_accounting.py:422-510` does not resolve (file not found / lines out of range / line content does not match claim)."
4. **Block if causal claims are present with ZERO artifacts cited.** Same exit 2 with: "Concept contains causal claims but cites no artifacts. Add file:line citations backing each claim, or rephrase as non-causal."
5. **Allow if all causal claims have ≥1 resolving artifact citation.** Exit 0.

### What the gate does NOT do

- Does NOT judge whether the claim is *true* — only whether the cited artifact exists and plausibly supports it
- Does NOT accept `[FACT]` as a receipt marker (v1 error: `[FACT]` asserts epistemic status, not evidence; agent can self-certify)
- Does NOT accept `receipt:` without a resolving file:line behind it
- Does NOT do LLM-as-judge semantic evaluation (v2 keeps it deterministic; LLM judgment is a possible v3 if deterministic resolution is insufficient)

### Trigger surfaces

- `.data/wiki/concepts/*.md`
- `docs/handoffs/*/HANDOFF.md`

(Path matching uses absolute or normalized paths — v1's regex only matched relative paths, which was an implementation bug.)

## Alternatives considered

1. **v1 lexical receipt-lint** — REJECTED. Workspace documentation (ROOT_CAUSE_BACKLOG Item 8, lexical-vs-semantic-verification-gap) explicitly identifies lexical enforcement as the wrong mechanism. Both external critiques (agy, codex) independently reached the same conclusion.

2. **Claim ledger (codex Option E)** — DEFERRED to v3. Causal claims originate in a structured ledger (`claim_id`, `claim`, `classification`, `source`, `locator`, `source_hash`); wiki/handoff prose is generated or validated against the ledger. This is the long-term shape, but it requires changes to how claims are authored (structured-first vs prose-first). v2 (artifact resolution) is the minimal change that addresses the root cause without restructuring the authoring workflow. v3 ledger can layer on top of v2.

3. **LLM-as-judge per write** — DEFERRED. Higher accuracy than deterministic resolution; much higher cost. Revisit if deterministic resolution has false-negative rate >20% on real causal claims.

4. **Behavioral rule only (no gate)** — REJECTED. Proven insufficient this session: the pattern recurred *after* the behavioral rule was documented in the wiki.

## Acceptance criteria

- [ ] Gate fires on writes to `.data/wiki/concepts/*.md` and `docs/handoffs/*/HANDOFF.md`
- [ ] Gate extracts `file:line` citations from content (multiple formats supported)
- [ ] Gate resolves each citation: file exists, lines in range, line content plausibly matches claim subject
- [ ] Gate blocks (exit 2) when: causal claims present + zero artifacts cited, OR any cited artifact fails to resolve
- [ ] Gate allows (exit 0) when: no causal claims present, OR all causal claims have ≥1 resolving artifact citation
- [ ] Gate does NOT accept `[FACT]` alone as satisfying the citation requirement
- [ ] Bypass mechanism: session-scoped flag with written justification + 5-minute TTL (same as v1 proposal; necessary for legitimate prescriptive content)
- [ ] Test: re-write the original (uncorrected) `close-scanner-verification-gap-stale-read.md` — gate should block (causal claims, no resolving citations)
- [ ] Test: write the corrected version (with `close_accounting.py:422-510` citations) — gate should allow (citations resolve)
- [ ] Test: write a concept with a fake citation (`nonexistent.py:9999`) — gate should block (citation fails to resolve)
- [ ] Test: write a prescriptive concept ("the agent should...") — gate should not fire (no causal claims)
- [ ] Performance: gate runs in <1s for typical files (one file-open per unique citation; cache resolved paths within a single write)

## Implementation notes

- **Where to install:** `~/.grok/hooks/PreToolUse_artifact_verify.py` (Grok-native PreToolUse hook)
- **Trigger phrases (same as v1):** `the scanner|gate|hook|system|agent (does|can't|cannot|doesn't|will|won't|is)`, `because|since|given that (the|it|this)`, `works by|happens when|fails when`, `can't see`, plus v1's missing patterns: `causes`, `leads to`, `results in`, `due to`, `drives`, `produces`, `prevents`, `enables`, `triggers`
- **Mood filter (from v1, retained):** imperative/prescriptive mood ("the agent should") does not trigger; past/present declarative does
- **Citation parsers:** support `receipt: <path>:<line>` / `receipt: <path>:<line>-<line>` / `<path>:<line>` / `Lines N-M of <path>` / `lines?\s+\d+` near a `source:` field
- **Resolution cache:** within a single write, cache resolved file:line tuples so multiple claims citing the same source resolve once
- **Shared helper location:** `P:/.agents/scripts/artifact_verify.py` (factor the resolver so `/check` and `/close` can call it later)

## Dependencies

- Requires: nothing
- Blocks: nothing
- Non-blocking to: precommit-sibling-collision-hook, close-scanner-check-receipts, close-scanner-coded-enforcement-gates

## Out of scope

- Claim ledger (codex Option E) — v3, layers on top of v2
- LLM-as-judge variant — v3, only if deterministic resolution insufficient
- Linting commit messages, ADRs, design docs (different surfaces; revisit once wiki+handoffs are covered)
- Cross-session claim tracking (ledger feature; v3)

## Related artifacts

- Wiki concept: `causal-mechanism-claims-require-source-receipts-before-durable-write.md` (the rule this gate enforces)
- Wiki concept: `lexical-vs-semantic-verification-gap.md` (the workspace doc that says lexical enforcement is insufficient — v1 ignored this)
- `P:/.claude/ROOT_CAUSE_BACKLOG.md` Item 8 (the workspace doc that says artifact-checking gates are the correct mechanism — v1 ignored this)
- Incident: `close-scanner-verification-gap-stale-read.md` was written without receipts, corrected after operator pushback
- agy critique of v1 design (BLOCK verdict): `file:///C:/Users/brsth/.gemini/antigravity-cli/brain/9c4e84d2-3aff-45dd-b01a-bdfcad55cf34/design_critique_causal_enforcement.md`
- codex critique of v1 design (REVISE verdict): `P:/tmp/codex-critique-final.md`

## Status

OPEN — ready for implementation. v2 design (artifact verification) supersedes v1 (lexical receipt-lint). Priority raised: this is the load-bearing structural fix for the pattern documented across 4+ wiki concepts and recurred-within-session despite documentation.
