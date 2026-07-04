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

_MANIFEST = """## MECHANISM INVENTORY (check before proposing new gates/detectors)
Non-regex detection: epistemic_validator, semantic_critic, anti_dodge_judge
Claim gates: cross_validator, unverified_stance, fabrication_detector, cks_quality_gate
Adversarial skills: /red-team, /pre-mortem, /adversarial-review, /code-review
Search: /search, /prospect, sr MCP — before assuming something is unreachable.
Proposing a new gate/retriever? Grep this repo for an existing one first.""".strip()


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
