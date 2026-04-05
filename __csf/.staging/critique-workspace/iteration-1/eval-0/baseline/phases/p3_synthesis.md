# Phase 3: Synthesized Refined Critique

Produce a refined version of your critique using the RNS (Results/Next Steps) format familiar from /gto.

## Input

Read the inputs via file paths:

**Original Work:** `cat "{WORK_FILE}"`
**Phase 1 Critique:** `cat "{PHASE1_FILE}"`
**Phase 2 Meta-Critique:** `cat "{PHASE2_FILE}"`

## Verification Step (MANDATORY — do not skip)

Before writing any findings, re-read the original source files and **verify every claim** in the Phase 1/2 outputs against what the code actually does. Flag and correct any finding that misrepresents the code. Specifically:

- If a finding claims code does X but it actually does Y, correct the finding with the accurate description and the correct file:line citation.
- If a finding claims code does not do Z but it does, remove or downgrade that finding.
- If a finding references a file but the relevant behavior is in a different file, update the citation.
- Do not accept Phase 1/2 output as ground truth — treat it as unverified claims requiring your own confirmation.

## Output Schema

**Important:** Render markdown properly — use formatting for headings, bold, italic, code spans, etc. Do NOT show raw markdown syntax (no `**bold**`, no code fences around the output, etc.).

Return the refined critique in this exact structure:

```
## Intent Summary
[2-3 sentences: what this work is trying to achieve]

## Health Score: XX%
[Brief assessment of overall work quality - Healthy ≥80%, Warning 50-79%, Critical <50%]

## Logical Gaps & Inconsistencies
[Items sorted by severity: CRITICAL, HIGH, MEDIUM, LOW]
1.1. [HIGH] issue description (file:line)
1.2. [MEDIUM] issue description

## Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] issue description

## Missing Obvious Actions / Best Practices
3.1. [HIGH] issue description

## Risks and Edge Cases
4.1. [MEDIUM] issue description

## Concrete Recommendations
5.1. [MEDIUM] specific change or question

## Open Questions / Unknowns
6.1. [LOW] uncertainty

## Recommended Next Steps

Organize by domain using the critique's 7 sections as domains. Use alpha-numeric sub-items. Severity is implied by domain order (domain 1 = most critical). Within each domain, sort items by severity: CRITICAL > HIGH > MEDIUM > LOW. No severity tags in sub-items.

**Format** (GTO v2 style):

```
**Recommended Next Steps**

1 (DOMAIN NAME) - Brief domain description
- 1a: Action → Manual - context (file:line)
- 1b: Action → Use /skill - context

2 (DOMAIN NAME) - Brief domain description
- 2a: Action → Manual - context

0 - Do ALL Recommended Next Steps
```

**MANDATORY FORMAT REQUIREMENTS**:
- Domain headers: `1 (DOMAIN) - description` format
- Sub-items: `1a:`, `1b:`, `2a:`, etc. under each domain
- Action format: `- 1a: Action → Manual - context` or `- 1a: Action → Use /skill - context`
- Dash prefix required for all sub-item lines
- Terminator: `0 - Do ALL Recommended Next Steps`
- No severity tags in sub-items (severity is implied by domain ordering)
