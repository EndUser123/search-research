# Web search tool investigation & PKM research handoff

| Field | Value |
|---|---|
| **Date** | 2026-07-19 |
| **Source session** | Grok Build — wiki + export-EPERM investigation |
| **Status** | Investigation complete; implementation deferred to a future wiki-focused session |
| **What's in here** | (1) Three available search tools and their selection rules; (2) Karpathy's LLM Wiki pattern, confirmed and disconfirmed; (3) PKM/wiki maintenance research; (4) Cognitive-load rubric literature; (5) QMD auto-link failure diagnosis; (6) deferred action items for the wiki work session. |
| **What's NOT in here** | The two wiki pages we already created (cross-linked below); the directory_policy.json investigation; the runtime hook enforcer analysis. Those live in conversation transcript and the wiki. |

---

## TL;DR

Three search tools were available this session; I used only one (`web_search`). Per its tool description, `minimax-search__web_search` is the primary tool for real-time / external info and was the right default. `web-search-prime__web_search_prime` offers unique features (`search_recency_filter`, `search_domain_filter`, configurable `content_size`) that would have answered time-bounded questions (the v2.1.163 version-fix question specifically) more cleanly. Recorded for future sessions.

Karpathy's LLM Wiki pattern is well-documented as of April 2026 (gist, ~5,000+ stars/forks, multiple independent reviewers). Three-layer architecture (raw sources / wiki / schema) with periodic lint every 2–3 weeks, 30–45 min/session — required, not optional. Real failure modes surface at 150+ pages (we're at ~1,000). Our auto-link returning empty is an early symptom of the same pathology.

**Action items for the next wiki session are at the bottom.** All seven implementation steps are queued and ready.

---

## 1. Tool inventory — three search paths were available

| Tool | Server | When to use | Distinct capabilities |
|---|---|---|---|
| `web_search` | Built-in (xAI) | Generic search, full results | None distinct vs other tools |
| `minimax-search__web_search` | MCP | **Primary default** per its tool description: *"You MUST use this tool whenever you need to search for real-time or external information on the web."* | Structured results with date stamp, related-searches section |
| `web-search-prime__web_search_prime` | MCP | Time-bounded queries, domain-scoped queries, longer summaries | `search_recency_filter` (`oneDay`/`oneWeek`/`oneMonth`/`oneYear`), `search_domain_filter` (whitelist scope), `content_size: high` (2500-word summaries) |

**Tool-selection drift observed this session:** I used `web_search` for all four searches. Two were 429-rate-limited. I told the user "will retry once" and didn't — both follow-throughs. The other two tools were never tried. The user explicitly asked "are you handicapping yourself?" — yes.

### Selection rule (draft, ready to encode)

```
- Default search -> minimax-search__web_search
- Time-bounded question ("is X fixed in version Y?", "what's current state of Z?") ->
  web-search-prime__web_search_prime with search_recency_filter=oneMonth
- Domain-scoped question ("only github.com", "only one specific blog") ->
  web-search-prime__web_search_prime with search_domain_filter
- Need a 2500-word summary for analytical synthesis ->
  web-search-prime__web_search_prime with content_size=high
- web_search (built-in) -> only as fallback if MCPs unavailable
```

**Encoding options:** (a) lightweight note in `~/.grok/skills/wiki/SKILL.md`; (b) free-standing tool-preference note; (c) the broken/working-tool doc per AGENTS.md. Recommend (a) — narrowest scope, fits the wiki-as-host pattern.

## 2. Rate-limit observation (verified)

`web_search` API limit: **2 RPS**. Parallel batches of ≥4 calls trip 429. Confirming reproduction with the two MCPs not done this session — likely the same limit applies fleet-wide (cheap to test on next multi-search event).

**Failure mode observed:** I sent 4 parallel searches, 2 hit 429, I told user "will retry once" and didn't. Recovery is one inline retry call. Don't promise-then-defer; the cost of retry is negligible.

## 3. Karpathy's LLM Wiki pattern — confirmed

### Architecture (verified via Karpathy's gist + multiple Apr–Jun 2026 reviews)

```
Raw sources (immutable)        ← LLM reads; never writes
Wiki (LLM-edited Markdown)     ← entities, concepts, summaries, syntheses
Schema/constitution (file)     ← page types, conventions, lint cadence, style
```

Each layer has a distinct role. Operations on the wiki are **Ingest / Query / Lint** (slash commands; sometimes `/ingest`, `/lint-wiki`). Periodic lint is **explicitly not optional** per Karpathy's gist.

### What people actually implemented (confirmed)

- Obsidian vault + Dataview + git + Web Clipper for sources
- `index.md` as top-down catalog (most important when scaling)
- `log.md` as append-only audit trail (we have this — the wiki vault)
- Schema file: `SCHEMA.md` or vault-level `CLAUDE.md` / `AGENTS.md`
- QMD-style local semantic search
- LLM does bookkeeping; human curates sources, reviews diffs

### Disconfirmation: 1–3 month reviews surface real failure modes

| Failure | What happens |
|---|---|
| **"Zero maintenance is marketing"** | Real cost: 30–45 min every 2–3 weeks for contradiction checks, stale detection, link maintenance, schema enforcement |
| **Drift and staleness** | Agents under-update cross-references; new sources silently supersede old claims. **Without linting, the wiki becomes "an unreliable source that confidently serves outdated info."** This is **exactly the failure mode my OneDrive page's `## Scope` block was created to defend against** (claiming breadth I had not reproduced) |
| **Scale breaks ~150 pages** | Sweet spot 100–150; 150–300+ strains context windows: missed links, duplicates, over-linking, style drift. **We are at ~10x that (783 concept pages + 1007 total docs)** — the scale problem applies directly |
| **Compounding errors** | Bad syntheses get baked in and cited. Adversarial review + grounding in source summaries are the documented mitigations |
| **Habit discipline required** | Inconsistent ingestion = stagnation. Schema co-evolution = work |
| **Weaker ROI for casual use** | Narrow deep-research works; broad-web-already-served-by-search doesn't justify the overhead |
| **Team editions need ownership/PR gates/schema governance** | Karpathy's pattern assumes single-human-driven; multi-host multi-agent is **harder than his pattern** by design |

### Primary sources (cross-checked)

- `https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f` — Karpathy's gist (created April 2026; **note: gist shows "updated 2 days ago" per `minimax-search` on 2026-07-19 — still maintained**)
- `https://x.com/karpathy/status/2039805659525644595` — original X post
- `https://www.rdworldonline.com/is-karpathys-viral-llm-wiki-helpful-mostly-yes-one-month-in/` — measured-positive 1-month review
- `https://www.kunalganglani.com/blog/llm-wiki-karpathy-local-knowledge-base` — detailed 1-month review with failure modes
- `https://www.recall.it/post/andrej-karpathy-llm-wiki-no-code-no-maintenance` — critique ("maintenance tax reduces but doesn't disappear")

## 4. PKM/wiki maintenance research — what people do and don't do

### What the PKM/Docs-as-Code ecosystem does well

| Practice | Source | What it solves |
|---|---|---|
| **Status flags** (`evergreen` / `stale` / `wip` / `archived`) on every page | Cody Burleson's "garden maintenance" pattern, Obsidian Dataview queries | Erodes "capture-once-and-forget" decay; gives a date-driven ritual surface |
| **Link density rule** — every new note links to ≥3 existing notes | Zettelkasten derivative, Obsidian/Logseq communities | Prevents orphans (the most-cited orphan-creation source is isolated capture) |
| **MOCs** (Maps of Content) — top-down hub pages that cluster related notes | Tiago Forte, Obsidian practice | Makes discovery explicit instead of emergent-only-via-graph |
| **Diátaxis framework** — Tutorial / How-to / Reference / Explanation as page-intent types | Daniele Procida; mainstream in Sphinx/MkDocs | Mixing intents on one page is the top cause of cognitive overload per CLT |
| **Linting in CI** — Vale, readability scores, jargon detection | Docs-as-code community | Catches ECL (extraneous cognitive load) before publication |
| **Periodic gardening sessions** — weekly/monthly review by mtime | Burleson, Andy Matuschak | Maintenance tax has to be paid; flags create a ritual-friendly surface |

### What the ecosystem doesn't do (the gaps relevant to our wiki)

| Gap | Why it matters here |
|---|---|
| **No `verification:` frontmatter discipline** | Status flags cover staleness (out of date) but not **scope confidence** (was the claim ever tested at all?). Our ad-hoc `## Scope` block on the OneDrive page is unusual; codifying as frontmatter closes a real drift gap |
| **Semantic-threshold auto-link is rare** | Most PKM use exact-match `[[wikilinks]]` because relevance-score auto-link fails on loosely-indexed corpora (our QMD situation). Either raise precision (current: nothing fires) or recall (too much noise) — there is no free lunch |
| **No community-standard `cognitive_load` field** | DCLRS exists but isn't widely adopted; multi-dimensional rubrics (ICL/ECL/GCL) are research-grade. Single-number rubrics like ours are unusual. Most PKM systems skip the field entirely |
| **No disconfirmation-as-habit** | Wiki culture values confirmation (link, capture, capture-and-link). I couldn't find community-standard "search for counter-evidence before publishing a fix" ritual. Closest is red-team threads in engineering blogs but nothing systematic |
| **Top-down MOCs require human curation** | High-value but high-cost. AI-assisted MOC generation is emerging but not yet a community norm |

### Why some approaches work and others fail

- **Status flags work** because they're cheap metadata that creates a "what should I look at this week?" surface.
- **Link-density rules work** because they force serendipity during capture moments. Three is the empirical sweet spot; two is too few (likely redundant), five is too many (cognitive overload at write time).
- **MOCs work** because they encode curator intent above the page level. **They fail when stale** (a stale MOC is worse than no MOC).
- **Auto-link with semantic threshold doesn't work generally** because relevance scoring breaks down in loosely-indexed or low-redundancy corpora. Most communities sidestep by using exact-match wikilinks plus MOCs.

### Sources

- `https://medium.com/@cody.burleson/patterns-for-pkm-garden-maintenance-50c5dfe12b20`
- `https://medium.com/@helloantonova/the-pkm-paradox-why-most-knowledge-management-tools-fail-to-meet-our-needs-d5042f08f99e`
- `https://miscellaneplans.medium.com/escape-the-pkm-trap-of-sophisticated-procrastination-8eed3acd4b04`
- `https://www.reddit.com/r/ObsidianMD/comments/mu3umb/what_is_pkm_what_is_personal_knowledge_management/`
- `https://medium.com/intuitionmachine/the-flaw-of-pkm-what-if-forgetting-is-not-a-bug-but-a-feature-b5d549e8c112`
- `https://adubrg.medium.com/organising-a-personal-knowledge-management-system-62dd0a758aa1`

## 5. Cognitive load rubric — confirmed against literature

**Confirmed source:** DCLRS (Documentation Cognitive Load Rating System) draws from Cognitive Load Theory (CLT, John Sweller). Three-category taxonomy:

- **Intrinsic (ICL)** — inherent complexity, 1–5 rated
- **Extraneous (ECL)** — presentation-induced friction, 1–5 rated
- **Germane (GCL)** — productive schema-building effort, 1–5 rated
- Composite CLI = (ICL + ECL) / (GCL × 0.5 + 1); target < 3.0

**Paas Cognitive Load Rating Scale** — 9-point subjective scale, used as research/measurement instrument.

### How this affects our wiki

- Our `cognitive_load: <int>` is a **single-number** approximation of one dimension (probably ICL or "overall effort"). It is *coarse* but appropriate for our scale (783 pages, single-document granularity).
- Multi-dimensional DCLRS would be a **3× metadata overhead per page** — overkill for our corpus size.
- **Local rubric (proposed, will need user approval to apply):**

| Value | Pattern (verified across 16 sampled pages) | Effort |
|---|---|---|
| `1` | Single-fact rule (often wikified AGENTS.md Hard rule). Load and apply reflexively. | Minimal reading |
| `1-3` (range form) | Same rule as `1` but admitting edge cases. 8 pages use this. | Quick scope check, then apply |
| `2` | Single-concept with caveats (ADRs, scoped conventions, diagnostic mechanics) | Read carefully; apply with caveats |
| `3` | Investigation / debugging recap; has `evidence_gaps:`. Read, probe, judge before acting. | Read, probe, judge |
| `4` | Architecture / wide-impact (multi-system ADRs, cross-provider benchmarks) | Deep reading |
| `5` | Reserved; unused in current corpus | n/a |

**Distribution across corpus (verified):** `1` x11, `1-3` x8 (range form), `2` x19, `3` x17, `4` x7. Total pages with the field set: 55. 729 pages have no field set.

### Sources

- `https://www.docsie.io/blog/glossary/cognitive-overload/`
- `https://hyperlint.com/blog/5-critical-documentation-best-practices-for-docs-as-code/`
- `https://pure.northampton.ac.uk/files/6968558/Turner_etal_SL_2019_Measuring_and_Reducing_the_Cognitive_Load_for_the_End_Users_of_Complex_Systems.pdf`

## 6. QMD auto-link failure — corpus reality, not bug

**Verified facts (session 2026-07-19):**

- QMD collection `wiki` indexed **1007 documents**, db size **41.47 MB**
- Control queries with topics I knew existed ("AGENTS.md hard rules", "plan mode recommendation", "slash command /export /plan /init claude code") returned max relevance **0.083** with most hits being unrelated noise from `sources/` and `chat-sessions/`
- The relevant concept pages exist but don't surface above the auto-link's threshold
- `wiki_after_write.py` correctly no-ops when QMD finds no qualifying concept neighbors — script behavior is correct, corpus relevance is below threshold
- Direct `qmd search --collection wiki "<query>"` for highly specific (OneDrive, mkdir) queries returns zero documents — confirms semantic similarity is genuinely low for our new pages

**Conclusion (high confidence):** Auto-link is **not broken**. The corpus has too low semantic redundancy for threshold-based auto-linking to work above zero precision. The QMD tooling may also benefit from `qmd update --collection wiki` to refresh against current corpus.

**Cited by the user as a discoverability problem.** The fix is not better thresholds — it's MOCs and link density (the Karpathy-derived remedies), not semantic-search tuning.

## 7. Deferred action items — ranked for the wiki session

These are ready to execute when the user pivots back to wiki work. Each has the why, what, and effort pre-stated.

### A. Reindex QMD — 30-second test (low risk, possibly fixes nothing)

```
qmd update --collection wiki
```

If QMD has been silently lagging since corpus growth past ~700 docs, relevance scores should jump. If they don't, no harm. Confirm before trying other items.

### B. Build MOC `claude-code-on-windows-moc.md` (~30 min)

Path: `P:/.data/wiki/concepts/claude-code-on-windows-moc.md`

Pull together:
- `claude-code-windows-11-config`
- `claude-code-windows-11-fixes`
- `claude-code-export-drive-root-perm-bug` (the export-EPERM page)
- `windows-onedrive-readonly-marker`
- `windows-cross-process-file-locking`
- `openai-codex-windows-11-troubleshooting`

Direct top-down entry; readers don't have to find these by QMD search. **Highest leverage** for discoverability per the Karpathy review.

### C. Add 3-link quality gate to wiki skill (~10 min skill edit)

Path: `~/.grok/skills/wiki/SKILL.md`

Append to Quality Gate section:

> Every new concept page must include ≥3 `[[wikilinks]]` to existing concept pages in `## Related` or `## Auto-related`. If neither can reach 3 links, link more directly or split the page.

### D. Add `verification:` frontmatter convention (~10 min, multi-page update)

Values: `local-only` / `inferred-only` / `multi-source-verified`.

Codifies the discipline the OneDrive page practices inline (`## Scope: /export only — other surfaces inferred`). Directly addresses the "confidently serves outdated info" failure mode Karpathy's reviewers warn about. Apply retroactively to existing pages where the answer is unambiguous.

### E. Document periodic lint ritual (~5 min skill edit)

```
## Recommended maintenance cadence

Run `python P:/packages/.claude-marketplace/plugins/cc-skills-utils/skills/main/scripts/wiki_health_check.py [--fix]`
monthly. Budget 30–45 min. Review by mtime for staleness, scan
orphans via the JSON report, fix structural issues with --fix
(safe repairs only). Karpathy's LLM Wiki reviewers find that
without this cadence the wiki becomes "an unreliable source that
confidently serves outdated info."
```

Adopting this in the skill text creates the surface for future ritual even if we don't enforce it.

### F. Optional: lift cognitive_load rubric into SKILL.md (~20 lines)

User to confirm. Draft is in this session's transcript; the rubric-paragraph proposal from earlier turn is ready. **Honest value assessment:** small but real; mostly helps future authors pick ad-hoc → consistent.

### G. Open questions — flag for user decision

1. **Vault-level `SCHEMA.md`** — Karpathy's "constitution" pattern. We have skill config (`~/.grok/skills/wiki/SKILL.md`) and ad-hoc conventions; a discoverable vault-level schema is what his reviewers credit as the highest-leverage piece. ~50 lines; clarifies "what convention was that?" ambiguity across agents. **Recommend: yes, after items A–E land.**
2. **Multi-agent coordination debt** — Karpathy's pattern is single-human-driven; we have Claude Code + Grok Build sharing the vault. This is a problem his pattern doesn't solve. Options: (a) strict SCHEMA.md + linting; (b) session-id in every edit; (c) accept noise + git log forensics. **Out of scope for this session.** Long-term architectural question.

### H. Cross-references

Wiki pages already created in this session (do NOT duplicate — link from new work):

- `P:/.data/wiki/concepts/claude-code-export-drive-root-perm-bug.md` — symptom-side of OneDrive EEXIST
- `P:/.data/wiki/concepts/windows-onedrive-readonly-marker.md` — cause-side; explicitly scoped to /export-only this session, other surfaces inferred

Log entries written this session (audit trail): 1 ingest for each new page + 2 update entries = 4 log entries dated 2026-07-19.

---

## 8. Open questions not yet resolved

1. **Tool drift lesson — encode where?** Per AGENTS.md there's a `~/.grok/tool-fallbacks.md` for broken-tool observations, but this isn't really a "broken tool" — it's "tools available but never tried." Different doc needed or don't encode at all (lesson lives in this conversation).
2. **Whether QMD scoring can be tuned** — `qmd` has backend options (`auto`, `llama_cpp`, `sentence_tf`). If scores are systematically low, switching backends might help. Out of scope until A is run.

   **Q2 closure (added 2026-07-19 B-lite execution):** QMD `llama_cpp` backend was not installed this session (`No module named 'llama_cpp'`); the cross-backend ceiling-equivalence claim has therefore **not** been empirically verified. Rejection of QMD tuning as a remedy is based on **theoretical reasoning only** (corpus has low semantic redundancy; embedder quality is unlikely to overcome that), not on empirical comparison. Defer until either `llama_cpp` is installed and tested, or corpus redundancy is improved via the wiki B-lite items (especially the MOC + link density), after which the ceiling can be re-measured. Captured baseline fingerprint at `P:/.data/wiki/qmd-baseline-2026-07-19.json` (top-1 score 0.083 on a control query, 1044 documents).
3. **Multi-host coordination gap** — Karpathy's pattern doesn't address; we have no answer. Long-term architectural.
