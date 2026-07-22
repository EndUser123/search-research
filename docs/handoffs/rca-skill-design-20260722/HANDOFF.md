---
thread_id: b774282c-1a5e-4054-9897-d838af5dbd6f
parent_handoff_path: none
current_session_id: 019f819a-7619-7cb3-a6a4-480ff1c916ce
current_terminal_id: console
produced_at: 2026-07-22T15:30:00Z
status: open
handoff_type: design
accurate_as_of_head: 126891056635ff42155ee68027aeda11fc6cf2d2
assigned_to: unassigned
---

# Handoff: Design and build an RCA skill

## 1. Objective

Create a `/rca` skill that provides a systematic diagnostic method for failures
that are NOT code-change bugs (those are covered by `debugging-protocol.md`'s
green-state axiom). The skill covers: API failures, model dispatch failures,
config issues, transport/protocol mismatches, and quota/rate-limit problems.

## 2. Status

**Design only — not yet implemented.**

This handoff captures the design rationale, what should be in the skill, and
reference incidents that shaped the design.

## 3. Why this skill is needed (the gap)

### What exists

| Artifact | Covers | Doesn't cover |
|----------|--------|---------------|
| `P:/.claude/rules/debugging-protocol.md` | Code-change bugs (green-state axiom), runtime mismatch (wrong code running), user observation hierarchy | API failures, model dispatch issues, config problems |
| `~/.grok/AGENTS.md` "Mandatory Preflight" | Pre-change discovery (inventory before editing) | Post-failure diagnosis |
| `~/.grok/AGENTS.md` "Blocker Triage" | Classifying blockers (domain/env/tool/decision/data/scope) | The actual diagnostic method |
| `/check` skill | Session verification (PASS/FAIL on claims) | Root cause identification |
| `/aar` skill | Retrospective analysis (post-session) | Real-time diagnosis |

### What's missing

A systematic method for: "something is failing and I don't know why. How do I
find the root cause efficiently, with evidence, without guessing?"

## 4. Reference incidents (why each feature exists)

### Incident 1: DiffusionGemma empty content via spawn_subagent (2026-07-21/22)

**Symptom:** `spawn_subagent(model="nvidia-diffusiongemma-26b")` returns empty
content. Direct API calls work fine.

**Time spent before diagnosis:** ~4 hours across two sessions.

**What the other LLM did right:** systematic layer isolation — direct curl
(no Grok), single-turn vs multi-turn, with/without tool_calls, max_tokens sweep.
Eliminated 6 hypotheses with receipts before finding the actual cause.

**What went wrong initially:** multiple wrong diagnoses (thinking mode, max_tokens,
force_nonempty_content parameter). Each was stated as fact without a verification
receipt. The host's receipt rule eventually forced correction.

**Lesson:** layer isolation + hypothesis elimination with receipts is the method.
Jumping to the first plausible explanation wastes hours.

### Incident 2: Gemini Pro "quota exceeded, limit: 0" (2026-07-21)

**Symptom:** `gemini-2.5-pro` returns 429 with "limit: 0" on free tier.

**Initial diagnosis (wrong):** "Pro models have zero free-tier access."

**Actual cause:** daily RPD exhaustion. Pro models have ~50 RPD on free tier,
not zero. The "limit: 0" message appears after the daily quota is used up, not
as a permanent policy.

**Lesson:** error messages can be misleading. The "limit: 0" was accurate for
that moment (0 requests remaining) but not the permanent limit.

### Incident 3: Stop hook "can't access agent text" (2026-07-21)

**Symptom:** Agent claimed Stop hook can't access agent text on Grok Build.

**What happened:** the agent inferred this from reading the hook docs (which
described the payload fields) without actually checking what data was available.
The `chat_history.jsonl` workaround was sitting in the workspace's own
`STOP_PAYLOAD_SCHEMA_LIMITATION.md`.

**Lesson:** read existing workspace artifacts before concluding something is
impossible. The `STOP_PAYLOAD_SCHEMA_LIMITATION.md` was written 2026-06-18 and
already documented the workaround.

### Incident 4: Serper API 403 (2026-07-21)

**Symptom:** Serper search API returns 403 Unauthorized.

**Initial assumption:** rate limiting.

**Actual cause:** expired/invalid API key. The key was present in `.env` but
no longer valid.

**Lesson:** distinguish auth failures (401/403) from rate limits (429). Don't
assume rate limiting when the status code says unauthorized.

## 5. Proposed skill design

### Name: `/rca`

### Trigger phrases

- "why does X fail"
- "root cause"
- "what's wrong with"
- "debug this failure" (when NOT a code-change bug)
- "why isn't X working"
- "diagnose this"

### When to use vs NOT use

| Use `/rca` | Use instead |
|------------|-------------|
| API returns errors (400, 401, 403, 429, 500, empty content) | Code-change bug → `debugging-protocol.md` |
| Model dispatch fails (spawn_subagent returns error) | Code review → `/review` |
| Config issue (wrong model loaded, missing env var) | Session retrospective → `/aar` |
| Transport/protocol mismatch (empty content, wrong format) | Claim verification → `/check` |
| Quota/rate-limit investigation | |
| "This used to work, now it doesn't" (non-code change) | |

### Core method: LIMED (Layer Isolation, Monitor, Eliminate, Document)

**Step 1: Layer Isolation**

Identify which layer the failure occurs at:

| Layer | How to test | Tool |
|-------|-------------|------|
| **Model/API** | Direct curl/HTTP call, no client | `run_terminal_command` with `Invoke-RestMethod` or `curl` |
| **Client (Grok Build)** | Check what Grok actually sends | `chat_history.jsonl`, `events.jsonl` in session dir |
| **Config** | Read config.toml, .env, settings.json | `read_file`, `grep` |
| **Transport** | Single-turn vs multi-turn; with/without tools | Controlled API calls |
| **Environment** | Env vars, PATH, process state | `Get-ChildItem env:`, `Get-Command` |

**Step 2: Hypothesis enumeration**

List ALL plausible hypotheses before testing any:

```
H1: <first plausible explanation>
H2: <second plausible explanation>
H3: <third>
...
```

**Step 3: Elimination with receipts**

Test each hypothesis. For each, record:
- What was tested
- How it was tested (command or action)
- What was observed
- Verdict: ELIMINATED / CONFIRMED / INCONCLUSIVE

**Step 4: Confirm the root cause**

When one hypothesis is confirmed:
- State the root cause in one sentence
- Name the specific layer where it occurs
- Name the fix (or the fix path if it requires upstream change)
- Name the falsifier (what would prove this diagnosis wrong)

**Step 5: Document**

Write the RCA as a structured finding:
```
ROOT CAUSE: <one sentence>
LAYER: <model/API/client/config/transport/environment>
EVIDENCE: <tool call receipts>
HYPOTHESES ELIMINATED: <list with reasons>
FIX: <action or fix path>
FALSIFIER: <what would prove this wrong>
```

### Pattern library (failure-mode → first checks)

| Symptom | First checks |
|---------|-------------|
| Model returns empty content | (1) max_tokens too low? (2) thinking mode required? (3) multi-turn history format? |
| API returns 401/403 | (1) Key expired? (2) Wrong env var? (3) Key not loaded in process env? |
| API returns 429 | (1) Daily quota (RPD) exhausted? (2) Per-minute limit (RPM) hit? (3) Burst-fire without spacing? |
| API returns 400 "bad request" | (1) Request payload format wrong? (2) Required field missing? (3) Provider-specific validation stricter than spec? |
| spawn_subagent returns error | (1) Model slug valid for this session? (2) Model supports tool use? (3) Provider reachable? |
| "This used to work" | (1) What changed? Config, env, model version, API version? (2) Is the same code running? |
| Works for trivial, fails for real tasks | (1) Context window exceeded? (2) Tool-call format mismatch? (3) Multi-turn history issue? |

### Integration with existing artifacts

| Existing | How `/rca` integrates |
|----------|----------------------|
| `debugging-protocol.md` (green state axiom) | `/rca` handles non-code-change failures; debugging-protocol handles code-change failures. Both apply when a code change triggers an API/config issue. |
| `AGENTS.md` "Blocker Triage" | `/rca` feeds the blocker classification: after root cause is found, classify (domain/env/tool/decision/data/scope) |
| `AGENTS.md` "Verification receipt rule" | Every hypothesis test in `/rca` must have a receipt (tool call output). Unreceipted diagnoses are `[INFERENCE]`. |
| `/check` | `/rca` produces causal claims; `/check` can verify them against code/runtime |
| `tool-fallbacks.md` | Pattern library entries can link to known-broken combinations |

### What NOT to do (anti-patterns from reference incidents)

1. **Don't state the first plausible explanation as fact.** (Incident 1: "thinking mode is the cause" — wrong)
2. **Don't assume the error message tells you the root cause.** (Incident 2: "limit: 0" meant exhausted, not zero-policy)
3. **Don't conclude something is impossible without checking workspace artifacts.** (Incident 3: chat_history.jsonl workaround was already documented)
4. **Don't conflate status codes.** (Incident 4: 403 ≠ 429)
5. **Don't test hypotheses in your head.** Test them with tool calls and record the receipt.
6. **Don't skip layer isolation.** If you haven't tested the API directly (no client), you haven't isolated the model layer from the client layer.

## 6. Proposed output format

```markdown
# RCA: <failure description>

## Symptom
<what was observed>

## Root cause
<one sentence>

## Layer
<model/API/client/config/transport/environment>

## Evidence
<tool call receipts — each cited with the command/output that confirms>

## Hypotheses tested
| # | Hypothesis | Test | Result |
|---|-----------|------|--------|
| H1 | <explanation> | <what was tested> | ELIMINATED: <why> |
| H2 | <explanation> | <what was tested> | CONFIRMED: <why> |

## Fix
<action taken or fix path>

## Falsifier
<what would prove this diagnosis wrong>
```

## 7. Suggested skill location

`~/.grok/skills/rca/SKILL.md` — user-level Grok skill, same as `/tp`, `/check`, `/go`.

## 8. Reference incidents to cite in the skill

| Incident | Date | Root cause | Time wasted |
|----------|------|-----------|-------------|
| DGemma empty content via spawn_subagent | 2026-07-21/22 | NVIDIA validator rejects empty-content assistant messages on tool-call turns | ~4 hours |
| Gemini Pro "limit: 0" | 2026-07-21 | Daily RPD exhaustion, not permanent zero-policy | ~30 min |
| Stop hook "can't access agent text" | 2026-07-21 | Agent didn't check chat_history.jsonl (workaround was in workspace docs) | ~1 hour |
| Serper API 403 | 2026-07-21 | Expired API key, not rate limiting | ~15 min |

## 9. What to build

1. `~/.grok/skills/rca/SKILL.md` — the skill with the LIMED method, pattern library, output format, and anti-patterns
2. Optionally: `~/.grok/skills/rca/references/pattern-library.md` — expandable pattern library (loaded when the symptom matches)
3. Test: run `/rca` on a real failure to validate the method works

## 10. Non-blocking

This is a new skill creation — not blocking any operational work. Build when ready.
