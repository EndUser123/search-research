---
title: "in claude code, what's the optimal way to do discovery so that the llm knows how to modify code to add and remove featur"
date: "2026-07-14"
mode: "COPILOT"
uuid: "4664398a-9e03-44eb-a07f-7b2e53133694"
entry_count: 3
---

## Human

in claude code, what's the optimal way to do discovery so that the llm knows how to modify code to add and remove features safely, not leave hanging refernces, make sure there are no dead code paths, etc.  I don't know what I don't know, so please act as a thought partner and include what should be included.

## Assistant

Yes: the optimal pattern is to make discovery a **first-class phase** with explicit artifacts, then gate editing on evidence from that phase rather than hoping the model “looks around enough.” In Claude Code, that means combining a discovery contract, structural repo mapping, impact analysis, and blocking hooks so edits cannot proceed until the model has shown what is live, what depends on it, and how safety will be verified.[1][2][3][4]

## Core model

The main failure mode is not “bad coding” but incomplete situational awareness: the model edits the local file it sees, while the real risk lives in unseen callers, registries, configs, tests, feature flags, schemas, and generated artifacts. Your own prior work already points at the right direction: move from advisory text to enforced, evidence-first gates, because hooks mechanically shape behavior while prompts and CLAUDE.md are often ignored.[2]

A good mental model is: **discovery produces a change graph**. Before modifying code, Claude should know at least: entrypoints, callers, callees, registrations, tests, configs, docs/contracts, and runtime/live status of the target area; otherwise it is making a local patch in a global system. Structural tools such as ast-grep and Tree-sitter are well-suited here because they search code by syntax structure and support code navigation/static analysis beyond plain text grep.[5][6][7]

## Discovery artifacts

What should be included in discovery before any non-trivial add/remove/refactor:

- Change intent: add feature, remove feature, replace path, retire dead code, rename contract.
- System surface: files likely involved, entrypoints, exposed APIs/CLI commands/routes/events/jobs/hooks.
- Dependency map: inbound references, outbound references, dynamic registrations, config wiring, tests.
- Safety invariants: what must still work after change, what must disappear after removal.
- Verification plan: exact searches/tests/build checks to run before declaring completion.[8][9][3]

The artifact I would require from Claude before editing is a short **impact statement**:
- Target objects to change.
- Inbound dependents.
- Outbound dependents.
- Non-obvious wiring, registries, schemas, env vars, docs, prompts, hooks.
- Risk class: local / cross-module / cross-boundary.
- Proposed verification commands.[10][1]

That is the key shift: do not ask Claude to “be careful.” Require it to present the map it will use to be careful.[2][8]

## Discovery stack

For practical discovery, use layers rather than one tool.

| Layer | Purpose | Best tool |
|---|---|---|
| File inventory | Find candidate files, modules, tests, configs | `fd`, `rg` [10] |
| Text references | Fast broad recall, names/strings/flags/docs | `rg` [10] |
| Structural references | Find imports, calls, handlers, exports, object members by syntax | ast-grep [7][11] |
| Code navigation graph | Parse symbols, scopes, query syntax trees | Tree-sitter [6][5] |
| Runtime truth | What is actually executed/live vs merely present | your live-set / runtime ledger approach [1] |
| Enforcement | Block edits/claims until discovery evidence exists | Claude Code hooks [3][4][2] |

Why this matters: `rg` tells you “where the string appears,” but removal safety often depends on structural matches such as imported-but-renamed symbols, route registrations, event handlers, subclass overrides, decorators, or config-driven wiring; that is where ast-grep and Tree-sitter close gaps plain text search misses.[6][7][5]

## Safe add/remove flow

For adding a feature, discovery should answer:
1. Where is the nearest existing pattern already solving part of this?
2. What contract does the new feature extend: route, command, schema, UI state, event, job?
3. What tests and docs prove the new path is now reachable and owned?[12][13]

For removing a feature, discovery should answer:
1. What makes this feature reachable today: route, menu item, command, registry, flag, job, cron, prompt, import?
2. What inbound references remain after removal?
3. What fallback or replacement path must be updated?
4. What proof shows it is truly dead afterward: no references, no registration, no runtime hits, no tests expecting it?[9][1]

This is where many LLM workflows fail: “remove feature” is usually a **distributed change**, not a delete. It often needs edits in code, tests, navigation, config, docs, analytics, permissions, prompts, and migration logic.[12][1]

## Hooked enforcement

Claude Code supports hooks that run at lifecycle points, including PreToolUse, PostToolUse, and Stop, which makes it suitable for deterministic gating rather than advisory reminders.[3][4]

Given your preferences, I would enforce discovery with hooks roughly like this:

- PreToolUse on `Edit|Write|MultiEdit`: block unless a fresh discovery artifact exists for the touched file set. [3][2]
- PostToolUse on file edits: trigger structural re-scan of affected symbols/files and update an impact ledger.[4][7]
- Stop hook: block “done/safe/removed/fixed” claims unless tests/searches/runtime evidence are attached, matching your evidence-first pattern.[14][8][9]

The important detail is freshness. Discovery should be invalidated when:
- new files are touched,
- scope expands,
- target symbols change,
- or the model proposes a cross-boundary edit not covered by the original map.

That prevents the common failure where the agent did one good scan, then drifted into adjacent areas with stale assumptions.[8][10]

## What to require

A strong minimum discovery checklist for Claude Code:

- Read nearest architecture docs/spec/task file if they exist.[12]
- Find target symbol definitions and exports.
- Find all inbound references.
- Find all outbound references.
- Find registrations: routes, commands, event subscriptions, DI containers, plugin manifests, cron/jobs, feature flags.
- Find tests covering current behavior.
- Find docs/prompts/config mentioning the feature.
- Classify whether the code is statically reachable, dynamically wired, or runtime-proven live.[1]

Then require one of these dispositions before edit:
- **Additive-local**: safe to proceed.
- **Cross-cutting**: must update multiple surfaces.
- **Removal-risky**: requires retirement plan.
- **Unknown wiring**: stop and discover more.

That last category is crucial. The model should be allowed to say “unknown wiring” and halt; otherwise it will often guess.[15][1]

## Dead code and hanging references

To avoid hanging references and false removals, use three separate checks, not one:

- **Reference check**: no remaining imports/calls/usages/strings that indicate real dependency. `rg` plus ast-grep.[7][10]
- **Wiring check**: no registries/routes/configs/prompts/menus/tests still expose the feature.[1][12]
- **Runtime/live check**: the code is not in the live set, or is explicitly being retired. Your earlier “live set from runtime evidence” idea is the strongest long-term answer because it distinguishes merely-present code from executed code.[1]

That gives you a much better taxonomy:
- Unreferenced but still registered.
- Unregistered but still tested.
- Untested but runtime-live.
- Textually referenced only in docs.
- Truly dead.

Those distinctions are where safe cleanup gets won or lost.[9][1]

## Discovery prompt contract

A practical contract to give Claude Code before implementation:

1. Discover before editing.
2. Produce an impact map for the requested change.
3. Separate static evidence from runtime evidence.
4. State unknowns explicitly.
5. Do not remove code until references, wiring, and verification plan are accounted for.
6. Use atomic edits, not write-delete churn.[8]

A compact template:

- Goal.
- Existing implementation pattern reused.
- Files inspected.
- Inbound references.
- Outbound references.
- Registrations/wiring.
- Tests/docs/config touched.
- Unknowns.
- Planned edits.
- Verification commands.

That is small enough to be practical and rich enough to prevent most “messy patch” failures.[10][12]

## Long-term architecture

The optimal long-term design is not just “better search,” but a lightweight **repo knowledge layer** that Claude updates as it works. Your prior live-set direction is the most valuable piece here: maintain a machine-readable ledger of what is proven live, what owns it, and what references it, then use hooks to require consultation/update of that ledger before risky edits.[1]

The lean version would include:
- Symbol/reference index from static scans.
- Registry/entrypoint inventory.
- Runtime live ledger from tests, executions, logs, or traced dispatch.
- Change-impact record per task.
- Stop-gate verification record.[8][1]

FACT: Claude Code hooks are intended for automatic actions at lifecycle points, including blocking before tools execute, so this enforcement-oriented design fits the product’s mechanism well.[3][4]

Confidence: **high** on the workflow shape, **medium** on exact implementation details because the best hooks depend on your repo mix and how much dynamic wiring you have.[4][3][1]

Concrete next step: pilot one blocking discovery gate for `Edit|Write|MultiEdit` that requires an impact statement plus evidence of `rg`/structural search over inbound references and registrations before allowing cross-file edits. Then add a second Stop gate that blocks “safe/complete/removed” claims without verification evidence. [3][2][8]

Would you like me to turn this into a concrete Claude Code implementation package: hook design, discovery schema, and a minimal prompt/skill contract tuned for Python + TypeScript repos?

## Human

what popular supported repos have ideas that enhance your propsoal?  graphify?

## Assistant

Yes — **Graphify is directly relevant**, and it strengthens the proposal in a few important ways, but it is not the whole solution by itself. It is best used as the repo discovery/indexing layer, while hooks and verification gates remain the enforcement layer that decides whether Claude can safely modify code or claim completion.[1][2][3]

## Best-fit repos

The strongest repo ideas that enhance this proposal are:

- **Graphify** for repository-wide knowledge graphing, path queries, community detection, and cross-file/context discovery. It builds a queryable graph from code and docs, uses Tree-sitter for local AST-based extraction, and exposes commands like `query`, `path`, and `explain`, which map well to “what else does this touch?” discovery.[1]
- **ast-grep** for structural search, linting, and rewrites. It is ideal for precise inbound/outbound reference discovery and rule-based structural checks, especially where `rg` is too shallow. 
- **Sourcegraph-style ideas** for structural search and cross-repository code navigation. Even if you do not adopt Sourcegraph itself, the ideas worth copying are indexed structural search and compiler-accurate cross-reference navigation for “who calls this / where is this defined / what breaks if this changes?” workflows.[4][5][6]

If your question is “what popular supported repos add ideas I should steal?”, Graphify is the most directly aligned with Claude Code workflow shaping, while ast-grep contributes the best low-friction structural search primitives, and Sourcegraph contributes the best large-scale code-intelligence mental model.[1][4]

## What Graphify adds

Graphify’s useful ideas are not just “make a graph.” The more important pieces are:

- It treats the codebase as a **queryable graph**, not a flat directory, so the model can ask path and neighborhood questions instead of re-reading raw files.[1]
- It labels edges with confidence such as `EXTRACTED` versus `INFERRED`, which is a strong pattern for epistemic hygiene because it distinguishes directly observed relations from resolved/inferred ones. That fits your evidence-first preference very well.[1]
- It supports project-scoped installation for assistants including Claude Code and writes assistant-facing configuration so the graph becomes part of normal workflow rather than a one-off report.[7]
- It is local-first for code extraction via Tree-sitter AST, which is useful when you want deterministic structure without paying token cost for raw code ingestion.[1]

That said, Graphify mainly improves **discovery and retrieval**. It does not, by itself, guarantee safe edits, detect all dead code correctly, or block unjustified “done” claims; that still requires hooks, policies, and verification passes.[2][8]

## Where Graphify fits

The clean architecture is:

1. **Graph/index layer**: Graphify builds a repo graph and answers “what is connected?”[1]
2. **Structural search layer**: ast-grep verifies concrete usages, definitions, registrations, and rewrite candidates. 
3. **Runtime/live layer**: your live-set or execution ledger answers “what is actually exercised?” because static graphs alone cannot prove code is dead.[9]
4. **Enforcement layer**: Claude Code hooks block edits or completion claims until required discovery and verification evidence exists.[3][10][2]

That is why my answer is “yes, Graphify — but as one layer.” If you rely on Graphify alone, you still risk deleting code that is only dynamically wired, feature-flagged, loaded by convention, or live only under runtime paths the graph does not prove.[9]

## Ideas worth copying

Even if you do not adopt these repos wholesale, these are the ideas to steal:

| Repo / system | Idea worth copying | Why it helps |
|---|---|---|
| Graphify | Queryable repo graph; shortest-path and explain commands; `EXTRACTED` vs `INFERRED` edges [1] | Better discovery and uncertainty tracking before edits. |
| Graphify | Project-scoped assistant install plus hooks/instruction files  | Makes discovery part of the agent’s default workflow rather than optional. |
| ast-grep | AST-based structural search and YAML rules  | Precise impact analysis and safer reference checks than plain grep. |
| Sourcegraph | Indexed structural search and cross-repo code navigation [5][6] | Strong mental model for “who uses this?” and “what else must change?” at scale. |
| Your live-set approach | Runtime-proven liveness ledger [9] | Separates “present in repo” from “actually live,” which is essential for dead-code claims. |

The `EXTRACTED`/`INFERRED` distinction is especially strong. I would absolutely import that idea into your discovery artifact so Claude must label each dependency or impact claim as one of:
- directly observed,
- structurally inferred,
- runtime-proven,
- or unknown.[9][1]

## Recommendation

My recommendation is **not** “install Graphify and call it done.” The better move is:

- Use Graphify for broad repo topology and question answering.[1]
- Use ast-grep for concrete structural proof on the exact symbols/files being changed. 
- Keep your hook-based blocking gates for pre-edit discovery and post-edit verification, because advisory mechanisms are too weak for the safety level you want.[2][3]
- Add a live/runtime ledger for any repo with dynamic wiring, plugins, registries, feature flags, or indirect dispatch.[9]

Confidence: **high** that Graphify improves the proposal; **medium-high** that it is the best off-the-shelf discovery complement for Claude Code specifically; **high** that it still needs enforcement and runtime truth layers around it.[1][9]

A concrete next step would be to define a discovery contract that uses:
- Graphify for `path/query/explain`,
- ast-grep for structural verification,
- and hooks that reject edits unless both have been consulted for cross-file work.[2]

Would you like a concrete “best-of-breed stack” next — e.g. Graphify vs Sourcegraph vs ast-grep vs your own live-set, with what each should own in the pipeline?

## Human

yes please

## Assistant

Best-of-breed stack: use **Graphify for repo topology**, **ast-grep for structural proof**, **Sourcegraph-style code nav/search for scale or multi-repo use**, and **your own live-set + hooks for actual safety enforcement**. The winning pattern is not choosing one; it is assigning each tool a narrow job and refusing to let any one layer pretend it solved discovery, liveness, and verification by itself.[1][2][3][4][5]

## Recommended ownership

Here is the clean ownership model I’d use for Claude Code-driven modification safety:

| Layer | Best tool | Owns | Should not own |
|---|---|---|---|
| Repo topology | Graphify | Cross-file map, paths, concepts, docs-to-code relationships, “what is connected?” [2][6] | Final proof of safety or dead-code status |
| Structural proof | ast-grep | Definitions, usages, imports, registrations, rewrite candidates, policy rules [4][7] | Runtime liveness |
| Code intelligence at scale | Sourcegraph or Sourcegraph-style indexing | Cross-repo references, indexed search, symbol navigation at large scale [3][8][9] | Claude-specific enforcement |
| Runtime truth | Your live-set / execution ledger | “Is it actually exercised?” and “is this code live?” [5] | Static topology discovery |
| Enforcement | Claude Code hooks | Block edits/claims until required evidence exists [10][11][1] | Discovery itself |

This split matters because Graphify is excellent at compressing the repo into a graph the agent can query, but even Graphify advocates still position grep as the source of truth for implementation details, which is the right instinct.[2][12]

## Graphify

Graphify is the best fit for the **discovery front-end** in your workflow because it turns code, docs, and other project material into a queryable knowledge graph and exposes commands such as query, path, and explain. It combines Tree-sitter static analysis with LLM-driven semantic extraction, which makes it much better than raw grep for “show me the shortest path from feature X to subsystem Y” or “explain this component in project context.”[6][13][2]

Its best ideas for your design are:
- shortest-path exploration between two concepts or files,
- graph queries instead of repeated file rescans,
- update-only changed files,
- and confidence distinctions such as extracted versus inferred relationships.[13][2]

Where I would limit it: Graphify is a **structural index and explainer**, not a proof engine. Its semantic edges are useful for narrowing scope, but they should not be enough to authorize deletion or completion claims without structural and runtime checks.[12][5][2]

## ast-grep

ast-grep is the best fit for **pre-edit proof** because it searches code by AST structure and supports linting, rewriting, and YAML-configured rules. That makes it excellent for exact checks like “find all callsites of this method,” “find route registrations matching this handler,” or “reject introducing a maintained helper without test ownership metadata.”[4][7]

This is the layer I would trust most for:
- inbound reference checks,
- outbound reference checks,
- registration pattern checks,
- policy enforcement rules,
- and targeted rewrite candidates.[7][4]

In your system, ast-grep should be the thing the hook consults before allowing risky edits. It is deterministic enough to be enforcement-friendly, unlike soft semantic retrieval.[1][4]

## Sourcegraph

Sourcegraph is most valuable as a **mental model and scale pattern**, especially if you work across many repos or want compiler-like navigation. Its key strengths are structural search, indexed multi-repo search, and precise cross-reference/code-navigation via its indexing stack.[3][8][14]

If you are operating mostly inside a single repo in Claude Code, I would not make Sourcegraph the center of the workflow. But I would copy these ideas from it:
- pre-indexing instead of repeated ad hoc search,
- references/definitions as first-class navigation,
- structural search for syntax-aware matching,
- and cross-repo dependency awareness where boundaries matter.[8][9][3]

So for you, Sourcegraph is probably more “architecture inspiration or optional enterprise-scale layer” than “core daily enforcement primitive.”[3][8]

## Live-set and hooks

This is the part no off-the-shelf repo fully replaces. Your live-set idea is what closes the biggest safety gap: static tools can show that code is referenced, but they do not reliably prove whether it is **actually live**, especially under plugin loading, registries, feature flags, reflection, config-driven dispatch, or runtime-only paths.[5]

And your hook preference is exactly right for this use case: advisory instructions are too weak, while blocking/gating hooks can mechanically require discovery artifacts and verification evidence before edits or completion claims proceed. Your own history already shows that this is the layer you trust, and for good reason.[15][1]

So I would treat:
- Graphify as “map,”
- ast-grep as “proof,”
- live-set as “truth,”
- hooks as “judge.”[2][4][5][1]

## Pipeline design

The optimal pipeline for safe feature add/remove in Claude Code looks like this:

1. **Graphify first** for scope shaping: query/path/explain to identify likely impact surface.[6][2]
2. **ast-grep second** for exact structural evidence: refs, defs, registrations, handlers, tests, flags.[4][7]
3. **Live-set check third** for liveness: runtime-proven, recently executed, test-covered, or unknown.[5]
4. **Hook gate** decides whether edit is allowed, whether more discovery is required, or whether removal must be downgraded to “candidate retirement.”[10][1]
5. **Post-edit re-scan** with ast-grep plus tests/build to confirm no hanging references or broken paths remain.[16][7]

That pipeline is strong because each step reduces a different uncertainty class rather than duplicating the same kind of search.[2][4][5]

## What I’d actually deploy

If I had to choose the highest-ROI version for your workflow:

- **Must have**
  - Graphify for fast repo topology/context.[2]
  - ast-grep for structural verification and policy rules.[7][4]
  - Blocking Claude Code hooks for pre-edit and stop-gate enforcement.[10][1]

- **Should have**
  - Lightweight live-set ledger for runtime-proven liveness.[5]
  - Cached impact artifact per task, so the model does not repeat expensive discovery unnecessarily.

- **Optional**
  - Sourcegraph, if you are spanning many repos or want stronger global code intel.[8][3]

If you want the shortest answer: **Graphify + ast-grep + hooks** is the best practical core, and **live-set** is the thing that upgrades it from “good static discovery” to “actually safe removal/refactor architecture.”[1][4][5][2]

## Concrete recommendation

My recommendation for ownership in your stack:

- Graphify owns “what might this touch?”[6][2]
- ast-grep owns “show me exactly where it is defined/used/wired.”[4][7]
- your runtime ledger owns “is this really live?”[5]
- hooks own “may Claude proceed, and may it claim success?”[10][1]

Confidence: **high** on this division of responsibilities; **medium** on whether Sourcegraph is worth it for your exact environment, since that depends on how multi-repo and language-diverse your working set is.[3][8]

The next useful step is to turn this into a concrete policy: which discovery evidence is required for add, remove, rename, refactor, and delete operations in Claude Code.
