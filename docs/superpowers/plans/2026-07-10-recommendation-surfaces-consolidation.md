# Recommendation Surfaces Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/recap`, `/debrief`, and `/rns` the intentional user-facing analysis surfaces while preserving GTO detectors as debrief internals and moving DNE's useful pre-handoff checks into recap.

**Architecture:** `/recap` owns continuity and an optional pre-handoff check; `/debrief` owns transcript forensics, durable learning, and GTO-backed gap detection; `/rns` owns generic evidence-to-action ranking. GTO's engine remains under `skills/gto/` without a `SKILL.md`; DNE's risk calculator and rubric move under recap, and the DNE skill directory is removed.

**Tech Stack:** Python, Markdown skill contracts, pytest, Claude plugin manifests.

## Global Constraints

- Preserve unrelated working-tree changes.
- Do not delete `skills/gto/__lib/`, `orchestrator.py`, agents, schemas, hooks, or GTO tests.
- Do not make `/recap` implement fixes; it remains a handoff/check surface.
- `/debrief gaps` remains the only documented user path to GTO-backed detectors.
- Every moved behavior gets a source-level reference and targeted test coverage.

---

### Task 1: Move DNE risk capability into recap

**Files:**
- Move: `plugins/cc-skills-lab/skills/dne/scripts/risk_calculator.py` → `plugins/cc-skills-analysis/skills/recap/risk_calculator.py`
- Move: `plugins/cc-skills-lab/skills/dne/tests/test_risk_calculator.py` → `plugins/cc-skills-analysis/skills/recap/tests/test_risk_calculator.py`
- Modify: `plugins/cc-skills-analysis/skills/recap/tests/test_risk_calculator.py` imports
- Delete: DNE references and tests after migration

- [ ] Move the calculator and tests without changing formula semantics.
- [ ] Update imports and module docstrings to identify recap as the owner.
- [ ] Run `pytest -q plugins/cc-skills-analysis/skills/recap/tests/test_risk_calculator.py` and verify all tests pass.

### Task 2: Add recap pre-handoff check mode

**Files:**
- Modify: `plugins/cc-skills-analysis/skills/recap/__init__.py`
- Modify: `plugins/cc-skills-analysis/skills/recap/SKILL.md`
- Test: `plugins/cc-skills-analysis/skills/recap/tests/test_recap.py`

- [ ] Add a `check` CLI mode that reports evidence scope, risk inputs, and Red/Yellow/Blue pre-handoff checks.
- [ ] Keep findings advisory and require the user or `/go` to execute work.
- [ ] Test command parsing and output markers for an empty and populated session list.

### Task 3: Remove GTO's public husk and repair routing

**Files:**
- Delete: `plugins/cc-skills-analysis/skills/gto/SKILL.md`
- Modify: `plugins/cc-skills-analysis/skills/gto/README.md`
- Modify: `plugins/cc-skills-analysis/skills/debrief/SKILL.md`
- Modify: `plugins/cc-skills-analysis/CLAUDE.md`
- Modify: `plugins/cc-skills-analysis/skills/recap/SKILL.md`

- [ ] Remove `/gto` from public triggers and replace direct-command wording with internal-engine wording.
- [ ] Keep adapter imports, engine artifacts, and GTO tests intact.
- [ ] Change recap's lost-context route from `/gto` to `/debrief gaps`.
- [ ] Verify no live skill contract advertises `/gto` or `/dne`.

### Task 4: Delete DNE's public skill after migration

**Files:**
- Delete: `plugins/cc-skills-lab/skills/dne/` source, references, scripts, and tests
- Modify: `plugins/cc-skills-lab/CLAUDE.md`

- [ ] Remove the DNE skill directory once Task 1 and Task 2 tests pass.
- [ ] Remove DNE from the lab catalog.
- [ ] Preserve only the selected risk calculator and pre-handoff semantics in recap.

### Task 5: Full verification and adversarial review

- [ ] Run recap targeted tests and debrief adapter/GTO tests.
- [ ] Run package-wide tests for both affected plugins if targeted tests pass.
- [ ] Compare source and cache contracts; report cache refresh as a remaining operational step if needed.
- [ ] Re-run `rg` for `/gto`, `/dne`, and stale renderer paths, classify remaining references as engine/test/history or actionable drift.
- [ ] Review the diff for accidental deletion of GTO runtime code or unrelated working-tree changes.
