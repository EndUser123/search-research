---
title: "Telemetry logging as standard for Stop hooks — JSONL append for FP/FN measurement"
created: 2026-08-07
source: session-20260807
tags: [telemetry, stop-hooks, measurement, jsonl, fleet-observability]
summary: >
  Stop hooks that make decisions (block/allow, flag/pass) should log every
  decision as an append-only JSONL record. This enables false-positive and
  false-negative rate measurement — the gating criterion for promoting hooks
  from advisory to blocking mode. The pattern is: append a compact JSON
  object (status, mode, decision, claims, latency) to a per-hook JSONL file
  on every fire. Fail-open: telemetry is best-effort and never blocks the hook.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/ungrounded-state-prediction-claims-detection-architecture.md
    type: extends
  - target: wiki/concepts/tool-failure-lifecycle-llm-agent-fleets.md
    type: complements
  - target: wiki/concepts/silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap.md
    type: related
---

# Telemetry logging as standard for Stop hooks

## Decision context

Stop hooks that enforce policy (claim detection, bias gating, completion
verification) face a deployment problem: they must start in advisory mode
(exit 0, log-only) and only switch to blocking mode (exit 2) after
proving their false-positive rate is acceptable. Without telemetry, the
advisory-to-blocking transition is undecidable — there's no data to
measure FP rate against.

This pattern emerged from building three Stop hooks: `behavioral_check.py`
(claim detection Layer 1), `Stop_claim_judge.py` (claim detection Layer 3,
LLM-as-judge), and `Stop_creative_nudge.py` (creative technique nudges).
The claim-judge hook explicitly requires 5 sessions of FP measurement
before switching to blocking — without telemetry, this measurement is
impossible.

## The pattern

Every Stop hook that makes a decision appends a compact JSON record to a
per-hook JSONL file on every fire:

```python
TELEMETRY_LOG = Path("P:/.claude/hooks/.evidence/<hook-name>.jsonl")

def log_telemetry(entry: dict) -> None:
    """Append a telemetry record. Fail-open (never blocks the hook)."""
    try:
        TELEMETRY_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        with open(TELEMETRY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # telemetry is best-effort
```

Called at every decision point:
- After LLM judge returns: `log_telemetry({"status": "judged", "has_unsupported": True, "claims_count": 3})`
- On API error: `log_telemetry({"status": "api_error"})`
- On pre-filter skip: optionally log `{"status": "skipped_prefilter"}`

## What each field means

| Field | Purpose |
|-------|---------|
| `ts` | Timestamp for temporal analysis |
| `status` | `judged` / `api_error` / `skipped_prefilter` / `truncated` |
| `mode` | `advisory` or `blocking` — which mode the hook was in |
| `has_unsupported` | The judge's boolean decision (for claim hooks) |
| `claims_count` | How many claims were evaluated |
| `unsupported` | List of unsupported claim texts (for FP analysis) |
| `msg_len` | Message length (context for understanding trigger patterns) |

## Why JSONL append (not a database, not a structured log)

1. **Zero dependencies** — no DB, no log framework, just `open(..., "a")`
2. **Atomic appends** — `write()` on most filesystems is atomic for small records
3. **Human-readable** — `cat claim-judge.jsonl | python -m json.tool` works
4. **Machine-parseable** — one JSON object per line, standard format
5. **Fail-open** — if the file can't be written, the hook still runs
6. **Multi-session safe** — append mode doesn't clobber concurrent writes

## What this means for our workspace

All Stop hooks that make enforcement decisions should adopt this pattern.
Currently using it:
- `behavioral_check.py` → `behavioral-check-log.jsonl`
- `Stop_claim_judge.py` → `claim-judge.jsonl`
- `creative_nudge.py` → cooldown file (similar pattern, different shape)

Hooks NOT yet using it:
- `minimal_bias_gate.py` — should log every fire, decision, and FP signal
- `PreToolUse_ship_phase_gate.py` — should log every push-block event
- Any future enforcement hook

The measurement workflow:
1. Deploy hook in advisory mode (exit 0)
2. After N sessions, scan the JSONL: `python -c "import json; [json.loads(l) for l in open('claim-judge.jsonl')]"`
3. Count: total fires, unsupported claims, how many were false positives (operator manually validates)
4. If FP rate < threshold (e.g., 30%), switch to blocking mode
5. Continue logging in blocking mode for ongoing monitoring

## Falsifier

This pattern is wrong if:
- The JSONL file grows unbounded and causes performance issues (mitigation: rotate quarterly)
- Concurrent writes from multiple terminals corrupt records (mitigation: small writes are atomic on NTFS/ext4)
- The telemetry data leaks sensitive information from transcripts (mitigation: apply `redact_secrets()` before logging, as done in `Stop_claim_judge.py`)
- The FP measurement never actually influences the advisory→blocking decision (mitigation: the handoff must specify the measurement step as a gate)

## Sources

- Session 019fcdd2 (2026-08-07): built `Stop_claim_judge.py` with telemetry, measured 2 entries during e2e test
- `/review` finding S3: "Telemetry log persists claim text without scrubbing" — confirmed the need for redaction before logging
- `/aar` opportunity O4: "Telemetry logging as Stop-hook standard — PRESERVE"
- [[silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap]] — prior incident where telemetry existed but no consumer validated it
- [[ungrounded-state-prediction-claims-detection-architecture]] — the hook that motivated this standard
- [[tool-failure-lifecycle-llm-agent-fleets]] — passive telemetry as fleet observability
- [[stop-hook-lastassistantmessage-payload-field-2026]] — Stop hook payload mechanics

## Receipts

- `C:/Users/brsth/.grok/hooks/scripts/Stop_claim_judge.py` lines 165-176 (`log_telemetry` function), lines 285-291 (telemetry call in main), lines 310-316 (unsupported claims logged with redaction)
- `C:/Users/brsth/.grok/hooks/scripts/behavioral_check.py` — prior art: writes to `behavioral-check-log.jsonl`
- `C:/Users/brsth/.grok/hooks/state/behavioral-check-log.jsonl` — existing telemetry file with real entries

## Auto-related

- [[opentelemetry-logging-patterns]]
- [[opentelemetry-structured-logging-patterns]]
- [[opentelemetry-logging]]
- [[Are-there-repos-or-solutions-to-claude-code-gettin]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]

