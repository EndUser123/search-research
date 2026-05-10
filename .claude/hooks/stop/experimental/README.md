# stop/experimental — Validator Classification Index

This directory holds validators extracted from Stop_router.py, classified for integration or archival.

## Production Candidates

### phase0_depends_on_skills.py

**Classification:** Integrate as blocking gate (production candidate)

**Purpose:** Phase 0 gate that enforces skill dependency chains. Skills declaring `depends_on_skills` in SKILL.md frontmatter must have step-1 evidence present before they are considered ready.

**Input contract:**
- `transcript_entries`: list of dicts (from Stop.py payload)
- `terminal_id`: str (from Stop.py payload)

**BLOCKS if:**
- Skill has `depends_on_skills`
- Step-1 evidence file is missing, empty, or corrupt

**PASSES if:**
- Gate disabled via `DEPENDS_ON_SKILLS_GATE_ENABLED=false`
- No skill detected in transcript
- Skill has no `depends_on_skills`
- No terminal_id resolvable (bypass)
- Step-1 evidence file exists and is valid JSONL

**Evidence file format:**
```
~/.claude/.evidence/{skill}-{terminal}/step_{step1_name}.jsonl
```
Must be non-empty and have a valid JSON line as first entry.

**Wiring:** Add to Stop.py IN_PROCESS_GATES + GATE_CLASSES entry.

**Tests:** `test_phase0_depends_on_skills.py` (23 tests, all pass)

---

## Archived (Not Wired)

### Stop_tdd_refactor_gate.py

**Classification:** Archive without integration

**Reason:** Depends on TDDState singleton from `__lib/tdd_core.py`. Stop.py does not have TDDState in its execution context. This gate cannot be wired without making TDDState available in Stop.py.

**Purpose:** Prevents premature completion claims during TDD REFACTORING phase with circuit breaker.

---

### evidence_verification_gate.py

**Classification:** Archive without integration

**Reason:** Wrong coupling direction — this gate imports `EvidenceManager` from the `/code` skill. Stop.py should NOT import from skills. Additionally, non-standard `process(conversation, final_response)` signature vs standard `run(data)` protocol.

**Purpose:** Integrates with EvidenceManager for file existence validation.

**Integration path (if needed):** Re-architect so that `/code` skill writes evidence markers that Stop.py reads, rather than Stop.py importing from the skill.

---

## Backlog

- Stop_verification_gate.py — assessment pending (session-scope too permissive for production)
