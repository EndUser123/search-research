---
title: "Act as a Senior AI Architect. Research and output a complete technical specification + Python boilerplate for a **Python"
date: "2026-04-10"
mode: "COPILOT"
uuid: "510b75dc-e090-4e2c-b978-5cce90d65943"
entry_count: 1
---

## Human

Act as a Senior AI Architect. Research and output a complete technical specification + Python boilerplate for a **Python Behavior Tree (BT) framework** using **py_trees** + **Pydantic**, optimized for **autonomous LLM agents** to produce optimal outcomes in tasks like code gen, planning, or tool orchestration.

**Core Goal**: Enable agents to execute hierarchical plans that self-optimize: run BT → capture outputs/errors → prune failures → regrow superior branches via LLM → repeat until optimal result (e.g., verified success metric). No system monitoring; pure outcome focus.

Provide exactly these sections with code:

1. **Data Schema**: Pydantic recursive model for **Universal BT Node** (Action/Condition/Decorator/Selector/Sequence types). Fields: `node_id`, `type`, `priority_weight` (float), `children` (list[Self]), `params` (dict for tool mappings/LLM prompts), `metadata` (dict: {'static': bool, 'description': str}). Use `model_rebuild()` for recursion. Validate schemas [web:7][web:19].

2. **Execution Engine**: **Tree Ticker** class (wrap py_trees.BehaviourTree). Detail `tick()` loop handling **SUCCESS** (complete), **FAILURE** (prune), **RUNNING** (continue). On FAILURE, trigger self-correction: capture `feedback_message` → LLM expand → update tree [web:1][web:8][web:17].

3. **Tool Mapping**: Pattern for leaf Action nodes: `params` → tool calls (e.g., {'tool': 'yt-dlp', 'args': {...}} or MCP/CLI). Return structured output dict for parent eval.

4. **ToT Self-Optimization**: LLM integration to expand on FAILURE: prompt="Analyze failure '{feedback}'; generate new subtree JSON schema for better outcome toward goal '{goal}'." Parse/validate new nodes, insert via `tree.add_children()` or prune [web:9][web:20]. Define success metric (e.g., task completion score).

5. **Persistence**: Serialize BT state (node statuses, counters) to JSON/disk via Pydantic `model_dump_json()`. Resume: load → py_trees setup → tick from last RUNNING node [web:17].

6. **Boilerplate Code**: Full runnable script (py_trees + Pydantic + NetworkX for viz). Demo **self-correcting loop**: init tree for mock task (e.g., "build API endpoint") → simulate FAILURE → LLM stub expands → re-tick → SUCCESS. Include main loop: `while not optimal: tick(); if failure: optimize_tree()` [web:3][web:22].

Output: Markdown with **bold code blocks**. Use latest py_trees (2.4+) [web:2]. Ensure agentic: trees must evolve to maximize outcomes without human intervention.

## Assistant

Here's the complete technical specification and boilerplate for your autonomous LLM agent Behavior Tree framework. The report covers all six sections you requested, grounded in the actual py_trees 2.4+ and Pydantic v2 APIs.

## What's in the Report

**Section 1 — Architecture Overview**: Full component map showing how `AgentOrchestrator → TreeTicker → LLMOptimizer → Pydantic schema → Disk` wire together. Four design invariants are stated explicitly (schema-first, non-blocking, failure-as-signal, deterministic resume).

**Section 2 — Universal BTNode Schema**: Complete Pydantic v2 `BTNode` model with `list["BTNode"]` recursion resolved via `model_rebuild()`. Includes `NodeMetadata` for failure history, `priority_weight`, `runtime_status` (synced back from py_trees post-tick), and two `@field_validator` guards (leaf has no children; decorator has exactly one child).[1][2]

**Section 3 — TreeTicker (Execution Engine)**: Wraps `py_trees.BehaviourTree`. `tick()` calls `tick_once()`, reads `tree.tip().feedback_message`, syncs status back to schema, and fires `on_failure_hook` on `FAILURE`. `replace_subtree()` uses the official `BehaviourTree.replace_subtree(uuid, subtree)` API for live surgery — both in the py_trees object graph and the Pydantic schema simultaneously.[3][4][5]

**Section 4 — Tool Mapping**: A `BEHAVIOUR_REGISTRY` dict maps `params['tool']` strings to `ToolActionBase` subclasses. Includes `CLIToolAction`, `LLMPromptAction`, `MCPToolAction`, and `PassthroughBehaviour` as fallback. Results are written to the py_trees blackboard under `result/<node_name>`.[6]

**Section 5 — LLMOptimizer (ToT Loop)**: Structured prompt uses failure context (`feedback_message`, `failure_count`, `last_feedback` from metadata) + goal string to request a replacement subtree as JSON. Pydantic validates LLM output before any tree mutation — a `ValidationError` aborts the round cleanly. `compute_success_score()` is the pluggable success metric.[7][8]

**Section 6 — Persistence**: `save_tree()` does atomic `tmp → rename` writes via `model_dump_json()`. `load_tree()` calls `model_rebuild()` pre-parse. `find_resume_node_id()` depth-first-searches for the deepest `RUNNING` node for crash-safe resume.[9][10]

**Section 7 — Visualization**: NetworkX `DiGraph` built from `BTNode` tree; nodes colored by status (green/red/blue/grey), shaped by type. Falls back from graphviz to spring layout if graphviz is absent.[11][12]

**Section 8 — Full `main.py`**: The self-correcting loop: `while not optimal: tick(); if failure: optimizer (via hook); rebuild_tree(); save()`. Demo uses a `SimulatedFailThenSucceed` leaf that fails tick 1 → triggers LLM stub → replacement subtree inserted → tick 2 → `SUCCESS`.

**Critical gotcha**: `replace_subtree()` raises `AssertionError` if you target the root — the optimizer must never prune the root node. All Action leaf `update()` methods must be non-blocking; long LLM/CLI calls belong behind `concurrent.futures` polled each tick.[13][5]
