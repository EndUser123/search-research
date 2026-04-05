# ADR-2026-03-27: ADR Verification System — Acceptance Criteria as Automated Tests

**Date:** 2026-03-27
**Status:** ACCEPTED
**Deciders:** Solo Developer
**Reviewers:** [External LLM review applied — 2026-03-27]

---

## Context

Architectural decisions recorded in ADRs at `P:/__csf/arch_decisions/` are not connected to implementation. There is no automated way to verify that code matches the architectural intent documented in an ADR. This creates a drift problem: ADRs become stale documents that no longer reflect actual implementation.

The `/planning` skill can create a plan from an ADR, and the `/code` skill has a 9-phase workflow, but neither skill generates test stubs from ADR acceptance criteria, runs ADR verification in the AUDIT phase, or detects when implementation diverges from ADR intent.

---

## Problem Statement

1. **No implementation verification**: ADR acceptance criteria exist only as prose. Nothing verifies that implementation satisfies them.

2. **No drift detection**: When code changes, there is no mechanism to detect whether the change violates an ADR's architectural intent.

3. **No test stubs from ADR acceptance**: `/planning` creates a plan from an ADR but emits no pytest test file. The ADR's acceptance criteria remain unactionable.

4. **AUDIT phase gap**: `/code` Phase 7 AUDIT runs ruff, mypy, and pylint — it does not verify ADR compliance.

---

## Decision

Implement an ADR verification system with five components:

1. **ADR markdown schema** with required `## Acceptance Criteria` section and imperative, testable statements
2. **`adr_to_tests` script** that parses ADR markdown and emits pytest skeleton functions
3. **`/planning` integration** that generates test stubs when ADR status transitions to `implementation-ready`
4. **`/code` AUDIT integration**:
   - When plan has `adr:<id>` tasks, `/code` AUDIT invokes `/verify adr:<id>`
   - `/verify` runs `verify_adr.py` which runs pytest on the ADR's test file
   - AUDIT fails if ADR tests fail
   - Modify: `P:/.claude/skills/code/SKILL.md` (Phase 7 AUDIT, ~line 1800)
5. **`PostToolUse_adr_deviation_check` hook** that detects changes to ADR-governed files and warns on drift

---

## Schema

### ADR Markdown Schema

Every ADR file must include:

```markdown
## Acceptance Criteria

- AC1: [Imperative, testable statement — creates pytest function: test_<adr_id>_ac1()]
- AC2: [Imperative, testable statement — creates pytest function: test_<adr_id>_ac2()]
- AC3: [...]
```

**Rules:**
- ACs must be imperative ("Must X", "Use Y over Z", "Store data in Z").
- ACs must be testable (assertable boolean outcomes — not prose opinions).
- Numbered sequentially: `AC1`, `AC2`, ...
- If no testable ACs exist: mark `status: prose-only` in registry.

**Fallback:** If `adr_to_tests` cannot parse an AC into a valid pytest name, it emits `@pytest.mark.skip("TODO: manual AC")` rather than failing.

### ADR_REGISTRY.json Schema

Registry file: `~/.claude/adr/ADR_REGISTRY.json` (home-dir for cross-terminal access).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": {
        "type": "string",
        "pattern": "^\\d{4}-\\d{2}-\\d{2}_.*$"
      },
      "covers": {
        "type": "array",
        "items": {"type": "string"}
      },
      "test_file": {
        "type": "string"
      },
      "status": {
        "enum": ["proposed", "accepted", "implementation-ready", "deprecated", "prose-only"]
      },
      "deprecated_by": {
        "type": "string",
        "nullable": true
      }
    },
    "required": ["id", "covers", "status"]
  }
}
```

**Example entry:**
```json
{
  "id": "2025-03-08_python_tree_sitter_integration",
  "covers": ["src/search/backends/tree_sitter_backend.py"],
  "test_file": "tests/adr/test_adr_2025-03-08_tree_sitter.py",
  "status": "prose-only",
  "deprecated_by": null
}
```

### ADR Lifecycle States

| State | Meaning | Verification |
|-------|---------|-------------|
| `proposed` | Under consideration | Manual review only |
| `accepted` | Approved, implementation pending | Tests generated |
| `implementation-ready` | Plan created, ready for /code | Trigger: test stub generation |
| `deprecated` | Superseded by another ADR | Tests renamed with `@pytest.mark.skip` |
| `prose-only` | No parseable ACs | Skipped in batch verification |

---

## Alternatives Considered

### Option A: Schema-First Staged Implementation (CHOSEN)

Build in dependency order: schema → scripts → skill integrations → hook.

**Pros:** All components depend on the schema. Building it first prevents rework.
**Cons:** Sequential — cannot deliver scripts immediately.

### Option B: Script-First

Build `adr_to_tests` first, then retroactively normalize existing ADRs and define schema.

**Pros:** Faster initial script delivery.
**Cons:** Existing ADRs are prose-only and cannot be auto-parsed. Retroactive schema definition would invalidate the initial script design.

### Option C: Hook-First

Build the deviation detection hook before any other component.

**Pros:** Simple — detects file changes without needing formal ACs.
**Cons:** Detects drift but cannot verify compliance. No way to know if a change violates an ADR's intent without testable ACs.

### Option D: ADR Linter at Commit Time

Run `ruff` or a custom linter on ADR files at commit time to enforce AC format.

**Pros:** Enforces schema adoption incrementally.
**Cons:** Does not address verification or drift detection. Linter without test stubs is incomplete.

---

## Consequences

### Happy Path

1. ADR authored with `## Acceptance Criteria` in required format
2. `/planning` generates test stubs from ACs when status → `implementation-ready`
3. `/code` implements feature, AUDIT phase verifies ADR tests pass
4. `PostToolUse_adr_deviation_check` warns if ADR-governed files are modified without ADR update
5. `/verify adr:<id>` runs ADR-specific test suite on demand

### Sad Path

1. ADR has no parseable ACs → marked `prose-only` in registry, skipped in `verify_all_adrs`
2. ADR is revised → old tests renamed with `@pytest.mark.skip`, new tests generated from revised ACs
3. Code changes without ADR update → hook warns, human triages (updates ADR or confirms deviation)

### Registry Structure

```json
{
  "// JSON Schema v1": "{ adr_id: { covers: string[], test_file: string, status: string } }",
  "0001": {
    "covers": ["src/search/backends/tree_sitter_backend.py"],
    "test_file": "tests/adr/test_adr_0001_tree_sitter.py",
    "status": "prose-only"
  }
}
```

**Location:** `~/.claude/adr/ADR_REGISTRY.json` (home-dir for cross-terminal access)

---

## Files to Create or Modify

| File | Action | Phase |
|------|--------|-------|
| `P:/__csf/docs/adr_schema.md` | Create — ADR format specification | 0 |
| `P:/__csf/scripts/adr_to_tests.py` | Create — parse ADR, emit pytest skeleton | 1 |
| `P:/__csf/scripts/verify_adr.py` | Create — check AC-to-test linkage | 1 |
| `P:/__csf/scripts/verify_all_adrs.py` | Create — run all ADR test suites | 1 |
| `~/.claude/adr/ADR_REGISTRY.json` | Create — ADR registry with inline schema | 4 |
| `P:/.claude/hooks/PostToolUse_adr_deviation_check.py` | Create — drift detection hook | 4 |
| `P:/.claude/hooks/commit-msg_adr_enforce.py` | Create — enforce `ADR-<id>` in commit footer | 4 |
| `P:/__csf/arch_decisions/2025-03-08_python_tree_sitter_integration.md` | Modify — add `prose-only` status | 0 |
| `P:/.claude/skills/planning/SKILL.md` | Modify — add test stub generation step | 2 |
| `P:/.claude/skills/code/SKILL.md` | Modify — AUDIT invokes `/verify adr:<id>` | 3 |
| `P:/.claude/skills/verify/SKILL.md` | Modify — add `verify adr:<id>` trigger | 5 |

---

## Resolved Questions

1. **Threshold for ADR test coverage** — Only ADRs with objectively testable ACs (not architectural rationale). Prose-heavy ADRs → `prose-only` status.

2. **ADR ID in commit messages** — Yes. `commit-msg_adr_enforce.py` hook enforces `ADR-<id>` in footer for commits touching `covers` files.

3. **ADR test maintenance burden** — Use `deprecated` status + `@pytest.mark.skip("ADR deprecated")` to pause maintenance without deletion.

4. **ADR test location** — `P:/__csf/tests/adr/test_adr_<id>_<slug>.py` (repo root, not alongside ADR file).

5. **AUDIT mechanism** — `/code` AUDIT invokes `/verify adr:<id>` (reuses `/verify` infrastructure, not subprocess).

6. **Fallback for unparseable ACs** — `adr_to_tests` emits `@pytest.mark.skip("TODO: manual AC")` rather than failing.

---

## References

- ADR verification system critique: `P:/__csf/.staging/critique-20260327_110359_p3.md`
- ADR triage findings: `P:/__csf/.staging/critique-20260327_110359_p1_findings.md`
- Cross-agent meta-critique: `P:/__csf/.staging/critique-20260327_110359_p2.md`
- `/planning` ADR-aware behavior: `P:/.claude/skills/planning/SKILL.md:145-152`
- `/code` AUDIT phase: `P:/.claude/skills/code/SKILL.md:1790-1869`
- `/verify` tier structure: `P:/.claude/skills/verify/SKILL.md:55-114`
- MADR template primer: https://ozimmer.ch/practices/2022/11/22/MADRTemplatePrimer.html
- JSON Schema: https://json-schema.org/learn/json-schema-examples
