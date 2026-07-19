# Phase 1 Research Quality Improvement Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve evidence-finding quality through deterministic evidence-category extraction, targeted query planning, source contribution telemetry, inverse-query evaluation, and conservative stopping signals while preserving the current `/all` runtime and provider boundary.

**Architecture:** Add a pure quality-analysis module consumed by the existing Phase 1 artifact builder. It classifies required evidence categories from task signals and query text, records planned query variants and source contribution/duplicate signals, and emits a recommendation-oriented stopping assessment without changing provider selection or Phase 2A activation. Evaluation uses the existing research-run artifacts plus a bounded 20-case agentic-coding corpus.

**Tech Stack:** Python dataclasses, JSON research-run.v1 artifacts, existing pytest suite, QMD/MMX/Brave existing lanes only.

## Global Constraints

- Keep caller `search-research:/all` unchanged.
- Do not rename commands, add providers, invoke `agy`, integrate `/search` or `/go`, or automate Phase 2A.
- Do not replace deterministic routing with opaque LLM routing.
- Preserve provider results, opened-source identity, assessment status, failures, and immutable run paths.
- Prefer minimum sufficient evidence over source count or parallelism.

### Task 1: Audit the current quality data path

- [x] Inspect `P:\tools\research_run_v1\phase1.py`, `assessment.py`, `validator.py`, router signals, and current `/all` adapter.
- [x] Identify where query, lane, source, assessment, and stop fields are written and read.
- [x] Record current gaps without changing command topology.

### Task 2: Add pure quality analysis

**Files:**
- Create: `P:\tools\research_run_v1\quality.py`
- Test: `P:\tests\research_run_v1\test_quality.py`

- [x] Implement deterministic evidence-category extraction for conceptual, implementation, authority, maintenance, failure, and local evidence.
- [x] Implement targeted query planning from the user question and missing categories.
- [x] Implement conservative inverse-query classification and duplicate/usefulness helpers.
- [x] Implement stopping assessment using opened useful evidence, unresolved required categories, redundancy, and failures.

### Task 3: Bind quality telemetry to Phase 1 artifacts

**Files:**
- Modify: `P:\tools\research_run_v1\phase1.py`
- Modify: `P:\tools\research_run_v1\validator.py` only if schema validation requires additive fields
- Test: `P:\tests\research_run_v1\test_phase1.py`
- Test: `P:\tests\research_run_v1\test_workflow_integration.py`

- [x] Add additive `quality` fields: required categories, planned query variants, inverse-search decision, source contribution counts, missing evidence, and stopping assessment.
- [x] Do not alter lane recommendations or Phase 2A activation.
- [x] Keep all existing provenance and failure fields intact.

### Task 4: Create and evaluate the 20-case corpus

**Files:**
- Create: `P:\tests\research_run_v1\research_quality_corpus.json`
- Create: `P:\tools\research_run_v1\evaluate_quality.py`

- [x] Cover adoption, repository selection, architecture, compatibility, implementation, maintenance, local architecture, and official documentation questions.
- [x] Use existing artifacts where possible; run only bounded new `/all` cases after quota/readiness checks.
- [x] Measure the required YAML-equivalent fields and distinguish measured runtime evidence from heuristic quality labels.

### Task 5: Verify and report

- [x] Run focused quality tests and the canonical `P:\tests\research_run_v1` suite.
- [x] Validate all newly generated artifacts.
- [x] Report before/after measurements, inverse-search value/noise, stopping behavior, source contribution, authorization, and remaining unknowns.
- [x] Choose exactly one required quality verdict.

Note: the canonical suite recorded 68 passed and 3 pre-existing router-corpus
failures from staged `router.py` changes outside this increment; no router
changes were made here.
