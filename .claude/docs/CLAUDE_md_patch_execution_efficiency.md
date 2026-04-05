# Execution Efficiency Implementation

## Status: Implemented

**Primary mechanism:** Output style (`.claude/output-styles/expert.md`)  
**Observability:** Style friction detector (`hooks/style_friction_detector.py`)  
**Reinforcement:** CLAUDE.md "Execution Efficiency" section

---

## How to Use

### Activate Expert Mode

```bash
/output-style expert
```

This replaces the default system prompt with terse, action-oriented behavior:
- Verify paths before executing commands
- No permission seeking for reversible actions
- Minimal formatting (prose over tables)
- Answer literal questions only

### Check If It's Working

```bash
/hook-audit friction
```

Shows friction events if the style is too aggressive or too permissive.

### Tune Back

```bash
/output-style default      # Full revert
/output-style explanatory  # Verbose with insights
```

Or edit `.claude/output-styles/expert.md` directly for fine-tuning.

---

## Implementation Details

### Output Style (Primary)

**File:** `.claude/output-styles/expert.md`

Uses CC's native output style system with `keep-coding-instructions: true` to:
- Replace default behavioral instructions
- Keep coding-specific behaviors (testing, verification)
- Trigger turn-by-turn adherence reminders

### Friction Detector (Observability)

**File:** `hooks/style_friction_detector.py`  
**Log:** `logs/style_friction.jsonl`

Detects patterns suggesting friction:
- `permission_seeking`: User says "yes just do it" (we asked when we shouldn't)
- `too_terse`: User asks "what are my options?" (we didn't provide alternatives)
- `repeat_request`: User repeats request (we didn't act)

Integrated into `/hook-audit` dashboard as `friction` subcommand.

### CLAUDE.md Section (Reinforcement)

Lines 27-68 add "Execution Efficiency (Force Multiplier Mode)" section with:
- Verify Before Execute rules
- Answer the Question Asked guidance
- No Unsolicited Options principle
- Minimal Formatting requirements

This reinforces but does not replace the output style.

### Legacy Env Flags

These exist in `settings.json` but are NOT actively used:

```json
"USER_PREFERENCE_MODE": "expert",
"EXPERT_MODE_NO_OPTIONS_TABLES": "true",
"EXPERT_MODE_NO_PERMISSION_SEEKING": "true",
"EXPERT_MODE_MINIMAL_FORMATTING": "true",
"EXPERT_MODE_VERIFY_BEFORE_EXECUTE": "true"
```

Previously used by hook injection, now superseded by output style.

---

## Why This Architecture

| Approach | Strength | Weakness |
|----------|----------|----------|
| Output style | Replaces system prompt, native integration | Can't be toggled per-turn |
| CLAUDE.md | Persistent across sessions | Weaker than system prompt |
| Hook injection | Turn-by-turn, dynamic | Overhead, still fights training priors |
| Env flags | Easy to toggle | Requires hook to read them |

**Decision:** Output style is primary because it operates at system prompt level (strongest). CLAUDE.md reinforces. Friction detector provides observability for tuning.

---

## Feedback Loop

1. Expert mode activates via output style
2. Friction detector logs when user overrides (e.g., "yes just do it")
3. `/hook-audit friction` shows aggregate friction
4. If >30% friction is one type, tune the style or switch profiles
