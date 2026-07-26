# HANDOFF: qmd viability evaluation + stuck Python dependencies

**Status:** ready-to-implement
**Created:** 2026-07-25
**Session:** 019f9bfe-1b89-7602-9384-0212224ff30b
**Priority:** HIGH — architectural decision with accumulating maintenance cost
**Assignee:** fresh session (cold-start LLM)
**Parent handoff:** none
**Thread:** qmd-architecture-20260725

---

## Objective (one sentence)

Decide whether to keep qmd (pinned at 0.1.x with surgical patches against a dead upstream), replace it (vendor/fork/swap/in-house), or keep it with a defined exit trigger — and resolve two stuck-Python-dependency issues in the same subsystem that block upgrades.

## Why this session (not the current one)

This session surfaced the problem and did the investigation, but the decision itself needs a fresh context: clean-slate evaluation, alternatives prototyping, and threshold calibration. The current session has too much invested in the "keep qmd" framing to evaluate it impartially (anchoring risk — see §Evidence).

## Scope

### In scope
1. **qmd architectural decision** (keep / replace / keep-with-exit-trigger)
2. **Exit-criteria threshold calibration** (decision 3 from the prioritized list)
3. **crawl4ai upgrade blocker investigation** (Python 3.14 / lxml issue — decision 4)
4. **Prototype Option D** (raw sqlite-fts5 + sentence-transformers, ~200-300 LOC)

### Out of scope
- Implementing the chosen path (that's a follow-up `/go` session)
- The crawl4ai Phase 2 shim fix (being implemented in session 019f9bfe — see `wiki_search.py` shim)
- The `/tp --adhd` prototype (separate workstream — see handoff `tp-adhd-prototype-20260725`)

---

## The problem (decomposed into 3 independent tracks)

### Track B: qmd architectural viability (the main decision)

**Current state:**
- qmd pinned at 0.1.2 with operator rule: "do not auto-upgrade qmd" (source: `qmd-patch-durability-strategy.md`)
- qmd upstream dead: `chengzhag/qmd-py` returns 404 (verified 2026-07-20)
- Patch count grown from 1 (FTS5) → 4+ (FTS5 + llm_backend + timeout + embedding-model)
- qmd Python API works: `from qmd import connect; client.collection('wiki').hybrid_search(query, top_k=N)` returns `{chunk_ref, text, score, bm25_score, vector_score}`
- qmd CLI partially broken: `qmd update` doesn't exist in 0.1.2 (only `search`, `collection`, `document`); `qmd search` signature differs from what `crawl_to_qmd.py` assumes
- Database: 76 documents, 650 chunks, 1024-dim embeddings, 56MB at `~/.config/qmd/qmd.db`

**The exit criterion has arguably triggered:**
The patch-durability concept (`P:/.data/wiki/concepts/qmd-patch-durability-strategy.md` lines 85-95) named at R2: "Re-evaluate Option B/F [vendor/fork/swap] if N+1 patches needed or upstream unreachable for M months." Both conditions are plausibly met:
- Upstream dead ~3 months (since at least 2026-07-20, possibly longer)
- Patch count 4+ and growing

**The decision:** keep / replace / keep-with-exit-trigger. The clean-slate test (would you install qmd today?) suggests "no" — but that test has a blind spot: alternatives haven't been prototyped, so their costs are unmeasured.

### Track C: crawl4ai upgrade blocker (decision 4 — NOT a simple upgrade)

**CRITICAL:** crawl4ai is NOT stuck on 0.7.8 by accident. The wiki at `P:/.data/wiki/concepts/web-scraping-tool-alternatives-free-tier.md:113` documents: **"crawl4ai is being upgraded (stuck on 0.7.8 due to Python 3.14 lxml issue)"**. The host runs Python 3.14 (`C:\Python314\python.exe`).

**The CVEs are real but the upgrade is blocked:**
- 0.8.7: Docker API critical CVEs
- 0.8.6: supply-chain switch (litellm → unclecode-litellm)
- Upgrade requires resolving the lxml/Python 3.14 compatibility issue first

**Investigation needed:** is the lxml issue still present? Has lxml released a Python 3.14-compatible version? Is there a workaround (lxml build from source, alternative parser)? Check PyPI for lxml Python 3.14 wheels as of the session date.

### Exit-criteria threshold calibration (decision 3)

The current "N+1 patches / M months" is hand-wavy and lets the decision drift. Name real numbers. Candidates to evaluate:
- **Patch count trigger:** 5 patches? 6? (currently at 4+)
- **Upstream-dead duration trigger:** 6 months? 12 months? (currently ~3 months)
- **Both must be met, or either?** (AND vs OR)

The threshold should be mechanical (fires without judgment) because closure pressure defers judgment calls. Reference: `~/.grok/AGENTS.md` "Claims require receipts" — the threshold is the receipt that the decision is overdue.

---

## Evidence (gathered this session — verify before relying)

### qmd state
| Claim | Tier | Receipt |
|---|---|---|
| qmd 0.1.2 installed, importable, Python API works | Tier 1 | `python -c "from qmd import connect; ..."` this session |
| `qmd update` doesn't exist (only `search`, `collection`, `document`) | Tier 1 | `qmd --help` this session |
| `qmd search` requires `--query`/`--top-k`, no `--format`, returns `{chunk_ref, text}` | Tier 1 | `qmd search --help` + live search this session |
| qmd upstream dead (404) | Tier 2 | `qmd-patch-durability-strategy.md` citing 2026-07-20 verification |
| 4+ patches against site-packages | Tier 2 | `qmd-semantic-search-requires-llm-backend.md` + `qmd-patch-durability-strategy.md` |
| Database 76 docs / 650 chunks / 1024-dim / 56MB | Tier 1 | `qmd collection list` + `collection().info()` this session |

### crawl4ai state
| Claim | Tier | Receipt |
|---|---|---|
| crawl4ai 0.7.8 installed, 0.9.2 latest | Tier 1 | `version_check.py --skill crawl4ai` this session |
| Stuck on 0.7.8 due to Python 3.14 lxml issue | Tier 2 | `web-scraping-tool-alternatives-free-tier.md:113` |
| Today's crawl worked on 0.7.8 | Tier 1 | `/crawl4ai` run this session (UditAkhourii/adhd) |

### Key architectural insight from /tp critique
**Subprocess-as-degradation-boundary:** shelling out to qmd via subprocess is wrong-on-syntax but right-on-architecture — it fails at runtime (degradable) rather than import time (tight coupling). Direct import (`from qmd import connect`) tightens the coupling surface at exactly the moment when qmd's viability is in question. This insight is why the crawl4ai fix uses a shim module (`wiki_search.py`) rather than direct import — preserves the replacement boundary regardless of Track B's decision.

---

## Options to evaluate (with selection criterion)

**Selection criterion:** optimal long-term (lowest future maintenance cost + risk, best meets requirements). Transition effort is NOT a criterion.

### Option B: Vendor qmd 0.1.2 source
Copy the qmd source into the workspace (e.g., `P:/.agents/lib/qmd-vendored/`), apply patches directly to the vendored source. Eliminates the "patches lost on pip reinstall" class.
- **Pros:** no upstream dependency, patches become first-party code, full control
- **Cons:** absorbs maintenance surface, no upstream bug fixes (but upstream is dead anyway)

### Option D: Replace with raw sqlite-fts5 + sentence-transformers (~200-300 LOC)
qmd is a thin wrapper around sqlite-vec + FTS5 + sentence-transformers, all of which are already installed. A custom module provides `search(query, collection, top_k)` against the same database, bypassing qmd entirely.
- **Pros:** no upstream dependency, full control, can add features (tag filtering, cross-collection) as needed
- **Cons:** one-time migration effort, must maintain the wrapper (but "own 200 LOC" vs "patch dead upstream" — the maintenance profile is better)
- **MUST PROTOTYPE before deciding** — the clean-slate test has a blind spot here

### Option F: In-house rewrite
Build a purpose-built wiki search system from scratch.
- **Pros:** exactly fits requirements, no legacy constraints
- **Cons:** highest transition cost, reinvents what qmd already does

### Option I (status quo): Keep qmd pinned with patches + SessionStart hook
The documented current decision. Extend the `.patch` convention as needed.
- **Pros:** zero transition cost, documented convention, working today
- **Cons:** patches accumulate against a tombstone, every new qmd bug requires reverse-engineering against 0.1.2 source

### Option K (keep-with-exit-trigger): Status quo + mechanical threshold
Keep Option I but with a defined trigger: "at N patches or M months dead, automatically escalate to Option B/D evaluation." Forces the decision out of judgment-call territory.
- **Pros:** defers the transition cost until the threshold fires, makes the trigger mechanical
- **Cons:** still accumulates patches until the threshold

---

## Acceptance criteria (the decision is complete when)

1. **For Track B (qmd architecture):** a decision is made AND documented in a wiki concept with: selected option, rationale, steelman of rejected options, falsifier, and (if "keep") concrete exit-criteria thresholds. Update `qmd-patch-durability-strategy.md` — either supersede it (if replacing) or add the §14 "Exit criteria" section that R2 deferred.

2. **For Track C (crawl4ai upgrade):** the lxml/Python 3.14 blocker is investigated (current status, available workarounds, ETA if upstream). If blocked indefinitely, document; if unblocked, upgrade and verify.

3. **For exit-criteria thresholds (decision 3):** real numbers are named in the decision concept, with rationale for why those numbers (not hand-wavy "N+1 / M months").

---

## Constraints

- **Operator preferences:** optimal long-term over minimal-diff; transition effort is not a disqualifier; radical refactoring on the table when ROI justifies (source: `~/.grok/AGENTS.md` § "Optimal long-term solution," reinforced in `/design` commit `b39d97b`)
- **qmd is currently working** — hybrid_search returns good results. The decision is about long-term viability, not fixing a live break.
- **Database must be preserved or migrated** — 76 docs / 650 chunks of indexed content is the real asset
- **Fresh-lens required** — the current session is anchored on "keep qmd." Use `/design` or `/tp` to get a fresh framing, or explicitly run the clean-slate test.

---

## Files to read first

- `P:/.data/wiki/concepts/qmd-patch-durability-strategy.md` — the existing decision (keep with patches)
- `P:/.data/wiki/concepts/qmd-semantic-search-requires-llm-backend.md` — why patches are needed
- `P:/.data/wiki/concepts/web-scraping-tool-alternatives-free-tier.md` — crawl4ai lxml blocker (line 113)
- `P:/packages/.claude-marketplace/plugins/cc-skills-utils/__lib/` — the existing `.patch` files
- `P:/.data/wiki/log.md` lines 730-735 — the superseded log entry (corrected this session)
- `~/.grok/skills/crawl4ai/crawl_to_qmd.py` — the consumer with the qmd API mismatch
- `P:/.data/wiki/concepts/subprocess-as-degradation-boundary.md` — (if written by session 019f9bfe) the coupling insight

## Related work

- **crawl4ai Phase 2 shim fix** — being implemented in session 019f9bfe (`wiki_search.py` shim module). Decision B does not block this; the shim preserves the replacement boundary regardless.
- **`/tp --adhd` prototype** — separate workstream, deferred (see handoff `tp-adhd-prototype-20260725`).

## Open questions for the fresh session

1. Is the lxml/Python 3.14 issue still blocking crawl4ai 0.9.2? (Check PyPI for wheels as of session date.)
2. Has anyone forked qmd since 2026-07-20? (Re-check GitHub for forks.)
3. What's the actual maintenance cost of Option D once prototyped? (The clean-slate test's blind spot — must measure, not assume.)
4. Are there features qmd provides that Option D wouldn't easily replicate? (Tag filtering, cross-collection, reranking — audit qmd's API surface.)
