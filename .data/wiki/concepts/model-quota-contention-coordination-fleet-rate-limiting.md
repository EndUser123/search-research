---
title: "Model quota contention coordination: proactive rate-limit avoidance for agent fleets"
created: 2026-08-02
source: session-20260802 (/www research: rate-limit avoidance for multi-agent model dispatch)
tags: [models, routing, rate-limit, contention, coordination, fault-tolerance, self-healing, distributed-systems, lease, semaphore, token-bucket, admission-control, fleet, grok-build]
summary: >
  When N agent terminals share the same provider API quotas, independent
  per-session retry/failover logic actively makes contention worse (thundering
  herd on recovery). The solution is a shared coordination layer that tracks
  quota consumption centrally and admits dispatches before they hit 429s.
  The key distinction the operator's framing missed: rate limits are
  throughput-based (RPM/TPM/RPD), not concurrency-based ("model in use") —
  so the coordinator must track token consumption, not just availability
  flags. This concept synthesizes 50+ findings across distributed rate
  limiting, lease/lock availability tracking, fault-tolerant self-healing,
  and production LLM gateways into 5 tiers of recommendations, each passed
  through an applicability gate against this host's constraints (no proxy
  point for parent/spawn traffic, single Windows host, shared filesystem).
agent: grok
host: grok
cognitive_load: 4
verification: research-synthesis
status: active
sources:
  - "https://www.tamirdresher.com/blog/2026/03/21/rate-limiting-multi-agent (Tamir Dresher: 9 AI Agents One API Quota — rate coordination patterns)"
  - "https://redis.io/docs/latest/develop/use-cases/rate-limiter/redis-py/ (Redis token bucket with atomic Lua)"
  - "https://oneuptime.com/blog/post/2026-01-21-redis-distributed-semaphore/view (Distributed semaphore with Redis sorted set)"
  - "https://matheuspalma.com/blog/http-api-admission-control-concurrency-queues-load-shedding (Admission control: concurrency caps, queues, load shedding)"
  - "https://www.oh-bug.com/posts/llm-multi-tenant-quota-gateway-production-guide/ (Multi-tenant LLM quota gateway: control plane + data plane)"
  - "https://singhajit.com/distributed-systems/lease/ (Lease pattern: TTL + fencing tokens)"
  - "https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html (Kleppmann Redlock critique)"
  - "https://etcd.io/docs/v3.7/learning/why/ (etcd leases + lock API)"
  - "https://quality.arc42.org/approaches/watchdog-supervision (Watchdog supervision pattern)"
  - "https://agents.stackoverflow.com/blueprints/e17a499e-a439-48e9-8124-597b2241a6e9 (Progress-based liveness vs process-only heartbeat)"
  - "https://docs.litellm.ai/docs/proxy/load_balancing (LiteLLM proxy: RPM/TPM, cooldown, Redis-synchronized state)"
  - "https://medium.com/@ThinkingLoop/6-fastapi-rate-limiter-strategies-that-dont-stall-throughput-356a8f906c6c (Dual-layer rate limiting: local-first + global reconciliation)"
  - "https://digitalthoughtdisruption.com/2026/07/29/ai-agent-feeding-frenzy-shared-resource-governance/ (Shared resource governance for AI agents)"
  - "https://arxiv.org/html/2603.12229v1 (Language Model Teams as Distributed Systems — centralized vs decentralized coordination)"
  - "https://www.onorca.dev/docs/agents/usage-tracking (Orca: reads local per-agent usage state files for centralized tracking)"
relations:
  - target: wiki/concepts/execution-path-based-model-routing-grok-build.md
    type: extends
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: complements
  - target: wiki/concepts/model-pool-not-chain.md
    type: related
  - target: wiki/concepts/auto-model-switch-on-rate-limit-20260728
    type: precedes
  - target: wiki/concepts/fleet-quota-api-discovery-2026.md
    type: extends
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: related
---

# Model quota contention coordination: proactive rate-limit avoidance for agent fleets

## Decision context

**The problem that motivated this research:** the operator's fleet of 5-10
concurrent AI agent terminals on a single Windows host frequently hits rate
limits from model/inference providers. The existing system is entirely
**reactive** — each session independently fails over on 429 (per-session
model pools, spawn gate deny-and-redirect, tool-fallbacks). There is no
fleet-wide coordination: two sessions can simultaneously select the same
hot model because nothing tells session B what session A just selected.
The operator asked: "maybe we need to track centrally or in a shared way
when a model is being used vs available."

**What alternatives were explored during research:** proxy-based gateways
(LiteLLM, Portkey, Cloudflare AI Gateway), distributed coordination stores
(etcd, Redis, ZooKeeper, SQLite, file locks), admission control patterns
(token bucket, semaphore, queue-with-tickets), and fault-tolerance
mechanisms (Raft consensus, watchdog supervision, lease TTL + fencing
tokens). Each was evaluated against this host's specific constraints.

**What the research changed:** it reframed the operator's intuition. The
question "is the model available?" (concurrency) is necessary but
insufficient — rate limits are throughput-based (RPM/TPM/RPD), so the
coordinator must track **quota consumption rate**, not just "in use"
flags. The research also confirmed that a proxy-based gateway — the
industry default — doesn't fit this host because parent-session and
spawn_subagent traffic bypasses any proxy we can insert (per
[[execution-path-based-model-routing-grok-build]]). The viable path is a
**shared-state advisory layer** (file-based or Redis-backed) that each
session consults before dispatching, combined with local-first
rate-limiting per process and watchdog-based self-healing.

## Workspace observations (Phase 1a)

1. **The system was reactive-only until 2026-08-03, when proactive pre-checks were added.** `fleet_quota.py`
   checks provider quota dashboards; `pick_model.py` filters by quota
   cache; `PreToolUse_spawn_model_gate.py` denies serde-broken or
   quota-exhausted models; `PostToolUseFailure_spawn_quota.py` updates the
   cache *after* a failure. As of 2026-08-03, `/design` and `~/.grok/AGENTS.md` now mandate a **proactive quota pre-check**: run `pick_model.py --list` before the first subagent dispatch, use the returned models instead of hardcoded slugs. The `PreToolUse_spawn_model_gate.py` hook remains as the reactive safety net. This eliminated the pattern of 3+ failed spawn attempts on quota-exhausted providers (observed 2026-08-03 with OpenCode-Go at 0%). [FACT: commit `f768c24` — `/design` SKILL.md "Quota pre-check" subsection + AGENTS.md "Quota pre-check before subagent dispatch"]

2. **Prior incidents are documented.** Session 019f821c: Token Plan 429s
   made `/tp` degrade to inline every time. Session 019fa94d: parent
   glm-5.2 halted on 429, requiring manual `/model` intervention. The
   `auto-model-switch-on-rate-limit-20260728` handoff explicitly states:
   "no fleet-wide mechanical parent-session failover verified." [FACT:
   handoff content read above]

3. **The proxy pattern was already rejected for this host.** The
   `execution-path-based-model-routing` concept documents: "Grok Build's
   parent model talks to xAI's API directly — there's no proxy point we
   can insert. Subagent spawns go through Grok's internal dispatch, not an
   HTTP API we control." This means a LiteLLM-style gateway can only help
   for Layer 3 (CLI: opencode/mmx/agy) traffic, not the main
   parent/spawn traffic. [FACT: wiki concept read above]

4. **The operator's priority-tier system already exists.** The
   `model-pool-selection-policy` defines Critical / Standard / Background
   priority tiers. The Tamir Dresher priority-retry-window pattern maps
   directly onto these existing tiers. [FACT: wiki concept read above]

## Research threads (Phase 1)

- **Prior:** this extends [[execution-path-based-model-routing-grok-build]]
  (researched 2026-07-30) and [[auto-model-switch-on-rate-limit-20260728]]
  (investigated 2026-07-28). Those focused on *reactive failover*; this
  focuses on *proactive coordination* — the missing layer.
- **Pattern:** 3rd research on the model-dispatch/rate-limit domain.
  Prior runs: model-pool-selection-policy, execution-path-based-routing.
  This is the first to research *contention coordination* specifically.
- **No threads from the www-ledger** — no prior /www run on this topic.

## The critical distinction: concurrency vs throughput

**This is the highest-signal finding from the research.** The operator's
framing — "track when a model is being used vs available" — maps to a
**concurrency semaphore** (how many calls are in flight right now). But
provider rate limits are **throughput-based**:

| Rate limit type | What it constrains | Semaphore catches it? |
|----------------|-------------------|----------------------|
| **RPM** (requests per minute) | Call count over a 60s window | Partially — limits concurrency but not total calls |
| **TPM** (tokens per minute) | Token consumption over 60s | **No** — a single call can consume 100K tokens |
| **RPD** (requests per day) | Call count over 24h | **No** — semaphore resets per-call |
| **Concurrency** (in-flight requests) | Simultaneous connections | Yes — but this is rarely the binding constraint |

**Implication:** a pure availability tracker ("model X has 3 slots, 2 in
use") prevents connection-pool exhaustion but does NOT prevent RPM/TPM/RPD
exhaustion. The coordinator must track **quota token consumption** using a
token bucket / shared ledger, not just an in-use flag. The Tamir Dresher
"Shared Token Pool" pattern and the "Multi-Tenant LLM Quota Gateway"
pattern both combine concurrency caps + token-bucket accounting — that is
the correct model.

## Five tiers of recommendations (each passed applicability gate)

### Tier 1: Shared quota ledger (file-based, no external server) — RECOMMENDED FIRST

**What:** A single JSON or SQLite file on the shared filesystem
(`P:/.data/fleet/quota-state.json` or `.db`) that tracks per-provider,
per-window quota consumption. Each session consults it before dispatching
and updates it after each API call. Uses atomic file writes (tmp +
`os.replace`) or SQLite WAL transactions for crash safety.

**Why this first:** it requires zero infrastructure beyond the shared
filesystem that already exists. It directly extends the existing
`fleet_quota.py` (which reads dashboards) into a live consumption tracker.
The Orca tool (source: onorca.dev) does exactly this: "reads the local
usage state each agent maintains on disk (under ~/.claude, ~/.codex, and
the Gemini/OpenCode equivalents)" — a production example of file-based
quota tracking across concurrent agent sessions.

**Applicability gate:**

| Dimension | Assessment |
|-----------|-----------|
| System openness | ✅ Works for any execution path (parent, spawn, CLI) since it's advisory, not a proxy |
| Multi-model pool | ✅ Tracks per-provider, per-model independently |
| Evidence type | ✅ Operates on actual consumption data, not predictions |
| Ground truth | ✅ Provider 429s are the ground truth; ledger is the estimate |
| Task domain | ✅ Applies to all task types |

**PROMOTE: YES.** This is the foundational layer. Self-healing: TTL-based
lease expiry on each ledger entry (see Tier 4). Fault tolerance: if the
ledger is corrupted or stale, each session falls back to its own local
quota estimate (dual-layer pattern, Tier 3).

**[HIGH confidence]** — 3+ independent sources (Tamir Dresher shared
ledger, Orca local-state-reading, LLM quota gateway two-phase accounting).
Disconfirmation pass: the central file is a potential SPOF, mitigated by
atomic writes + local-first fallback.

### Tier 2: Priority-tier dispatch with staggered retry windows

**What:** Assign each dispatch a priority (P0 critical / P1 standard / P2
background — maps directly to the existing
`model-pool-selection-policy` tiers). When contention is detected (quota
pool <30%), P2 agents yield automatically, P1 agents use reservations, P0
agents always get completions. Each tier gets non-overlapping retry
windows (P0: 0-0.5s, P1: 0.5-3.5s, P2: 3.5-9.5s) so priority inversion is
structurally impossible. Starvation prevention: any P2 agent denied for
5+ minutes gets promoted to P1.

**Why this matters:** without priority tiers, a background breadth-scan can
starve a critical implementation the operator is actively watching. With
staggered windows, critical work always consumes freed quota before
background work even begins retrying. This is the Tamir Dresher pattern,
validated on a 9-agent fleet.

**PROMOTE: YES.** Natural fit with existing priority tiers. [HIGH confidence]

### Tier 3: Dual-layer rate limiting (local-first + shared reconciliation)

**What:** Each terminal process maintains an in-memory token bucket for
ultra-low-latency local checks (nanosecond-fast), then reconciles against
the shared ledger every 1-3 seconds. If the shared state is stale or
unreachable, local buckets still guard the session. Brief overshoot is
possible if all sessions spike simultaneously — acceptable for API quotas,
not for financial controls.

**Why this is the self-healing layer:** if the shared ledger dies, each
session continues operating on its local estimate. The system degrades
gracefully (back to reactive per-session failover) rather than failing
catastrophically. The hot path (every dispatch) never blocks on file I/O
or network — only the background reconciliation touches shared state.

**PROMOTE: YES.** This is what makes the system fault-tolerant. [HIGH
confidence — Medium/@ThinkingLoop, appscale.blog, matheuspalma.com all
describe this pattern]

### Tier 4: Watchdog supervisor + lease TTL (self-healing coordinator)

**What:** An independent watchdog process (Python script, launched by
`cc-ccr.ps1` or a Windows scheduled task) monitors the shared ledger's
heartbeat file. Every entry in the ledger has a TTL (e.g., 120s). The
holder must refresh via heartbeat before TTL expiry; if a session crashes
without releasing, a background sweep every 30s reclaims stale entries.
The watchdog itself uses progress-based liveness (not just process-exists
checks) — it measures "tokens allocated per minute" and restarts if
progress stalls, catching **wedged** (hung-but-alive) sessions that a
plain heartbeat would miss.

**Why this is mandatory:** without TTL expiry, crashed sessions leave
phantom quota reservations that slowly starve the pool. Without a
watchdog, the ledger itself has no self-healing. The fencing-token
pattern (monotonically increasing token on each lease acquisition)
prevents a paused/crashed coordinator from writing stale state after
restart.

**PROMOTE: YES.** The cc-ccr.ps1 supervisor pattern already exists on this
host and could host the watchdog. [HIGH confidence — arc42 watchdog
pattern, agents.stackoverflow.com progress-based liveness, Kleppmann
fencing tokens]

### Tier 5: LiteLLM proxy for CLI traffic only (optional, Layer 3)

**What:** Deploy a local LiteLLM proxy with Redis-backed shared state for
the CLI execution path (opencode, mmx, agy). It enforces RPM/TPM per
deployment, places 429-returning deployments on cooldown, and load-balances
across alternatives automatically.

**Why only CLI traffic:** the `execution-path-based-model-routing` concept
already established that parent-session and spawn_subagent traffic bypasses
any HTTP proxy — Grok Build's parent talks to xAI directly, and spawns go
through Grok's internal dispatch. LiteLLM can only intercept CLI traffic.
This makes it a **complement** to Tiers 1-4 (which work on all paths), not
a replacement.

**PROMOTE: CONDITIONAL.** Only worth the setup cost (Redis + LiteLLM
process) if CLI traffic is a significant source of 429s. For most of the
fleet's traffic (parent + spawn), Tiers 1-4 cover the need. [MEDIUM
confidence — applicability is partial for this host]

## Patterns evaluated and rejected

| Pattern | Why rejected for this host |
|---------|--------------------------|
| **Raft consensus cluster** | Overkill for single-host. No quorum benefit when all sessions share one filesystem. |
| **etcd / ZooKeeper** | Requires running a 3+ node cluster. Operational overhead far exceeds the problem. A file-based ledger + watchdog achieves the same liveness guarantees. |
| **Redlock (multi-instance Redis)** | Kleppmann critique: no fencing tokens, fails under clock jumps. Single-instance Redis SETNX is simpler and sufficient if Redis is used at all. |
| **Cloudflare AI Gateway / Portkey / OpenRouter** | Cloud-managed. Cannot run locally on a single Windows host. Adds network dependency + latency. |
| **Pure proxy gateway (all traffic)** | Rejected per [[execution-path-based-model-routing-grok-build]]: no proxy point exists for parent/spawn traffic. |
| **CRDT-based distributed rate limiter** | Novel (IJSET 2025) but research-stage; no production LLM implementation exists. File-based ledger is simpler and proven (Orca). |

## The architecture that fits this host

```
┌─────────────────────────────────────────────────────────────┐
│  Each terminal session (5-10 concurrent)                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Local token bucket (in-memory, nanosecond checks)  │   │
│  │  ↕ reconciles every 1-3s                            │   │
│  └──────────────────────┬──────────────────────────────┘   │
│                         │                                   │
│  Before dispatch:       │ read shared quota state           │
│  After API call:        │ write actual consumption          │
│  Priority tier:         │ P0/P1/P2 (from pool-selection)    │
└─────────────────────────┼───────────────────────────────────┘
                          │
          ┌───────────────▼───────────────┐
          │  Shared quota ledger           │
          │  P:/.data/fleet/quota-state.db │
          │  (SQLite WAL or JSON+atomic)   │
          │  Per-provider, per-window      │
          │  Each entry: TTL lease         │
          └───────────────┬───────────────┘
                          │
          ┌───────────────▼───────────────┐
          │  Watchdog supervisor           │
          │  (background Python process)   │
          │  - Sweep stale entries (30s)   │
          │  - Progress-based liveness     │
          │  - Restart on stall            │
          │  - Fencing tokens on writes    │
          └───────────────────────────────┘
```

**No external server required.** The entire coordination stack is a shared
file + a background process. This is the lightest possible implementation
that provides: proactive avoidance, fault tolerance (local-first
fallback), self-healing (TTL + watchdog), and accuracy (consumption
accounting, not just availability flags).

## Fault tolerance and self-healing properties

| Failure mode | What happens | Recovery |
|-------------|-------------|----------|
| **Session crashes mid-call** | Its lease entry has a TTL; expires after ~120s | Watchdog sweep reclaims tokens to donation pool |
| **Shared ledger corrupted** | SQLite WAL or atomic-write guarantees prevent partial writes | If corrupted: sessions fall back to local token buckets (Tier 3) |
| **Watchdog process dies** | Leases stop being swept; stale entries accumulate slowly | Windows scheduled task restarts watchdog; existing cc-ccr supervisor pattern |
| **Watchdog is wedged (hung-but-alive)** | Progress-based liveness detects zero allocations/min | Restarts watchdog (distinguishes hung from busy) |
| **All sessions spike simultaneously** | Local buckets may briefly overshoot shared quota | Acceptable for API quotas; brief 429 possible, mitigated by failover pool |
| **Provider changes rate limits** | Ledger estimates drift from reality | Actual 429s correct the estimate (PostToolUseFailure already does this) |

## What people actually like (practitioner signal)

`[PRACTITIONER]` sources from Reddit, GitHub Issues, and blogs:

- **Reddit r/LLMDevs (2026-03-17):** "Why don't we have a proper 'control
  plane' for LLM usage yet? The hard part is that LLM control planes need
  semantic routing, not just rate limiting." — confirms the gap is widely
  felt but unsolved. [ENGAGEMENT: active discussion thread]
- **Reddit r/LLMDevs (2025-08-08):** "How do you handle rate limits in LLM
  providers in a larger scale? The agent can call multiple sub-agents in
  parallel with thousands of tokens." — exactly the operator's problem.
- **r/LLM_Gateways:** a dedicated subreddit exists for LLM gateway
  discussions — confirms an active practitioner community around this.
- **LiteLLM GitHub Issue #13930 (closed, implemented):** "Add per-model
  `max_parallel_requests` limit" — the most-requested concurrency feature
  for LLM gateways, now shipped. LiteLLM also has open issues for RPD rate
  limits (#14398) and TPM bugs (#24677) — active development.
- **"The AI Agent Feeding Frenzy" (digitalthoughtdisruption.com,
  2026-07-29):** "Several agents may consume the same provider quota even
  when each agent has its own local limiter." — names the exact failure
  mode this concept addresses.
- **"Single Point of Failure Hidden in Your AI Agent Fleet"
  (agentcenter.cloud):** "Four agents all sharing the same rate-limited API.
  When that API hits its limit, four failures show up at once." — the
  thundering-herd problem on recovery.
- **Codex CLI (codex.danielvaughan.com, 2026-04):** "The Two Faces of 429:
  not all 429s are equal." Plan-quota exhaustion vs API-key rate limits need
  different recovery paths. [STALE-CHECK: version-specific, but pattern
  generalizes]

## Disconfirmation pass results

**Disconfirmation queries used:**
1. "centralized rate limit coordinator bottleneck single point of failure"
2. "why not central coordinator multi-agent rate limit provider quota opaque"

**Emerging conclusions tested:**

| Conclusion | Result | Evidence |
|-----------|--------|---------|
| Centralized coordination is needed for shared quotas | **CONFIRMED** | Tamir Dresher: "independent retry logic doesn't just fail. It actively makes things worse." 5+ practitioner sources agree. |
| The central coordinator is a SPOF | **CONFIRMED — but mitigable** | Kleppmann: "the coordinator is a single point of failure." arxiv 2603.12229: centralized = "bottlenecks and single points of failure." Mitigated by local-first dual-layer (Tier 3) + watchdog (Tier 4). |
| Tracking "model in use" prevents rate limits | **REFUTED as sufficient** | Rate limits are throughput-based (RPM/TPM), not concurrency-based. Must track consumption, not just availability. |
| Proxy gateway solves the problem | **QUALIFIED** | Only for CLI traffic. Parent/spawn bypasses proxy (per execution-path concept). |

**Gap-as-signal check:** why doesn't everyone build centralized coordination?
1. Most frameworks (LangGraph, CrewAI, AutoGen) defer rate limiting to provider retry — they treat 429 as transient, not coordination.
2. The problem only manifests at fleet scale (5+ concurrent agents). Most users have 1-2 agents.
3. Provider rate limits are opaque — no API to check remaining quota. Must estimate from consumption.
4. The central coordinator is a SPOF — people avoid it (or mitigate with local-first).

The absence is NOT evidence of an anti-pattern — it's evidence of
under-solving. The Tamir Dresher post ("the rate limiting problem nobody
talks about") and the r/LLMDevs "why don't we have a control plane yet"
thread both confirm this is an unsolved problem the field is starting to
recognize.

## Host invariant check

**Scanned against known host constraints:**

| Invariant | Check | Result |
|-----------|-------|--------|
| Multi-terminal isolation (CDP/cookie/auth) | Quota ledger reads/writes quota state files only — never touches browser state | ✅ No violation |
| Shared filesystem atomic writes | Must use atomic write (tmp + `os.replace`) or SQLite WAL — consistent with file-editing-protocol | ✅ Use SQLite WAL or Python atomic write |
| No external server dependency preferred | Tiers 1-4 require zero external servers (file + background process only) | ✅ Preferred path is serverless |
| Single Windows host | All patterns work on single host; no multi-region/multi-host assumptions | ✅ |
| Concurrent commit collision (git) | Ledger is in `P:/.data/fleet/`, not git-tracked — no commit collision | ✅ Add to .gitignore |

**Host invariant check: PASSED.** No violations. The file-based approach
is the safe alternative; the proxy approach (Tier 5) is scoped to CLI
traffic only and does not violate multi-terminal isolation.

## Falsifier

This concept is wrong if:
1. **The file-based ledger proves unreliable on NTFS under 10 concurrent
   writers.** SQLite WAL handles this, but if corruption is observed in
   practice, the concept must fall back to Redis (adding the external
   server it tried to avoid).
2. **Provider rate limits are so opaque that consumption estimates drift
   too far from reality to be useful.** If the ledger's estimates produce
   more 429s than the current reactive system, proactive coordination
   adds overhead without benefit.
3. **The watchdog/sweep approach proves insufficient for wedged
   sessions.** If progress-based liveness can't reliably detect hung
   agents on Windows, stale entries accumulate and starve the pool.
4. **Grok Build adds `updatedInput` to PreToolUse hooks**, making
   seamless model injection at the hook level possible — this would
   obsolete the advisory-layer approach in favor of hook-level
   enforcement (per the execution-path concept's falsifier).

## What this means for our workspace

- **Build Tier 1 first:** a shared quota ledger extending `fleet_quota.py`
  from dashboard-only to live consumption tracking. The
  `auto-model-switch-on-rate-limit-20260728` handoff's AMS-02 task packet
  (shared spawn pool helper) is the natural integration point — the helper
  should consult the ledger before picking a model.
- **Wire `pick_model.py` to read the ledger** before returning a model —
  this closes the "no skill currently calls pick_model.py before spawning"
  gap noted in the execution-path concept.
- **Add the watchdog** to the existing `cc-ccr.ps1` supervisor startup
  sequence so it launches and restarts automatically.
- **The priority-tier dispatch** (Tier 2) maps directly onto the existing
  Critical/Standard/Background tiers in `model-pool-selection-policy` —
  add staggered retry windows to the spawn pool helper.
- **Handoff:** this research identifies the architecture; implementation
  belongs in a `/go` or `/design` follow-up, not this /www run.

## Receipts

Local mechanism claims are sourced from workspace artifacts read during Phase 1a:

| Claim | Receipt |
|-------|---------|
| `fleet_quota.py` checks provider quota dashboards | `execution-path-based-model-routing-grok-build.md` lines 127-129 (infrastructure list) |
| `pick_model.py` filters by quota cache + serde-broken set | same concept, line 128; function `pick()` documented at line 148 |
| `PreToolUse_spawn_model_gate.py` denies serde-broken + quota-exhausted models | same concept, line 128; function `get_serde_broken()` at line 148 |
| `PostToolUseFailure_spawn_quota.py` updates cache after failure | same concept, line 128 |
| "no skill currently calls pick_model.py before spawning" | same concept, line 129-130 |
| Proxy pattern rejected: "parent model talks to xAI's API directly — no proxy point" | same concept, lines 106-109 (Steelman section) |
| Parent 429 requires manual `/model` intervention (no auto-failover) | `auto-model-switch-on-rate-limit-20260728/HANDOFF.md` lines 68, 76 |
| cc-ccr.ps1 supervisor exists on this host | `~/.grok/AGENTS.md` Environment section |
| Priority tiers (Critical/Standard/Background) already defined | `model-pool-selection-policy-speed-quota-diversity.md` lines 218-228 |

All external findings are cited inline with source URLs and quality scores
(see Sources table below). Findings marked `[PRACTITIONER]` include
engagement signals. The disconfirmation pass results are labeled CONFIRMED
/ QUALIFIED / REFUTED in the Disconfirmation section.

## Sources (quality-scored)

| Source | Score | Type |
|--------|-------|------|
| tamirdresher.com (9 AI Agents, One API Quota) | 13 | Practitioner blog with working patterns |
| redis.io (token bucket rate limiter) | 12 | Official docs |
| docs.litellm.ai (proxy load balancing) | 12 | Official docs |
| etcd.io (leases + lock API) | 11 | Official docs |
| martin.kleppmann.com (Redlock critique) | 11 | Authority (author of DDIA) |
| matheuspalma.com (admission control) | 10 | Practitioner blog |
| oh-bug.com (LLM multi-tenant quota gateway) | 10 | Production guide |
| oneuptime.com (distributed semaphore) | 10 | Technical blog |
| quality.arc42.org (watchdog supervision) | 10 | Architecture reference |
| agents.stackoverflow.com (progress-based liveness) | 9 | Blueprint |
| medium.com/@ThinkingLoop (dual-layer rate limiting) | 9 | Technical blog |
| digitalthoughtdisruption.com (shared resource governance) | 9 | Practitioner blog |
| onorca.dev (local usage state tracking) | 9 | Product docs |
| arxiv 2603.12229 (Language Model Teams as Distributed Systems) | 9 | Academic paper |
| singhajit.com (lease pattern) | 8 | Technical reference |
| reddit r/LLMDevs (control plane thread) | 8 | Community discussion |
