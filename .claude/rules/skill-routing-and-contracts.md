# Skill Routing and Contract Policy

**Status**: Advisory — not structurally enforced. Principles are applied manually.

**Purpose**: Guidance for sequencing non-trivial work and establishing explicit handoff contracts between skills, sessions, and components.

---

## Core Principles

When in doubt, prefer:
- **transcript truth** over memory
- **contract closure** over flexible ambiguity
- **freshness verification** over cached confidence
- **root cause** over symptom repair

---

## Routing Spine

```
/recap  →  /gto  →  /top-problems  →  /arch  →  /planning  →  /pre-mortem  →  /code  →  /critique  →  /verify  →  /sqa
```

Not every step is always needed. Use the decision rules below to determine which steps apply.

---

## When to Run Each Skill

| Skill | Run when |
|-------|----------|
| `/recap` | Session was compacted, resumed from handoff, or context may be incomplete |
| `/gto` | Gap or health picture is unclear before planning or coding |
| `/top-problems` | Multiple candidate problems or repeated failures need ranking |
| `/arch` | Work is stateful, cross-session, or touches hooks/providers/persistence |
| `/planning` | Work spans multiple tasks, files, or phases |
| `/pre-mortem` | Work is stateful, risky, security-sensitive, or hard to reverse |
| `/code` | Architecture is closed (if needed) and plan exists |
| `/critique` | Claiming done on non-trivial, stateful, or high blast-radius work |
| `/verify` | Claiming verified on any feature or fix |
| `/sqa` | Work touches hooks, skills, routing, or system infrastructure |

---

## Contract Authority Packet

When `/arch` closes architecture for stateful work, it must emit a **Contract Authority Packet** — the authoritative record of boundary semantics.

### Minimum Schema

```json
{
  "contract_name": "string",
  "producer": "string",
  "consumer": "string",
  "input_schema": ["required_field_1", "required_field_2"],
  "output_schema": ["produced_field_1"],
  "freshness_authority": "source that wins on conflict",
  "invalidation_event": "what makes output stale",
  "isolation": "terminal | session | workspace",
  "failure_behavior": "what happens on missing/stale required fields",
  "verification": "test or check that proves contract holds"
}
```

### Rules

- The packet is authoritative. Prose summaries are explanatory only.
- If packet and prose disagree, follow the packet.
- If runtime artifact state contradicts the packet, the packet's named freshness authority decides.
- If freshness cannot be proven, re-run the producing skill.

---

## Contract Checklist

At every handoff boundary, confirm:

1. Producer and consumer are named
2. Required input/output fields are explicit
3. Freshness authority is named
4. Invalidation event is defined
5. Isolation level is declared (terminal / session / workspace)
6. Failure behavior on missing fields is defined

---

## Mandatory Triggers

### Resume after compaction or handoff

Run `/recap` first. Transcript-derived reconstruction is authoritative over memory-style summaries.

### Stateful or cross-session work

Run `/arch` before `/planning` or `/code`. Must close at minimum:
- identity model
- ordering / dedupe / freshness contracts
- event source of truth
- isolation boundary
- trigger conditions

If these cannot be closed, the design is incomplete.

### Non-trivial implementation

`/code` only when:
- current context has been explored
- architecture is closed (if stateful)
- plan exists for non-trivial work
- contract inputs/outputs are known

`/code` must not invent missing contracts mid-implementation.

---

## Anti-Forgetting

Before building anything, explicitly name:
- inputs consumed and outputs produced
- fields required by downstream consumers
- who verifies those fields
- what breaks if fields are absent or stale

This applies to: function signatures, hook payloads, handoff envelopes, plan artifacts, evidence files, session ledgers, skill outputs.

---

## Decision Rule

When unsure which skill to run next:

1. `/recap` — if context may be incomplete
2. `/gto` — if current gaps are unclear
3. `/top-problems` — if prioritization is unclear
4. `/arch` — if contracts or state are unclear
5. `/planning` — if execution shape is unclear
6. `/pre-mortem` — if risk is unclear
7. `/code` — only when the above are sufficiently closed
