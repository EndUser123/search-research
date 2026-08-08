# Enforcement Infrastructure Measurement Baseline (2026-08-08)

**Status:** measured (captured 2026-08-08)
**Provenance:** historical transcript analysis, 412 main sessions, 18,726 assistant messages
**Scanner:** `P:/tmp/measure_enforcement_v2.py`
**Raw data:** `P:/tmp/enforcement_measurement.json`
**Host applicability:** Grok Build (measurement is host-specific; patterns transfer)

## Purpose

Establishes the **before** baseline for three enforcement mechanisms shipped this session:
1. Stop_recommendation_commitment_gate.py (option-theater detection)
2. EGDP template (evidence → recommendation → receipt)
3. Hash-bound verification receipts

Future sessions re-measure to determine whether these mechanisms reduced the patterns they target.

## Q1: Recommendation commitment gate fire rate

| Metric | Value |
|-----------|-------|
| Would-block events (raw) | 708 |
| Per long assistant message (≥80 chars) | 4.77% |
| Sessions with ≥1 block | 135 / 412 (32.8%) |
| Real option-theater (precision) | **93.4%** |
| False-positive rate | 6.6% (from `<think>` blocks — structurally fixed this session) |

**Distribution:** 32 sessions with 1 block, 36 with 5-9, 19 with 10-19, 1 with 20. Median: 4 per blocking session.

**Interpretation:** the gate fires usefully. 32.8% of sessions contain at least one instance of option-theater that the gate would catch. The 6.6% false-positive source (`<think>` blocks containing internal "should I do X?" reasoning) was fixed by stripping thinking blocks before pattern matching.

## Q2: Option-theater persistence (operator correction rate)

| Metric | Value |
|-----------|-------|
| Real would-block messages | 661 |
| Followed by operator correction | 4 (0.6%) |
| Ratio (blocks : corrections) | **1 : 165** |

**Interpretation:** the operator silently absorbs 99.4% of option-theater events. The hook's value is **prevention, not catch** — it would prevent ~165× more option-theater events than the operator currently corrects. This makes it a high-leverage enforcement mechanism relative to its cost (one regex match per Stop event).

## Q3: EGDP template baseline

| Metric | Value |
|-----------|-------|
| Recommendation messages (visible, ≥80 chars) | 687 |
| Evidence cited BEFORE recommendation | 414 |
| **EGDP-shaped rate** | **60.3%** |
| Non-compliant (room to gain) | 39.7% |

**Per-session:** 24% of sessions are fully EGDP-shaped, 61% partially, 15% not at all.

**Interpretation:** the model already structures evidence-before-recommendation in 60% of cases. The EGDP template adds value on the remaining 40% (~273 messages across the corpus). Re-measure after 5+ sessions with the template active to measure lift.

## Implications for Layer 3 (Pydantic AI structured-output envelope)

The measurement shows the Stop hook achieves **93.4% precision** (→ ~100% after the `<think>` fix). Layer 3 (structured output enforcement) would provide diminishing returns over this baseline. **Decision: defer Layer 3 until the Stop hook + EGDP template's measured lift plateaus below target.** Re-evaluate after 5+ sessions.

## Re-measurement protocol

1. Re-run `P:/tmp/measure_enforcement_v2.py` after 5+ sessions with the enforcement active
2. Compare:
   - Q1: does the raw block count decrease? (the hook blocks option-theater, so it should)
   - Q2: does the correction rate stay flat? (operator corrections shouldn't increase)
   - Q3: does the EGDP-shaped rate increase from the 60.3% baseline?
3. If EGDP rate >80% and block count decreased >50%, the enforcement is working
4. If EGDP rate unchanged, the template isn't firing under pressure → consider Layer 3

## Falsifier

This baseline is wrong if:
- The scanner's delegation patterns don't match what the operator considers option-theater (precision may be lower than 93.4%)
- The EGDP detection (evidence cited before recommendation) is too loose (evidence patterns match non-evidence text)
- The 412-session sample isn't representative (selection bias toward sessions with issues)
