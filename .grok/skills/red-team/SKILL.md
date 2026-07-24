# /red-team workspace overlay — adaptive investigation + precision incentives + cross-model specialists

This file is a workspace-level overlay that extends the bundled /red-team
skill with three features: **adaptive investigation space expansion**,
**specialist precision incentives**, and **cross-model specialist dispatch**.

## When this overlay applies

This overlay adds the features described below to every /red-team
run. It does not replace or modify any other aspect of the bundled skill.
All other phases (planning, specialist dispatch, critic verification,
synthesis, telemetry) remain unchanged.

## Expansion gate (runs after specialist manifest, before critic dispatch)

After all specialists return and the dispatch manifest is written, the
orchestrator reviews the combined findings for **new attack surfaces**
that the original plan didn't cover. This is confidence-gated expansion:
the orchestrator must be confident the operator would want more
investigation, not just curious about a tangent.

### Expansion trigger (all three required)

1. A specialist finding reveals a defect class or attack surface that
   **none of the dispatched specialists was scoped to investigate** (not
   a deeper version of an existing finding — a genuinely new surface).
2. The finding is **severity HIGH or CRITICAL** (medium/low findings
   don't trigger expansion — they go in the synthesis as-is).
3. The orchestrator is **highly confident** the operator would want this
   investigated in the same run rather than deferred to a future one.

### Expansion mechanics (bounded)

| Constraint | Limit |
|---|---|
| Max expansion rounds per run | **1** (one-shot: expanded specialists cannot trigger further expansion) |
| Max additional specialists per expansion | **2** |
| Specialist types available for expansion | any specialist from the standard roster, OR a custom specialist scoped to the new surface |
| Budget disclosure | state the expansion decision + specialist count + estimated time before dispatching |

### What does NOT trigger expansion

- A finding that's a deeper version of something another specialist already covered → fold into existing finding, don't expand
- A finding about a different part of the system than the target → note in synthesis, don't expand (wrong scope)
- A medium/low finding that's interesting but not urgent → note in synthesis, don't expand
- Curiosity about whether a pattern exists elsewhere → not confident enough, don't expand

### Expansion output

- Expanded specialists write to `{run_dir}/specialists/<name>-expanded.json`
- The dispatch manifest gets an `expansion` section recording: trigger finding, new specialist, rationale
- The synthesis includes expanded findings alongside original findings, tagged `[expanded]`

### Why one-shot, not recursive

Recursive expansion (E→F→G...) creates unbounded latency and makes the
synthesis reference a plan that drifted far from the original. One-shot
expansion catches the highest-value adjacent surface without
rabbit-holing. The /review skill's sufficiency stop is the mirror:
contract when enough evidence exists; expand when a genuinely new
HIGH/CRITICAL surface appears.

## Precision incentive (applies to every specialist dispatch)

**The over-reporting problem:** specialists generate many speculative
findings because there's no cost to being wrong — a false positive looks
thorough, while a missed finding looks like a gap. The 2026 Entelligence
benchmark shows precision ranges from 16% to 67% across AI reviewers,
meaning most findings from most tools are noise.

**Add this paragraph to every specialist dispatch prompt:**

> **Precision incentive:** Each finding that the critic marks
> `non_reproducible` reduces your specialist's quality signal. Prefer
> fewer high-confidence findings over many speculative ones. If you are
> <70% confident a finding is real, either drop it or explicitly label
> it `[speculative]` so the critic can weight it lower. The goal is
> precision, not volume. A specialist with 5 verified findings out of 7
> reported is better than one with 5 verified out of 20.

**Critic-side precision tracking:** the critic's verdicts (verified vs.
non_reproducible) are the precision signal — NOT operator acceptance
(operator trust makes acceptance unreliable). Precision per specialist =
verified / (verified + non_reproducible). Track in telemetry. After 5+
runs, specialists below 30% precision get prompt revisions in the
Phase 3b improvement loop.

## Cross-model specialist (one per run)

**The correlated-errors problem:** all parent-model specialists share
blind spots from the same model family. Research (FERZ Oct 2025, Cemri
2025) confirms that same-family N-agents barely outperform N=1 on
uncorrelated error detection. Cross-model diversity is the highest-
leverage decorrelation.

**Rule:** one specialist per /red-team run uses a cross-model model
instead of parent-model. **Do NOT use Claude or Anthropic models**
(operator constraint).

**Cross-model pool** (drawn from wiki concept `model-fleet-provider-pools.md`,
filtered for reasoning lane + tool-calling capability per
`model-tool-calling-capability-matrix.md`):

| Try order | Model | Provider | Cost | Context | Tool access | Notes |
|---|---|---|---|---|---|---|
| 1 | `glm-5-2` | GLM | Subscription | 1M | spawn_subagent OK | Best tool-calling (76.8% MCP Atlas); scarce quota |
| 2 | `go-mimo-v2-5` | OpenRouter | ~$0.005/1M | 200K | spawn_subagent OK | Verified working (this session); paid |
| 3 | `minimax-m3` | MiniMax | Subscription | 1M | chat-only | No file access — reasoning-only specialist only |
| 4 | parent-inherited | — | — | — | full | Last resort (same-model, weakest decorrelation) |

**Note:** `nvidia-nemotron-3-ultra` is excluded from this pool because it
serialization-fails on real tool tasks (verified this session + documented
in `model-tool-calling-capability-matrix.md`). It works for trivial probes
but not for the file-reading, grep-heavy work a cross-model specialist needs.

Pool selection logic: subscription-first-but-strongest (glm), then paid
(mimo), then chat-only (mmx), then parent. Free-first is sacrificed here
because the only free reasoning model with tool-call support that survived
real testing is glm via subscription. If all pool members fail, fall back
to parent-model for that specialist (disclose in synthesis).

**Which specialist gets the cross-model slot:** the one with the highest
expected value from independent verification — typically the correctness
or logic specialist, since those catch bugs most likely to share blind
spots across same-family agents.

**Implementation:** dispatch via spawn_subagent with the model slug, OR
shell out to the CLI (/agy, /codex, /mmx) if spawn_subagent doesn't
support the model. The specialist prompt is written to a file; the CLI
runs against it; output is parsed into the standard findings JSON. Tag
findings from the cross-model specialist with `[cross-model: <slug>]` in
the synthesis.

**Quota optimization (critical for agy):** agy quota is **request-based**,
not token-based. Each tool-call round-trip (file read, file write) counts
as an API request. A 3-file review via separate tool reads costs ~15% of
the 5h budget; the same review with files merged into 1 temp file costs
~1.6%. **Always merge target files into a single temp file before
dispatching to agy.** This takes effective capacity from ~5 runs/5h to
~50 runs/5h.

**Merge script (use this, don't merge manually):**

```bash
python P:/.agents/scripts/merge_files.py P:/tmp/<slug>-merged-source.py <file1> <file2> <file3>
```

Then the specialist prompt references the single merged file. This is a
mechanical operation — no LLM judgment needed. The script is at
`P:/.agents/scripts/merge_files.py` and is shared across all skills that
dispatch to CLI-based models (red-team, /tp, future consumers).

Measured quota data (2026-07-23, account a.hominidae@gmail.com, Gemini
Flash + Pro group):

| Pattern | Tool reads | Quota used (5h) | Runs per 5h |
|---|---|---|---|
| Single file (merged) | 1 | ~1.6% | ~50 |
| Multi-file (separate reads) | 3-4 | ~15.6% | ~5 |
| Light review (1 small file) | 1-2 | ~1.9% | ~40 |

Source: 3-run quota measurement experiment, session 2026-07-23.

**Reference:** `model-fleet-provider-pools.md` (fleet inventory),
`model-tool-calling-capability-matrix.md` (tool-call compatibility),
`model-pool-not-chain.md` (pool selection philosophy).

**Telemetry:** record `cross_model_specialist: <slug>` in the run's
telemetry line. After 5+ runs, compare cross-model specialist precision
vs parent-model specialist precision to validate the decorrelation claim.

## Provenance

Added 2026-07-23:
- **Expansion gate:** after the operator's /red-team review of /tp, where
  the operator asked for adaptive expansion.
- **Precision incentive + cross-model specialist:** after /www research
  on improving red-team analysis. The 2026 Entelligence benchmark (67
  bugs, 8 tools) proved precision is the dominant quality problem (F1
  scores 13-47%, precision 16-67%). Source: wiki concept
  `improving-red-team-precision-and-cross-model.md`.

Added 2026-07-24:
- **Root-cause clustering + finding classification + minimum-fix-set:** after
  the operator's red-team on model pool policy produced 62 raw findings
  that collapsed to 5 root causes. The operator asked "is this a disaster?"
  The clustering had to be done manually post-hoc by a `/tp` subagent. The
  improvements below move clustering, classification, and fix-set analysis
  into the critic/synthesis pipeline.

## Root-cause clustering (runs in critic, before verdict)

**The amplification problem:** one architectural gap (e.g., "domain table
has no enforcement mechanism") gets independently discovered by
gate-reviewer, workflow, logic, state, and performance specialists. Each
emits a BLOCK. The synthesis shows 5 BLOCKs. The operator sees
"62 findings, is this a disaster?" — when the answer is "5 root causes, 3
are implementation bugs fixable in an hour."

**Protocol (the critic MUST run this after severity-gating, before verdict):**

1. **Group findings** where multiple specialists independently identified
   the same underlying problem. Two findings share a root cause when fixing
   the root cause would resolve both (per `AGENTS.md` § "Root-cause
   clustering before fix proposal").
2. **Emit each group** as a cluster: cluster_id, root_cause (one sentence),
   findings (list of finding IDs), amplification_count (how many specialists
   found it), severity (highest among members), and the single fix that
   addresses all members.
3. **Rank clusters** by impact × amplification (a problem found by 4
   specialists with a single fix is higher priority than 2 independent
   REVISEs).
4. **Collapse severity in the count** — if 5 specialists each emit a BLOCK
   for the same root cause, the cluster is ONE BLOCK (amplified × 5), not
   five BLOCKs. The synthesis shows "BLOCK × 5 (amplified)" so the operator
   knows coverage was broad without inflating the apparent severity.
5. **Surface unclustered findings** — anything that doesn't join a cluster
   stays as a standalone finding with its original severity.

**Output format (clusters replace the flat findings list in synthesis):**

```
ROOT CAUSE CLUSTERS (ranked by impact × amplification)

Cluster RC-1 [BLOCK × 4 amplified] — Domain table has no enforcement mechanism
  Members: GATE-1, WF-1, WF-4, GATE-7
  Root cause: the domain table is documented but no skill, hook, or router
  reads it. Every skill defaults to parent Grok.
  Fix: add model= parameter to spawn_subagent calls, or build a routing hook.
  Impact: the entire policy is non-operational until this is fixed.

Cluster RC-2 [BLOCK × 3 amplified] — Telemetry has concurrency bugs
  Members: ST-1, ST-4, ST-7
  Root cause: JSONL append with no locking + bare except:pass + char-based truncation
  Fix: SQLite backend + targeted exception + line-boundary truncation
  Impact: data corruption under multi-terminal use; silent data loss

STANDALONE FINDINGS (not clustered)
  ST-5 [BLOCK] — temperature=0.1 contradicts determinism claim
  LOGIC-002 [REVISE] — M3 fallback contradicts body text
  ...
```

**Why this matters:** the operator's first question after a red-team is
"how bad is it, really?" The cluster view answers that directly: "5 root
causes, 2 are implementation bugs, 1 is a wiring gap, 2 are definitional."
The flat finding list answers "list everything wrong" — which is the
critic's job, not the operator's first need.

## Finding classification (tags every cluster or standalone finding)

After clustering, tag each cluster/finding with exactly one of:

| Class | Meaning | Operator action |
|---|---|---|
| `architectural` | The design itself is wrong — the pattern won't work regardless of implementation quality | Redesign needed; may block ship |
| `implementation` | The design is sound but the code has bugs | Fix the code; does not block the design |
| `definitional` | A term, threshold, or gate is undefined (e.g., "quality floor" with no definition) | Define the term or downgrade the gate; documentation work |
| `deferrable` | Real finding but safe to defer — won't affect correctness or safety in the near term | Backlog item; track but don't block |

**How the critic assigns classes:**
- If the finding says "this approach/pattern/architecture is flawed" → `architectural`
- If the finding says "this code path has a bug/corruption/race/error" → `implementation`
- If the finding says "this term is undefined / this threshold is unjustified / this gate has no measurement" → `definitional`
- If the finding is real but the impact is future-scale (not blocking current ship) → `deferrable`

**Output:** the synthesis header shows class counts:

```
CLASSIFICATION SUMMARY
  Architectural:  0   (no design-level flaws found)
  Implementation: 4   (bugs in the code — fixable in hours)
  Definitional:   8   (undefined terms — documentation work)
  Deferrable:     3   (real but safe to defer)
  Total clusters: 5   (from 62 raw findings across 6 specialists)
```

This directly answers "is this a disaster?" If architectural = 0, the
design is sound. If implementation = 4, it's a few hours of fixes. The
operator triages by class, not by raw finding count.

## Minimum fix-set (synthesis output, replaces flat "recommended next steps")

After clustering and classification, the synthesis emits a **prioritized
minimum fix-set**: the smallest set of changes that addresses the highest-
impact clusters. This is the 20/80 analysis the operator needs — not "fix
all 62 findings" but "these 3 changes collapse 12 findings."

**Format:**

```
MINIMUM FIX-SET (prioritized — do these first)

1. [implementation, 15 min] Fix extract.py temperature to 0.0
   Addresses: ST-5 (determinism contradiction)
   Impact: makes the wiki's determinism claim true
   Why first: 1-line fix, eliminates 1 BLOCK immediately

2. [implementation, 10 min] Add model= to /check spawn block
   Addresses: RC-1 cluster (domain table unenforced)
   Impact: proof-of-concept that the policy can fire
   Why first: highest-amplification cluster, simplest fix

3. [implementation, 20 min] Fix telemetry exception handling + truncation
   Addresses: RC-2 partial (ST-4, ST-7)
   Impact: prevents silent data loss and syntax corruption
   Why first: concurrency bugs compound over time

DEFERRED (do NOT fix now — track in backlog)
- LOGIC-001 to LOGIC-018 (most): definitional; policy is internally consistent enough
- ST-6: telemetry growth — 2326 bytes today; fix at 10MB
- PERF-001: benchmark sequential — 5 min acceptable
```

**The rule:** the minimum fix-set addresses all clusters tagged
`architectural` or `implementation` with BLOCK severity, plus the highest-
amplification REVISE clusters. It explicitly lists what NOT to fix
(deferrable and definitional findings that don't block ship).

**Why this replaces the old "recommended next steps":** the old format
listed every real step without priority or triage. The operator had to
manually decide "which of these 15 steps do I actually do first?" The
minimum fix-set answers that directly: "these 3, in this order, for these
reasons; defer the rest."
