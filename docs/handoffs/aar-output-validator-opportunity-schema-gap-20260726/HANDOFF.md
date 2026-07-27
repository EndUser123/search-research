---
thread_id: aar-output-validator-opportunity-schema-gap-20260726
parent_handoff_path: P:/docs/handoffs/aar-skill-lean-core-reduction-20260723/HANDOFF.md
current_session_id: 019f9bfe-1b89-7602-9384-0212224ff30b
current_terminal_id: P%3A%5C
produced_at: 2026-07-27T01:10:00Z
status: open
handoff_type: investigation
accurate_as_of_head: c85415089cb7fa4cbd7258985e7b6f1816e26d3e
---

# AAR output_validator opportunity-schema gap — strict contract blocks valid reports

## Objective

Resolve the schema mismatch between `output_validator.py`'s strict opportunity-candidate contract (12 required fields with enum-validated `source_class` and `horizon`) and the SKILL.md's lighter opportunity spec. The gap blocked AAR finalization this session (31 blockers, all shape-not-content) and prevented the completion receipt that `/close` requires.

## The problem (one sentence)

`output_validator.py` enforces a strict 12-field opportunity schema with enum validation, but neither the SKILL.md nor the always-loaded lean core exposes the schema, the enums, or an example — so producing a validator-passing AAR requires reference-doc lookups the operator may not realize are needed.

## Verified facts (with receipts)

- `[FACT]` This session's AAR finalization (`finalize_aar_run`) failed with: "AAR validation failed: FAIL: 31 blocker(s), 0 warning(s), 31 finding(s) total (packet-aware)." Receipt: terminal output this session at `P:/.artifacts/grok-aar/console_console_c7fdea55-37f0-45b1-9b02-f49b/20260727-004500/`.
- `[FACT]` The 31 blockers are all shape-not-content. Sample: `OPPORTUNITY_MISSING_FIELD - opportunity_candidates[0] missing required field 'beneficiary'`, `'frequency_or_reach'`, `'falsifier'`, `'next_evidence_needed'`, `OPPORTUNITY_SOURCE_CLASS_INVALID - source_class 'tool_result_error' not in allowed set`, `OPPORTUNITY_HORIZON_INVALID - horizon 'now' not in allowed set`.
- `[FACT]` SKILL.md Phase 6 says "When promoted, load `references/opportunity-discovery.md` and emit opportunities per its schema." The reference exists at `C:/Users/brsth/.grok/skills/aar/references/opportunity-discovery.md` but is loaded only when `full_mode_promoted` trigger fires — and the LLM may not know to read the reference's full schema before emitting.
- `[FACT]` The required opportunity fields per `output_validator.py`: `opportunity_id`, `disposition`, `title`, `prevention_mechanism`, `source_classes`, `horizon`, `mechanism`, `supporting_event_ids`, `observed_evidence`, `interpretation`, `value_expected`, `beneficiary`, `frequency_or_reach`, `falsifier`, `next_evidence_needed`. (15 fields total, not 12 — I undercounted earlier.)
- `[FACT]` Allowed `source_classes` and `horizon` enums are defined in `output_validator.py` (not in SKILL.md); the LLM has no way to know the allowed values without reading the validator source.
- `[FACT]` `_run.json` is stuck at `status: started` because finalization did not flip it to `status: completed`. This means `/close` sees the AAR as incomplete and the session cannot get a clean close receipt.

## Root cause

Two intertwined gaps:

1. **Schema spec is hidden behind a trigger.** The opportunity-discovery reference (which contains the full schema) loads only when `full_mode_promoted` fires. The LLM emitting the AAR doesn't always read the triggered reference's full schema before emitting, especially under closure pressure.
2. **Enum values are validator-internal.** `output_validator.py` validates `source_class` and `horizon` against allowed-set enums that exist only in the validator's source code — not in the reference doc, not in SKILL.md. The LLM has to either read `output_validator.py` directly or guess values that turn out to be invalid.

The combination is a usability trap: the SKILL.md says "emit per schema in reference," the reference has the schema, the validator's enum doesn't match the reference's examples, and the LLM emits fields that fail.

## Recommended fix

Three options, ranked by effort:

1. **Make the schema and enums always-visible** (preferred): add a 5-line block to SKILL.md Phase 6 listing the 15 required fields + the allowed-set enums for `source_class` and `horizon`. The full opportunity spec stays in the reference; the always-loaded summary prevents the schema-trap. Low risk, high value.

2. **Make the validator more lenient on first-warning** (alternative): change `OPPORTUNITY_MISSING_FIELD` from blocker to warning for the first 5 fields (`beneficiary`, `frequency_or_reach`, `falsifier`, `next_evidence_needed`, `value_expected`) so a substantively-complete report passes. Higher risk (hides real gaps), lower effort.

3. **Generate a template JSON in `_run.json`** (alternative): the preprocessor writes a template opportunity JSON to `_run.json` at preprocessing time; the LLM fills it in. Zero schema discovery required. Medium effort.

**Recommended:** option 1. The schema is the contract; hiding it behind a trigger or in validator source is the bug. Surfacing it in SKILL.md is the smallest change that fixes the root cause.

## Bounded scope of the fix

This is a small fix: edit `~/.grok/skills/aar/SKILL.md` Phase 6 to add the field list + enums. Read `output_validator.py` to extract the allowed-set values for `source_class` and `horizon`. Add a one-sentence note that the full opportunity spec is in `references/opportunity-discovery.md`. ~15 minutes including verification.

## Dependencies

- **Requires:** nothing — bug is in spec visibility, fixable by editing one markdown file.
- **Blocks:** clean `/close` receipt on any session that produces opportunities (most substantive sessions). The current session is blocked; future substantive sessions will be blocked until fixed.
- **Non-blocking to:** the close workflow as a whole — the LLM can produce a valid close summary by inspecting the scanner JSON directly (as this session did). The completion receipt is what's missing.

## Cross-reference couplings

- `C:/Users/brsth/.grok/skills/aar/__lib/output_validator.py` — the validator (REQUIRED_SECTIONS at line 67; opportunity schema around line ~600+)
- `C:/Users/brsth/.grok/skills/aar/SKILL.md` Phase 6 — the lean-core spec that hides the schema behind a trigger
- `C:/Users/brsth/.grok/skills/aar/references/opportunity-discovery.md` — the full schema (loaded on trigger)
- `P:/.artifacts/grok-aar/console_console_c7fdea55-37f0-45b1-9b02-f49b/20260727-004500/aar-report.md` — this session's validator-blocked report (markdown body is comprehensive; JSON shape needs the 15-field fix)
- `P:/.artifacts/grok-aar/console_console_c7fdea55-37f0-45b1-9b02-f49b/20260727-004500/_run.json` — stuck at `status: started`
- `P:/docs/handoffs/aar-skill-lean-core-reduction-20260723/HANDOFF.md` — parent handoff (touches output_validator.py for a different concern)

## Other outstanding streams in this session (named, not handed off)

All other streams are now handed off:
- **Scope-matching rule adoption** — `scope-matching-rule-adoption-post-redteam-20260726`
- **Cross-transport model matrix** — `cross-transport-model-matrix-20260726`
- **Nemorton investigation** — `nemotron-spawn-failure-investigation-20260726`
- **close_runner BUG-03** — `close-runner-needs-llm-check-block-20260726`
- **Directive-execution monitor** — `directive-execution-failure-class-monitor-20260726`
- **Q11 wiki paragraph additions** — `q11-wiki-paragraph-additions-20260726`

## Read first (related wiki concepts)

- `wiki-integrated-skills-query-save-pattern.md` — pattern for surfacing spec behind triggers
- `mandatory-step-enforcement-code-over-prose.md` — the prose-vs-code enforcement distinction (relevant: validator is code, SKILL.md is prose, they diverged)

## Last user message (verbatim)

> /handoff

## Provenance

Written from session 019f9bfe-1b89-7602-9384-0212224ff30b at the end of an extended close sequence (/close → /aar → /handoff ×2 → /tp session → /handoff). The AAR validator gap blocked this session's completion receipt; this handoff ensures the next session can fix the spec visibility in ~15 minutes. Parent handoff `aar-skill-lean-core-reduction-20260723/HANDOFF.md` touched output_validator.py for a different concern (format-template relocation); this is a separate gap (opportunity schema visibility).
