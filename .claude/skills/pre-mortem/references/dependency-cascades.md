# Step 4.5: Inter-Risk Dependency Cascades

**Purpose**: Detect when resolving one risk automatically resolves others (keystone risks).

**When to use**: OPTIONAL — Only when risks have structural dependencies (causes, blocks, enables).

**When to skip**: Most risks are independent — skip this step if no clear causal relationships exist.

## Dependency Types

| Type | Meaning | Example |
|------|---------|---------|
| `causes` | A directly creates B | "No test infrastructure" CAUSES "Can't verify fixes" |
| `blocks` | A prevents B from starting | "Missing API keys" BLOCKS "Integration testing" |
| `enables` | A is required for B | "Fix dispatch chain" ENABLES "Hook execution" |
| `triggered-by` | B occurs when A occurs | "Fallback failure" TRIGGERED-BY "API rate limit" |

## Keystone Risk Pattern

The most valuable pattern to detect: **fixing A resolves B, C, and D.**

```
RISK-A: Hook not in dispatch registry (Risk 8)
  [causes] RISK-B: Hook never runs (Risk 9)
  [causes] RISK-C: Feature silently fails (Risk 9)

Action: Fix RISK-A → All three resolved
```

Without Step 4.5, you might create separate action plans for each risk. With Step 4.5, you focus on the keystone.

## When Dependencies Don't Exist

Most solo dev pre-mortems have independent risks:

```
RISK-A: Pattern doesn't trigger (Risk 7)
RISK-B: Performance overhead (Risk 4)
RISK-C: Edge case not covered (Risk 5)
```

These are parallel concerns — no dependency relationship. Skip Step 4.5.

## Output Format

Use inline annotations in the Compact Snapshot:

```
## 🔴 WHAT'S ACTUALLY BROKEN

• CRIT-001 | Hook not in dispatch (Risk 8)
  [causes: CRIT-002, CRIT-003]
  • Missing from UNIVERSAL hooks list

• CRIT-002 | Hook never executes (Risk 9)
  [caused-by: CRIT-001]
  • Silent failure - no errors thrown

• CRIT-003 | Feature silently broken (Risk 9)
  [caused-by: CRIT-001]
  • Users see no effect, no error messages
```

## Anti-Patterns to Avoid

**Don't map:**
- "Related to" or "Similar domain" — That's categorization (Step 3), not dependency
- "Happens at same time" — Coincidence, not causation
- "Both are security issues" — That's classification, not dependency

**Only map structural relationships:**
- A must complete before B can start (blocks)
- A directly creates B (causes)
- A is prerequisite for B (enables)

## Integration Step

After Step 4 (Rate risks), ask:

> "Do any risks CAUSE, BLOCK, or ENABLE other risks?"

- If YES → Add inline annotations, proceed to Step 5
- If NO → Skip to Step 5 (Prevent top 3)

This step typically takes 30-60 seconds when dependencies exist. Skip it when risks are clearly independent.
