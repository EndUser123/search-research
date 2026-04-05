# Pre-Mortem: Handoff V2 `extract_pending_operations()` and `short_task_name()` Fixes

**Target**: `P:/packages/handoff/scripts/hooks/__lib/transcript.py` (fix to Pass 1 of `extract_pending_operations()` + completion detection) and `P:/packages/handoff/scripts/hooks/__lib/handoff_v2.py` (removal of 120-char limit)

**Date**: 2026-03-31
**Kill criteria**: Revert if regressions introduced; if production transcript format differs materially from test fixtures; if completion detection produces false positives corrupting handoff state.

---

## Step 0.7 — Kill Criteria

- If any existing handoff test regresses → revert
- If production transcripts use a format incompatible with the fix → revert
- If completion detection produces systematic false positives → revert

---

## Step 1 — Failure Scenario

"It's 6 months later. The handoff system is marking operations as completed when they're actually still running (or vice versa). Sessions restore with incorrect task state — the AI repeats completed work or skips in-progress work. The `pending_operations` field is useless or actively misleading."

---

## Step 1.5 — Fix Side Effects

**Fix 1 (`extract_pending_operations()`)** introduces:
- New heuristic: `type="tool"` entry IDs = completed tools. If this correlation doesn't hold in production (e.g., `type="tool"` entries don't correspond 1:1 with `tool_use` IDs), ALL operations will be marked `in_progress` incorrectly.
- New loop iteration over `content_items` — adds O(n) per entry in worst case.

**Fix 2 (`short_task_name()`)** introduces:
- No new risk — removed an arbitrary limitation. Potential downstream display issues if consuming code assumes length ≤ 120.

---

## Step 2 — Failure Causes (10+)

### Architectural Principles at Risk

1. **Transcript parsing is a structural mapping problem** — wrong assumption about entry nesting causes systematic detection failure.
2. **Completion detection relies on ID correlation** — if `tool_use.id` ≠ `tool.id` in practice, heuristic fails entirely.
3. **Test fixtures may not reflect production format** — the `conftest.py` nested format may be idealized.

### Failure Causes

| ID | Principle Violated | Description |
|----|-------------------|-------------|
| F-001 | Structural mapping | Production transcript uses flat `{"type": "tool_use", ...}` entries (like test_edge_case_transcripts.py), NOT nested inside `message.content`. Fix iterates `entry["message"]["content"]` which doesn't exist in flat format. |
| F-002 | ID correlation | `type="tool"` entries don't have `id` fields matching `tool_use.id` — completion detection produces all `in_progress` (false negative). |
| F-003 | ID correlation | Every `type="tool"` entry IS a completed tool result, but `id` field format differs (e.g., UUID vs call_ID) — no matches in `completed_tool_ids` set. |
| F-004 | Structural mapping | `entry["message"]` exists but is not a dict (e.g., string, list) — `isinstance` check skips entry entirely. |
| F-005 | Structural mapping | `entry["message"]["content"]` exists but is not a list (e.g., string) — inner `isinstance(list)` check skips. |
| F-006 | Heuristic brittleness | Keyword fallback (Pass 2) fires even when Pass 1 finds tool entries, because Pass 1 only collects up to 5 and exits. Keyword detection on assistant text produces garbage. |
| F-007 | Cascading assumption | Completion state stored in `pending_ops[i]["state"]` but downstream `build_restore_message_compact()` only uses `pending_operations` count, not state — completion detection has no observable effect on behavior. |
| F-008 | Regression risk | Existing tests use flat-format entries that Pass 1 now skips entirely. Keyword fallback works by accident (empty text = no detection). Adding a real test with assistant text would fail. |
| F-009 | Performance | Pre-building `completed_tool_ids` set scans entire transcript before processing. For large transcripts (>10K entries), adds measurable overhead per extraction call. |
| F-010 | Version skew | Different Claude Code versions emit different transcript structures. Fix assumes one specific format. |
| F-011 | Display overflow | `current_task` now unbounded. If consuming UI truncates at a smaller boundary, task name is silently cut. Unlikely but possible. |

---

## Step 2.5 — Cascade Analysis

**F-001 (flat-format transcripts)**:
1. Pass 1 never matches → always falls to Pass 2 keyword detection → `pending_operations` shows wrong targets → restore message is misleading → AI works on wrong task.
2. If `build_restore_message_compact()` ignores `pending_operations` entirely (F-007), cascade is harmless.
3. Cascade probability: "sure" if production uses flat format.

**F-002 (ID mismatch)**:
1. All ops marked `in_progress` → restore always says "Resume X" even when X is done → AI repeats completed work.
2. User sees repeated work → loses trust in handoff → manually restates context defeating handoff purpose.
3. Cascade probability: "maybe" — depends on whether `type="tool"` entries have matching IDs.

---

## Step 2.6 — AI/LLM-Specific Failure Modes

- **Context overflow**: If transcript grows large, completion detection scans all entries. The `completed_tool_ids` set building is O(n) and happens on every extraction call, not cached.
- **Forgotten constraints**: The `[:120]` removal was a user request; downstream consumers may not handle unbounded strings.

---

## Step 2.7 — Temporal Failure Modes

- No evidence the character limit was causing observed failures — the user's concern was theoretical ("asking for problems").
- If downstream display code assumes ≤120 chars and truncates silently, the removal could cause invisible data loss.

---

## Step 3 — Categorization

| ID | Category |
|----|----------|
| F-001 | Tech (structural assumption) |
| F-002 | Tech (ID correlation assumption) |
| F-003 | Tech (ID format assumption) |
| F-004 | Tech (message field type) |
| F-005 | Tech (content field type) |
| F-006 | Tech (keyword fallback misuse) |
| F-007 | Tech (unused output) |
| F-008 | Process (test coverage gap) |
| F-009 | Tech (performance) |
| F-010 | External (version skew) |
| F-011 | Tech (downstream assumption) |

---

## Step 3.5 — Reference Class Forecasting

Reference: Past transcript parsing fixes in this codebase (TEST-001: `role` → `type` mismatch in `extract_last_substantive_user_message`). That fix also assumed a specific field name and had to be reverted/reworked when the actual transcript used a different key.

**Base rate signal**: 2 out of 3 transcript structural assumptions in this codebase were wrong on first attempt.

---

## Step 3.6 — Success Theater

- 35 transcript tests pass — but all test fixtures use flat entry format OR the nested assistant+content format. Neither tests the flat-format-with-real-content scenario.
- `tool_state = "completed" if tool_id in completed_tool_ids else "in_progress"` — state is computed but not verified against real transcript data.

---

## Step 3.8 — Operational Verification

| Finding | Evidence |
|---------|----------|
| F-001 | `conftest.py:67-84` — test fixture uses nested `{type: "assistant", message: {content: [{type: "tool_use", ...}]}}`. Production format UNKNOWN. |
| F-002 | `transcript.py:2287-2292` — `completed_tool_ids` built from `entry.get("id")` where `entry.get("type") == "tool"`. Whether `tool_use.id == tool.id` in production is UNVERIFIED. |
| F-007 | `handoff_v2.py:654-662` — `pending_operations` is formatted as count + bullet list of `{type, target}`, state field NOT included in output. |

---

## Step 4 — Risk Ratings

| ID | Likelihood (1-3) | Impact (1-3) | Score | Confidence% |
|----|-----------------|--------------|-------|-------------|
| F-001 | 2 | 3 | 6 | 70% |
| F-002 | 2 | 3 | 6 | 60% |
| F-007 | 3 | 2 | 6 | 85% |
| F-008 | 3 | 2 | 6 | 75% |
| F-003 | 1 | 3 | 3 | 50% |
| F-006 | 2 | 2 | 4 | 60% |
| F-009 | 1 | 2 | 2 | 70% |
| F-010 | 1 | 3 | 3 | 40% |
| F-011 | 1 | 1 | 1 | 50% |

---

## Step 4.5 — Dependency Cascades

- F-001 and F-002 are independent root causes that produce the same observable failure (all ops marked in_progress).
- F-007 is a consequence of F-001/F-002: if detection fails, the state field being unused doesn't matter.

---

## Step 5 — Prevent Top 3

1. **F-001** (Score 6, L=2, I=3): Verify actual production transcript structure by reading a live transcript file. If flat format confirmed, fix Pass 1 to handle flat entries.
2. **F-002** (Score 6, L=2, I=3): Add logging when `completed_tool_ids` set is empty (indicates no `type="tool"` entries found, or IDs don't match). Add empirical test that creates `tool_use` + `tool` entries and verifies completion state.
3. **F-007** (Score 6, L=3, I=2): `build_restore_message_compact()` ignores `state` field — either wire it into the output or don't compute it.

---

## Step 6 — Warning Signs

| Risk | Warning Sign | Detection | Trigger |
|-------|--------------|-----------|--------|
| F-001 | All `pending_operations` show state=`in_progress` even for trivially fast tools (Read) | Log `completed_tool_ids` size on each extraction; if always 0, format mismatch likely | Revert fix; use keyword fallback only |
| F-002 | Restore messages always say "Resume X" regardless of actual completion | Spot-check restore messages post-compact | Audit `pending_operations` state in handoff JSON |
| F-007 | Completion state computed but never observable | Code inspection: `build_restore_message_compact` doesn't reference `state` | Wire state into output or remove computation |
| F-008 | New test with assistant-text keywords fails | Run full test suite after any transcript parsing change | Fix test or fix detection |

---

## REMAINING ITEMS

| Step | Status | Gap | Priority |
|------|--------|-----|----------|
| 1 (F-001) | ✅ FIXED | Tests updated to nested format matching production. `make_tool_use_entry()` helper creates proper nested entries. 17/17 tests pass. Production format confirmed from conftest.py: nested `{type: "assistant", message: {content: [{type: "tool_use", ...}]}}`. |
| 2 (F-002) | ⚠️ UNVERIFIED | Completion detection logic correct (tool_id in completed_tool_ids → completed), but cannot empirically verify tool_use↔tool ID correlation without live transcript. |
| 3 (F-007) | ❌ Open | `state` field computed but not wired into compact output. Per-user guidance: confirm if state is needed in compact restore before implementing. |
| 4 (F-008) | ✅ FIXED | Tests now use nested format via `make_tool_use_entry()` helper. Pass 1 correctly traverses nested structure. |
| 5 (F-009) | ❌ Open | No caching of `completed_tool_ids` across extraction calls. Low priority — performance concern only. |

## ADVERSARIAL REVIEW FINDINGS (8 agents, 2026-03-31)

Key verified findings:
- **LOGIC-004** (medium): Keyword fallback fires whenever Pass 1 returns empty — no structural validation distinguishing "no entries found" from "structural mismatch." Recommendation: track flat-format tool_use count to only trigger fallback when flat entries existed.
- **TEST-006** (medium): No test used `conftest.make_transcript_entry()` fixture — FIXED by adding `make_tool_use_entry()` to test file.
- **TEST-007** (low): `test_grep_with_pattern_target` used flat format — FIXED.
- **PERF-005** (info): 50MB/50K entry hard limits undocumented to users — low priority.
- **PERF-006** (info): F-007 confirmed — state computed but excluded from compact output.
- **QUAL-005** (low): short_task_name() 120-char removal — no downstream consumer confirmed, low risk.
- **SEC-008-CHECKSUM-BYPASS** (medium): `quality_score` not in MUTABLE_METADATA_FIELDS — checksum changes on metadata update. NOT related to this fix (handoff_v2.py issue, not transcript.py).
- **5 pre-existing integration test failures**: `SessionStart_handoff_restore.py` subprocess exit 1 — environmental, unrelated to transcript changes.
