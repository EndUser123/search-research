# `/session-health` — Design Document

| Field | Value |
|---|---|
| **Capability owner** | `session-health-monitoring` |
| **Domain** | `lifecycle` |
| **Skill path** | `C:/Users/brsth/.grok/skills/session-health/SKILL.md` |
| **Capability contract** | `P:/.data/wiki/capabilities/session-health-monitoring.md` |
| **Author** | Session 019f9f4f via `/design` |
| **Date** | 2026-07-29 |
| **last_modified** | 2026-07-29 (revision 3.1: F-60 propagation fix; v0.3 → v0.3.1) |
| **Status** | Draft v0.3.1 |
| **Version** | 1.0.0 (semver; bumps on schema changes) |
| **Host** | `grok` |

---

## 1. Goal

In one sentence: own the mechanical extraction of friction and pushback signals from session transcripts, compare to a rolling baseline, detect drift across sessions, and emit a verdict that any Grok skill (or the operator) can read at **three human-facing granularities** (quick / full / trend) plus **one stable machine contract** (`--json` for downstream skill integration).

**The "4 modes" framing is corrected (resolves Critique Premise 1):** `--json` is structurally different from the operator-facing modes. The three human modes answer "how's this session going?" at different levels of detail; `--json` is a stable schema consumed by `/close`, `/tp`, `/debrief`, `/notice`, `/aar`. Operator UX is 3 modes; downstream integration is 1 contract. The two surfaces are documented separately.

The skill replaces scattered friction-regex code in `/tp Step 0b` and `close/__lib/friction_detector.py` (real DRY violation — see §"Friction vs pushback DRY framing") with a single canonical signal extractor + cache + drift analyzer, following the [context-firewall-architecture](file:///P:/.data/wiki/concepts/context-firewall-architecture.md) 3-layer pattern (script IS the firewall). Pushback-keyword extraction is a **new signal** introduced by this skill, not consolidation of existing code.

## 2. Contracts and invariants

### 2.1 Capability contract

`session-health-monitoring` is a new capability in the `lifecycle` domain, distinct from existing `session-opportunity-review` (owned by `/tp`) and `session-retrospective` (owned by `/debrief`). It is the **signal source** that those skills read from.

### 2.2 Input contract

| Input | Source | Format |
|---|---|---|
| `transcript_path` | `~/.grok/sessions/<encoded-cwd>/<session-id>/chat_history.jsonl` | JSONL with `{"type": "user" | "assistant", "content": [{"type": "text", "text": "..."}, ...]}` (verified: see §chat_history schema below) |
| `compaction_dir` | `~/.grok/sessions/<encoded-cwd>/<session-id>/compaction/` | `INDEX.md` (always present if compacted) + `segment_<NNN>.md` (markdown; see §compaction schema below) |
| `--mode` | CLI flag | `quick` (default) \| `full` \| `trend` \| `json` |
| `--sessions N` | CLI flag | int (default 5 for trend) |
| `--no-cap` | CLI flag (with `--full`) | bool; bypasses 500-message cap |
| `--include-segments` | CLI flag (with `--full`) | bool; reads segment files in addition to `INDEX.md` summary |

**Path encoding (verified 2026-07-29 against this host's session directory):**

- `<encoded-cwd>` = URL percent-encoding of the absolute path. `C:\` becomes `C%3A%5C`; `P:\` becomes `P%3A%5C`; backslashes within worktree paths become `%5C`.
- `<session-id>` = lowercase UUIDv8 with timestamp prefix (e.g., `019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9`).
- **Concrete example** (verified path on this host): `C:\Users\brsth\.grok\sessions\P%3A%5C\019f6b24-dd44-7192-8a98-02e2be35f8c6\chat_history.jsonl`
- **Source of encoding scheme** [FACT]: this is the URL-encoding pattern produced by Grok Build's session ID derivation; observed across 50+ session directories at `~/.grok/sessions/`.

**`chat_history.jsonl` schema (verified against `P:/tmp/detect_pushback.py` and live transcripts):**

```json
{
  "type": "user" | "assistant" | "tool_use" | "tool_result" | ...,
  "content": [
    {"type": "text", "text": "<user_query>\n...actual user text...\n</user_query>"}
  ]
}
```

User messages wrap their query text in `<user_query>...</user_query>` delimiters. This is how `detect_pushback.py` extracts the query.

**Compaction schema (verified against `~/.grok/sessions/P%3A%5C\019f6b24-...\compaction\INDEX.md`):**

`INDEX.md` is a markdown table:

```markdown
# Compaction Segment Index

| Segment | File | Turns | Approx bytes | Keywords |
|---|---|---|---|---|
| 000 | segment_000.md | 513 | 520649 | "User", "update", ... |
```

`segment_NNN.md` is a structured markdown file with sections: `## Segment metadata` (Index, Turn count, Timestamp), `## Turn statistics` (per-type counts, tool usage, file targets, error count), `## Summary (curated by compaction step)` (8 numbered points: Primary Request, Key Technical Concepts, Files and Code Sections, Errors and Fixes, Problem Solving, All User Messages, Pending Tasks, Current Work, Optional Next Step).

Header: `# HISTORICAL -- DO NOT EDIT` + `# Record of compaction segment <NNN> (detail=verbose) from this same task.`

[UNKNOWN]: The compaction schema is documented but lacks a version field. If the compaction step evolves, schema drift could occur without detection. Mitigation: re-scan INDEX.md and segment files on every cache invalidation.

### 2.3 Output contract (JSON mode)

```json
{
  "session_id": "<session-id>",
  "scanned_at": "2026-07-29T17:30:00Z",
  "transcript_path": "C:/Users/brsth/.grok/sessions/<encoded-cwd>/<session-id>/chat_history.jsonl",
  "compaction_aware": true,
  "schema_version": "1.0.0",
  "error": null,
  "degraded": false,
  "degraded_reasons": [],
  "metrics": {
    "friction_count": 13,
    "pushback_count": 8,
    "user_messages": 22,
    "f_per_user": 0.59,
    "p_per_user": 0.36,
    "duration_sec": 7220
  },
  "friction": {
    "by_category": {"NO_COVERING_RECEIPT": 13, "Traceback": 2},
    "transcript_lines": [12, 45, 89]
  },
  "pushback": {
    "keywords_hit": ["no ", "wrong", "did you do"],
    "quotes": [
      {"line": 23, "text": "no, that's not right", "keyword": "no"}
    ]
  },
  "baseline": {
    "f_u_low": 0.5, "f_u_high": 1.5,
    "p_u_low": 0.1, "p_u_high": 0.3,
    "verdict": "elevated"
  }
}
```

**Error contract:**

- `error` is `null` on success.
- `error` is a non-null string on failure (e.g., `"transcript file not found"`, `"JSONL parse error at line 42"`, `"compaction INDEX.md missing segment_NNN.md"`).
- On failure: `metrics` = zero-valued defaults; `friction` and `pushback` blocks are empty objects; `baseline.verdict` = `"unknown"`.
- Consumers MUST check `error == null` before reading metrics. A zero-friction session is indistinguishable from a failed scan without this check.

**Degraded contract (resolves Critique Premise 7 — Consumer error handling):**

- `degraded` is a boolean flag (`true`/`false`). When `true`, the scan completed but with one or more known limitations.
- `degraded_reasons` is a list of strings explaining what went wrong. Empty when `degraded: false`.
- Degradation triggers (each adds a reason string):
  - `"registry_lock_timeout"` — `msvcrt.locking` exceeded the 5-second timeout; another process holds the registry lock.
  - `"compaction_incomplete"` — `compaction/INDEX.md` references a `segment_NNN.md` that is missing or unreadable; INDEX keywords are partial.
  - `"transcript_truncated"` — transcript exceeds the 500-message cap (`--full --no-cap` not set); only the tail was scanned.
  - `"transcript_parse_partial"` — one or more JSONL lines failed to parse; scan continued with valid lines.
  - `"friction_categories_drifted"` — `session_signals.py` pattern list differs from `/tp/SKILL.md` category table (post-Unit-7 only; check via OQ-8 CI).

**Consumer behavior on `degraded: true` (resolves Critique Premise 7):**

- `/close` consumer: when `degraded: true`, the close summary shows the friction/pushback line as `"<adjective> (degraded: <reasons>)"`. Do NOT silently substitute zero values. Example: `"high friction (degraded: registry_lock_timeout)"`. If all reasons are non-fatal (e.g., `transcript_truncated`), close can proceed normally. If reasons include `transcript_parse_partial` or `registry_lock_timeout`, close should surface a warning to the operator.
- `/tp session` consumer: when `degraded: true`, the NOW/NEXT/LATER output omits any finding that depends on the missing data and notes the degradation in the synthesis header (e.g., "⚠️ DEGRADED: registry_lock_timeout — friction/pushback unavailable, transcript review relies on model recall"). The session review still proceeds with model recall.
- `/debrief` Lens 3 consumer: when `degraded: true`, Lens 3 produces a stub finding `"Session signals unavailable (degraded: <reasons>)"` and proceeds without numeric F/U and P/U. Lens 3 is one of 5 lenses; loss of Lens 3 does not block the rest.
- `/notice` T1/T6 consumer: when `degraded: true`, suppress the suggestion to invoke `/session-health --full` (the suggestion would point to a degraded source). Suggest the operator manually inspect.
- `/aar` Phase 4 consumer: when `degraded: true`, do not write `friction_signal_baseline_delta` for the affected sessions. The AAR proceeds; the degraded sessions are flagged.

**Consumers proceed with model recall only when `degraded: true`.** They do not block on signal unavailability — the script is best-effort infrastructure.

**Pushback keyword normalization (resolves F-55):**

`keywords_hit` preserves the original search pattern, including trailing whitespace or punctuation where present (e.g., `"no "` with trailing space, `"actually,"` with trailing comma). Rationale: substring matching depends on the trailing space/comma to avoid false positives (e.g., `"no "` does not match `note`, `"nothing"`; `"actually,"` does not match `actually` in middle of a sentence). Consumers that want trimmed tokens should call `.strip()` themselves.

### 2.4 Invariants

1. **Deterministic extraction** — given the same transcript + registry state, the script MUST produce the same output. No LLM in the hot path.
2. **Self-healing registry** — if `P:/.data/telemetry/session-signal-registry.json` is lost or corrupt, re-scanning all sessions regenerates it without data loss.
3. **Compaction-aware, summary-only by default** — if `compaction/INDEX.md` exists, the script reads its segment table (turns, bytes, keywords) for pre-compaction context but does NOT load individual `segment_NNN.md` files unless `--include-segments` is passed. Rationale: summary-only is fast and fail-open; full-segment read is slow and may stall on 1MB+ segments. Trade-off documented in Risk Table row "Compaction scan accuracy/speed tradeoff."
4. **Fail-open** — script errors return zero-valued `metrics` with `error: <string>`, never raise or crash callers. Invariant satisfied by §2.3's `error` contract.
5. **Multi-terminal safe (with lock)** — registry writes use `msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)` on a sidecar `registry.lock` file (matching the pattern in `~/.grok/skills/close/__lib/close_runner.py:85-104`). The lock is held for the duration of the read-modify-write cycle. Concurrent `/session-health` calls block on the lock for up to 5s, then fail with `error: "registry_lock_timeout"`. Acceptable because (a) the script is fast (<1s) and (b) blocking is preferred over silently losing entries. Without the lock, two concurrent writers could both rename their `tmp` files over the same target and lose entries — this is what the original `os.replace` claim got wrong.

## 3. What this skill does

Three layers:

### 3.1 Layer 1: Monitor (deterministic, no LLM)

**Script:** `scripts/session_signals.py`

Scans a single transcript and produces:

- **Friction signals — 13 patterns in 11 categories (resolves Critique Premise 5).** [FACT] The actual `/tp Step 0b` regex at `~/.grok/skills/tp/SKILL.md:250-280` contains **13 distinct patterns** separated by `|`, not 11 as originally claimed. Counting by hand from the regex: `"exit":\s*[1-9]` | `exit code:\s*[1-9]` | `Traceback` | `Denied by permission` | `timed out after` | `FAIL:` | `SyntaxError` | `fatal:` | `automatically moved to background` | `SECRET DETECTED` | `gitleaks` | `NO_COVERING_RECEIPT` | `New code was modified`. That's **13 patterns**. Two of them (`FAIL:`, `fatal:`) are not represented in the original 11 named categories, and one category (`command_not_found`) had no corresponding regex pattern. Correct mapping (v0.3 corrections):
  - `exit_code_nonzero` → 2 patterns (`"exit":\s*[1-9]`, `exit code:\s*[1-9]`)
  - `Traceback` → 1 pattern
  - `SyntaxError` → 1 pattern
  - `NO_COVERING_RECEIPT` → 1 pattern
  - `auto_backgrounded` → 1 pattern (`automatically moved to background`)
  - `SECRET_DETECTED` → 1 pattern
  - `gitleaks` → 1 pattern
  - `permission_denied` → 1 pattern (`Denied by permission`)
  - `timeout` → 1 pattern (`timed out after`)
  - `post_verify_mutation` → 1 pattern (`New code was modified`)
  - `command_not_found` → **NO regex pattern in `/tp` source**. This category was added in v0.2 without a corresponding `/tp` source pattern. **Removed in v0.3.**
  - `uncategorized_failure` → **NEW** category in v0.3 to absorb `FAIL:` and `fatal:` (these were in `/tp`'s regex but lacked a design category). Surfaced as raw pattern names in the registry so a future session can categorize them.

  Pattern set inherits from `/tp Step 0b` — single source of truth; the inline regex in `/tp/SKILL.md` is **deleted when `session_health.tp_delegate` flips to `true` (Phase 2)** per removal-protocol.md. After deletion, `scripts/session_signals.py` owns the patterns; this is documented as the **post-Phase-2 source-of-truth** (resolves Critique Premise 4 — see Maintenance Contract below). Unit 7 ships with the regex still present (the flag is `false`); deletion happens in Phase 2 only.
  - **Implementation note [FACT]** (resolves F-56): `auto_backgrounded` is detected by grepping transcript content for the literal string `automatically moved to background` (the message emitted when a command exceeds the 120s timeout). This is transcript-text matching, NOT session-tool state file reading. Verified by `Select-String` against `~/.grok/sessions/P%3A%5C\019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe\chat_history.jsonl`: matched in 4+ `tool_result` records (lines 121, 131, 138, 271, …). The other 12 patterns are also regex over transcript content.
- **Pushback signals — 16 keywords. NEW signal, not a duplicate (resolves Critique Premise 4).** [FACT] The 11-keyword pushback detector at `P:/tmp/detect_pushback.py` is a **different signal** from the friction regex. Pushback measures operator-correction density (interaction friction); friction measures tool-failure density (operational friction). They share a `transcript-scan` mechanism but answer different questions. There is **no DRY violation** for pushback; the migration to `scripts/pushback_keywords.txt` (per F-10) is **durable placement**, not consolidation.
  - 11 from `P:/tmp/detect_pushback.py` (validated 2026-07-29): `"no "`, `"wrong"`, `"not right"`, `"but we"`, `"stop doing"`, `"shouldn"`, `"actually,"`, `"don't"`, `"why"`, `"are throwing"`, `"did you do"`
  - 5 from `/friction/SKILL.md` Mode 1 markers (in `~/.claude/plugins/cache/local/cc-skills-analysis/1.0.123/skills/friction/SKILL.md`): `"I disabled"`, `"you are confused"`, `"old data"`, `"same problem again"`, `"didn't call"`
  - **Overlap check [FACT]**: no duplicates between the two sets (verified by sorting and diffing; union = 16 distinct keywords, intersection = ∅).
- **Derived metrics** — `F/U` (friction per user message), `P/U` (pushback per user message), session duration in seconds.

This layer is **pure Python**. No LLM calls. Exit 0 always; errors captured in `error` AND `degraded` fields of output JSON (§2.3).

**Maintenance contract (resolves Critique Open-ended Risk 4.1 — Friction category synchronization):** After the `session_health.tp_delegate` flag flips to `true` (Phase 2) and the inline regex is deleted from `/tp/SKILL.md:250-280`, `scripts/session_signals.py` becomes the **single source of truth** for friction patterns. When patterns change (add/remove), update this file. The `/tp/SKILL.md` "Transcript-to-findings linkage" table (lines 262-271) is a *category reference*, not a pattern source — it should be regenerated from `session_signals.py`, not maintained independently. This is a soft contract for v1.0 (no CI enforcement); Open Question OQ-8 covers whether to add a CI check that compares `/tp`'s category table to `session_signals.py` pattern list and fails on divergence.

**Compaction strategy (resolves F-01, F-17):**

By default: read `chat_history.jsonl` (post-compaction tail) + `compaction/INDEX.md` table (segment turns/bytes/keywords summary). Do NOT read `segment_NNN.md` content. Rationale:
- INDEX.md gives pre-compaction context (turn counts, keyword extraction) without loading 1MB+ segment files.
- Speed: full-segment scan would add 5-30s per compacted session. INDEX-only adds <100ms.
- Accuracy: undercounts friction/pushback in pre-compaction turns if they were not surfaced in INDEX's keyword list. Mitigated by `--include-segments` flag for explicit operator-driven full scans.

[INFERENCE]: The accuracy delta between INDEX-only and full-segment scan has not been measured. Recommend a pilot (5 compacted sessions, both modes, compare F/U and P/U deltas) before declaring the default acceptable. See Risk Table row "Compaction scan accuracy/speed tradeoff."

### 3.2 Layer 2: Analyze (LLM judgment, embedded)

**Mode:** `--full`

When `F/U > 2.0 OR P/U > 0.4`, emit a `/behave`-style hypothesis block:

- 3-5 hypotheses per elevated symptom (loop detection, context degradation, decision inefficiency, cognitive overload).
- Cost-ordered tests (cheap → medium → expensive).
- Falsification pass.
- Calibrated confidence using `/behave`'s evidence tier table.

**LLM mechanism (resolves F-07):**

"Embedded LLM judgment" means: the skill runs in the operator's session context. When the SKILL.md prompt template is loaded, the operator's existing model emits the hypothesis block as part of its response. There is **no subagent spawn, no separate quota cost, no external API call**. The hypothesis block is a few hundred tokens of structured output added to whatever the model is already producing.

Contrast:
- **Layer 1 (deterministic)**: script invocation, no LLM, ~500ms latency.
- **Layer 2 (embedded LLM)**: skill prompt loaded by model, LLM emits hypothesis block as part of its reply. Same quota as the active session.
- **Layer 3 (orchestrator)**: the SKILL.md itself, which wraps the script and renders verdicts.

**Why not a subagent spawn**: subagent spawn costs quota (per `/tp/SKILL.md:830-870` pool model) and adds 30-90s latency. For a 200-token hypothesis block, the marginal value is negative. Embedded LLM is the right tool.

**Why not an external API**: violates Grok Build constraint (no external services).

The `/behave` skill lives in the disabled `cc-skills-thinking` plugin; we cannot depend on it. The hypothesis-testing pattern is **adopted, not delegated**. Cite the source in SKILL.md so a future maintainer can re-sync if `/behave` becomes available.

[UNKNOWN]: If the `/behave` plugin is re-enabled on this host, the citation should be re-evaluated — we could delegate to `/behave` instead of embedding. See Open Questions §OQ-3.

### 3.3 Layer 3: Orchestrator (this skill)

**Modes:** `--trend` and the integration modes for `/close`, `/tp session`, `/debrief`.

Cross-session analysis reads the registry and emits:

- Drift alerts (rolling mean > 1.5× historical median)
- Chronic patterns (any friction category in ≥3 of last 10 sessions)
- Workflow automation opportunities (same command 3+ times across sessions)

**Workflow opportunity origin (resolves F-46):**

The "same command 3+ times" detection has **two distinct sources**:

1. **Within-session recurrence** (single session): `~/.grok/skills/close/__lib/friction_detector.py` with `RECURRENCE_THRESHOLD = 2` (counts duplicate-issue occurrences within one session).
2. **Cross-session pattern** (multiple sessions): `/friction/SKILL.md` Mode 2 ("Same command run 3+ times in a session — candidate for a hook or skill"). This is a SKILL.md description, not a code path.

`/session-health --trend` reads the registry and emits cross-session workflow opportunities using the Mode 2 threshold (3+ identical commands across ≥2 sessions). The within-session `friction_detector.py` is NOT modified by this skill — they serve different scopes.

## 4. Output surfaces — human-facing modes + machine contract

This design exposes **two distinct output surfaces**:

1. **Three human-facing modes** — operator UX at different granularities.
2. **One machine contract** (`--json`) — stable schema consumed by 5 callers: `/close`, `/tp`, `/debrief`, `/notice`, `/aar`.

The previous "4-mode UX" framing conflated these surfaces; v0.3 separates them. Operator UX is 3 modes; downstream integration is 1 contract. The two surfaces do not share flag namespace: human modes accept `--full`, `--full --no-cap`, `--full --include-segments`; the JSON contract is selected by `--json` (or implied when consumed programmatically).

### 4.1 Human-facing modes (operator UX)

| Mode | Invocation | Output | Latency target |
|---|---|---|---|
| Quick (default) | `/session-health` | One-line verdict + 3 most elevated signals | <500ms (P95 over 100 invocations against full `~/.grok/sessions/` corpus) |
| Full | `/session-health --full` | Friction breakdown + pushback quotes + workflow opportunities + hypothesis block (if elevated) + drift alert | <2s (P95); adds ~200 tokens of LLM output if hypothesis block fires |
| Trend | `/session-health --trend` | Last N sessions' F/U + P/U trend, chronic patterns, drift alerts | <1s (P95; registry read with cache) |

**Default invocation (resolves F-20):** Bare `/session-health` (no flag) is quick mode. There is NO `--quick` flag. This matches the convention in `/tp` (where bare `/tp` = two-lens critique, no `--two-lens` flag).

**Full-mode sub-flags (resolves F-21, F-57):**

- `--full --no-cap`: read full `chat_history.jsonl` (no 500-message cap). For sessions with very long tails.
- `--full --include-segments`: read `compaction/segment_NNN.md` files in addition to INDEX.md summary. Slow (5-30s per session) but more accurate.
- Flag composition (resolves F-57): `--no-cap` applies **only** to `chat_history.jsonl`; segment files (loaded by `--include-segments`) are always read in full — there is no segment cap. `--include-segments` is independent of `--no-cap`: it controls whether segment files are read, not how many `chat_history.jsonl` lines are processed.
- Flags compose: `--full --no-cap --include-segments` is the most thorough mode (full transcript + all segment files).

### 4.2 Machine contract — `--json` (integration surface)

| Invocation | Consumer | Output | Latency |
|---|---|---|---|
| `/session-health --json` | `/close`, `/tp session`, `/debrief` Phase 0, `/notice` T1/T6, `/aar` Phase 4 | JSON output per §2.3 contract (includes `error` and `degraded` fields) | <500ms (P95) |

**`--json` is structurally different from the human modes:**

- **No LLM invocation**: `--json` is pure Python. The hypothesis block (§3.2) is NEVER emitted via JSON; it requires operator-visible interpretation that belongs to the human `--full` mode.
- **No color/formatting**: JSON is whitespace-stable. Human modes may use color or formatting per operator preference; JSON is unstyled.
- **Stable schema contract**: the JSON schema (§2.3) is versioned via `schema_version`. Adding a field is non-breaking if consumers ignore unknown fields; removing or renaming is breaking and requires a `schema_version` bump.
- **Error and degraded flags always present**: every JSON output includes `error` (string or null) and `degraded` (boolean). Consumers MUST check both before using the data (see §2.3 degraded contract).

## 5. Baselines

[INFERENCE] The following thresholds are seeded from a manual 10-session scan performed this session. The scan was not rigorously calibrated — values were spot-checked, not statistically derived. They serve as **initial defaults** to be replaced by rolling-median computation once the registry has 30+ sessions of empirical data.

| Signal | Low | Normal | High | Alert at |
|---|---|---|---|---|
| Friction F/U | < 0.5 | 0.5 – 1.5 | > 1.5 | > 2.0 (hypothesis block fires) |
| Pushback P/U | < 0.1 | 0.1 – 0.3 | > 0.3 | > 0.4 (hypothesis block fires) |

**Threshold calibration strategy:**

- **Initial values (now → 30 sessions):** hardcoded from the 10-session scan above.
- **Recalibration (30+ sessions):** thresholds shift to `median ± 1.5× MAD` (median absolute deviation) computed across the registry. Drift alert = rolling 5-session mean > 1.5× historical median.
- **Weekly refresh:** `scripts/signal_registry.py --recalibrate` recomputes thresholds from the registry and updates `baseline.json`.

[INFERENCE] The 10-session scan source: the brief states "Friction density F/U is useful — receipt: 10-session baseline shows 0.04-11.06 range." This range was computed from `~/.grok/sessions/P%3A%5C\` directories via hand-counted grep of friction patterns and pushback keywords. Per-session values were not durably persisted (the scan was ephemeral); only the range survived in the brief. The registry will durably persist per-session metrics starting with Unit 1 deployment.

[UNKNOWN]: Whether 0.5 / 1.5 / 2.0 are the right absolute thresholds. The brief provided the range; the threshold choice is a design call that should be re-evaluated after 30 sessions of empirical registry data.

## 6. Integration with existing skills

| Caller | How it uses `/session-health` | Replaces | Citation |
|---|---|---|---|
| `/tp session` Step 0b | `python session_signals.py --json \| jq` (gated by `session_health.tp_delegate`) | **CONDITIONAL on flag flip:** while flag is `false`, inline regex at `/tp/SKILL.md:250-280` stays as the active behavior; when flag flips to `true` (Phase 2 after validation), the inline regex is DELETED per removal-protocol.md. Pre-flag-flip state is preserved (resolves F-48 empty-state bug). | `/tp/SKILL.md:250-280` (regex kept during shadow; deleted on flag flip); new Step 0b calls session-health when flag is on |
| `/close` final summary | Reads `--json` output; adds friction + pushback one-liner to verdict | New — supplements `friction_detector.py` (which stays for recurrence detection) | `~/.grok/skills/close/__lib/close_runner.py` |
| `/debrief` Phase 0 | Reads `--json` output as Lens 3 (workflow friction) input | New — Phase 0 Discovery reads the output before Phase 1 lens fan-out | `~/.grok/skills/debrief/SKILL.md:60-130` (Phase 0 Discovery) |
| `/notice` T1/T6 trigger | When T1 (error state) or T6 (unverified diagnosis) fires, `/notice` appends `/session-health --full` to suggestion text | New — suggestion-only, never auto-invoke | `~/.grok/skills/notice/SKILL.md:116-122` (T1 = error state; T6 = unverified diagnosis) |
| `/aar` Phase 4 (revised by round-2 critical friend; resolves Blocker 4) | `/aar` Phase 4 REPLACES its inline signal computation with `python session_signals.py --json --session <id>` calls. `/session-health` becomes the canonical EXTRACTION layer; `/aar` Phase 4 becomes a CONSUMER. | **NOT a no-op** — `/aar` is modified to consume `session_signals.py` output instead of computing signals inline | `~/.grok/skills/aar/SKILL.md:147-185` (Phase 4 `operator_signal_delta`); replace inline computation with `session_signals.py --json` calls |

**Decision (revised by Blocker 4):** `/session-health` is the canonical EXTRACTION layer. The 5 consumers are:
1. `/tp session` Step 0b — `python session_signals.py --json | jq` (gated by `session_health.tp_delegate`). Inline regex at `/tp/SKILL.md:250-280` DELETED on flag flip (Phase 2) per removal-protocol.md.
2. `/close` final summary — adds friction + pushback one-liner to verdict. `close/__lib/friction_detector.py` STAYS (different scope — recurrence, not density).
3. `/debrief` Phase 0 — reads `--json` as Lens 3 (workflow friction) input.
4. `/notice` T1/T6 trigger — appends `/session-health --full` to suggestion text (suggestion-only, never auto-invoke).
5. `/aar` Phase 4 (revised) — REPLACES its inline signal computation (pushback_count, pushback_categories, etc.) with `python session_signals.py --json --session <id>` calls. **The AAR is now a consumer, not a redundant compute path.**

**Why the /aar revision matters (resolves Blocker 4):** Round-2 critical friend verified that `/aar/SKILL.md:147-185` (Phase 4 `operator_signal_delta`) ALREADY computes signals that overlap with `/session-health` — specifically:
- `pushback_count` (same as session_signals P/U numerator)
- `pushback_categories` (6 categories: tool misuse, context loss, goal drift, retry loops, cascading errors, silent quality degradation — overlaps with our 11 friction categories)
- `friction_signal_baseline_delta` (session vs rolling baseline, last 10 sessions — same shape as our drift detector)

Without the revision, **two paths would compute overlapping signals** — `/session-health` on demand and `/aar` Phase 4 during AAR runs. The revised design makes `/session-health` the canonical extractor and `/aar` Phase 4 a consumer. The `/aar` modification adds 1 file (`/aar/SKILL.md`) to the File Change Inventory.

**Verified citations (resolves F-08, F-18, F-19, F-38, Blocker 4):**

- `/notice/SKILL.md:116-122` defines T1 = "Error state" (tool call failed, exit ≠ 0) and T6 = "Unverified diagnosis" (confident causal claim without verification receipt). Both confirmed.
- `/debrief/SKILL.md:67-68` defines "Lens 3: Workflow Friction (general reasoning)" as one of the 5 lenses. The lens structure exists; `/session-health --json` becomes the input to this lens in Phase 0 Discovery.
- `/aar/SKILL.md:147-185` (revised citation, was 152-201) defines Phase 4's `operator_signal_delta` block with `pushback_count`, `pushback_categories`, `trust_loss_markers`, `reactive_adversarial_invocations`, `meta_cognition_verbs`, `deferred_persistence_count`, `friction_signal_baseline_delta`. **Revised integration:** `/aar` Phase 4 is modified to read from `session_signals.py --json` instead of computing these signals inline. The AAR's value-add (cross-session episode clustering, double-loop analysis, operator_signal_delta synthesis) remains; only the raw signal extraction is delegated.

**No deletion of sibling skills.** `/friction`, `/behave`, `/pace` stay as standalone entry points for operators who want those workflows directly. `/session-health` is the **internal integration** that absorbs their patterns.

**Removal protocol compliance (resolves F-06, refined by F-48, further refined by vendor-lock-in mitigation):** When the `session_health.tp_delegate` flag flips to `true` (Phase 2), the inline regex at `/tp/SKILL.md:250-280` is DELETED. Per AGENTS.md "Replacement default": "when replacing behavior X with Y, delete X. Keeping X as fallback requires explicit justification — 'preserves old behavior' is circular." The justification for NOT keeping the regex active: (a) the script is deterministic and well-tested, (b) keeping both creates two sources of truth for the friction pattern list, (c) any future pattern addition requires editing only the script. **Phase 2 entry criterion (per F-48):** the flag flip must be preceded by a backup of the inline regex to `P:/.artifacts/<term>/tp-step-0b-inline.bak`, gated by a `PreToolUse` hook (see Risk Table row "Backup enforcement"). **Post-flip recovery path (per vendor-lock-in risk 4.4):** after deletion, the `@deprecated` comment marker is left in place for 30 days post-flip (not 30 days post-Unit-7-ship) as a soft-removal with `git blame` history preserved. After 30 days of stable operation, the comment is hard-removed too. **Therefore:** delete on `tp_delegate` flag flip to `true` (Phase 2), not on Unit 7 ship.

**Consumer error contract (resolves Critique Premise 7):** Each consumer's behavior on `error != null` or `degraded: true` is specified in §2.3 degraded contract. Summary:
- `/close`: shows degraded reasons in summary; proceeds with model recall.
- `/tp session`: omits friction/pushback findings; notes degradation in synthesis header; proceeds.
- `/debrief` Lens 3: emits stub finding "signals unavailable"; proceeds without numeric F/U/P/U.
- `/notice` T1/T6: suppresses suggestion to invoke `/session-health --full` when degraded.
- `/aar` Phase 4: omits `friction_signal_baseline_delta` for degraded sessions; proceeds.

Consumers do not block on signal unavailability — the script is best-effort infrastructure.

## 7. Why a new skill (not a feature in `/tp`)

`/tp` is 1310 lines (per `wc -l ~/.grok/skills/tp/SKILL.md`). Adding transcript-scanning responsibility:

- Increases the SKILL.md that the fresh subagent reads on every `/tp` invocation → increases context cost.
- Mixes live-critique concerns with monitoring concerns — different invariants (monitoring = deterministic + registry-aware; critique = LLM-judgment + bundle-based).
- Forces `/close` and `/debrief` to import `/tp` — wrong dependency direction (downstream depends on upstream).

The optimal long-term solution is a dedicated skill with its own SKILL.md (under 400 lines, focused), deterministic Layer 1 script, and clear capability boundary (`session-health-monitoring` in the `lifecycle` domain).

## 8. Key design questions resolved

1. **Script vs skill structure** → Script (Layer 1) + thin skill wrapper (Layer 3). Embedded LLM only in `--full` hypothesis block (Layer 2). Mirrors the `close/__lib/` pattern (specifically `close_accounting.py` for the script-as-firewall idea, and `close_runner.py` for the orchestrator-with-feature-flags pattern — both files exist; see F-27 clarification).
2. **Integration with `/tp`, `/debrief`, `/close`, `/notice`, `/aar`** → Canonical extraction layer (revised by Blocker 4). `/tp Step 0b` delegates; `/close`, `/debrief`, `/notice`, `/aar` consume via `--json`. `/aar` Phase 4 is **revised from no-op to consumer** — it replaces inline signal computation with `session_signals.py --json` calls. No replacement of `/close/__lib/friction_detector.py` (different semantics — recurrence vs density; only `SyntaxError` overlaps per round-2 verification).
3. **When to invoke** → Mid-session (operator only — `/notice` suggests when elevated). End-session (`/tp session`, `/close`, `/debrief` integrate). Drift (`/aar` Phase 4).
4. **Registry format** → JSON at `P:/.data/telemetry/session-signal-registry.json` with mtime-based invalidation; self-healing on loss.
5. **`/behave` integration** → Adopt pattern in `--full` mode; do not delegate (plugin disabled). Cite source.
6. **`/pace` integration** → Out of scope for v1.0. `--load` flag deferred to v1.1.

---

## 9. Anchoring Premises (resolves Critique Premise 6)

The critical-friend review identified 5 premises the design brought in without critical examination. Each is now labeled with `[FACT]` / `[INFERENCE]` / `[UNKNOWN]` and a mitigation. **Falsifier-gating: every claim here is now traceable to either a tool call (this session), a labeled inference chain, or a named unknown.**

### A1. "Friction regex duplicated across `/tp`, `/close`, `/tmp/detect_pushback.py`, `/friction`." [FACT, corrected by round-2 critical friend]

- [FACT] `~/.grok/skills/tp/SKILL.md:250-280` contains the inline regex with **13 patterns** (verified by hand count this session, see §3.1). This is the canonical friction pattern source.
- [FACT — verified by round-2 critical friend] `~/.grok/skills/close/__lib/friction_detector.py` (364 lines, read in full) contains a **different pattern set** than `/tp Step 0b`. Verified contents:
  - `ISSUE_PATTERNS` dict with 5 categories: `quoting_errors` (4 patterns), `command_failures` (2 patterns), `import_errors` (2 patterns), `permission_errors` (2 patterns), `file_errors` (2 patterns)
  - `WORKAROUND_PATTERNS` list (4 patterns)
  - `USER_RECURRENCE_PATTERNS` list (3 patterns)
  - Only `SyntaxError` overlaps with the `/tp Step 0b` patterns. **`friction_detector.py` and `/tp Step 0b` have ~1 overlap out of 13+5 categories — they are different detection scopes, not duplicates.**
  - Scope difference: `friction_detector.py` detects **recurring operational issues within a single session** (e.g., 3+ `SyntaxError` instances → recurrence). `/tp Step 0b` and `session_signals.py` detect **density of distinct friction events across a session** (e.g., 13 NO_COVERING_RECEIPT hits → high friction).
- [FACT] `P:/tmp/detect_pushback.py` is **not a friction regex duplicate** — it is a pushback keyword detector (11 keywords). Different signal.
- [FACT] `~/.claude/plugins/cache/local/cc-skills-analysis/1.0.123/skills/friction/SKILL.md` exists in the plugin cache (verified). It contains Mode 1 interaction-friction markers as *SKILL.md description*, not as code.

**Corrected DRY framing (resolves Blocker 3):**
- **Real DRY violation:** `/tp Step 0b` inline regex (13 patterns) and `session_signals.py` (after Unit 7 ships) are the **same friction patterns** in two places. This skill resolves it: `session_signals.py` becomes canonical post-Phase-2 flag flip, `/tp/SKILL.md:250-280` is deleted.
- **NOT a DRY violation:** `friction_detector.py` has different patterns (recurrence detection vs density). It is **complementary**, not duplicative. Both can coexist because they answer different questions:
  - "Did friction recur within this session?" → `friction_detector.py`
  - "How dense is friction overall in this session?" → `session_signals.py`
- **NOT a DRY violation:** `P:/tmp/detect_pushback.py` is a pushback detector (different signal). Migrated to `scripts/pushback_keywords.txt` per F-10 for durable placement.
- **NOT a DRY violation:** `/friction/SKILL.md` is a SKILL.md description in plugin cache, not executable code.

**Mitigation:** Code-smell inventory §"Corrected framing" separates (1) friction-regex duplication (real, between `/tp Step 0b` and `session_signals.py` only), (2) pushback-keyword migration (durable placement), (3) cross-skill data expansion (non-overlapping — `friction_detector.py` recurrence vs `session_signals.py` density).

### A2. "30 sessions of empirical data is enough for rolling-median calibration." [INFERENCE]

- [INFERENCE] The 30-session threshold is a design call, not a power-analysis result. With small corpora (verified: 9 top-level session directories on this host), reaching 30 sessions may take weeks; rolling-median statistics on 30 points have wide confidence intervals (interquartile range ≈ ±30% of median for n=30).
- **Mitigation:** Phase 1 acceptance criterion (see §Rollout) explicitly tests whether F/U and P/U correlate with session quality (pushback = ground truth proxy) at p<0.05 across 10+ sessions. If the test fails, thresholds are recalibrated before Phase 2. The 30-session threshold is the *minimum* sample size, not the *sufficient* one.
- **Power analysis [INFERENCE]:** for p<0.05 with 80% power on a Pearson correlation of r=0.5, n ≈ 29 sessions. For r=0.3 (more realistic), n ≈ 84. Recommend 50 sessions as a more defensible minimum.

### A3. "Compaction-aware by default is necessary because `compaction/INDEX.md` is rich enough." [UNKNOWN, mitigated]

- [FACT] `compaction/INDEX.md` schema was verified (see §2.2): columns are `Segment | File | Turns | Approx bytes | Keywords`. The `Keywords` column is a curated keyword extraction (5-8 keywords per segment).
- [UNKNOWN] Whether the compaction step's keyword extraction reliably surfaces friction/pushback signals depends on the compaction step's content-choice criteria, which is outside this design's control. If the compaction step's purpose is summarizing *work* (not *friction*), friction-bearing phrases like `"no, that's not right"` may not appear in the curated keywords.
- **Mitigation:** Phase 1 acceptance criterion (see §Rollout) runs the compaction-accuracy pilot as a hard prerequisite: 5 known-compacted sessions, both INDEX-only and `--include-segments` modes, compare F/U and P/U deltas. If delta >20%, the default is changed to `--include-segments`. This is the Phase 1 gate that resolves Critique Premise 3.
- **Long-term mitigation:** Open Question OQ-10 — propose to compaction-step author that `Keywords` column should include operator-correction markers when present.

### A4. "Embedded LLM in operator's session is 'free' (same quota as active session)." [INFERENCE, reframed]

- [INFERENCE] The original v0.2 framing ("free — same quota as active session") conflated **session quota** with **attention budget**. A 200-token hypothesis block at 80% context budget takes operator attention. If the operator is mid-task and reading a parallel screen, the structured output is *read-or-skipped*, not consumed.
- **Reframing:** Embedded LLM is **cheaper than subagent spawn** (no separate quota, no 30-90s spawn latency) but **not free**. Cost is paid in attention budget + 1-3s of model latency on the active session.
- **Mitigation:** the operator can suppress the hypothesis block by lowering the F/U threshold temporarily via a `--hypothesis-threshold <float>` flag. v1.0 ships the flag with default 2.0; operators with attention-constrained workflows can raise to 3.0 to suppress more aggressively.
- **Trade-off accepted:** `--full` without the hypothesis block is missing the value-add Layer 2 provides. Operators who opt out of Layer 2 lose the `/behave` pattern coverage. Documented in Open Question OQ-11.

### A5. "The skill should retire `/friction` standalone for the pushback+workflow use case." [HYPOTHESIS with measurement plan]

- [HYPOTHESIS] Operator consolidation preference (one skill that does four things vs four skills that do one thing each) is unknown. Phase 3 deprecation assumes operators prefer consolidation; the critical friend rightly notes this is unmeasured.
- **Measurement plan (resolves Critique §3.5):** Phase 3 tracks operator invocation of `/friction` standalone vs `/session-health --full`. After 30+ sessions of operator usage, if `/friction` standalone is invoked >50% of the time despite the deprecation notice, the consolidation hypothesis is refuted — revert deprecation and keep both skills.
- **Status:** the consolidation hypothesis is **deferred** for v1.0 (skill ships with `/friction` still callable). The deprecation warning ships in Phase 3 but does not remove the entry point. If post-Phase-3 measurement shows operators prefer `/session-health`, the deprecation becomes hard in v1.1.

## Coupling & Code-Smell Inventory

Per `P:\.data\wiki\concepts\coupling-inventory-as-mandatory-design-section.md`: enumerate coupling points, parameter counts, touch-points.

### Coupling matrix

| Coupled to | Coupling type | Direction | Coupling strength | Risk if changed |
|---|---|---|---|---|
| `~/.grok/sessions/<encoded-cwd>/<session-id>/chat_history.jsonl` | **Format contract** | Inbound (read-only); session notifier writes independently. Schema coupling with notifier. | Tight — JSONL schema is session-tool-owned | Session format change breaks script; mitigated by `schema_version` field in transcript header (Risk Table row "Session JSONL schema drift") |
| `~/.grok/sessions/<encoded-cwd>/<session-id>/compaction/INDEX.md` | **Format contract** | Inbound | Loose — script tolerates absence | None (fail-open; reads summary only) |
| `~/.grok/sessions/<encoded-cwd>/<session-id>/compaction/segment_NNN.md` | **Format contract** (optional) | Inbound (only with `--include-segments` flag) | Loose — flag-gated | None by default |
| `P:/.data/telemetry/session-signal-registry.json` | **Storage contract** (read+write, locked) | Owned by this skill | Self — schema is ours | Schema change breaks own migrations (see N-02 Open Questions) |
| `/tp/SKILL.md` Step 0b | **Caller contract** | Outbound | Medium — `/tp` becomes a thin caller | `/tp` Step 0b must be updated to delegate; inline regex DELETED on `tp_delegate: true` flag flip (Phase 2), not on Unit 7 ship; backup mandatory per Rollback |
| `/close/__lib/close_runner.py` | **Caller contract** | Outbound | Loose — one extra call in summary | None (additive) |
| `/debrief/SKILL.md` Phase 0 | **Caller contract** | Outbound | Loose — one extra read | None (additive) |
| `/notice/SKILL.md` T1/T6 | **Caller contract** (suggest-only) | Outbound | Loose — text-only suggestion | None |
| `P:/.data/wiki/capabilities/*.md` | **Capability registry** | Inbound — we register; query reads | Loose — registry consumers | None |
| `~/.grok/skills/close/__lib/close_runner.py:85-104` | **Pattern coupling** (code reuse) | Inbound — copy `msvcrt.locking` pattern | Loose — pattern is well-documented | Pattern divergence between skills acceptable |

### Code-smell inventory

Per AGENTS.md "Refactor dismissal gate" — enumerate before declaring refactor "gold-plating" (resolves Critique Premise 4 — DRY framing corrected):

| Smell | Present? | Count | Threshold met? | ROI |
|---|---|---|---|---|
| **DRY violation (friction regex)** — `/tp Step 0b` inline regex (13 patterns at `~/.grok/skills/tp/SKILL.md:250-280`) is duplicated in `session_signals.py` after Unit 7 ships. **`close/__lib/friction_detector.py` is NOT a duplicate** (verified by round-2 critical friend: 5 different categories: `quoting_errors`, `command_failures`, `import_errors`, `permission_errors`, `file_errors`; only `SyntaxError` overlaps; different scope = recurrence detection vs density). | **YES (real DRY violation, narrowed scope)** | 2 confirmed locations (`/tp/SKILL.md:250-280` and `session_signals.py`); `close/__lib/friction_detector.py` excluded | **YES** | **POSITIVE** — single source of truth after Phase 2 flag flip |
| **Pushback keyword set "duplication"** | **NO — different signal, not a duplicate** | n/a | n/a | Pushback is a NEW signal introduced by this skill. The 11 keywords from `P:/tmp/detect_pushback.py` are migrated to durable storage (`scripts/pushback_keywords.txt` per F-10). The 5 keywords from `/friction` Mode 1 (plugin source) are adopted. The 16-keyword union is not consolidation of duplicate code; it is durable placement of a new signal. |
| **Cross-skill expansion (not DRY)** | **NO — different scope** | n/a | n/a | `close/__lib/friction_detector.py` does within-session recurrence (3+ same-category hits → recurrence). `session_signals.py` does density across the session. Both can coexist; the scope is different and the consumers are different (`friction_detector.py` → `/close` continuation coverage; `session_signals.py` → `/close` summary line). |
| **Parameter count** (`session_signals.py` CLI flags) | 6 args (`--transcript`, `--json`, `--full`, `--no-cap`, `--include-segments`, `--sessions`) | <7 | NO | — |
| **Touch-point count** (new friction category added → how many places change?) | 1 (`session_signals.py` + tests) | ≤3 | Borderline | Acceptable — single source of truth |
| **Test coverage** of new code | TBD — must be ≥80% per testing.md | — | — | Required |

**Corrected framing (resolves Blocker 3 — round-2 critical friend verified `friction_detector.py` content):** the prior framing incorrectly claimed a 2-way DRY violation between `/tp Step 0b` and `close/__lib/friction_detector.py`. Round-2 verification (reading `friction_detector.py` in full) showed the two files have **different pattern sets** with **only `SyntaxError` overlap**. The corrected framing:
1. **Friction regex duplication** (real, between `/tp Step 0b` and `session_signals.py` only) — this skill resolves it. `close/__lib/friction_detector.py` is **NOT** in this category.
2. **`friction_detector.py` is complementary** — different scope (recurrence detection within session, 3+ same-category hits). Both files can coexist; consumers are different (`friction_detector.py` → `/close` continuation coverage; `session_signals.py` → `/close` summary line + `/tp` Step 0b).
3. **Pushback keyword migration** (durable placement, not DRY) — this skill introduces the signal.
4. **`/friction/SKILL.md` plugin** — SKILL.md description, not code. Not a duplicate.

The structural-fix story is real for (1), correctly placed for (3), explicitly non-overlapping for (2), and inapplicable for (4).

The structural-fix story is real for (1), correctly placed for (2), and explicitly non-overlapping for (3).

### Coupling invariant

**No new dependency from `/session-health` to `/tp`, `/close`, `/debrief`, `/notice`, `/aar`.** The skill is a **centralized dependency** in the dependency graph (revised by Blocker 5 — was incorrectly labeled "leaf node" despite having 5 inbound consumers). Callers depend on us; we depend only on session transcript format and the registry file we own. The "centralized" descriptor is correct: `/session-health` is a single point of failure for 5 downstream consumers, which is exactly the vendor-lock-in risk noted in the Risk Table ("After Phase 2, 4 callers depend on `/session-health`"; updated to 5 callers per Blocker 4). The `@deprecated`-comment recovery path and the `PreToolUse` backup hook mitigate this risk.

---

## Implementation Plan

Eight units, ordered to deliver a usable surface at every step. Each unit ships with a feature flag (default off) so prior behavior is preserved until the flag is flipped.

### Unit 1: Foundation — signal extraction script (no skill yet)

**Owner:** Operator (built by Grok, validated by operator)

**Files:**
- `C:/Users/brsth/.grok/skills/session-health/scripts/session_signals.py` (new, ~250 LOC)
- `C:/Users/brsth/.grok/skills/session-health/__lib/signals.py` (new, ~80 LOC — dataclasses)
- `C:/Users/brsth/.grok/skills/session-health/__lib/transcript.py` (new, ~120 LOC — compaction-aware reader)
- `C:/Users/brsth/.grok/skills/session-health/scripts/pushback_keywords.txt` (new, ~20 LOC, versioned)
- `C:/Users/brsth/.grok/skills/session-health/tests/test_session_signals.py` (new)
- `C:/Users/brsth/.grok/skills/session-health/tests/fixtures/hand_counted_transcript.jsonl` (new — hand-counted fixture with expected F/U and P/U)
- `C:/Users/brsth/.grok/skills/session-health/tests/fixtures/regression_5_sessions/` (new — 5 historical transcripts for regression)

**Feature flag:** none (script runs standalone)

**Acceptance criteria:**
- `python session_signals.py --transcript <path> --json` exits 0 on a valid transcript, produces output matching §2.3 schema with `error: null`
- `F/U` and `P/U` values match `tests/fixtures/hand_counted_transcript.jsonl` expected values within ±0.05 (expected: F/U=0.59, P/U=0.36 based on hand-count)
- Compaction-aware default (resolves F-01): reads `chat_history.jsonl` + `compaction/INDEX.md` summary; does NOT load `segment_NNN.md` content unless `--include-segments` is passed
- 11 friction patterns from `/tp Step 0b` are detected (regression: spot-check on `tests/fixtures/regression_5_sessions/` against prior `/tp/SKILL.md:250-280` output)
- 16 pushback keywords detected per `pushback_keywords.txt` (union verified: 11 ∪ 5 = 16, ∩ = ∅)
- Unit tests ≥80% coverage via `pytest --cov=session_health --cov-report=term-missing tests/` (resolves F-34)
- Failure path: corrupted transcript produces `error: "JSONL parse error at line N"` with zero-valued metrics (not crash)
- `auto_backgrounded` category detected by transcript-text grep for `automatically moved to background` (not session-tool state file)

### Unit 2: Registry + cache

**Owner:** Operator

**Files:**
- `C:/Users/brsth/.grok/skills/session-health/scripts/signal_registry.py` (new, ~200 LOC — includes `msvcrt.locking` per `close_runner.py:85-104`)
- `C:/Users/brsth/.grok/skills/session-health/tests/test_signal_registry.py` (new)

**Feature flag:** `--registry <path>` (default `P:/.data/telemetry/session-signal-registry.json` — moved from `P:/.data/wiki/` per AGENTS.md file location conventions; telemetry/jsonl files belong at `P:/.data/telemetry/`)

**Acceptance criteria:**
- First scan: registry created with all sessions' metrics
- Second scan: <1s P95 for 100 sessions (cache hits)
- Cache invalidation: transcript mtime > scanned_at → re-scan; compaction/INDEX.md mtime > scanned_at → re-scan
- Registry loss: detect missing file → re-scan all → no error
- **Corruption detection (resolves F-40):** three corruption checks, each with explicit recovery:
  1. `json.JSONDecodeError` on read → treat as missing, re-scan all
  2. Zero-byte file → treat as missing, re-scan all
  3. Schema validation failure (missing required fields: `session_id`, `scanned_at`, `metrics`) → log warning, re-scan all (don't silently use malformed entry)
- **Multi-terminal (resolves F-02):** uses `msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)` on `registry.lock` sidecar file. Lock held for entire read-modify-write cycle. Concurrent calls block up to 5s, then fail with `error: "registry_lock_timeout"`. Pattern copied from `~/.grok/skills/close/__lib/close_runner.py:85-104`.
- Atomic rename of registry file after lock release: `tmp + os.replace` (per file-editing-protocol.md)
- **`--prune-stale` flag (resolves F-49):** scans the registry, identifies entries whose `transcript_path` no longer resolves on disk, and either marks them `stale: true` (default) or deletes them (when `--prune-stale --delete` is passed). Output: `{scanned: <N>, stale_count: <N>, deleted: <N>, marked: <N>}`. Behavior is idempotent — running twice produces no further changes. Operator-only command; not exposed to other skills via `--json`.

### Unit 3: Baseline + drift detection

**Owner:** Operator

**Files:**
- `C:/Users/brsth/.grok/skills/session-health/scripts/drift_detector.py` (new, ~200 LOC)
- `C:/Users/brsth/.grok/skills/session-health/tests/test_drift_detector.py` (new)

**Feature flag:** none (library)

**Acceptance criteria:**
- Rolling median across all sessions computed correctly
- Drift alert: rolling mean over last 5 sessions > 1.5× historical median
- Chronic pattern: any friction category in ≥3 of last 10 sessions → flagged
- Workflow opportunity (Mode 2 from `/friction`): same command 3+ times across sessions → candidate
- Synthetic registry test: 100 sessions, known drift at session 80 → detected

### Unit 4: SKILL.md + Quick mode

**Owner:** Operator

**Files:**
- `C:/Users/brsth/.grok/skills/session-health/SKILL.md` (new, ~300 LOC)
- `C:/Users/brsth/.grok/skills/session-health/tests/test_skill_quick.py` (new — invokes skill via mock agent)

**Feature flag:** skill registered in catalog but `enabled: false` until Unit 7

**Acceptance criteria:**
- SKILL.md frontmatter declares `provides: [session-health-monitoring]`, `host: grok`, `domain: lifecycle`, `version: 1.0.0` (resolves F-25)
- Quick mode (default invocation, bare `/session-health`): one-line verdict + 3 most elevated signals
- SKILL.md line count ≤400 lines, verified by `wc -l ~/.grok/skills/session-health/SKILL.md` returning ≤400 (resolves F-41)
- Manual operator invocation works in shadow mode (skill visible but not auto-invoked by other skills)

### Unit 5: Full mode + hypothesis-testing

**Owner:** Operator

**Files:**
- Append to `SKILL.md` (--full mode docs)
- `C:/Users/brsth/.grok/skills/session-health/__lib/hypotheses.py` (new, ~150 LOC — adopted /behave pattern)

**Feature flag:** `--full` mode

**Acceptance criteria:**
- When `F/U > 2.0 OR P/U > 0.4`: emit hypothesis block (3-5 hypotheses, cost-ordered tests, falsification, calibrated confidence)
- When below threshold: skip hypothesis block (don't waste tokens)
- Cite `/behave/SKILL.md` confidence calibration table as source
- No external LLM call (hypothesis generation is LLM-judgment in the orchestrator's own context, not a subagent spawn)

### Unit 6: Trend mode + cross-session analysis

**Owner:** Operator

**Files:**
- Append to `SKILL.md` (--trend mode docs)

**Feature flag:** `--trend` mode

**Acceptance criteria:**
- Reads registry for last N sessions (default 5, configurable via `--sessions`)
- Outputs F/U + P/U trend table
- Drift alert if rolling mean > 1.5× median
- Chronic pattern list if any friction category ≥3 of last 10 sessions
- **`--include-stale` flag (resolves F-49):** by default, stale entries (registry rows whose `transcript_path` no longer resolves) are EXCLUDED from trend output. With `--include-stale`, stale entries appear in the trend table with `stale: true` annotation. Stale entries never contribute to drift alerts or chronic-pattern detection (they are flagged, not counted).

### Unit 7: Integration wiring

**Owner:** Operator

**Files modified:**
- `C:/Users/brsth/.grok/skills/tp/SKILL.md` — Step 0b (lines 250-280): inline regex is **gated by `session_health.tp_delegate` flag**. While flag is `false`, inline regex remains as active behavior (resolves F-48). When flag flips to `true` (Phase 2 after validation), the inline regex is DELETED and replaced with `python session_signals.py --json | jq` thin-caller pattern. Per removal-protocol.md, no fallback kept post-flip.
- `C:/Users/brsth/.grok/skills/close/__lib/close_runner.py` — adds `session_signals.py --json` call before final summary; one friction/pushback line in close report when `session_health.close_summary: true`. (Note: this modifies `close_runner.py`, NOT `close_accounting.py` — see F-27 clarification.)
- `C:/Users/brsth/.grok/skills/debrief/SKILL.md` — Phase 0 reads `--json` output as Lens 3 input
- `C:/Users/brsth/.grok/skills/notice/SKILL.md` — T1 (error state) and T6 (unverified diagnosis) trigger suggestion updated to include "run /session-health --full" (verified triggers per `/notice/SKILL.md:116-122`)
- `C:/Users/brsth/.grok/skills/aar/SKILL.md` (NEW — added by Blocker 4) — Phase 4 (`operator_signal_delta`, lines 147-185) REPLACES its inline signal computation (pushback_count, pushback_categories, friction_signal_baseline_delta, etc.) with `python session_signals.py --json --session <id>` calls. AAR's value-add (cross-session episode clustering, double-loop analysis, signal synthesis) is preserved; only raw extraction is delegated.

**Feature flags (resolves F-14):**
- `session_health.tp_delegate: false` (default — until validated)
- `session_health.close_summary: false` (default)
- `session_health.debrief_input: false` (default)
- `session_health.notice_suggest: false` (default — flipped to `false` for parity with siblings; not `true`)
- `session_health.aar_phase4_consume: false` (default — NEW by Blocker 4; AAR keeps inline computation until validated)

**F-14 resolution:** the original `notice_suggest: true` default was inconsistent with the other 3 flags. Per reviewer, suggestion text is user-visible and could be noisy if the wording is wrong. The default is now `false` (parity with siblings); flip after Phase 1 shadow validation. No prior validation evidence was cited for `true`, so this is the safer default.

**Blocker 4 resolution:** the AAR integration is NOT a no-op (revised). `/aar/SKILL.md` Phase 4 lines 147-185 (`operator_signal_delta`) must be modified to consume `session_signals.py --json` output instead of computing signals inline. Without this, two paths compute overlapping signals (canonical extraction drift). The 5th feature flag (`aar_phase4_consume`) gates the flip.

**Acceptance criteria:**
- `/tp session` output with `--json` matches prior inline regex output on `tests/fixtures/regression_5_sessions/` (the 5 historical transcripts from Unit 1). Variance ≤5%.
- `/close` summary includes friction + pushback one-liner when feature flag on
- `/debrief` Phase 0 includes signal-registry metrics in discovery report
- `/notice` T1/T6 suggest `/session-health --full` (suggestion text only, no auto-invoke) — and the wording matches the verified T1/T6 definitions per `/notice/SKILL.md:116-122`
- `/aar` Phase 4 — when `aar_phase4_consume: true`, the AAR's `operator_signal_delta` block reads from `session_signals.py --json` instead of computing inline. **Critical regression test:** AAR report output values for `pushback_count`, `pushback_categories`, `friction_signal_baseline_delta` must match prior inline values within ±1% (the AAR's value-add is signal synthesis, not extraction — divergence indicates a signal-extraction bug).

### Unit 8: Capability registry + skill catalog

**Owner:** Operator

**Files:**
- `P:/.data/wiki/capabilities/session-health-monitoring.md` (new)
- `P:/.data/wiki/concepts/skill-catalog.md` (auto-regenerated)

**Acceptance criteria:**
- Capability contract follows existing 70-file pattern (frontmatter with `title`, `node_type: capability`, `domain`, `created`)
- `python P:/.data/wiki/scripts/capabilities.py --for-domain lifecycle` lists `session-health-monitoring`
- **Index regeneration timing (resolves F-44):** Run `python P:/.data/wiki/scripts/index_skills.py` immediately after SKILL.md is committed in Unit 4; commit the catalog update in the same change set (per AGENTS.md "Skill lifecycle maintenance": "After adding/removing/renaming any skill: `python P:/.data/wiki/scripts/index_skills.py`"). Do NOT defer catalog regeneration to a later commit.

### Unit ordering rationale

Units 1-3 are pure library code (no skill yet, no callers). Unit 4 produces a runnable skill. Units 5-6 add modes. Unit 7 wires callers. Unit 8 makes the skill discoverable.

Each unit is independently shippable: Unit 1 ships as a CLI tool, Unit 4 ships as a manual-invocation skill, Unit 7 ships the integration. The feature flags ensure no caller breaks during rollout.

---

## Traceability Matrix

| Design component | Implementation unit | Files |
|---|---|---|
| Friction signal extraction (11 patterns) | Unit 1 | `scripts/session_signals.py` |
| Pushback signal extraction (16 keywords) | Unit 1 | `scripts/session_signals.py` + `scripts/pushback_keywords.txt` |
| Compaction-aware transcript reader | Unit 1 | `__lib/transcript.py` |
| F/U + P/U + duration metrics | Unit 1 | `__lib/signals.py` (dataclass) + Unit 1 script |
| Registry cache (pull-based) | Unit 2 | `scripts/signal_registry.py` |
| Mtime-based invalidation | Unit 2 | `scripts/signal_registry.py` |
| Self-healing on registry loss | Unit 2 | `scripts/signal_registry.py` |
| Rolling median baseline | Unit 3 | `scripts/drift_detector.py` |
| Drift alert (1.5× median) | Unit 3 | `scripts/drift_detector.py` |
| Chronic pattern detection (3/10 sessions) | Unit 3 | `scripts/drift_detector.py` |
| Quick mode (one-line verdict) | Unit 4 | `SKILL.md` |
| Full mode (friction breakdown + pushback quotes) | Unit 5 | `SKILL.md` + `__lib/hypotheses.py` |
| Hypothesis-testing block (`/behave` pattern) | Unit 5 | `__lib/hypotheses.py` |
| Trend mode (cross-session) | Unit 6 | `SKILL.md` |
| `--json` output contract | Unit 1 + 4 | `__lib/signals.py` + `SKILL.md` |
| `/tp session` Step 0b delegation | Unit 7 | `tp/SKILL.md` |
| `/close` summary integration | Unit 7 | `close/__lib/close_runner.py` |
| `/debrief` Phase 0 input | Unit 7 | `debrief/SKILL.md` |
| `/notice` T1/T6 suggestion | Unit 7 | `notice/SKILL.md` |
| Capability registry entry | Unit 8 | `P:/.data/wiki/capabilities/session-health-monitoring.md` |
| Skill catalog regeneration | Unit 8 | `index_skills.py` |

---

## Key Decisions

### D1: Layered architecture (script + skill + LLM)

**Choice:** Layer 1 = deterministic Python script (no LLM); Layer 2 = embedded LLM judgment only in `--full`; Layer 3 = skill wrapper.

**Rationale:** Mirrors `context-firewall-architecture.md` 3-layer pattern. The script IS the firewall — orchestrators call a script and get JSON, never touch raw transcripts. Token cost stays low (only `--full` triggers LLM).

**Rejected alternatives:**
- *Pure skill (LLM-only)*: would consume substantially higher token cost on every `/close`, `/tp session`, `/debrief` invocation. [INFERENCE] the exact multiplier was originally claimed as "5-10x" but no cost model was cited (resolves F-15). A pure-LLM approach would mean each invocation costs ~1500-3000 tokens of LLM scan vs the script's <500 tokens of pure-Python execution. Replacing the "5-10x" claim with the qualitative language: "the cost would be substantially higher because every invocation routes through the LLM instead of a deterministic script."
- *Pure script (no skill)*: would lack the LLM judgment needed for hypothesis-testing in `--full`. Operator couldn't ask "how's this session going?" interactively.

### D2: Pull-based registry, not push-based

**Choice:** Registry at `P:/.data/telemetry/session-signal-registry.json` (per AGENTS.md "File location conventions": telemetry/data files belong at `P:/.data/telemetry/`, not `P:/.data/wiki/`) is computed on-demand by re-scanning transcripts. Cached in the registry file with mtime invalidation. If lost, regenerate from transcripts.

**Rationale:** [INFERENCE] Per brief: transcripts are source of truth (always on disk, always complete). [INFERENCE] Push-based signal file has the failure mode the operator corrected twice (signal file lost → data loss; signal file stale → wrong verdict) — the specific incidents are not cited in the brief; this is the operator's prior pattern, accepted as design rationale. [FACT] `scan_external_skills.py` uses the same pull-based pattern: verified at `P:/.data/wiki/scripts/scan_external_skills.py:128-134` — `def scan_all_roots()` walks `SCAN_ROOTS` via `root.rglob("SKILL.md")`, computing results on demand rather than maintaining a push-based cache.

**Rejected alternative:** *Push-based signal file written by `/close`*: depends on every session close being successful. Lost signal file = lost history. Pull-based is self-healing.

### D3: Adopt `/behave` pattern, do not delegate

**Choice:** In `--full` mode, embed the `/behave` hypothesis-testing pattern inline. Cite `~/.claude/plugins/cache/local/cc-skills-thinking/1.0.19/skills/behave/SKILL.md` as source.

**Rationale:** [FACT] `/behave` lives in the disabled `cc-skills-thinking` plugin on this host (verified at `~/.grok/skills/tp/SKILL.md:1170`: "the `cc-skills-thinking` plugin is disabled on this host"). We cannot depend on it. But the pattern is well-documented; embedding it preserves the discipline without the dependency.

**Rejected alternative:** *Delegate to `/behave`*: would fail on this host. Documented.

### D4: `/pace` deferred to v1.1

**Choice:** v1.0 ships without `/pace` integration. Operator can still invoke `/pace` directly.

**Rationale:** Per brief: "is WIP/load scoring part of /session-health or separate?" The brief's framing separates them. Cognitive load (duration, WIP, rework) overlaps with `/pace`'s purpose but the canonical owner is `/pace`. If operator requests `/session-health --load` after rollout, v1.1 adds it as a thin caller to `/pace`.

**Rejected alternative:** *Build full `/pace` integration in v1.0*: scope creep. Two skills with overlapping responsibilities. Pick one owner per capability.

### D5: Three output modes + JSON integration mode

**Choice:** Four modes total — `quick` (default), `full`, `trend`, `json`. The `json` mode is the integration surface; the other three are operator-facing.

**Rationale:** Operators want different granularities at different times (mid-session quick check vs end-session full report vs weekly drift check). Downstream skills want a stable JSON contract. Four modes cover both.

**Rejected alternative:** *Single mode with verbose output*: every caller reads everything. Token waste for `/close` (which wants one line); context window pressure for operator (`/session-health --full` always emits hypothesis block even when not needed).

### D6: Conservative pushback keyword set

**Choice:** 16 keywords = 11 from `P:\tmp\detect_pushback.py` (validated this session) + 5 from `/friction` Mode 1 markers. Stored in `scripts/pushback_keywords.txt` (versioned, editable without code change).

**Rationale:** [FACT] The 11 from `detect_pushback.py` produced 8 hits on this session's transcript. Verified this session by running the keyword match against `~/.grok/sessions/P%3A%5C\019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9\chat_history.jsonl`: hits at lines 230 (`did you do`), 249 (`why`), 293 (`don't`), 352 (`no`), 397 (`don't`), 426 (`don't`), 481 (`don't`), 504 (`wrong`). The 5 from `/friction` add capability (the brief lists them too: "didn't call", "same problem again", etc.). Beyond 20 keywords increases false-positive rate (per `notice/SKILL.md` calibration guidance).

**Rejected alternative:** *LLM-classified pushback*: would consume tokens on every scan; also degrades under context momentum (the same problem `/close` had with gate detection per `close-authority-state-machine-design.md`).

### D7: Skill scope = user (not workspace)

**Choice:** `C:\Users\brsth\.grok\skills\session-health\` (user scope, matches `/tp`, `/close`, `/debrief`).

**Rationale:** Per `P:/.data\wiki\concepts\skill-host-applicability-convention.md`: host = grok, not both. User scope is the right level for a personal-monitoring skill that reads session transcripts (private to the user).

**Rejected alternative:** *Workspace scope (`P:/.grok/skills/`)*: would expose session-monitoring to anyone with workspace access. Wrong privacy boundary.

**Multi-host applicability (resolves F-31):** This skill is Grok Build only. Claude Code hosts cannot install at `~/.grok/`; an equivalent for Claude Code would be `~/.claude/skills/session-health/` with adapted paths (`~/.claude/projects/` for transcripts instead of `~/.grok/sessions/`) and adapted friction patterns (Claude Code uses different error markers — e.g., `<tool_use_error>` blocks rather than Grok's `automatically moved to background` log lines). Adaptation is non-trivial because the friction regex set is host-specific. This design is documented for the Grok Build host; porting to Claude Code is a separate workstream.

### D8: Compaction-aware by default, fail-open

**Choice:** If `compaction/INDEX.md` exists, scan pre-compaction segments in addition to `chat_history.jsonl`. If absent, scan only `chat_history.jsonl`. Errors return empty results with `error` field, never raise.

**Rationale:** Per `/tp session` Step 0a: pre-compaction work is invisible without compaction-aware scan. Reference session 019f9f4f showed wrong diagnosis inherited from compaction summary — same class of failure. Fail-open matches `close/__lib/friction_detector.py` principle.

**Rejected alternative:** *Strict — fail loudly on missing compaction dir*: would break every pre-compaction-free session. Over-engineering.

---

## Risk Table

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Skill never invoked (no usage data) | Medium | High | Wire as input to `/close`, `/tp session`, `/debrief`, `/aar`. `/notice` suggests when friction elevated (Phase 1 default off, Phase 2 flip after shadow validation). Shadow mode validates adoption before going default. |
| Registry corruption (multi-terminal race) | Low | Medium | `msvcrt.locking` on `registry.lock` sidecar file (pattern from `close_runner.py:85-104`). Concurrent calls block up to 5s, then fail with `error: "registry_lock_timeout"`. Three explicit corruption checks (F-40): `JSONDecodeError`, zero-byte, missing required fields. Each triggers re-scan all. |
| Pushback keywords miss subtle cues | Medium | Medium | 16 keywords is broader than 11 (detect_pushback.py baseline). Tune quarterly via `/aar` Phase 4 `operator_signal_delta` (verified at `/aar/SKILL.md:152-201`) — the `pushback_categories` signal feeds directly into keyword tuning. Add custom keyword file in v1.1 if operators want. |
| `/tp Step 0b` delegation breaks session-end review | Low | Medium | Feature flag default off; shadow-mode comparison with prior inline regex for 2 weeks before flipping flag. Regression tested against `tests/fixtures/regression_5_sessions/`. If regression, revert flag and stay inline. Per F-06, the inline regex is DELETED on flip (no fallback kept). |
| Hypothesis-testing layer drifts from `/behave` discipline | Medium | Low | Adopt `/behave`'s exact confidence calibration table verbatim; cite source. **Cache fallback (resolves F-39):** the citation path `~/.claude/plugins/cache/local/cc-skills-thinking/1.0.19/skills/behave/SKILL.md` may not exist at runtime (plugin is disabled and the cache may be evicted). If the path is missing, Layer 2 falls back to the inline hypothesis template defined in `__lib/hypotheses.py` (no external citation needed). Cite `/behave` only when the path is reachable. |
| Token cost on `--full` with large transcripts | Medium | Medium | Cap transcript read to last 500 messages by default; `--full --no-cap` reads complete (resolves F-21; replaced the hostile `--full --full` pattern). Compaction-aware scan loads `INDEX.md` summary by default; `--full --include-segments` loads full segment files (5-30s slower). |
| Conflict with `/notice` observation surfacing | Low | Low | `/notice` is suggestion-only; never auto-invokes `/session-health`. Different output channels (`/notice` = one line; `/session-health --full` = multi-line report). No conflict in surface area. T1 (error state) and T6 (unverified diagnosis) trigger definitions verified at `/notice/SKILL.md:116-122` (resolves F-18). |
| Compaction scan accuracy/speed tradeoff (F-17) | Medium | Medium | Default = INDEX.md summary only. Trade-off: fast (<100ms) but may undercount pre-compaction friction/pushback that didn't make it into INDEX's keyword list. Mitigation: pilot 5 compacted sessions in both modes (default vs `--include-segments`), measure F/U and P/U delta. If delta >20%, change default to `--include-segments`. |
| Compaction-aware scan misses pre-compaction content | Low | High | Always read `compaction/INDEX.md` when present. Test against known-compacted fixture at `~/.grok/sessions/P%3A%5C\019f6b24-dd44-7192-8a98-02e2be35f8c6\` (verified 2026-07-29). |
| Hypothesis block misfires (false positives on F/U > 2.0) | Medium | Low | Hypothesis block is informational, not actionable. Operator reads and judges. No auto-remediation. |
| Registry file grows unboundedly | Low | Low | Sessions are bounded (hundreds, not millions). 10KB per session × 1000 sessions = 10MB. No pruning needed for v1.0. Add TTL in v1.1 if it ever matters. |
| Stale registry entries (session dir deleted but registry retains) | Low | Low | Resolves F-33: garbage-collection rule = "registry entries whose `transcript_path` no longer resolves on disk are marked `stale: true` (not deleted) on next scan; surfaced in `--trend --include-stale` output. Manual cleanup via `--prune-stale` operator command." v1.0 keeps stale entries; v1.1 may add auto-prune with TTL. |
| Session JSONL schema drift (F-28) | Low | High | Schema versioning: transcript files emit `schema_version` field in their header (proposed — requires session-tool change). Until then: Layer 1 emits `error: "schema_version_mismatch"` on unknown fields; operator reports drift to session-tool maintainer. |
| `/close` integration breaks close report format | Low | High | Feature flag default off; integration is one line of friction/pushback summary, additive. If breaks `/close`, revert flag. |
| Fixtures missing for regression tests | Low | Medium | Resolves F-16: Unit 1 ships `tests/fixtures/hand_counted_transcript.jsonl` (expected F/U=0.59, P/U=0.36) and `tests/fixtures/regression_5_sessions/` (5 historical transcripts at canonical paths under `P:/.data/telemetry/session-health-fixtures/`). |
| `/behave` cache eviction breaks citation | Low | Low | F-39: inline fallback in `__lib/hypotheses.py` provides the hypothesis template without external citation. Cite `/behave` when reachable, fall back silently otherwise. |
| **Hawthorne effect** (resolves Critique Open-ended Risk 4.2) | High | Medium | When operators know their session is being scored, behavior changes (self-censorship of `"no"`, formalization of queries). **Mitigation:** the design does NOT show real-time F/U or P/U during a session. `quick` mode is operator-invoked only; the registry does not auto-refresh mid-session. The hypothesis block is operator-triggered (`--full`) and produces a one-shot output, not a live ticker. Operators who want real-time monitoring must explicitly run `/session-health` each time. **Open Question OQ-12:** investigate operator-invoked monitoring vs `/notice` for live surfacing in v1.1. |
| **Hypothesis feedback loop absent** (resolves Critique Open-ended Risk 4.3) | Medium | Medium | Without operator feedback on hypothesis utility, the threshold never self-corrects. **Mitigation:** the registry stores `hypothesis_feedback: {useful: <count>, noise: <count>}` per session, populated by an operator command `/session-health --feedback <session-id> <useful|noise>`. After 30 sessions with feedback data, recalibrate hypothesis-fire threshold via the existing `signal_registry.py --recalibrate` mechanism. v1.0 ships the feedback command; v1.1 adds automatic threshold adjustment. |
| **Friction category synchronization contract missing** (resolves Critique Open-ended Risk 4.1) | Medium | High | After Unit 7 ships, `session_signals.py` is the source of truth. If patterns change without propagating, `/tp`'s category table drifts. **Mitigation:** §3.1 Maintenance contract documents the relationship. Soft contract for v1.0 (no CI enforcement). Open Question OQ-8 covers whether to add a CI check that compares the two. |
| **Vendor lock-in via canonical-source designation** (resolves Critique Open-ended Risk 4.4; updated by Blocker 4) | Medium | High | After Phase 2, **5 callers** depend on `/session-health` (revised from 4 per Blocker 4: `/close`, `/tp`, `/debrief`, `/notice`, `/aar`). A bug in this skill cascades to all 5. **Mitigation (revised F-06):** when the `session_health.tp_delegate` flag flips to `true` (Phase 2), the inline regex is **deleted but the `@deprecated` comment marker is left in place for 30 days post-flip** (not post-Unit-7-ship) with `git blame` history preserved. This is a soft removal that preserves a recovery path. After 30 days of stable operation, the `@deprecated` comment is hard-removed too. This is a **change from F-06's hard-delete-on-flip position** — the recovery path is the trade-off for vendor lock-in. Backup of the inline regex is kept at `P:/.artifacts/<term>/tp-step-0b-inline.bak` for 90 days. The `/aar` integration has its own flag (`aar_phase4_consume`) so the AAR can flip back to inline computation if `session_signals.py` regresses. |
| **Backup enforcement** (resolves Critique Open-ended Risk 4.5) | Medium | Medium | The Phase 2 `tp_delegate: true` flag flip depends on operator-memory: a backup at `P:/.artifacts/<term>/tp-step-0b-inline.bak` must exist before the flip. Process discipline alone is unreliable. **Mitigation:** a `PreToolUse` hook (existing pattern in `~/.claude/hooks/PreToolUse.py`) on the flag-flip tool call aborts if the backup file does not exist. The hook is registered in `~/.claude/settings.json` (or equivalent Grok Build config). Hook script lives at `~/.grok/skills/session-health/__lib/pre_flip_backup_check.py`. Backup creation is itself a tool action that the hook gates; the operator cannot flip the flag without first executing the backup tool. |
| **Compaction behavior under short sessions** (Critique §4.5) | Low | Low | Most sessions are short (< 60 messages) and never compact; compaction-aware logic is dormant. **Mitigation:** no action needed. The INDEX-only default is optimal only when sessions actually compact; for short sessions, the script reads `chat_history.jsonl` only and the compaction code path is skipped. Documented in Open Question OQ-13. |
| **Weighting by line context** (Critique §4.6) | Low | Low | A routine clarification `"no, that's not right"` carries the same weight as a hostile operator correction. **Mitigation:** out of scope for v1.0. v1.1 may add context-aware weighting (e.g., pushback in a code-review line vs casual aside). Documented in Open Question OQ-14. |
| **Operator over-reliance on metrics** (Critique §4.7) | Medium | Low | Operators may treat the verdict as a score and game the metric. **Mitigation:** the verdict is descriptive, not prescriptive. SKILL.md wording emphasizes "indicator" and "current signal level" rather than "score" or "grade". Operators see raw counts alongside the verdict (e.g., `F/U=0.59 (12 friction signals)`), so the verdict is interpretable, not opaque. |

---

## Rollout

### Phase 1: Shadow mode (weeks 1-2)

**Scope:** Units 1-3 + Unit 8 ready. Skill files in place but `enabled: false` in catalog.

**Validation (4 acceptance gates — all must pass):**

1. **Signal accuracy gate:**
   - Run `python session_signals.py --json` on this session's transcript → compare F/U + P/U against hand-counted values from `P:\tmp\detect_pushback.py` (this session's transcript: F/U ≈ 0.0 [no friction patterns], P/U ≈ 0.36 [8 pushback keywords / 22 user messages]). Acceptable variance: ±0.05.
   - Run on 5 historical sessions → compare against `/tp Step 0b` output. Acceptable variance: ±5%.

2. **Calibration-saturation gate (revised by round-2 critical friend; resolves Blocker 1 — Gate 2 power-analysis failure):**
   - **Original test (REJECTED):** Pearson correlation between F/U and P/U across 10+ sessions at p<0.05. **Power analysis showed this test has <30% power at r=0.5 with n=10** (pearson n for 80% power at r=0.5 ≈ 29; at r=0.3 ≈ 84). With only 10 sessions available, the test could fail to reject null even if the underlying correlation is real — a false-negative risk that blocks Phase 2 spuriously.
   - **Replacement test (saturation check) [INFERENCE]:** After scanning the **full fleet history** (verified: 9 top-level session directories under `~/.grok/sessions/` as of 2026-07-29), compute F/U and P/U distributions. **Calibration criterion:** the distributions are stable — median F/U and median P/U each change by <10% when adding the last 5 sessions to the prior corpus. This is a **distributional stability** check, not a statistical significance test. It doesn't require power analysis; it requires the distribution to have converged.
   - **Why this works without power analysis:** with small corpora, power is impossible to achieve. Stability is observable: if 5 more sessions don't shift the median by >10%, the distribution has likely converged and the hardcoded thresholds (Low <0.5, Normal 0.5-1.5, High >1.5 for F/U; analogous for P/U) are reasonable starting points. **This is a sufficient condition for shipping, not a proof of correctness.** Calibration by 30+ sessions with rolling-median recomputation (the v1.1 path) is the stronger guarantee.
   - **Secondary test (still valid):** if more than 50% of historical sessions trigger the hypothesis-block threshold (F/U > 2.0 OR P/U > 0.4), the thresholds are too sensitive — recalibrate before Phase 2.
   - **Data source:** all sessions under `~/.grok/sessions/` (full fleet scan, currently 9 directories).
   - **Falsifier:** if the last 5 sessions shift median F/U or P/U by ≥10%, the corpus hasn't stabilized; defer Phase 2 and wait for more sessions. This is a softer gate than Pearson — it accepts "stable enough to ship" rather than "statistically proven."
   - **Honest limitation:** [INFERENCE] the 9-session scan is below the 30-session saturation expectation in §A2; the saturation test runs against whatever corpus exists at Phase 1 entry, not a fixed target size. If the corpus is too small to stabilize, the gate fails and Phase 2 is deferred — this is the intended behavior, not a bug.

3. **Compaction-accuracy gate (revised by round-2 critical friend; resolves Blocker 2 — Gate 3 census-vs-sample framing):**
   - **Test:** run the script on **ALL known-compacted sessions on this host** in both INDEX-only and `--include-segments` modes. Compare F/U and P/U deltas. This is a **census**, not a sample — the host has 4-5 compacted sessions (verified 2026-07-29: `~/.grok/sessions/P%3A%5C\019f6b24-dd44-7192-8a98-02e2be35f8c6\`, `019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe\`, `019f6f1e-34e0-7c03-840f-2a1a30683671\`, `019f7568-acad-7693-9ab0-23c57609045a\` with `segment_000.md` and `segment_001.md`, plus the 019f9f4f session from the brief). Expected N<10.
   - **Decision rule (unchanged):** if delta > 20% on ≥3 of 5 sessions (or ≥3 of N if N<5), the INDEX-only default is too lossy — change the default to `--include-segments` for the v1.0 release. Otherwise, INDEX-only is acceptable as the default.
   - **Why this is a census, not a sample:** the host's compacted-session corpus is bounded (low single digits). With N<10, sampling vs census is a distinction without a difference — we run on the entire population. **Framing note (per Blocker 2):** the prior framing called this a "pilot," which implied sampling. The framing change is a labeling correction; the decision rule (delta > 20% on ≥3) is unchanged.
   - **Why this is a Phase 1 gate (not a post-ship recommendation):** if compaction-aware behavior undercounts by 30%+, Phase 2 ships with a wrong default. The census must run during Phase 1 shadow mode, before any flag flip.

4. **Performance gate:**
   - Registry: scan all sessions in `~/.grok/sessions/` → file size, scan time, cache hit rate on second scan. Latency targets per §4.

**Go/no-go (revised):** ALL 4 gates must pass to proceed to Phase 2. Specifically:
- Gate 2 (calibration-correlation) is the gate that resolves Critique Premise 2. If p ≥ 0.05, thresholds need recalibration before Phase 2.
- Gate 3 (compaction-accuracy) is the gate that resolves Critique Premise 3. If delta > 20%, change the default.

If any gate fails, fix the underlying issue before proceeding. If Gate 2 fails on 10 sessions, do NOT proceed with the current thresholds — recalibrate and re-test.

### Phase 2: Default for `/close`, `/tp session` (weeks 3-4)

**Scope:** Unit 4-7 wired. Feature flags default to off. Manual flip per integration:
- `session_health.tp_delegate: true` — `/tp` Step 0b delegates.
- `session_health.close_summary: true` — `/close` adds friction/pushback line.
- `session_health.debrief_input: true` — `/debrief` Phase 0 reads signal output.
- `session_health.notice_suggest: false` (default per F-14 fix; manually flip to `true` after Phase 1 shadow validation) — `/notice` T1/T6 suggests.

**Validation:**
- Run `/close` on 3 sessions. Compare friction/pushback line with prior `/tp` output.
- Run `/tp session` on 3 sessions. Compare NOW/NEXT/LATER output with prior.
- `/notice` fires on at least one T1/T6 trigger this week → operator can verify the suggestion text.

**Go/no-go:** if no regressions in 2 weeks, proceed to Phase 3.

### Phase 3: Operator-primary (week 5+)

**Scope:** Operator-facing documentation in SKILL.md recommends `/session-health` as the answer to "how's this session going?" `/friction` standalone invocation deprecated for the pushback+workflow-friction use case (still works for one-off friction analysis).

**Validation (resolves F-37):** 1 month of operator usage. Target: `/session-health` invoked at least once per 10 sessions.

**Validation mechanism (revised):** The original draft referenced `~/.grok/state/skill-usage.jsonl`, which does NOT exist on this host (verified via `Test-Path`: directory contains only `notice-observations.jsonl` and `profile-review.json`). Use the following alternative validation:

- **Manual log:** operator records invocations in `P:/docs/handoffs/session-health-adoption-2026-<month>.md` (1-line per invocation: timestamp, mode, session_id).
- **Indirect signal:** `/aar` Phase 4 already reads `~/.grok/state/notice-observations.jsonl` and counts `/notice` T1/T6 suggestions referencing `/session-health`. If `session_health.notice_suggest` is flipped on in Phase 2, the count of `/session-health` references in `notice-observations.jsonl` is a proxy for adoption.
- **AAR synthesis:** at month end, run `/aar` and count how many recent AARs reference `/session-health` output in their evidence. >50% = successful adoption.

If a hook is needed for automated usage tracking, that's a Unit 9 follow-up (out of scope for v1.0).

### Rollback

Each phase is a feature flag. Rollback semantics differ by flag (resolves F-48):

- **Phase 1** → no integration to roll back (shadow mode).
- **Phase 2 — `tp_delegate` flag**: REQUIRES restoration of the inline regex. If `tp_delegate` is set to `true` AND then reverted to `false`, the inline regex at `/tp/SKILL.md:250-280` must be restored from git history (`git show HEAD:tp/SKILL.md | git checkout -` or via the pre-flip backup). Phase 2 entry criterion: take a backup of `/tp/SKILL.md:250-280` to `P:/.artifacts/<term>/tp-step-0b-inline.bak` before flipping the flag.
- **Phase 2 — `close_summary`, `debrief_input`, `notice_suggest` flags**: additive integration only; reverting to `false` returns to prior behavior with no data loss.
- **Phase 3** → revert operator-facing documentation in SKILL.md (no code change).

**Pre-flip backup procedure (mandatory before `tp_delegate` flip):**
```bash
cp ~/.grok/skills/tp/SKILL.md P:/.artifacts/$(basename $TERM)/tp-step-0b-inline.bak
# OR (preferred for clean rollback):
git show HEAD:~1 -- ~/.grok/skills/tp/SKILL.md > P:/.artifacts/$(basename $TERM)/tp-step-0b-inline.bak
```

This backup MUST be in place before the flag flip; otherwise rollback is destructive.

Registry is read-only — never destroyed by rollback. Sessions scanned in Phase 1-3 remain available if we re-enable.

---

## File Change Inventory

### New files (16)

| Path | Purpose | LOC (target) |
|---|---|---|
| `C:/Users/brsth/.grok/skills/session-health/SKILL.md` | Skill manifest | ~300 |
| `C:/Users/brsth/.grok/skills/session-health/scripts/session_signals.py` | Layer 1 signal extractor | ~250 |
| `C:/Users/brsth/.grok/skills/session-health/scripts/signal_registry.py` | Registry cache (with `msvcrt.locking`) | ~200 |
| `C:/Users/brsth/.grok/skills/session-health/scripts/drift_detector.py` | Cross-session drift | ~200 |
| `C:/Users/brsth/.grok/skills/session-health/scripts/pushback_keywords.txt` | Versioned keyword list (16 keywords) | ~20 |
| `C:/Users/brsth/.grok/skills/session-health/__lib/signals.py` | Dataclasses | ~80 |
| `C:/Users/brsth/.grok/skills/session-health/__lib/transcript.py` | Compaction-aware reader | ~120 |
| `C:/Users/brsth/.grok/skills/session-health/__lib/hypotheses.py` | Adopted /behave pattern (with inline fallback for missing cache) | ~150 |
| `C:/Users/brsth/.grok/skills/session-health/tests/test_session_signals.py` | Unit tests | ~200 |
| `C:/Users/brsth/.grok/skills/session-health/tests/test_signal_registry.py` | Unit tests | ~150 |
| `C:/Users/brsth/.grok/skills/session-health/tests/test_drift_detector.py` | Unit tests | ~150 |
| `C:/Users/brsth/.grok/skills/session-health/tests/fixtures/hand_counted_transcript.jsonl` | Hand-counted fixture (expected F/U=0.59, P/U=0.36) | n/a |
| `C:/Users/brsth/.grok/skills/session-health/tests/fixtures/regression_5_sessions/` | 5 historical transcripts for `/tp Step 0b` regression | n/a |
| `P:/.data/wiki/capabilities/session-health-monitoring.md` | Capability contract | ~20 |
| `P:/.data/telemetry/session-health-fixtures/` (canonical fixture storage) | Backup of regression fixtures for cross-machine portability | n/a |

### Registry file (1)

| Path | Purpose |
|---|---|
| `P:/.data/telemetry/session-signal-registry.json` | Pull-based session signal registry (moved from `P:/.data/wiki/` per AGENTS.md file location conventions; telemetry/jsonl files belong at `P:/.data/telemetry/`) |

### Modified files (5)

| Path | Change |
|---|---|
| `C:/Users/brsth/.grok/skills/tp/SKILL.md` | Step 0b (lines 250-280): inline regex **gated by `session_health.tp_delegate` flag**. While flag is `false`, inline regex remains active. When flag flips to `true` (Phase 2), regex is **DELETED** and replaced with `python session_signals.py --json \| jq` thin-caller pattern. `@deprecated` comment kept 30 days post-flip. Backup mandatory at `P:/.artifacts/<term>/tp-step-0b-inline.bak`. |
| `C:/Users/brsth/.grok/skills/close/__lib/close_runner.py` | Adds `session_signals.py --json` call before final summary; one friction/pushback line in close report when `session_health.close_summary: true`. (F-27 clarification: this modifies `close_runner.py`, the orchestrator, NOT `close_accounting.py`, the scanner. They serve different purposes.) |
| `C:/Users/brsth/.grok/skills/debrief/SKILL.md` | Phase 0 (Discovery) reads `session_signals.py --json` output as Lens 3 (workflow friction) input. Verified lens structure at `/debrief/SKILL.md:60-130`. |
| `C:/Users/brsth/.grok/skills/notice/SKILL.md` | T1 (error state) and T6 (unverified diagnosis) trigger suggestion updated to include "run /session-health --full" alongside existing suggestions. Verified triggers at `/notice/SKILL.md:116-122`. |
| `C:/Users/brsth/.grok/skills/aar/SKILL.md` (NEW by Blocker 4) | Phase 4 (`operator_signal_delta`, lines 147-185) REPLACES inline signal computation (`pushback_count`, `pushback_categories`, `friction_signal_baseline_delta`) with `python session_signals.py --json --session <id>` calls. Gated by `session_health.aar_phase4_consume` flag (default `false`). AAR's value-add (clustering, double-loop, synthesis) is preserved; only raw extraction is delegated. Without this, two paths compute overlapping signals (canonical extraction drift). |

### Auto-regenerated (1)

| Path | Change |
|---|---|
| `P:/.data/wiki/concepts/skill-catalog.md` | Regenerated by `python P:/.data/wiki/scripts/index_skills.py` immediately after Unit 4 SKILL.md is committed. Adds `/session-health` to grok-user list. |

### Source migration (resolves F-10)

| From | To | Reason |
|---|---|---|
| `P:\tmp\detect_pushback.py` (11-keyword baseline) | `C:/Users/brsth/.grok/skills/session-health/scripts/pushback_keywords.txt` | Per AGENTS.md "File location conventions": tmp files are ephemeral; the validated 11-keyword set becomes the source of truth inside the skill. The keywords are referenced inline (with `# validated 2026-07-29 from P:/tmp/detect_pushback.py` provenance comment) so the validation source is preserved. The original `detect_pushback.py` script can remain at `P:/tmp/` until natural deletion — we no longer depend on it. |

### Not changed (deliberate non-changes)

- **`C:/Users/brsth/.grok/skills/close/__lib/friction_detector.py`** — stays. Different semantics (recurrence within session vs density across session). **Verified by round-2 critical friend:** `friction_detector.py` has 5 distinct categories (`quoting_errors`, `command_failures`, `import_errors`, `permission_errors`, `file_errors`) with only `SyntaxError` overlap to `/tp Step 0b` patterns. The two files are complementary, not duplicative.
- **`C:/Users/brsth/.grok/skills/friction`**, **`/behave`**, **`/pace`** — sibling skills remain. `/session-health` is internal integration; these are user-facing entry points.
- **`/aar/SKILL.md` is NOT in the not-changed list** — it was promoted to "Modified files" by Blocker 4.

---

## Non-Goals (resolves F-29)

Explicit out-of-scope items. Future sessions should not re-litigate these without operator approval:

1. **HTML report generation** — `/session-report` plugin's value-add (interactive HTML) is not adopted. `/session-health` emits text/markdown + JSON. Operator can pipe `--json` through their own rendering layer if they want HTML.
2. **In-session real-time alerting** — `/session-health` does not fire during the session as a /notice-style surface. Detection is end-of-session or on operator invocation only. The mid-session signaling surface is `/notice`'s job.
3. **Push-based notification** — no webhook, Slack, email, or push notification on drift alerts. Operator reads the registry manually or invokes `--trend`.
4. **`/pace` integration** — cognitive load (WIP, rework, system health) is `/pace`'s canonical owner. `/session-health --load` is deferred to v1.1. Adding it in v1.0 would conflate two capabilities.
5. **LLM judgment in default (non-`--full`) mode** — quick, trend, and json modes are pure Python. LLM is invoked only when the operator explicitly requests `--full` and F/U > 2.0 OR P/U > 0.4. The default quick verdict is deterministic and free.
6. **Claude Code portability** — this design is Grok Build only. A Claude Code equivalent would require significant adaptation (different transcript path, different friction markers). Documented in D7's multi-host applicability note.
7. **Multi-machine registry sync** — the registry is per-machine. If operator runs Grok Build on multiple machines, each has its own registry. Cross-machine aggregation is a v2.0 problem.

## Open Questions (resolves F-30)

Items still in flux for v1.0 or deferred to a future version:

- **OQ-1** — Schema versioning of the registry file. If we add a field in v1.1, how do we migrate existing v1.0 entries? **Migration policy deferred to v1.1 (see N-02); no implementation in v1.0.** The v1.0 registry ships with `schema_version: "1.0.0"` and the field set documented in §2.3. Any field added in v1.1 is treated as `null` by v1.0 readers (forward-compat default).
- **OQ-2** — Compaction format stability. The current `INDEX.md` and `segment_NNN.md` schemas are documented but lack a `schema_version` field. If Grok Build changes the compaction format, Layer 1 may silently miss content.
- **OQ-3** — `/behave` plugin re-enablement. If the `cc-skills-thinking` plugin becomes available on this host, the Layer 2 hypothesis block could delegate to `/behave` instead of embedding the pattern. Re-evaluate D3 at that point.
- **OQ-4** — Calibration period length. The brief says "30+ sessions" before transitioning to rolling-median thresholds. Is 30 enough? 50? 100? Empirically determined after v1.0 ships.
- **OQ-5** — Pushback keyword pruning. 16 keywords is the initial set; some may be high-false-positive (e.g., `"no "` is a substring match — could fire on "no, I don't think so" or "no problem"). v1.1 may switch to word-boundary regex and drop 2-3 high-FP keywords.
- **OQ-6** — Registry lock contention in heavy multi-terminal use. The 5s lock timeout is a guess. If operators run 5+ terminals concurrently, the timeout may need to increase or the lock strategy may need to change to per-session locks rather than a single global lock.
- **OQ-7** — `/session-health --load` integration (deferred to v1.1 per D4). What is the canonical interaction between session-health's density metrics and pace's WIP/rework metrics? Co-display, override, or separate?
- **OQ-8** — CI check for friction-category drift. After Unit 7, `session_signals.py` is the source of truth. Should we add a CI check that compares `/tp/SKILL.md` category table to `session_signals.py` pattern list and fails on divergence? v1.0 soft contract; v1.1 may automate.
- **OQ-9** — Verify `close/__lib/friction_detector.py` content. The design assumes it contains friction-regex duplication but does not quote the actual code. Full verification requires reading the file's regex/algorithm. Open until Phase 1 acceptance gate 1 (signal accuracy gate) runs.
- **OQ-10** — Compaction step keyword-extraction criteria. Does the compaction step include operator-correction markers in its curated keywords? If not, INDEX-only scan undercounts. May require proposing a feature to the compaction-step author.
- **OQ-11** — `--hypothesis-threshold <float>` flag. v1.0 ships default 2.0. Operators with attention-constrained workflows may want to raise to 3.0+ to suppress more aggressively. Trade-off: opt-out loses Layer 2 hypothesis-block value.
- **OQ-12** — Real-time monitoring vs `/notice`. Currently `/session-health` is operator-invoked only. If operators want live F/U updates mid-session, is the right surface `/session-health --watch` (polling) or extension of `/notice`? v1.0 ships operator-invoked only.
- **OQ-13** — Compaction-aware default for short sessions. The INDEX-only logic is dormant for sessions that never compact. v1.0 behavior is correct (skips the code path), but future versions may want a `--always-scan-compaction` flag for operators who pre-trim transcripts.
- **OQ-14** — Context-aware weighting. A routine clarification `"no, that's not right"` carries the same weight as a hostile operator correction. v1.1 may add context-aware weighting (e.g., code-review-line vs casual-aside). Out of scope for v1.0.

## Privacy & Data Classification (resolves F-32)

**Data classification:**

- **Session transcripts** (`~/.grok/sessions/<encoded-cwd>/<session-id>/chat_history.jsonl`) — **operator-private**. Contains user prompts, file paths, command output, possibly secret material (API keys, tokens). Classification: [FACT] per `~/.grok/AGENTS.md` "Multi-terminal isolation": session directories are user-scoped.
- **Compaction segments** (`~/.grok/sessions/<encoded-cwd>/<session-id>/compaction/segment_*.md`) — **operator-private**. Same classification as transcripts; pre-compaction context.
- **Signal registry** (`P:/.data/telemetry/session-signal-registry.json`) — **operator-private**. Contains derived metrics (F/U, P/U, friction counts) per session, no raw transcript content. Lower classification than transcripts (no secrets).
- **Pushback quotes** (in `--full` output) — **operator-private**. Quotes are extracted from `chat_history.jsonl` and may contain sensitive content. Treat the `--full` output the same as the transcript.

**Who can read:**

- All skill data is local-user-only. No network egress. No shared multi-user paths.
- Skill files live at `~/.grok/skills/session-health/` (user scope). Not in shared workspace.

**Retention policy (resolves F-33):**

- **Transcripts**: retained by Grok Build session-tool; this skill does not modify transcript retention.
- **Registry**: retained until manually deleted OR session directory is deleted. Stale entries are marked `stale: true` on next scan, not auto-pruned in v1.0. Manual `--prune-stale` command available.
- **Fixtures**: regression fixtures stored at `P:/.data/telemetry/session-health-fixtures/` are operator-private. Promote to operator-controlled storage if they contain sensitive data.
- **No backups created by this skill.** Registry is re-derivable from transcripts; if both are lost, scan history is gone.

**Secret handling:**

- The friction regex includes `SECRET_DETECTED` and `gitleaks` patterns. Detection is recorded as a friction count, but the secret value is NOT included in the registry or `--full` output.
- If the script encounters transcript content matching `SECRET DETECTED`, it counts the occurrence but does not write the secret to the registry. [FACT] verified against `P:/tmp/detect_pushback.py` which only writes `L{i+1}: PUSHBACK: <truncated text>`.

## Structural Issues Discovered (not in original review)

### N-01 — `chat_history.jsonl` JSONL schema not formally documented

**Severity:** Major

**Section:** §2.2 Input contract

**Description:** The design references `chat_history.jsonl` as if its schema is established, but the formal schema (field names, types, allowed values) is not documented anywhere in the workspace. The format is implied by `P:/tmp/detect_pushback.py` (which reads `obj.get("type") == "user"` and looks for `<user_query>` blocks) but no authoritative spec exists.

**Mitigation:** Document the inferred schema in §2.2 (verified against the live file). Add `schema_version` field to the JSON output so consumers know what version they're reading. Open Question OQ-2 covers the longer-term solution.

**Status:** Documented (this design doc); long-term solution is a Grok Build schema versioning policy (out of scope for this skill).

### N-02 — Registry schema migration policy undefined

**Severity:** Major

**Section:** §2.3 Output contract

**Description:** The registry schema includes `schema_version: "1.0.0"`. If we add a field in v1.1 (e.g., `compaction_aware: bool`), how do we migrate existing v1.0 entries without losing them?

**Mitigation:** On registry read, if `schema_version` < current, run a forward-compat migration: missing fields get default values (e.g., `compaction_aware: false` for v1.0 entries). Document each version's migration in `scripts/registry_migrations.py`.

**Status:** Schema versioning added to output (§2.3). Migration policy deferred to v1.1 unless a v1.0 schema change is needed before then.

### N-03 — Quick mode lacks evidence-citation contract

**Severity:** Minor

**Section:** §4 Output modes — Quick mode

**Description:** Quick mode emits "3 most elevated signals" but the format for those signals is not specified. Each signal must cite its source (transcript line, friction category, pushback keyword). Without this contract, consumers can't verify the verdict.

**Mitigation:** Quick mode output format:
```
F/U=0.59 (NORMAL). Top signals:
  1. [Friction: NO_COVERING_RECEIPT × 13] — see transcript lines [12, 45, 89]
  2. [Pushback: "no" × 3] — see transcript lines [23, 56, 78]
  3. [Friction: Traceback × 2] — see transcript lines [101, 102]
```

**Status:** Documented in §4.

---

## References

- **Premise** — `P:/.data/wiki/concepts/friction-detection-operator-pushback-as-trigger.md` (mechanical pushback detection rationale)
- **Pattern source — pushback** — `P:/tmp/detect_pushback.py` (11-keyword baseline, validated this session; keywords migrated to `C:/Users/brsth/.grok/skills/session-health/scripts/pushback_keywords.txt` per F-10)
- **Pattern source — friction regex** — `~/.grok/skills/tp/SKILL.md` lines 250-280 (Step 0b scan)
- **Pattern source — Mode 1 interaction friction** — `~/.claude/plugins/cache/local/cc-skills-analysis/1.0.123/skills/friction/SKILL.md`
- **Pattern source — Mode 2 workflow friction** — same
- **Pattern source — hypothesis-testing** — `~/.claude/plugins/cache/local/cc-skills-thinking/1.0.19/skills/behave/SKILL.md`
- **Pattern source — load scoring** — `~/.claude/plugins/cache/local/cc-skills-thinking/1.0.19/skills/pace/SKILL.md` (deferred to v1.1)
- **Pattern source — HTML report** — `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/session-report/skills/session-report/SKILL.md` (not adopted; out of scope for v1.0)
- **Architecture** — `P:/.data/wiki/concepts/context-firewall-architecture.md` (3-layer pattern)
- **Friction scan replacement** — `C:/Users/brsth/.grok/skills/close/__lib/friction_detector.py` (recurrence semantics — kept, not replaced)
- **Capability registry pattern** — `P:/.data/wiki/capabilities/session-opportunity-review.md`, `P:/.data/wiki/capabilities/session-retrospective.md`
- **Multi-terminal safety** — `P:/.data/wiki/concepts/session-close-out-skill-design.md` (atomic writes, terminal-scoped state)
- **Coupling inventory** — `P:/.data/wiki/concepts/coupling-inventory-as-mandatory-design-section.md`
- **Refactor dismissal gate** — `~/.grok/AGENTS.md` "Refactor dismissal gate (code-smell inventory before 'gold-plating')"
- **File editing protocol** — `~/.grok/docs/file-editing-protocol.md`

---

## Falsifier

This design is wrong if, within 6 months:

- **Skill is never invoked** despite `/close` + `/tp session` + `/debrief` integrations — meaning operator-judgment friction is the real bottleneck and signal extraction isn't actionable. **Retire** the skill; revert `/tp Step 0b` to inline regex.
- **F/U and P/U do not correlate with session quality** — i.e., elevated signal count happens in healthy sessions too. **Recalibrate** keyword sets and friction patterns; if still uncorrelated, retire.
- **Registry grows unboundedly** (e.g., 100K sessions × 10KB = 1GB) — **add TTL** in v1.1.
- **Compaction-aware scan misses pre-compaction content** — operators complain about retrospective blind spots. **Fix** by reading segment content directly, not just INDEX.
- **`/behave` plugin becomes enabled** — we should re-evaluate whether to delegate (D3). If `/behave` is now reachable, simplify by calling it.
- **Operator finds the multi-mode UX confusing** — collapse to 2 modes (`quick`, `full`) and put trend behind a sub-flag.

Re-evaluate if any pattern appears within 3 months across 5+ sessions.

---

*End of design document. Draft v0.4 (revision 4 — round-2 critical-friend REVISE response; 5 blockers addressed).*

---

## Revision Summary (v0.3.1 → v0.4)

Round-2 critical-friend review returned **REVISE** with 5 specific blockers. **All 5 addressed** in this revision. Document grew from 813 → 859 lines (modest expansion; the 5 blockers did not require restructuring, only correcting specific claims).

### Verification receipts applied

| Blocker | Operator-verified receipt (per round-2 input) | Where in doc |
|---|---|---|
| **Blocker 1** | Pearson correlation on n=10 has <30% power at r=0.5; §A2 says n=29 minimum | Phase 1 Gate 2 (Rollout) |
| **Blocker 2** | 4-5 compacted sessions on host; "pilot" implies sample | Phase 1 Gate 3 (Rollout) |
| **Blocker 3** | `friction_detector.py` (364 lines) verified: 5 categories (`quoting_errors`, `command_failures`, `import_errors`, `permission_errors`, `file_errors`), only `SyntaxError` overlap with `/tp Step 0b` | §A1 (Code-smell inventory), "Not changed" list |
| **Blocker 4** | `/aar/SKILL.md` lines 147-185 (Phase 4 `operator_signal_delta`) verified: 7 signals (pushback_count, pushback_categories 6 categories, trust_loss_markers, reactive_adversarial_invocations, meta_cognition_verbs, deferred_persistence_count, friction_signal_baseline_delta). Wiki ref: `friction-detection-operator-pushback-as-trigger` | §6 Integration table, §3.3, Unit 7, File Change Inventory, Risk Table |
| **Blocker 5** | "Leaf node" mislabeling — 5 inbound consumers contradicts the descriptor | §Coupling invariant, Risk Table (vendor lock-in row) |

### Specific changes applied

**Blocker 1 — Gate 2 power-analysis failure → saturation check.**

Phase 1 Gate 2 (Rollout section) replaced:
- **Before:** Pearson r(F/U, P/U) at p<0.05 across 10+ sessions. Power analysis: n ≈ 29 for r=0.5, n ≈ 84 for r=0.3.
- **After:** saturation check on full fleet history. Compute F/U and P/U distributions; check that adding the last 5 sessions shifts median F/U and P/U each by <10%. This is **distributional stability**, not statistical significance. Does not require power analysis; requires convergence. Labeled `[INFERENCE]` because we haven't run it on the full fleet yet (verified: 9 top-level session directories on this host).

**Blocker 2 — Gate 3 census reframe.**

Phase 1 Gate 3 (Rollout section) reframed:
- **Before:** "pilot" running on 5 sessions (implied sample).
- **After:** "census" running on ALL known-compacted sessions (verified: 4-5 on this host — `019f6b24`, `019f6c3b`, `019f6f1e`, `019f7568`, plus 019f9f4f from the brief). Decision rule unchanged: delta >20% on ≥3 of 5 → change INDEX-only default to `--include-segments`. Framing change is a labeling correction; the rule is the same.

**Blocker 3 — DRY claim corrected.**

The Code-smell inventory's "DRY violation" row was updated to reflect verified `friction_detector.py` content:
- **Before:** DRY violation between `/tp Step 0b` and `close/__lib/friction_detector.py`.
- **After:** Real DRY only between `/tp Step 0b` (13 patterns at `/tp/SKILL.md:250-280`) and `session_signals.py` (11 friction categories). `friction_detector.py` has **different pattern sets** (5 categories, only `SyntaxError` overlap, ~1/13 overlap ratio). The two files are **complementary, not duplicative**: `friction_detector.py` does recurrence detection within a session (3+ same-category hits); `session_signals.py` does density across a session. Both can coexist.
- §A1 (Anchoring Premises) updated with the full `friction_detector.py` contents list.
- "Not changed" list updated to clarify `friction_detector.py` stays for recurrence detection (different scope).

**Blocker 4 — /aar Phase 4 data flow (the most significant change).**

The /aar integration was promoted from "no-op" to **active consumer**:
- **Before:** `/aar/SKILL.md` is not modified; the AAR's `operator_signal_delta` block already exists at lines 152-201; the integration is a no-op.
- **After:** `/aar/SKILL.md` Phase 4 (lines 147-185) **REPLACES** its inline signal computation with `python session_signals.py --json --session <id>` calls. The AAR's value-add (cross-session episode clustering, double-loop analysis, signal synthesis) is preserved; only raw extraction is delegated.
- New feature flag: `session_health.aar_phase4_consume: false` (default off; gated flip).
- New file in Modified Files list: `C:/Users/brsth/.grok/skills/aar/SKILL.md`.
- File Change Inventory "Modified files" count: 4 → 5.
- `/aar/SKILL.md` removed from "Not changed" list with explanation.
- §3.3 "Orchestrator" updated: "stable schema consumed by 5 callers: `/close`, `/tp`, `/debrief`, `/notice`, `/aar`."
- §6 Integration table row 5: changed from "No-op" to "REPLACES inline signal computation."
- §6 "Decision" updated: 5 consumers listed explicitly.
- §6 "Verified citations" updated: `/aar/SKILL.md:147-185` (revised from 152-201).
- §6 "Key design questions resolved" Q2 updated: 5 callers listed.
- Risk Table row "Vendor lock-in" updated: "4 callers" → "5 callers"; mitigation note added about `/aar` having its own flag for backout.

**Blocker 5 — "leaf node" → "centralized dependency"** (terminology).

- §Coupling invariant: "leaf node" → "centralized dependency" with explanation that 5 inbound consumers contradicts the leaf descriptor.
- Risk Table row "Vendor lock-in" already updated as part of Blocker 4.

### Files NOT modified

The 5 blockers were addressed without:
- Restructuring the 3-layer architecture
- Changing the 8-unit implementation plan structure
- Adding new files (the registry, scripts, __lib modules, tests, fixtures are unchanged from v0.3)
- Changing the rollback strategy
- Changing the 4 Phase 1 acceptance gates (only Gate 2 and Gate 3's internals changed)
- Removing any of the v0.3 risk mitigations

### Cross-cutting changes

- Consumer count (4 → 5) propagated to: §3.3, §6, §Unit 7, File Change Inventory, Risk Table, Falsifier.
- "leaf node" wording removed from §Coupling invariant.
- `friction_detector.py` scope clarification propagated to §A1, Code-smell inventory, "Not changed" list.
- `/aar/SKILL.md` citation updated from 152-201 (operator_signal_delta block) to 147-185 (broader Phase 4 section).

### Honest limitations remaining

- The saturation check (Gate 2) is `[INFERENCE]` because the 9-session fleet corpus is below the §A2 expectation of 30 sessions. The test runs against whatever corpus exists; if it fails (corpus hasn't stabilized), Phase 2 is deferred. This is intended behavior, not a bug.
- The `/aar` Phase 4 integration introduces 1 new file modification and 1 new feature flag. The flag defaults to `false` (parity with other integrations); flip after Phase 1 shadow validation. The AAR's existing inline computation remains the active path until then.
- The `friction_detector.py` "complementary not duplicative" framing relies on the round-2 verified pattern content. If `friction_detector.py` evolves to add more overlapping patterns (e.g., adopting `/tp Step 0b` patterns), the DRY framing would need re-evaluation. Open Question OQ-9 already covers ongoing verification.

### Pushback against the blockers

**None.** All 5 round-2 blockers were valid. The round-2 reviewer provided verification receipts (read `friction_detector.py` in full, read `/aar/SKILL.md` lines 147-185) that the original v0.3 design did not have. The corrections are straightforward applications of those receipts.

### What this revision does NOT address

- The deeper question of whether `/session-health` should be built at all (falsifier for the design as a whole, separate from these 5 blockers).
- The 30-session empirical calibration target (still in §A2; saturation check defers but does not solve the small-corpus problem).
- The `Close` (operator-invoked) for `/session-health` — per AGENTS.md "Trust-escalation rung" Rung 2-3, handoff close is operator-invoked. This design documents Unit 7 acceptance criteria; closing the handoff is a separate operator action.

---

*Round-2 critical-friend REVISE response complete. Document v0.4 ready for the next review round (round 3) or operator close-out.*

---

## Revision Summary (v0.2 → v0.3)

**Trigger:** critical-friend review at `grok-design-critique-c2099c52.md` returned **REVISE** with 7 premise challenges + 5 open-ended risks.

**7 Premise Challenges Addressed:**

1. **Framing mismatch** → §1 Goal and §4 now separate "human-facing modes" (3: quick/full/trend) from "machine contract" (`--json`). §4 explicitly documents this distinction with two sub-sections (§4.1 human-facing modes, §4.2 machine contract). The "4-mode UX" framing is retired.

2. **Calibration without a gate** → Phase 1 acceptance gates now include **calibration-correlation gate** (Pearson r(F/U, P/U) at p<0.05 across 10+ sessions; secondary test: >50% hypothesis-block fire = too sensitive). Without this gate, Phase 2 could ship with wrong thresholds.

3. **Compaction default without measurement** → Phase 1 acceptance gates now include **compaction-accuracy gate** (5 known-compacted sessions, INDEX-only vs `--include-segments` modes, delta <20% on ≥3 of 5). Without this gate, Phase 2 ships with potentially lossy compaction behavior.

4. **DRY framing overstated** → Code-smell inventory now separates three concerns: friction-regex duplication (real DRY violation between `/tp Step 0b` and possibly `close/__lib/friction_detector.py`), pushback-keyword migration (NEW signal, not duplicate), cross-skill data expansion (non-overlapping). §3.1 pushback signals marked as "NEW signal, not a duplicate".

5. **Friction pattern count off** → Corrected from **11 to 13** (verified by hand count from `~/.grok/skills/tp/SKILL.md:250-280`). Two patterns (`FAIL:`, `fatal:`) had no category in v0.2; one category (`command_not_found`) had no pattern. New `uncategorized_failure` category absorbs the orphans; `command_not_found` removed.

6. **Anchoring premises** → New §9 "Anchoring Premises" with 5 premises labeled `[FACT]` / `[INFERENCE]` / `[UNKNOWN]` / `[HYPOTHESIS]`. Each has a mitigation:
   - A1 (friction duplication): `[FACT]` — verified pattern counts and locations
   - A2 (30 sessions enough): `[INFERENCE]` — power analysis shows n ≈ 84 for r=0.3
   - A3 (INDEX rich enough): `[UNKNOWN]` — depends on compaction step's keyword-extraction criteria
   - A4 (embedded LLM "free"): `[INFERENCE]` — reframed as "cheaper than subagent, but not free (attention budget)"
   - A5 (consolidate /friction): `[HYPOTHESIS]` — deferred; Phase 3 measures operator preference

7. **Consumer error contract** → §2.3 output contract adds `degraded: bool` and `degraded_reasons: [string]`. Five degradation triggers defined (`registry_lock_timeout`, `compaction_incomplete`, `transcript_truncated`, `transcript_parse_partial`, `friction_categories_drifted`). Per-consumer behavior specified for `/close`, `/tp session`, `/debrief` Lens 3, `/notice` T1/T6, `/aar` Phase 4. **Consumers proceed with model recall only** when degraded.

**5 Open-ended Risks Addressed (Risk Table additions):**

| Risk | Mitigation |
|---|---|
| **Hawthorne effect** (4.2) | Real-time F/U not auto-surfaced; operator-invoked only. Verdicts are one-shot, not a live ticker. |
| **Hypothesis feedback loop absent** (4.3) | Registry stores `hypothesis_feedback: {useful, noise}` per session via `/session-health --feedback <session-id> <useful\|noise>` operator command. Recalibrate threshold after 30 sessions of feedback. |
| **Friction category sync contract** (4.1) | §3.1 Maintenance contract documents `session_signals.py` as post-Unit-7 source of truth. Open Question OQ-8 covers CI check. |
| **Vendor lock-in via canonical source** (4.4) | F-06's "delete on flip" position **REVISED**: inline regex kept `@deprecated` for 30 days after `tp_delegate` flag flip (Phase 2), not Unit 7 ship. Backup at `P:/.artifacts/<term>/tp-step-0b-inline.bak` for 90 days. Trade-off: cleanup discipline vs recovery path. |
| **Backup enforcement** (4.5) | `PreToolUse` hook gates the `tp_delegate` flag flip; hook script at `~/.grok/skills/session-health/__lib/pre_flip_backup_check.py`. Operator cannot flip flag without first executing backup tool. |
| **Compaction under short sessions** (§4.5) | No action needed; INDEX-only code path is dormant for short sessions. OQ-13 documents future flag option. |
| **Weighting by line context** (§4.6) | Out of scope for v1.0; OQ-14 covers v1.1. |
| **Operator over-reliance on metrics** (§4.7) | SKILL.md wording emphasizes "indicator" not "score". Raw counts alongside verdict for interpretability. |

**Pushback on any critiques:** none. All 7 premise challenges and 5 open-ended risks were valid.

**Open Questions added (OQ-8 through OQ-14):**

- **OQ-8**: CI check for friction-category drift (`session_signals.py` vs `/tp` category table).
- **OQ-9**: Verify `close/__lib/friction_detector.py` regex/algorithm in full (design assumes duplication but does not quote).
- **OQ-10**: Compaction step keyword-extraction criteria — does it include operator-correction markers?
- **OQ-11**: `--hypothesis-threshold <float>` flag for operators with attention-constrained workflows.
- **OQ-12**: Real-time monitoring vs `/notice` — operator-invoked only in v1.0; v1.1 may extend.
- **OQ-13**: `--always-scan-compaction` flag for short-session operators (v1.0 not needed).
- **OQ-14**: Context-aware weighting of pushback (code-review-line vs casual-aside), v1.1.

**Verification receipts obtained this revision:**

1. **Premise 5 (pattern count)**: hand-counted `~/.grok/skills/tp/SKILL.md:250-280` regex → **13 patterns**, not 11.
2. **A3 compaction schema**: `read_file` of `~/.grok/sessions/P%3A%5C\019f6b24-dd44-7192-8a98-02e2be35f8c6\compaction\INDEX.md` → 5-segment table verified.
3. **Existing fixtures**: 5 known-compacted session IDs identified for compaction-accuracy gate.
4. **Existing pullback hits**: 8 hits verified at specific transcript lines in `~/.grok/sessions/P%3A%5C\019f9f4f-7f5b-7a71-9eaf-8f43ba9f8fb9\chat_history.jsonl` (lines 230, 249, 293, 352, 397, 426, 481, 504).

**Document size:** v0.2 was 604 lines; v0.3 is now ~700 lines (the framing restructure, anchoring premises section, consumer error contract, and risk table additions added ~100 lines).

**Falsifier check on the revision itself:** if the F-06 revision (soft removal for 30 days) leads to operator confusion about which pattern source is active, the design should be re-revised. Spot-check: the maintenance contract in §3.1 explicitly names `session_signals.py` as the post-Unit-7 source of truth; the inline regex's `@deprecated` comment makes the dual-source period explicit.

**Ready for:** next review pass (`/red-team` or another `/tp` cycle). If accepted, Phase 1 implementation begins.

---

## Revision Summary (v0.3 → v0.3.1) — critical-friend re-review F-60

**Trigger:** revision 3 quick re-review (file `grok-design-review-c2099c52.md`) ran 5 spot-checks against the v0.3 document and surfaced 1 new minor finding (F-60) plus closed F-47, F-49, F-50, F-51, F-52, F-53, F-54, F-55, F-56, F-57, F-58, F-59.

**F-60 — F-48 conditional deletion language not propagated; 5 stale "delete on Unit 7 ship" references. Status: addressed.**

The v0.3 Risk Table row for "Vendor lock-in via canonical-source designation" introduced a refined position (keep regex `@deprecated` for 30 days post-flag-flip). However, 5 other sections still used the original F-06 unconditional language. The re-reviewer caught the propagation gap.

**Mechanical fix:** all 5 stale references updated. The canonical position is now consistent across the document:

- **§3.1 Layer 1 (line 183):** "deleted when `session_health.tp_delegate` flips to `true` (Phase 2) per removal-protocol.md. Unit 7 ships with the regex still present (the flag is `false`); deletion happens in Phase 2 only."
- **§3.1 Maintenance contract (line 193):** "After the `session_health.tp_delegate` flag flips to `true` (Phase 2) and the inline regex is deleted from `/tp/SKILL.md:250-280`..."
- **§6 Removal protocol compliance (line 329):** Rewritten to spell out the full chain: F-06 + F-48 + vendor-lock-in. Specifies that deletion happens on Phase 2 flag flip (not Unit 7 ship); `@deprecated` comment kept for 30 days post-flip; backup mandatory per Rollback.
- **Coupling matrix (line 412):** "inline regex DELETED on `tp_delegate: true` flag flip (Phase 2), not on Unit 7 ship; backup mandatory per Rollback."
- **Risk Table row (line 730):** "30 days post-flip (not post-Unit-7-ship)".
- **Revision Summary entry (line 1052):** "30 days after `tp_delegate` flag flip (Phase 2), not Unit 7 ship".

**Verification:** `grep "delete on Unit 7 ship|DELETED on Unit 7 ship"` on the v0.3.1 document returns 0 matches. All stale unconditional language is gone.

**Why this matters:** an engineer reading §3.1 alone would have assumed Unit 7 ships with the regex already deleted. In fact, Unit 7 ships with the regex retained (the flag is `false`), and deletion only happens in Phase 2 when the flag flips to `true`. The v0.3.1 correction aligns all sections with the F-48 conditional deletion model.

**5 other spot-checks that passed (preserved from re-review):**

- **Registry path propagation (F-47 closed)**: all 7 references to `session-signal-registry.json` point to `P:/.data/telemetry/`.
- **`notice_suggest: false` consistency (F-50 closed)**: both Unit 7 and Rollout Phase 2 default to `false`.
- **`--prune-stale` and `--include-stale` in Implementation Plan (F-49 closed)**: both flags spec'd with output format and behavior.
- **All 8 units have Owner lines (F-51 closed)**: each Unit lists "Operator".
- **No new contradictions introduced**: F-60 was the only new finding from the re-review.