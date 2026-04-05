# Lesson Capture Ecosystem - Reference

**Purpose**: Consolidated reference for all lesson capture skills and hooks.

**Created**: 2026-02-05
**Status**: Active documentation

---

## Quick Reference

| Mechanism | Type | Trigger | Storage |
|-----------|------|---------|---------|
| `/learn` | Skill | User | CKS (auto) |
| `/cks` | Skill | User | CKS |
| `UserPromptSubmit_retrospective.py` | Hook | Auto | CKS |

---

## 1. Skills (User-Initiated)

### `/learn` - Intelligent Lesson Capture (Consolidated)

**Purpose**: Adaptive lesson extraction that figures out what you actually learned using novelty detection and usefulness scoring. Consolidates functionality from `/rr`, `/retro`, and `/cooldown`.

**Features**:
- Session summary (duration, files, operations)
- What worked / what didn't work
- Novelty detection via CKS queries (prevents duplicates)
- Usefulness scoring (4 dimensions: novelty, complexity, pattern, impact)
- Threshold filtering (≥4 to store)
- Follow-up items
- Auto-stores to CKS

**Storage**: CKS (automatic)

**Usage**:
```bash
/learn              # Adaptive: figures out what you need
/learn --verbose    # Show full scoring breakdown
/learn --dry-run    # Show what would be stored
```

**Output Format**:
```markdown
============================================================
Session Summary (47 min)
============================================================
Files: 3 | Operations: 5 Edit, 2 Read

→ What Worked
   • Implemented session isolation via ConsoleHost handle

→ What Didn't Work
   • Terminal detection path mismatch

→ Lessons Found (2 new, 0 already known)

1. [score: 7] terminal_detection (NEW)
   SessionStart writes to %TEMP%/claude_terminal_id.txt but
   skill_execution_state reads from P:/.claude/state/ (wrong path)
   → CKS: pattern_abc123

2. [score: 6] session_isolation (NEW)
   ConsoleHost handle provides unique terminal ID across all
   PowerShell sessions, more reliable than PID-based detection
   → CKS: pattern_def456

→ Follow-Up Items
   1. Update skill_execution_state.py to read from %TEMP%
   2. Test cross-terminal isolation
```

**Pipeline Architecture**:
```
transcript → candidates → novel → scored → keepers
             [patterns]   [CKS]   [score]  [≥4]
```

**Quality Filter** (What IS a lesson):
- Non-obvious implementation details affecting architectural decisions
- Patterns that change future behavior
- Root causes that required investigation
- Decisions with trade-offs

**What is NOT a lesson**:
- Routine operations: "ran pytest", "checked git"
- One-off fixes: "fixed typo on line 42"
- Facts/outputs: "created 5 docs"
- Obvious statements: "read the file"

---

### `/cks` - Constitutional Knowledge System

**Purpose**: Direct storage for patterns, memories, decisions, insights.

**Entry Types**:
- `memory` - Session memories
- `pattern` - Repeat/Avoid patterns
- `code` - Code snippets
- `knowledge` - Documentation
- `correction` - Anti-patterns
- `decision` - Decisions made
- `commitment` - Commitments
- `insight` - Insights
- `learning` - Learnings

**Usage**:
```bash
/cks add "Pattern: Use X for Y. Results: Z benefit."
/cks search "query"
/cks recent
```

---

## 2. Hooks (Automatic)

### `UserPromptSubmit_retrospective.py`

**Event**: UserPromptSubmit (before prompt processing)

**Purpose**: Automatically detects lesson-worthy content in session transcript. Uses intelligent pipeline with novelty detection and usefulness scoring.

**Cooldown**: 30 minutes (prevents spam)

**Detection Logic**:
- Reads session transcript (last 50 entries)
- Uses `LessonExtractor` pipeline (same as `/learn`):
  - Causal pattern detection
  - Novelty checking via daemon CKS queries
  - Usefulness scoring (4 dimensions: novelty, complexity, pattern, impact)
  - Threshold filtering (≥4)
- Fallback to `retro_common.extract_lesson_segments()` if daemon unavailable
- Checks if topics already covered in today's SKILL.md lessons (prevents false positives)
- Spawns `lesson_extractor_claude.py` worker in background

**Location**: `P:\.claude\hooks\UserPromptSubmit_retrospective.py`

**Worker**: `P:\__csf\src\core\lesson_extractor_claude.py`

**State File**: `P:\.claude\hooks/logs/retrospective/last_detection.txt`

**Enhanced**: 2026-02-05 - Now uses `LessonExtractor` for intelligent extraction with novelty detection and usefulness scoring (same pipeline as `/learn`).

---

## 3. Recommended Best Practice

### Optimal Workflow

**During Session**:
- Automatic hook detects lesson-worthy content
- Background worker extracts with novelty detection and usefulness scoring
- High-value lessons (≥4) auto-stored to CKS
- Zero friction, no user action needed

**End of Session**:
```bash
/learn
```
This provides:
- Session summary (duration, files, operations)
- What worked / what didn't work
- Lessons found (new vs already known)
- Follow-up items

### When to Use What

| Situation | Use |
|-----------|-----|
| End of session / end of day | `/learn` |
| Store specific pattern/decision | `/cks add "..."` |
| Search CKS | `/cks "query"` |
| Let automation handle it | Nothing (hooks auto-detect) |

### What NOT to Do

- Don't run `/learn` multiple times per session (novelty check prevents duplicates)
- Don't manually store patterns that `/learn` already captured
- Don't obsess over score - threshold (≥4) filters noise appropriately

---

## 4. File Locations

| Component | Path |
|-----------|------|
| `/learn` skill | `P:\.claude\skills\learn\SKILL.md` |
| `/learn` script | `P:\.claude\skills\learn\learn.py` |
| `/cks` skill | `P:\.claude\skills\cks\SKILL.md` |
| Retrospective hook | `P:\.claude\hooks\UserPromptSubmit_retrospective.py` |
| Lesson extractor | `P:\__csf\src\core\lesson_extractor.py` |
| Lesson worker | `P:\__csf\src\core\lesson_extractor_claude.py` |
| Retro common | `P:\__csf\scripts\retro_common.py` |

---

## 5. Schema Reference

### `/learn` Output Format

```markdown
[Session Summary (duration)]
Files: N | Operations: N Edit, N Read

→ What Worked
   • [Success]

→ What Didn't Work
   • [Problem]

→ Lessons Found (N new, N already known)

N. [score: X] category (NEW/KNOWN)
   [Lesson text - truncated to 100 chars]
   → CKS: [entry_id or "success"]

→ Follow-Up Items
   N. [Action item]
```

### `/cks` Manual Storage Format

```bash
/cks add "Pattern: Use X for Y. Results: Z benefit."
/cks add "Anti-pattern: X. Problem: Y. Alternative: Z."
/cks add "Memory: Q: What? A: Answer."
```

---

## 6. Troubleshooting

### Retrospective hook firing too often

- Check cooldown file: `P:\.claude\hooks/logs/retrospective/last_detection.txt`
- Should be 30 minutes between detections

### `/learn` not finding lessons

- Run with `--verbose` to see scoring breakdown
- Run with `--dry-run` to see what would be stored
- Check if transcript path is correct
- Lesson quality filter may be filtering obvious facts

### Daemon not responding (novelty check failing)

- Check if semantic daemon is running: `/daemon status`
- Hook will fall back to `retro_common` if daemon unavailable
- Score threshold may be too high (default: 4)

---

## 7. Design Notes

### Current Architecture (2026-02-05 Simplification)

**Consolidated from 6 mechanisms to 3:**

| Before | After |
|--------|-------|
| `/rr`, `/retro`, `/cooldown`, `/cks add`, retrospective hook, CKS storage hook | `/learn`, `/cks`, retrospective hook |

**Strengths**:
- Single intelligent command (`/learn`) replaces 3 separate skills
- Automatic hook eliminates friction
- Novelty detection prevents duplicate lessons
- Usefulness scoring filters low-value content
- CKS centralized storage (searchable, semantic)

**Key Design Decisions**:
1. **CKS > SKILL.md** - Centralized knowledge base is superior to scattered files
2. **Intelligence > Manual** - Novelty detection and usefulness scoring reduce cognitive load
3. **Automatic + Manual** - Hook catches most lessons, `/learn` for end-of-session ritual

**Removed**:
- `/rr` - Merged into `/learn`
- `/retro` - CKS is superior to SKILL.md storage
- `/cooldown` - `/learn` provides same functionality
- `PostToolUse_rr_cks_storage.py` - Redundant (hook handles CKS storage)

---

## 8. Related Documentation

- `/learn` SKILL.md - Complete skill documentation
- `P:/__csf/src/core/lesson_extractor.py` - Core pipeline implementation
- `P:/__csf/src/daemons/CLAUDE.md` - Daemon documentation for semantic search
