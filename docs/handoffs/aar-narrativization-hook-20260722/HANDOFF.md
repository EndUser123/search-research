---
thread_id: ae827d97-9852-4f51-81d7-e8f3cb490e9d
parent_handoff_path: none
current_session_id: 019f8507-6395-7bc0-87a9-9122e28d68c8
current_terminal_id: console_896ff2fb-4053-4c04-9d6a-74e4
produced_at: 2026-07-22T05:10:29Z
status: open
handoff_type: investigation
accurate_as_of_head: b3fb5225caa69e4759ca6697df715b6b6214259d
---

# HANDOFF — Narrativization hook: enforce "verify before claiming" structurally

## 1. Objective

Extend the existing `Stop_diagnostic_analysis_quality_gate` hook (or add a new Stop hook) to scan assistant responses for causal/behavioral claims that lack nearby verification tool calls. This is the structural enforcement for the "verification receipt rule" — the rule exists in AGENTS.md but is advisory text only; this hook would make it runtime-enforced.

## 2. Status

**OPEN** — not started. This handoff is derived from AAR report session 019f8507 (Pattern P2: narrativization without verification, 3 episodes).

## 3. Producing context

- **Date:** 2026-07-22
- **Session:** `019f8507-6395-7bc0-87a9-9122e28d68c8`
- **AAR report:** `P:/.artifacts/grok-aar/console_console_896ff2fb-4053-4c04-9d6a-74e4/20260721-224551/aar-report.md`

## 4. Read-first list

1. `P:/.grok/AGENTS.md` § "Verification receipt rule (anti-fabrication)" — the rule this hook enforces
2. `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md` — the pattern this prevents
3. `P:/.data/wiki/concepts/writing-discipline-not-enforced.md` — why advisory text alone is insufficient
4. `P:/.claude/hooks/Stop_diagnostic_analysis_quality_gate.py` — the existing hook to extend (or model a new one after)

## 5. Verified facts

- [FACT] The agent made 3 narrativized claims this session without verification receipts: "nobody closes handoffs" (wrong — I closed 2), "drift-endemic problem" (wrong — designed signal), "fabricated evidence" (wrong — other sessions exist). All 3 were corrected by the operator.
- [FACT] The verification-receipt rule exists in `~/.grok/AGENTS.md` but is advisory text. No hook enforces it.
- [FACT] The `Stop_diagnostic_analysis_quality_gate` hook already scans for some quality issues. Extending it is the minimal-sufficient intervention per the AAR's "Minimal sufficient intervention" rule.

## 6. Current state

Nothing done. The wiki concepts are written (`writing-discipline-not-enforced.md`, `analyst-exhibits-pattern-being-analyzed.md`). The rule is in AGENTS.md. The hook does not exist yet.

## 7. Task packets

### TASK-01: Extend Stop hook for narrativization detection

- goal: Add a detector to the Stop hook that flags causal/behavioral claims without nearby verification tool calls.
- in scope: `P:/.claude/hooks/Stop_diagnostic_analysis_quality_gate.py` (extend) or new hook file.
- out of scope: PreToolUse enforcement (too expensive per-call); removing the advisory rule from AGENTS.md (keep as documentation).
- files / anchors: `P:/.claude/hooks/Stop_diagnostic_analysis_quality_gate.py`
- acceptance: When the assistant makes a causal claim ("X is a problem because Y", "nobody does Z", "this is broken"), the hook checks for a nearby tool call (read_file, grep, run_terminal_command) that could have verified the claim. If none found, emit a warning.
- falsifier: The hook fires on legitimate analysis that doesn't need verification (e.g., "the function returns None when input is empty" after reading the code). False positive rate > 15% means the detection regex is too broad.
- verification level required: UNIT_TEST

### TASK-02: Add efficiency detectors to AAR preprocessor

Add deterministic detectors to `~/.grok/skills/aar/__lib/detectors.py`. Each is a pure function `events -> list[Signal]`. These feed the AAR preprocessor's signal pipeline (already wired; just append to `ALL_DETECTORS`).

- goal: Add 5 efficiency-waste detectors that catch the patterns identified by /www research (AgentDiet taxonomy + this session's evidence).
- in scope: `~/.grok/skills/aar/__lib/detectors.py` (add functions + register in `ALL_DETECTORS`)
- out of scope: AAR report format changes (TASK-03); proactive Stop hook (TASK-05); cross-session aggregation (v0.3)
- files / anchors: `~/.grok/skills/aar/__lib/detectors.py`, `~/.grok/skills/aar/__lib/detectors.py:ALL_DETECTORS` (registration tuple at end of file)

**Detectors to implement:**

| Detector | AgentDiet category | Detection method | Threshold | Severity |
|---|---|---|---|---|
| `detect_context_rederivation` | Redundant | Same file path read ≥3 times via `read_file` in one session | 3+ reads | MEDIUM |
| `detect_redundant_verification` | Redundant | Same validation command (pytest, validator script) run ≥3 times without intervening `search_replace` or `write` edits | 3+ runs, 0 edits between | MEDIUM |
| `detect_retry_storm` | Useless | Same tool name + similar args (hash similarity > 0.7) in ≥4 consecutive tool calls | 4+ calls | HIGH |
| `detect_oversized_read` | Useless | `read_file` result > 10KB when a `limit` param was available but not used | result > 10KB, no limit | LOW |
| `detect_expired_context` | Expired | File read early in session (first 1/3 of turns) that is never referenced again after a subsequent read of the same or related file | 1+ reads with no later reference | LOW |

**Important design notes:**
- **Context amplification:** `detect_oversized_read` and `detect_context_rederivation` should weight signals by a cost proxy. Formula: `file_size + (file_size * cache_discount_factor) * remaining_turns` where `cache_discount_factor = 0.1` (models KV cache reads being ~10x cheaper than full processing). This avoids the 10x overestimate of naive `file_size * remaining_turns`. Report the result as `amplified_cost_proxy` in the signal detail.
- **"Related file" definition for `detect_expired_context`:** two files are "related" if they share the same directory OR the same filename stem (before the first `.` or `-`) OR one is referenced by name in the assistant text of the same turn as the other's read. This prevents the implementor from guessing.
- **Quoting loop:** `detect_retry_storm` should catch the specific "PowerShell quoting failure" pattern (same `run_terminal_command` with Python one-liner containing brackets, SyntaxError in result). This was 5 instances this session.
- **All signals carry a falsifier** per the detector design contract in `detectors.py:1-5`.
- **Exception safety:** verify that `ALL_DETECTORS` wraps each call in try/except (per the design contract). If any detector raises, the preprocessor catches, logs the error, and continues with the other detectors. Do NOT assume this — verify by reading the existing wrapper code.

- acceptance: each detector produces signals on the session's transcript; signals are cited with `event_indices`; no false positives on legitimate retries (the falsifier distinguishes).
- falsifier: detectors fire on legitimate non-wasteful patterns (e.g., reading the same file 3x because it changed between reads; running the validator 3x because code was edited between runs).
- verification level required: UNIT_TEST

### TASK-02b: Add efficiency signal aggregator to aggregators.py

- goal: Add a deterministic aggregator that groups efficiency-detector output by tool name and produces the heatmap data structure. Without this, the heatmap table in TASK-03 has no deterministic data source.
- in scope: `~/.grok/skills/aar/__lib/aggregators.py` (add function); the aggregator is called by the preprocessor after all detectors run.
- out of scope: the report rendering (TASK-03 handles that)
- files / anchors: `~/.grok/skills/aar/__lib/aggregators.py`
- acceptance: the aggregator takes the full signal list + event list and produces a structured table: `{tool_name: {total_calls, succeeded, failed, redundant_count, amplified_cost_proxy_sum}}`. The LLM report step reads this structure and renders it as a markdown table.
- falsifier: the aggregator miscounts (e.g., counts a successful retry as redundant) or misses a tool entirely.
- verification level required: UNIT_TEST

**Why this is needed:** The plan review identified a data-flow gap — the detectors produce `Signal` objects, but the heatmap needs aggregate counts per tool. Without an aggregator, the LLM would have to count raw signals, which is unreliable. The aggregator is deterministic and testable.

### TASK-03: Add efficiency report section to AAR SKILL.md

- goal: Add a "Token efficiency findings" section to the AAR report format (Phase 9, §Required report format) that surfaces efficiency signals in fleet-director-triage format.
- in scope: `~/.grok/skills/aar/SKILL.md` (Phase 9 report format section)
- out of scope: detector implementation (TASK-02); proactive hook (TASK-05)
- files / anchors: `~/.grok/skills/aar/SKILL.md` § "Required report format"
- acceptance: the report format includes a "Token efficiency findings" section with: (1) tool-call waste heatmap table, (2) waste by root cause with bullet points + fix recommendations, (3) top 3-5 recommendations.
- falsifier: the report section is so verbose that the operator skips it; or the findings are so generic ("you read files") that they don't lead to actionable fixes.
- verification level required: STATIC_INSPECTION

**Report format specification (from operator feedback):**

```markdown
## Token efficiency findings

### Tool-call waste heatmap
| Tool | Calls | Success | Failed | Redundant | Amplified cost proxy |
|------|-------|---------|--------|-----------|---------------------|
| read_file | 47 | 47 | 0 | 12 | ~180KB |
| run_terminal_command | 39 | 31 | 8 | 5 | ~45KB |
| ...

### Waste by root cause (high confidence)

**[Root cause name] (N instances, ~XK tokens proxy)**
- Turn N: [one-line description]
- Turn M: [one-line description]
- **Fix:** [recommended fix]

### Waste by root cause (lower confidence)

**[Root cause name] (N instances)**
- Turn N: [one-line description]
- (no fix recommended — needs more evidence)

### Top recommendations
1. [highest-leverage fix] — eliminates ~X% of detected waste
2. [second fix]
3. [third fix]
```

### TASK-04: Add secret exposure severity triage to AAR preprocessor

- goal: Add a post-detection step that checks whether a `secret_exposure_in_tool_output` signal actually represents remote exposure (tracked in git, public repo) or local-only exposure (gitignored, private repo). Downgrade local-only to LOW.
- in scope: `~/.grok/skills/aar/SKILL.md` rule 3a (already edited with the triage text); optionally a helper in `detectors.py` or `secret_engine.py` that does the git check.
- out of scope: removing the detector (keep it firing; just triage the severity)
- files / anchors: `~/.grok/skills/aar/SKILL.md` rule 3a (lines ~742-752); `~/.grok/skills/aar/__lib/secret_engine.py` (existing secret detection module)
- acceptance: when a secret_exposure signal fires, the orchestrator runs `git ls-files --error-unmatch <path>` on the containing file and the session transcript dir. If both are gitignored/untracked, severity is downgraded to LOW with the note "local-only exposure."
- falsifier: a real remote exposure (key in a tracked file in a public repo) is downgraded to LOW because the git check has a bug.
- verification level required: UNIT_TEST

### TASK-05: Add proactive efficiency-warning Stop hook

- goal: Add a Stop hook that warns in real-time when efficiency waste patterns are detected during the session (not post-session like the AAR). Sibling to the narrativization hook (TASK-01).
- in scope: new Stop hook file (e.g., `Stop_quality_warnings.py`) or extension of `Stop_diagnostic_analysis_quality_gate.py`
- out of scope: PreToolUse enforcement (too expensive per-call); AAR report changes (TASK-03)
- files / anchors: `P:/.claude/hooks/` (new file); `P:/.claude/settings.json` (registration)
- acceptance: when the agent reads the same file 3+ times, or runs the same validation command 3+ times without intervening edits, or hits the same error pattern 3+ times, the Stop hook emits a `systemMessage` warning: "⚠️ Efficiency: you've read <file> 3 times; consider caching or using grep for specific lines."
- falsifier: the hook fires on legitimate repeated reads (file changed between reads) or creates so much noise that the operator disables it.
- verification level required: LIVE_BEHAVIOR

**Latency design (mandatory):**
- The hook runs on EVERY Stop event. It MUST be O(n) in the scan window, not O(n²) in the full session.
- **Sliding window = last 20 tool calls.** The hook maintains rolling counters per file path / tool name / error pattern. On each Stop, it scans only the window (last 20 calls), updates counters, and checks thresholds.
- **Rolling counter implementation:** a `defaultdict(int)` keyed by `(tool_name, arg_hash)` or `(file_path)` or `(error_signature)`. Increment on each matching event in the window; decrement when an event falls out of the window. Check threshold after each increment.
- **No full-session scan.** The hook must not read or iterate over the entire `chat_history.jsonl`. Only the last 20 tool-call events (parsed from stdin payload).

**Why this is high-leverage:** The AAR documents waste post-session. The Stop hook prevents waste in the current session AND in the 4 other concurrent sessions. Same architecture as the narrativization hook (TASK-01); should be built in the same pass.

## 8. Open decisions

### 8a. Narrativization hook scope — resolved (well-scoped)

This is a well-scoped extension of an existing hook.

### 8b. Efficiency detector scope — expanded after /www research + /tp gap analysis

The scope has grown beyond just the narrativization hook. This handoff now covers **two related work streams** that share the same Stop-hook architecture and deployment path:

1. **Narrativization detection** (original scope, TASK-01)
2. **Efficiency waste detection** (new scope, TASK-02 through TASK-05 below)

Both are Stop hooks that scan recent assistant behavior and emit advisory warnings. Both use the same file structure, test pattern, and deployment path. Building them together is cheaper than building them separately.

### 8c. Efficiency report format — informed by /www research and operator feedback

The AAR report should surface efficiency findings in a format designed for fleet-director triage (scan → approve → fleet executes):

**Format:**
1. **Tool-call waste heatmap** — compact table (tool, calls, success, failed, redundant, % of session). No limit on rows. Operator scans in 5 seconds.
2. **Waste by root cause** — bullet points grouped by domain/root cause. Each item: one-line description + turn reference + token-cost proxy. High-confidence items get a recommended fix. Low-confidence items are noted without fix.
3. **Recommendations** — top 3-5 highest-leverage fixes. These compete for operator attention; too many = none get actioned.

**Design principles (from operator feedback):**
- Surface ALL mechanically-detected waste — no cap. The constraint is not operator cognitive load (solo-director scans fast).
- Group by root cause, not by severity. The operator cares which fix eliminates the most waste.
- Token estimates are rough proxies ("~2000 tokens"), not precise measurements (token counting is unreliable at application level).
- High confidence = bullet with fix. Low confidence = noted without fix.

## 9. Hard constraints

1. Do NOT block (Stop hooks are advisory in Grok Build; warn only).
2. Do NOT add PreToolUse enforcement for this (too expensive per-call).
3. The narrativization detection regex must be narrow enough to avoid false positives on legitimate analysis.
4. Efficiency detectors must be **deterministic** (pure functions in `detectors.py`), not LLM-based. LLM synthesis handles interpretation; detectors handle pattern detection.
5. Efficiency detectors should NOT claim to measure exact token cost — they measure behavioral patterns associated with waste. Frame findings as "redundant reads detected" not "X tokens wasted."
6. The report format must support **fleet-director triage** (scan → approve → execute), not academic analysis. Compact, actionable, grouped by fix.

## 10. Cross-reference couplings

- `~/.grok/AGENTS.md` § "Verification receipt rule" → the rule being enforced by TASK-01
- `P:/.data/wiki/concepts/writing-discipline-not-enforced.md` → the "why" for the narrativization hook
- `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md` → the pattern being caught
- Stanford (Bai et al., 2026, arXiv:2604.22750) → token consumption patterns; input tokens dominate; 1000x multiplier for agentic tasks
- Tokenomics (Salim et al., 2026, arXiv:2601.14470) → 59.4% of tokens in Code Review/verification; input tokens = 53.9% of total
- AgentDiet (Xiao et al., 2025, arXiv:2509.23586) → 3-category waste taxonomy (useless/redundant/expired); 39.9-59.7% reduction proven

## 11. Other outstanding streams

- AAR batch handoff 2: config/doc updates (tool-fallbacks documentation)
- File-editing-protocol merge: `file-editing-protocol-merge-20260722`

## 12. Explicit non-goals

- Do NOT implement PreToolUse enforcement for narrativization or efficiency.
- Do NOT remove the advisory rules from AGENTS.md (keep as documentation alongside the hooks).
- Do NOT build cross-session aggregation in this pass (v0.3 feature; requires AAR-to-AAR comparison).
- Do NOT attempt exact token counting (unreliable at application level per multiple sources).
- Do NOT build LLM-based trajectory reduction in this pass (AgentDiet-style compaction is a separate concern from detection).

## 13. Resumption protocol

1. Read this handoff end-to-end.
2. Read the `/www` research findings (§8c above has the key source citations).
3. Read the existing AAR detectors: `~/.grok/skills/aar/__lib/detectors.py` (to understand the `ALL_DETECTORS` pattern and the `Signal` schema).
4. Read `Stop_diagnostic_analysis_quality_gate.py` to understand the existing Stop hook structure (for TASK-01 and TASK-05).
5. **Recommended build order:** TASK-02 (detectors, deterministic, testable first) → TASK-03 (report format, depends on detector output) → TASK-01 + TASK-05 (Stop hooks, can be built in parallel once the detector patterns are validated) → TASK-04 (secret triage, independent).

## 14. Suggested next invocation

```
/go Implement AAR efficiency detectors and Stop hooks. Follow the handoff at
P:/docs/handoffs/aar-narrativization-hook-20260722/HANDOFF.md.

Build order:
1. TASK-02: Add 5 efficiency detectors to detectors.py (detect_context_rederivation,
   detect_redundant_verification, detect_retry_storm, detect_oversized_read,
   detect_expired_context). Register in ALL_DETECTORS. Run existing test suite.
2. TASK-03: Add "Token efficiency findings" section to AAR SKILL.md report format.
3. TASK-01 + TASK-05: Build the narrativization Stop hook AND the efficiency-warning
   Stop hook in the same pass (same architecture, same test pattern).
4. TASK-04: Add secret exposure severity triage (git check for local-only vs remote).
```

## 15. Last user message (verbatim)

> first update the handoff

## 16. Epistemic labels

- [FACT] 3 narrativization incidents this session (AAR P2)
- [FACT] Verification-receipt rule exists in AGENTS.md as advisory text
- [FACT] This session had: 47 read_file calls (12 redundant), 6 validator runs (4 without intervening edits), 5 PowerShell quoting failures, 1 oversized config.toml read (~10KB when line 92 was needed)
- [FACT] Stanford (Bai et al., 2026): agentic tasks consume 1000x more tokens than code chat; input tokens dominate; higher token usage does not improve accuracy
- [FACT] Tokenomics (Salim et al., 2026): 59.4% of tokens in Code Review; input = 53.9% of total
- [FACT] AgentDiet (Xiao et al., 2025): 3-category waste taxonomy (useless/redundant/expired); 39.9-59.7% reduction without performance loss
- [INFERENCE] Extending the existing Stop hook is the minimal-sufficient intervention for narrativization
- [INFERENCE] The proactive efficiency Stop hook (TASK-05) is higher-leverage than the post-session AAR report (TASK-03) because it prevents waste in the current session AND the 4 concurrent sessions
- [INFERENCE] Token counting is unreliable at application level (per multiple vendor sources); behavioral pattern proxies are the right approach
- [UNKNOWN] Whether the narrativization detection regex can be narrow enough to avoid false positives
- [UNKNOWN] Whether `detect_expired_context` can reliably detect "file read that is never referenced again" without semantic analysis

## Dependencies

- **Requires:** nothing — can start immediately
- **Blocks:** nothing
- **Non-blocking to:** AAR batch handoff 2 (config/doc updates)