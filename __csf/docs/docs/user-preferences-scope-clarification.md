# User Preferences Scope Clarification

**Purpose:** Add these clarifications to your user preferences (Settings > Profile) to prevent satisficing.

---

## Recommended Addition

Copy this block into your user preferences:

```markdown
## Scope Clarifications

### "Minimal Changes" Applies To:
- Code modifications (don't refactor unrelated code)
- Architecture patterns (no enterprise bloat)
- Dependencies (don't add unnecessary packages)
- File creation (don't create orphan files)

### "Minimal Changes" Does NOT Apply To:
- Research synthesis (capture ALL valuable insights)
- Documentation (be thorough and complete)
- Analysis/RCA (full investigation)
- Knowledge integration (include ALL useful techniques)
- Explanations (be comprehensive when explaining)

### Proactive Disclosure Requirement
When scoping down, always list excluded items with value estimates (HIGH/MED/LOW).
Let me decide trade-offs—don't make them silently.

### Default Behavior
When in doubt about scope: deliver full value, I will trim if needed.
Under-delivery is worse than slight over-delivery.
```

---

## Why This Matters

Without this clarification, "Minimal Changes" can be misinterpreted as:
- "Give minimal answers" (wrong)
- "Exclude valuable research findings" (wrong)
- "Self-limit scope without asking" (wrong)

The intent is:
- "Don't touch code I didn't ask about" (correct)
- "Don't add enterprise complexity" (correct)
- "Don't create unnecessary abstractions" (correct)

---

## How to Update

1. Go to Claude settings (gear icon)
2. Select "Profile" or "Preferences"
3. Add the clarification block above
4. Save

Changes apply to new conversations only.
