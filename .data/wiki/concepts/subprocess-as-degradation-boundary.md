---
title: "Subprocess as degradation boundary — runtime failure degrades, import-time failure breaks"
created: 2026-07-25
source: session-20260725 (/tp critique of crawl4ai qmd integration)
tags: [architecture, coupling, subprocess, degradation, import-time, runtime-failure, skill-design, durability]
summary: >
  When wrapping an external library whose long-term viability is uncertain, calling it via
  subprocess (wrong-on-syntax, right-on-architecture) preserves a property that direct import
  (right-on-syntax, wrong-on-architecture) destroys: the consumer degrades at runtime with a
  clear error rather than breaking at import time. Subprocess is a degradation boundary — the
  consumer still loads, the failure is localized, and the external dependency is replaceable
  without touching every consumer. The crawl4ai-qmd integration failure (2026-07-25) is the
  reference case: a shim module (wiki_search.py) recovers both properties — clean syntax AND
  the degradation boundary — by isolating the external API behind a single import point.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - session-20260725 (/tp critique subagent finding, go-mimo-v2-5, 40 tool calls)
relations:
  - target: wiki/concepts/qmd-patch-durability-strategy.md
    type: refines
  - target: wiki/concepts/raising-coding-best-practices-in-ai-agents.md
    type: complements
  - target: wiki/concepts/adhd-parallel-frame-divergent-ideation-integration.md
    type: related
---

# Subprocess as degradation boundary

## Decision context

**Why this knowledge was needed:** during a `/tp` critique of the crawl4ai-qmd integration
problems (session 20260725), the fresh subagent identified an architectural principle that
the orchestrator's `/why` analysis had missed. The orchestrator recommended "replace subprocess
calls with direct Python API import" (`from qmd import connect`) to fix the broken qmd CLI
syntax. The fresh subagent's second-order analysis caught the hidden cost: direct import
tightens coupling at exactly the moment when qmd's long-term viability is in question
(upstream dead ~3 months, patch count growing, exit criterion arguably triggered). The
principle that emerged — subprocess as degradation boundary — reframes "ugly subprocess calls"
as a deliberate architectural choice when the wrapped dependency might be replaced.

## The principle

When consumer code wraps an external library, the call mechanism determines the failure mode:

| Call mechanism | Failure mode | Coupling | Replaceability |
|---|---|---|---|
| **Direct import** (`from lib import api`) | **Import-time failure** — the consumer module won't load if `lib` is absent/incompatible | Tight — every consumer is a blocker for replacing `lib` | Low — replacing `lib` requires touching every consumer |
| **Subprocess** (`subprocess.run(["lib", ...])`) | **Runtime failure** — the consumer loads fine; the specific call fails with a clear error when invoked | Loose — the consumer only knows the CLI contract | High — replacing `lib` requires changing only the command string |
| **Shim module** (`from shim import api`) | **Runtime failure** at the shim boundary, or **lazy import-time** if the shim lazy-imports | Medium — every consumer imports the shim, not the library | High — replacing `lib` requires changing only the shim |

Subprocess preserves a property that direct import destroys: **degradability**. The consumer
still loads, the failure is localized to the specific call, and the error is actionable ("qmd
not found" vs. ImportError traceback at module load).

## Why subprocess is "right-on-architecture, wrong-on-syntax"

The crawl4ai skill (ported from `search-research/core/backends/local/qmd_wiki_backend.py`)
used subprocess to call qmd. The syntax was wrong — `qmd update` doesn't exist, `qmd search`
signature mismatched — but the architectural instinct was right. The plugin's docstring
documents why: *"qmd is often installed in the user-site (global) Python, not the plugin venv,
so `[sys.executable, '-m', 'qmd']` fails with 'No module named qmd'."* The subprocess pattern
was a deliberate workaround for an environment-isolation constraint, and it had the side effect
of preserving loose coupling.

The port to `~/.grok/skills/crawl4ai/` inherited the subprocess pattern without re-evaluating
the context. In the new context (global Python, where qmd IS importable), the environment
justification no longer applies — but the loose-coupling property still does. The /why
recommendation (direct import) would have fixed the syntax while destroying the coupling
property.

## The shim solution (recovers both properties)

A shim module (`P:/.agents/scripts/wiki_search.py`) provides the clean syntax of direct import
while preserving the degradation boundary of subprocess:

```python
# consumer (e.g., crawl4ai):
from wiki_search import WikiSearch   # imports fine even if qmd absent
ws = WikiSearch("wiki")
ws.search(...)   # fails HERE with clear error if qmd not installed
```

The shim lazy-imports qmd inside `_connect()`, so:
- Consumer modules load without qmd installed (degradable)
- The qmd API surface is isolated in ONE file (replaceable)
- If qmd is replaced (vendored / raw sqlite-fts5 / in-house), only the shim changes

This is the architectural pattern for wrapping any uncertain-viability dependency.

## When subprocess-as-degradation-boundary applies

Apply this principle when ANY of:
- The external library's upstream is dead or uncertain
- The library is pinned at an old version with surgical patches (the qmd case)
- The library might be replaced (vendor / fork / swap / in-house rewrite)
- The consumer runs in multiple environments (venv, global, container) where the library may or may not be installed
- The cost of every consumer breaking at import time exceeds the cost of one indirection layer

## When it does NOT apply

Skip the shim when ALL of:
- The library has a healthy upstream and stable API
- The library is installed in every environment the consumer runs in
- Direct import is idiomatic for the language/framework (e.g., a React component importing a util)
- The coupling cost of direct import is lower than the indirection cost of a shim

Most internal workspace code falls in this second category. The shim is for the boundary
between stable internal code and uncertain external dependencies.

## What this means for our workspace

- **`wiki_search.py` shim** is the canonical implementation of this pattern for qmd access.
  Every consumer of qmd (crawl4ai, future skills, any plugin that needs wiki search) should
  import the shim, not qmd directly. This preserves the qmd-replacement boundary regardless
  of whether the dedicated qmd-viability session (handoff `qmd-viability-evaluation-20260725`)
  decides to keep, vendor, or replace qmd.
- **Audit other uncertain dependencies** — are there other external libraries we wrap that
  would benefit from the shim pattern? Candidates: crawl4ai itself (Python 3.14 lxml blocker),
  sentence-transformers (heavy model load, version drift), any MCP server wrapper. This is
  a separate audit, not a blocking follow-up.
- **Skill porting checklist** — when porting a skill from one context to another (e.g.,
  search-research plugin → `~/.grok/skills/`), re-evaluate inherited patterns against the new
  context. The crawl4ai port inherited subprocess for venv-isolation reasons that no longer
  applied; the syntax was wrong and the architectural property was preserved by accident.

## Falsifier

This principle is wrong if, within 12 months:
- **The shim accumulates more complexity than direct import would have** (the indirection cost
  exceeds the coupling cost). Mitigation: if `wiki_search.py` grows past ~300 LOC or adds
  features that aren't "wrap qmd," split it.
- **qmd is never actually replaced** and the shim was unnecessary ceremony. Counter: the shim
  costs ~150 LOC and isolates 2+ consumers; even if qmd is never replaced, the isolation makes
  the qmd API drift failure class structurally impossible to recur.
- **Direct import turns out to be more degradable than claimed** (e.g., Python's import system
  handles missing modules gracefully enough). Counter: ImportError at module load prevents the
  *entire consumer module* from loading; subprocess failure only prevents the *specific call*.
  These are different failure modes and the principle holds.

## Receipts

- **`/tp` critique subagent finding** — go-mimo-v2-5, session 019f9bfe, 2026-07-25, 40 tool
  calls. The "subprocess-as-degradation-boundary" insight was the subagent's core domain 2
  (optimal long-term vs simplicity) finding: "Direct import tightens the coupling surface at
  exactly the moment when the substrate's long-term viability is in question."
- **`qmd_wiki_backend.py:40-49`** — the plugin docstring documenting the venv-isolation
  rationale for subprocess.
- **`P:/.agents/scripts/wiki_search.py`** — the shim implementation (this session, verified
  via smoke test).
- **`~/.grok/skills/crawl4ai/crawl_to_qmd.py` lines 100-115, 524-545** — the shim integration
  replacing the broken subprocess calls (commit `b8d7dee`).

## Sources

- [[qmd-patch-durability-strategy]] — the existing decision to pin-and-patch qmd; this concept
  refines it by adding the consumer-side coupling boundary that the patch strategy didn't
  address.
- [[raising-coding-best-practices-in-ai-agents]] — the dismissal-bias rule; the /why analysis
  initially dismissed the subprocess pattern as "just wrong" without inventorying its
  architectural properties. The fresh /tp lens caught what the same-lens /why missed.
- [[adhd-parallel-frame-divergent-ideation-integration]] — the /tp critique that surfaced this
  finding was itself the session's first use of the two-lens architecture on a coupling
  question; the fresh lens is what caught the second-order coupling cost.
