# Design Review (Re-Review): `/behave` — Grok-Native Behavioral Decision-Integrity Skill

**Document under review (revised):** `C:\Users\brsth\AppData\Local\Temp\grok-design-81539877\grok-design-doc-81539877.md`
**Reviewer scope:** Implementability, completeness, consistency, alternatives quality, plan quality, traceability, premise labeling, and the domain-specific concerns named in the review prompt.

---

## Executive summary

The revised design (39KB → 62KB) addresses all 25 findings from the prior review. The structural issues that gated implementation (F-01 reuse contract verification, F-02 cross-model payload contract, F-03 unit granularity, F-04/F-05 schema gaps) are resolved. The schema is now dimension-keyed, the input contract has explicit CLI flags, the coupling inventory is per-module and per-reference, and the rollout phasing has quantified acceptance.

The revision introduces a small number of new issues, mostly minor:
- **2 major**: a `why_version_max: <TBD>` placeholder in the frontmatter that blocks Unit 1 ship; the Phase 1 handoff-selection precondition is not assigned to any implementation unit.
- **9 minor**: ambiguities in evidence-tier assignment, metadata source, schema dual-naming, example-phrasing provenance, frontmatter/verification mismatch, an unexplained 4th value in the cross-model response schema, contradictory "committed together" / per-unit disposition language, and several consistency gaps.
- **3 nit**: CLI flag positional language, Open-Questions categorization, and Key-Decisions table bloat.

**Total new findings: 14 (2 major, 9 minor, 3 nit).** All 25 prior findings: addressed.

**Post re-review pass (current state):** all 14 new findings addressed in a single revision. See "Revision Summary" at the end of this document for the per-finding resolution map.

The design is implementable after the 2 major new findings are resolved (TBD placeholder, Phase 1 precondition assignment).

---

## Status of prior findings

All 25 prior findings are addressed in the revised design. The table below summarizes how each was resolved.

| ID | Sev | Resolution |
|---|---|---|
| F-01 | critical | §3 "Reuse contract verification" added with file/line citations for all 4 `/why` interfaces and an honest gap analysis noting that `evidence-tier-calibration` and `cross-model-review` are documented procedures, not named `provides:` entries |
| F-02 | critical | Step 8 expanded with full payload contract: `field_set`, `omitted_fields`, prompt template pointer, `reviewer_response_schema`, reviewer selection, `timeout_ms`, `unavailable_handling` |
| F-03 | critical | Units 1-11 collapsed to Units 1-4 (within one rollback unit); Units 5-8 independently revertible; explicit "unit-of-rollback is the entire SKILL.md" statement added |
| F-04 | critical | Output schema restructured with `dimensions:` keyed map (d1–d7); operational fields (`verdict`, `confidence`, `metadata`, `cross_model_review`, `wiki_writes`) flat |
| F-05 | critical | `evidence_tier: <1-4>` added to `d4_claim_verification` entries (per-claim) and `d7_self_protection_patterns` entries |
| F-06 | major | Schema uses canonical labels: `AUTONOMOUS_DETECTION / USER_TRIGGERED_VERIFICATION / USER_SUPPLIED_DIAGNOSIS / USER_FORCED_REVERSAL` |
| F-07 | major | Hidden anchor restated as "where the skill boundary lives"; detection-layer axis explicitly separated from skill-boundary axis; Option C reclassified as "infeasible regardless of axis" |
| F-08 | major | Touch-points recounted as 7 for SKILL.md with per-reference justification (4 strongest, 1 acceptable, 0 unacceptable) |
| F-09 | major | Unit 1 acceptance explicitly specifies "Section headers for: Step 0, Step 1, ..., Step 10 (11 headers, all empty after Unit 1)" |
| F-10 | major | `acceptance_criteria: [<quantified-criterion>, ...]` added to `repair_proposals` schema |
| F-11 | major | Per-pattern schema defined in Unit 8 with 11 fields (`pattern_id`, `name`, `definition`, `signals`, `example_phrasings`, `verbatim_quote_requirement`, `severity_rubric`, `examples`, `added_date`, `added_by`, `status`, `retraction_reason`) |
| F-12 | major | Resolved with self-counting `insufficient_evidence_count` field on the report itself; no separate log written; counter shape is `count + per_dimension` |
| F-13 | major | Three-archetype test set (clear-cut / ambiguous / false-positive trap); operator baseline capture; acceptance = "≥2 of 3 correctly classified AND 0 false positives on the cleared set" |
| F-14 | major | `include_incident` and `share_incident` boolean fields added to input contract; argument-hint updated to `<incident-packet-path> [--include-incident] [--share-incident]`; default off/off |
| F-15 | minor | `metadata` block added: `report_timestamp`, `operator_id`, `input_packet_sha256`, `behave_version`, `why_version` |
| F-16 | minor | `verdict_timeline[]` entry schema defined: `{ timestamp: <ISO-8601>, verdict: <enum>, actor: <string>, justification_ref: <path-or-text>, evidence_at_time: [<path>] }` |
| F-17 | minor | `why_version_min: 3.0.0` and `why_version_max: <TBD>` added to frontmatter; upgrade protocol documented in §12 |
| F-18 | minor | `when-to-use` widened to "After any verdict transition where integrity is in question — including verdict changes without external challenge, suspected self-protection patterns before a reversal, and retrospective audit on a third-party design. Operator-invoked only; auto-invocation is v2." |
| F-19 | minor | Each BP pattern now has `definition`, `signals`, `example_phrasings` (≥2), and `severity_rubric` in Step 7 |
| F-20 | minor | Fallback path rule: `P:/docs/handoffs/_unaffiliated/behave-<date>-<sha256[:8]>.yaml` for unknown/unaffiliated `source_session_id` |
| F-21 | minor | Three rollback modes: (1) full removal, (2) paused mode via `## Status: paused`, (3) pattern retraction via `status: retracted` |
| F-22 | nit | Units 1-11 collapsed to 4 units (within one rollback group); 4 additional independent units (5-8) |
| F-23 | nit | Note on rule application: "touch-point count for a new field" rule is extended to new artifacts, not directly applicable to new skills |
| F-24 | nit | Step 8 trigger now says: "≥3 self-protection patterns detected (in v1 with 3 patterns defined, this trigger fires only when all three are detected — this is by design...)" |
| F-25 | nit | Terminology note at Step 7 first use: "evidence tier (1-4)" vs "pattern severity (1-3)" explicitly disambiguated as "not interchangeable" |

**All 25 prior findings: addressed.**

---

## New findings

## F-26 — Severity: major
- **Section:** §4 Implementation Sketch — frontmatter (line 124)
- **Description:** The frontmatter declares `why_version_max: <TBD>`. This is a YAML placeholder that (a) cannot be parsed cleanly in all YAML parsers due to the unquoted angle brackets, and (b) is an unresolved value that blocks Unit 1 ship. §16 [UNKNOWN] #4 acknowledges this but treats it as a question to revisit, not a prerequisite. An implementer finalizing Unit 1 cannot ship the SKILL.md without operator input on the upper bound. This is an implementation blocker dressed as an open question.
- **Suggestion:** Either (a) decide the upper bound now (e.g., `why_version_max: <current-/-why-version-at-v1-ship>`), or (b) move `[UNKNOWN] #4` to a new §"Prerequisites for Implementation" section that explicitly says "implementation cannot start until operator provides `why_version_max`." Option (b) is more honest about the dependency. Do not let Unit 1 commit with `<TBD>` in shipped frontmatter.
- **Response:** Option (b) implemented. The frontmatter now declares `why_version_max: "OPERATOR_SET_BEFORE_V1_SHIP"` (a valid quoted YAML sentinel). §16 has been split (per F-38) into "Open Questions" and "Implementation Prerequisites"; the `why_version_max` value is now Prerequisite #1 with an explicit decision rule (set to highest `/why` minor version known in production at v1 ship) and a resolution path (operator confirms current `/why` version and sets the field; Unit 1 ships). The Unit 1 acceptance criteria were updated to reference §16 Implementation Prerequisites #1 instead of "TBD."
- **Status:** addressed

## F-27 — Severity: major
- **Section:** §12 Rollout — Phase 1 acceptance + §13 Implementation Plan
- **Description:** Phase 1 acceptance requires (a) the operator to pick ≥3 past handoffs covering the three archetypes (clear-cut / ambiguous / false-positive trap), (b) the operator to write their own baseline analysis before running `/behave`, and (c) the three handoff paths to be written in `P:/docs/handoffs/session-health-behave-rollout-2026XXXX/HANDOFF.md` before the first `/behave` run. But the §13 implementation plan (Units 1-8) has no unit that creates the rollout handoff or captures the baseline. §16 [UNKNOWN] #5 acknowledges this but, like F-26, treats it as an open question rather than a prerequisite. The implementation plan is incomplete: it does not have a Unit 0 for "operator creates rollout handoff and baseline." Without this, Phase 1 acceptance cannot be measured, and Unit 6 (acceptance test) is partially ungrounded.
- **Suggestion:** Add a Unit 0 (or merge into Unit 6) with: "Operator creates `P:/docs/handoffs/session-health-behave-rollout-2026XXXX/HANDOFF.md` containing the three archetype handoff paths and a written baseline analysis for each. This is a precondition for Unit 6 (acceptance test) and for any `/behave` run against past incidents." Either commit this as a handoff-update task outside the SKILL.md creation, or document it explicitly as an operator-action prerequisite. Do not leave Phase 1 acceptance criteria un-measurable.
- **Response:** Unit 0 added to §13 Implementation Plan as the first unit. Unit 0 is explicitly marked as an **operator-action precondition** (not a code commit) with `Disposition: OPERATOR_ACTION`. Unit 6's `Dependencies:` line now lists "Unit 0 (operator-created rollout handoff)." The Phase 1 rollout handoff is also added to the File Change Inventory (§15) as an operator-authored file and to the Traceability Matrix (§14) as the first row. §16 Implementation Prerequisites #2 (per F-38 split) documents this as a blocking prerequisite with explicit resolution path.
- **Status:** addressed

## F-28 — Severity: minor
- **Section:** §4 Implementation Sketch — Step 8 cross-model review payload contract (lines 251-258)
- **Description:** The cross-model reviewer selection logic is duplicated from `/why` Step 15b: "prefer `glm-5-2` via `spawn_subagent` (reasoning lane, cross-family). Fallback to `/codex` CLI (GPT-5, write-capable). Fallback to parent-inherited if both unavailable. Reuse `/why` Step 15b's selection logic." The trailing sentence ("Reuse `/why` Step 15b's selection logic") contradicts the preceding sentence (which restates that logic). When `/why` Step 15b's selection changes, `/behave`'s selection will not auto-update; a maintainer must remember to update both places. This is exactly the DRY problem §17 says the design avoids.
- **Suggestion:** Remove the restated selection logic and leave only the reference: "Reuse `/why` Step 15b's selection logic for reviewer selection." If specific reviewer preferences need to override `/why`'s defaults, document only the *delta* (e.g., "if `/behave` requires a write-capable reviewer and `/why` Step 15b defaults to a read-only reviewer, fall back to the next candidate"). Do not duplicate the full logic.
- **Response:** Implemented. Step 8 reviewer-selection bullet now reads: "reuse `/why` Step 15b's selection logic (reviewer ordering, fallback chain, and parent-inherited last resort). `/behave` inherits the same reviewer preferences; it does not override them. If `/why` Step 15b's selection changes, `/behave`'s selection updates with it (no maintenance burden)." The duplicated `glm-5-2 → /codex CLI → parent-inherited` chain is removed; `/behave` documents no delta from `/why` Step 15b.
- **Status:** addressed

## F-29 — Severity: minor
- **Section:** §4 Implementation Sketch — output schema `cross_model_review.reviewer_response_schema` (line 213)
- **Description:** The schema lists `reviewer_response_schema: VERIFIED|DISPUTED|INCOMPLETE|<path-or-uri-of-full-schema>`. The first three values are documented (in Step 8 prose immediately below). The fourth value, `<path-or-uri-of-full-schema>`, is an unexplained escape hatch: what does it mean? When is it used? Who provides it? Is it a reference to a separate schema file? The §3 reuse verification cites `/why` `--verify` mode lines 561-573 as the schema source, but the schema as shown here includes a 4th value that does not appear in the citation.
- **Suggestion:** Either (a) document the 4th value: "`<path-or-uri-of-full-schema>` is an optional pointer to an extended response schema when the reviewer returns a non-standard format. Used only when the operator has configured a custom reviewer with additional fields." Or (b) remove the 4th value if it's unused — keep the schema to the three documented values. Pick one; do not leave an unexplained escape hatch in the schema.
- **Response:** Option (a) implemented. The 4th value is documented in-line on the schema definition: "the 4th value (`<path-or-uri-of-full-schema>`) is an optional pointer to an extended response schema, used only when the operator has configured a custom reviewer with additional fields beyond the three canonical verdicts. The default reviewer (`/why` Step 15b) returns only the three canonical values; the 4th is reserved for non-default configurations and is not produced under v1 defaults."
- **Status:** addressed

## F-30 — Severity: minor
- **Section:** §4 Implementation Sketch — output schema `metadata` block (line 181)
- **Description:** The `metadata` block requires `operator_id`. The design does not say whether this comes from the input packet (operator-supplied, spoofable) or from the runtime (Grok Build session id, not spoofable). Audit-trail integrity depends on this distinction. If operator-supplied, the design should note that operator_id is advisory (not authoritative). If runtime-sourced, the design should cite the env var or runtime field that provides it (`$GROK_OPERATOR_ID`? `$GROK_SESSION_ID`?).
- **Response:** Implemented. Each `metadata` field is now annotated inline with its source: `report_timestamp` (runtime ISO-8601), `operator_id` (runtime from Grok Build session context — `$GROK_OPERATOR_ID` or `$GROK_SESSION_ID`; advisory, not auth/authorization; "unknown" if unresolvable), `input_packet_sha256` (runtime SHA-256 of incident_packet), `behave_version` (runtime), `why_version` (runtime, must be within `[why_version_min, why_version_max]`). Step 10 prose now includes a "Metadata provenance (F-30)" paragraph stating all `metadata` fields are runtime-populated, not operator-overridable, and not used for authentication/authorization.
- **Status:** addressed

## F-31 — Severity: minor
- **Section:** §4 Implementation Sketch — Step 4 + output schema `d4_claim_verification.evidence_tier`
- **Description:** Step 4 says "Use `/why` evidence-tier system with weakest-link ceiling." The output schema now has `evidence_tier: <1-4>` per claim in `d4_claim_verification`. But there is no assignment rubric: who assigns the tier? Is it the operator (manual)? Is it inferred from the source type (a tool citation auto-assigns Tier 1; a hearsay citation auto-assigns Tier 3)? Is there a `tier_rationale` field that documents why each tier was chosen? Without a rubric, two different operators could assign different tiers to the same claim, making the diagnostic report non-reproducible.
- **Suggestion:** Specify the tier assignment model. Two options: (a) **Operator-assigned with rationale** — add `tier_rationale: <string>` to each entry; the operator documents why. (b) **Inferred from source type** — define a mapping (e.g., `evidence: <file:line>` → Tier 1, `evidence: <observation>` → Tier 2, `evidence: <heuristic>` → Tier 3, `evidence: <speculation>` → Tier 4). Option (a) is more honest about the human-judgment nature of the assignment; option (b) is more reproducible. Pick one and document in Step 4.
- **Response:** Option (a) implemented. The `d4_claim_verification` schema entry now includes `tier_rationale: <string>` alongside `evidence_tier: <1-4>`. Step 4 prose now has a "Tier assignment rubric (F-31)" paragraph: `evidence_tier` is operator-assigned with rationale; the model does not auto-assign tiers from source type; the four canonical tier definitions (Tier 1 = execution artifact, Tier 2 = direct observation, Tier 3 = inference from indirect evidence, Tier 4 = speculation) are restated from `/why` Step 4b; `tier_rationale` cites the tier definition and identifies the concrete evidence.
- **Status:** addressed

## F-32 — Severity: minor
- **Section:** §4 Implementation Sketch — output schema `confidence` vs `d4_claim_verification.evidence_tier`
- **Description:** The metadata/operational fields have `confidence: <evidence tier 1-4>` (described as "/why weakest-link ceiling"). The `d4_claim_verification` entries each have `evidence_tier: <1-4>` (per-claim). The relationship between per-claim tier and report-level confidence is not documented. Is `confidence = min(per-claim tiers)`? Is it weighted by materiality (using the `material: bool` field)? Does the report-level `confidence` exist if there are no `d4_claim_verification` entries (e.g., no load-bearing claims)?
- **Suggestion:** Document the derivation rule in Step 4 prose: "`confidence` is the weakest-link ceiling across all `material: true` claims in `d4_claim_verification`. If there are no material claims, `confidence` reflects the report-level assessment." Cite the rule in Unit 2 acceptance criteria.
- **Response:** Implemented. Step 10 prose now has a "Confidence derivation (F-32)" paragraph: report-level `confidence` is the weakest-link ceiling across all `material: true` claims in `d4_claim_verification`; if zero material claims, `confidence` is a report-level assessment documented in a new `confidence_basis: <string>` field (always populated). The `diagnostic_report` schema now includes `confidence_basis: <string>` as a sibling of `confidence`. The numeric derivation is `min(material_claim_tiers)` (Tier 1 = highest, Tier 4 = lowest).
- **Status:** addressed

## F-33 — Severity: minor
- **Section:** §4 Implementation Sketch — output schema `dimensions:` keyed map vs flat operational fields
- **Description:** The schema is dual-named: 7 analysis dimensions are nested under `dimensions:` (d1-d7), but operational fields (`verdict`, `confidence`, `metadata`, `cross_model_review`, `wiki_writes`, `insufficient_evidence_count`, `repair_proposals`) are flat at the top level. A downstream consumer must look in two places to find all the data. The convention is reasonable but not documented in the schema itself; a reader has to infer it from the §4 prose.
- **Suggestion:** Add a one-line comment to the output schema in §4 explicitly stating the convention: "7 analysis dimensions are nested under `dimensions:`; operational metadata fields (verdict, confidence, repair_proposals, cross_model_review, etc.) are flat at the top level." Or, alternatively, put everything under `dimensions:` (e.g., `dimensions.d1_decision_timeline`, `dimensions.d8_repair_proposals`) and make the operational fields a single `operational:` key. Pick one convention and document.
- **Response:** Implemented. The "Schema-to-dimension mapping" preamble now has an explicit "Convention (F-33)" paragraph: 7 analysis dimensions are nested under `dimensions:` (d1-d7); operational fields (`verdict`, `confidence`, `confidence_basis`, `metadata`, `cross_model_review`, `cross_model_review_pending`, `wiki_writes`, `insufficient_evidence_count`, `repair_proposals`) are flat at top level. Downstream consumers look in two places: per-dimension analytical content under `dimensions:`, operational summaries at top level. Convention is fixed in v1; restructuring is deferred to v2 if catalog consumers complain.
- **Status:** addressed

## F-34 — Severity: minor
- **Section:** §4 Implementation Sketch — Step 7 BP pattern `example_phrasings`
- **Description:** Step 7 now includes `example_phrasings` for each of the 3 v1 patterns (e.g., for BP-001: "The hook fires correctly because I observed it"; "The reviewer saw X"; "This is the documented behavior"). These phrasings are designer-fabricated illustrations, not derived from observed incidents in the operator's fleet. The patterns are intended to detect real failure modes that have already occurred; the example phrasings should be grounded in those incidents. Fabricated examples may not match the actual language patterns the skill will see in real incident packets.
- **Suggestion:** Either (a) note explicitly in Step 7 that `example_phrasings` in v1 are illustrative placeholders and will be replaced with real incident-grounded examples as the pattern library grows (per Step 9 wiki writes), or (b) require that v1 `example_phrasings` be derived from existing handoffs (e.g., the operator reviews past incidents and identifies actual phrases that would have triggered each pattern). Option (a) is honest about v1's limitations; option (b) is more rigorous. Either way, do not ship fabricated examples as if they were empirically grounded.
- **Response:** Option (a) implemented. Step 7 prose now begins with a "Note on `example_phrasings` (F-34)" paragraph: v1 example phrasings for BP-001/007/008 are illustrative placeholders based on the McCormick taxonomy definitions and the operator's mental model, not empirically grounded in observed fleet incidents. As v1 progresses, `/behave` Step 9 (feedback-to-wiki) accumulates real incident-grounded phrasings into `P:/.data/wiki/concepts/governance-pattern-library.md`, and the SKILL.md Step 7 entries are refreshed to cite observed phrasings (with source incident paths). v1 ships with placeholders; v1.1 replaces them.
- **Status:** addressed

## F-35 — Severity: minor
- **Section:** §3 Architecture — Reuse contract verification (lines 89-99) vs frontmatter (lines 130-134)
- **Description:** The reuse contract verification table honestly admits that `evidence-tier-calibration` and `cross-model-review` are "Partial" — they are documented procedures, not named `provides:` entries in `/why`'s frontmatter. But the `/behave` frontmatter still lists them as `consumes:` entries alongside the named ones. The frontmatter is supposed to be machine-readable catalog data (per the skill catalog format). Mixing named interfaces and procedure-references under the same `consumes:` field is a documentation mismatch: catalog consumers cannot tell which consumes are interface invocations and which are procedure references.
- **Suggestion:** Distinguish the two in the frontmatter. Two options: (a) add a sub-field `consumes_procedures: [evidence-tier-calibration, cross-model-review]` separate from `consumes: [pattern-library-query, feedback-to-wiki]`, or (b) mark each entry with a type tag (e.g., `consumes: [{name: pattern-library-query, type: interface}, {name: evidence-tier-calibration, type: procedure}]`). Option (b) is more explicit. Whichever you pick, document it in §3 so catalog consumers know how to interpret.
- **Response:** Option (a) implemented. The frontmatter now has two distinct fields: `consumes:` for named `/why` interfaces (currently `[why.pattern-library-query, why.feedback-to-wiki]`) and `consumes_procedures:` for `/why` documented procedures invoked by reference (currently `[why.evidence-tier-calibration, why.cross-model-review]`, with procedure citations). §3 has a new "Frontmatter convention (F-35)" paragraph documenting the distinction and the migration rule: if `/why` v4 promotes a procedure to a named `provides:` entry, it moves from `consumes_procedures:` to `consumes:` without methodology change. The two fields are mutually exclusive per entry.
- **Status:** addressed

## F-36 — Severity: minor
- **Section:** §13 Implementation Plan — Unit disposition language
- **Description:** The plan says: "Units 1-4 are sub-units of one rollback unit (the SKILL.md); they are committed together and rolled back together. Units 5-8 are independently revertible." But each of Units 1-4 has its own `Disposition: COMMIT_THIS_SESSION` line. The plan's prose says "committed together" but the unit dispositions treat them as separate commits. If each is committed separately, the "together" language is inaccurate; if they are committed as one, the per-unit `Disposition` line is misleading.
- **Suggestion:** Either (a) clarify that Units 1-4 are committed as a single commit (and remove per-unit `Disposition: COMMIT_THIS_SESSION`, replacing with "Units 1-4: one commit, one rollback"), or (b) clarify that they are committed sequentially as separate commits (and remove "committed together" from the prose). Pick one. Currently the wording is internally contradictory.
- **Response:** Option (a) implemented. The §13 opening prose now has a "Disposition convention (F-36)" paragraph: Units 1-4 share `Disposition: SINGLE_COMMIT_GROUP` (one commit, one rollback); Units 5-8 each carry `Disposition: COMMIT_THIS_SESSION`. Units 1-4 disposition lines were updated to `Disposition: SINGLE_COMMIT_GROUP (part of Units 1-4; one commit, one rollback; see F-36)`. The contradiction between prose and per-unit disposition is eliminated.
- **Status:** addressed

## F-37 — Severity: nit
- **Section:** §4 Implementation Sketch — argument-hint (line 119)
- **Description:** `argument-hint: <incident-packet-path> [--include-incident] [--share-incident]` does not specify whether flags go before or after the positional argument. Some CLI parsers are strict (Grok Build's parser may be one of them); if flags must come before positional args, the hint is misleading.
- **Suggestion:** Verify the order against Grok Build's CLI parser. Either move flags before the positional (`[--include-incident] [--share-incident] <incident-packet-path>`) or add a note that flags are position-independent.
- **Response:** Implemented. `argument-hint` reordered to `[--include-incident] [--share-incident] <incident-packet-path>` with an inline note: "flags precede the positional argument; Grok Build CLI parser treats flags as position-independent but listing them first matches the conventional hint order." The reorder addresses the case where the parser enforces flag-before-positional ordering.
- **Status:** addressed

## F-38 — Severity: nit
- **Section:** §16 Open Questions — [UNKNOWN] premises #4 and #5
- **Description:** [UNKNOWN] #4 (`why_version_max`) and #5 (Phase 1 handoff selection) are not "open questions" in the philosophical sense; they are "prerequisites for implementation that require operator input." Putting them in §16 Open Questions alongside genuinely-uncertain premises (e.g., "whether a diagnostic skill can reliably detect self-protection patterns") muddies the meaning of "open question." A reader scanning §16 cannot tell which unknowns block implementation and which are deferred-to-v2.
- **Suggestion:** Split §16 into two sections: "Open Questions" (philosophical unknowns, v2 candidates) and "Implementation Prerequisites" (operator inputs required before implementation can begin). Move #4 and #5 to the prerequisites section. This also makes F-26 / F-27 easier to resolve by surfacing them as preconditions rather than as questions.
- **Response:** Implemented. §16 is now titled "Open Questions and Implementation Prerequisites" and split into two parts. "Open Questions" retains the philosophical [INFERENCE] and [UNKNOWN] premises (renumbered #1-3 under [UNKNOWN] after [F-26 / F-27 moved]). "Implementation Prerequisites" is a new section with two entries: #1 (why_version_max — blocks Unit 1; F-26) and #2 (Phase 1 test-set handoff — blocks Unit 6 acceptance; F-27). Each prerequisite has an explicit decision rule and resolution path.
- **Status:** addressed

## F-39 — Severity: nit
- **Section:** §10 Key Decisions — table bloat
- **Description:** §10 grew from 9 to 13 entries. Some of the new entries (Three rollback modes, INSUFFICIENT_EVIDENCE counter on the report, CLI flags governed by booleans) are design decisions documented elsewhere in the design (F-12, F-14, F-21). Listing them in §10 with rationale duplicates information that is already in §4, §8, §9, §12. The Key Decisions table should be a high-signal summary, not a log of every design choice.
- **Suggestion:** Either (a) trim §10 to ~8 high-level decisions (the original 9 minus ones that were relabeled, plus the new "Output schema: structured YAML with `dimensions:` keyed map" entry — the most consequential new decision), or (b) explicitly label §10 as "Decisions Log" and accept that it duplicates §4/§12 content. Option (a) restores the original purpose of Key Decisions (high-signal summary).
- **Response:** Option (a) implemented. §10 trimmed from 13 to 8 entries. Dropped (duplicated in §4, §9, §12, §13): "Allow INSUFFICIENT_EVIDENCE", "8 implementation units", "INSUFFICIENT_EVIDENCE counter on the report itself", "CLI flags governed by input contract booleans", "Three rollback modes". Retained as high-signal: separate-skill choice, diagnostic-not-enforcement, v1=3-patterns, /why reuse, /behave naming, dimensions: keyed map schema, replay fixture, /why Step 15 wiki writes. The "Output schema: structured YAML with `dimensions:` keyed map" entry was expanded to note the F-33 convention (dimensions nested vs operational fields flat).
- **Status:** addressed

---

## Updated cross-cutting checks

### Scope constraints honored from handoff (unchanged)

| Constraint | Honored? | Evidence |
|---|---|---|
| Diagnostic not enforcement | Yes | §1, §3 "What the skill is NOT", §7 alternative C rejected |
| v1 = 3 patterns | Yes | §1, §4 Step 7, Unit 3 acceptance criteria |
| Separate skill, not merge into /tp | Yes | §7 alternatives A/B rejected, Unit 1 creates new SKILL.md |
| No Claude Code hooks | Yes | §5 API/Interface Changes |

### 7-dimension contract preservation

The 7 dimensions are now structurally enforced via the `dimensions:` keyed map (d1 through d7). Each dimension's output is nested under its dimension key. **F-04 is fully resolved.**

### Hypothesis discipline

Unchanged from prior review. The design uses `/why`'s 7-tier system and adds a status inflation check in Step 2. The original `/behave`'s specific mechanics are not explicitly retained or replaced. **Still a clarifying-edit suggestion, not a blocker.**

### Replay fixture testability

Unchanged. The fixture is a markdown file, manual in v1, deterministic. The Phase 1 acceptance is now well-defined (three archetypes, baseline capture, ≥2 of 3 + 0 false positives). **F-13 is fully resolved at the criteria level, but F-27 notes that the test set selection is not assigned to any implementation unit.**

### Repair contract advisory-only check

`acceptance_criteria: [<quantified-criterion>, ...]` is now in the schema. The "be more careful" rule is documented in Step 9 prose. **F-10 is fully resolved.**

### Skill name justification

Unchanged. Justified but "original is Claude-only" still lacks a receipt.

### BE-01 vs VI-01 separation

Unchanged. §7 explicitly maintains the separation. /tp, /why, /debrief untouched.

### Frontmatter catalog hygiene

**F-35** notes a new mismatch between the frontmatter (which lists `evidence-tier-calibration` and `cross-model-review` as `consumes:` entries) and the §3 reuse contract verification (which says they are procedures, not named `provides:` entries). The design acknowledges the gap but does not resolve it in the frontmatter itself.

---

## Summary table — new findings

| ID | Severity | Section | One-line issue |
|---|---|---|---|
| F-26 | major | §4 frontmatter | `why_version_max: <TBD>` is a placeholder that blocks Unit 1 ship |
| F-27 | major | §12 / §13 | Phase 1 handoff-selection precondition not assigned to any implementation unit |
| F-28 | minor | §4 Step 8 | Cross-model reviewer selection logic duplicated from `/why` Step 15b |
| F-29 | minor | §4 schema | 4th value in `reviewer_response_schema` (`<path-or-uri-of-full-schema>`) is unexplained |
| F-30 | minor | §4 metadata | `operator_id` source (runtime vs operator-supplied) unspecified |
| F-31 | minor | §4 Step 4 | Per-claim `evidence_tier` has no assignment rubric |
| F-32 | minor | §4 schema | Per-claim `evidence_tier` vs report-level `confidence` derivation not documented |
| F-33 | minor | §4 schema | `dimensions:` keyed map vs flat operational fields convention undocumented |
| F-34 | minor | §4 Step 7 | BP `example_phrasings` are designer-fabricated, not incident-grounded |
| F-35 | minor | §3 / frontmatter | Frontmatter `consumes:` lists procedures alongside named interfaces without distinction |
| F-36 | minor | §13 disposition | "Committed together" language contradicts per-unit `Disposition: COMMIT_THIS_SESSION` |
| F-37 | nit | §4 argument-hint | Flag positional order not specified |
| F-38 | nit | §16 Open Questions | Implementation prerequisites mixed with philosophical unknowns |
| F-39 | nit | §10 Key Decisions | Table has grown from 9 to 13 entries; duplicates §4/§12 content |

**Total new findings: 14** (2 major, 9 minor, 3 nit).

---

## Reviewer recommendation

The design is **close to implementable**. The two major new findings (F-26, F-27) must be resolved before implementation begins:

- **F-26** is a documentation blocker — Unit 1 cannot ship with `<TBD>` in frontmatter. Either decide `why_version_max` now, or move it to a clearly-marked "Implementation Prerequisite" section.
- **F-27** is a procedural blocker — Phase 1 acceptance criteria require operator action (creating the rollout handoff with three archetype handoffs and a baseline). Without this unit (or a documented operator prerequisite), Phase 1 cannot be measured.

Once these are resolved and the minor findings are addressed in the same revision pass, the design can proceed to implementation under `/go`. The 14 new findings are mostly documentation-quality issues that won't block implementation if noted for v1.1 follow-up.

**Priority for the writer's next pass:**
1. F-26, F-27 (blockers)
2. F-28, F-29, F-30, F-31 (schema/payload contract clarifications that an implementer will need)
3. F-32, F-33, F-34, F-35 (consistency)
4. F-36, F-37, F-38, F-39 (wording and structure)

---

## Revision Summary (post re-review pass)

**Pass scope:** all 14 new findings (F-26 through F-39) addressed in a single revision of `grok-design-doc-81539877.md`. No prior findings (F-01 through F-25) regressed.

**Severity breakdown:**
- 2 major (F-26, F-27) — both implementation blockers resolved with operator-action preconditions surfaced in a new §16 "Implementation Prerequisites" section.
- 9 minor (F-28, F-29, F-30, F-31, F-32, F-33, F-34, F-35, F-36) — schema/convention/rubric clarifications.
- 3 nit (F-37, F-38, F-39) — wording and structure.

### Per-finding resolution map

| ID | Section(s) modified | Change summary |
|---|---|---|
| F-26 | §4 frontmatter, §13 Unit 1 acceptance, §16 (split) | `<TBD>` placeholder replaced with `"OPERATOR_SET_BEFORE_V1_SHIP"` YAML sentinel; §16 split into Open Questions + Implementation Prerequisites; Prerequisite #1 documents decision rule and resolution path. |
| F-27 | §13 (added Unit 0), §14 Traceability, §15 File Inventory, §16 (split) | Unit 0 added as operator-action precondition (`Disposition: OPERATOR_ACTION`); Unit 6 dependencies updated; rollout handoff added to file inventory and traceability matrix; §16 Prerequisite #2 documents resolution path. |
| F-28 | §4 Step 8 reviewer-selection bullet | Duplicated `glm-5-2 → /codex → parent-inherited` chain removed; replaced with reference to `/why` Step 15b's selection logic and explicit "no delta" statement. |
| F-29 | §4 schema (`reviewer_response_schema`) | 4th value documented in-line: optional pointer to extended response schema, used only when operator has configured a custom reviewer with additional fields; not produced under v1 defaults. |
| F-30 | §4 schema (`metadata`), §4 Step 10 prose | Each metadata field annotated with runtime source; `operator_id` documented as advisory runtime-sourced (not auth/authorization); Step 10 adds "Metadata provenance (F-30)" paragraph. |
| F-31 | §4 schema (`d4_claim_verification`), §4 Step 4 prose | `tier_rationale: <string>` field added to schema; Step 4 adds "Tier assignment rubric (F-31)" paragraph with operator-assigned-with-rationale model and canonical tier definitions. |
| F-32 | §4 schema (top-level), §4 Step 10 prose | `confidence_basis: <string>` field added; Step 10 "Confidence derivation (F-32)" paragraph documents `min(material_claim_tiers)` rule and zero-material-claims fallback. |
| F-33 | §4 schema preamble | "Convention (F-33)" paragraph explicitly documents dimensions-nested vs operational-flat structure; v2 restructure noted as deferred. |
| F-34 | §4 Step 7 intro | "Note on `example_phrasings` (F-34)" paragraph added: v1 phrasings are illustrative placeholders; v1.1 replaces with observed phrasings via Step 9 wiki writes. |
| F-35 | §4 frontmatter, §3 prose | Frontmatter split into `consumes:` (named interfaces) + `consumes_procedures:` (referenced procedures); §3 "Frontmatter convention (F-35)" paragraph documents mutual-exclusivity and migration rule. |
| F-36 | §13 opening prose + Units 1-4 disposition lines | "Disposition convention (F-36)" paragraph added; Units 1-4 disposition lines changed to `SINGLE_COMMIT_GROUP`; Units 5-8 unchanged at `COMMIT_THIS_SESSION`. |
| F-37 | §4 frontmatter (`argument-hint`) | Flag order moved before positional: `[--include-incident] [--share-incident] <incident-packet-path>` with inline parser note. |
| F-38 | §16 (entire section restructured) | Title → "Open Questions and Implementation Prerequisites"; split into Open Questions (philosophical) and Implementation Prerequisites (operator-input blockers). |
| F-39 | §10 Key Decisions | Trimmed from 13 to 8 entries; dropped decisions duplicating §4/§9/§12/§13; preamble added explaining high-signal intent. |

### Cross-cutting edits that touched multiple findings

- **§16 split (F-38)** drove the structural fix for both F-26 and F-27 by surfacing them as prerequisites rather than questions. F-26 prerequisite #1 and F-27 prerequisite #2 reference the new sections elsewhere (Unit 1 acceptance criteria, §13 Unit 6 dependencies).
- **Frontmatter restructure (F-26 + F-35)** — the `why_version_max` placeholder fix and the `consumes:`/`consumes_procedures:` split were applied together to avoid a duplicate frontmatter edit.
- **Step 4 / Step 10 prose expansion (F-30 + F-31 + F-32)** — three findings all touched the metadata/output schema prose; consolidated into Step 4 (tier rubric), Step 10 (metadata provenance + confidence derivation), and inline schema annotations.

### What did NOT change

- All 25 prior findings (F-01 through F-25) remain addressed as documented in the prior pass. No regression detected.
- The 7-dimension contract preservation (F-04), input contract (F-14), and output schema field set are unchanged; only annotations, conventions, and rubric prose were added.
- The §17 Coupling & Code-Smell Inventory is unchanged.
- Risk Table (§11) is unchanged; new findings did not introduce new risks.

### Open follow-ups (not blocking implementation)

- The 4th value in `reviewer_response_schema` (F-29) is documented as "reserved for non-default configurations"; no v1 reviewer produces it. If `/why` v4 introduces a custom-reviewer path, the 4th value's semantics may need elaboration.
- The `confidence_basis` field (F-32) is new and may need adjustment after first v1 runs surface zero-material-claim reports.
- `consumes_procedures` (F-35) is an extension to the frontmatter schema; if `index_skills.py` does not yet recognize the new field, the catalog entry for `/behave` may show the field as ignored. Confirm catalog regeneration handles the new field correctly during Unit 7.

— End of re-review —
