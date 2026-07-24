---
thread_id: notebooklm-consolidation-20260724
parent_handoff_path: none
current_session_id: 019f94ac-82be-7f63-b308-13060d337601
current_terminal_id: console_16e8f28f-7b6c-48ba-b689-9ffb
produced_at: 2026-07-24T22:20:22Z
status: open
handoff_type: investigation
accurate_as_of_head: 854968a52b8922603ff67822cd11cf1fb20b8c76
---

## Objective

Audit, consolidate, and reorganize existing Gemini Notebooks (NotebookLM) into logical, efficient groupings — eliminating duplicates, archiving stale notebooks, and creating a clean taxonomy.

## Status

OPEN — not started. This is a fresh task packet from the operator.

## Producing context

2026-07-24, session 019f94ac, terminal console_16e8f28f, Grok Build (glm-5-2). Authenticated as a.hominidae@gmail.com (profile "codex").

## Read-first list

1. `P:/.data/wiki/concepts/notebooklm-gemini-notebook-programmatic-access.md` — tool comparison, API surface, nlm CLI commands
2. `C:/Users/brsth/.agents/skills/nlm-skill/SKILL.md` — full nlm CLI reference (890 lines, 16 command categories)
3. Run `nlm notebook list --json` to get the current notebook inventory

## Verified facts

- [FACT] NotebookLM authenticated (a.hominidae@gmail.com, profile "codex", 51 cookies)
- [FACT] At least 3 notebooks exist (from `nlm notebook list`): one empty, one titled "_2026-01-15" with 73 sources, one more
- [FACT] `nlm` CLI supports: `notebook list/create/get/describe/query/rename/delete`, `source list/add/delete`, `tag add/remove/list/select`, `batch` operations, `cross query`
- [INFERENCE] The full notebook count is unknown — only saw the first 3 in truncated output

## Current state

Not started. Need to:
1. Get the full notebook inventory
2. Assess each notebook's purpose, source count, last-updated
3. Identify duplicates, stale notebooks, and consolidation opportunities
4. Design a taxonomy
5. Execute the reorganization

## Task packets

### NB-01: Inventory all notebooks
- **goal:** Get a complete list of all notebooks with metadata
- **command:** `nlm notebook list --json`
- **acceptance:** Full JSON output saved to `P:/tmp/notebook-inventory.json` with id, title, source_count, updated_at for every notebook
- **verification level:** STATIC_INSPECTION

### NB-02: Assess and categorize
- **goal:** For each notebook, determine: purpose, relevance, staleness, duplication
- **method:** Read titles + source lists; tag with proposed category
- **acceptance:** Each notebook has a row in a categorization table: id | title | sources | last_updated | proposed_action (keep/merge/archive/delete) | proposed_category
- **verification level:** STATIC_INSPECTION

### NB-03: Design consolidation taxonomy
- **goal:** Define logical groupings (e.g., "AI Agents", "Python Libraries", "Research Topics", "Archive")
- **acceptance:** Written taxonomy with category names, descriptions, and which notebooks go where
- **verification level:** STATIC_INSPECTION

### NB-04: Execute reorganization
- **goal:** Apply the consolidation plan using nlm CLI
- **commands:**
  - `nlm tag add <id> --tags "<category>"` for categorization
  - `nlm notebook rename <id> "<new-title>"` for consistent naming
  - `nlm source add <target-id> --url <source-from-old>` for merging
  - `nlm notebook delete <id> --confirm` for archiving empties/duplicates
- **acceptance:** Notebook list reflects the new taxonomy; no duplicates; stale notebooks archived or deleted
- **falsifier:** Any source is lost during merge (verify source counts before/after)
- **verification level:** LIVE_BEHAVIOR
- **auth-expiry mitigation:** Cookie auth may expire mid-operation; if so, re-run `nlm login` and continue

## Open decisions

**Q: What taxonomy to use?**
- Options: (a) by topic domain (AI, Python, DevOps), (b) by use case (research, reference, temp), (c) by date/recency, (d) hybrid
- Criterion: findability + avoids over-fragmentation
- Currently leading: (d) hybrid — domain categories + a "temp/staging" category + an "archive" category
- Would change if: notebook count is small (<10) → flat list is fine

**Q: Delete or archive stale notebooks?**
- Options: (a) delete (frees quota), (b) tag as "archive" and keep (preserves sources)
- Criterion: irreversibility vs knowledge preservation
- Currently leading: (b) tag as archive — NotebookLM has no quota limit on notebook count

## Hard constraints

- ⚠️ ALWAYS ASK USER BEFORE DELETE — deletions are irreversible
- Source counts must be verified before and after any merge operation
- Cookie auth may expire mid-operation — have re-login plan ready
- Do NOT delete notebooks with unique sources without confirming they're ingested elsewhere

## Cross-reference couplings

- `nlm login` credentials → shared between `nlm` CLI and `notebooklm-py` Python API
- Consolidation plan should consider which notebooks feed the /www temp-staging pattern (those should be kept active)
- Tag taxonomy should align with wiki concept categories for consistency

## Other outstanding streams

- **Skill infrastructure** — crawl4ai, version_check, config. Separate handoff.
- **Data-source integration** — NotebookLM + Context7 + Jina Reader wiring. Separate handoff.

## Explicit non-goals

- Do NOT migrate NotebookLM sources to the local wiki (that's the /crawl4ai staging pattern's job, separate concern)
- Do NOT reorganize Google Drive sources (only NotebookLM notebooks)
- Do NOT change the nlm CLI or notebooklm-py installation

## Resumption protocol

1. Run `nlm notebook list --json > P:/tmp/notebook-inventory.json`
2. Read the inventory and build the categorization table (NB-02)
3. Present the consolidation plan to the operator for approval before executing (NB-04)

## Suggested next invocation

```
Continue NotebookLM consolidation. Get the full notebook inventory with `nlm notebook list --json`, categorize each notebook, and propose a consolidation plan for operator approval.
```

## Last user message (verbatim)

> "/handoff write handoffs for all the open and paused workstreams and all the decisions we made. Write one to cleanup and consolidate our gemini notesbooks into logical efficient groupings."

## Epistemic labels

- [FACT] nlm authenticated and working (verified via `nlm notebook list`)
- [FACT] At least 3 notebooks exist (truncated output; full count unknown)
- [INFERENCE] A consolidation taxonomy of 4-6 categories will be sufficient (based on typical personal NotebookLM usage patterns)
- [UNKNOWN] Total notebook count, duplication level, and staleness distribution (need NB-01 first)
