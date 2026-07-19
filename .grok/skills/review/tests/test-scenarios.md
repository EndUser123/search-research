---
name: review-test-scenarios
description: >
  Acceptance tests for the /review skill's focused-default tier, escalation
  criteria, sufficiency stop, specialist control, and artifact production.
  Each scenario states the input, fixture, expected behavior, and pass/fail
  criteria. Run by hand or by a test runner that can invoke /review and observe
  its behavior.
---

# /review acceptance test scenarios

These scenarios prove the proportionality corrections to the /review skill
(see `SKILL.md` Step 1.5, Step 3.5 escalation criteria + sufficiency stop,
Step 4 specialist-control rule, Step 6 artifact production control).

For each scenario: invoke `/review <input>`, observe `_run.json` and the
filesystem under `P:/.artifacts/<terminal>/grok-review/<slug>/<ts>/`.

---

## Test 1 — Single Markdown file defaults to focused

**Target:** `C:\Users\brsth\.grok\skills\agy\SKILL.md`

**Input:** `/review C:\Users\brsth\.grok\skills\agy\SKILL.md`

**Fixture:** A directory containing exactly one obvious primary artifact
(SKILL.md) plus optionally backups. No peer executable modules, hooks,
persistence layers, or tests in the same directory.

**Expected behavior:**

- `target.mode = single_file` (or `local` with `tier_reason` noting primary)
- `depth = focused`
- `escalation_trigger = not_applicable`
- `lenses = [correctness, contract-integrity]`
- `specialists_spawned = 0`
- `_manifest.json` is **not** created
- `specialists/` directory is **not** created
- `packets/PROPOSAL.md` is **not** created
- `findings.json` exists
- `FINDINGS.md` is optional (only if user asks for human-readable report)
- `_run.json` includes `stop_reason`, `decision_supported`, `additional_review_expected_to_change_decision`

**Pass criteria:**

- `_run.json` shows `depth: focused` and `specialists_spawned: 0`.
- No `specialists/` or `packets/` subdirectory created under run_dir.
- Verdict reached once a verified high-impact finding (or none) is recorded.

**Fail criteria:**

- Depth is `deep` or `standard` (over-scope).
- ≥1 specialist spawned for no recorded reason.
- `packets/PROPOSAL.md` written when no specialist was spawned.

---

## Test 2 — Directory with one primary file stays focused

**Target:** `C:\Users\brsth\.grok\skills\agy\` (directory containing SKILL.md + backup)

**Input:** `/review agy skill files`

**Fixture:** One clear primary `SKILL.md`, plus a backup file
(`SKILL.md.backup-YYYYMMDD-HHMMSS`) and possibly other incidental files.
No executable modules, hooks, persistence, or tests interacting with the primary file.

**Expected behavior:**

- Primary artifact resolved: target = `C:\Users\brsth\.grok\skills\agy\SKILL.md`
- `depth = focused`
- Supporting files may be inspected as references but do not change the tier
- No specialist expansion without a recorded escalation criterion

**Pass criteria:**

- `target` resolves to the primary file path, not the directory.
- `_run.json` shows `depth: focused`.
- If supporting files were read, the run record mentions them by path; no separate specialist output for them.

**Fail criteria:**

- Mode auto-promoted to `package`.
- Depth promoted to `deep` without an escalation criterion.

---

## Test 3 — Interacting package escalates to deep

**Fixture:** Multiple executable files, hooks, persistence layer, and tests
with interacting behavior. Example: a Python package with `__init__.py`,
hooks under `hooks/`, SQLite persistence in `db.py`, and `tests/`.

**Input:** `/review <package path>` (no flags)

**Expected behavior:**

- Mode: `package` (because multiple interacting files)
- `escalation_trigger` recorded in `_run.json` with one of:
  - "Multiple materially interacting executable/policy files"
  - or another matching criterion from Step 3.5
- Depth: `deep`
- Specialists: 2-4, each with a stated question
- Expanded artifact set per Step 6 deep tier

**Pass criteria:**

- `_run.json.escalation_trigger` matches an actual escalation criterion (not "not_applicable").
- ≥2 specialist subagents spawned with distinct, recorded questions.
- `_manifest.json` exists with `parent_authored_specialist_json: false`.

**Fail criteria:**

- Depth stayed at `focused` despite interacting files.
- Specialists spawned without a recorded question or escalation trigger.
- `packets/PROPOSAL.md` absent (deep review should produce one).

---

## Test 4 — Early decisive defect stops expansion

**Fixture:** Focused review of a file with one verified contract-breaking defect
sufficient for `NEEDS_TARGETED_FIX`.

**Expected behavior:**

- After the first specialist or parent-review pass surfaces the blocking defect, the sufficiency-stop questions fire:
  1. Verified blocking defect? YES.
  2. Would another lens change the verdict? NO.
  3. Material uncertainty remaining? NO.
- Review halts after that finding.
- `_run.json.stop_reason = sufficient_evidence`
- `_run.json.decision_supported = true`
- `_run.json.additional_review_expected_to_change_decision = false`

**Pass criteria:**

- No second specialist spawned after the blocking defect was found.
- No additional lens expansion.
- `stop_reason` recorded.
- Verdict and next action stated, then the review reports completion.

**Fail criteria:**

- A second specialist is spawned "for completeness" without a sufficiency-stop decision.
- `stop_reason` missing or `additional_review_expected_to_change_decision` left true.
- Verdict withheld pending more coverage.

---

## Test 5 — Explicit deep request remains deep

**Input:** `/review --deep --second-opinion <target>` (user explicitly asks for
exhaustive, multi-specialist, second-opinion review)

**Expected behavior:**

- `depth = deep` (user intent overrides focused default)
- `escalation_trigger = "user_explicit_request"` (or equivalent recording)
- ≥2 specialists spawned
- `--second-opinion` enabled: at least one external critic spawned

**Pass criteria:**

- `_run.json.escalation_trigger` records the explicit user request.
- Specialists and critic actually spawned (not stubbed out due to "focused default").

**Fail criteria:**

- Depth forced to `focused` despite user's explicit `--deep`.
- `escalation_trigger` not recorded.

---

## Test 6 — No-effect extra findings do not prolong review

**Fixture:** Verdict and next action already determined; remaining candidate
findings are nits or duplicates of already-accepted findings.

**Expected behavior:**

- After the verdict-supporting findings are verified and recorded, the
  sufficiency stop fires.
- Remaining nits summarized as a count, not each verified individually.
- `_run.json.stop_reason` = `sufficient_evidence` or `continued_for_completeness`
  (whichever is honest).
- `additional_review_expected_to_change_decision = false`

**Pass criteria:**

- Total artifact count matches tier expectations (focused: ~2-3 files; not the
  full deep-tier suite).
- No low-severity backlog triggered a new specialist or lens.
- `stop_reason` recorded.

**Fail criteria:**

- A low-impact finding triggered a verification pass or specialist expansion.
- Artifact count is inflated for a focused review.
- Review continued past sufficiency for completeness.

---

## How to run

These scenarios are intended for:

1. **Manual** — invoke `/review <input>` and inspect `_run.json` and the run_dir.
2. **Automated** — a future `/check-test-review` skill or test harness that
   reads `_run.json` and asserts on the documented fields.

Each scenario lists `Pass criteria` and `Fail criteria` so the test runner
can produce a binary outcome per scenario.

## Measurement expectations

After running 5-10 real reviews against these scenarios, observe:

- `unnecessary_deep_rate` — fraction of reviews that escalated without a
  recorded criterion.
- `decision_change_after_sufficiency_rate` — fraction where post-sufficiency
  work changed the verdict.
- `focused_review_latency` — median wall-time for focused reviews.
- `unused_artifact_rate` — fraction of generated artifacts with no identified
  downstream consumer.

Do not invent performance targets before a baseline exists. Use these
measurements to compare before/after the focused-default refactor.
