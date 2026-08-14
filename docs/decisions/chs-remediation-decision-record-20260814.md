# Decision Record: CHS remediation — location, storage, MCP, retirement

## Scope

Covers the remediation campaign for the chat-history-search (CHS) subsystem
shipped 2026-08-13/14 in session 019ffbf4: package location, git topology,
database topology, MCP surface, episodic-memory retirement, and execution
shape. Produced by /grill-me (2 rounds, 16 decisions) on 2026-08-14.

## Resolved decisions

### D1 (Q1/Q11): Package location — `P:/packages/search-research/`
**Answer:** Neutral `packages/` path, not `.claude-marketplace/plugins/`, not `.agents/`.
**Rationale:** Cross-host tool in a Claude-branded path was the root location
incoherence. `.agents/` is the agent-scripts/skills home (referenced by every
AGENTS.md rule); an 812-file pip package + MCP server belongs with the other
packages (`research_runtime`, `claude-history`, yt-is). `P:/packages/search-research/`
already existed with CHS data in it.
**Load-bearing:** yes.

### D2 (Q2): One unified DB at `P:/.data/chs/chat_history.db`
**Answer:** Single DB with a `provider` column; path `P:/.data/chs/chat_history.db`
(matches workspace data convention, neutral, cross-host).
**Rationale:** Separate DBs disable the provider architecture's core payoff —
cross-agent search ("what did any agent conclude about X"). `__csf/` is the
data dir of the system this package replaces (EOL 2026-09-01) — new data must
not land there.
**Load-bearing:** yes.

### D3 (Q3): Fresh rebuild, not migration
**Answer:** Rebuild the unified DB from sources via all providers.
**Rationale:** All corpora are derived data; providers re-read sources.
Simpler than three-way merge; guarantees `provider` column populated everywhere.
**Load-bearing:** yes (blocks D2 rollback thinking — old DBs remain on disk as fallback).

### D4 (Q12): Dedicated `chs` MCP server, NOT extending the sr server
**Answer:** New small FastMCP stdio server, tools `search` + `read` under
server prefix `chs` (i.e., `chs__search` / `chs__read`). Registered in Grok
config.toml. sr MCP server left untouched.
**Rationale:** The sr MCP server is not registered on Grok at all and drags
web-search/CKS machinery. Deep module, tiny surface. Operator requested
`search_chs` naming — resolved as prefix `chs` + tool `search` to avoid the
redundant `chs__search_chs`.
**Load-bearing:** yes.

### D4b (Q12 follow-up): search-fleet integration — yes
**Answer:** Add `[tools.chs]` block to `~/.grok/search-fleet.toml` so CHS is a
backend in unified search (search_web MCP).
**Rationale:** Registry-based — no code changes; makes chat history searchable
from the fleet's unified entry point.

### D5 (Q5/Q13): episodic-memory OFF on Grok now
**Answer:** Remove/disable the episodic-memory MCP registration on Grok this
campaign; port the `remembering-conversations` skill to CHS. Claude-side fix
deferred ("we'll leave claude to fix claude" — operator will run /plugin there).
**Rationale:** It was in Grok's plugin-disabled list twice already yet the MCP
still connected — plugin-disable and MCP-disable are separate switches, and
neither took. Overlapping memory systems are the anti-goal of rationalization.
**Load-bearing:** yes.

### D6 (Q6): De-submodule — absorb into parent repo
**Answer:** `packages/search-research/` becomes plain tracked files in the
parent `P:\` repo. No submodule, no gitlink.
**Rationale:** The submodule class caused every failure this session: empty
source dir (unresolved init), unreachable gitlink (395cc56 never pushed),
placeholder URL, broken worktree link. One source of truth; parent `git log`
covers it.
**Load-bearing:** yes.

### D6b (Q15): GitHub as mirror, not submodule remote
**Answer:** Keep `github.com/EndUser123/search-research` as an offsite backup
via `git subtree push --prefix=packages/search-research <url> absorbed-main`.
**Rationale:** Regular push is safe; force-push forbidden on this host; GitHub
`main` has unrelated old history, so the mirror lives on a new branch
(`absorbed-main`); old `main` = pre-absorption snapshot.
**Load-bearing:** no (backup mechanism).

### D7 (Q7): Watermark-based unified indexer
**Answer:** One `reindex` that runs all providers via `ingest_since(watermark)`,
storing watermarks; populates `sessions.first_prompt` so CLI Stage-1 works;
builds turns.
**Rationale:** Provider protocol already implies this design; the shipped
`reindex_grok.py` bypassed it (re-read + INSERT OR IGNORE).
**Load-bearing:** yes.

### D8 (Q8): One campaign, staged commits with verify gates
**Answer:** Execute now, in-session, staged A–E with verification after each.
**Rationale:** Pieces interlock; doing them separately means moving/migrating/
reindexing multiple times. Operator: "/go now".
**Load-bearing:** no (execution shape).

### D9 (Q9): FTS full backfill in-campaign; embeddings deferred
**Answer:** Full FTS index of all Grok + Claude sessions now; semantic
embeddings later as a separate pass.
**Rationale:** FTS is the immediate search payoff; 203K+ event embedding
compute is a schedulable background pass.

### D10 (Q10): Acceptance criteria adopted
(a) `chs__search` via MCP returns hits across all providers from one DB;
(b) both hosts' `/chs` skills return non-empty results with commands test-fired;
(c) episodic-memory MCP off on Grok, skill ported;
(d) no new wiring path under `.claude-marketplace` or `__csf`;
(e) parent repo green, no stale gitlink; (f) mirror branch pushed.

### D11 (Q14): Claude re-point — junction + reinstall (owner: operator/Claude side)
**Answer:** Junction `marketplaces/local/plugins/search-research` →
`P:/packages/search-research`, bump version, reinstall to refresh cache.
Operator chose to handle Claude-side himself ("we'll leave claude to fix claude").
Campaign ships the junction; Claude reinstall documented in handoff.
**Load-bearing:** yes (cross-host continuity).

## Glossary

- **CHS** — Chat History Search subsystem of search-research (`core/chs/`).
- **Provider** — a class implementing discover/ingest_since/fetch_session/
  fetch_message over one transcript format. Four: claude_code_raw,
  codex_desktop, claude_log, grok_sessions.
- **Watermark** — per-source checkpoint (last processed line/offset) enabling
  incremental ingest.
- **Absorption** — moving a submodule's files into the parent repo as plain
  tracked files (opposite of vendoring-as-submodule).
- **Git mirror** — second remote receiving subtree pushes of one directory;
  no pinning semantics.

## Open questions

- Claude-side episodic-memory disable + plugin reinstall (operator-owned).
- Embeddings daemon wiring for the unified DB (deferred pass).

## Recommended next

Executing per D8. Feed this record to /check at campaign end.
