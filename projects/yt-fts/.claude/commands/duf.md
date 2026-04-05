---
id: duf
aliases: ["/duf"]
category: command
---

# /duf - Did You Forget?

## ⚡ EXECUTION DIRECTIVE

**First, clear any existing DUF notification:**
```bash
python P:/__csf.nip/scripts/clear-notifications.py --type duf 2>/dev/null || true
```

**Then run these four cognitive checks:**

### 1. Pre-mortem
> It's next week. Something broke because of your changes. What was it?

Don't say "nothing." Force yourself to imagine a specific failure:
- A user hit an edge case you didn't handle
- A dependency you touched broke something downstream
- A test you didn't write would have caught this

### 2. Inversion
> What's the EASIEST way this could fail?

Not the unlikely edge case—the obvious failure you're blind to:
- Missing import?
- Typo in a string?
- Wrong file path?
- Forgot to save?

### 3. Blast Radius
> What depends on what you changed?

Trace the dependency chain:
- What imports/calls the code you modified?
- What configs reference files you touched?
- What tests cover this path?
- What documentation mentions this?

### 4. Assumption Audit
> What did you assume without verifying?

List assumptions you made:
- "This function handles nulls" — did you check?
- "This test covers that case" — did you run it?
- "This config is correct" — did you validate?

## Response Format

```
## Pre-mortem: What Broke?
[Specific failure scenario]

## Inversion: Easiest Failure?
[Obvious thing that could go wrong]

## Blast Radius
- [Dependent 1]: [Status/Risk]
- [Dependent 2]: [Status/Risk]

## Assumptions Made
- [Assumption]: [Verified? How?]

## Actions
- [ ] [Thing to check/fix/verify]
```

## The Point

You forget things. Your "perfect" solution has gaps.

These four techniques force different thinking modes:
- **Pre-mortem**: Future hindsight (imagination)
- **Inversion**: Flip the question (find obvious failures)
- **Blast radius**: Trace dependencies (systematic)
- **Assumption audit**: Surface beliefs (epistemics)

Don't rush. Each check takes 30 seconds but catches different blind spots.
