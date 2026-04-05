# ADR-20260329: LLM Behavioral Integrity — Preventing Fabrications, Misreadings, and Argumentativeness

**Date:** 2026-03-29
**Status:** Accepted
**Decision Maker:** Solo developer (architectural decision for personal Claude Code setup)
**Implemented:** 2026-03-30 (Phases 1-4 complete)

## Context and Problem Statement

Claude Code exhibits three infuriating failure modes that erode trust and waste user time:

1. **Fabricated sources** — Claiming information came from a source it did not (e.g., "Perplexity search" for AI Studio quota data the user provided directly)
2. **Reading failure** — Stopping reading a document early, then confidently claiming content that contradicts what appears later (e.g., "no OCR mentioned" when OCR was present)
3. **Argumentativeness** — Defending wrong answers instead of accepting corrections; using persuasive language to justify errors

Existing anti-sycophancy hooks (`StopHook_cross_validator.py`, `Stop_unverified_stance.py`, `hypothesis_as_fact_detector.py`) gate **output patterns** — they fire AFTER response generation to catch confident language without evidence. They cannot detect whether the model accurately processed input documents.

**Root cause:** Hooks enforce how claims are stated, not whether the model's internal processing of provided documents was complete or accurate.

## Decision

Implement a **multi-layer behavioral integrity system** combining:

| Layer | Component | Addresses | Mechanism |
|-------|-----------|-----------|-----------|
| 1 | Citation-Only Ground Truth | Source fabrication | Require explicit source binding for document claims |
| 2 | Embedding-Drift Sentinel | Reading failure | Monitor semantic similarity during generation |
| 3 | Correction Acknowledgment Gate | Argumentativeness | Require explicit acknowledgment of user corrections |
| 4 | State Invalidation Hooks | Stale evidence | Mark evidence stale when source files change |

## Rationale

Evidence from NotebookLM research on LLM behavioral integrity:

**1. Citation-Only Ground Truth**
> "Shift the model's instructions from a 'helpful assistant' to a strict transducer. Require that every claim is bound to a specific source ID from the provided context. Instruct the model that if support is missing, it must explicitly output the word 'unsupported' and stop, rather than inventing facts."
— Sources: 9158d66a-5a3a-484b-861a-b245d616c61b, b94f9b85-6704-47f9-add3-ba0f26152add

**2. Embedding-Drift Sentinels**
> "In long outputs, models follow a 'correct-then-incorrect' slope where they start accurately but drift into plausible fabrication. An embedding-drift sentinel automatically summarizes each generated paragraph, embeds it, and compares the cosine similarity against the original intent. If similarity drops below a threshold (e.g., 0.75), generation is halted, and the model is forced to re-ground itself with the source text."
— Sources: 5f1a6272-fcf2-4fbf-a153-de279372e6da, 447b6a96-cbf5-4bb5-903e-bc39aec6b755

**3. Epistemic Verification Layer (EVL)**
> "Before the agent is allowed to stop, it must output a `<verification_proof>` block containing the unique IDs of the tool calls it used. The hook checks a local database; if the agent fabricated a tool call or didn't actually read the necessary files, the hook returns `Exit Code 2`. This blocks termination and feeds the error back to the agent via `stderr`, forcing a mechanical 'Repair Turn'."
— Sources: c16abbed-f9e3-4eaf-af3c-2b5c6b611ebd, 2aec98ed-4285-4ce5-9dd1-54a4a4f3ac66

**4. Constitutional Layer**
> "Supplement task prompts with a 'constitution' — a short set of non-negotiable rules of engagement. For example, explicit anti-sycophancy rules can demand that the model 'prefer calibrated refusal over agreement without evidence'."
— Sources: 39de6dc1-a667-422e-8663-f9d9d9cf63fe, e14bd074-271c-4230-9503-7868a2baf264

**Why Option A (Source Citation Gate) alone was insufficient:**
Option A only addressed confabulation. It did not address the reading failure (attention collapse mid-document) or the behavioral pattern of defending errors. The NotebookLM research confirms that output-pattern gating is necessary but not sufficient — we need input-processing monitoring (drift detection) and behavioral enforcement (correction acknowledgment).

## Alternatives Considered

| Alternative | Description | Pros | Cons | Why Rejected |
|-------------|-------------|------|------|--------------|
| **Option A (Source Citation Gate only)** | PreToolUse/Stop hook requiring Read tool evidence for document claims | Simple, similar to existing fabrication detection | Only addresses confabulation, not reading failure or argumentativeness | Incomplete — 2 of 3 failures unaddressed |
| **Team of Rivals / Multi-Agent Critics** | Independent critic agents with veto authority | Catches argumentativeness structurally | Architecture complexity, different model vendors required | Overkill for solo dev setup |
| **Formal Verification (SMT solvers)** | Mathematically verify claims against specifications | Precise, unambiguous signals | Heavy infrastructure, not practical for natural language | Outside solo-dev scope |
| **Remote Code Execution** | LLM writes code that executes against real data | Every fact traceable to executed query | Complexity, latency | Not applicable to document Q&A |

## Implementation

### Phase 1: Citation-Only Ground Truth (Foundation) ✅ IMPLEMENTED
**Effort:** 4-6 hours | **Addresses:** Source fabrication

**Status:** ✅ Complete (2026-03-30)

1. ✅ Extend `StopHook_cross_validator.py` with document claim detection:
   - Pattern: claims about "the document/file says X" where X matches content from user-provided files
   - Required evidence: Read tool event for that file in this session
   - If missing: block with "You claimed X from the document without reading it. Either Read the file or say 'I haven't read that document yet.'"

2. ✅ Add source binding to CLAUDE.md principles:
   - New principle: "When making claims about provided documents, cite the specific source. If no source supports a claim, state 'unsupported'."

**Implementation details:**
- `P:\.claude\hooks\__lib\claim_patterns.py`: Added `DOCUMENT_CLAIM_PATTERNS` and `has_document_claim()` function
- `P:\.claude\hooks\StopHook_cross_validator.py`: Added `verify_document_claim()` function and integrated into `run()`
- `P:\.claude\CLAUDE.md`: Added "Source Binding for Document Claims" section

### Phase 2: Embedding-Drift Sentinel
**Effort:** 6-8 hours | **Addresses:** Reading failure

**Status:** ✅ Implemented (2026-03-30)

1. ✅ Create `StopHook_drift_sentinel.py`:
   - Compare TF-IDF cosine similarity between generated paragraphs and source document
   - Threshold: 0.75 similarity (configurable via `DRIFT_SENTINEL_THRESHOLD`)
   - If drift detected: inject "Re-grounding required" message, block stop
   - Uses `sklearn.feature_extraction.text.TfidfVectorizer` + `cosine_similarity`
   - Sklearn fail-open: module-level `try/except ImportError` setting `_SKELEARN_AVAILABLE = False`
   - In warn mode: logs drift, allows stop

2. ✅ Registered in `Stop_router.py`:
   - Added to `HOOK_SEQUENCE` tuple
   - Added to `ACTIVE_RUNTIME_HOOKS` frozenset

3. ✅ Configuration env vars:
   - `DRIFT_SENTINEL_ENABLED` (default: `true`)
   - `DRIFT_SENTINEL_MODE` (default: `warn`) — `warn` or `block`

**Implementation details:**
- `P:\.claude\hooks\StopHook_drift_sentinel.py`: Drift detection with TF-IDF cosine similarity
- `P:\.claude\hooks\tests\test_drift_sentinel.py`: 18 test cases covering all detection scenarios
- `P:\.claude\hooks\Stop_router.py`: Registered as active runtime hook

### Phase 3: Correction Acknowledgment Gate
**Effort:** 2-3 hours | **Addresses:** Argumentativeness

**Status:** ✅ Implemented (2026-03-30)

1. ✅ Create `StopHook_correction_acknowledgment.py`:
   - Detect user corrections: "no", "wrong", "you were wrong", "I didn't say that", "that's not what I asked"
   - Require explicit acknowledgment pattern in response: "I was wrong about X because..." or "Let me correct: ..."
   - Mutually exclusive patterns: correction regex vs acknowledgment regex never both match
   - 200-character proximity requirement for acknowledgment after correction
   - Block if response argues back without acknowledging the correction

2. ✅ Registered in `Stop_router.py`:
   - Added to `HOOK_SEQUENCE` tuple
   - Added to `ACTIVE_RUNTIME_HOOKS` frozenset

3. ✅ Configuration env vars:
   - `CORRECTION_GATE_ENABLED` (default: `true`)
   - `CORRECTION_GATE_MODE` (default: `warn`) — `warn` or `block`

**Implementation details:**
- `P:\.claude\hooks\__lib\claim_patterns.py`: Added `has_correction()` and `has_acknowledgment()` functions
- `P:\.claude\hooks\StopHook_correction_acknowledgment.py`: Main gate logic
- `P:\.claude\hooks\tests\test_correction_detector.py`: 22 test cases — all pass

### Phase 4: State Invalidation Hooks
**Effort:** 3-4 hours | **Addresses:** Stale evidence

**Status:** ✅ Implemented (2026-03-30)

1. ✅ Extend `evidence_store.py` with `file_metadata` table:
   - `file_path TEXT NOT NULL UNIQUE`
   - `invalidated INTEGER NOT NULL DEFAULT 0`
   - `invalidated_at TEXT NOT NULL`
   - `session_id TEXT NOT NULL`
   - `terminal_id TEXT NOT NULL DEFAULT ''`
   - Index on `file_path` for fast lookups

2. ✅ Add functions to `evidence_store.py`:
   - `mark_file_invalidated(path, session_id, terminal_id) -> bool` — uses `INSERT OR REPLACE INTO`
   - `is_file_invalidated(path) -> bool` — queries with `invalidated = 1` check

3. ✅ Create `posttooluse/file_invalidation_tracker.py`:
   - PostToolUse hook with `tool_matcher = {"Edit", "Write"}`
   - Marks file paths as invalidated after Edit/Write tool execution
   - Fail-open on evidence store errors

4. ✅ Register in `posttooluse/__init__.py`:
   - Import `FileInvalidationTrackerHook`
   - Register as `"file_invalidation_tracker"` in `create_registry()`

5. ✅ Extend `StopHook_cross_validator.py`:
   - Import `is_file_invalidated` from evidence_store
   - In `verify_document_claim()`: after confirming Read executed, check if file was invalidated
   - If invalidated: block with message to re-read document

6. ✅ Configuration env vars:
   - `FILE_INVALIDATION_TRACKER_ENABLED` (default: `true`)

**Implementation details:**
- `P:\.claude\hooks\evidence_store.py`: Added `file_metadata` table schema + `mark_file_invalidated()` + `is_file_invalidated()`
- `P:\.claude\hooks\posttooluse\file_invalidation_tracker.py`: PostToolUse hook
- `P:\.claude\hooks\posttooluse\__init__.py`: Registry entry added
- `P:\.claude\hooks\StopHook_cross_validator.py`: Extended `verify_document_claim()` with invalidation check
- `P:\.claude\hooks\tests\test_file_invalidation.py`: 7 test cases — all pass

## Rollback Strategy

- Each phase is independently disableable via environment variable
- State: `export CITATION_GATE_ENABLED=false`, `export DRIFT_SENTINEL_ENABLED=false`, etc.
- Phase 1 (Citation-Only GT) is the minimum viable fix — can deploy alone

## Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| No fabricated sources | Zero occurrences of "from Perplexity/Google/WebSearch" for user-provided data per session |
| Complete document reading | Zero "no X mentioned" errors when X appears in provided document |
| Correction acknowledgment | 100% of user corrections acknowledged explicitly, not argued against |

## Multi-Terminal Isolation Assessment

**State sharing:** Yes — session state files in `P:/__csf/state/` are shared across terminals
- **Mitigation:** Terminal-scoped state files (`{terminal_id}` suffix) prevent cross-terminal contamination
- **Read events:** Scoped to session_id, not global — terminal A cannot see terminal B's reads

**Concurrency safety:** Low risk — state files are append-only (Read events), writes only invalidate stale flags
- **Race condition:** Terminal A reads file while Terminal B modifies it → possible stale read
- **Mitigation:** State invalidation happens atomically on file modification

**Stale data immunity:** High — file modification triggers immediate invalidation
- **Propagation:** File system is authoritative; next Read by any terminal refreshes state

## References

- [NotebookLM: Claude Code - Hooks and Agent Control Systems](d66afb5b-35cb-4e89-bd51-3b120e15d643)
- [NotebookLM: Claude Code - Workflow and Logic Inefficiencies](2c9cc8e9-f1c4-4724-a83b-62412d20846c)
- [NotebookLM: Agentic Engineering Playbook](59329bf3-4765-4d4e-8ec6-f2eceeba0f41)

---

**Confidence:** 65% — Research-backed approach, but untested in this specific hook architecture. Phase 1 is conservative extension of existing fabrication detection patterns.

**Review status:** Pending user review

**Last updated:** 2026-03-30
