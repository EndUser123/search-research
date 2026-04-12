# ADR-004: Optimize /recap Path Resolution Strategy

**Date:** 2026-04-11
**Status:** Proposed
**Decider:** Bruce Thomson

## Context

`/recap` needs reliable session chain reconstruction across multiple Claude Code data sources. The current implementation attempts to import `search_research.session_chain` which doesn't exist at the expected import path. Meanwhile, multiple packages provide overlapping functionality for session traversal and chat history search.

## Data Format Validation

**Input:** Claude Code transcript and handoff file formats

**Sample examined:**
- `C:\Users\brsth\.claude\projects\P--\*.jsonl` (100+ files, 1.7-34 MB each)
- `P:\.claude\state\handoff\console_*_handoff.json`

**Schema verified:**
- **Transcript JSONL:** Each line has `type`, `sessionId`, `timestamp`/`createdAt`, `message` (with `content` blocks)
- **Handoff JSON:** Contains `resume_snapshot` with `transcript_path`, `prior_transcript_path`, `created_at`, `goal`, `current_task`, `active_files`

**Assumptions verified:**
- Handoff files contain `prior_transcript_path` (valid)
- Handoff files use `console_{session_id}_handoff.json` naming (valid - but NOTE: filename doesn't contain its own session ID, contains the NEXT session's ID)
- Project transcripts are in `~/.claude/projects/{project_hash}/` (valid)

**Mismatches found:** None - format documentation matches actual file structure

## Package Capabilities Analysis

| Package | Technology | Purpose | Strengths | Weaknesses |
|---------|------------|---------|-----------|------------|
| **claude-chain-miner** | Python | Handoff-chain walker, exporter, miner | Compact-proof, self-match fix, dual-path search | Standalone CLI, not importable as library |
| **claude-history** | Rust + SQLite FTS5 | Fast keyword search for chat history | ~10ms search, 2.7GB indexed, MCP server mode | Read-only search, no chain traversal |
| **claude-log** | Python | Hook-based logging for learning tool schemas | Educational, captures tool invocations | Not a search backend, diagnostic only |
| **search-research** | Python | Unified search router | Multiple backends, session chain traversal | Current import path mismatch in /recap |

### Module-Level Capabilities

**search-research/core/session_chain.py:**
- `walk_session_chain()` - Unified entry point with 3 strategies
- `walk_handoff_chain()` - Strategy 1: handoff-file chain
- `walk_sessions_index_chain()` - Strategy 2: mtime-gap + semantic verification
- `walk_semantic_chain()` - Strategy 3: pure similarity fallback
- Security: Path traversal validation, bounded reads, TOCTOU fixes

**claude-chain-miner/scripts/walker.py:**
- `walk_handoff_chain()` - Similar handoff traversal
- `get_chain_for_slug()` - Slug-based lookup (broken, per README)
- Uses same reverse-lookup approach as search-research

**claude-history CLI:**
- `claude-history search` - Keyword search via FTS5
- `claude-history list` - List recent sessions
- `claude-history get <id>` - Get session details
- No Python API - subprocess invocation required

## Current /recap Issues

**Issue 1: Import Path Mismatch**
```python
# Current (broken):
from search_research.session_chain import SessionChainEntry, walk_session_chain

# Actual path:
from search_research.core.session_chain import SessionChainEntry, walk_session_chain
```

**Issue 2: Single-Strategy Dependency**
- Only attempts unified chain walk
- No direct handoff-file fallback when chain returns empty
- Doesn't leverage handoff files for immediate resume context

**Issue 3: Missing Handoff Priority**
- Handoff files are the highest-fidelity resume source
- Current implementation treats them equally with session-index scan
- Session summary block parsing (ADR-003) is a workaround, not primary path

## Decision

### R1: Fix Import Path

**Change:** Update import in `/recap` to use correct module path

```python
# P:/.claude/skills/recap/__init__.py line ~1294
from search_research.core.session_chain import SessionChainEntry, walk_session_chain
```

### R2: Handoff-First Resolution Strategy

**Change:** Prioritize handoff files as the primary resume context source

**Resolution order:**
1. **Fresh handoff** - If handoff with `created_at` < 5 minutes old exists, use as primary source
2. **Handoff chain walk** - Use `walk_handoff_chain()` for session history
3. **Unified chain** - Fallback to `walk_session_chain()` for missing links
4. **Direct transcript** - Final fallback to current .jsonl file

**Rationale:**
- Handoff files are written atomically at compaction time
- They contain the `resume_snapshot` with goal, current_task, active_files
- They survive compaction and preserve `prior_transcript_path` links
- They are the source of truth for session continuity

### R3: Package Usage Clarification

| Task | Use | Don't Use |
|------|-----|-----------|
| Session chain traversal | `search_research.core.session_chain` | `claude-chain-miner` (standalone CLI) |
| Chat history search | `claude-history` CLI via subprocess | Direct transcript scanning |
| Tool schema learning | `claude-log` (for hook development) | Production workflow |

**claude-chain-miner** should be considered **deprecated for /recap integration** - its functionality is fully subsumed by `search_research.core.session_chain`.

### R4: Subagent Transcript Filtering

**Change:** Add filter in `/recap` to exclude subagent transcripts from session chain

**Problem:** ADR-003 identified that subagent transcripts (`agent-*.jsonl` in `subagents/` directories) were being returned as standalone sessions.

**Solution:** In `_load_all_sessions_via_history_index()`, filter out entries where:
- `transcript_path` contains `/subagents/` or `\subagents\` as path component
- OR filename starts with `agent-`

**Implementation:**
```python
def _is_subagent_transcript(path: Path) -> bool:
    """Check if a transcript path belongs to a subagent."""
    parts = path.parts
    if "subagents" in parts:
        return True
    if path.name.startswith("agent-"):
        return True
    return False
```

### R5: Session Summary Block as Secondary Signal

**Change:** When handoff chain returns empty but session summary block exists in transcript, use it as prior session context

**Implementation:** (From ADR-003 R2, restated for completeness)

Parse session summary block from current transcript's early entries (first 200 lines):
```
##\s*Last\s*Session\s*Summary\s*\n(?:.*?\n)*?(?=\n##|\Z)
```

**Quality gate:** Summary is usable only if ALL of:
- Contains `**When:**` field with timestamp
- Contains `**Duration:**` field with value > 0
- Content between header and next `##` is > 50 chars

## Contract Authority Packet

```yaml
contract_authority_packet:
  packet_version: "1"
  contract_sensitive: true
  authority:
    closure_source: "contract_authority_packet"
    prose_role: "explanatory_only"
  boundaries:
    - boundary_id: "recap-path-resolution"
      producer: "/recap skill"
      consumer: "Claude Code session restore, conversation context recovery"
      schema:
        id: "recap-session-chain"
        version: "1"
      required_fields: ["session_id", "transcript_path", "entries"]
      optional_fields: ["handoff_snapshot", "session_summary_block"]
      freshness_authority: "handoff_file_transcript_path"
      invalidation_trigger: "new handoff written for same terminal_id"
      precedence_rule: "fresh handoff > stale handoff > session summary > mtime transcript"
      failure_behavior: "degrade to direct transcript scan"
      validator_owner: "/recap"
      proof_owner: "/verify --contracts"
      downstream_consumers: ["/recap", "session restore workflow"]
```

## Planning Handoff Packet

```yaml
planning_handoff_packet:
  packet_version: "1"
  source_adr: "P:/.claude/arch_decisions/ADR-004-recap-path-resolution-strategy.md"
  plan_title: "Fix /recap import path and implement handoff-first resolution"
  goal: "Enable /recap to reliably reconstruct session chains using optimal path resolution strategy"
  current_state_with_evidence:
    - "P:/.claude/skills/recap/__init__.py:1294 uses wrong import path 'from search_research.session_chain'"
    - "Actual module is at 'search_research.core.session_chain' (verified via Bash ls and Read)"
  design_decisions_and_invariants:
    - id: "DEC-001"
      decision: "Handoff files are the highest-fidelity resume source"
      rationale: "Written atomically at compaction, survive transcript compaction, contain resume_snapshot"
    - id: "DEC-002"
      decision: "Filter out subagent transcripts from session chain"
      rationale: "Subagent transcripts are not user-visible sessions"
    - id: "DEC-003"
      decision: "Use claude-history CLI for chat search, not direct transcript scan"
      rationale: "10ms FTS5 search vs unindexed JSONL scan"
  implementation_changes:
    - task_id: "TASK-001"
      title: "Fix import path in /recap"
      scope:
        files: ["P:/.claude/skills/recap/__init__.py"]
        dependencies: []
      acceptance:
        - "Import statement uses 'from search_research.core.session_chain import'"
        - "/recap executes without ImportError"
    - task_id: "TASK-002"
      title: "Implement handoff-first resolution strategy"
      scope:
        files: ["P:/.claude/skills/recap/__init__.py"]
        dependencies: ["TASK-001"]
      acceptance:
        - "Fresh handoff (< 5 min) is used as primary source"
        - "Handoff chain walk attempted before unified chain"
        - "Subagent transcripts filtered from results"
    - task_id: "TASK-003"
      title: "Add subagent transcript filtering"
      scope:
        files: ["P:/.claude/skills/recap/__init__.py"]
        dependencies: ["TASK-001"]
      acceptance:
        - "_is_subagent_transcript() helper function exists"
        - "Filter applied in _load_all_sessions_via_history_index()"
  test_matrix:
    - task_id: "TASK-001"
      test_binding: "pytest P:/.claude/skills/recap/tests/test_recap.py::test_import_path"
    - task_id: "TASK-002"
      test_binding: "pytest P:/.claude/skills/recap/tests/test_recap.py::test_handoff_first_resolution"
    - task_id: "TASK-003"
      test_binding: "pytest P:/.claude/skills/recap/tests/test_recap.py::test_subagent_filtering"
  contract_authority_reference:
    contract_sensitive: true
    packet_ref: "contract_authority_packet.packet_version=1"
  assumptions_defaults:
    - "Handoff files exist in P:/.claude/state/handoff/ or ~/.claude/state/handoff/"
    - "search-research package is importable"
  open_questions: []
```

## Consequences

**Positive:**
- Correct import path eliminates ImportError
- Handoff-first strategy provides most reliable session reconstruction
- Subagent filtering eliminates false session pollution
- Clear separation of concerns between packages

**Negative:**
- Requires fixing import path (breaking change)
- Handoff dependency means /recap fails if handoff directory is missing (graceful degradation required)

**Alternatives Considered:**

1. **Use claude-chain-miner as library** - Rejected: Package is standalone CLI, not designed for import
2. **Implement custom handoff walker in /recap** - Rejected: Duplicates existing functionality in search-research
3. **Ignore subagent transcripts at display layer only** - Rejected: Filtering should happen at collection layer to avoid processing overhead

## Implementation Notes

**Files to modify:**
- `P:/.claude/skills/recap/__init__.py` (line ~1294 for import, lines 1268-1337 for resolution logic)

**Dependencies:**
- `search-research` package must be installed and importable
- `claude-history` CLI optional (for future chat search enhancement)

**Backward compatibility:**
- Graceful degradation if handoff files don't exist (fall back to current behavior)
- No changes to output format (same session dict structure)

## Follow-up (Out of Scope)

- **Chat history search integration** - Use `claude-history` CLI for "what did we discuss" queries
- **Semantic chain enhancement** - Add optional semantic similarity for loose chain reconstruction
- **Handoff validation** - Add checksum/integrity check for handoff files
