---
thread_id: 9b7c2f4a-3e1d-4c8b-9a52-7f6e3d5b1c8a
parent_handoff_path: none
current_session_id: 019f9a3c-a088-7230-97c3-7959e8bae1cd
current_terminal_id: console_1faf8be6-6283-4495-939e-9252
produced_at: 2026-07-26T01:05:00Z
status: open
handoff_type: investigation
accurate_as_of_head: beb1a583785315b0283b64b082a9eca3eda3d532
---

# NotebookLM bulk-ingest + wiki round-trip pipeline (2026-07-25)

## Objective

Build and exercise a reusable pipeline that takes a large list of URLs
(YouTube videos, PDFs, web pages), clusters them into themed NotebookLM
notebooks under the per-notebook source cap, and (in the inverse direction)
syncs NotebookLM notebook content back into the wiki with full provenance.
Originally triggered by a 4244-entry YouTube watch-later JSON; expanded into
two skills, three wiki concepts, one SCHEMA principle, and one wiki indexer
enhancement.

## Goal

**One sentence:** take 4244 watch-later videos → themed NotebookLM notebooks
→ reusable skills + wiki concepts so the next session (or any agent) can
repeat either direction without re-deriving the pipeline.

**Success criteria (all met):**
- 4244 videos deduped to 4143, 4116 addable, all 4116 ingested as sources
- 15 notebooks, each ≤300 sources, each verified via `source_count`
- Two reusable skills committed at `P:/.agents/skills/` with test suites
- Three wiki concept pages capture the hard-won findings
- One SCHEMA principle captures the doc-design lesson
- Indexer annotates skill state so future sessions can tell active vs disabled

## Decisions

### D1. Clustering: two-pass HDBSCAN + KNN-assign + greedy merge + recursive split
**Rationale:** single-pass HDBSCAN left 40% of videos as noise. The four-stage
pipeline (embed → strict HDBSCAN → soft HDBSCAN on noise → KNN-assign residual
→ greedy merge to size cap → split oversize) produced 15 clusters of 154–300
each (mean 274) with zero residual. Documented in
`wiki/concepts/semantic-clustering-bounded-size.md`.

### D2. Bulk-add via repeatable `--youtube` flag (one CLI call per notebook)
**Rationale:** `nlm source add <nb> --youtube u1 --youtube u2 ...` ingests
all URLs in one call. Cost was 15 bulk calls (~30 min), not 4116 single
calls (~2.3 hours). I initially asserted "no bulk endpoint exists" — that
was wrong; the operator corrected it. Receipt: `nlm source add --help` says
"(repeatable for bulk)". Documented in
`wiki/concepts/notebooklm-cli-operational-gotchas.md`.

### D3. Pilot before full run (one cluster end-to-end, then commit to the batch)
**Rationale:** creating 15 notebooks with bulk-adds is an irreversible
commitment. Pilot on cluster 3 (claude-skills-code, 191 videos) validated
the bulk-add API path before the full run. The pilot revealed the cosmetic
first-URL error (D5).

### D4. NotebookLM paid account = 300 sources per notebook (not 50)
**Rationale:** I asserted "NotebookLM caps at 50 sources" from stale
training data. Operator corrected: paid account = 300. Verified empirically
when cluster 10 hit exactly 300 sources. Documented as its own page at
`wiki/concepts/notebooklm-source-limits-free-vs-paid.md` per the keyword
test (D7).

### D5. The first-URL "Error: Failed to add URL source" + exit code 1 is cosmetic
**Rationale:** every bulk-add call printed this on the first URL and exited
1, but the bulk continued and landed all sources. Verified across 14
independent bulk-add calls (all source_counts matched). The right
verification is `nlm notebook get <id>` `source_count`, not exit code.
Documented in `wiki/concepts/notebooklm-cli-operational-gotchas.md`.

### D6. `nlm login --check` lies; `nlm login --profile <name>` recovers silently
**Rationale:** `--check` returns `network_error: ClientAuthenticationError`
even when auth is fine. Recovery is `nlm login --profile <name>` (silent
CDP-based re-auth, ~10s, no user interaction). Recipe recorded in
`~/.grok/tool-fallbacks.md` under "CLI auth + bulk recipes".

### D7. Decision-time facts must be findable at the keyword a search would use (SCHEMA §13 #11)
**Rationale:** the NotebookLM 300-source correction was initially going to
be buried inside a longer operational-gotchas page. Operator caught it:
"How are you supposed to know for next time?" A future session grepping
"notebooklm source limit" would not read a 4-page gotchas doc. Solution:
thin standalone page for the single fact + new SCHEMA principle #11 codifying
the rule. The rule's keyword test: "what 2–4 word query would a future
session actually type?"

### D8. Skill name `/nlm-bulk-ingest`, scope `.agents/skills/`
**Rationale:** action-oriented name (matches `red-team`, `plan-writer`
convention); cross-agent scope (`P:/.agents/skills/`) so Codex/Claude/Grok
all see it; one combined skill rather than split (`/semantic-partition` +
`/nlm-bulk-ingest`) — premature split = two skills to maintain.

### D9. `/nlm-to-wiki` v2: Report + Data-Table extraction, 4-hop provenance, branch-as-refines
**Rationale:** the existing v1 plugin used chat query (ephemeral, uncited)
and a frontmatter shape that wouldn't pass `validate_wiki_entry.py`. v2 uses
Report + Data-Table Studio artifacts (persistent, citable), emits SCHEMA-
compliant frontmatter, branches as `refines` on collision with existing
concepts (preserves both framings). Full 4-hop provenance chain
(concept → notebook → cluster → source URL) — hop 4 is documented as
deferred (manual match today).

### D10. Annotate skill catalog with Grok/Claude enable state (don't filter)
**Rationale:** operator asked "why can't we include if the skill or plugin
is disabled?" — correct framing. Catalog gets two columns (G/C) showing
✓/✗/— per skill per host; stubs get `grok_enabled`/`claude_enabled`
frontmatter. Reads `~/.grok/config.toml` `[plugins].disabled` (opt-out) and
`~/.claude/settings.json` `enabledPlugins` (opt-in).

## Status

**OPEN — primary work complete, follow-ups tracked below.**

The eight shipped items (Evidence §A) are done. The two partial items
(Evidence §B) and four deferred items (Evidence §C) are tracked.

## Evidence

### A. Fully done (verified)

| # | Item | Verification receipt |
|---|---|---|
| A1 | Dedup 4244→4143 watch-later videos | `C:/Users/brsth/Downloads/watch-later-1784999007767-deduped.json`; 101 removals (97 dead placeholders + 4 dupes) |
| A2 | Cluster 4116 addable → 15 themed clusters | `C:/Users/brsth/Downloads/watch-later-1784999007767-deduped-clusters.json`; sizes 154–300, mean 274 |
| A3 | 15 NotebookLM notebooks created + bulk-added | `P:/tmp/wl_notebooks_run.json`; all 15 with `status: ok`, source_counts: 295/294/299/191/299/154/227/296/297/296/300/299/299/291/279 = 4116 total |
| A4 | 3 wiki concepts written, validated, indexed, logged | `P:/.data/wiki/concepts/{notebooklm-cli-operational-gotchas,semantic-clustering-bounded-size,notebooklm-source-limits-free-vs-paid}.md`; all pass `validate_wiki_entry.py`; all in qmd; all logged in `P:/.data/wiki/log.md` |
| A5 | SCHEMA.md §13 principle #11 added | `P:/.data/wiki/SCHEMA.md:496`; principles #1–#10 intact (no regression) |
| A6 | `~/.grok/tool-fallbacks.md` nlm recipes added | `~/.grok/tool-fallbacks.md:50-69`; "CLI auth + bulk recipes" section |
| A7 | `/nlm-bulk-ingest` skill shipped | `P:/.agents/skills/nlm-bulk-ingest/` (SKILL.md + 3 scripts + 2 references); 14-test suite passing; smoke-tested end-to-end on 50 real YT entries |
| A8 | `/nlm-to-wiki` v2 skill shipped | `P:/.agents/skills/nlm-to-wiki/` (SKILL.md + 6 scripts + 4 references); 14-test suite passing |
| A9 | `index_skills.py` enable-state annotation | `P:/.data/wiki/scripts/index_skills.py` + `test_index_skills_state.py` (19 tests passing); catalog now shows G/C columns |

### B. Partially done

| # | Item | Gap | Next step |
|---|---|---|---|
| B1 | `/nlm-to-wiki` v2 — scripts compile + 14 tests pass | Never run end-to-end against a real notebook. `nlm report create` → parse → write_pages flow not validated against live nlm output | Run `sync.py --notebook <id> --dry-run` against pilot notebook `23bf4931-...` to surface Report-format drift |
| B2 | Pilot notebook (cluster_id 3) verification | Created + bulk-added successfully (source_count: 191 was confirmed live via `nlm notebook get` during the session), but `P:/tmp/wl_notebooks_run.json` shows `actual: null, status: pilot` — the state file was seeded before the verify step and never updated | One command: `nlm notebook get 23bf4931-d0cb-4550-9d11-f9b38843254a --json` confirms source_count, then patch the state file |

### C. Not started (deferred)

| # | Item | Why deferred | Trigger to start |
|---|---|---|---|
| C1 | Studio artifacts (podcasts/reports/flashcards) for the 15 notebooks | Operator-resource-bounded (paid NotebookLM quota, 5–15 min per artifact × 15 notebooks) | When operator wants a per-cluster digest, podcast, or study guide |
| C2 | `nlm-to-wiki` hop-4 UUID→URL matching | Requires NotebookLM API exploration; manual match via `nlm source list` works today | When a wiki writeback needs full automation without human UUID matching |
| C3 | `nlm-bulk-ingest` validation on non-YT input (CSV/PDF/RSS) | Wait for natural demand — first non-YT input will surface parser bugs | When operator has a non-YT list to ingest |
| C4 | Vault audit for buried decision-time facts (per SCHEMA §13 #11) | ~30 min scan; low urgency now that the principle is in place | Next time `/wiki` work surfaces a candidate |
| C5 | Claude-side propagation of nlm auth recipe | Claude-side has no `tool-fallbacks.md` equivalent; recipes are Grok-only today | When Claude-side sessions start hitting the same `nlm login --check` trap (or proactively, ~5 min) |

## Key files

### Skills (committed to git at P:/)
- `P:/.agents/skills/nlm-bulk-ingest/` — ingest direction (URL list → notebooks)
  - `SKILL.md`, `scripts/{normalize,cluster,ingest}.py`, `references/{input-formats,decisions}.md`
- `P:/.agents/skills/nlm-to-wiki/` — sync direction (notebooks → wiki)
  - `SKILL.md`, `scripts/{sync,extract,parse_report,reconcile,write_pages,expand_citations}.py`
  - `references/{extraction-prompts,frontmatter-mapping,provenance-model,dedup-policy}.md`
  - `tests/test_parse_and_slug.py` (14 tests)

### Wiki concepts (committed to git at P:/)
- `P:/.data/wiki/concepts/notebooklm-cli-operational-gotchas.md`
- `P:/.data/wiki/concepts/semantic-clustering-bounded-size.md`
- `P:/.data/wiki/concepts/notebooklm-source-limits-free-vs-paid.md`
- `P:/.data/wiki/SCHEMA.md` (§13 principle #11 added)

### Run artifacts (uncommitted, in P:/tmp/)
- `P:/tmp/wl_notebooks_run.json` — notebook IDs + verified source_counts for the 15 notebooks
- `P:/tmp/wl_notebooks_run.log` — run log
- `P:/tmp/wl_notebooks_driver.py` — the driver script (reusable template)
- `P:/tmp/cluster_watchlater.py` — original clustering script (superseded by the skill's `cluster.py`)
- `P:/tmp/dedup_watchlater.py` — original dedup script (superseded by `normalize.py`)

### NotebookLM notebooks (15)
All at `https://notebooklm.google.com/notebook/<id>`:

| Cluster | Title | Sources | Notebook ID |
|---|---|---|---|
| 0 | WL: Local AI Models & GPU | 295 | `33b058e9-5de1-49da-8d8a-b1ef3d50467e` |
| 1 | WL: Multi-Agent Orchestration | 294 | `917784eb-ef7d-40e5-b823-7bd74c2bc9bd` |
| 2 | WL: AI Coding & Tooling | 299 | `56999a7a-e52f-4e04-9335-342df85cdfde` |
| 3 | WL-Pilot: Claude Skills & Code | 191 | `23bf4931-d0cb-4550-9d11-f9b38843254a` |
| 4 | WL: Claude Code Repos & Tools | 299 | `8b807d28-b283-4de3-a369-4ff5e065ac92` |
| 5 | WL: Health (ADHD/Sleep/Cancer) | 154 | `b8a105cf-ada2-4343-88ce-184b1e7c9387` |
| 6 | WL: Model Reviews & Benchmarks | 227 | `7d22f36a-4283-4b43-8d3f-1d9334aa4751` |
| 7 | WL: GitHub Trending & AI News | 296 | `06717c64-8597-4a59-a5e3-871e841585af` |
| 8 | WL: NotebookLM & Google AI | 297 | `cd7609ec-3c21-48d2-a2ca-2d2ee3f989f0` |
| 9 | WL: Anthropic & Agent Ecosystem | 296 | `7ef4d1e8-319f-4e27-a751-e777ddc2b723` |
| 10 | WL: Canadian Politics & Trade | 300 | `683781d4-4e8f-4ae0-a1d0-57a5f2c4c566` |
| 11 | WL: Health & Weight Loss | 299 | `fff42c44-d4ba-474a-93f7-7384bd536a1b` |
| 12 | WL: Misc (HFY + assorted) | 299 | `b69bbe99-32d8-43ed-8489-50ab2ab822c9` |
| 13 | WL: Options & Trading | 291 | `1ca5db24-0bf4-4e35-9cd6-94e79f13aaa6` |
| 14 | WL: Geopolitics (Israel/Islam/Trump) | 279 | `c347df80-c8a5-409c-956b-e4ae2691003d` |

### Source data (operator-owned, not committed)
- `C:/Users/brsth/Downloads/watch-later-1784999007767.json` — original 4244-video export
- `C:/Users/brsth/Downloads/watch-later-1784999007767-deduped.json` — 4143 after dedup
- `C:/Users/brsth/Downloads/watch-later-1784999007767-deduped-clusters.json` — 4116 clustered
- `C:/Users/brsth/Downloads/watch-later-1784999007767-deduped-clusters.md` — human-readable cluster preview

## Verification commands

```bash
# Confirm all 15 notebooks still have expected source_counts
python -c "
import json, subprocess
state = json.load(open(r'P:/tmp/wl_notebooks_run.json', encoding='utf-8'))
for cid, rec in state['notebooks'].items():
    nb = rec['notebook_id']
    r = subprocess.run(['nlm','notebook','get',nb,'--profile','codex','--json'],
                       capture_output=True, text=True, timeout=60)
    actual = json.loads(r.stdout).get('source_count')
    expected = rec['expected']
    status = 'OK' if actual == expected else 'MISMATCH'
    print(f'{cid:>3} {rec[\"title\"][:40]:<40} {actual}/{expected} {status}')
"

# Confirm wiki pages validate
python ~/.grok/skills/wiki/scripts/validate_wiki_entry.py P:/.data/wiki/concepts/notebooklm-cli-operational-gotchas.md
python ~/.grok/skills/wiki/scripts/validate_wiki_entry.py P:/.data/wiki/concepts/semantic-clustering-bounded-size.md
python ~/.grok/skills/wiki/scripts/validate_wiki_entry.py P:/.data/wiki/concepts/notebooklm-source-limits-free-vs-paid.md

# Confirm skill tests pass
python -m pytest P:/.agents/skills/nlm-bulk-ingest/ -v
python -m pytest P:/.agents/skills/nlm-to-wiki/tests/ -v
python -m pytest P:/.data/wiki/scripts/test_index_skills_state.py -v
```

## Cross-reference couplings

- `~/.grok/tool-fallbacks.md` § "CLI auth + bulk recipes" — nlm auth recovery + bulk-add correction (Grok-only; C5 covers Claude side)
- `P:/.data/wiki/SCHEMA.md` §13.11 — decision-time-facts principle (motivated by D7)
- `P:/.data/wiki/scripts/index_skills.py` — enhanced to read the tool-fallbacks + settings.json state
- Three wiki concepts cross-reference each other and the two skills

## Read-first (related wiki concepts)

Top qmd results for "notebooklm clustering skill provenance":

1. `wiki/concepts/notebooklm-cli-operational-gotchas.md` — the 3 operational traps (auth probe, bulk add, cosmetic error)
2. `wiki/concepts/semantic-clustering-bounded-size.md` — the 4-stage clustering pipeline
3. `wiki/concepts/notebooklm-source-limits-free-vs-paid.md` — the 50 vs 300 cap

Also relevant (pre-existing): `wiki/concepts/dgemma-gemini-flash-operational-tests-2026-07-22.md` (references a dangling `yt-is-notebooklm-pipeline-improvements` wikilink that this session's work effectively replaces).

## Other outstanding streams (not in scope; flagged for awareness)

- `P:/docs/handoffs/notebooklm-consolidation-20260724/` — status: open, pre-existing. Consolidation task predates this session's 15 new notebooks. May need re-scoping to account for `WL: *` notebooks.
- `P:/docs/handoffs/multi-terminal-auto-commit-20260725/` — status: open. Tool-fallbacks.md edits made this session live in `~/.grok/` which may or may not be auto-committed by that other stream's policy.

## Last user message (verbatim)

```
/handoff
```

(The slash-command invocation. The semantic intent — "write a handoff for the
session's work stream" — is per the `/handoff` SKILL.md process.)

## Open questions for next session

1. Should the `notebooklm-consolidation-20260724` handoff be re-scoped to
   include the 15 new `WL: *` notebooks, or do they belong to a separate
   workflow that the consolidation shouldn't touch?
2. Is there value in generating Studio artifacts (podcasts/reports) for any
   of the 15 notebooks now, or wait for natural demand?
3. The `nlm-to-wiki` hop-4 UUID→URL matching (C2) — is the manual-match
   workaround acceptable indefinitely, or should we build the automation?

## Falsifier

This handoff is wrong if:
- Any of the 15 notebook source_counts drift from what's recorded (re-run
  the verification block above)
- The skill tests don't pass (re-run the pytest commands above)
- A future session can't act on B1/B2/C1–C5 without re-deriving the work
  (the handoff failed its core purpose)
- The "verbatim last user message" misrepresents intent (the actual text
  was `/handoff` — preserved above)
