# Command-Surface Map: Intent-Level Architecture

**Created:** 2026-08-01
**Status:** Active design document
**Evidence base:** 50-session audit at `P:/docs/audits/system-redesign-authority-and-behavior-audit-2026-08-01.md`

## Principle

The user-facing surface exposes **7 intent-level commands**. Everything else is an internal mechanism selected by those commands or by the agent at runtime.

## The 7 user-intent commands

| Command | Cognitive contract | Input → Output |
|---|---|---|
| `/research` | Reduce uncertainty | Question → Evidence-backed understanding |
| `/design` | Reduce decision ambiguity | Goal + options → Chosen direction + rationale |
| `/plan` | Reduce execution ambiguity | Settled decision → Ordered implementation path |
| `/go` | Reduce implementation risk | Approved plan → Validated change |
| `/review` | Evaluate quality | Change → Verified findings |
| `/red-team` | Challenge safety/trustworthiness | Proposal → Adversarial assessment |
| `/close` | Session lifecycle | Session state → Completion gate verdict |

## Internal mechanisms (not user-facing commands)

These are invoked by the 7 commands or by the agent internally. They are skills the agent can call, but not commands the user needs to remember or choose between.

### Retrieval primitives (internal to /research)

| Skill | Role | Invoked by |
|---|---|---|
| `/web` | Web search execution | /research, /design (bounded), /red-team |
| `/search-fleet` | Multi-backend search with RRF | /research (internal), /web |
| `/wiki` | Durable knowledge query/write | /research, /design, /plan, /go, /review |
| `/wiki-crawl4ai` | Durable web page ingestion | /research (opt-in) |
| `/find` | Local file/skill retrieval | /research, /go |

### Investigation primitives (internal to /why and /design)

| Skill | Role | Invoked by |
|---|---|---|
| `/why` | Root-cause analysis | User (when investigating a failure), /red-team |
| `/trace` | Manual trace-through verification | /review, /check, user (when debugging) |

### Session lifecycle (internal to /close and /go)

| Skill | Role | Invoked by |
|---|---|---|
| `/handoff` | Continuation documents | /close, user (when ending mid-work) |
| `/harvest` | Obligation tracking | /close, /aar, /why |
| `/check` | PASS/FAIL session verification | /close, user (when checking work) |
| `/grok-verify` | Evidence-first completion gate | /go (internal pipeline step) |
| `/capture` | Improvement opportunity scanner | /close, user (when capturing findings) |
| `/aar` | After-action review | User (post-session) |
| `/recap-grok` | Session recap | User (when catching up) |
| `/friction` | Friction detection | /aar, user |
| `/slc` | Behavioral reset | User (when drift detected) |
| `/todo` | Work prioritization | User (when lost thread) |
| `/notice` | Mid-conversation surfacing | Automatic (trigger-based) |
| `/dream` | Cross-session consolidation | User (periodic) |

### External-model advisory (internal, fail-open)

| Skill | Role | Invoked by |
|---|---|---|
| `/agy` | Gemini second opinion | /review, /red-team, /design, user |
| `/codex` | GPT-5 second opinion | Same |
| `/mmx` | MiniMax search/chat | Same, plus web search via MiniMax index |
| `/model-web` | Browser-based LLM bridge | User (when specific web UI needed) |

### Fleet ops (internal)

| Skill | Role | Invoked by |
|---|---|---|
| `/model-quota` | Fleet quota dashboard | User (when checking quota) |
| `/model-benchmark` | Latency/cost benchmark | User (periodic) |
| `/maintain` | Fleet maintenance | User (periodic) |
| `/refactor` | Structural refactor | /go (when refactor-shaped) |
| `/refine` | Task tightening | User (before /go on vague tasks) |
| `/ship` | Publish chain | User (when ready to ship) |
| `/packet` | Evidence packing | User (when sharing context cross-model) |
| `/wargame` | Decision wargaming | /plan (when hard-to-reverse) |
| `/preflight` | Evidence-backed inventory | /go (discovery step) |
| `/skill-dev` | Skill measurement/improvement | User (periodic) |
| `/skill-prune` | Knowledge hygiene | /maintain |
| `/fmea` | Failure modes analysis | /go (pipeline scripts) |
| `/doc-check` | Documentation readiness | /ship |

### Aliases (compatibility redirects, no independent behavior)

| Alias | Redirects to | Status |
|---|---|---|
| `/grok-go` | /go | Keep (1 ref) |
| `/grok-sdlc` | /go | Keep (1 ref) |
| `/sdlc` | /go | Keep (1 ref) |
| `/debrief` | /aar | Keep (9 refs) |
| `/www` | /research | Will become alias after rename |

### Retired (to be deleted)

| Skill | Reason | Action |
|---|---|---|
| `why-old` | A/B comparison complete; superseded by /why v3 | Delete |
| `plan/SKILL.md.disabled` | Superseded by plan-writer | Delete file |

## What changes for the user

**Before:** The user must choose between `/web`, `/search-fleet`, `/www`, `/wiki`, `/find` for retrieval — 5 options.

**After:** The user types `/research <question>`. The skill internally selects the right retrieval backend (wiki for existing knowledge, web for external, grep for code, firecrawl for pages). The retrieval primitives remain available as power-user shortcuts but are not the primary interface.

**Before:** The user must choose between `/check`, `/review`, `/trace`, `/grok-verify` for verification — 4 options.

**After:** `/review` is the primary quality evaluator. `/check` remains as a session-completion verifier (used by /close). `/trace` becomes a mode of /review or remains as a power-user tool for manual verification. `/grok-verify` stays internal to /go.

## What does NOT change

- `/go`, `/design`, `/plan`, `/review`, `/red-team`, `/close` stay as they are — they already have distinct cognitive contracts.
- All internal mechanisms stay as skills — they just stop being primary user-facing commands.
- External-model skills (`/agy`, `/codex`, `/mmx`) stay user-invocable for power users but are primarily called internally by /review, /red-team, /design.
- The agent can still invoke any skill at any time — the map defines the *recommended* user surface, not a restriction on agent behavior.
