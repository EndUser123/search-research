---
title: "For claude code on Windows 11, I discovered that we have single file tool review skills and technology, but it doesn't d"
date: "2026-03-10"
mode: "COPILOT"
uuid: "954a9af8-d037-40ec-b2c6-4943e0e8dbc2"
entry_count: 8
---

## Human

For claude code on Windows 11, I discovered that we have single file tool review skills and technology, but it doesn't do cross-file checking.  What do you think is an optimal solution to ensure we get cross-file checking?

## Assistant

The optimal solution is to introduce a *review bundle* pattern: a single orchestrator skill that (a) selects a coherent multi-file scope, (b) materializes that scope into a temporary “bundle” structure, and (c) runs your existing single-file review tools against that bundle with explicit cross-file checks layered on top.[1]

## Core idea

You keep your current single-file review skills as-is, but wrap them in a higher-level skill that always operates on a set of related files (module, package, or feature) instead of one file at a time.[1]
That bundle skill is responsible for discovering, normalizing, and exporting enough context that cross-file issues (imports, doc/code mismatch, path traversal, etc.) become visible in a single prompt and/or tool call.[1]

## Concrete design

Inside your existing ecosystem (P:/.claude/), you add something like `/review-bundle`:

- Phase 1 – **Scope resolver**: Given a target file or directory, glob the module/package: sibling modules, `__init__.py`, tests, and docs that reference that path.[1]
- Phase 2 – **Bundle builder**:  
  - Build a JSON index (bundle_manifest.json) listing files, import graph, and key symbols per file.  
  - Optionally write a synthetic “bundle summary” file (imports, public API, tests mapped to sources).[1]
- Phase 3 – **Tool fan-out**: Invoke your existing single-file tools (`/q`, `/r`, `/adversarial-*`, `/test-analyzer`, etc.) against each file, but pass the bundle manifest/summary as shared context so they can reason across boundaries.[1]
- Phase 4 – **Cross-file analyzers**: Add a tiny set of focused analyzers that *only* read the manifest plus the bundle files:  
  - Import resolver: check every import target exists and matches real paths, flag sys.path hacks, circular imports, and inconsistent package layouts.[1]
  - Doc consistency checker: compare docstrings/README claims to actual signatures and behaviors across files.[1]
  - Security/path traversal checker: central scan for user-input → filesystem joins, looking for `..` use and similar patterns across the bundle.[1]
- Phase 5 – **Aggregation & gating**: Aggregate findings, apply your existing quality gate (e.g., 80+ confidence threshold), and emit a single structured report back to the user.[1]

This leverage your current multi-agent / multi-phase patterns (e.g., `/q`’s ScopeResolver, QuickCollectors, IssueNormalizer, etc.), but makes “multi-file” an explicit first-class concern at the skill level rather than hoping each file review will infer cross-file issues.[1]

## Implementation notes tailored to your setup

- Put the orchestrator skill in `P:/.claude/skills/review-bundle/` with a SKILL.md that clearly declares it as the canonical entry point for cross-file review.  
- Reuse your existing **ScopeResolver + QuickCollectors** concepts from `/q` so you don’t re-invent discovery logic; teach ScopeResolver to operate at a package/feature level instead of pure single-file.[1]
- Have the bundle manifest written into `P:/.claude/state/skill_execution_{terminal_id}/review_bundle/…` so any sub-skill or hook in that terminal can load it cheaply without re-scanning the filesystem.[1]
- Use your current PreToolUse gates (`path_validator`, `python_import_gate`, `dependency_verification_gate`) to guard bundle discovery and the cross-file analyzers, but keep them fail-open for quality checks and fail-closed only for dangerous operations.[1]

## Why this is “optimal” for you

- It fits your existing architecture: skills orchestrate, hooks validate, agents do parallel analysis, tools read/grep/glob/bash; you’re just adding a new “bundle” orchestration layer and a couple of focused analyzers.[1]
- It avoids duplicating single-file logic; you reuse `/q`, `/r`, `/adversarial-*`, `/test-analyzer`, etc., and only add thin glue for cross-file relationships and manifest building.[1]
- It generalizes: The same bundle skill can run before media generation, packaging, or CI-like checks, and can be extended later with language-specific analyzers (Python/TypeScript) without changing the call site.  

Would you rather target *Python packages* or *feature directories* (mixed Python + TypeScript + docs) as the primary “bundle” unit for the first version?  

## Human

Is there refactoring we can do to make the optimal solution more efficient, effective, elegant?  I don't care about transition effort, and I'm ok with removing redundant skills/code/etc after.

## Assistant

Yes. You can collapse this into a smaller, more **elegant** core by refactoring around “analysis units” and a single meta-orchestrator, then deleting a lot of redundant skills.[1]

## 1. Introduce “AnalysisUnit” as the primitive

Right now the primitive is “skill that takes a path,” which leads to 150+ skills, each deciding scope and depth themselves.[1]
Refactor to a single low-level concept: an AnalysisUnit = {scope, files, manifest, questions}, and let everything operate on that.

- New tiny library under `P:/.claude/lib/analysis_unit/` (not a skill, just Python) that can: discover files for a package/feature, build the manifest (imports, symbols, tests, docs), and persist it in `P:/.claude/state/analysis_units/{terminal_id}/…`.[1]
- All higher-level capabilities (security, performance, docs, spec-compliance, etc.) take an AnalysisUnit ID instead of a raw path, so cross-file is automatic and consistent.  

This centralizes scope resolution and cross-file graph building into one place and eliminates per-skill ad‑hoc discovery logic.[1]

## 2. Replace many skills with one “meta-review” skill

Instead of `/q`, `/r`, `/adversarial-*`, `/test-analyzer`, `/code-*` each doing their own orchestration, introduce one `/meta-review` that:

- Accepts: `{target_path, modes[]}` where modes are semantic: `["security","imports","docs","performance","testing","architecture"]` (not separate skills).  
- Internally:  
  1. Creates or loads an AnalysisUnit for `target_path`.  
  2. Spawns the relevant adversarial/agent perspectives in parallel, all reading the same manifest and file set.[1]
  3. Runs a single normalization + quality-gate pass and emits a unified report.  

Then you can remove entire skills that are just thin wrappers around “security review of this path,” “performance review of this path,” etc., and keep only one meta-skill with flags.[1]

Example:  

- Delete `/adversarial-security`, `/adversarial-performance`, `/adversarial-quality`, etc. as *entry-point* skills.  
- Keep the corresponding agents, but they now only ever run via `/meta-review` using a shared contract: `analyze(AnalysisUnit, perspective)`.

## 3. Specialize a small set of analyzers instead of many skills

You already know the big missing capabilities: cross-file imports, path traversal, docs vs code, import anti-patterns.[1]
Implement them as *pure analyzers* (functions or simple scripts) instead of full skills:

- `analyzers/import_graph.py`: takes manifest, verifies all imports, detects mismatches, circulars, sys.path hacks.[1]
- `analyzers/path_traversal.py`: static scan of bundle for user-input → filesystem join patterns, `..` handling, and suspicious path math.[1]
- `analyzers/doc_consistency.py`: maps docs → code signatures and flags contradictions like your TTL doc/code mismatch.[1]

`/meta-review` becomes a thin shell that: build AnalysisUnit → call analyzers → call agents → aggregate.  
This dramatically reduces the number of skills while increasing cross-file power.  

## 4. Normalize phases instead of per-skill pipelines

You already have a strong pipeline in `/q` (ScopeResolver, QuickCollectors, IssueNormalizer, ModePlanner, StrategicRenderer, ContextSink).[1]
Make that pipeline the **only** pipeline and reuse it everywhere:

- Move Q1–Q6 into the shared library (e.g., `analysis_pipeline.py`) parameterized by AnalysisUnit and “mode profile” (security-heavy, perf-heavy, doc-heavy, etc.).[1]
- `/meta-review`, `/trace`, `/diagnose`, `/p` can all invoke the same Q1–Q6 with different profiles instead of reinventing their own phase flows.  

Then you can delete per-skill phase machinery and let skills be minimal “profiles + UX” wrappers around a single engine.  

## 5. Simplify hooks: from many small gates to composite policies

You currently have a large zoo of PreToolUse/ PostToolUse hooks (authorization, dependency verification, path validator, syntax gate, investigation gate, etc.).[1]
You can keep the coverage but make the system leaner and more comprehensible:

- Implement a single `PreToolUse_policy_gate` that loads a JSON policy from `P:/.claude/state/policies/` or `P:/.claude/config/policies/` and then internally runs the checks that used to be separate hooks (path, imports, risk tier, observe-before-act).[1]
- Similarly, implement one `PostToolUse_quality_gate` that wraps artifact, docs, and code-quality validation with policy-based toggles per tool/skill.[1]

This preserves the “fail-closed security, fail-open quality” contract but removes a lot of hook sprawl, and it lets you evolve policies without touching code.[1]

## 6. Make multi-source the default, not an opt‑in

NotebookLM only found those five issues because it was forced to see README + code + tests + pyproject.toml together.[1]
You can mirror that insight by design:

- Any code-review entry (e.g., `/meta-review`, `/p PHASE 4.5`) always builds an AnalysisUnit at the *package/feature* level, not a single file, unless explicitly overridden.[1]
- Media/packaging skills (`/package`, NotebookLM integration) must call `/meta-review` with that same AnalysisUnit ID before generating artifacts, instead of letting the user skip PHASE 4.5.[1]

This turns your cross-file analysis from “extra step” into “default first-class behavior,” which is where the real gains are.  

## 7. Aggressive deletion/reduction candidates

Given you don’t care about transition costs and are okay deleting things:

- Collapse many of these into profiles of `/meta-review`:  
  - `/adversarial-*` entry skills, `/code-python`, `/code-typescript`, `/code-standards`, `/comply`, `/validate-safety-patterns`, `/adversarial-qa`, `/adversarial-failure-modes`.[1]
- Keep as separate skills only where the UX / intent is distinct:  
  - `/trace` (step-through mental execution for a specific scenario).  
  - `/diagnose` (interactive hypothesis-testing loops).  
  - `/p` (development pipeline controller).  
- Replace `/multi-file-refactor` and similar with a generalized “refactor” profile that consumes the same AnalysisUnit (now naturally cross-file).[1]

This leaves you with: one meta-review skill, a few UX-focused skills, a shared pipeline, a shared AnalysisUnit abstraction, and a small number of analyzers and agents.  

---  

If you had to pick *one* of these refactors to implement first for maximum impact, I’d start with the AnalysisUnit abstraction plus `/meta-review` and only then collapse older skills into profiles—does that ordering match how you want to approach this?  

## Human

Are there repos that already provide what I'm asking for?

## Assistant

There are repos that cover big chunks of what you want, but nothing that cleanly matches your “Claude Code-native, cross-file, AI‑assisted review orchestrator” vision end‑to‑end.[1][2]

## 1. Repos that are closest in spirit

- **TypeScript Static Analysis MCP (community MCP for Claude)** – Reddit post describes an MCP server that gives Claude project‑wide TypeScript analysis: symbol search, class/Interface relationships, import/export graph, circular dependency detection, and complexity checks.[2]
  - This is very close to your “AnalysisUnit + import graph + cross-file reasoning” idea, but TS‑only and MCP‑oriented rather than skill/hook‑oriented.  
- **DiffDeck (open source code review workflow tool)** – Focused on generating structured diffs and security assessments across branches/dirs, with directory‑level context and reporting.[3]
  - Gives good ideas for “bundle” diffs and report structuring, but is not a general-purpose static analyzer or Claude‑native orchestration layer.  

## 2. Traditional multi-file static analysis frameworks

These solve import graphs, call graphs, and path traversal, but are heavy/standalone:

- **SonarQube/SonarCloud** – Mature static analysis with cross-file rules for TypeScript, Python, etc., including import misuse, dead code, security smells, and path traversal patterns.[4][5]
- **CodeChecker (Clang/LLVM ecosystem)** – Multi‑file static analysis orchestrator with incremental analysis and dependency‑aware re‑runs.[6]
- **SVF (Static Value-Flow Analysis)** – Research‑grade framework for whole‑program, cross‑file value‑flow analysis.[7]
- **findimports** – Python utility to statically inspect and validate Python import statements across a project.[8]

These are excellent **engines** to call from Claude (via Bash or custom tools) for imports, path traversal, and data‑flow, but they don’t give you an AI‑native “meta-review skill” pattern out of the box.[7][6][8]

## 3. AI-native context engines (proprietary but informative)

- **Augment Code Context Engine** – Maintains a semantic dependency graph over 400k+ files and does cross‑repo, architectural‑context‑aware review.[1]
  - Confirms that your “AnalysisUnit + graph + orchestrated review” architecture is exactly what cutting‑edge tools do, but the engine is closed‑source.  

## 4. Net answer for your use case

- There is **no** open-source repo that:  
  - Integrates directly into Claude Code skills/hooks,  
  - Builds reusable “review bundles” or AnalysisUnits,  
  - Orchestrates multiple AI agents plus static analyzers for cross‑file review the way you’re envisioning.  
- The closest pieces you can **steal patterns from** are:  
  - The TypeScript Static Analysis MCP design (for project graph + MCP/LLM interface).[2]
  - Tools like findimports and Sonar rulesets for concrete cross‑file/import/path checks.[5][4][8]

You’ll almost certainly need to build your own orchestrator + manifest/graph layer, then optionally plug in these existing analyzers as backends; does that match your tolerance for owning a custom “context engine” in this ecosystem?

## Human

Yes I’m fine owning a custom context engine

## Assistant

Great. Then the next step is to define the **minimal contract** for your custom context engine and let everything else hang off that.[1]

## Proposed minimal contract

Have a Python library, say `P:/.claude/lib/context_engine/analysis_unit.py`, that exposes three core functions:

- `create_analysis_unit(target_path, language_hints=None, mode_profile=None) -> AnalysisUnitId`  
  - Discovers related files (package/feature scope), builds import graph, maps tests/docs, and writes a manifest into `P:/.claude/state/analysis_units/{terminal_id}/{id}/manifest.json`.[1]
- `load_analysis_unit(id) -> dict`  
  - Returns manifest: files, imports, symbols, tests, docs, risk hot-spots, etc.  
- `update_analysis_unit(id, changed_files) -> None`  
  - Incrementally refreshes the manifest after edits, so repeated reviews stay cheap.  

All higher-level skills (review, refactor, trace, diagnose, package, NotebookLM integration) should accept either `target_path` or `analysis_unit_id`, but internally always normalize to an AnalysisUnit via this API.[1]

## How it plugs into your current ecosystem

- `/meta-review` (new skill):  
  1. Calls `create_analysis_unit` if needed.  
  2. Runs shared Q1–Q6 pipeline using the manifest instead of ad‑hoc globbing.[1]
  3. Invokes agents (`adversarial-*`, `test-analyzer`, etc.) with a stable “here is the manifest + key questions” contract.  
- `/p` PHASE 4.5, `/package`, NotebookLM steps: call `/meta-review` with the AnalysisUnit ID before media generation, making multi-source review mandatory rather than optional.[1]
- Hooks like `PreToolUse_path_validator` and `PreToolUse_dependency_verification_gate` can optionally query the manifest to validate paths/imports more intelligently instead of re-parsing files themselves.[1]

## First implementation slice

For a first working version that already beats today’s behavior:

1. Scope = Python package rooted at `target_path` (directory or file’s parent).  
2. Manifest includes, per file:  
   - Relative path, module name, imports, exported symbols.  
   - Linked tests and docs (simple heuristics: `tests/`, `test_*.py`, `README*.md`).[1]
3. Built-in analyzers operating solely on the manifest:  
   - Import existence and mismatch checker (like a lightweight `findimports`).[2][1]
   - Path traversal heuristic: flag any user-input-ish symbols used in joins with `..` or `os.path` / `Path` manipulations.[1]
   - Docs vs code sanity (only for obviously linked README/docstrings, not deep semantic checks yet).[1]

You can then iterate toward TS and deeper security/architecture checks without changing the external contract.  

Would you like a concrete manifest schema draft (JSON structure and example) for this AnalysisUnit so you can start coding against it immediately?  

## Human

Do we need to walk thru each step?  Or can you make reasonable assumptions and come up with a solution design that I can take to another LLM for review that can see the actual code base beyond what I provided in the attachment?

## Assistant

We do not need to walk through each step; I can propose a full solution design with reasonable assumptions that another LLM can refine against your actual code base.  

## High-level goal

Design a **custom context engine + meta-review skill** for Claude Code on Windows 11 that provides cross-file, package/feature-level analysis (imports, security, docs vs code, anti-patterns) and replaces many existing per-file/per-mode skills with a smaller, more powerful core.[1]

***

## 1. Core concept: AnalysisUnit and Context Engine

### 1.1 AnalysisUnit abstraction

**Definition (conceptual):**

An AnalysisUnit is the canonical description of “a thing to review,” representing a coherent scope (package, feature directory, or sub-tree) and all relationships inside it.

Minimal fields:

- `id`: Stable identifier (e.g., hash of absolute root path + timestamp or monotonic counter per terminal).  
- `terminal_id`: To respect your terminal-scoped state isolation.[1]
- `root_path`: Absolute path of the unit (package root or feature directory).  
- `language_profiles`: E.g., `{python: true, typescript: true, markdown: true}` inferred from files.  
- `files`: List of file entries, each with:  
  - `relative_path` (from `root_path`)  
  - `language` (python, typescript, markdown, json, other)  
  - `module_name` (for Python/TS where applicable)  
  - `symbols_exported` (classes, functions, constants, etc. – best-effort static parse)  
  - `symbols_imported` (imports per file, unresolved at first)  
  - `tests_for` (list of source-relative paths this file’s tests are associated with)  
  - `docs_for` (linked docs/README sections if trivially detectable)  
- `import_graph`: Directed graph representation, e.g.:  
  - `nodes`: module or file identifiers  
  - `edges`: `{from, to, type}` where `type` ∈ {`import`, `dynamic_import`, `sys_path_hack`}  
- `issues_precomputed`: Optional early static-heuristic findings (e.g., import target not found, obvious path traversal patterns).  
- `metadata`: Misc flags:  
  - `has_sys_path_manipulation`, `has_io_on_import`, `has_user_input_to_path`, etc.  

This structure is JSON-serializable and stored per terminal under:

- `P:/.claude/state/analysis_units/{terminal_id}/{analysis_unit_id}/manifest.json`.[1]

### 1.2 Context engine library

Introduce a Python library (not a skill) at `P:/.claude/lib/context_engine/`:

- `analysis_unit.py` with API:

```python
def create_analysis_unit(target_path: str,
                         language_hints: dict | None = None,
                         mode_profile: dict | None = None) -> str:
    """
    Returns analysis_unit_id.
    Creates directory under P:/.claude/state/analysis_units/{terminal_id}/{id}/
    and writes manifest.json.
    """

def load_analysis_unit(analysis_unit_id: str) -> dict:
    """Loads manifest.json into memory."""

def update_analysis_unit(analysis_unit_id: str,
                         changed_files: list[str]) -> None:
    """Re-parses only changed files and updates manifest + derived graphs."""
```

Implementation responsibilities (reasonable assumptions):

- Determine `terminal_id` from existing state conventions you already use for `breadcrumbs_{terminal_id}` and `skill_execution_{terminal_id}`.[1]
- Discover scope:  
  - If `target_path` is a file, set `root_path` to its package/feature directory (heuristics: nearest directory with `__init__.py`, `pyproject.toml`, `package.json`, or `.feature-root` marker).  
  - If `target_path` is a directory, treat that as `root_path` and limit depth by config (e.g., max files or depth).  
- File discovery: glob all files under `root_path` with relevant extensions.  
- Parsing/import graph: use standard library (`ast`, `pathlib`, maybe `tokenize`) and no external deps (per your constraints).[1]

***

## 2. New `/meta-review` skill as the single entry point

### 2.1 UX and invocation

Skill: `/meta-review` (in `P:/.claude/skills/meta-review/`)

**Invocation examples:**

- `/meta-review P:/packages/skill-guard --modes security,imports,docs`  
- `/meta-review src/skillguard/breadcrumb_tracker.py --modes imports`  

### 2.2 Arguments and modes

- Required: `target_path` (file or dir).  
- Optional flags:  
  - `--modes`: comma-separated high-level perspectives:  
    - `security`, `imports`, `docs`, `performance`, `testing`, `architecture`, `style`.  
  - `--depth-profile`: e.g., `fast`, `balanced`, `deep`.  
  - `--analysis-unit-id`: reuse existing AnalysisUnit if present (skip discovery).  

### 2.3 Meta-review flow

**PHASE M1 – AnalysisUnit normalization**

1. If `--analysis-unit-id` passed, try `load_analysis_unit`.  
2. Else, call `create_analysis_unit(target_path, hints, mode_profile)`; write manifest to state.[1]
3. Record the `analysis_unit_id` in `P:/.claude/state/skill_execution_{terminal_id}/meta-review.json` for reuse by sub-skills/agents.[1]

**PHASE M2 – Shared Q1–Q6 pipeline (generalized `/q`)**

Refactor your existing `/q` phases (ScopeResolver, QuickCollectors, IssueNormalizer, ModePlanner, StrategicRenderer, ContextSink) into a reusable pipeline function in a shared module (e.g., `P:/.claude/lib/pipeline/q_pipeline.py`).[1]

- `ScopeResolver`: Already effectively done by AnalysisUnit. For meta-review, this becomes “select subset of files from manifest based on modes.”  
- `QuickCollectors`:  
  - Collect quick static facts from manifest (imports, dependencies, doc ↔ code mapping, known hotspots).  
  - For more depth, schedule per-file static inspections (using Read/Grep/Glob/Bash tools) for a sample of high-risk files (imports with unresolved targets, sys.path manipulation, IO on import, etc.).[1]
- `IssueNormalizer`: Map raw findings into unified structure: `{id, file, location, severity, confidence, category, description, remediation_hint}`.  
- `ModePlanner`: For each mode, decide which analyzers & agents to run and what depth to use.  
- `StrategicRenderer`: Plan how to summarize outcomes and what follow‑ups to propose.  
- `ContextSink`: Persist results to `P:/.claude/state/analysis_units/{terminal_id}/{id}/findings.json` and to general skill state, following your existing ContextSink conventions.[1]

**PHASE M3 – Built-in analyzers (non-LLM, static-ish)**

Implement a small set of dedicated analyzers that operate solely on the manifest:

- `imports_analyzer.py`:  
  - Check each imported module/symbol resolves to a real file/module within the unit or allowed external modules.  
  - Flag: unresolved imports, circular imports, and suspicious `sys.path.insert` or `Path.cwd()`-based imports (import anti-pattern detector).[1]
- `path_traversal_analyzer.py`:  
  - Look for usage of `..` or similar patterns in path construction where any variable is likely influenced by user input (approximation: function args named `path`, `filename`, `user`, etc.; maybe config for names).  
  - Annotate manifest with suspected vulnerable call-sites.[1]
- `docs_consistency_analyzer.py`:  
  - For each exported function/class with clear docstring or README reference, check simple invariants: described params exist, no obvious contradictions like “No TTL” vs defined TTL constant.[1]

All analyzers emit findings into the shared IssueNormalizer pipeline.

**PHASE M4 – Agent-based multi-perspective review**

Using your existing agents:

- `adversarial-security`, `adversarial-performance`, `adversarial-quality`, `adversarial-testing`, `rca-specialist`, `test-analyzer`, `code-critic`, etc.[1]

Meta-review uses an `Agent` wrapper to spawn these with a standardized prompt contract:

- Input:  
  - Summary of the manifest (imports graph, hotspots, docs/code mapping).  
  - Sampled or prioritized source snippets around hotspots.  
  - Explicit task: “You are the X perspective reviewing this AnalysisUnit; focus on Y; here are candidate issues already detected by static analyzers; refine, confirm, or add.”  
- Output:  
  - Structured text or JSON that maps neatly into IssueNormalizer.  

**PHASE M5 – Quality gate and aggregation**

- Reuse your `quality-gate` agent/skill but now treat it as a library/pipeline step, not a separate entry.[1]
- Filter out findings below confidence 0.8, preserving your confidence-based filtering invariant.[1]
- Aggregate by category, severity, and file; produce final report + recommended next actions (e.g., `/trace here`, `/r here`, `/refactor here`).[1]

**PHASE M6 – Output to user and downstream tools**

- Present human-readable summary and optionally a machine-readable artifact (`findings.json`) that can be consumed by:  
  - `/p` PHASE 4.5 (code maturation pipeline).  
  - `/package` before NotebookLM/media generation.[1]
  - Custom scripts or CI wrappers you build later.  

***

## 3. Integration with existing skills and phases

### 3.1 `/p` and `/package` integration

- **New rule**: PHASE 4.5 of `/p` and `/package` must call `/meta-review` with a package-level `target_path` and `--modes security,imports,docs` before PHASE 4.7 Media Generation.[1]
- The NotebookLM adapter should:  
  1. Construct an AnalysisUnit for the package.  
  2. Run `/meta-review` and fail or warn if severe, unaddressed issues remain.  
  3. Only then select multi-source input (README + key source + tests + pyproject.toml) for media, piggybacking off the manifest instead of manual selection.[1]

### 3.2 Refactoring existing skills

Goal: replace as many “review-ish” skills as possible with `/meta-review` modes.

- Deprecated entry skills (to be removed or made thin aliases):  
  - `/adversarial-review` and mode variants, `/adversarial-*` entry points, `/code-python`, `/code-typescript`, `/code-standards`, `/comply`, `/validate-safety-patterns`, much of `/multi-file-refactor` for inspection aspects.[1]
- Kept as distinct UX/front-end skills:  
  - `/trace`: scenario-focused step-through; can still use `AnalysisUnit` to get context for the file under trace.  
  - `/diagnose`: interactive root-cause investigation; may reuse findings.json from `/meta-review` to start from suspected hotspots.  
  - `/refactor`: uses AnalysisUnit manifest to plan cross-file refactors, but its primary goal is writing, not reviewing.  
  - `/p`: high-level pipeline orchestrator.  

Each of these should depend on the context engine instead of re‑discovering code structure themselves.  

***

## 4. Hook and policy simplification

### 4.1 Policy-driven PreToolUse gate

Introduce a `PreToolUse_policy_gate` hook that:

- Loads a policy definition from `P:/.claude/config/policies/*.json`, specifying rules like:  
  - Allowed/disallowed tools per skill.  
  - When to enforce `observe-before-act` for specific modes.[1]
  - Extra checks for paths or imports when tool is e.g. `Bash` or `Write`.  
- Internally calls existing validation routines that your current individual hooks use (`path_validator`, `python_import_gate`, `dependency_verification_gate`, `risk_tier_gate`, etc.), but under a single executable script.[1]

This simplifies enforcement without changing behavior and can leverage manifest data when present (e.g., verifying that a path to be modified actually belongs to the current AnalysisUnit).  

### 4.2 PostToolUse quality gate

Similarly, a `PostToolUse_quality_gate` hook can:

- Aggregate what are now `PostToolUse_artifact_validator`, `PostToolUse_documentation_validator`, `PostToolWrite_code_quality`, etc., guided by per-skill policy.[1]
- Use the manifest (if available) to ensure the updated file is still import-resolvable and consistent with surrounding docs/tests.  

***

## 5. What another LLM should do with this design

Given this design, another LLM with full repo access can:

1. **Locate integration points**:  
   - Where `/q`, `/adversarial-*`, `/p`, `/package`, hooks, and agents currently live and how they’re wired (matching what’s in the review bundle).[1]
2. **Implement the context engine**:  
   - Flesh out `analysis_unit.py`, file discovery, AST parsing, graph construction.  
   - Decide exact manifest schema fields based on actual code.  
3. **Refactor `/q` into a shared pipeline** and migrate `/meta-review` to use it.  
4. **Gradually deprecate old skills** by turning them into shims that just call `/meta-review` in specific mode profiles and then finally delete them once you’re satisfied.  
5. **Update hooks/settings.json** to register the new policy gates and wire them for relevant skills.[1]

***

If I package this into a single “design brief” file (e.g., DESIGN_CONTEXT_ENGINE.md) with explicit API signatures and manifest schema, would that be the most useful format for dropping into another LLM session for implementation work?  

## Human

How does this solution look? Any gaps or improvements you can think of?

## Assistant

This is a solid, ambitious plan. I see several real gaps and some areas where the LLM that built it over-engineered relative to what actually solves your original problem. Here's my assessment:

## What's strong

- The AnalysisUnit primitive and manifest concept are exactly right — centralizing scope resolution and cross-file graph into one reusable structure is the core insight.[1]
- The non-destructive deployment strategy (shadow → canary → parallel → migrate → cutover) is disciplined and respects your multi-terminal environment.[1]
- Terminal-scoped state isolation carried forward correctly from your existing conventions.[2][1]

## Gaps and concerns

### SCIP is likely a dead end for you

The plan treats SCIP as a primary dependency with AST fallback, but `scip-python` has limited Python 3.12+ support (the plan itself acknowledges this gap), and you're on Python 3.14. For a solo dev on Windows 11, maintaining a SCIP indexing pipeline is high friction for marginal gain over `ast` + `importlib.util`. **Recommendation**: Drop SCIP entirely. Use Python's `ast` module for symbol/import extraction (it handles 3.14 syntax natively) and simple heuristics for TypeScript (`import/export` regex or a lightweight TS parser). You can always add SCIP later if AST proves insufficient — but it almost certainly won't for your use cases (import graphs, symbol exports, doc consistency).[2][1]

### Multi-model consensus (Star Chamber) is premature

T-024/T-025 add GPT-4o and Gemini API clients with weighted voting and quorum logic. This is a significant complexity increase (API keys, cost, latency, error handling for 3 providers, timeout coordination) that solves a problem you don't have yet — false positive reduction. You haven't even measured your false positive rate with a single-model system. **Recommendation**: Cut the Star Chamber entirely from the initial plan. Build the single-model path well, measure false positives after shadow mode, and only add multi-model consensus if the data shows you need it. Your existing confidence-threshold + quality-gate pattern already handles noise filtering.[2][1]

### The Invariant Kernel adds a second rule system alongside your hooks

You already have a hook-based enforcement system with fail-closed/fail-open semantics. The Invariant Kernel (T-004/T-005) introduces a parallel rule engine with its own JSON schema, reconvergence cycles, and 4-tier hierarchy (Prime/System/Domain/Artifact). This creates two enforcement paths that must stay in sync. **Recommendation**: Merge the Invariant Kernel concept *into* the policy-gate hook design from our earlier discussion. Instead of a separate rule engine, make `PreToolUse_policy_gate` load policy JSON files that encode the same Prime/System/Domain/Artifact tiers. One enforcement path, not two.[1][2]

### The 3-phase ToT framework is solving for auditability, not cross-file detection

T-020 through T-022 build a ToT reasoning framework (Error Inventory → Logic Trace → Minimal Fix) that's more about structured LLM reasoning than about the core problem of cross-file analysis. The actual cross-file detection comes from the analyzers (import_graph, path_traversal, doc_consistency) — those are deterministic and don't need ToT. **Recommendation**: Defer the ToT framework. Your existing GoT+ToT in `/q` already works for LLM-driven analysis. Focus effort on making the deterministic analyzers excellent, then let agents reason over their findings using your existing patterns.[2][1]

### No manifest schema is actually defined

The plan references `bundle_manifest.json` repeatedly but never specifies the actual JSON schema — what fields, what types, what the import graph edges look like, how tests are associated with source files. This is the single most important contract in the entire system. **Recommendation**: Define the manifest schema as T-000 (before T-001). Every downstream task depends on it. Without it, the implementing LLM will make ad-hoc decisions that fragment the design.[1]

### 18-week timeline is ~3x too long for what matters

The core value — cross-file analysis that catches the 5 issues NotebookLM found — lives entirely in Phase 1 (AnalysisUnit + analyzers + shadow mode). Phases 2–5 are deployment ceremony, multi-model consensus, and migration wrappers. For a solo dev, you don't need canary sampling or A/B testing against yourself. **Recommendation**: Compress to ~4–6 weeks:[2][1]
- Weeks 1–2: Manifest schema + AnalysisUnit API + 3 analyzers (import, path traversal, docs).
- Weeks 3–4: `/meta-review` skill wired to the engine + policy gate hook.
- Weeks 5–6: Run against real packages, tune, then start aliasing old skills to `/meta-review`.

### Missing: how agents receive manifest context

The plan says agents will use the manifest but doesn't specify the prompt contract — how much of the manifest goes into an agent's prompt, how findings from deterministic analyzers are passed as "pre-seeded issues" for agents to refine, or how to stay within the 200K token agent context window for large packages. **Recommendation**: Define a `prepare_agent_context(analysis_unit_id, perspective, max_tokens)` function that selects relevant manifest slices + pre-seeded findings + sampled source code, with explicit token budgeting.[1][2]

### Missing: incremental analysis for edited files

`update_analysis_unit()` is listed but not designed. After a `/refactor` or manual edit, you need to know *which* manifest fields are stale and re-derive only those. Without this, you'll regenerate the full manifest on every review, which gets expensive for large packages. **Recommendation**: Track file content hashes in the manifest. `update_analysis_unit()` diffs hashes, re-parses only changed files, and re-derives affected graph edges.[1]

## Suggested revised task list

If you strip out the premature complexity, the critical path becomes:

1. **T-000**: Define manifest JSON schema (the contract everything depends on).
2. **T-001**: AnalysisUnit API (`create`, `load`, `update` with content hashing) — AST-only, no SCIP.
3. **T-002**: `import_graph.py` analyzer.
4. **T-003**: `path_traversal.py` analyzer.
5. **T-004**: `doc_consistency.py` analyzer.
6. **T-005**: `/meta-review` SKILL.md — wires AnalysisUnit + analyzers + existing agents with a `prepare_agent_context()` contract.
7. **T-006**: `PreToolUse_policy_gate` — consolidates existing hooks + manifest-aware checks, with Invariant Kernel tiers as policy JSON.
8. **T-007**: Integration into `/p` PHASE 4.5 and `/package`.
9. **T-008**: Tests against known-bad packages (your skill-guard issues as regression suite).
10. **T-009**: Alias/deprecate old skills.

That's roughly 8–10 tasks vs 40, with the same end-state for what actually matters. The shadow/canary/parallel ceremony can be added later if you find you need gradual rollout — but for a solo dev, you probably just flip a switch and start using it.

## Human

The target LLM says that advice is excellent.  What do you think you did differently?  Or more preciesily, what should I have the target LLM do different next time when developinng the solution and plan?

## Assistant

You should keep doing what you did with me: force the model to optimize for *system design leverage* instead of “feature completeness.”  

Here’s what was different and how to steer the target LLM next time.

## 1. I optimized for value, not coverage

What I did:
- Took your original *problem* (cross-file review, reduce skill zoo) as the objective function, then evaluated each plan element against that.[1][2]
- Flagged features that don’t move that objective (SCIP, Star Chamber, ToT framework) as deferrable or unnecessary, even if they’re cool.[2]

What to ask the target LLM:
- “For each major subsystem you propose, justify it *strictly* against these goals: A) cross-file vulnerability detection, B) skill consolidation, C) runtime safety. Anything that does not materially improve A–C must be either cut or explicitly justified as ‘future / optional’. List cuts.”  
- “Given my goals, identify at least 3 parts of your own plan that are likely over-engineered or premature optimization. Propose a strictly smaller but equally effective design.”  

## 2. I collapsed parallel rule systems

What I did:
- Noticed the Invariant Kernel would duplicate your existing hook-based enforcement; recommended merging “rules” into the policy gate instead of creating a second engine.[1][2]

What to ask:
- “Before introducing any new enforcement mechanism or rule engine, compare it explicitly to existing hooks/policies. If it overlaps, refactor into a single system and delete the weaker one. Describe the merged design.”  

## 3. I attacked external dependencies and complexity

What I did:
- Treated SCIP, multi-model consensus, and ToT as high-cost dependencies relative to your solo-dev constraints and your actual wins.[2]
- Recommended an AST-only, single-model v1 with optional later upgrades.  

What to ask:
- “For every external dependency or new service (SCIP, MCP, extra LLMs), classify as MUST/SHOULD/MAY based on my constraints: solo dev, Windows 11, Python 3.14, no ops team. Propose a v1 that uses only MUST, and move the rest to an explicit ‘Phase X – Optional Enhancements’ section.”  
- “Replace any suggested dependency that is brittle or under-maintained with a baseline approach using only Python stdlib + TypeScript compiler APIs unless absolutely impossible.”  

## 4. I forced a contract-first design (manifest schema)

What I did:
- Pointed out that the manifest schema is the critical contract and that your plan never actually defined it, even though 30+ tasks depend on it.[2]

What to ask:
- “Before listing tasks, define the core data contracts (e.g., AnalysisUnit manifest JSON schema) in detail. Every task must reference those contracts instead of inventing ad-hoc formats. If you propose tasks without a prior schema, stop and define the schema first.”  
- “Produce the manifest schema and one realistic example instance, then re-derive the task list from that.”  

## 5. I shortened the critical path and removed process ceremony

What I did:
- Collapsed 40 tasks and 18 weeks into ~8–10 essential tasks that deliver the same core outcome: AnalysisUnit + analyzers + meta-review + policy gate + migration of top skills.[2]
- Treated shadow/canary/parallel as optional extras for a solo user, not mandatory SDLC ceremony.  

What to ask:
- “Identify the smallest set of tasks that delivers 80% of the user’s stated value. Present that as the *primary* plan. Move all other tasks into a ‘Secondary / Nice-to-have’ section.”  
- “Assume a single user (me) is the only stakeholder. Remove SDLC processes that only make sense for a team/organization (A/B, canary percentages, training materials) unless you can justify them concretely.”  

## 6. I looked for double systems and missing glue

What I did:
- Flagged gaps: no defined prompt contract from manifest → agents; no incremental update strategy; no manifest schema.[2]
- Flagged duplication: ToT vs your existing `/q` GoT/ToT; Invariant Kernel vs hooks; Star Chamber vs confidence thresholds.[1][2]

What to ask:
- “Scan your design for any pair of components that appear to solve similar problems (e.g., two rule engines, two reasoning frameworks). For each pair, propose a merged design or delete one.”  
- “List integration gaps: which components claim to exist but have no contract defined (data shape, prompt template, or function signature). Fill those in before expanding the plan.”  

## 7. I biased toward your stated preferences

What I did:
- Exploited your constraints: solo dev, Windows 11, no DB, stdlib-only, and your tolerance for deleting skills and refactoring aggressively.[1]

What to ask:
- “Optimize for: solo developer, Windows 11, Claude Code skills/hooks, stdlib-only Python. You may *not* introduce infra I can’t reasonably run and maintain alone. If you do, justify and add a no-infra fallback.”  
- “Assume I am willing to delete old skills and aggressively refactor. Prefer fewer, more powerful components over many shims or migration scaffolds.”  

***

If you want, I can turn these into a reusable “meta-prompt” you can paste in front of any future planning request to that LLM so it automatically behaves more like this analysis.

## Human

yes please!

## Assistant

Here’s a reusable meta-prompt you can paste in front of future “design + plan” requests to the target LLM.

***

### META-PROMPT FOR SYSTEM DESIGN & IMPLEMENTATION PLANS

You are helping a **solo developer** who is a **solution architect and AI-first systems designer** working on **Claude Code skills/hooks on Windows 11**.
Your job is to produce **lean, high-leverage system designs and implementation plans**, not maximal feature lists.

Follow these rules strictly:

#### 1. Optimize for value, not coverage

- Treat the user’s *stated goals* as the objective function. For this project, the primary goals are:  
  1) cross-file/codebase-level understanding and validation,  
  2) consolidation and simplification of skills/tools,  
  3) runtime safety and correctness.  
- For every major subsystem you propose, explicitly justify how it advances one or more of these goals.  
- Any component that does not meaningfully move these goals must be **cut** or clearly marked as “optional / future enhancement”.

Before finalizing the design, do this explicitly:

> “For each major subsystem I proposed, here is how (or if) it directly advances the core goals. Here are at least 3 parts of my own plan that are over-engineered or premature; here is a strictly smaller but equally effective design.”

#### 2. Prefer merging to duplicating mechanisms

The user already has:  
- A hook system (PreToolUse, PostToolUse, Stop, SessionStart) with fail-open vs fail-closed semantics.[1]

Before creating any **new** enforcement or rule engine:

- First compare it to the existing hooks/policies.  
- If they overlap in responsibility, design a **merged** system and delete or avoid the weaker one.  
- You must not leave two parallel, overlapping rule systems unless you give a strong, explicit justification.

Add an explicit section:

> “Potential duplicate mechanisms I introduced vs existing hooks/policies, and how I will merge or remove them.”

#### 3. Be ruthless about external dependencies and complexity

Constraints:

- Solo dev, Windows 11, Python 3.14, no ops team, no DB, standard library only for hooks/skills.[1]

For every external dependency (SCIP, MCP servers, extra LLM providers, heavy infra):

- Classify as MUST / SHOULD / MAY.  
- Design a **v1** that uses only MUST-level dependencies.  
- Move SHOULD/MAY items into an “Optional Enhancements” section with clear triggers (e.g., “add this only if false positive rate > 20% after initial rollout”).

Add a section:

> “Dependency audit: which dependencies are absolutely required for v1, which are optional later, and what is the minimal v1 without them?”

Avoid multi-model consensus / Star Chamber patterns, complex A/B infra, or SDLC ceremony unless you can show they are essential for this user’s constraints and goals.

#### 4. Contract-first: define core schemas and APIs before task lists

Before listing tasks:

- Define the **core data contracts** that everything will use (e.g., an AnalysisUnit/manifest JSON schema, key function signatures for the context engine).  
- Use concrete field names, types, and at least one realistic example instance.  
- All later tasks must build on these contracts; do not invent ad-hoc structures per task.

Add a section *before* any implementation plan:

> “Core Contracts: Manifest schema(s), key API signatures, and an example manifest instance. All tasks below assume and reuse these contracts.”

If you find yourself writing tasks that require data structures that were not previously defined, **stop**, define/extend the schema, and then continue.

#### 5. Shorten the critical path; separate core from ceremony

You must produce two plans:

1. **Core Plan (v1, small)**: The smallest set of tasks that delivers ~80% of the user’s value.  
2. **Extended Plan (optional)**: Additional ceremony/features (shadow/canary/parallel modes, dashboards, multi-model, training docs, etc.).

For the Core Plan:

- Aim for 5–10 tasks, focused on:  
  - the context/manifest engine,  
  - the key analyzers,  
  - the main orchestrator skill (e.g., `/meta-review`),  
  - minimal policy hooks or gates,  
  - migration of the most-used legacy skills to the new path.  
- Assume the user can flip a feature flag and live with a sharp cutover if needed; do not default to multi-phase enterprise rollout.

Add explicit sections:

> “Core Plan (minimal v1 to achieve goals)”  
> “Extended Plan (optional, only if/when needed)”

#### 6. Hunt for double systems and missing glue

As you design:

- Scan for pairs of components that appear to solve similar problems (e.g., two reasoning frameworks, two rule engines, two review entrypoints) and either merge or remove one.  
- Scan for **integration gaps**: components that claim to exist but lack defined contracts (data shape, prompt template, or function signature). Fill these gaps **before** expanding the plan.

Add a section:

> “Consolidation & Gaps:  
> - Duplicate or overlapping systems I removed or merged.  
> - Missing contracts/glue I filled in (e.g., how agents receive manifest context, how manifests update incrementally).”

#### 7. Align tightly with this user’s environment and preferences

- Assume: Claude Code skills/hooks, terminal-scoped JSON state, no DB, Python and TypeScript code, 50K+ LOC monorepo.[1]
- The user is comfortable deleting old skills and aggressively refactoring toward fewer, more powerful components.  
- Prefer “one powerful engine + slim adapters” over “many overlapping skills.”

Add a short “fit check”:

> “Environment & Preference Fit: How this design respects solo-dev constraints, Windows 11 + Claude Code hooks, stdlib-only, and aggressive consolidation.”

#### 8. Output expectations

- Produce:  
  - A concise architecture section.  
  - Core Contracts (schemas/APIs with examples).  
  - Core Plan (minimal v1 tasks).  
  - Extended Plan (optional extras, clearly marked).  
  - Consolidation & Gaps analysis.  
  - Environment & Preference Fit note.

Do **not** optimize for number of tasks, diagrams, or phases. Optimize for **leverage per unit of complexity**.

***

You can prepend this meta-prompt and then say something like:

> “Now, within this framework, design the meta-review system and implementation plan for my codebase, given the attached docs.”

If you’d like, I can now specialize this meta-prompt further for this exact meta-review/context-engine project so you have a ready-to-paste combined prompt.
