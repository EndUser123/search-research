# Pydantic Model as Contract: The Schema-Validation Failure Class

**Status:** concept (captured 2026-08-08)
**Provenance:** /www research on pipeline orchestration + transport reliability, session 019fdf3c
**Citations:** [[pipeline-orchestration-and-transport-reliability]], [[predictable-enforcement-for-recommendation-commitment]], [[causal-mechanism-claims-require-source-receipts-before-durable-write]]
**Host applicability:** Host-agnostic (pattern applies to any Python-based LLM agent workspace)

## The recurring failure class

Three independent incidents across the workspace share the same root cause and the same fix shape:

| Incident | What happened | Root cause |
|----------|---------------|------------|
| ship-py findings schema (2026-08-08) | Agent wrote `{findings:[], critical_findings:0}` instead of `{bugs:[], risks:[], suggestions:[]}` | No schema enforcement — dict keys are unchecked |
| close-authority INTG-1/INTG-2 (2026-07-27) | close_runner passed dict where str was expected, and vice versa | No type enforcement between producer and consumer |
| close_runner dict-vs-str (2026-07-25) | Evidence dict's `check_receipts` field was sometimes dict, sometimes str | Same — no contract between writer and reader |

**The common pattern:** data passed between two components (agent → orchestrator, scanner → renderer, phase A → phase B) has no enforced schema. The producer writes whatever shape feels right; the consumer assumes a different shape; the mismatch is silent until it crashes or produces wrong results.

## The fix: Pydantic model as transport contract

**Rule:** every inter-component data handoff in Python uses a Pydantic v2 model with `model_config = ConfigDict(extra="forbid")`. The model is the single source of truth for the data shape. Both producer and consumer import the same model.

**Why `extra="forbid"`:** without it, Pydantic silently ignores unknown fields. This means `{findings:[]}` passes validation even when the model expects `{bugs:[]}` — the wrong key is just dropped. `extra="forbid"` makes the wrong key a validation error, catching the mismatch at write time.

### Implementation pattern

```python
# findings_models.py — the contract
from pydantic import BaseModel, ConfigDict, Field

class ReviewFindings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bugs: list[ReviewBug] = Field(default_factory=list)
    risks: list[ReviewBug] = Field(default_factory=list)
    suggestions: list[ReviewBug] = Field(default_factory=list)

# Writer (agent via write_findings.py):
from findings_models import ReviewFindings
data = ReviewFindings(bugs=[...], risks=[...], suggestions=[...])
path.write_text(data.model_dump_json())

# Reader (orchestrator phase):
from findings_models import ReviewFindings
data = ReviewFindings.model_validate_json(path.read_text())
```

The wrong schema (`{findings:[]}`) now fails at write time with a field-level error, not at read time with a mysterious KeyError.

## Where this applies (the 3 known sites)

1. **ship-py inter-phase data** — ✅ shipped (`findings_models.py`, `write_findings.py`, 2026-08-08)
2. **close-authority evidence dict** — the `Evidence` dataclass in `close_accounting.py` should migrate to Pydantic with `extra="forbid"`
3. **close_runner dict-vs-str** — the type confusion in `check_receipts` should be a Pydantic model field with strict type

## The abstraction

This is a specific instance of the broader principle: **contracts should be enforced at the type level, not at the documentation level.** Prose documentation of data shapes ("the output must have bugs, risks, suggestions arrays") has the same ~50% compliance ceiling as other prose rules. Type enforcement (`extra="forbid"`) is the structural fix.

The same principle applies to:
- **JSON APIs** → Pydantic response models (or TypedDict with total=True)
- **CLI tool outputs** → schema validation on the producing side
- **Cross-skill data handoffs** → shared models in a `__lib/` that both skills import

## When NOT to apply

- **Ad-hoc exploration** — if the data shape is still evolving, strict models slow iteration
- **One-off scripts** — if the data crosses exactly one boundary and will never be reused
- **Non-Python boundaries** — JSON crossing to JavaScript/shell needs JSON Schema, not Pydantic

## Falsifier

This concept is wrong if:
- Pydantic's validation overhead is material (>5% latency on hot paths) — unlikely for I/O-bound agent workflows
- The `extra="forbid"` pattern produces too many false positives (agents fighting the schema instead of fixing their output) — mitigated by `write_findings.py --template` which prints the correct shape
- The 3 incidents were actually caused by something else (not schema enforcement) — but all 3 were traced to unchecked dict keys
