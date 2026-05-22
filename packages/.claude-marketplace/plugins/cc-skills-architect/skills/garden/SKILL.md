---
name: garden
version: "1.0.0"
status: "stable"
description: Knowledge hygiene for CKS and SKILL.md to prevent knowledge entropy
category: maintenance
triggers:
  - /garden
  - "knowledge cleanup"
  - "prune patterns"
aliases:
  - /garden

suggest:
  - /cks
  - /chs
  - /cleanup
---

# /garden – Knowledge Hygiene

## Purpose

Keep your knowledge base (CKS + SKILL.md) clean and high-signal by:
- Merging duplicates.
- Archiving stale entries.
- Promoting high-value patterns.

## When to Use

- On a regular cadence (e.g., weekly).
- After periods with many new lessons or CKS entries.

## Inputs

- Optional scope:
  - `cks` – CKS entries only.
  - `skills` – SKILL.md lessons only.
  - `all` – both (default).
- Optional time window:
  - e.g., "last 30 days", "this month".

## Dependencies

- Skills / components:
  - CKS semantic search and metadata (timestamps, usage counts).
  - SKILL.md parser for Neural Cache or Lessons sections.
  - `/chs` (optional) for usage examples.

## High-Level Behavior

### 1. Inventory
For the chosen scope/time window:
- List CKS entries (id, title, created_at, last_used_at, usage_count).
- List SKILL.md lessons (skill, section, text, last touched).

### 2. Issue Detection
- **Duplicates or near-duplicates**: Cluster by semantic similarity
- **Stale entries**: Old + low usage or superseded patterns
- **Hot entries**: Frequent usage, recent high value (e.g., mentioned in /rr, /value, /ship, /skeptic)

### 3. Action Proposals
For each cluster or entry:
- Duplicate clusters → propose a canonical merged version
- Stale entries → propose archive/demotion
- Hot entries → propose promotion:
  - E.g., move to CLAUDE.md, skill docs, or add as rule/heuristic

### 4. Interactive Confirmation (Optional)
Present a concise list with actions:
- `[merge]`, `[archive]`, `[keep]`, `[promote]`, `[skip]`

Apply chosen actions:
- Update CKS entries.
- Edit SKILL.md.
- Optionally log changes.

### 5. Verification & Summary
Re-scan a small sample to verify changes.
Output a short summary:
- Number of merges, archives, promotions.
- Notable promoted patterns.

## PHASE STRUCTURE

```
PHASE 1: INVENTORY (Generation) — List CKS entries, SKILL.md lessons
    ↓ STOP: Present inventory before action proposals
PHASE 2: ISSUE DETECTION (Validation) — Identify duplicates, stale, hot entries
    ↓ STOP: Present findings before proposing actions
PHASE 3: ACTION PROPOSALS (Generation) — Propose merge/archive/promote actions
    ↓ STOP: Present proposed actions for user confirmation
PHASE 4: INTERACTIVE CONFIRMATION (Validation) — User confirms/rejects actions
PHASE 5: APPLY + VERIFY (Validation)
```

**STOP conditions separate each phase:**
- Between PHASE 1 and PHASE 2: STOP after inventory (present before analysis)
- Between PHASE 2 and PHASE 3: STOP after issue detection (present findings before actions)
- Between PHASE 3 and PHASE 4: STOP after proposals (await user confirmation)
- Between PHASE 4 and PHASE 5: STOP if user rejects proposals

**Key separation**: Detection is Validation. Proposals are Generation. Application is Validation.

## Output Format

- "Garden report" including:
  - Summary counts (merged/designived/promoted).
  - A brief list of key changes.
  - Optional recommended future gardening focus (e.g., a specific skill or topic that's noisy).

## Evidence-First Principles

### E1 — Evidence before claims
Before claiming code is absent, unchanged, or non-existent — search the codebase and verify with tools first. Claims of absence are only valid after confirmed Read/Grep/git failures.

### E4 — Investigate before asking
Do NOT answer without reading relevant source files first. Do not ask the user for information you can obtain yourself via Read, Grep, Bash, git, or available MCP tools.

### E5 — Anti-lazy escape hatch
Prohibited:
- "I assume", "I think", "probably" without tool verification
- Claiming something doesn't exist without confirmed tool failure
- Skipping evidence gathering because the answer seems obvious

## Notes

- Start conservative (more "propose" than "auto-apply").
- Over time, you can tighten heuristics once you trust the behavior.
