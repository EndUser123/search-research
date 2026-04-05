# rca v2.5.0 - CKS Pattern Auto-Learning

**Date:** 2026-02-28
**Version:** v2.4.2 → v2.5.0
**Type:** Self-improving knowledge system

## Objective

Implement automatic pattern extraction and CKS storage so rca learns from every mechanism-only search miss and becomes smarter over time.

## Problem Statement

Phases 1 and 2 provide substantial improvement (80% expected reduction), but the system doesn't learn from new patterns. Each unique symptom type requires manual template creation.

**Example:**
- Phase 2 catches "Progress(" → suggests "yt-api:"
- But if user searches for "Spinner(" → misses "spinner-status:"
- System doesn't learn this pattern for next time

## Solution

Build self-improving loop:
1. **Detect** mechanism-only search (Phase 2 already does this)
2. **Extract** pattern: mechanism → functional relationship
3. **Store** in CKS with symptom classification
4. **Query** CKS at start of RCA for suggested searches
5. **Improve**: System learns with every session

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  RCA Session Start                                          │
│  ↓                                                          │
│  Query CKS: "What functional searches relate to [symptom]?" │
│  ↓                                                          │
│  Get suggestions: ["grep('visible-output:', 'src/')"]      │
│  ↓                                                          │
│  User searches (may or may not follow suggestions)         │
│  ↓                                                          │
│  Hook detects mechanism-only → WARNING                      │
│  ↓                                                          │
│  AUTO-EXTRACT PATTERN:                                      │
│    - Symptom type (PERFORMANCE/ERROR/INTEGRATION/etc)       │
│    - Mechanism pattern searched: ["Progress("]              │
│    - Missing functional pattern: ["yt-api:"]                │
│    - Relationship: "When searching X, also search Y"        │
│  ↓                                                          │
│  STORE IN CKS:                                              │
│    Entry: {symptom, mechanism_patterns, functional_pattern} │
│  ↓                                                          │
│  Next RCA session finds this pattern automatically          │
└─────────────────────────────────────────────────────────────┘
```

## Acceptance Criteria

- [ ] Create CKS pattern extractor module
- [ ] Extend search validator hook to auto-extract and store patterns
- [ ] Add CKS query step to rca workflow (Step 1.4: Check Learned Patterns)
- [ ] Patterns classified by symptom type (5 types from Phase 1)
- [ ] Update SKILL.md with new workflow step
- [ ] Update version from 2.4.2 to 2.5.0
- [ ] Test: pattern extraction, storage, retrieval, and suggestion

## Tasks

### Task 1: Create CKS Pattern Extractor
**File:** `P:/packages/rca/skill/hooks/pattern_extractor.py` (NEW)
**Purpose:** Extract reusable patterns from mechanism-only searches

**Logic:**
```python
def extract_learning_from_mechanism_search(state: dict) -> dict:
    """
    Extract learning from mechanism-only search sequence.

    Returns:
    {
        "symptom_type": "PERFORMANCE|ERROR|INTEGRATION|INTERMITTENT|SECURITY",
        "mechanism_patterns": ["Progress(", "class Progress"],
        "functional_suggestion": "yt-api:",
        "relationship": "When searching progress implementations, also search for visible output markers",
        "confidence": 0.8,  # Based on pattern strength
    }
    """
```

**Symptom Classification Logic:**
- `Progress|Spinner|Loader` → PERFORMANCE
- `Exception|Error|Traceback` → ERROR
- `API|Client|Server|Request` → INTEGRATION
- `race|lock|async|await` → INTERMITTENT
- `auth|token|password|login` → SECURITY

### Task 2: Extend Search Validator Hook
**File:** `P:/packages/rca/skill/hooks/PostToolUse_rca_search_validator.py`
**Change:** Add CKS storage after warning

**Integration:**
```python
# After warning user
if should_warn:
    print(warning_message, file=sys.stderr)

    # NEW: Extract and store learning
    from pattern_extractor import extract_learning_from_mechanism_search
    learning = extract_learning_from_mechanism_search(state)

    # Store in CKS
    from cks_integration import store_rca_pattern
    store_rca_pattern(learning)
```

### Task 3: Create CKS Integration Module
**File:** `P:/packages/rca/skill/hooks/cks_integration.py` (NEW)
**Purpose:** Store and query patterns in CKS

**API:**
```python
def store_rca_pattern(learning: dict) -> None:
    """Store RCA pattern learning in CKS."""

def query_rca_patterns(symptom_type: str) -> list[dict]:
    """Query CKS for patterns related to symptom type."""
```

### Task 4: Add CKS Query to rca Workflow
**File:** `P:/packages/rca/skill/SKILL.md`
**Location:** After "Step 1: Problem Classification" (around line 200)
**Change:** Insert new step

```markdown
### Step 1.4: Check Learned Patterns (MANDATORY)

Before searching, check CKS for learned patterns from previous RCA sessions.

**Query CKS:**
```bash
/memory-system search "rca pattern [symptom_type]"
```

**Apply suggested functional searches:**
- CKS may suggest: "When searching Progress(, also search: yt-api:, status:, %"
- Add these to your multi-angle search from Step 1.5

**Why:** System learns from every mechanism-only miss, so you benefit from others' experience.
```

### Task 5: Update Version
**File:** `P:/packages/rca/skill/SKILL.md`
**Location:** Line 6
**Change:** `version: 2.4.2` → `version: 2.5.0`

## CKS Entry Format

```json
{
  "type": "rca_search_pattern",
  "symptom_type": "PERFORMANCE",
  "mechanism_patterns": ["Progress(", "class Progress", "def update_progress"],
  "functional_pattern": "yt-api:",
  "relationship": "When searching progress implementation, also search for visible output markers",
  "example_session": "yt-api flashing bug - mechanism-only search missed stdout writes",
  "confidence": 0.8,
  "created_at": "2026-02-28T10:00:00",
  "times_helpful": 0
}
```

## Verification

- [ ] Test 1: Mechanism-only search → pattern extracted
- [ ] Test 2: Pattern stored in CKS with correct format
- [ ] Test 3: CKS query retrieves pattern
- [ ] Test 4: Pattern suggested in next RCA session
- [ ] Test 5: Multiple patterns for same symptom don't duplicate
- [ ] Test 6: Symptom classification accurate (all 5 types)

## Success Metrics

- **Primary:** CKS contains 10+ learned patterns after 20 RCA sessions
- **Secondary:** 90% of mechanism-only searches prevented (up from 80%)
- **Tertiary:** System becomes more effective with use (measurable improvement)

## Risk Assessment

**Risk Level:** MEDIUM
- CKS dependency: requires memory-system to be available
- Pattern quality: bad extractions could pollute CKS
- Performance: CKS query on every RCA session

**Mitigation:**
- Graceful degradation if CKS unavailable
- Confidence threshold (0.7+) before storing
- Efficient caching of CKS queries
- Manual curation ability (edit/delete bad patterns)

## Rollback

If auto-learning proves problematic:
- Disable pattern extraction in hook
- Keep Phase 2 warnings (still valuable)
- Remove Step 1.4 from SKILL.md
- No code rollback needed

## Estimated Impact

- **Implementation:** 6-8 hours
- **Testing:** 2 hours
- **Documentation:** 1 hour
- **Total:** 9-11 hours

## Future Enhancements

- Pattern ranking by usefulness (times_helpful counter)
- Automatic pattern expiration if not used
- Cross-symptom pattern generalization
- Community pattern sharing (export/import CKS entries)
