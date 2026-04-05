# Second-Order Effects Analysis

**Purpose**: Most failure analysis stops at first-order effects. Real disasters come from cascading consequences.

**Technique**: Ask "And then what?" 3-5 times for each high-likelihood cause.

**Required (v3.6)**:
For each risk with score ≥ 6 (High or Medium-High):
- ✅ **Trace cascade to minimum 3 steps**
- ✅ **Classify cascade depth** (Shallow/Medium/Deep)
- ✅ **Boost priority for Deep cascades** (even if likelihood is Medium)

**IF cascade depth < 3**: INCOMPLETE ANALYSIS - Continue tracing until minimum depth reached.

## Example

```
First order: "Skip writing tests"
→ Second order: "Bugs slip into production"
→ Third order: "Fixing bugs takes 10x longer than writing tests"
→ Fourth order: "Project delays accumulate, we rush even more"
→ Fifth order: "Vicious cycle of tech debt and shortcuts"

CASCADE DEPTH: DEEP (5 steps)
PRIORITY BOOST: Even if likelihood is Medium, Deep cascade → High priority
```

## Patterns to Look For

- Compensating behaviors that create new problems
- Time borrowing (trading quality for speed → paying back with interest)
- Hidden feedback loops (fixes that make the root cause worse)

## Cascade Depth Classification

- **Shallow** (1-2 steps): Localized failure, easy to recover
- **Medium** (3-4 steps): Affects multiple subsystems
- **Deep** (5+ steps): System-wide collapse, prioritize prevention

## Output Format

Add cascade depth classification to each high-risk item:

```
[RISK:6] [Failure cause] - CASCADE: DEEP (5 steps)
```
