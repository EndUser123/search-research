---
title: "CLI API drift in skill scripts — hardcoded subprocess calls break when the wrapped CLI changes"
created: 2026-07-25
source: session-20260725 (/why root cause analysis of crawl4ai qmd integration failures)
tags: [skill-design, cli-drift, subprocess, api-compatibility, failure-pattern, durability, root-cause]
summary: >
  Skills that shell out to external CLIs via subprocess hardcode API assumptions (subcommand
  names, flag signatures, response schemas) that break silently when the wrapped CLI's version
  changes. The crawl4ai skill (ported from search-research plugin) called `qmd update` and
  `qmd search <positional> --format json` — neither exists in qmd 0.1.2's API. The failure was
  latent for months because Phase 2 (related-link injection) silently skipped on every crawl.
  The structural fix: runtime API probing (detect available subcommands, dispatch accordingly)
  OR a shim module that isolates the external API behind one import point. The skill's own
  dependency check verified the CLI was *installed* but never verified the *API shape* matched
  the script's assumptions.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - session-20260725 (/why root cause analysis of crawl4ai-qmd integration)
  - session-20260719 (log.md entry documenting the earlier qmd CLI syntax mismatch — later found to be documenting a non-existent command)
relations:
  - target: wiki/concepts/subprocess-as-degradation-boundary.md
    type: complements
  - target: wiki/concepts/qmd-semantic-search-requires-llm-backend.md
    type: related
  - target: wiki/concepts/raising-coding-best-practices-in-ai-agents.md
    type: related
---

# CLI API drift in skill scripts

## Decision context

**Why this knowledge was needed:** the crawl4ai skill's qmd integration broke silently across
multiple sessions. The `/why` investigation (session 20260725) traced it to two hardcoded
subprocess calls assuming a qmd API that doesn't match the installed version. The pattern —
skill scripts that shell out to CLIs without runtime API verification — is systemic: it will
recur for every skill that wraps a versioned external tool. Capturing the root cause and the
structural fix prevents the next skill from repeating the failure.

## The failure pattern

Skill scripts that wrap external CLIs via `subprocess.run([..., "cli", "subcommand", "--flag", ...])`
make three hardcodable assumptions:

1. **Subcommand existence** — the CLI has the subcommand the script calls (e.g., `qmd update`)
2. **Flag signature** — the subcommand accepts the flags the script passes (e.g., `--format json`)
3. **Response schema** — the output matches the shape the script parses (e.g., `{title, file}` vs `{chunk_ref, text}`)

When the wrapped CLI's version changes, any of these can break. The skill's dependency check
typically verifies only that the CLI is *installed* (`shutil.which("qmd")` or `subprocess.run(["qmd", "--help"])`),
not that the *API shape* matches the script's assumptions. The failure is silent: the subprocess
returns non-zero or empty output, the script treats it as "no results," and the feature degrades
without any error surfacing to the user.

## The reference incident (crawl4ai-qmd, 2026-07-25)

The crawl4ai skill at `~/.grok/skills/crawl4ai/crawl_to_qmd.py` had two hardcoded mismatches
against qmd 0.1.2:

| Line | Assumption | Reality (qmd 0.1.2) |
|------|-----------|---------------------|
| 528 | `qmd update <collection>` (bulk rebuild) | `update` subcommand doesn't exist; only `search`/`collection`/`document` |
| 100-104 | `qmd search <positional> --format json --limit N`, expects `{title, file}` | Needs `--query`/`--top-k`, no `--format`, returns `{chunk_ref, text}` |

Phase 2 (related-link injection) silently skipped on every crawl since the port from the
search-research plugin. The `_check_dependencies()` function verified qmd was installed but
never probed the API shape. A log entry from 2026-07-19 (`log.md:734`, later corrected)
documented `qmd update` as a real command — itself an instance of the same failure (documenting
a CLI API without runtime verification).

## Why this is systemic (with honest scoping)

The pattern recurs for any skill that wraps a versioned external tool:

- **crawl4ai** wraps qmd (this incident)
- **/wiki** wraps qmd (auto-link uses subprocess — fixed via the wiki_search shim)
- **search-research plugin** wraps qmd via `qmd_wiki_backend.py` (same pattern, documented venv rationale)
- Future skills wrapping MCP servers, CLI tools, or versioned Python libraries are at risk

**Honest scoping (cross-model review, 2026-07-25):** all three concrete workspace instances above target the same CLI (qmd), not three independent CLIs. This concept is therefore a **prevention document arguing from the structural pattern**, not from a broad empirical base of multiple CLI-wrapping skills having failed. The pattern is generic enough to justify capture; the workspace evidence is currently qmd-specific. If the pattern recurs against a different CLI in the next 12 months, that confirms the systemic claim. If it doesn't, the concept may be over-generalized from a single incident (see Falsifier condition 1).

The failure mode is particularly insidious because:
1. The dependency check passes (CLI is installed)
2. The failure is silent (subprocess returns non-zero, script treats as "no results")
3. The feature degrades without surfacing an error
4. The root cause is invisible without source inspection (the script *looks* correct)

## The structural fixes (in priority order)

### Fix 1: Shim module (highest durability, recovers both properties)

Route all access to the external API through a single shim module. Consumers import the shim,
not the external library directly. This is the `wiki_search.py` pattern documented in
[[subprocess-as-degradation-boundary]]. If the external API changes, only the shim changes.

**When to apply:** the external dependency's long-term viability is uncertain, OR multiple
consumers wrap the same API.

### Fix 2: Runtime API probing (middle ground)

Before calling the CLI, probe its actual API shape and dispatch accordingly. This mirrors the
`_normalize_result()` pattern crawl4ai already uses for its *own* API drift across versions:

```python
def _qmd_api_probe():
    """Detect available qmd subcommands. Returns set of supported subcommands."""
    result = subprocess.run(["qmd", "--help"], capture_output=True, timeout=5)
    # parse "choose from: search, collection, document" → {"search", "collection", "document"}
    ...

if "update" in _qmd_api_probe():
    subprocess.run(["qmd", "update", collection])  # bulk path
else:
    for f in files:
        subprocess.run(["qmd", "document", "add", ...])  # per-doc path
```

**When to apply:** the shim is overkill (single consumer, stable dependency) but the CLI's
version drifts across environments.

### Fix 3: Dependency check that probes API shape, not just existence

Extend `_check_dependencies()` to verify the specific subcommands/flags the script uses, not
just that the CLI is installed:

```python
def _check_qmd_api():
    result = subprocess.run(["qmd", "--help"], capture_output=True, timeout=5)
    help_text = result.stdout.decode()
    required = ["search", "document"]  # subcommands the script uses
    missing = [r for r in required if r not in help_text]
    if missing:
        raise DependencyError(f"qmd missing required subcommands: {missing}")
```

**When to apply:** always, as a baseline. This catches the failure at skill startup rather
than silently at runtime.

## What this means for our workspace

- **Audit existing skills** for the pattern: grep for `subprocess.run` in skill scripts and
  check whether the called CLI's API is verified at any point. Candidates: crawl4ai (fixed),
  wiki auto-link (fixed via shim), search-research plugin backend (documented, low priority
  since it's a plugin not a skill).
- **Skill authoring checklist** — when writing a skill that wraps an external CLI:
  1. Probe the API shape in `_check_dependencies()`, not just existence
  2. Prefer a shim module if the dependency is uncertain or shared
  3. Surface subprocess failures loudly (non-zero exit → error, not silent skip)
  4. Document the CLI version the script was authored against
- **`/crawl4ai` version check** already exists (`--check-version` flag) but checks crawl4ai's
  version, not qmd's API shape. The shim fix makes this moot for qmd, but the pattern applies
  to future skills.

## Falsifier

This pattern is wrong if, within 12 months:
- **No other skill exhibits the CLI-drift failure** despite the pattern being common — meaning
  the failure is specific to qmd's API instability, not a systemic skill-design issue.
- **The shim module accumulates drift itself** (the shim's assumptions diverge from qmd's API
  without being caught). Mitigation: the shim's smoke test (`python wiki_search.py`) catches
  drift at runtime.
- **Runtime API probing proves too slow or brittle** (the probe itself drifts). Counter: the
  probe uses `--help`, the most stable CLI contract; if `--help` drifts, the CLI is fundamentally
  broken.

## Receipts

- **crawl4ai source** — `~/.grok/skills/crawl4ai/crawl_to_qmd.py` lines 100-115 (search), 524-545
  (update). Both hardcoded subprocess calls documented in the /why analysis (session 20260725).
- **qmd CLI verification** — `qmd --help` (this session): only `search`/`collection`/`document`;
  `qmd search --help`: requires `--query`/`--top-k`, no `--format`.
- **Latent failure evidence** — every `/crawl4ai` run since the port printed "NOTE: Related-link
  injection skipped (index stale or update failed)" without surfacing the underlying API mismatch.
- **Log entry correction** — `P:/.data/wiki/log.md:734` (this session) marked SUPERSEDED after
  discovering it documented a non-existent `qmd update` command.
- **Shim implementation** — `P:/.agents/scripts/wiki_search.py` (commit `b8d7dee`, this session).

## Sources

- [[subprocess-as-degradation-boundary]] — the companion concept: subprocess preserves a
  degradation property that direct import destroys. This concept (CLI API drift) names the
  failure class; that concept names the architectural response.
- [[qmd-semantic-search-requires-llm-backend]] — prior qmd integration issues; same subsystem,
  different failure layer (semantic search bugs vs CLI API drift).
- [[raising-coding-best-practices-in-ai-agents]] — the dismissal-bias rule; the original /why
  dismissed subprocess as "just wrong" without inventorying why it existed.
