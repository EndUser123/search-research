# ADR-20260403: SDLC Group Package with Junction-Linked Skills

**Status:** Accepted

## Context

Four skills — `/planning`, `/code`, `/tdd`, `/arch` — share `contract-primitives` as a common dependency. They form an implicit SDLC cluster: planning authors plans, code and tdd execute from them, and arch validates boundary contracts.

**Current problems:**
1. **Versioning drift** — `contract-primitives` at `P:/packages/contract-primitives/` is independently versioned from the skills that consume it. A schema change can break one skill while others remain unupdated.
2. **Discovery** — The cluster relationship is invisible; nothing groups these four skills together in the filesystem.
3. **Deployment** — Each skill's `__lib__/` uses `sys.path.insert(0, ...)` hacks to reach `contract-primitives` rather than importing it as a first-class module.

## Decision

Create a group package at `P:/packages/sdlc/` that contains:
- The canonical `contract-primitives` source
- The real content directories for all four skills

Create **Windows junction points** from `P:/.claude/skills/{planning,code,tdd,arch}` to the corresponding directories inside `P:/packages/sdlc/`.

### Directory Structure

```
P:/packages/sdlc/
  __init__.py                      # version anchor + re-exports
  contract-primitives/
    src/contract_primitives/
      __init__.py                  # re-exports schemas, validators, events
      schemas.py
      validators.py
      events.py
      plan_consumption.py
  planning/
    SKILL.md
    __lib__/
      auto_verify.py
      ...
  code/
    SKILL.md
    hooks/
      PreToolUse_plan_consumer_gate.py
      ...
  tdd/
    SKILL.md
    hooks/
      PreToolUse_plan_consumer_gate.py
      ...
  arch/
    SKILL.md
    arch_validate.py
    ...

P:/.claude/skills/
  planning/  ────────── junction ──→ P:/packages/sdlc/planning/
  code/      ────────── junction ──→ P:/packages/sdlc/code/
  tdd/       ────────── junction ──→ P:/packages/sdlc/tdd/
  arch/      ────────── junction ──→ P:/packages/sdlc/arch/
```

### Import Resolution

Inside `P:/packages/sdlc/planning/__lib__/auto_verify.py`:
```python
from contract_primitives import validate_contract  # resolves via junction
```

No `sys.path.insert` needed. The junction makes `contract-primitives/` a real parent directory of each skill's location, so Python's default import resolution finds it without manipulation.

### Version Anchor

`P:/packages/sdlc/__init__.py` exposes:
```python
__version__ = "0.1.0"
from contract_primitives import *
```

Skills declare their dependency in SKILL.md frontmatter:
```yaml
depends_on:
  - sdlc: ">=0.1.0"
```

## Consequences

**Positive:**
- Atomic versioning: one commit bumps the entire group
- Canonical `contract-primitives` location — single source of truth
- No `sys.path` hacks — standard Python imports
- Skills remain CLI-discoverable as `/planning`, `/code`, `/tdd`, `/arch` via their junctions
- Each skill's git history lives entirely under `P:/packages/sdlc/{skill}/`

**Negative:**
- Two directory trees to maintain (`P:/packages/sdlc/` and `P:/.claude/skills/`)
- Junctions must be created manually on first setup (`mklink /J`)
- Evidence, tests, and state files live inside `P:/packages/sdlc/` — a non-obvious location for skills traditionally thought of as living under `P:/.claude/skills/`

## Alternatives Rejected

| Alternative | Reason Rejected |
|-------------|-----------------|
| Move skills into `P:/.claude/skills/sdlc/` subdirectory | Changes CLI invocations from `/planning` to `/sdlc/planning`; worse ergonomics |
| Keep `contract-primitives` standalone, add `dependencies` frontmatter only | Solves discovery, not versioning or deployment |
| Single `.claude-plugin/` with all four skills inside | Same CLI erosion problem as above |
| Symlinks instead of junctions | Symlinks on Windows require admin privileges; junctions work at user level |

## Contract Authority Packet

Not applicable — this is a structural/organizational decision, not a contract-sensitive boundary design.

## Implementation Notes

- Create junctions with `mklink /J "P:\.claude\skills\planning" "P:\packages\sdlc\planning"`
- Delete `P:/packages/contract-primitives/` after migrating its contents into `P:/packages/sdlc/contract-primitives/`
- Update `settings.json` plugin registrations if needed (should not change — junctions preserve paths)
- Verify imports work: `python -c "from contract_primitives import validate_contract"` from inside `P:/packages/sdlc/planning/__lib__/`
