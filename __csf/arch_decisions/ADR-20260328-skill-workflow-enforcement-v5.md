# ADR: Skill Workflow Enforcement v5.0 — Compaction-Proof State Machine

**Status:** Proposed | **Date:** 2026-03-28 | **Decision ID:** ADR-20260328-skill-workflow-enforcement

---

## Problem Statement

The current three-layer enforcement system (UserPromptSubmit -> PreToolUse -> Stop) has four converging failure modes:

| Root Cause | Symptom | Evidence |
|---|---|---|
| RC1: Prose bypass | AI generates text without tools, PreToolUse never fires | Stop hook log: `"WARNING: Tool extraction returned empty list"` |
| RC2: Transcript parsing failure | `extract_user_prompt()` returns empty after compaction | `StopHook_skill_execution_gate.py:437-449` falls back to transcript parsing which drops user messages post-compaction |
| RC3: Registry gaps | `/gto` missing from `SKILL_EXECUTION_REGISTRY` | `StopHook_skill_execution_gate.py:133-314` — no entry for `gto` |
| RC4: No completion tracking | Intent file DELETED on Skill() call (PreToolUse.py:1006), destroying all enforcement state | `_intent_candidate.unlink(missing_ok=True)` at line 1006 |

**User constraint:** Multi-terminal isolated, stale-data immune, compaction-proof. No concern about transition effort.

---

## Verbalized Sampling — K=4 Candidates

### Candidate A: Stateful Intent File (Phase Machine)

**Core idea:** Replace the delete-on-Skill() pattern with a phase-transition model. Intent file persists through the entire workflow lifecycle.

**Phases:** `pending` -> `loaded` -> `executing` -> `complete`

- UserPromptSubmit writes intent file (phase=pending)
- PreToolUse transitions to `loaded` when Skill() called (instead of deleting)
- PostToolUse transitions to `executing` when workflow tools used
- Stop hook checks phase: if not `complete`, blocks with specific guidance
- Skills declare `completion_criteria` in SKILL.md frontmatter

**Multi-terminal:** Already terminal-scoped via `state/terminals/{terminal_id}/pending_command_intent.json`

**Stale data immunity:** TTL field + phase checks. A `complete` file can be GC'd immediately.

**Compaction proof:** State lives on disk, not in context. Stop hook reads file directly.

**P[select]=0.55** — Moderate complexity, strong fit with existing patterns.

### Candidate B: Completion Promise + Quality Gate

**Core idea:** Skills emit structured completion tags. Stop hook validates presence and quality.

**Mechanism:**
- Skills declare `required_outputs` in frontmatter (e.g., `["report_generated", "tests_passed"]`)
- PostToolUse tracks which outputs produced (by matching tool outputs against declared patterns)
- Stop hook checks: all required_outputs produced? If not, blocks.
- AI must emit `<!-- WORKFLOW_COMPLETE -->` in final response
- Quality-driven adaptive loop: Stop hook evaluates outcome quality, not just tool occurrence

**Multi-terminal:** Output tracking stored in terminal-scoped JSONL.

**Stale data immunity:** Each output event is idempotent (dedup by tool_call_id).

**Compaction proof:** Output events persisted to disk, not context.

**P[select]=0.25** — Novel but requires AI cooperation (emitting tags). Fragile if AI forgets tag.

### Candidate C: Auto-Discovery Registry + State Machine

**Core idea:** Eliminate the hardcoded registry. Skills self-declare enforcement config via SKILL.md frontmatter. Combine with Candidate A's state machine.

**Mechanism:**
- On Skill() call, PostToolUse reads the loaded skill's SKILL.md frontmatter
- Extracts: `required_tools`, `workflow_steps`, `completion_criteria`, `enforcement_tier`
- Writes to terminal-scoped state file (replaces hardcoded `SKILL_EXECUTION_REGISTRY` lookup)
- Stop hook reads state file — no registry dependency at all
- Intent file transitions through phases from Candidate A

**Multi-terminal:** All state terminal-scoped.

**Stale data immunity:** State file has TTL and skill_name verification.

**Compaction proof:** All state on disk.

**P[select]=0.65** — Highest probability. Eliminates RC3 (registry gaps) structurally while also fixing RC1, RC2, RC4.

### Candidate D: Event-Sourced Workflow Ledger

**Core idea:** Every tool call appends to a terminal-scoped JSONL ledger. Stop hook replays ledger to reconstruct full workflow state.

**Mechanism:**
- PostToolUse appends `{tool_name, tool_input_hash, timestamp, skill_name}` to `ledger_{terminal_id}.jsonl`
- Stop hook reads ledger, reconstructs: which skills loaded, which tools used, which outputs produced
- Skills declare `workflow_steps` as a DAG with `required_outputs` per step
- Ledger replay checks DAG completion

**Multi-terminal:** One ledger per terminal.

**Stale data immunity:** Append-only with TTL compaction.

**Compaction proof:** Ledger is disk-native.

**P[select]=0.15** — Over-engineered for solo dev. Ledger replay adds latency to every Stop event. DAG validation is complex.

---

## GoT Analysis

**Nodes extracted:**

| Node Type | Nodes |
|---|---|
| Constraints | ["Multi-terminal isolation", "Stale data immunity", "Compaction proof", "No transition effort concern"] |
| Ideas | ["Phase-transition intent file", "Completion promise tags", "Auto-discovery from frontmatter", "Event-sourced ledger"] |
| Risks | ["AI forgets completion tag", "Frontmatter schema drift", "Ledger replay latency", "Legacy state migration"] |
| Components | ["Intent file", "State file", "SKILL.md frontmatter", "Stop hook", "PostToolUse tracker"] |

**Edge relationships:**
- "Auto-discovery" **supports** "Phase-transition" (provides phase transition criteria)
- "Completion promise tags" **contradicts** "No AI cooperation required" (fragile)
- "Event-sourced ledger" **contradicts** "Solo dev simplicity" (over-engineered)
- "Auto-discovery" **depends on** "SKILL.md frontmatter" (correct)

**Cycles detected:** None

**Architectural insight:** Candidates A and C are complementary, not competing. C extends A with auto-discovery. Candidates B and D introduce orthogonal risk (AI cooperation dependency and complexity, respectively).

---

## Evaluation Matrix

| Dimension | A: Phase Machine | B: Promise Tags | C: Auto-Discovery + SM | D: Event Ledger |
|---|---|---|---|---|
| Addresses RC1 (prose bypass) | Partial | Partial | Full | Full |
| Addresses RC2 (transcript parse) | Full | Partial | Full | Full |
| Addresses RC3 (registry gaps) | No | No | **Full** | No |
| Addresses RC4 (completion) | Full | Full | Full | Full |
| Multi-terminal isolated | Yes | Yes | Yes | Yes |
| Compaction proof | Yes | Partial | Yes | Yes |
| Stale data immune | Yes | Yes | Yes | Yes |
| Solo-dev complexity | Low | Medium | Medium | High |
| Backward compatible | Moderate | Low | High | Low |
| **Jaccard distance from next** | 0.45 | 0.55 | 0.60 | 0.70 |

---

## RECOMMENDATION: Candidate C (Auto-Discovery + Phase Machine)

**Favored quality/goal:** Structural correctness — eliminates all four root causes without relying on AI cooperation.

**Degraded quality/goal:** Slightly higher initial implementation complexity (frontmatter schema + auto-discovery).

**Failure conditions:** Low risk. Frontmatter schema is self-documenting. Skills without frontmatter degrade gracefully to knowledge-skill behavior (current default).

**ISO 25010 mapping:** +Reliability (compaction-proof), +Maintainability (auto-discovery, no hardcoded registry), +Portability (frontmatter is portable), -Performance Efficiency (one extra file read on Skill() call, <5ms).

---

## Detailed Design

### 1. SKILL.md Frontmatter Schema Extension

```yaml
---
name: gto
enforcement: strict
required_tools: ["Bash", "Read", "Grep"]
completion_criteria:
  - phase: scan
    required_output: "corpus_scanned"
  - phase: analyze
    required_output: "gap_report_generated"
  - phase: report
    required_output: "final_report_written"
---
```

**Auto-discovery rule:** When Skill() is called, PostToolUse reads the loaded SKILL.md, extracts this frontmatter, and writes it to the terminal-scoped state file. This eliminates the hardcoded `SKILL_EXECUTION_REGISTRY` entirely — the skill IS the registry entry.

### 2. Intent File Phase Machine

Replace the delete-on-Skill() pattern:

**Current (broken):**
```
UserPromptSubmit: write intent file (phase=pending)
PreToolUse:      Skill() called -> DELETE intent file  <- destroys state
Stop hook:       tries to parse transcript <- fails after compaction
```

**Proposed:**
```
UserPromptSubmit: write intent file (phase=pending)
PreToolUse:      Skill() called -> TRANSITION to phase=loaded
PostToolUse:     first workflow tool -> TRANSITION to phase=executing
PostToolUse:     each completion_criteria met -> update progress
Stop hook:       if phase != complete -> BLOCK with specific missing criteria
```

**State file schema** (`state/terminals/{terminal_id}/workflow_state.json`):
```json
{
  "skill": "gto",
  "phase": "executing",
  "loaded_at": 1743193200,
  "terminal_id": "console_abc123",
  "completion_criteria": [
    {"phase": "scan", "required_output": "corpus_scanned", "satisfied": true},
    {"phase": "analyze", "required_output": "gap_report_generated", "satisfied": false},
    {"phase": "report", "required_output": "final_report_written", "satisfied": false}
  ],
  "tools_used": ["Bash", "Read", "Grep"],
  "enforcement_tier": "strict"
}
```

### 3. Stop Hook: Read State File Instead of Parsing Transcript

**Current (broken):** `extract_user_prompt()` -> `_parse_transcript_snapshot()` -> fails after compaction.

**Proposed:** Read `workflow_state.json` directly. No transcript parsing needed. The state file IS the source of truth.

```python
def check_workflow_completion(terminal_id: str) -> dict | None:
    state_file = TERMINALS_DIR / terminal_id / "workflow_state.json"
    if not state_file.exists():
        return None
    state = json.loads(state_file.read_text())
    if state["phase"] == "complete":
        return None  # Allow stop
    unsatisfied = [c for c in state["completion_criteria"] if not c["satisfied"]]
    if unsatisfied and state["enforcement_tier"] == "strict":
        return {"decision": "block", "reason": f"Workflow incomplete: {unsatisfied}"}
    return None  # Advisory or no enforcement
```

### 4. PostToolUse Completion Tracker

New component that validates tool outputs against declared `completion_criteria`:

```python
def track_completion(terminal_id: str, tool_name: str, tool_output: str) -> None:
    state_file = TERMINALS_DIR / terminal_id / "workflow_state.json"
    state = json.loads(state_file.read_text())
    for criteria in state["completion_criteria"]:
        if not criteria["satisfied"]:
            # Check if tool_output contains the required_output marker
            if criteria["required_output"] in tool_output:
                criteria["satisfied"] = True
    if all(c["satisfied"] for c in state["completion_criteria"]):
        state["phase"] = "complete"
    state_file.write_text(json.dumps(state, indent=2))
```

### 5. Compaction Immunity: PreCompact Hook

Add a PreCompact hook that preserves workflow state:

- Reads `workflow_state.json` for the current terminal
- Writes a compact summary to `state/terminals/{terminal_id}/compaction_checkpoint.json`
- On session resume, Stop hook reads checkpoint + state file
- State file survives compaction (it's on disk, not in context)

### 6. Stale Data Immunity

- Every state file has `loaded_at` (epoch seconds)
- Stop hook checks: if `time.time() - loaded_at > STALE_TIMEOUT` -> warn but allow stop
- SessionEnd hook cleans up all state files for that terminal
- `SKILL_FIRST_INTENT_TTL_SECONDS` (existing 90s) applied to intent files

---

## Component Map

| Component | Event | Purpose | File |
|---|---|---|---|
| Intent Writer | UserPromptSubmit | Write intent file (phase=pending) | `skill_enforcer.py` (existing, modified) |
| Phase Transitioner | PreToolUse | Skill() -> phase=loaded | `PreToolUse_skill_pattern_gate.py` (modified) |
| Completion Tracker | PostToolUse | Track workflow progress | `posttooluse/workflow_completion_tracker.py` (NEW) |
| State Reader | Stop | Check phase + completion | `StopHook_skill_execution_gate.py` (modified) |
| Compaction Checkpoint | PreCompact | Persist state across compaction | `PreCompact_workflow_checkpoint.py` (NEW) |
| Cleanup | SessionEnd | Remove state files | `SessionEnd_cleanup.py` (existing, extended) |

---

## Migration Path

1. **Phase 1:** Add frontmatter schema to all enforcement-requiring skills (gto, code, tdd, v, etc.)
2. **Phase 2:** Create `workflow_completion_tracker.py` (PostToolUse)
3. **Phase 3:** Modify `PreToolUse_skill_pattern_gate.py` — transition instead of delete
4. **Phase 4:** Modify `StopHook_skill_execution_gate.py` — read state file instead of transcript
5. **Phase 5:** Remove hardcoded `SKILL_EXECUTION_REGISTRY` (replaced by auto-discovery)
6. **Phase 6:** Add PreCompact checkpoint hook
7. **Phase 7:** Testing — all existing tests pass, new tests for phase transitions

**User stated no concern about transition effort**, so all phases can proceed without backward-compatibility shims.

---

## Edge Case Considerations

| Edge Case | Mitigation |
|---|---|
| Skill has no frontmatter | Degrade to current behavior (knowledge-skill, no enforcement) |
| Frontmatter has invalid schema | Fail-open with warning log, treat as knowledge skill |
| Two terminals load same skill | Terminal-scoped state files — no cross-contamination |
| AI calls Skill() then immediately stops (prose bypass) | State file shows phase=loaded but no completion_criteria satisfied -> Stop hook blocks |
| Compaction happens mid-workflow | State file on disk survives; PreCompact checkpoint adds safety net |
| Skill crashes mid-workflow | Stale timeout (300s) allows eventual stop; SessionEnd cleans up |
| Required output marker never appears in tool output | Completion criteria can use regex patterns, not just substring match |
| Skill has 0 completion_criteria | Treat as knowledge skill (current behavior) — no enforcement |

---

## Synthesis

**Decision:** Candidate C — Auto-Discovery Registry + Phase Machine.

**Rationale:** This is the only candidate that structurally eliminates all four root causes. By reading enforcement config directly from SKILL.md frontmatter, RC3 (registry gaps) becomes impossible — every skill is self-registering. By persisting workflow state through phase transitions instead of deleting the intent file, RC4 (no completion tracking) is solved. By having the Stop hook read disk state instead of parsing transcripts, RC2 (compaction failure) is solved. And by tracking completion criteria through PostToolUse, RC1 (prose bypass) is caught — the Stop hook sees phase=loaded with zero satisfied criteria and blocks.

**KPI Scores:**
- Relevance: **High** (addresses all four root causes)
- Accuracy: **High** (all mechanisms use proven disk-based state patterns already in the codebase)
- Coherence: **High** (extends existing state_paths.py terminal isolation and skill_execution_state.py patterns)

---

## Research Sources

Cross-notebook query from NotebookLM (10/10 notebooks responded) produced five key patterns that informed this design:

1. **Stop Hook Validators** — exit code 2 blocking when completion criteria unmet
2. **Phase-Gated State Machines** — explicit phase transitions with guard conditions
3. **Disk-Backed Workflow State** — terminal-scoped JSON survives compaction
4. **Quality-Driven Adaptive Loops** — evaluate outcome quality, not just tool occurrence
5. **PreCompact Hooks** — capture state before context erasure, re-inject on resume
