"""Mechanism Manifest - UserPromptSubmit Hook Module.

Injects a short pointer list of existing detection/retrieval mechanisms so the
model does not propose new gates/detectors/retrievers when an existing one
already does the job. Counter to mechanism-inventory blindness: the failure
where a model defaults to "expand the regex list" because nothing in its context
said non-regex detectors already exist.

Unconditional by design. The fault this counters (defaulting to regex on a
general /prospect) does not announce itself with trigger words, so trigger-gating
would miss exactly the case that motivates the manifest. Kept tiny (~330 chars)
to avoid ceremony fatigue.

Priority: 9.5 (late, near generation).
Config: MECHANISM_MANIFEST_ENABLED (default: true). Not in the weak-model skip
list — weak models are the population that needs this most.
"""
from __future__ import annotations

import os

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Glosses follow the function-calling / MCP convention (name + description): a bare
# name tells the model a mechanism exists; a gloss tells it WHEN to reach for each.
# Without glosses the manifest raises awareness but not actionability — the model
# still has to grep to know if semantic_critic fits its situation.
#
# Scaling cliff: RAG-MCP (arXiv 2505.03275) shows listing wins below ~10-20 tools and
# LOSES selection accuracy above it. We are at ~12 mechanisms. Past ~20, migrate this
# to daemon-backed retrieval (index these glosses, retrieve top-k per prompt) rather
# than growing the list. Do not just keep appending — past the cliff the list itself
# becomes the bug.
_MANIFEST = """## MECHANISM INVENTORY — check before proposing new gates/detectors
Non-regex detection — rule-based (no LLM): epistemic_validator (Stop warn-mode structural/causal/claim checks)
Non-regex detection — LLM-based: semantic_critic (cheap-model reasoning review), anti_dodge_judge (external judge for hook answers)
Claim gates: cross_validator (evidence for "fixed"/"done"), unverified_stance (empty hedges/doubt), fabrication_detector (fake tool-use), cks_quality_gate (LLM gate on CKS ingest)
Adversarial reviews: /red-team, /pre-mortem, /adversarial-review, /code-review
Search before assuming unreachable: /search, /prospect, sr MCP
Native verify/cleanup (harness-built-in, zero surface): /verify (launch + observe real behavior — use after hook/plugin changes, before any "done" claim), /simplify (applied cleanup of changed code — legacy surface only, review its diff)
Proposing a new gate/retriever? Grep this repo first.""".strip()


@register_hook("mechanism_manifest", priority=9.5)
def mechanism_manifest(context: HookContext) -> HookResult:
    enabled = os.environ.get("MECHANISM_MANIFEST_ENABLED", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    if not enabled:
        return HookResult.empty()
    return HookResult(
        context=_MANIFEST, tokens=len(_MANIFEST) // 4, priority=9.5
    )
