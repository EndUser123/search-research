---
name: ai-api
description: Multi-provider LLM API calls with dynamic model discovery and performance-based curation
version: "1.0.0"
status: stable
category: ai-llm
triggers:
  - /ai-api

suggest:
  - /comply
  - /bug-hunt
  - /analyze
---

# LLM API - Multi-Provider LLM Access

**Dynamic model discovery with performance-based curation.** Direct API calls to LLM providers via litellm with live model catalog and tiered selection.

## Purpose

Multi-provider code review with specialized category analysis using **live provider catalogs** (not hardcoded model lists).

## ⚡ EXECUTION DIRECTIVE

**When invoked, execute:**

```bash
python "P:\.claude\skills\ai-api\ai_api.py" "{{user_path}}" --mode {{mode}}
```

**MANDATORY:**
1. Parse user's path and mode from invocation
2. Read file content as context
3. Run analysis with dynamically-discovered models
4. Aggregate findings by priority (P0 → P1 → P2 → P3)
5. Return formatted results

**DO NOT:**
- Provide your own analysis instead of running the script
- Use hardcoded model lists

## Project Context

### Constitution/Constraints
- Evidence-first: Only report what LLMs actually found
- Priority ordering: Bugs (P0) > Error handling (P1) > DRY (P2) > Conventions (P3)
- Dynamic discovery: No hardcoded model counts

### Technical Context
- **Live model catalog**: Discovers models from provider APIs (24h cache)
- **Tiered selection**: Proven (T1) > Promising (T2) > Experimental (T3)
- **Task-based routing**: Auto-classifies query and selects appropriate models
- **Performance tracking**: Logs success rate, latency, output quality, dedup metrics
- **Five modes**: chill (1 model), mid (2 models), chad (3 models), adaptive (2-6 models with auto-stopping), route (rule-based keyword routing)
- **Finding deduplication**: Identifies duplicate findings across models using semantic signatures

### Architecture Alignment
- Uses ModelCatalog for dynamic discovery (internal)
- Integrates with `/comply` for standards validation
- Supports `/bug-hunt` for focused bug finding

## Your Workflow

1. Classify task type from query (code_review, debug, implement, etc.)
2. Discover available models from cached catalog (refresh if --refresh-models)
3. Select top N models by tier and task-type compatibility
4. Execute parallel review across selected models
5. Log performance metrics for future curation
6. Aggregate findings by priority (P0 → P1 → P2 → P3)

## Validation Rules

- MUST order findings by priority (P0 first, P3 last)
- MUST include model name and duration with each finding
- DO NOT suppress lower-priority findings if explicitly requested

## Quick Start

```bash
# Standard review (2 models, auto-detected task)
python "P:\.claude\skills\ai-api\llm_api.py" src/main.py

# Fast review (1 model)
python "P:\.claude\skills\ai-api\llm_api.py" src/main.py --mode chill

# Comprehensive review (3 models)
python "P:\.claude\skills\ai-api\llm_api.py" src/ --mode chad

# Adaptive review (2-6 models, auto-stops at finding convergence)
python "P:\.claude\skills\ai-api\llm_api.py" src/ --mode adaptive

# Route mode (keyword-based routing from llm-route)
python "P:\.claude\skills\ai-api\llm_api.py" src/main.py --mode route

# Force refresh model catalog
python "P:\.claude\skills\ai-api\llm_api.py" src/main.py --refresh-models
```

## Modes

| Mode | Models | Speed | Use Case |
|------|--------|-------|----------|
| chill | 1 (T1 only) | Fastest | Quick checks, rapid iteration |
| mid | 2 (T1+T2) | Standard | Default for most reviews |
| chad | 3 (T1+T2+T3) | Comprehensive | Deep analysis, edge cases |
| adaptive | 2-6 (auto-stops) | Variable | Cost-efficient, stops when findings converge |
| route | 1-3 (keyword-based) | Variable | Rule-based routing by task type (from llm-route) |

### Adaptive Mode Details

**Adaptive mode** iteratively runs models until finding convergence:
- Starts with 2 models (T1 + best T2 for task type)
- Adds one model at a time
- Computes deduplication metrics after each iteration
- Stops when last iteration added < 20% new unique findings
- Safety cap: 6 models maximum

**Finding Deduplication:**
- Extracts semantic signature from each finding
- Signatures based on: file paths, line numbers, issue type keywords, function/class names
- Duplicates identified across models
- Metrics tracked: total findings, unique findings, dedup ratio, duplicates found

## Task Types (Auto-Detected)

code_review, debug, implement, refactor, explain, plan, test, general

## Model Tiers

- **Tier 1 (Proven)**: 100+ successful runs, <90th percentile latency
- **Tier 2 (Promising)**: 20+ successful runs, good quality scores
- **Tier 3 (Experimental)**: New models, opt-in via chad mode

## Categories

security, bugs, error_handling, configuration, performance, concurrency, code_quality, testing, api_design, type_safety, dependencies, documentation

## Implementation

- **Path**: `P:\.claude\skills\ai-api\llm_api.py`
- **Dependencies**: litellm (via `P:\.claude\proxy\litellm`)
- **Cache**: `~/.claude/llm-api-models.json` (24h expiry)
- **Performance log**: `~/.claude/llm-api-performance.jsonl`
