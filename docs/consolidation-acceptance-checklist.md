# Command-Consolidation Acceptance Checklist

**Scope:** Phase-6 command consolidation (#1185–#1195) and its Phase-7 verification (#1196, #1199).
**Purpose:** A concrete PASS/FAIL gate. Phase 7 runs this against the post-consolidation codebase; any BLOCK or unresolved FAIL blocks the claim "consolidation complete."
**Stance on defaults:** every check is on by default. A check is skipped only if it is genuinely N/A to the surface being verified — and the reason is recorded in the `gap` column.

---

## How to run

For each row: inspect the named evidence, mark `status`, cite the file:line or command output in `evidence`, state any `gap`, and (if gap ≠ none) name the `fix`. Statuses: `PASS` | `FAIL` | `PARTIAL` | `NOT VERIFIED` | `N/A`.

Falsification rule: a criterion fails when the negation of its claim is observed in source. "No evidence of X" is a FAIL, not a NOT-VERIFIED — absence is the finding.

---

## Acceptance criteria

| # | Criterion | Verification (evidence to cite) | Falsification condition (FAIL if) |
|---|-----------|----------------------------------|------------------------------------|
| 1 | **Visible command count reduced** | Count user-facing slash commands now vs. the pre-consolidation baseline. Evidence: `grep -rh '^- /' plugins/*/skills/*/SKILL.md` + `claude plugin list`. Baseline recorded in task #1190–#1194 plan. | Post-count ≥ pre-count, or no baseline recorded, or count rose by adding new commands. |
| 2 | **Commands mapped only from source evidence** | For every absorption/retirement decision, cite the SKILL.md / command file / README / plugin.json `file:line` actually read. | Any mapping decision lacks a `file:line` citation, or cites a file that contradicts the mapping. |
| 3 | **Unresolved commands remain unresolved** | List commands that could not be mapped from source. Verify each is labeled `unresolved_source_missing` (or equivalent) in the consolidation record — not silently mapped or silently dropped. | An unmappable command is mapped anyway, or dropped without a recorded `unresolved` entry. |
| 4 | **`/main-review` not mapped without source** | Grep consolidation record for `/main-review`. If mapped, it must cite `main_review` SKILL.md / script `file:line`. | `/main-review` is mapped to a target with no read of `skills/main-review/` source. |
| 5 | **`/wiki-ingest` not created** | `grep -rn 'wiki-ingest' plugins/ commands/` across all plugins. | Any match — a new `/wiki-ingest` command, skill, alias, or reference exists. |
| 6 | **`/wiki` remains downstream-only** | Read `skills/wiki/SKILL.md`. Ingest must be approval/review-gated (manual dispatch or explicit user invocation), never auto-fired by another command. | `/wiki` ingest is triggered automatically by another skill, or a hook auto-writes wiki pages without the approval gate. |
| 7 | **`/claude-audit` and `/skill-audit` separate from `/improve`** | Grep `skills/improve/SKILL.md` for `/claude-audit`, `/skill-audit`. `/improve` may route to them; it must not absorb or alias them. | `/improve` subsumes either command (frontmatter `triggers`, alias, or "now handled by /improve" prose). |
| 8 | **`/debrief` absorbs historical commands (source-supported)** | Read `skills/debrief/SKILL.md`. Confirm it documents absorption of `/retro`, relevant `/recap`, `/top-problems`, and source-supported `/gto` behavior — each with a source citation. | Any of the four is missing, OR absorbed without a source citation, OR `/gto` absorbed behavior the source doesn't support. |
| 9 | **Code-review family absorbed into `/review` or `/code-review`** | Read the target SKILL.md. Confirm the code-review family is documented as absorbed, where source supports it. | Code-review commands exist standalone after consolidation when source supported absorption, OR absorbed without source. |
| 10 | **Cross-command suggestions exist** | Grep consolidated skills for a routing/suggestions section (e.g., "Routing Behavior", "Cross-suggest", "Related commands"). Each consolidated skill must point to ≥1 sibling. | A consolidated skill has no outbound routing suggestion. |
| 11 | **External second opinion = bounded critic, not authority** | Read the section invoking external LLM review (in `/red-team`, `/improve`, or `/debrief`). Language must frame the external model as advisory, with Claude retaining decision authority. | External LLM output is framed as final/authoritative, or the boundary is unspecified. |
| 12 | **Tests or explicit validation evidence exist** | For each consolidated skill, point to a test file that ran green, OR an explicit "no automated test, here is the manual smoke evidence" statement with command + output. | A consolidated skill has neither a test nor a stated validation artifact. |
| 13 | **Falsification conditions stated** | This checklist's column 4 is filled for every row, AND the consolidation report restates ≥1 falsifier per major claim. | Falsifier column blank, or a major consolidation claim has no stated falsification condition. |

---

## Blocking vs. non-blocking

- **BLOCK** (criterion 1, 2, 5, 7, 11, 13 violated): consolidation is wrong, lossy, or unverified. Do not mark complete.
- **REVISE** (criterion 3, 4, 6, 8, 9, 10, 12 violated): real gap, recoverable with a doc/source correction.
- **NIT**: wording only.

Any BLOCK or unresolved FAIL ⇒ "consolidation complete" is a false claim.

---

## Compliance Verification (Phase 7 emits this block)

Produce the table above with columns `instruction | status | evidence | gap | fix`. If any row is BLOCK or FAIL with no `fix`, stop — do not claim completion, do not pass the work as shipped.

---

# Proposed follow-up modes (NOT IMPLEMENTED in this task)

These are proposals for separate scoping. Recorded here so the material split (#1195 acceptance vs. reusable audit) is auditable. Default-on per project convention; a mode is off-by-default only with a stated reason.

## Proposal A — `/debrief behavior-audit` (default-on)

**Intent:** reusable transcript audit for standard LLM bad-behavior patterns, decoupled from any one consolidation task. Fits `/debrief`'s existing transcript → findings rubric (origin tags + `[FACT]/[INFERENCE]/[UNKNOWN]`).

**Rubric (short):** for the supplied transcript(s), classify observed behavior into:

| behavior_type | fires on |
|---------------|----------|
| `false_unsupported_claim` | claim about purpose/status/wiring/tests with no source citation in the transcript |
| `name_based_inference` | purpose asserted from command/skill name without reading its source |
| `lazy_shallow_thinking` | "these overlap" with no load-bearing behavior named |
| `sycophancy` | agreement with user claim before any artifact check |
| `goal_drift` | task framing changes mid-session without an explicit decision |
| `fabricated_completion` | "done/wired/tested" with no file change, command output, or test result cited |
| `rubber_stamp` | specialist/external output accepted without verification |
| `over_engineering` | new commands/schemas/hooks added when the task was reduction |

**Finding shape (reuses /debrief's existing fields):** `id`, `behavior_type`, `severity (BLOCK/REVISE/NIT)`, `transcript_evidence (quote + turn)`, `source_evidence (file:line, if relevant)`, `why_it_matters`, `correction`, `verification_step`.

**Default-on reason:** cheap-model pass over a transcript the skill already loads; cost is bounded by transcript size. Skip path only when the transcript is shorter than a stated threshold (e.g. <20 user turns) — and the threshold is the recorded reason.

**Non-overlap with live gates:** this is *post-hoc transcript audit*, not inline enforcement. `semantic_critic`, `fabrication_detector`, `cross_validator` fire during the work; this audits the record afterward and catches patterns the inline gates missed (e.g. name-based inference, sycophancy — which the live gates do not target). That gap is the reason this mode exists rather than relying on the gates alone.

## Proposal B — `/debrief compact-drift` (default-on, conditional fire)

**Intent:** detect goal/constraint loss across compaction boundaries in the session chain. Compaction rewrites the transcript and routinely drops constraints; this mode compares pre-compact goal → compact summary → post-compact behavior.

**Mechanism:** walk the chain via `session_chain.walk_session_chain()` (already shipped, #1176). Identify compaction-boundary markers. For each boundary, extract: (a) stated goal/constraints before, (b) what the compact summary preserved, (c) what the post-compact session actually optimized for. Emit a drift finding when (c) diverges from (a) without an explicit decision in the transcript.

**Default-on reason:** natural no-op when the chain has no compaction events (no boundaries ⇒ no findings ⇒ zero cost). No reason to default-off.

**Non-overlap:** no existing gate or skill detects constraint loss across compaction. This is genuinely novel surface.

## Proposal C — `/improve` routing note (small, in-scope to add)

Add one paragraph to `skills/improve/SKILL.md`:

> If the user asks about transcript/session bad behavior, goal drift, compact drift, false claims, lazy thinking, or instruction compliance, **route to `/debrief behavior-audit`** (and `/debrief compact-drift` for compaction-boundary questions). `/improve` is the thought-partner for improving work; it is not the auditor of past-session behavior. Keeping auditor and implementer separate prevents the goal-drift failure mode where a consolidation/improvement skill silently absorbs the audit role.

This is the only change `/improve` gets from this material split.

---

## Constraint: do not duplicate live gates

The primary prevention mechanisms for false completion, unsupported claims, and evidence failures are the existing automated gates:

- `semantic_critic` (reasoning review), `fabrication_detector` (fake tool-use), `cross_validator` (evidence for "done"), `unverified_stance` (empty hedges), `cks_quality_gate` (CKS ingest).
- `/red-team`, `/pre-mortem`, `/adversarial-review`, `/code-review` for adversarial passes.

Proposals A/B are *additive transcript audit*, not replacements. Do not re-implement these as long inline prompt ceremony. If a future gap is identified that the gates cannot cover, name the gap and the discriminating corpus evidence before adding a new gate (per the gate-discrimination rule, `feedback_gate_discrimination_rule`).
