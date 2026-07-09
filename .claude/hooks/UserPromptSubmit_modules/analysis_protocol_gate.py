"""
Analysis Protocol Gate - UserPromptSubmit Hook
==============================================

Injects Failure Analysis Protocol (FAP) checklist when prompts signal
failure analysis, root cause investigation, or meta-level correction.

Detection: single regex layer, deliberately narrow.

History (2026-07-09): previously two-layer. Layer 2 was a semantic-daemon
path that never fired once in production (fap_layer_stats.json had no
layer2_semantic_hit key) plus a keyword-overlap fallback that fired 1671
times vs 614 regex hits -- ~73% of all firings -- tripping on ordinary
troubleshooting vocabulary ("fix", "issue", "why", "again"). Both deleted
per Replacement Default: regex captures deliberate intent; the fallback
was a stopgap that had silently become the primary path. Backup of the
old version: hooks/_archive/analysis_protocol_gate.py.bak-20260709.

Priority: 11.8 (higher than cognitive_enhancers for precedence)

Config options (cognitive_enhancers_config.json):
- analysis_protocol_gate: true - toggle for this gate
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Use os.path.realpath to avoid symlink traversal (SEC-003)
_HOOK_DIR = Path(os.path.realpath(__file__)).parent
CONFIG_PATH = _HOOK_DIR.parent / "cognitive_enhancers_config.json"

_DEFAULT_CONFIG = {
    "enabled": True,
    "analysis_protocol_gate": True,
    "min_prompt_length": 30,
}


def _load_config() -> dict:
    """Load config with defaults. Fail open on any error."""
    config = dict(_DEFAULT_CONFIG)
    try:
        if CONFIG_PATH.exists():
            user_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            config.update(user_config)
    except Exception:
        pass
    return config


# ---------------------------------------------------------------------------
# Intent detection patterns
# ---------------------------------------------------------------------------

_QUESTION_ONLY_RE = re.compile(r"^[^.!]*\?\s*$", re.MULTILINE)
_SLASH_RE = re.compile(r"^\s*/[a-z]", re.IGNORECASE)


def _extract_skill_name(prompt: str) -> str | None:
    """Extract skill name from a slash command, or None if not a slash command."""
    if not _SLASH_RE.match(prompt.strip()):
        return None
    return prompt.strip().lstrip("/").split()[0] if prompt.strip() else None


def _is_actionable_prompt(prompt: str, config: dict) -> bool:
    """Check if prompt is substantial enough to warrant cognitive injection."""
    if not prompt or len(prompt.strip()) < config.get("min_prompt_length", 30):
        return False
    stripped = prompt.strip()
    # Handle slash commands: allow unless blacklisted
    skill = _extract_skill_name(stripped)
    if skill is not None:
        if not config.get("enhance_skills", True):
            return False
        skip_list = config.get("skip_skills", [])
        if skill in skip_list:
            return False
    if _QUESTION_ONLY_RE.match(stripped):
        return False
    return True


# ---------------------------------------------------------------------------
# FAP Detection: regex patterns (sole trigger layer)
# ---------------------------------------------------------------------------

_RCA_PATTERN = re.compile(
    r"\b(root\s+cause|why\s+did\s+(?:it|this|that)\s+(?:fail|break|happen)|"
    r"what\s+caused|diagnos[ei]|post[-\s]?mortem|incident\s+review|"
    r"failure\s+analysis|bug\s+report|retrospective|investigate\s+(?:the|this|why))\b",
    re.IGNORECASE,
)

_META_PRINCIPLE_PATTERN = re.compile(
    r"\b(wrong\s+(?:level|abstraction|approach|layer)|"
    r"missing\s+(?:principle|pattern|abstraction|invariant|gap[s]?)|"
    r"broader\s+(?:principle|pattern|issue|problem)|"
    r"(?:this|the)\s+(?:fix|patch|solution)\s+(?:doesn\'t|won\'t)\s+(?:scale|generalize|hold)|"
    r"(?:should|need\s+to)\s+(?:generalize|step\s+back|zoom\s+out|think\s+bigger))\b",
    re.IGNORECASE,
)

_CORRECTION_PATTERN = re.compile(
    r"\b(you\s+(?:missed|ignored|overlooked|skipped)|"
    r"you\s+(?:removed|deleted|changed)|"
    r"did\s+you\s+just\s+remove|"
    r"without\s+(?:even\s+)?consider(?:ing|ation)|"
    r"that's\s+(?:not\s+right|wrong|incorrect|not\s+the\s+point)|"
    r"that\s+doesn't\s+(?:address|fix|solve)\s+(?:the|my)|"
    r"still\s+(?:missing|not\s+addressing|wrong)|"
    r"you\s+(?:are|were|re)\s+(?:still\s+)?(?:solving|fixing|patching)\s+the\s+wrong)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# FAP Layer Stats - firing telemetry
# ---------------------------------------------------------------------------
_FAP_STATS_FILE = _HOOK_DIR.parent / "logs" / "fap_layer_stats.json"


def _bump_fap_stat(key: str) -> None:
    """Increment a counter in fap_layer_stats.json. Fire-and-forget."""
    try:
        if not _FAP_STATS_FILE.parent.exists():
            return  # fail silently if logs dir missing (IO-003)
        stats: dict = {}
        if _FAP_STATS_FILE.exists():
            stats = json.loads(_FAP_STATS_FILE.read_text(encoding="utf-8"))
        stats[key] = stats.get(key, 0) + 1
        # Atomic write (.tmp + os.replace): a non-atomic write_text here got
        # interrupted on 2026-07-08 and left the file as truncated JSON.
        tmp = _FAP_STATS_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(stats, indent=2), encoding="utf-8")
        os.replace(tmp, _FAP_STATS_FILE)
    except Exception:
        pass  # Never fail the hook for stats


def _should_inject_fap(prompt: str, config: dict | None = None) -> bool:
    """Regex-only FAP trigger. Returns True if FAP injection should fire."""
    if not prompt or len(prompt.strip()) < 15:
        return False
    if (
        _RCA_PATTERN.search(prompt)
        or _META_PRINCIPLE_PATTERN.search(prompt)
        or _CORRECTION_PATTERN.search(prompt)
    ):
        _bump_fap_stat("layer1_regex_hit")
        return True
    return False


# ---------------------------------------------------------------------------
# FAP Injection
# ---------------------------------------------------------------------------

_FAP_INJECTION = (
    "**Failure Analysis Protocol active.**\n"
    "Before diagnosing: (1) name the specific artifact you're diagnosing from "
    "(transcript, diff, log, test output) -- if you don't have it, go get it, "
    "don't infer from a description of it. (2) For every causal claim, cite the "
    "file:line, command output, or tool-call result that supports it -- an "
    "uncited causal claim does not go in the analysis. (3) State explicitly what "
    "you did NOT check, rather than filling the gap with a plausible narrative. "
    "(4) Classify the fix as delete, source-fix, or gate, in that preference "
    "order -- a gate requires stating why the source could not be fixed "
    "directly. (5) The fix is incomplete without a test or reproducible check "
    "that would have caught the original failure."
)


# ---------------------------------------------------------------------------
# Hook registration
# ---------------------------------------------------------------------------


@register_hook("analysis_protocol_gate", priority=11.8)
def analysis_protocol_gate(context: HookContext) -> HookResult:
    """Inject FAP checklist when prompt signals failure analysis or meta-correction."""
    config = _load_config()
    if not config.get("enabled") or not config.get("analysis_protocol_gate", True):
        return HookResult.empty()
    prompt = context.prompt or ""
    if not _is_actionable_prompt(prompt, config):
        return HookResult.empty()
    if not _should_inject_fap(prompt, config):
        return HookResult.empty()
    return HookResult(
        context=_FAP_INJECTION,
        tokens=len(_FAP_INJECTION) // 4,
        priority=11.8,
    )
