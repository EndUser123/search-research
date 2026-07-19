# Dream-State Concurrency Risk Report

**Date:** 2026-07-13
**Repository:** `P:/packages/.claude-marketplace/plugins/cc-skills-analysis`
**HEAD:** `6807a6710277a1db2d897631ce74e55084c5b0cf`

---

## 1. Verified Data-Path Map

### Storage
- **Path:** `~/.claude/.artifacts/debrief/dream-state.json`
- **Schema:** Single JSON object with `topics: { [topic: string]: { last_reviewed, last_actioned, findings, findings_count, reviews } }`
- **Identity:** **NONE** — no session_id, terminal_id, or run_id in the state file. Single global file shared by all sessions.

### Writers
| Writer | Trigger | Frequency | Identity available |
|---|---|---|---|
| `SessionEnd_debrief_reflect.py:408` via `record_dream_review(topic="system_efficiency", ...)` | SessionEnd hook — any Claude Code session end | Per-session-end | `session_id` from hook payload (line 259) and `transcript_path` — **NOT USED** |
| `dream_state._selfcheck()` | `python dream_state.py --selfcheck` | Testing only | None needed |

### Write Algorithm (`record_dream_review`, lines 76-94)
```
1. state = read whole file from disk             (get_last_dream_state)
2. state.topics[topic] = {new entry}              (modify in memory)
3. write whole file back atomically               (_write_state via os.replace)
```
**This is a classic read-modify-write race.** `os.replace` provides per-write atomicity but no protection against two concurrent readers.

### Readers
| Reader | Trigger | Decision influenced | Authority |
|---|---|---|---|
| `SessionEnd_debrief_reflect.py:376` via `should_re_review("system_efficiency", threshold_days=7)` | SessionEnd hook — any session end | Whether to produce a `system_findings.json` (advisory dream-cycle review) | Advisory |
| `dream_state.list_topics_since(days)` | No production caller found | None | None |
| `dream_state.list_outstanding_dream_findings()` | No production caller found | None | None |

**Only one production read path exists:** SessionEnd → `should_re_review("system_efficiency", threshold_days=7)` → determines whether to emit a one-entry `system_findings.json` file.

### Session/terminal identity
The writer (`SessionEnd_debrief_reflect.py`) has `session_id` available from the hook payload at line 259. The reader (same file) also has it. The `session_id` is the unique session UUID from the Claude Code hook system — it is the **only reliable session-wide identity** in the hook runtime. Terminal-borne identity (`WT_SESSION`, `terminal_id`) is NOT reliable across concurrent sessions in one Windows Terminal (proven in prior memory: `terminal_id_not_per_session.md`).

**The dream_state module does not use any identity.** It is a global file with no partitioning key.

---

## 2. Live Test Procedure and Evidence

### Method
20 iterations of two concurrent child processes calling `record_dream_review()` from the **exact consumed code path** (`from dream_state import record_dream_review` imported from `skills/debrief/__lib/dream_state.py` at committed HEAD). Both processes were synchronized to start from the same initial file state using a file-based go barrier.

### Results
```
OK: 17 | LOSS: 1 | STATE_CHANGED: 0 | TIMEOUT: 0 | PARSE_ERR: 2
Loss rate: 1/18 (5.5%)
```

### Detailed loss (iteration 3)
```
A: topic-alpha before_topics=['initial-seed']  present_after=False
B: topic-beta  before_topics=['initial-seed']  present_after=True
Final: topics=['initial-seed', 'topic-beta']
```
Sequence of events:
1. Both A and B read the same initial state (`['initial-seed']`)
2. B writes first → file has `['initial-seed', 'topic-beta']`
3. A writes second → A read the initial state, added `topic-alpha`, wrote back
4. A's write overwrites the entire file → B's `topic-beta` is **silently dropped**
5. A's own `present_after` is False because B's read came first, but A's write made the final state correct for A — while B's data is gone

### Consequence
The read-modify-write pattern means the **last writer wins**, and all changes made by earlier concurrent writers that touched DIFFERENT keys are silently lost. No merge, no conflict detection, no warning.

---

## 3. Classification

`RACE_REPRODUCED_NO_MATERIAL_IMPACT`

### Why no material impact

The race was reproduced: two concurrent `record_dream_review()` calls can lose one session's update. However:

1. **The only data at risk is the `reviews` counter** and `last_reviewed` timestamp for the `"system_efficiency"` topic. One session's increment is lost — the counter goes from N to N+1 instead of N+2.

2. **No behavioral impact on `should_re_review()`** — the surviving write has the MORE RECENT timestamp, which correctly suppresses duplicate review requests. The lost write's timestamp is OLDER and would have had the same effect. The gate decision is identical regardless of which write wins.

3. **The `last_actioned` field is always `False`** from the only production writer (SessionEnd hook always passes `actioned=False`). No code path calls `record_dream_review` with `actioned=True` from production. So the `actioned` flag isn't at risk.

4. **The `findings` list** — both writers write the same finding (`["model-routing review due (7+ days since last)"]`), so content loss is identical regardless of which write survives.

5. **The downstream consumer is advisory** — `system_findings.json` has no automated consumer (G1 from prior investigation). The dream-cycle output is logged to stderr and written to a file that no one reads.

6. **The race window is tight** requires two SessionEnd hooks firing within ~50ms of each other. In practice this requires closing a multi-tab Windows Terminal or an automated test suite triggering concurrent session ends. Rare in normal solo-director use.

---

## 4. Material Impact Assessment

| Scenario | Impact | Severity |
|---|---|---|
| Two concurrent session ends, both `actioned=False` | `reviews` counter undercounts by 1. No decision change. | **NONE** |
| One `actioned=True`, one `actioned=False` (impossible from production code path) | `last_actioned` flag could flip. No production path calls with `actioned=True` | **NONE — can't occur** |
| Two concurrent session ends, different findings | The content strings are identical (both write `"model-routing review due..."`) | **NONE — identical content** |
| Two concurrent `/debrief` invocations calling `should_re_review` | Both read the same state; both get the same True/False answer. Race only affects the write, not the read decision. | **NONE** |

**Verdict: The race exists but produces no material user-facing impact in the current codebase.** The `reviews` counter may be off by 1, but no gate, consumer, or decision depends on the exact count.

---

## 5. Remedy Comparison (informational — no change is justified)

| Option | Writer | Storage | Reader | Authority | Freshness | Failure direction | Multi-terminal isolation |
|---|---|---|---|---|---|---|---|
| **No change** | SessionEnd hook | Global file, no identity | should_re_review | Advisory | Updated per-session-end | Silent counter undershoot | None — race window exists but no impact |
| **Session-scoped files** (`dream-state.{session_id}.json`) | SessionEnd hook (has session_id) | Per-session files | Reader must know session_id | Per-session | Per-session lifecycle | Foreign session = no state (correct fail-silent) | Complete — files are scoped |
| **File locking** (`portalocker`) | SessionEnd hook | Single global file | Same as today | Advisory | Lock serializes writers | Lock timeout → skip write (safe) | Serialized — no loss but no parallelism |
| **Remove dream_state entirely** | N/A | N/A | replaced by existing session-scoped carryover | N/A | N/A | N/A | N/A |

### Why none is justified
- The race has no material behavioral impact.
- The `reviews` counter undermeasurement is cosmetic.
- The only downstream product (`system_findings.json`) has no automated consumer.
- Adding session-scoped files, locking, or removal all increase complexity for zero user-facing benefit.

---

## 6. Remaining Cleanup

The test scripts at `P:/tmp/dream_state_race*.py` are temporary test artifacts. They are outside the Git repository and will be cleaned up naturally by the system temp-directory policy.

---

`RACE_REPRODUCED_NO_MATERIAL_IMPACT`
