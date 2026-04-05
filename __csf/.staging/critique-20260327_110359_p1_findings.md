## Triage Classification

**plan** — Architectural design proposal for ADR verification system spanning /planning, /code, /verify modifications plus new scripts and a hook.

## Dispatched Specialists

- **adversarial-critic**: Reasoning quality, feasibility, implementation completeness
- **adversarial-compliance**: Schema alignment, spec completeness, architectural pattern compliance

## Specialist Findings Summary

### adversarial-critic
**Domain:** Reasoning quality, bias, feasibility of proposed design

**Key findings:**
- [MEDIUM] (adversarial-critic) — No causal chain provided for how `/planning` generates test stubs at acceptance time. The proposal assumes parsing ACs from prose but doesn't address ambiguity in natural language criteria.
- [MEDIUM] (adversarial-critic) — `/code` AUDIT phase modification is vague — "verify ADR ACs are still satisfied" implies running pytest, but no spec for how AC test results map back to pass/fail at the skill level.
- [LOW] (adversarial-critic) — No rollback plan if ADR tests fail after implementation. What happens when a refactor breaks an ADR AC test?

**No HIGH findings.**

### adversarial-compliance
**Domain:** Schema alignment, spec completeness, architectural patterns

**Key findings:**
- [HIGH] (adversarial-compliance) — No ADR schema defined. The proposal references "ADR acceptance criteria in prose" but doesn't specify the required markdown structure. Without a schema, `adr_to_tests` cannot reliably parse ACs.
- [MEDIUM] (adversarial-compliance) — ADR_REGISTRY.json design is underspecified — no schema for how it maps ADR ID → covered files → test file path. A registry without schema will drift.
- [MEDIUM] (adversarial-compliance) — The proposal doesn't address what happens when an ADR is deprecated or superseded. Should tests be archived, deleted, or marked obsolete?

**No CRITICAL findings.**

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (adversarial-compliance) — **No ADR markdown schema** — Without `## Acceptance Criteria` structured field and required format, `adr_to_tests` cannot reliably extract ACs. Must define schema before scripts can be built.
1.2. [MEDIUM] (adversarial-critic) — **AUDIT phase undefined** — `/code` AUDIT step says "verify ADR ACs are still satisfied" but gives no mechanism. Is it `pytest tests/adr/ADR_*`? A subprocess call? A skill invocation? Must specify the execution model.

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (adversarial-critic) — **Prose AC parsing assumption** — The proposal assumes natural language ACs can be parsed into pytest function names. Realistically, ~30-50% of ACs will be ambiguous. The script needs a fallback (TODO marker) or a strict AC authoring format.
2.2. [LOW] (adversarial-critic) — **No version pinning for ADR state** — When ADR is revised, are old test files kept, overwritten, or versioned? Ambiguous for iterative ADR lifecycles.

### Missing Obvious Actions / Best Practices
3.1. [MEDIUM] (adversarial-compliance) — **ADR_REGISTRY.json needs schema** — Define the registry schema: `{ adr_id: { "covers": ["file1.py"], "test_file": "tests/adr/test_adr_*.py", "status": "active|deprecated" } }`. Without it, the registry will accumulate inconsistencies.
3.2. [MEDIUM] (adversarial-critic) — **ADR deprecation path missing** — When an ADR is superseded, what happens to its tests? Design decision: archive with `_deprecated` suffix, mark all tests `pytest.mark.skip`, or delete. Must choose one.

### Risks and Edge Cases
4.1. [MEDIUM] (adversarial-compliance) — **Circular dependency risk** — If ADR covers files that include the ADR registry itself, changes to the registry could break ADR verification. File tracking should exclude registry and test infrastructure.
4.2. [LOW] (adversarial-critic) — **ADR test maintenance burden** — For a solo dev, maintaining ADR tests for every architectural decision may be overhead-heavy. No guidance on when an ADR is "significant enough" to warrant test coverage vs. when prose-only is sufficient.

### Concrete Recommendations
5.1. [HIGH] (adversarial-compliance) — **Define ADR markdown schema first** — Add to `P:/__csf/docs/adr_schema.md`:
   ```
   ## Acceptance Criteria
   - AC1: [imperative testable statement]
   - AC2: ...
   ```
   Require `pytest` naming compatibility: `AC1` → `test_<adr_id>_ac1()`.
5.2. [MEDIUM] (adversarial-compliance) — **Schema-validate ADR_REGISTRY.json** — Add JSON Schema for the registry at `P:/__csf/docs/adr_registry_schema.json`. Validate on write with a lightweight check.
5.3. [MEDIUM] (adversarial-critic) — **Specify `/code` AUDIT execution model** — Choose: (a) subprocess `pytest tests/adr/ADR_<id>_*.py`, (b) skill invocation `/verify adr:<id>`, or (c) direct import of test functions. Recommend (b) — reuse `/verify` infrastructure.
5.4. [MEDIUM] (adversarial-compliance) — **ADR deprecation protocol** — Add to schema: when `status → deprecated`, rename test file to `test_adr_<id>_DEPRECATED.py` and mark all tests `@pytest.mark.skip("ADR deprecated")`.

### Open Questions / Unknowns
6.1. [LOW] (adversarial-compliance) — **ADR test location** — `tests/adr/` at repo root (`P:/__csf/tests/adr/`) or alongside the ADR file (`__csf/arch_decisions/tests/`)? Solo-dev convention typically puts tests near code, but ADR tests are cross-cutting by nature.
6.2. [LOW] (adversarial-critic) — **AC parsing fallback strategy** — If `adr_to_tests` cannot parse an AC into a valid pytest function name, should it emit a `# TODO: Manual AC test` placeholder or fail? Recommend: emit skeleton with `pytest.skip()`.
