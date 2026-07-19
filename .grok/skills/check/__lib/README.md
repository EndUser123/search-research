# check/\_\_lib — transcript preprocessor

Deterministic preprocessor for `/check`. Parses Grok `chat_history.jsonl`
into a structured `EvidencePacket` that verifier subagents cite instead of
re-reading the raw transcript. See `../SKILL.md` Step 0.5 for the
orchestrator contract.

## Module map

```
event_model.py         frozen dataclasses (Transcript/Event/ToolCall/ParseStats) + check contract enums
transcript_parser.py   JSONL -> Transcript
detectors.py           10 check-oriented signal detectors -> Signal[]
evidence_packet.py     assemble + serialise + atomic write
output_validator.py    validate_packet + validate_verifier_output
preprocessor.py        top-level entrypoint + CLI
```

Single dependency direction:

```
event_model  <-  transcript_parser
             <-  detectors  <-  evidence_packet  <-  output_validator
                                                         <-  preprocessor
```

---

## ⚠️ DUPLICATE IMPLEMENTATION — READ BEFORE EDITING

There is a **parallel implementation of the same preprocessor architecture**
under:

```
P:/.grok/skills/aar/__lib/
```

with the same five module names:

| module              | aar LOC | check LOC | delta  |
|---------------------|--------:|----------:|-------:|
| event_model.py      |     355 |       327 |    -28 |
| transcript_parser.py|     487 |       394 |    -93 |
| detectors.py        |    1269 |       863 |   -406 |
| evidence_packet.py  |     427 |       182 |   -245 |
| output_validator.py |    1434 |       332 |  -1102 |

(Counts via `len(Path(p).read_text().splitlines())`, captured 2026-07-18 during
/check. **The aar side is being actively extended by a parallel session** — the
numbers above were already different 30 minutes before this measurement. Do
NOT rely on this table for a merge decision. Re-run the snippet below before
deciding whether to consolidate:

```python
from pathlib import Path
for m in ("event_model","transcript_parser","detectors","evidence_packet","output_validator"):
    a = len(Path(rf"P:/.grok/skills/aar/__lib/{m}.py").read_text(encoding="utf-8").splitlines())
    c = len(Path(rf"P:/.grok/skills/check/__lib/{m}.py").read_text(encoding="utf-8").splitlines())
    print(f"{m:<22} aar={a:>5} check={c:>5} delta={c-a:>5}")
```

)

### Why two copies exist

Both `/aar` and `/check` consume the same transcript format and the same
5-module architecture (`event_model` → `transcript_parser` → `detectors` →
`evidence_packet` → `output_validator`). The original design called for a
single shared module. We deliberately did **not** share, because:

1. `/aar` and `/check` were being built by **separate LLM sessions in
   parallel**. Sharing a path would have caused merge collisions and one
   session's in-flight edits would have broken the other's test suite.
2. The two consumers have **different jobs**: AAR does causal synthesis
   (its `output_validator` carries AAR-specific enums —
   `ALLOWED_EPISODE_TYPES`, `ALLOWED_DISPOSITIONS`, `CONFIDENCE_LEVELS`,
   `POLICY_LEVELS`, etc.); /check does claim verification (its
   `output_validator` carries `CHECK_VERDICTS`, `CHECK_ISSUE_SEVERITIES`).
   The modules have already diverged by over a thousand lines of LOC in the
   largest cases, with fully disjoint detector sets (see Step 3 below).
3. Independent copies mean each skill keeps working regardless of the
   other's churn. Cost: ~700+ LOC of structural duplication.

### What "duplicated" actually means here

The modules are a **fork**, not a verbatim copy:

- Shared DNA: frozen-dataclass shape, JSONL parsing contract, the
  `Signal` dataclass, atomic-write pattern, reconciliation check,
  `PACKET_SCHEMA_VERSION` concept.
- Diverged: detector sets (AAR's are causal-synthesis-oriented; /check's
  are claim-verification-oriented — e.g. /check has
  `unverified_claim_candidates`), contract enums in `event_model` and
  `output_validator`, packet detail schema, and the
  `preprocessor.py` entrypoint (only /check has one; AAR has
  `session_resolver.py` instead).

The two implementations are **NOT interchangeable**. Do not import one from
the other.

### When to revisit this decision

Revisit when **any** of these becomes true:

- You are about to edit one of the 5 duplicated module names in either
  `__lib/` dir.
- The two sides have diverged so far that the JSONL-parser contract or the
  `Transcript`/`Event` shape no longer matches — at that point keeping them
  separate creates real bug risk (a parser fix in one won't propagate).
- Both skills are stable and no longer being actively edited by parallel
  sessions — at that point the merge cost drops below the duplication cost.

### What to do when revisiting

1. Diff the two copies of each of the 5 modules; classify every delta as
   `shared`, `aar-specific`, or `check-specific`.
2. If most deltas are `shared`, extract a single canonical copy to
   `P:/.grok/skills/_shared/transcript_preprocessor/` (or similar) and
   import from both skills. Move `aar-specific` / `check-specific` pieces
   into per-skill modules that import from the shared core.
3. If most deltas are skill-specific, leave them separate but add a
   cross-reference at the top of each duplicated file pointing to the
   other, so the next editor can't miss it.
4. Whichever path: bump `PACKET_SCHEMA_VERSION` in both if the on-disk
   packet schema changes.

### If you edit `/aar`'s copy

If you arrived here from `aar/__lib/`, consider mirroring this README into
`P:/.grok/skills/aar/__lib/README.md` so the note is discoverable from
both sides. We did not add it there to avoid colliding with the parallel
AAR session's work.
