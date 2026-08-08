# Design: Trajectory-Validity Gate (Layer 3)

**Status:** design-complete, measurement-validated, ready for implementation
**Session:** 019fde3e
**Date:** 2026-08-07
**Parent handoff:** `docs/handoffs/trajectory-validity-layer3-design-20260807/HANDOFF.md`
**Falsified prior:** `[[layer3-claim-extraction-falsified-trajectory-validity-is-field-standard-2026]]`

---

## TL;DR

A deterministic Stop hook that checks whether the agent searched the required
evidence space before making a capability claim. When the agent says "we
can't verify X" or "X doesn't exist" without having grepped the wiki or
skills catalog, the gate fires an advisory. No LLM in the hot path. The
trajectory check is deterministic — the detection regex is the precision
bottleneck, and this design addresses it with a two-layer filter.

---

## ALTERNATIVES GATE

**Options:**
1. **Regex detection + deterministic trajectory check** (no LLM)
2. **Regex pre-filter + LLM assertion/discussion filter** (like `Stop_claim_judge.py`)
3. **LLM-only claim classification + trajectory check**

**Selection criterion:** determinism + latency + no quota in hot path + GroundEval principle (deterministic scoring)

**Chosen: Option 1** (regex + deterministic) — wins because:
- GroundEval's core principle is deterministic scoring; LLM-as-judge is what it replaces
- `Stop_claim_judge.py` already exists for state/prediction claims (Option 2 territory); this gate targets a DIFFERENT claim class (capability claims) where regex precision is higher
- No quota consumption, no external API dependency, ~60ms total latency
- The measurement shows regex precision is workable with refinement (69% for capability claims)

**Rejected: Option 2** — adds 0.8s latency + Groq dependency for marginal precision gain. The assertion/discussion distinction is easier for capability claims ("we can't verify X") than for state claims ("X is stale") because capability claims have a distinctive syntactic form (agent-voice + negation + capability verb).

**Rejected: Option 3** — LLM-only reintroduces the LLM-as-judge problem GroundEval was designed to solve. Defeats the purpose.

---

## Measurement results (the evidence behind this design)

Retrodiction over **50 sessions, 288 turns, 1742 assistant messages**. Scripts:
`P:/tmp/trajectory_measure.py`, `P:/tmp/refined_analysis.py`. Raw data:
`P:/tmp/trajectory_measure_detections.jsonl`.

### Detection precision by claim type

| Claim type | Raw detections | Real claims | Precision | SILENT catches |
|---|---|---|---|---|
| NEGATIVE_EXISTENCE (broad) | 50 | ~7 | 14% | 1 (Instance 2) |
| NEGATIVE_EXISTENCE (refined: capability only) | 16 | ~5 | 69% (after discussion filter) | 1 (Instance 2) |
| SESSION_STATE | 2 | 0 | 0% (both were discussion of Instance 4) | 0 |
| SKILL_SYNTAX | 2 | 2 | 100% | 0 (both had evidence) |

### The critical catch

**Instance 2 (Cohere quota claim)** was detected as a true SILENT at
`019fd698:43`: the agent said "we cannot verify Cohere's monthly quota from
this host" without grepping the wiki. The wiki concept documenting exactly
how to do this was one grep away. **The gate would have fired.**

### The precision problem

The broad NEGATIVE_EXISTENCE pattern (`doesn't exist`, `we can't do X`) is
too noisy:
- **34 of 50 detections** (68%) are file/code claims where the evidence
  space is the file system (not wiki). The agent correctly checked via
  `read_file`/`list_dir` — an advisory saying "did you grep the wiki?" would
  be noise.
- **~16 detections** are discussion (quoting the pattern in design docs or
  self-corrections) — not real claims.

The refined capability pattern (`we/I + can't/cannot + do/verify/check/determine`)
reduces detections by 68% and raises precision to 69%. But it still catches
hedging ("I can't verify without burning quota") and discussion-quoting.

### Design resolution: two-layer filter

1. **Layer 1 — Regex detection** (refined capability pattern, ~50ms)
2. **Layer 2 — Context filter** (drop detections inside quotes, design-proposal
   sections, or self-correction contexts, ~5ms)

This is deterministic, fast, and addresses the precision problem without an LLM.

---

## Architecture

```
Stop event fires
       │
       ▼
┌─────────────────────────┐
│  1. Parse response text │  ← stdin JSON → response text
│     + transcript tail   │  ← GROK_SESSION_ID → chat_history.jsonl
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  2. Detect claims       │  ← regex patterns (capability, session-state)
│     (Layer 1)           │
└───────────┬─────────────┘
            │ claims found?
            │ no → exit 0
            ▼
┌─────────────────────────┐
│  3. Context filter      │  ← drop quoted, design-proposal, self-correction
│     (Layer 2)           │
└───────────┬─────────────┘
            │ claims survive?
            │ no → exit 0
            ▼
┌─────────────────────────┐
│  4. Parse tool trace    │  ← assistant.tool_calls from transcript
│     (trajectory)        │    [{name, arguments}] per turn
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  5. Evidence-space      │  ← for each claim type, check if required
│     check               │    tools were called this turn
└───────────┬─────────────┘
            │ all claims have evidence?
            │ yes → exit 0
            ▼
┌─────────────────────────┐
│  6. Advisory output     │  ← stderr: "Claim X lacks evidence search for Y"
│     (advisory mode)     │    exit 0 (advisory) or exit 2 (blocking)
└─────────────────────────┘
```

### Tool-trace parsing (Grok Build format)

The Grok transcript (`chat_history.jsonl`) records tool calls in assistant
messages' `tool_calls` field:

```json
{
  "type": "assistant",
  "content": "I'll check the wiki...",
  "tool_calls": [
    {"id": "call_abc123", "name": "grep", "arguments": "{\"pattern\": \"cohere\", \"path\": \"P:/.data/wiki/concepts/\"}"}
  ]
}
```

The parser:
1. Reads the transcript tail (last 1MB — bounded for latency)
2. Finds the current turn boundary (last real user message)
3. Collects all `tool_calls` from assistant messages in the current turn
4. For each tool call, extracts `{name, arguments}` (arguments is a JSON string)

This is a Grok-format adapter of the existing (dormant, Claude-format)
`build_turn_tool_events()` at `P:/.claude/hooks/__lib/turn_tool_events.py`.

### Evidence-space → tool mapping

| Claim type | Detection pattern | Required evidence | Tools that satisfy |
|---|---|---|---|
| Capability claim | `we/I + can't/cannot + verify/check/do/determine` | Wiki + skills catalog | `grep`/`rg` on wiki/concepts/skills paths; `search_tool` (MCP search_wiki); `read_file` on wiki/skills |
| Session-state claim | `context/quota + is/at + number%` | State probe | `run_terminal_command` with `/context`, `/quota`, `fleet_quota`, `pick_model` |
| Skill-syntax claim | `/skill + means/refers to` | SKILL.md | `read_file` on SKILL.md path; `grep` on skill docs |

### Composition with existing systems

| System | Question it answers | Overlap with trajectory gate? |
|---|---|---|
| `verification_receipt_writer.py` (PostToolUse) | "Was a verification command run for file X?" | None — checks command execution per file, not evidence-space coverage per claim |
| `Stop_claim_judge.py` (Stop, LLM) | "Are state/prediction claims supported by tool evidence?" | Adjacent — targets different claim class (state/prediction vs capability). Both fire on Stop; claim-judge uses LLM, trajectory gate uses deterministic check |
| `quality_gate.py` (Stop) | "Do modified files have covering receipts?" | None — checks file-level receipt coverage, not claim-level evidence search |

The trajectory gate is **complementary** to all three. It answers a question
none of them ask: "for this specific claim type, did the agent search the
right evidence space?"

---

## Detection patterns (refined, post-measurement)

### NEGATIVE_CAPABILITY (refined from measurement)

```python
# Layer 1: detect capability claims in agent voice
NEGATIVE_CAPABILITY_RE = re.compile(
    r"\b(?:we|I|this\s+(?:host|workspace))\s+"
    r"(?:can'?t|cannot|don'?t|do\s+not|unable\s+to)\s+"
    r"(?:verify|check|determine|confirm|access|reach|provide|do)\b"
    r"(?!.*(?:cross-domain|without burning|without checking))",  # exclude hedging
    re.IGNORECASE,
)
```

Measurement result: 16 detections per 50 sessions → ~5 real claims → ~1 true SILENT catch.

### SESSION_STATE

```python
# Instance 4 pattern: "context budget is too deep" / "session is at X%"
SESSION_STATE_RE = re.compile(
    r"(?:"
    r"\bcontext\s+(?:budget|window|usage|limit)?\s*(?:is|too|approaching)\s+(?:deep|full|low|exhausted|near)\b"
    r"|"
    r"\b(?:session|turn)\s+(?:is|at)\s+\d+\s*%\b"
    r"|"
    r"\bquota\s+(?:is|at|remaining)\s+\d+\b"
    r")",
    re.IGNORECASE,
)
```

Measurement result: 2 detections per 50 sessions (both were discussion). True frequency is
likely ~1-2 per 50 sessions (Instance 4 itself was in the data but phrased differently).

### SKILL_SYNTAX

```python
SKILL_SYNTAX_RE = re.compile(
    r"/\w+\s+(?:means|refers\s+to|stands\s+for|indicates|specifies)\b"
    r"|"
    r"/\w+\s+\{[^}]+\}\s+(?:means|is|fires|controls|overrides)\b",
    re.IGNORECASE,
)
```

Measurement result: 2 detections per 50 sessions, both had evidence. True frequency is low
but the claim type is high-precision when it fires.

---

## Context filter (Layer 2 — precision refinement)

Drop detections that appear in:

1. **Quoted text** — inside backticks, code blocks, or quotation marks
2. **Design/proposal sections** — preceded by "the broader pattern", "structural fix", "Unit N", "a similar hook could"
3. **Self-correction** — preceded by "my earlier claim", "I was wrong", "the operator corrected"
4. **Hedging** — followed by "without burning/checking/testing" (the agent is acknowledging a limitation, not claiming a gap)

This is ~20 lines of regex/string matching, deterministic, ~5ms.

---

## Enforcement strategy

### Phase 1: Advisory (ship immediately)
- Mode: `advisory` (exit 0 always, stderr message)
- Duration: until ≥50 live detections accumulated
- Telemetry: append to `P:/.claude/hooks/.evidence/trajectory-gate.jsonl`

### Phase 2: Promotion evaluation
- Run Wilson 95% CI on accumulated detections
- If FP ≤30% (Wilson lower bound): promote to `blocking` (exit 2 on SILENT)
- If FP >30%: refine patterns, re-measure, stay advisory

Per `[[advisory-vs-blocking-enforcement-decision-2026]]`.

---

## Latency budget

| Step | Cost | Notes |
|---|---|---|
| Read transcript tail (1MB) | ~5ms | Bounded seek + read |
| Parse tool_calls | ~3ms | JSON parse, last turn only |
| Regex detection (3 patterns) | ~50ms | Over response text (~10K chars typical) |
| Context filter | ~5ms | String matching on detected claims |
| Evidence-space check | ~2ms | Dict lookup per claim |
| **Total** | **~65ms** | Well under 10s Stop timeout |

No LLM, no external API, no quota consumption.

---

## What this design does NOT address (honest scope)

| Instance | Addressed? | Why |
|---|---|---|
| 1: Fabricated skill syntax | ✓ (SKILL_SYNTAX pattern) | Agent must read SKILL.md before claiming syntax |
| 2: Wrong capability claim | ✓ (NEGATIVE_CAPABILITY pattern — validated by measurement) | Agent must grep wiki before claiming "can't do X" |
| 3: Rate/quota conflation | ✗ | Conceptual error, no deterministic evidence space |
| 4: Fabricated context excuse | ✓ (SESSION_STATE pattern) | Agent must run /context before claiming budget pressure |
| 5: No /www before recommendation | ✗ | Assertion-vs-discussion unsolved (67% FP documented) |

3 of 5 instances addressed. Instances 3 and 5 remain out of scope per the
handoff — the field has not solved deterministic detection for these classes.

---

## Implementation plan

### Task 1: Build the Grok-format tool-trace parser
- **File:** `~/.grok/hooks/scripts/trajectory_tool_parser.py`
- **What:** Parse `tool_calls` from assistant messages in `chat_history.jsonl`
- **Adapt from:** `P:/.claude/hooks/__lib/turn_tool_events.py` (Claude format → Grok format)
- **Test:** unit test against a known transcript sample
- **Verify:** `python -m pytest ~/.grok/hooks/tests/test_trajectory_tool_parser.py`

### Task 2: Build the detection module
- **File:** `~/.grok/hooks/scripts/trajectory_detection.py`
- **What:** The 3 detection patterns + context filter + evidence-space checker
- **Test:** run against the 50-session retrodiction corpus; confirm Instance 2 is caught
- **Verify:** `python P:/tmp/trajectory_measure.py 50` with the new detection module plugged in

### Task 3: Build the Stop hook
- **File:** `~/.grok/hooks/scripts/Stop_trajectory_validity.py`
- **What:** Wire detection + parser + evidence check into a Stop hook
- **Registration:** `~/.grok/hooks/trajectory-validity.json` (Stop event, 10s timeout)
- **Mode:** advisory (exit 0)
- **Test:** manual fire against a session with known Instance 2 text
- **Verify:** run the hook against the current session's transcript; confirm it fires on SILENT

### Task 4: Ship advisory + accumulate telemetry
- Deploy hook in advisory mode
- Accumulate ≥50 live detections in `trajectory-gate.jsonl`
- Label TP/FP
- Evaluate Wilson CI for promotion to blocking

### Dependency order
Task 1 → Task 2 (uses parser) → Task 3 (uses detection) → Task 4 (deploy + measure)

---

## Falsifier

This design is wrong if:
1. **The context filter (Layer 2) cannot reduce FP below 30%.** The measurement
   shows ~69% precision after discussion filtering; the context filter adds
   hedging/quote/design-proposal exclusion. If live FP remains >30% after 50
   detections, the gate stays advisory and patterns need further refinement.
2. **The tool-trace parser misses tool calls** (false SILENT — the agent DID
   search but the parser didn't detect it). Mitigated by testing against known
   transcripts. Measured by the retrodiction's "with evidence" rate.
3. **Instance 2 is an outlier** (the only true SILENT in 50 sessions). If the
   true SILENT rate is <1 per 100 sessions, the gate's value may not justify
   the complexity. Instance 2 cascaded into the entire Layer 3 investigation,
   so even 1 per 50 sessions has high value — but this is a judgment call.

---

## Receipts

- **Transcript format probe:** `P:/tmp/probe_transcript_format.py` → confirmed
  `tool_calls` field in assistant messages, `tool_result` with `tool_call_id`
- **Transcript detail probe:** `P:/tmp/probe_transcript_detail.py` → confirmed
  `tool_calls: [{id, name, arguments}]` structure
- **Measurement script:** `P:/tmp/trajectory_measure.py` → 50 sessions, 54 detections
- **Raw detections:** `P:/tmp/trajectory_measure_detections.jsonl` → 54 records
- **Refined analysis:** `P:/tmp/refined_analysis.py` → capability pattern reduces
  detections 68%, precision to 69%
- **Instance 2 catch:** detection at `019fd698:43` — "we cannot verify Cohere's
  monthly quota" — SILENT (no wiki grep), confirmed as the exact documented failure
- **Existing parser (dormant):** `P:/.claude/hooks/__lib/turn_tool_events.py` —
  Claude format, needs Grok adapter
- **Existing claim judge:** `~/.grok/hooks/scripts/Stop_claim_judge.py` — LLM-based,
  targets state/prediction claims (different class)
- **Receipt system:** `~/.grok/hooks/scripts/verification_receipt_writer.py` —
  PostToolUse, file-level receipt coverage (complementary)
