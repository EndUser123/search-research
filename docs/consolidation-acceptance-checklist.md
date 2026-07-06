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

# Where the split material lands (no new user-facing commands)

**Constraint:** the retained top-level command set is fixed — `/improve`, `/red-team`, `/review` (or `/code-review`), `/debrief`, `/claude-audit`, `/skill-audit`, `/wiki`. No new commands or visible modes are created from this material. Everything below is internalized into existing skills, or stays in this checklist.

## 1. Reusable transcript bad-behavior detection → internal rubric in `/debrief`

When `/debrief` runs over a transcript/chain, it applies this rubric as an internal check (not a separate mode, not a separate command). Findings ride the existing /debrief finding shape (`[FACT]/[INFERENCE]/[UNKNOWN]` + origin tags).

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

Finding shape (reuses /debrief's existing fields): `id`, `behavior_type`, `severity (BLOCK/REVISE/NIT)`, `transcript_evidence (quote + turn)`, `source_evidence (file:line, if relevant)`, `why_it_matters`, `correction`, `verification_step`.

**Why internal, not a mode:** the goal is fewer visible commands. A user typing `/debrief` already expects transcript analysis; the rubric is just /debrief doing its job more thoroughly, not a new surface to learn.

## 2. Compact-event goal drift → internal check in `/debrief`

When the walked chain contains compaction/handoff markers, `/debrief` runs an internal drift check: compare pre-compact goal/constraints → what the compact summary preserved → what the post-compact session actually optimized for. Emit a finding when post-compact behavior diverges from the pre-compact goal without an explicit decision in the transcript.

Mechanism reuses `session_chain.walk_session_chain()` (shipped, #1176). Natural no-op when the chain has no compaction events — so it costs nothing outside its trigger condition, and there is no reason to gate it behind a flag.

## 3. Consolidation-specific compliance → this checklist only

The 13-row acceptance table above. Not wired into any skill. Phase 7 (#1196, #1199) runs it as a one-shot gate against the post-consolidation codebase.

## 4. Instruction-compliance ("did the implementer follow instructions?") → `/red-team` critic behavior

When `/red-team` reviews an implementation, its critic/acceptance pass applies an instruction-compliance check: for each instruction in the originating spec/plan, mark `PASS | FAIL | PARTIAL | NOT VERIFIED | N/A` with `evidence`, `gap`, `fix` columns. Any BLOCK or unresolved FAIL ⇒ `/red-team` does not emit PROCEED.

This is internal critic behavior, not a new `/red-team-improve` or `/compliance` command. It activates when `/red-team` is reviewing a shipped implementation against a spec — its existing job, with a structured acceptance layer.

## 5. `/improve` routing note (the only `/improve` change)

One paragraph in `skills/improve/SKILL.md`:

> If the user asks about transcript/session bad behavior, instruction compliance, false claims, lazy reasoning, or compact drift, **route instead of absorbing**: `/debrief` for historical transcript review, `/red-team` for pre-ship implementation verification. `/improve` is the thought-partner for improving work; it is not the auditor of past sessions or the verifier of shipped code.

This is the entire `/improve` change. No new mode, no absorbed audit role.

## 6. `/wiki` unchanged

`/wiki` remains the downstream long-term memory ingest tool, approval-gated. No `/wiki-ingest`. Criterion 5 in the acceptance table enforces this.

---

## Constraint: do not duplicate live gates

The primary prevention mechanisms for false completion, unsupported claims, and evidence failures are the existing automated gates:

- `semantic_critic` (reasoning review), `fabrication_detector` (fake tool-use), `cross_validator` (evidence for "done"), `unverified_stance` (empty hedges), `cks_quality_gate` (CKS ingest).
- `/red-team`, `/pre-mortem`, `/adversarial-review`, `/code-review` for adversarial passes.

The /debrief internal rubric (item 1) and compact-drift check (item 2) are *post-hoc transcript audit*, not replacements for the inline gates. They catch patterns the inline gates do not target (name-based inference, sycophancy, constraint loss across compaction). That gap is the reason they live in /debrief at all. Do not re-implement them as long inline prompt ceremony elsewhere. If a future gap is identified that the gates cannot cover, name the gap and the discriminating corpus evidence before adding a new gate (per `feedback_gate_discrimination_rule`).
