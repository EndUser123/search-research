# Lightweight Evidence and Changelog Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give a solo director and AI coder a low-friction way to record material knowledge use and decisions without building a telemetry platform.

**Architecture:** Keep provenance as a short, human-readable section in the design or plan. Create a project `CHANGELOG.md` lazily when a material decision or implementation needs recording. Use one small idempotent writer and a mechanical evidence gate; do not capture every tool call or add hooks.

**Tech Stack:** Python 3.11+, Markdown, pytest, existing `/planning` evidence gate.

## Global Constraints

- Do not add tool-use telemetry, project manifests, decision capsules, retention systems, or hooks in this plan.
- Do not require `/find`, `/nlm`, `/wiki`, or `/check`; require honest disclosure when they were or were not used.
- `/risks` and `/red-team` remain read-only.
- Create files lazily and only when the current design or implementation is material.
- Changelog entries summarize material decisions; they are not an audit log.
- Missing evidence is a review gap, not automatically a blocker unless the plan claims implementation readiness based on it.
- Keep the workflow useful when the AI used internal knowledge or no external source.

---

## File map

- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/references/knowledge-validation-ledger.md`: define the compact evidence section and changelog convention.
- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/scripts/record_changelog.py`: add lazy creation, explicit path handling, and duplicate-safe entries.
- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/scripts/evidence_gate.py`: validate the compact ledger and changelog reference without pretending it proves runtime value.
- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/design/SKILL.md`: require the compact evidence section for material designs.
- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/SKILL.md`: make the evidence section and changelog entry the final lightweight promotion check.
- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/risks/SKILL.md`: read and critique declared evidence without writing files.
- Modify `P:/packages/.claude-marketplace/plugins/red-team/commands/red-team.md`: challenge unsupported research or validation claims.
- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/tests/test_record_changelog.py`: writer behavior tests.
- Modify `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/tests/test_evidence_gate.py`: gate behavior tests.
- Do not modify hook files, Go handoff logic, or every existing project in this plan.

### Task 1: Simplify the evidence contract

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/references/knowledge-validation-ledger.md`

- [ ] **Step 1: Replace** the large ledger example with this compact contract:

```markdown
## Knowledge / Validation

- Sources/checks used: `/wiki`, `/check`, or `none`
- Sources/checks not used: `/find`, `/nlm`, or `none`
- Evidence: `path/to/output`, URL, test command, or `none`
- Claims affected: [claim IDs or concise descriptions]
- Unverified claims: [claims or `none`]

## Change Record

- Changelog: `CHANGELOG.md`
- Entry ID: `PROV-20260712T184200Z-design`
- Entry status: `recorded`
```

- [ ] **Step 2: State** that invocation does not prove influence or validation, and that internal model knowledge must be disclosed as `internal/unverified` when material.
- [ ] **Step 3: State** that changelog creation is lazy and only material decisions receive entries.
- [ ] **Step 4: Review** the reference for enterprise-only concepts; remove event schemas, retention policy, project manifests, and decision capsules.
- [ ] **Step 5: Commit** with `docs: simplify evidence and changelog contract`.

### Task 2: Make changelog creation lazy and idempotent

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/scripts/record_changelog.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/tests/test_record_changelog.py`

**Interface:**

```text
python record_changelog.py <changelog-path> \
  --summary "..." \
  --sources "/wiki, /check" \
  --claims "..." \
  --evidence "path or command" \
  --entry-id "PROV-..." \
  --create-if-missing
```

- [ ] **Step 1: Add failing tests** for creating a blank `CHANGELOG.md`, inserting `## [Unreleased]`, recording an ISO-8601 UTC timestamp, preserving existing entries, and rejecting duplicate entry IDs.
- [ ] **Step 2: Run** `pytest -q P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/tests/test_record_changelog.py`; expected: failures for lazy creation.
- [ ] **Step 3: Implement** `--create-if-missing`; never create a changelog unless the caller explicitly supplies that flag.
- [ ] **Step 4: Preserve** the existing duplicate guard and avoid adding file-locking infrastructure unless tests demonstrate a real concurrent-write failure.
- [ ] **Step 5: Run** the focused tests; expected: pass.
- [ ] **Step 6: Commit** with `feat: lazily create material changelog entries`.

### Task 3: Reduce the evidence-gate checks

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/scripts/evidence_gate.py`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/tests/test_evidence_gate.py`

- [ ] **Step 1: Add failing tests** for a valid compact `Knowledge / Validation` section, missing evidence disclosure, missing changelog, missing entry ID, stale entry ID, and a valid `none`-source plan.
- [ ] **Step 2: Run** `pytest -q P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/tests/test_evidence_gate.py`; expected: failures for the compact contract.
- [ ] **Step 3: Implement** only structural checks: required fields, explicit `none`, changelog existence, `[Unreleased]`, entry ID, timestamp, and current plan hash.
- [ ] **Step 4: Do not** validate that a source influenced the decision or that static evidence proves runtime value.
- [ ] **Step 5: Run** the focused gate tests; expected: pass.
- [ ] **Step 6: Commit** with `feat: gate plans on lightweight evidence records`.

### Task 4: Update skill behavior

**Files:**
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/design/SKILL.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/SKILL.md`
- Modify: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/risks/SKILL.md`
- Modify: `P:/packages/.claude-marketplace/plugins/red-team/commands/red-team.md`

- [ ] **Step 1: Update** `/design` to emit the compact evidence section only for material designs or designs making external/repository validation claims.
- [ ] **Step 2: Update** `/planning` to run the evidence gate last and create a changelog entry only when the decision is material.
- [ ] **Step 3: Update** `/risks` to report used, unused, unverified, and missing evidence without creating or repairing files.
- [ ] **Step 4: Update** `/red-team` to treat unsupported “tested,” “accepted,” “validated,” or “deployed” claims as findings, without requiring a particular knowledge source.
- [ ] **Step 5: Search** the four files for contradictory instructions implying that changelogs are telemetry or that tool invocation proves validation.
- [ ] **Step 6: Commit** with `docs: apply lightweight evidence workflow to skills`.

### Task 5: Verify the complete lightweight path

**Files:**
- Test: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/tests/test_record_changelog.py`
- Test: `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/tests/test_evidence_gate.py`

- [ ] **Step 1: Test** a low-risk plan with no external sources; expected: no changelog entry unless the change is material.
- [ ] **Step 2: Test** a material plan using `/wiki` and `/check`; expected: one dated changelog entry and valid evidence fields.
- [ ] **Step 3: Test** a plan that claims testing without evidence; expected: a clear gate finding.
- [ ] **Step 4: Test** a repeated planning run; expected: no duplicate changelog entry.
- [ ] **Step 5: Run** `python -m py_compile P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/scripts/evidence_gate.py P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/scripts/record_changelog.py`.
- [ ] **Step 6: Run** `pytest -q P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/tests/test_evidence_gate.py P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/planning/tests/test_record_changelog.py`.
- [ ] **Step 7: Commit** with `test: verify lightweight evidence workflow`.

## Deferred until evidence justifies it

- Hook-based tool-use capture.
- Append-only telemetry logs.
- Project metadata manifests.
- Decision capsules and provenance compilers.
- Cross-worktree identity tracking.
- Retention, analytics, and rollout dashboards.
- Bulk changelog backfill.

These are not rejected permanently. They require a concrete recurring failure
that the lightweight contract failed to catch, plus measured benefit greater
than the added maintenance and cognitive load.

## Self-review checklist

- [ ] A normal low-risk task remains low-friction.
- [ ] `/risks` and `/red-team` remain read-only.
- [ ] No hook or telemetry platform was added.
- [ ] `none` is a valid honest answer for source usage.
- [ ] Changelog entries are material, concise, dated, and idempotent.
- [ ] The validator checks structure, not invented semantic certainty.
- [ ] Every failure message tells the AI coder exactly how to repair the record.

