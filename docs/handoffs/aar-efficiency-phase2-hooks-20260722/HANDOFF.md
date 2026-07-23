---
thread_id: aar-efficiency-phase2-hooks
parent_handoff_path: P:/docs/handoffs/aar-efficiency-phase1-detectors-20260722/HANDOFF.md
current_session_id: 019f8507-6395-7bc0-87a9-9122e28d68c8
current_terminal_id: console_896ff2fb-4053-4c04-9d6a-74e4
produced_at: 2026-07-23T02:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: b3fb5225caa69e4759ca6697df715b6b6214259d
---

# HANDOFF — Phase 2: AAR quality hooks + efficiency report format

## 1. Objective

Build the Stop hooks (narrativization detection + efficiency warnings) and the AAR report's efficiency section. Depends on Phase 1 detectors being tested and wired.

## 2. Status

**OPEN — UNBLOCKED.** Phase 1 complete (2026-07-23): detectors tested, aggregator wired, `aggregates.json` artifact written. Phase 2 can start immediately.

## 3. Producing context

- **Phase 1 handoff:** `P:/docs/handoffs/aar-efficiency-phase1-detectors-20260722/HANDOFF.md`
- **Parent handoff:** `P:/docs/handoffs/aar-narrativization-hook-20260722/HANDOFF.md` (original design)
- **Red-team findings C3, M2 resolved here**

## 4. Read-first list

1. Phase 1 handoff — detector implementations + thresholds
2. `~/.grok/docs/user-guide/10-hooks.md` — Grok Build hook events, JSON format, matchers, Stop-decision-control
3. `~/.grok/plugins/proposal-grounding-monitor/hooks/hooks.json` — working example of a Grok-native Stop hook
4. `~/.grok/plugins/proposal-grounding-monitor/scripts/stop_detect.py` — working Stop hook implementation
5. `~/.grok/active-surface.last.md` — confirms which hooks actually fire
6. Wiki: `windows-gitbash-hook-invocation.md` — hooks fire via shebang, not executable bit
7. Wiki: `writing-discipline-not-enforced.md` — why advisory rules need structural enforcement

## 5. Verified facts

- [FACT] Stop hooks fire under Grok Build when registered as plugin `hooks/hooks.json` entries. Verified by `~/.grok/active-surface.last.md:85-89` which lists PGM's Stop hook.
- [FACT] The Stop hook payload contains `response` / `last_assistant_message` / `transcript_path` — NOT the full tool-call history. Red-team C3 finding.
- [FACT] To get tool-call history, the hook must read `transcript_path` (pointing to `chat_history.jsonl`) and parse it. The parent handoff's constraint "must not read chat_history.jsonl" is impossible to satisfy — corrected here.

## 6. Current state

Blocked on Phase 1. Design complete; implementation not started.

## 7. Task packets

### TASK-01: Narrativization Stop hook (Grok-native)

- goal: Add a Grok-native Stop hook that warns when the assistant makes causal/behavioral claims without nearby verification tool calls.
- in scope: new plugin or new hook file at `~/.grok/hooks/stop-narrativization.json` + script; or extend an existing enabled plugin's `hooks/hooks.json`
- out of scope: efficiency warnings (TASK-02); PreToolUse enforcement
- files / anchors: `~/.grok/hooks/stop-narrativization.json` (new) + `~/.grok/hooks/scripts/stop_narrativization.py` (new); OR add to an existing plugin's hooks
- acceptance: when the assistant makes a causal claim ("nobody does X", "this is broken because Y") without a nearby read_file/grep/run_terminal_command, emit a systemMessage warning.
- falsifier: hook fires on legitimate analysis after reading code. FP rate >15% means regex too broad.
- verification level required: LIVE_BEHAVIOR

**Red-team C1 correction:** The parent handoff referenced `P:/.claude/hooks/Stop_diagnostic_analysis_quality_gate.py` — that file is in a disabled Claude Code plugin. The hook must be Grok-native: either `~/.grok/hooks/*.json` (global) or inside an enabled plugin's `hooks/hooks.json` (like PGM). Follow the pattern at `~/.grok/plugins/proposal-grounding-monitor/hooks/hooks.json`.

### TASK-02: Efficiency Stop hook (Grok-native, corrected design)

- goal: Add a Grok-native Stop hook that warns in real-time when efficiency waste patterns are detected.
- in scope: new hook file + script (same registration pattern as TASK-01)
- out of scope: AAR report format (TASK-03); detector implementation (Phase 1)
- files / anchors: `~/.grok/hooks/stop-efficiency.json` (new) + `~/.grok/hooks/scripts/stop_efficiency.py` (new)
- acceptance: when the agent reads the same file 3+ times or runs the same validation command 3+ times without intervening edits, emit a systemMessage warning.
- falsifier: hook fires on legitimate repeated reads (file changed between reads)
- verification level required: LIVE_BEHAVIOR

**Red-team C3 correction — mandatory design change:**

The Stop hook payload does NOT contain tool-call history. To maintain a rolling counter:

1. **Read `transcript_path` from stdin** — the payload includes the path to `chat_history.jsonl`.
2. **Parse the last N lines of `chat_history.jsonl`** — extract tool calls from the tail (not the full file). This is O(N) in lines read, not O(session_length).
3. **Maintain per-session state** at `~/.grok/state/stop_efficiency_<session_id>.json` — rolling counters per file_path / tool_name / error_pattern.
4. **Use atomic writes + file-lock** (msvcrt on Windows) per the existing `Stop.py:LOCK_FILE` pattern.
5. **Scan window = last 20 tool calls** — read backwards from the transcript tail until 20 tool-call events are found.

The parent handoff's constraint "must not read chat_history.jsonl" is dropped — it's physically impossible to maintain a sliding window without it.

**Red-team M2 correction — state isolation:**

State file location: `~/.grok/state/stop_efficiency_<terminal_id>_<session_id>.json`. Per-session, file-locked, atomic writes. Evict state files older than 4h (same TTL as PGM's session-scoped state). Lock files (`.json.lock`) evicted after same TTL.

### TASK-03: AAR report format — efficiency section

- goal: Add a "Token efficiency findings" section to the AAR report format.
- in scope: `~/.grok/skills/aar/SKILL.md` § "Required report format"
- out of scope: detector implementation (Phase 1); hook implementation (TASK-01/02)
- files / anchors: `~/.grok/skills/aar/SKILL.md:538-625` (report format section)
- acceptance: report includes heatmap table + waste-by-root-cause bullets + top recommendations
- falsifier: section is so verbose the operator skips it; or findings are generic
- verification level required: STATIC_INSPECTION

**Format (from operator feedback):**
1. Tool-call waste heatmap (compact table)
2. Waste by root cause (bullet points, high-confidence with fix recommendations, low-confidence without)
3. Top 3-5 recommendations

**Red-team L1:** Adding the section is safe — `output_validator.py` does not reject extra sections. But the structured aggregator output should be preserved in the packet alongside the markdown, so future tools can read it programmatically.

## 8. Open decisions

### Decision 1: One hook file or two?

Whether to combine narrativization + efficiency into one Stop hook file or keep separate. **Recommendation:** one file (`stop_quality_warnings.py`) with both detectors. Same registration, same dispatch, easier to enable/disable as a unit.

### Decision 2: Global hook or plugin hook?

Global (`~/.grok/hooks/*.json`) or inside an enabled plugin. **Recommendation:** global for now. If the hooks prove valuable, promote to a plugin later.

## 9. Hard constraints

1. Hooks must be Grok-native (`~/.grok/hooks/*.json` or plugin `hooks/hooks.json`), NOT Claude Code `.claude/settings.json` hooks.
2. Hooks must read `transcript_path` from stdin for tool-call history (payload doesn't include it).
3. State files must be per-session with file-locking + atomic writes.
4. Hooks are advisory only (systemMessage warning, not blocking) per Grok Build hook contract.
5. Emit at most 1 warning per Stop event (avoid cumulative noise).

## 10. Cross-reference couplings

- Phase 1: `aar-efficiency-phase1-detectors-20260722` (blocked on)
- Parent: `aar-narrativization-hook-20260722` (original design)
- Wiki: `windows-gitbash-hook-invocation.md`, `writing-discipline-not-enforced.md`
- Docs: `~/.grok/docs/user-guide/10-hooks.md`
- Example: `~/.grok/plugins/proposal-grounding-monitor/hooks/hooks.json`

## 11. Other outstanding streams

- Phase 1 detectors (prerequisite — must complete first)
- `aar-config-updates-20260722`: tool-fallbacks doc (independent)
- `file-editing-protocol-merge-20260722`: protocol merge (independent)

## 12. Explicit non-goals

- Do NOT build detectors (Phase 1)
- Do NOT use `.claude/settings.json` hook dispatch
- Do NOT block tool calls (advisory only)
- Do NOT compute token cost estimates

## 13. Resumption protocol

1. Verify Phase 1 is complete: `python -m pytest ~/.grok/skills/aar/tests/ -v` — all tests pass including new efficiency detector tests.
2. Read `~/.grok/docs/user-guide/10-hooks.md` for hook JSON format and Stop-decision-control.
3. Read PGM's `hooks/hooks.json` and `stop_detect.py` as a working example.
4. Implement TASK-01 + TASK-02 (can be one file).
5. Implement TASK-03 (report format in SKILL.md).
6. Test: invoke hook manually on a test transcript with 3+ identical reads.

## 14. Suggested next invocation

```
/go Implement AAR efficiency Phase 2: Stop hooks + report format. Follow
handoff at P:/docs/handoffs/aar-efficiency-phase2-hooks-20260722/HANDOFF.md.
Prerequisite: Phase 1 (aar-efficiency-phase1-detectors-20260722) must be
complete. Read ~/.grok/docs/user-guide/10-hooks.md for hook format.
Build TASK-01 + TASK-02 as one Grok-native Stop hook, then TASK-03 (report).
```

## 15. Last user message (verbatim)

> /handoff add the red-team findings to the handoff file, or create a phase 1 / phase 2 via two linked handoff files. Think of something optimal but all items need to be accounted for.

## 16. Epistemic labels

- [FACT] Stop hooks fire under Grok Build via plugin hooks/hooks.json (C1 refuted)
- [FACT] Stop hook payload lacks tool-call history (C3 verified)
- [FACT] output_validator.py accepts extra sections (L1 verified)
- [INFERENCE] One combined hook file is simpler than two
- [UNKNOWN] Whether the narrativization regex can be narrow enough to avoid false positives

## Dependencies

- **Requires:** Phase 1 complete (aar-efficiency-phase1-detectors-20260722) — detectors tested + aggregator wired
- **Blocks:** nothing
- **Non-blocking to:** aar-config-updates, file-editing-protocol-merge