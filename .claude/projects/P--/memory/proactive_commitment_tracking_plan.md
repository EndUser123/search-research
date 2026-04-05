# Plan: Proactive Commitment Tracking — Surface Gaps Before User Complains

## Context

The user said: "1 shouldn't need to rely on feedback from the user, is that possible?"
The intent is **proactive surfacing** — the system notices when stated commitments
weren't fulfilled and surfaces them *before* the user has to point it out.

Currently, `SessionOutcomeDetector` detects uncompleted goals but only runs when
`/gto` is explicitly invoked. This is reactive. The gap: no proactive surfacing
on every session end.

## What "Proactive" Means

1. **Same-session proactive** (Path A): Agent states "I'll do X" → later, system
   interrupts before allowing unrelated work. High friction, requires interrupt
   mechanism.

2. **Next-session proactive** (Path C): At session end, detect stated commitments
   that weren't completed → persist to terminal-scoped state. At next session
   start, surface them before first prompt. Zero friction within session, natural
   continuity across sessions.

3. **Orchestrator registry** (Path B): Maintain a running commitment registry during
   the session. Tracks agent promises explicitly. Most precise but requires
   orchestrator changes.

**Recommendation: Path C first, Path A as feature-flagged Phase 2.**

Path C (next-session) is low friction, builds on existing patterns, and solves
the core complaint — the user doesn't have to re-explain what they wanted.
Path A (same-session interrupt) is higher value but higher complexity; defer
until Path C is validated.

## Architecture

### Data Flow

```
User says "I want to build X"
    → SessionOutcomeDetector patterns (TASK_INTENT_PATTERNS) detect it
    → commitment is added to CommitmentTracker (in-memory during session)
    → Session ends (any stop, not just /gto)
    → StopHook_commitment_tracker reads transcript
    → Checks: was X completed? (completion signal patterns in subsequent turns)
    → If not completed: persists to terminal-scoped state file
    → Next session starts
    → SessionStart_commitment_tracker loads prior uncompleted commitments
    → Surfaces via injected context BEFORE first prompt
```

### New Module: `commitment_tracker.py`

Location: `P:\.claude\skills\gto\lib\commitment_tracker.py`

```python
@dataclass
class TrackedCommitment:
    content: str
    turn_number: int
    category: Literal["user_goal", "agent_promise", "deferred_item"]
    completed: bool = False
    completion_turn: int | None = None

class CommitmentTracker:
    # Reuses SessionOutcomeDetector.TASK_INTENT_PATTERNS for detection
    # Reuses SuspicionDetector.COMPLETION_SIGNALS for completion checking

    def __init__(self, terminal_id: str):
        self.terminal_id = terminal_id
        self.commitments: list[TrackedCommitment] = []

    def scan_transcript(self, transcript_path: Path) -> list[TrackedCommitment]:
        """Scan transcript for stated commitments and completion signals."""
        ...

    def get_uncompleted(self) -> list[TrackedCommitment]:
        ...

    def persist(self) -> None:
        """Save uncompleted to terminal-scoped state file."""
        # Path: ~/.claude/.evidence/gto-commitments-{terminal_id}.json

    def load_prior(self) -> list[TrackedCommitment]:
        """Load uncompleted from prior session."""
        ...
```

### Hook: `StopHook_commitment_tracker.py`

- Registered in `Stop_router.py` (like `StopHook_sequential_thinking`)
- Runs on **every** stop, not just GTO stops
- Uses `emit_tag("COMMITMENT")` to tag response if commitments detected
- Uses reason injection for surfacing when stopping with commitments
- Falls back gracefully if no transcript available
- Feature flag: `PROACTIVE_COMMITMENT_TRACKER_ENABLED` (default: true)

### Hook: `SessionStart_commitment_tracker.py`

- Registered in `SessionStart.py` (settings.json)
- Runs at session start BEFORE first prompt
- Loads prior session's uncompleted commitments
- Injects via `additionalContext` if any found
- Content: "Prior session had N uncompleted commitments: [list]"

### State Persistence

- Path: `~/.claude/.evidence/gto-commitments-{terminal_id}.json`
- Schema:
  ```json
  {
    "terminal_id": "console_abc",
    "session_end": "2026-03-28T...",
    "commitments": [
      {
        "content": "build the authentication module",
        "turn_number": 3,
        "category": "user_goal",
        "completed": false
      }
    ]
  }
  ```
- Terminal-scoped for multi-terminal safety
- Single entry per terminal (last session's commitments)

### Integration with Existing Code

1. **Reuse `SessionOutcomeDetector.TASK_INTENT_PATTERNS`** — These already detect
   "I want to", "let's add", "we need to". Import and reuse directly.

2. **Reuse `SuspicionDetector.COMPLETION_SIGNALS`** — For checking if a commitment
   was completed in subsequent turns.

3. **Supplement, don't replace `SessionOutcomeDetector`** — SOD runs at `/gto` time
   for formal gap reports. CommitmentTracker runs at every stop for proactive
   surfacing. Different timing, different output mechanism, complementary.

4. **Path A (future)**: Add `UserPromptSubmit` hook that checks if the current
   prompt relates to an unaddressed commitment. If not, inject advisory:
   "Prior commitment not yet addressed: X"

### Feature Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `PROACTIVE_COMMITMENT_TRACKER_ENABLED` | true | Master switch |
| `PROACTIVE_COMMITMENT_SESSION_START` | true | Surface at session start |
| `PROACTIVE_COMMITMENT_SURFACE_ON_STOP` | true | Surface at session end |

### What the User Sees

**At session end (StopHook)**:
If commitments detected and not completed:
```
[COMMITMENT]
Session closing — 2 commitments not yet addressed:
  1. [user_goal] build the auth module (stated at turn 3)
  2. [deferred_item] add logging (deferred at turn 7)

These will be surfaced at next session start.
```

**At next session start (SessionStart)**:
```
Prior session had 2 uncompleted commitments:
  • build the auth module (user_goal)
  • add logging (deferred_item)

Address these now? Or defer further?
```

## Implementation Steps

### Phase 1 (this task — design only)
- [x] Analyze existing patterns (SessionOutcomeDetector, SuspicionDetector)
- [x] Design data structures and state persistence
- [x] Design hook integration points
- [x] Decide: Path C (next-session) primary, Path A Phase 2

### Phase 2 (implementation)
1. Create `lib/commitment_tracker.py` with `CommitmentTracker` class
2. Reuse `SessionOutcomeDetector.TASK_INTENT_PATTERNS` for detection
3. Reuse `SuspicionDetector.COMPLETION_SIGNALS` for completion checking
4. Create `StopHook_commitment_tracker.py`
5. Register in `Stop_router.py`
6. Create `SessionStart_commitment_tracker.py`
7. Register in `SessionStart.py` (settings.json)
8. Add `PROACTIVE_COMMITMENT_TRACKER_ENABLED` to settings.json
9. Write tests

### Phase 3 (Path A — future work)
- Add `UserPromptSubmit` hook for same-session interrupt
- Feature-flag behind `PROACTIVE_COMMITMENT_INTERRUPT_ENABLED`
- Only high-confidence cases (e.g., "I want to build X" followed by no related
  file edits after 3+ turns)

## Key Design Decisions

1. **Why not Path B (orchestrator registry)?**
   Requires modifying `gto_orchestrator.py` to track agent promises during
   execution. Complex coupling. Path C achieves the same outcome (surfacing
   uncompleted commitments) with simpler architecture.

2. **Why not Path A first?**
   Same-session interrupt is high friction. If the system is wrong, the user
   feels pestered. Path C is zero friction within session and surfaces at
   the natural boundary (next session start).

3. **Why reuse SessionOutcomeDetector patterns?**
   SOD already has well-tested regex patterns for "I want to", "let's add",
   "we need to". Reusing them ensures consistency and reduces new code.
   The completion signal patterns from SuspicionDetector are also directly
   applicable.

4. **Why terminal-scoped state?**
   Multi-terminal safety — each terminal has its own commitment history.
   Commitments are per-terminal, not global.
