---
title: "Local Config dataclass for circular-import boundaries"
concept_type: "decision"
created: 2026-07-27
agent: grok
host: both
cognitive_load: 2
verification: session-verified
sources:
  - session 019fa111-5dcb-7ff1-a4f5-415ad29bbe9e (2026-07-27 /go hermeticity refactor)
tags: [python, circular-import, config, dataclass, architectural-decision, dependency-injection, hermeticity]
summary: >
  When module B needs module A's configuration type (e.g., a Config
  dataclass) but A imports B at module load time, importing A's Config
  into B creates a circular import. The chosen solution is to define a
  local structurally-compatible Config dataclass in B (same field names
  and types) and have A adapt its Config to B's at the call site.
  Selected over shared base class (couples both modules to a third),
  duck-typed parameters (no type safety), and import restructuring
  (large diff with no other benefit).
relations:
  - target: wiki/concepts/stop-claim-gap-telemetry-probe-structure
    type: complements — that concept covers re-implementing helpers locally to break a circular import; this covers defining a parallel Config type for the same purpose
  - target: wiki/concepts/cross-module-call-graph-audit-false-negative
    type: related — both emerged from the same hermeticity refactor; the Config dataclass was the mechanism that enabled the cross-module cfg propagation
  - target: wiki/concepts/subprocess-as-degradation-boundary
    type: related — both are architectural patterns for managing module boundaries
---

# Local Config dataclass for circular-import boundaries

## Decision context

**Why this decision was needed:** during the `/close` hermeticity refactor
(Workstream B, session 019fa111), `close_accounting.py` needed to propagate
its new `Config` dataclass to `continuation_coverage.scan_continuation_coverage()`
so that `--no-mutate` and `--workspace` overrides reached the continuation
ledger writes. The natural approach — `from close_accounting import Config`
inside `continuation_coverage.py` — fails because `close_accounting.py`
imports `continuation_coverage` at module load time (line 37:
`from continuation_coverage import scan_continuation_coverage`). This is a
classic Python circular import.

The decision: how to give `continuation_coverage.py` access to a Config
type without creating a circular import.

## The decision

**Define a local `ContCovConfig` dataclass in `continuation_coverage.py`
with structurally-compatible fields. Have `close_accounting.py` adapt its
`Config` to `ContCovConfig` at the call site.**

```python
# continuation_coverage.py — local Config (avoids circular import)
@dataclass
class ContCovConfig:
    workspace: Path = Path("P:/")
    sessions_root: Path = field(default_factory=lambda: Path.home() / ".grok" / "sessions")
    artifacts_root: Path | None = None
    allow_mutate: bool = True

    @property
    def artifacts_dir(self) -> Path:
        return self.artifacts_root if self.artifacts_root is not None else self.workspace / ".artifacts"

    @property
    def handoffs_dir(self) -> Path:
        return self.workspace / "docs" / "handoffs"


# close_accounting.py — adapt at call site (no import of ContCovConfig needed at module load)
from continuation_coverage import ContCovConfig as _ContCovCfg
cc_cfg = _ContCovCfg(
    workspace=cfg.workspace,
    sessions_root=cfg.sessions_root,
    artifacts_root=cfg.artifacts_root,
    allow_mutate=cfg.allow_mutate,
)
coverage_result = scan_continuation_coverage(..., cfg=cc_cfg)
```

The two dataclasses are structurally compatible (same field names, same
types) but not inheritance-related. `close_accounting.Config` is the
"full" config (more fields, more derived properties); `ContCovConfig`
is the subset that `continuation_coverage` actually uses.

## Selection criterion

**Decoupling + type safety + minimal diff.** The chosen option must:
1. Break the circular import (decoupling)
2. Preserve type checking on the fields `continuation_coverage` actually reads (type safety)
3. Not require restructuring unrelated imports (minimal diff)

## Steelman (the rejected viable alternative)

**Shared base class in a third module.** Define `BaseWorkspaceConfig` in
a new `__lib/_config_base.py`, have both `close_accounting.Config` and
`continuation_coverage.ContCovConfig` inherit from it. This is the
"proper" OOP solution and gives both modules a shared type.

**Why it was reasonable:** it eliminates the field duplication (both
dataclasses share `workspace`, `sessions_root`, `artifacts_root`,
`allow_mutate`). If a third module later needs the same config, it inherits
from the base without re-declaring fields. It is the textbook solution.

**Why it was rejected:** it couples BOTH modules to a third module. That
third module becomes a load-bearing dependency whose every change
potentially breaks both consumers. For two modules with one call site,
the coupling cost exceeds the duplication cost. The duplication is 8
lines of field declarations — small enough to maintain by hand; the
shared-base alternative adds a module, an inheritance hierarchy, and
a coordination surface. **Duplication of 8 lines is cheaper than the
abstraction that eliminates it** (per the Karpathy guideline: "if the
abstraction is more complex than the duplicated code, keep the
duplication").

## Alternatives also considered

- **Duck-typed parameter** (`cfg: Any`). Rejected: loses type checking
  on the fields `continuation_coverage` reads. A typo in
  `cfg.sessions_root` vs `cfg.session_root` would not be caught until
  runtime.

- **Import restructuring** (move `Config` to a fourth module that both
  import). Rejected: same coupling cost as shared base class, plus
  forces a larger diff. The circular import is a real constraint of
  the current module organization; working around it via local types is
  less invasive than reorganizing imports. This echoes the
  [[subprocess-as-degradation-boundary]] principle: prefer the local
  solution that preserves the existing module boundary over the
  abstraction that crosses it.

- **Postponed annotation evaluation** (`from __future__ import
  annotations`). Rejected for this case: it defers annotation
  evaluation but does not defer the `from close_accounting import Config`
  statement itself, which still runs at module load. The circular import
  is at the import statement, not the type annotation. (This is a
  common confusion — see Python docs on [[python-typing-tradeoffs]],
  which is not yet in the wiki but worth capturing.)

## Falsifier

This decision is wrong if:
- A third module needs the same Config type and the duplication becomes
  a maintenance burden (3+ copies of the same 8 fields). At that point,
  the shared-base-class alternative wins because the abstraction cost
  amortizes across more consumers.
- Python adds a feature that allows deferred imports or forward-declaration
  of types for import (unlikely; not on any PEP roadmap as of 2026-07).
- The two dataclasses drift in field names or types, causing silent bugs
  at the adaptation site. Mitigation: a structural-compatibility test
  that asserts the field sets match (not yet implemented; candidate for
  `tests/test_config_compatibility.py`).

## Implications

1. **Field drift is the residual risk.** If `close_accounting.Config`
   renames `sessions_root` to `sessions_dir`, the adaptation at the call
   site silently breaks. Mitigation: keep a structural-compatibility
   test or add a runtime assertion at the adaptation site.

2. **The pattern is reusable.** Any time module B needs module A's Config
   but A imports B, the same pattern applies: local dataclass in B,
   adapt at A's call site. The 8-line duplication is the cost of
   decoupling.

3. **Module-level constants preserved as backward compat.** Both
   `close_accounting.py` and `continuation_coverage.py` keep their
   module-level constants (`WORKSPACE`, `ARTIFACTS_DIR`, etc.) as
   references to `_DEFAULT_CFG` so existing imports and monkeypatching
   in tests still work. The constants are not removed; they are
   re-routed through the default Config instance.

## Related patterns

- [[stop-claim-gap-telemetry-probe-structure]] § "Circular import risk" —
  the same circular-import problem solved by re-implementing a helper
  locally rather than importing it. This concept generalizes: when you
  cannot import from the module that imports you, define a local
  equivalent (helper function OR dataclass type) rather than forcing an
  import restructure.

## Receipts

- `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py:37` — `from continuation_coverage import scan_continuation_coverage` (the import that creates the circular constraint)
- `C:/Users/brsth/.grok/skills/close/__lib/continuation_coverage.py:33-58` — the local `ContCovConfig` dataclass (the chosen solution)
- `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py:225-236` — the adaptation at the call site (`ContCovConfig(workspace=cfg.workspace, ...)`)
