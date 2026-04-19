<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# For claude code on Windows 11, I discovered that we have single file tool review skills and technology, but it doesn't do cross-file checking.  What do you think is an optimal solution to ensure we get cross-file checking?

The optimal solution is to introduce a *review bundle* pattern: a single orchestrator skill that (a) selects a coherent multi-file scope, (b) materializes that scope into a temporary “bundle” structure, and (c) runs your existing single-file review tools against that bundle with explicit cross-file checks layered on top.[^1_1]

## Core idea

You keep your current single-file review skills as-is, but wrap them in a higher-level skill that always operates on a set of related files (module, package, or feature) instead of one file at a time.[^1_1]
That bundle skill is responsible for discovering, normalizing, and exporting enough context that cross-file issues (imports, doc/code mismatch, path traversal, etc.) become visible in a single prompt and/or tool call.[^1_1]

## Concrete design

Inside your existing ecosystem (P:/.claude/), you add something like `/review-bundle`:

- Phase 1 – **Scope resolver**: Given a target file or directory, glob the module/package: sibling modules, `__init__.py`, tests, and docs that reference that path.[^1_1]
- Phase 2 – **Bundle builder**:
    - Build a JSON index (bundle_manifest.json) listing files, import graph, and key symbols per file.
    - Optionally write a synthetic “bundle summary” file (imports, public API, tests mapped to sources).[^1_1]
- Phase 3 – **Tool fan-out**: Invoke your existing single-file tools (`/q`, `/r`, `/adversarial-*`, `/test-analyzer`, etc.) against each file, but pass the bundle manifest/summary as shared context so they can reason across boundaries.[^1_1]
- Phase 4 – **Cross-file analyzers**: Add a tiny set of focused analyzers that *only* read the manifest plus the bundle files:
    - Import resolver: check every import target exists and matches real paths, flag sys.path hacks, circular imports, and inconsistent package layouts.[^1_1]
    - Doc consistency checker: compare docstrings/README claims to actual signatures and behaviors across files.[^1_1]
    - Security/path traversal checker: central scan for user-input → filesystem joins, looking for `..` use and similar patterns across the bundle.[^1_1]
- Phase 5 – **Aggregation \& gating**: Aggregate findings, apply your existing quality gate (e.g., 80+ confidence threshold), and emit a single structured report back to the user.[^1_1]

This leverage your current multi-agent / multi-phase patterns (e.g., `/q`’s ScopeResolver, QuickCollectors, IssueNormalizer, etc.), but makes “multi-file” an explicit first-class concern at the skill level rather than hoping each file review will infer cross-file issues.[^1_1]

## Implementation notes tailored to your setup

- Put the orchestrator skill in `P:/.claude/skills/review-bundle/` with a SKILL.md that clearly declares it as the canonical entry point for cross-file review.
- Reuse your existing **ScopeResolver + QuickCollectors** concepts from `/q` so you don’t re-invent discovery logic; teach ScopeResolver to operate at a package/feature level instead of pure single-file.[^1_1]
- Have the bundle manifest written into `P:/.claude/state/skill_execution_{terminal_id}/review_bundle/…` so any sub-skill or hook in that terminal can load it cheaply without re-scanning the filesystem.[^1_1]
- Use your current PreToolUse gates (`path_validator`, `python_import_gate`, `dependency_verification_gate`) to guard bundle discovery and the cross-file analyzers, but keep them fail-open for quality checks and fail-closed only for dangerous operations.[^1_1]


## Why this is “optimal” for you

- It fits your existing architecture: skills orchestrate, hooks validate, agents do parallel analysis, tools read/grep/glob/bash; you’re just adding a new “bundle” orchestration layer and a couple of focused analyzers.[^1_1]
- It avoids duplicating single-file logic; you reuse `/q`, `/r`, `/adversarial-*`, `/test-analyzer`, etc., and only add thin glue for cross-file relationships and manifest building.[^1_1]
- It generalizes: The same bundle skill can run before media generation, packaging, or CI-like checks, and can be extended later with language-specific analyzers (Python/TypeScript) without changing the call site.

Would you rather target *Python packages* or *feature directories* (mixed Python + TypeScript + docs) as the primary “bundle” unit for the first version?

<div align="center">⁂</div>

[^1_1]: review_bundle_code_review_ecosystem_2026-03-10.md


---

# Is there refactoring we can do to make the optimal solution more efficient, effective, elegant?  I don't care about transition effort, and I'm ok with removing redundant skills/code/etc after.

Yes. You can collapse this into a smaller, more **elegant** core by refactoring around “analysis units” and a single meta-orchestrator, then deleting a lot of redundant skills.[^2_1]

## 1. Introduce “AnalysisUnit” as the primitive

Right now the primitive is “skill that takes a path,” which leads to 150+ skills, each deciding scope and depth themselves.[^2_1]
Refactor to a single low-level concept: an AnalysisUnit = {scope, files, manifest, questions}, and let everything operate on that.

- New tiny library under `P:/.claude/lib/analysis_unit/` (not a skill, just Python) that can: discover files for a package/feature, build the manifest (imports, symbols, tests, docs), and persist it in `P:/.claude/state/analysis_units/{terminal_id}/…`.[^2_1]
- All higher-level capabilities (security, performance, docs, spec-compliance, etc.) take an AnalysisUnit ID instead of a raw path, so cross-file is automatic and consistent.

This centralizes scope resolution and cross-file graph building into one place and eliminates per-skill ad‑hoc discovery logic.[^2_1]

## 2. Replace many skills with one “meta-review” skill

Instead of `/q`, `/r`, `/adversarial-*`, `/test-analyzer`, `/code-*` each doing their own orchestration, introduce one `/meta-review` that:

- Accepts: `{target_path, modes[]}` where modes are semantic: `["security","imports","docs","performance","testing","architecture"]` (not separate skills).
- Internally:

1. Creates or loads an AnalysisUnit for `target_path`.
2. Spawns the relevant adversarial/agent perspectives in parallel, all reading the same manifest and file set.[^2_1]
3. Runs a single normalization + quality-gate pass and emits a unified report.

Then you can remove entire skills that are just thin wrappers around “security review of this path,” “performance review of this path,” etc., and keep only one meta-skill with flags.[^2_1]

Example:

- Delete `/adversarial-security`, `/adversarial-performance`, `/adversarial-quality`, etc. as *entry-point* skills.
- Keep the corresponding agents, but they now only ever run via `/meta-review` using a shared contract: `analyze(AnalysisUnit, perspective)`.


## 3. Specialize a small set of analyzers instead of many skills

You already know the big missing capabilities: cross-file imports, path traversal, docs vs code, import anti-patterns.[^2_1]
Implement them as *pure analyzers* (functions or simple scripts) instead of full skills:

- `analyzers/import_graph.py`: takes manifest, verifies all imports, detects mismatches, circulars, sys.path hacks.[^2_1]
- `analyzers/path_traversal.py`: static scan of bundle for user-input → filesystem join patterns, `..` handling, and suspicious path math.[^2_1]
- `analyzers/doc_consistency.py`: maps docs → code signatures and flags contradictions like your TTL doc/code mismatch.[^2_1]

`/meta-review` becomes a thin shell that: build AnalysisUnit → call analyzers → call agents → aggregate.
This dramatically reduces the number of skills while increasing cross-file power.

## 4. Normalize phases instead of per-skill pipelines

You already have a strong pipeline in `/q` (ScopeResolver, QuickCollectors, IssueNormalizer, ModePlanner, StrategicRenderer, ContextSink).[^2_1]
Make that pipeline the **only** pipeline and reuse it everywhere:

- Move Q1–Q6 into the shared library (e.g., `analysis_pipeline.py`) parameterized by AnalysisUnit and “mode profile” (security-heavy, perf-heavy, doc-heavy, etc.).[^2_1]
- `/meta-review`, `/trace`, `/diagnose`, `/p` can all invoke the same Q1–Q6 with different profiles instead of reinventing their own phase flows.

Then you can delete per-skill phase machinery and let skills be minimal “profiles + UX” wrappers around a single engine.

## 5. Simplify hooks: from many small gates to composite policies

You currently have a large zoo of PreToolUse/ PostToolUse hooks (authorization, dependency verification, path validator, syntax gate, investigation gate, etc.).[^2_1]
You can keep the coverage but make the system leaner and more comprehensible:

- Implement a single `PreToolUse_policy_gate` that loads a JSON policy from `P:/.claude/state/policies/` or `P:/.claude/config/policies/` and then internally runs the checks that used to be separate hooks (path, imports, risk tier, observe-before-act).[^2_1]
- Similarly, implement one `PostToolUse_quality_gate` that wraps artifact, docs, and code-quality validation with policy-based toggles per tool/skill.[^2_1]

This preserves the “fail-closed security, fail-open quality” contract but removes a lot of hook sprawl, and it lets you evolve policies without touching code.[^2_1]

## 6. Make multi-source the default, not an opt‑in

NotebookLM only found those five issues because it was forced to see README + code + tests + pyproject.toml together.[^2_1]
You can mirror that insight by design:

- Any code-review entry (e.g., `/meta-review`, `/p PHASE 4.5`) always builds an AnalysisUnit at the *package/feature* level, not a single file, unless explicitly overridden.[^2_1]
- Media/packaging skills (`/package`, NotebookLM integration) must call `/meta-review` with that same AnalysisUnit ID before generating artifacts, instead of letting the user skip PHASE 4.5.[^2_1]

This turns your cross-file analysis from “extra step” into “default first-class behavior,” which is where the real gains are.

## 7. Aggressive deletion/reduction candidates

Given you don’t care about transition costs and are okay deleting things:

- Collapse many of these into profiles of `/meta-review`:
    - `/adversarial-*` entry skills, `/code-python`, `/code-typescript`, `/code-standards`, `/comply`, `/validate-safety-patterns`, `/adversarial-qa`, `/adversarial-failure-modes`.[^2_1]
- Keep as separate skills only where the UX / intent is distinct:
    - `/trace` (step-through mental execution for a specific scenario).
    - `/diagnose` (interactive hypothesis-testing loops).
    - `/p` (development pipeline controller).
- Replace `/multi-file-refactor` and similar with a generalized “refactor” profile that consumes the same AnalysisUnit (now naturally cross-file).[^2_1]

This leaves you with: one meta-review skill, a few UX-focused skills, a shared pipeline, a shared AnalysisUnit abstraction, and a small number of analyzers and agents.

---

If you had to pick *one* of these refactors to implement first for maximum impact, I’d start with the AnalysisUnit abstraction plus `/meta-review` and only then collapse older skills into profiles—does that ordering match how you want to approach this?

<div align="center">⁂</div>

[^2_1]: review_bundle_code_review_ecosystem_2026-03-10.md


---

# Are there repos that already provide what I'm asking for?

There are repos that cover big chunks of what you want, but nothing that cleanly matches your “Claude Code-native, cross-file, AI‑assisted review orchestrator” vision end‑to‑end.[^3_1][^3_2]

## 1. Repos that are closest in spirit

- **TypeScript Static Analysis MCP (community MCP for Claude)** – Reddit post describes an MCP server that gives Claude project‑wide TypeScript analysis: symbol search, class/Interface relationships, import/export graph, circular dependency detection, and complexity checks.[^3_2]
    - This is very close to your “AnalysisUnit + import graph + cross-file reasoning” idea, but TS‑only and MCP‑oriented rather than skill/hook‑oriented.
- **DiffDeck (open source code review workflow tool)** – Focused on generating structured diffs and security assessments across branches/dirs, with directory‑level context and reporting.[^3_3]
    - Gives good ideas for “bundle” diffs and report structuring, but is not a general-purpose static analyzer or Claude‑native orchestration layer.


## 2. Traditional multi-file static analysis frameworks

These solve import graphs, call graphs, and path traversal, but are heavy/standalone:

- **SonarQube/SonarCloud** – Mature static analysis with cross-file rules for TypeScript, Python, etc., including import misuse, dead code, security smells, and path traversal patterns.[^3_4][^3_5]
- **CodeChecker (Clang/LLVM ecosystem)** – Multi‑file static analysis orchestrator with incremental analysis and dependency‑aware re‑runs.[^3_6]
- **SVF (Static Value-Flow Analysis)** – Research‑grade framework for whole‑program, cross‑file value‑flow analysis.[^3_7]
- **findimports** – Python utility to statically inspect and validate Python import statements across a project.[^3_8]

These are excellent **engines** to call from Claude (via Bash or custom tools) for imports, path traversal, and data‑flow, but they don’t give you an AI‑native “meta-review skill” pattern out of the box.[^3_7][^3_6][^3_8]

## 3. AI-native context engines (proprietary but informative)

- **Augment Code Context Engine** – Maintains a semantic dependency graph over 400k+ files and does cross‑repo, architectural‑context‑aware review.[^3_1]
    - Confirms that your “AnalysisUnit + graph + orchestrated review” architecture is exactly what cutting‑edge tools do, but the engine is closed‑source.


## 4. Net answer for your use case

- There is **no** open-source repo that:
    - Integrates directly into Claude Code skills/hooks,
    - Builds reusable “review bundles” or AnalysisUnits,
    - Orchestrates multiple AI agents plus static analyzers for cross‑file review the way you’re envisioning.
- The closest pieces you can **steal patterns from** are:
    - The TypeScript Static Analysis MCP design (for project graph + MCP/LLM interface).[^3_2]
    - Tools like findimports and Sonar rulesets for concrete cross‑file/import/path checks.[^3_5][^3_4][^3_8]

You’ll almost certainly need to build your own orchestrator + manifest/graph layer, then optionally plug in these existing analyzers as backends; does that match your tolerance for owning a custom “context engine” in this ecosystem?
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://www.augmentcode.com/tools/open-source-ai-code-review-tools-worth-trying

[^3_2]: https://www.reddit.com/r/ClaudeAI/comments/1llksml/typescript_static_analysis_mcp/

[^3_3]: https://www.reddit.com/r/opensource/comments/1hpr8l1/i_just_made_an_open_source_tool_for_making_code/

[^3_4]: https://www.lucentsky.com/en/sast/path-traversal

[^3_5]: https://www.sonarsource.com/knowledge/languages/ts/

[^3_6]: https://github.com/Ericsson/codechecker

[^3_7]: https://svf-tools.github.io/SVF/

[^3_8]: https://github.com/mgedmin/findimports

[^3_9]: https://codepathfinder.dev

[^3_10]: https://projekter.aau.dk/projekter/files/239563289/final.pdf

[^3_11]: https://discourse.llvm.org/t/path-traversal-on-explodedgraph-of-clang-static-analyzer/47729

[^3_12]: https://ar5iv.labs.arxiv.org/html/2406.08098

[^3_13]: https://lists.llvm.org/pipermail/cfe-dev/2018-February/056975.html

[^3_14]: https://www.youtube.com/watch?v=WlSHiOsl7-U

[^3_15]: https://www.reddit.com/r/codereview/comments/1oz8dri/comment/np9ww4y/


---

# Yes I’m fine owning a custom context engine

Great. Then the next step is to define the **minimal contract** for your custom context engine and let everything else hang off that.[^4_1]

## Proposed minimal contract

Have a Python library, say `P:/.claude/lib/context_engine/analysis_unit.py`, that exposes three core functions:

- `create_analysis_unit(target_path, language_hints=None, mode_profile=None) -> AnalysisUnitId`
    - Discovers related files (package/feature scope), builds import graph, maps tests/docs, and writes a manifest into `P:/.claude/state/analysis_units/{terminal_id}/{id}/manifest.json`.[^4_1]
- `load_analysis_unit(id) -> dict`
    - Returns manifest: files, imports, symbols, tests, docs, risk hot-spots, etc.
- `update_analysis_unit(id, changed_files) -> None`
    - Incrementally refreshes the manifest after edits, so repeated reviews stay cheap.

All higher-level skills (review, refactor, trace, diagnose, package, NotebookLM integration) should accept either `target_path` or `analysis_unit_id`, but internally always normalize to an AnalysisUnit via this API.[^4_1]

## How it plugs into your current ecosystem

- `/meta-review` (new skill):

1. Calls `create_analysis_unit` if needed.
2. Runs shared Q1–Q6 pipeline using the manifest instead of ad‑hoc globbing.[^4_1]
3. Invokes agents (`adversarial-*`, `test-analyzer`, etc.) with a stable “here is the manifest + key questions” contract.
- `/p` PHASE 4.5, `/package`, NotebookLM steps: call `/meta-review` with the AnalysisUnit ID before media generation, making multi-source review mandatory rather than optional.[^4_1]
- Hooks like `PreToolUse_path_validator` and `PreToolUse_dependency_verification_gate` can optionally query the manifest to validate paths/imports more intelligently instead of re-parsing files themselves.[^4_1]


## First implementation slice

For a first working version that already beats today’s behavior:

1. Scope = Python package rooted at `target_path` (directory or file’s parent).
2. Manifest includes, per file:
    - Relative path, module name, imports, exported symbols.
    - Linked tests and docs (simple heuristics: `tests/`, `test_*.py`, `README*.md`).[^4_1]
3. Built-in analyzers operating solely on the manifest:
    - Import existence and mismatch checker (like a lightweight `findimports`).[^4_2][^4_1]
    - Path traversal heuristic: flag any user-input-ish symbols used in joins with `..` or `os.path` / `Path` manipulations.[^4_1]
    - Docs vs code sanity (only for obviously linked README/docstrings, not deep semantic checks yet).[^4_1]

You can then iterate toward TS and deeper security/architecture checks without changing the external contract.

Would you like a concrete manifest schema draft (JSON structure and example) for this AnalysisUnit so you can start coding against it immediately?

<div align="center">⁂</div>

[^4_1]: review_bundle_code_review_ecosystem_2026-03-10.md

[^4_2]: https://github.com/mgedmin/findimports

