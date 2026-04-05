# Verbalized Sampling + Calibrated Confidence Prompting

## Verbalized Sampling (VS)

**Purpose**: Generate diverse, calibrated failure hypotheses by explicitly enumerating multiple distinct failure modes per risk category.

**VS Prompt Template**:
```
List 5 different failure modes for each risk category. For each, assign P(failure).
Show your probability distribution across the 5 modes.

Example output format:
Risk Category: Authentication bypass
- Mode 1: Token expiry race (P=0.15)
- Mode 2: Session fixation (P=0.08)
- Mode 3: Privilege escalation via role confusion (P=0.20)
- Mode 4: Credential stuffing (P=0.10)
- Mode 5: OAuth state parameter tampering (P=0.05)
```

**When to use**:
- Step 2 (Brainstorm causes) — before enumerating specific failures
- Step 2.5 (Cascade analysis) — before tracing cascade paths
- When a risk category feels "obvious" — force enumeration of 5 distinct modes

**Why it works**: LLMs anchor on the first plausible failure. VS breaks anchoring by requiring explicit diversity in the sample.

---

## Calibrated Confidence Prompting (CCP)

**Purpose**: Make probability estimates explicit and range-checked, reducing overconfident single-point estimates.

**CCP Fields** (required output for each risk item):

| Field | Format | Range | Purpose |
|-------|--------|-------|---------|
| `likelihood%` | integer | 0-100 | Estimated probability this risk materializes |
| `confidence%` | integer | 0-100 | Confidence in the likelihood estimate |
| `uncertainty notes` | text | — | What could shift the estimate higher/lower |

**Example**:
```
- RISK-003: Database connection pool exhaustion
  likelihood%: 65
  confidence%: 70
  uncertainty notes: "65% based on current load tests; could spike to 85% under
    traffic burst, or drop to 40% if connection pooling is implemented"
```

**Range validation**: `likelihood%` and `confidence%` must be 0-100. This is documentation requirement (human-interpreted guidance), not enforced by quality gate.

**Integration**: CCP fields append to the existing Step 4 risk format. They are additional metadata, not replacements for the Likelihood × Impact score.

---

## Combining VS + CCP

VS generates diverse hypotheses. CCP calibrates each one. The combined workflow:

1. **VS**: For each risk category, enumerate 5 distinct failure modes
2. **CCP**: Assign likelihood%, confidence%, and uncertainty notes to each mode
3. **Selection**: Choose top 3-5 by adjusted score (likelihood% × confidence% / 100)

**Adjusted score formula**: `adjusted = likelihood% × confidence% / 100`

This penalizes high-likelihood estimates with low confidence, prioritizing well-calibrated bets over confident guesses.
