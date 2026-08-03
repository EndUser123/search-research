---
thread_id: close-scanner-architecture-and-root-causes-20260722
parent_handoff_path: none
current_session_id: 019f821c-854e-76c1-a755-add284838bdf
current_terminal_id: console
produced_at: 2026-07-22T16:30:00Z
status: CLOSED
handoff_type: investigation
assigned_to: unassigned
accurate_as_of_head: b9ff02f
---

# Handoff: /close scanner architecture + root-cause chain (levels 1-5)

## Objective (one sentence)

Capture the full root-cause analysis (5 levels deep) from the /tp critique of `/close`'s git_state gate failure — plus the non-regex alternative for the scanner — so a fresh session can implement the optimal long-term fix, not a band-aid.

## The incident

During `/close`, the scanner reported "1053 uncommitted files" (needs_attention). The LLM (end of a massive session) resolved the gate by saying "noting in Other sessions'" — acknowledging without acting. The operator caught this and pushed back: "why isn't there a tree row with a red X?" This triggered a 5-level root-cause analysis.

## Root cause chain (levels 1-5)

### Level 1: Symptoms (what happened)
- RC1: `.data/` mixes durable data with generated cache (979 wiki stubs in the same tree as hand-authored concepts)
- RC2: Scanner is a counter, not a diagnostician (counts files but doesn't categorize or recommend)
- RC3: The LLM guessed about qmd architecture instead of verifying (contradictory "needed" vs "noise")
- RC4: Gate guidance allows "acknowledgment as resolution" despite Hard Constraint #4
- RC5: No principle distinguishes "what belongs in git" from "what belongs on disk"

### Level 2: Mechanisms (why each happened)
- RC1: `index_skills.py` puts stubs in `.data/wiki/sources/` because the wiki schema said "sources live there" — but the schema meant *ingested evidence*, not *generated stubs*. Two meanings of "sources" collided.
- RC2: The scanner was designed as "evidence collector, let the LLM judge." Assumes a fresh, attentive LLM. Got an overloaded one at the end of a 13-gate session.
- RC3: Treated "I know where the script writes" as equivalent to "I know how qmd works." Never ran the 30-second verification (delete stubs, run `qmd search`).
- RC4: Gate guidance was written thinking about detection ("what should trigger needs_attention"), not about output ("what does the operator need to receive").
- RC5: `.gitignore` evolved through incremental patching. Each edit was locally rational; nobody asked for the principle.

### Level 3: The common pattern
Every RC has the same shape: **an agent solved an immediate problem without understanding the system it was modifying.**

### Level 4: Why agents do this
The host has Observe-Before-Propose, but its scope is wrong. It fires on *structural proposals* (file layout, naming) but NOT on infrastructure edits (.gitignore changes, script output paths, gate logic, scanner functions). These feel like local edits, not architecture — so the observe rule never triggers.

### Level 5: The deepest cause
The LLM optimizes for output production over system understanding. Producing a fix *feels like progress*; understanding the system *feels like delay*. But output without understanding produces debt. This is the identical pattern across every failure this session (edit persistence, API guessing, DGemma location, git noise, gate resolution).

## Non-regex alternatives for the scanner

The scanner uses regex to extract structured data from semi-structured markdown. Non-regex alternatives (from cheapest to most correct):

| Approach | What | Cost |
|----------|------|------|
| **YAML frontmatter parsing** | `yaml.safe_load()` on frontmatter instead of regex-scraping `current_session_id:` | Trivial (stdlib) |
| **Section-based parsing** | Split by `## ` headings; parse each known section as a unit | Low |
| **Structured handoff fields** | Move work_status/classification into YAML frontmatter (eliminates extraction) | Medium (schema change) |
| **Python-frontmatter library** | Proper parser for YAML + markdown body | Trivial (vendor or pip) |

**Optimal fix:** stop scraping prose with regex. Parse the YAML frontmatter (which already exists) with `yaml.safe_load()`. For data currently in prose (work_status), move to frontmatter. Body text is only for free-text analysis (file path extraction can use `Path()` validity checks).

## What needs to be built (the fix sequence)

### Task 1: Verify qmd architecture (RC3 — blocks everything)
```
1. Delete (or move) .data/wiki/sources/skills/ stubs
2. Run: qmd search "test topic" -c wiki
3. If results return → stubs are in qmd.db; they only need to exist during indexing
4. If no results → qmd reads them live; path change must update qmd config
```
30 seconds. Everything else depends on this.

### Task 2: Establish the git/disk/tmp principle (RC5)
Add to `P:/AGENTS.md`:
- **In git:** hand-authored source, skills, docs, handoffs, wiki concepts, configs, tests
- **On disk, not git:** generated cache (qmd stubs, qmd.db, catalog, pytest cache), runtime state (.artifacts/, session data, logs)
- **In tmp/:** session-local scripts, consumed-and-discarded files

Audit `.gitignore` against this principle.

### Task 3: Relocate generated artifacts (RC1)
Based on Task 1 results:
- If qmd.db holds the index: move stubs to `P:/.cache/wiki-stubs/` (gitignored)
- If qmd reads live: update `index_skills.py` output path + qmd config to `.cache/`
- Remove the `.data/wiki/sources/skills/` un-ignore from `.gitignore`

### Task 4: Scanner categorization (RC2)
Add `categorize_git_status()` to the scanner:
- Group uncommitted files by top-level directory
- Tag each: `generated` / `durable` / `unknown`
- Return categorized counts with per-category recommendation
- Gate output changes from "1053 files" to "979 generated (.data/wiki/sources/), 34 durable (docs/), 10 logs, 30 unknown"

### Task 5: Scanner regex → YAML parsing
Replace regex-based frontmatter extraction with `yaml.safe_load()`. Move prose-resident fields (work_status) to frontmatter. See "Non-regex alternatives" table above.

### Task 6: Observe-Before-Propose scope expansion (Level 4)
Extend the existing rule's trigger vocabulary from "structure, file layout, naming scheme" to also include: `.gitignore` edits, script output paths, gate logic, scanner functions, hook configuration. The rule: "before modifying any file that defines system behavior, verify what depends on the current state of that file."

### Task 7: Gate guidance fix (RC4)
Remove "note in Other sessions'" as a resolution path. Every needs_attention gate must produce: (a) an action, (b) a recommendation with a verb, or (c) an explicit operator decision. The Hard Constraint #4 is in place but the gate guidance contradicts it.

## Dependency order

```
Task 1 (qmd verification) → Task 3 (relocate stubs)
Task 2 (git principle) → Task 3 + Task 4
Task 3 (relocate) → Task 4 (scanner categorizes against new locations)
Task 4 (scanner categorize) → Task 7 (gate guidance uses categorized output)
Task 5 (regex→YAML) — independent, can run in parallel
Task 6 (observe scope) — independent behavioral rule, can run any time
```

## Related artifacts
- Scanner: `C:/Users/brsth/.grok/skills/close/__lib/close_accounting.py`
- SKILL.md: `C:/Users/brsth/.grok/skills/close/SKILL.md`
- .gitignore: `P:/.gitignore` (lines 599-611)
- index_skills.py: `P:/.data/wiki/scripts/index_skills.py`
- Prior handoffs: test-code-drift, api-guessing-without-verification, close-v6-deferred-design-findings
- Wiki: plausible-narratives-substitute-for-verification (the level-5 pattern)
