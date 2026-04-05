---
name: rns
description: Dynamic actions from findings w/ recover/prevent/realize tags, priority, file:line. Converts unstructured LLM output to selectable RNS actions.
version: 1.1.0
triggers:
  - "/rns"
  - "/rns {text}"
  - "turn this into actions"
  - "extract action items"
  - "what should I do about"
  - "RNS"
supports_multiple: true  # multiple findings per input; simultaneous invocations deduplicate by (description_hash, domain, action)
enforcement: advisory
persistence: none
scope: session
---

# RNS — Recommended Next Steps from Arbitrary Output

## Purpose

Convert any LLM output into a structured Recommended Next Steps (RNS) format with selectable actions. When you get output you don't like — or that has implicit actions buried in it — use `/rns` to extract and enumerate them.

## When to Use

- Output contains findings, recommendations, or implied actions
- User says "turn this into actions" or "what should I do about X"
- Long output with multiple distinct action items
- Post-mortem, critique, review, or analysis output with gaps to fix

## How to Use

```
/rns {optional pasted text or @reference}
```

If no text is provided, RNS will analyze the most recent LLM output in the conversation.

## Output Format

RNS outputs a **dynamic-domain, flat-numbered** action list:

```
🔧 QUALITY
  [recover/high] QUAL-001 Fix concurrent save registry integrity test @ test_critique_io_concurrent.py:89
  [prevent/med] QUAL-002 Add Phase 2/3 filename round-trip tests @ test_critique_io.py

📄 DOCS
  [realize/low] DOC-001 Update SKILL.md with Phase 1 completion gate @ SKILL.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0 — Do ALL Recommended Next Actions (N items)
```

### Format Rules

| Aspect | Rule |
|--------|------|
| **Domain grouping** | Dynamic — only domains with findings appear |
| **Section headers** | Emoji + domain name — rendered as text, no fences |
| **Item numbering** | Flat globally — QUAL-001, DOC-001, not hierarchical |
| **Item format** | `[effort] [R:reversibility] ID Description @ file:line` |
| **File references** | `@ file:line` suffix when available |
| **Do All directive** | 0 — Do ALL Recommended Next Actions (N items) |

### Domain Emoji Mapping

| Domain | Emoji |
|--------|-------|
| quality / code_quality | 🔧 |
| tests / testing | 🧪 |
| docs / documentation | 📄 |
| security | 🔒 |
| performance | ⚡ |
| git | 🐙 |
| deps / dependencies | 📦 |
| other | 📌 |

## Step 1 — Collect Input

If `/rns` was called with inline text, use that. If called alone, read the last assistant message in the conversation transcript. The "last" message is the most recent complete assistant message — do not read a message that is mid-sentence or still in progress. After context compaction, verify the message boundary is intact before analyzing.

If a file path is provided (e.g., `@p3.md`), read that file.

**Input signals to extract actions from:**
- Explicit recommendations ("you should X", "consider Y")
- Implicit gaps ("missing Z", "doesn't handle W")
- Problem statements ("X is broken", "Y fails when Z")
- Severity ratings (CRITICAL, HIGH, MEDIUM, LOW)
- Findings labeled with IDs (COMP-001, TEST-001, etc.)
- Anything the user has expressed dissatisfaction with

## Step 2 — Classify Each Finding

For each action item extracted, classify:

| Field | Values | How to Determine |
|-------|--------|------------------|
| **Domain** | quality, tests, docs, security, performance, git, deps, other | What type of work is needed |
| **Action** | recover, prevent, realize | recover=fix something broken; prevent=guard against future failure; realize=capture opportunity/extension |
| **Priority** | critical > high > medium > low | Explicit label or implied severity |
| **Effort** | ~2min, ~5min, ~15min, ~30min, ~1hr | Estimated from scope |
| **Reversibility** | 1.0–2.0 score | See Reversibility Scale below |

## Step 3 — Check for Dependencies

Some findings may be related. Look for:
- `[caused-by: ID]` — finding is a consequence of another (use singular form)
- `[blocks: ID]` — finding prevents another from being resolved

When dependencies exist, order them so cause-before-effect.

## Step 4 — Render RNS

Group findings by domain. Sort each domain by action (recover → prevent → realize), then by priority (critical → high → medium → low).

If a finding has dependencies, render dependency annotation on the line after the finding.

## Step 5 — Present with Selection Semantics

After rendering the RNS list, add:

```
Select: {number} or {domain-id} or 0 for all
```

- Selecting an item number executes that single action
- Selecting a domain ID (e.g., "🔧") executes all items in that domain
- Selecting "0" executes ALL items

### Machine-Parseable Format (Optional)

For downstream skill chaining, append `<!-- format: machine -->` to the output to render pipe-delimited records:

```
RNS|D|1|domain-label|emoji
RNS|A|1a|domain|E:5|recover/high|action description|file:line
RNS|Z|0|NONE
```

Where: `RNS|D|` = domain header, `RNS|A|` = action item, `RNS|Z|` = terminator. Fields: `domain-num|action-num|[domain|E:effort|action/priority|description|file:line]`.

## Error Handling

| Scenario | Behavior |
|---------|----------|
| Empty input (no text, no file, no recent output) | Return empty RNS with message: "No input provided. Use `/rns {text}` or `/rns @file`." |
| No extractable findings | Return empty RNS with message: "No actionable findings found in input." |
| Referenced file does not exist | Log as warning, skip item, include in RNS as orphaned with warning tag |
| Unresolved dependency ID | Report as orphaned dependency note below the affected item |
| Duplicate findings (same description, domain, action) | Deduplicate — keep the one with higher priority or severity |

## Constraints

- Do NOT fabricate file paths or line numbers. Only cite where evidence supports it.
- If a finding cannot be made concrete (no file, no scope), phrase it generically but still include it.
- Do NOT skip findings because they're "obvious" — include everything.
- Do NOT invent severity ratings not present in the source. Infer only when the source implies but doesn't label.
