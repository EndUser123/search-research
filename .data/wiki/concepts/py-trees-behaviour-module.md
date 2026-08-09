---
title: "Py Trees Behaviour Module"
created: 2026-08-09
source: nlm-sync-2026-08-09
tags: [nlm-synced, reference, trees]
summary: >
  The py_trees.behaviour module defines the abstract Behaviour class as the core template for all nodes in a py_trees behavior tree. Subclasses override user-customisable lifecycle methods (setup, initialise, update, terminate) so that the framework's tick driver can manage a node's lifecycle and prod
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 0fa07246-ba84-43fd-a9cd-f86999f24286" (LLM-Driven Behavior Trees for Autonomous Robot Task Planning, synced 2026-08-09)
  - "py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs" (https://docs.ros.org/en/humble/p/py_trees/py_trees.behaviour.html, transcript synced 2026-08-09)
  - "Automatic Behavior Tree Expansion with LLMs for Robotic Manipulation - arXiv" (https://arxiv.org/html/2409.13356v1, transcript synced 2026-08-09)
  - "Compatibility with py-trees-js · splintered-reality py_trees · Discussion #348 - GitHub" (https://github.com/splintered-reality/py_trees/discussions/348, transcript synced 2026-08-09)
  - "py_trees.trees module - ROS Docs" (https://docs.ros.org/en/iron/p/py_trees/py_trees.trees.html, transcript synced 2026-08-09)
  - "py_trees.visitors module — py_trees: Kilted 2.4.0 documentation - ROS Docs" (https://docs.ros.org/en/kilted/p/py_trees/py_trees.visitors.html, transcript synced 2026-08-09)
  - "NotebookLM source a95b340c-f779-46eb-abbf-6d2037889468" (Python Behavior Tree Framework for Autonomous LLM Agents  Technical Specification + Boilerplate.md, synced 2026-08-09)
  - "ReAcTree: Hierarchical Task Planning with Dynamic Tree Expansion using LLM Agent Nodes | OpenReview" (https://openreview.net/forum?id=KgKN7F0PyQ, transcript synced 2026-08-09)
  - "py_trees/py_trees/behaviour.py · 5782ea45b6403cc013f7b997b002a2c0600488e0 · Siqi Yi / py_trees_ros - GitLab" (https://gitlab.acfr.usyd.edu.au/siyi4041/py_trees_ros/-/blob/5782ea45b6403cc013f7b997b002a2c0600488e0/py_trees/py_trees/behaviour.py, transcript synced 2026-08-09)
provenance:
  chain:
    - level: concept
      id: py-trees-behaviour-module
    - level: notebook
      id: 0fa07246-ba84-43fd-a9cd-f86999f24286
      title: LLM-Driven Behavior Trees for Autonomous Robot Task Planning
      url: https://notebooklm.google.com/notebook/0fa07246-ba84-43fd-a9cd-f86999f24286
    - level: cluster
      id: 3
      name: trees-https-docs
    - level: source_url
      url: https://docs.ros.org/en/humble/p/py_trees/py_trees.behaviour.html
      title: py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs
    - level: source_url
      url: https://arxiv.org/html/2409.13356v1
      title: Automatic Behavior Tree Expansion with LLMs for Robotic Manipulation - arXiv
    - level: source_url
      url: https://github.com/splintered-reality/py_trees/discussions/348
      title: Compatibility with py-trees-js · splintered-reality py_trees · Discussion #348 - GitHub
    - level: source_url
      url: https://docs.ros.org/en/iron/p/py_trees/py_trees.trees.html
      title: py_trees.trees module - ROS Docs
    - level: source_url
      url: https://docs.ros.org/en/kilted/p/py_trees/py_trees.visitors.html
      title: py_trees.visitors module — py_trees: Kilted 2.4.0 documentation - ROS Docs
    - level: source_url
      url: https://openreview.net/forum?id=KgKN7F0PyQ
      title: ReAcTree: Hierarchical Task Planning with Dynamic Tree Expansion using LLM Agent Nodes | OpenReview
    - level: source_url
      url: https://gitlab.acfr.usyd.edu.au/siyi4041/py_trees_ros/-/blob/5782ea45b6403cc013f7b997b002a2c0600488e0/py_trees/py_trees/behaviour.py
      title: py_trees/py_trees/behaviour.py · 5782ea45b6403cc013f7b997b002a2c0600488e0 · Siqi Yi / py_trees_ros - GitLab
relations:
  - target: wiki/concepts/py_trees.trees-(behaviourtree-custodian).md
    type: related
  - target: wiki/concepts/py_trees.visitors-(visitorbase,-debugvisitor,-snapshotvisitor).md
    type: related
  - target: wiki/concepts/py_trees.composites-(sequence,-selector/fallback).md
    type: related
---

# Py Trees Behaviour Module

## Decision context

**Definition:** The py_trees.behaviour module defines the abstract Behaviour class as the core template for all nodes in a py_trees behavior tree. Subclasses override user-customisable lifecycle methods (setup, initialise, update, terminate) so that the framework's tick driver can manage a node's lifecycle and produce a discrete Status (SUCCESS, FAILURE, RUNNING, INVALID) on each tick.

Synthesized from **8 contributing transcripts** in NotebookLM notebook *LLM-Driven Behavior Trees for Autonomous Robot Task Planning*, clustered into the "trees-https-docs" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- A behaviour instance carries a name, an auto-generated uuid id, a status, parent/children references, a logger, a feedback_message string, and a BlackBoxLevel hint used by dot graphs and runtime GUIs to collapse or expand subtrees.
- The class exposes four user-customisable lifecycle methods: __init__ for offline construction (no middleware), setup for one-off configuration and verification of runtime infrastructure (e.g. middleware clients), initialise for just-in-time reset/clear of variables when the behaviour re-enters from a non-RUNNING state, and update which returns the new Status and must be near-instantaneous and non-blocking.
- The framework-driven methods include stop(new_status) which performs termination bookkeeping and resets the tick generator, tick() which is a generator yielding self and which calls initialise, update, and stop as appropriate, and tick_once() which invokes the generator to completion in one shot for callers that do not want step-by-step iteration.
- terminate(new_status) is invoked by stop when the behaviour transitions out of RUNNING (to SUCCESS/FAILURE/INVALID); users override it to cancel external actions or shut down temporary resources, since the next reset of variables is handled by initialise rather than terminate.
- Helper introspection methods include has_parent_with_name (regular-expression match against ancestors), has_parent_with_instance_type, iterate (yields this node plus descendants with an optional direct_descendants mode), tip (returns the deepest running node in this subtree or None if INVALID), visit (dispatches a VisitorBase to run on this behaviour), and attach_blackboard_client (creates and namespaces a blackboard Client attached to this behaviour).
- Initialise may be called more than once in the lifetime of a tree since every entry from a non-RUNNING status re-runs it; users should not override tick() or stop() to inject custom behaviour — those are reserved for update() and terminate() respectively.
- The framework expects users to raise exceptions inside setup for any construction or configuration fault; choice of exception type is left to the user.
- The earlier (legacy) form of the class used basestring assertions and a unique_id.fromRandom() id generator but preserves the same four lifecycle hooks and the same Status-driven tick generator design.

## Verifiable values

| Name | Value |
|---|---|
| module version (Humble docs) | `py_trees 2.2.3 (2023-02-08)` |
| module version (Iron docs) | `py_trees 2.2.3` |
| module version (Kilted docs) | `py_trees 2.4.0 (2025-11-13)` |
| Status enum members | `INVALID, RUNNING, FAILURE, SUCCESS` |
| priority_weight range (BTNode schema) | `0.0 to 10.0` |
| max_optimization_rounds default | `5` |
| success_threshold default | `0.9` |
| max_ticks default in TreeTicker | `100` |

## Related concepts

- [[py_trees.trees-(behaviourtree-custodian)]] — py_trees.trees (BehaviourTree custodian)
- [[py_trees.visitors-(visitorbase,-debugvisitor,-snapshotvisitor)]] — py_trees.visitors (VisitorBase, DebugVisitor, SnapshotVisitor)
- [[py_trees.composites-(sequence,-selector/fallback)]] — py_trees.composites (Sequence, Selector/Fallback)
- py_trees.decorators — py_trees.decorators
- [[py_trees.blackboard-(client,-attach_blackboard_client)]] — py_trees.blackboard (Client, attach_blackboard_client)
- [[py_trees.common-(status,-blackboxlevel,-duration,-parallelpolicy)]] — py_trees.common (Status, BlackBoxLevel, Duration, ParallelPolicy)
- [[betr-xp-llm-(llm-based-bt-expansion)]] — BETR-XP-LLM (LLM-based BT expansion)
- py_trees-2.4+-pydantic-v2-self-optimizing-framework — py_trees 2.4+ Pydantic v2 self-optimizing framework

## Citations (from contributing transcripts)

- **Claim:** The core behaviour template for all py_tree behaviours
  - Source: py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs (`0ab0bac7-25b2-43e2-97bc-f1866389e484`)
  - Context: The core behaviour template for all py_tree behaviours.
- **Claim:** Behaviour attributes include uuid id, name, status, parent, children, logger, feedback_message, blackbox_level
  - Source: py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs (`0ab0bac7-25b2-43e2-97bc-f1866389e484`)
  - Context: Attributes: ~py_trees.behaviours.Behaviour.id (uuid.UUID): automagically generated unique identifier ... name ... blackboards ... status (Status) ... parent ... children ... logger ... feedback_message ... blackbox_level (BlackBoxLevel)
- **Claim:** update() is the primary worker function and should be almost instantaneous and non-blocking
  - Source: py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs (`0ab0bac7-25b2-43e2-97bc-f1866389e484`)
  - Context: This method should be almost instantaneous and non-blocking
- **Claim:** initialise() runs whenever the behaviour is not RUNNING and may be called more than once in the lifetime of a tree
  - Source: py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs (`0ab0bac7-25b2-43e2-97bc-f1866389e484`)
  - Context: This method is automatically called via the ... tick() method whenever the behaviour is not RUNNING. ... note:: This method can be called more than once in the lifetime of a tree!
- **Claim:** terminate(new_status) handles disabling resources until next tick; do not set self.status there
  - Source: py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs (`0ab0bac7-25b2-43e2-97bc-f1866389e484`)
  - Context: Do not set self.status = new_status here, that is automatically handled by the stop() method.
- **Claim:** tip() returns the deepest node that was running before subtree traversal reversed direction, or None if INVALID
  - Source: py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs (`0ab0bac7-25b2-43e2-97bc-f1866389e484`)
  - Context: The deepest node (behaviour) that was running before subtree traversal reversed direction, or None if this behaviour's status is INVALID.
- **Claim:** attach_blackboard_client creates and attaches a blackboard client to this behaviour with an optional namespace
  - Source: py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs (`0ab0bac7-25b2-43e2-97bc-f1866389e484`)
  - Context: Create and attach a blackboard to this behaviour.
- **Claim:** tick() is a generator that yields itself and must be used with yield, otherwise prefer tick_once()
  - Source: py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs (`0ab0bac7-25b2-43e2-97bc-f1866389e484`)
  - Context: This is a generator function, you must use this with yield. If you need a direct call, prefer tick_once() instead.
- **Claim:** The lifecycle demo recommends __init__ for non-runtime config, setup for one-off infrastructure checks, and initialise for just-in-time checks
  - Source: py_trees.behaviour module — py_trees: Humble 2.2.3 documentation - ROS Docs (`0ab0bac7-25b2-43e2-97bc-f1866389e484`)
  - Context: Use __init__() for configuration of non-runtime dependencies (e.g. no middleware). Use setup() for one-offs or to get early signal that everything (e.g. middleware) is ready to go. Use initialise() for just-in-time configurations and/or checks.
- **Claim:** The legacy implementation uses basestring assertions and unique_id.fromRandom() but preserves the same four lifecycle hooks and Status-driven tick generator
  - Source: py_trees/py_trees/behaviour.py · 5782ea45b6403cc013f7b997b002a2c0600488e0 · Siqi Yi / py_trees_ros - GitLab (`dbeea1b4-c57a-4af3-8328-12183f31d428`)
  - Context: assert isinstance(name, basestring), ... self.id = unique_id.fromRandom() ... def setup(self, timeout): ... def initialise(self): ... def terminate(self, new_status): ... def update(self): ... def tick(self): ...

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `0fa07246-ba84-43fd-a9cd-f86999f24286`
(cluster `trees-https-docs`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: wiki-yt/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [LLM-Driven Behavior Trees for Autonomous Robot Task Planning](https://notebooklm.google.com/notebook/0fa07246-ba84-43fd-a9cd-f86999f24286)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)

## Auto-related

- [[skill-catalog]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[py-trees-documentation-cloudflare-verification]]
- [[sdlc-workflow-improvements-from-session-019fdf3d]]
- [[python-abstract-base-classes]]

