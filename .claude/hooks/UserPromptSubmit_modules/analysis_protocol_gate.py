"""
Analysis Protocol Gate - UserPromptSubmit Hook
==============================================

Standalone hook extracted from cognitive_enhancers.py.
Injects Failure Analysis Protocol (FAP) checklist when prompts signal
failure analysis, root cause investigation, or meta-level correction.

Two-layer detection:
1. Regex (fast path) - matches explicit RCA/correction language
2. Semantic similarity (all-MiniLM-L6-v2) - matches FAP intent patterns

Priority: 11.8 (higher than cognitive_enhancers for precedence)

Config options (cognitive_enhancers_config.json):
- fap_semantic_enabled: true - Master toggle for semantic embeddings
- fap_similarity_threshold: 0.85 - Configurable similarity threshold
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import numpy as np
from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# ---------------------------------------------------------------------------
# Optional Semantic Daemon imports (fail open if unavailable)
# ---------------------------------------------------------------------------
try:
    # Add packages/ to path for semantic daemon client
    _PACKAGES_ROOT = Path(__file__).resolve().parents[2] / "packages"
    if str(_PACKAGES_ROOT) not in sys.path:
        sys.path.insert(0, str(_PACKAGES_ROOT))
    from search_research.contrib.semantic_daemon.daemon_client import DaemonClient

    _SEMANTIC_CLIENT_AVAILABLE = True
except Exception:
    _SEMANTIC_CLIENT_AVAILABLE = False
    DaemonClient = None  # type: ignore[assignment, misc]

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Use os.path.realpath to avoid symlink traversal (SEC-003)
_HOOK_DIR = Path(os.path.realpath(__file__)).parent
CONFIG_PATH = _HOOK_DIR.parent / "cognitive_enhancers_config.json"

_DEFAULT_CONFIG = {
    "enabled": True,
    "analysis_protocol_gate": True,
    "fap_semantic_enabled": True,
    "fap_similarity_threshold": 0.85,
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
# Intent detection patterns (extracted from cognitive_enhancers.py)
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
# FAP Detection - Layer 1: Regex patterns
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
    r"that's\s+(?:not\s+right|wrong|incorrect|not\s+the\s+point)|"
    r"that\s+doesn't\s+(?:address|fix|solve)\s+(?:the|my)|"
    r"still\s+(?:missing|not\s+addressing|wrong)|"
    r"you\s+(?:are|were|re)\s+(?:still\s+)?(?:solving|fixing|patching)\s+the\s+wrong)\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# FAP Detection - Layer 2: Concept-cluster scoring
# ---------------------------------------------------------------------------
# Replaces sentence_transformers (8.5s cold start, unusable in subprocess mode)
# with fast concept-overlap detection. Each cluster captures a FAP intent via
# related keywords. If a prompt hits enough keywords from any cluster, it
# triggers. Handles paraphrasing without exact-phrase brittleness.

_FAP_CONCEPT_CLUSTERS: list[tuple[str, set[str], int]] = [
    # (cluster_name, keyword_set, min_hits_to_trigger)
    (
        "wrong_abstraction",
        {
            "wrong",
            "level",
            "abstraction",
            "layer",
            "approach",
            "solving",
            "addressing",
            "tackling",
            "attacking",
            "surface",
            "deeper",
            "fundamental",
            "underlying",
            "symptom",
            "band-aid",
            "bandaid",
            "workaround",
            "hack",
            "incidental",
            "accidental",
            "unintended",
        },
        2,
    ),
    (
        "root_cause",
        {
            "root",
            "cause",
            "origin",
            "source",
            "reason",
            "why",
            "failure",
            "broke",
            "broken",
            "crash",
            "regression",
            "happen",
            "happened",
            "trigger",
            "actual",
            "real",
            "true",
            "fundamental",
            "diagnostic",
        },
        2,
    ),
    (
        "missing_principle",
        {
            "missing",
            "overlooking",
            "ignoring",
            "blind",
            "gap",
            "principle",
            "pattern",
            "generalize",
            "generalization",
            "broader",
            "bigger",
            "picture",
            "systemic",
            "systematic",
            "class",
            "category",
            "family",
            "type",
            "recurring",
        },
        2,
    ),
    (
        "fix_inadequacy",
        {
            "fix",
            "patch",
            "solution",
            "approach",
            "doesn't",
            "won't",
            "isn't",
            "not",
            "fails",
            "address",
            "solve",
            "resolve",
            "handle",
            "cover",
            "underlying",
            "actual",
            "real",
            "core",
            "fundamental",
            "scale",
            "hold",
            "work",
            "sufficient",
            "enough",
            "inadequate",
            "superficial",
        },
        3,
    ),  # Higher threshold — common words need more overlap
    (
        "bug_class",
        {
            "class",
            "category",
            "type",
            "kind",
            "family",
            "bug",
            "error",
            "issue",
            "problem",
            "defect",
            "other",
            "similar",
            "related",
            "instances",
            "invariant",
            "guard",
            "catch",
            "prevent",
            "detect",
            "recurring",
            "repeating",
            "again",
            "keeps",
            "always",
        },
        2,
    ),
    (
        "frustration_signal",
        {
            "circles",
            "again",
            "still",
            "keeps",
            "same",
            "already",
            "told",
            "said",
            "asked",
            "mentioned",
            "wrong",
            "broken",
            "failing",
            "not working",
            "frustrat",
            "stuck",
            "spinning",
            "going nowhere",
        },
        2,
    ),
]


def _tokenize_lower(text: str) -> set[str]:
    """Fast word-boundary tokenization to lowercase set."""
    return set(re.findall(r"[a-z']+", text.lower()))


def _concept_cluster_match(prompt: str) -> bool:
    """Check if prompt matches any FAP concept cluster above its threshold."""
    tokens = _tokenize_lower(prompt)
    if len(tokens) < 3:
        return False

    for cluster in _FAP_CONCEPT_CLUSTERS:
        keywords = cluster[1]
        min_hits = cluster[2]
        hits = len(tokens & keywords)
        if hits >= min_hits:
            return True
    return False


# ---------------------------------------------------------------------------
# FAP Detection - Layer 2 (Semantic): Cluster centroids via UnifiedSemanticDaemon
# ---------------------------------------------------------------------------

# Sample phrases per cluster — used to compute cluster centroids lazily
_CLUSTER_SAMPLES: dict[str, list[str]] = {
    "wrong_abstraction": [
        "we're solving the wrong problem",
        "that's not the real issue",
        "misaligned abstraction level",
        "at the wrong layer of abstraction",
        "focused on the wrong thing",
    ],
    "root_cause": [
        "what actually triggered this failure",
        "why did this happen",
        "what's the underlying cause",
        "trace back to the origin",
        "find the source of the problem",
    ],
    "missing_principle": [
        "we're missing a key principle",
        "overlooking something important",
        "ignoring a fundamental requirement",
        "violated the core contract",
        "failed to account for invariant",
    ],
    "fix_inadequacy": [
        "the fix doesn't really solve it",
        "patching symptoms not root cause",
        "workaround instead of solution",
        "incomplete fix",
        "the solution is insufficient",
    ],
    "bug_class": [
        "this is a class of bug",
        "category of failure",
        "type of issue we're seeing",
        "pattern of failure",
        "kind of bug",
    ],
    "frustration_signal": [
        "this keeps happening",
        "circling back to the same issue",
        "happening again and again",
        "still failing after the fix",
        "we've seen this multiple times",
    ],
}

# Lazy-computed cluster centroids (np.ndarray, 384-dim)
_CLUSTER_CENTROIDS: dict[str, np.ndarray] = {}
_CENTROIDS_COMPUTED: bool = False
_SEMANTIC_DISABLED: bool = False
_SEMANTIC_CLIENT: DaemonClient | None = None

# Configured similarity threshold (loaded lazily)
_SEMANTIC_THRESHOLD: float = 0.85


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two numpy vectors."""
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _semantic_globally_enabled(config: dict | None = None) -> bool:
    """Return True only when semantic matching is explicitly usable."""
    if DaemonClient is None:
        return False
    effective_config = config or _load_config()
    return bool(
        effective_config.get("enabled")
        and effective_config.get("analysis_protocol_gate", True)
        and effective_config.get("fap_semantic_enabled", True)
    )


def _get_semantic_client(config: dict | None = None) -> DaemonClient | None:
    """Return a ready semantic client without starting external infrastructure."""
    global _SEMANTIC_CLIENT, _SEMANTIC_DISABLED

    if _SEMANTIC_DISABLED or not _semantic_globally_enabled(config):
        return None
    if _SEMANTIC_CLIENT is not None:
        return _SEMANTIC_CLIENT

    try:
        client = DaemonClient(auto_start=False, enable_fallback=False, timeout=0.75, max_retries=0)
        is_alive = getattr(client, "is_daemon_alive", None)
        if callable(is_alive) and not is_alive(timeout=0.2):
            _SEMANTIC_DISABLED = True
            return None
        _SEMANTIC_CLIENT = client
        return client
    except Exception:
        _SEMANTIC_DISABLED = True
        return None


def _compute_cluster_centroids(config: dict | None = None) -> None:
    """Compute and cache 6 cluster centroids via IPC.

    Called once lazily on first semantic match. Each centroid = mean of
    5 phrase embeddings from _CLUSTER_SAMPLES.
    """
    global _CLUSTER_CENTROIDS, _CENTROIDS_COMPUTED, _SEMANTIC_DISABLED

    client = _get_semantic_client(config)
    if client is None:
        _CENTROIDS_COMPUTED = True
        return

    for cluster_name, phrases in _CLUSTER_SAMPLES.items():
        embeddings: list[np.ndarray] = []
        for phrase in phrases:
            try:
                result = client.query("compute_embedding", {"text": phrase}, timeout=0.35)
                emb_list = result.get("result", {}).get("embedding")
                if emb_list:
                    embeddings.append(np.array(emb_list, dtype=np.float32))
            except Exception:
                _SEMANTIC_DISABLED = True
                _CLUSTER_CENTROIDS = {}
                _CENTROIDS_COMPUTED = True
                return
        if embeddings:
            _CLUSTER_CENTROIDS[cluster_name] = np.mean(embeddings, axis=0)
        else:
            # Zero centroid — will never match above threshold
            _CLUSTER_CENTROIDS[cluster_name] = np.zeros(384, dtype=np.float32)

    _CENTROIDS_COMPUTED = True


def _get_embedding(prompt: str, config: dict | None = None) -> np.ndarray | None:
    """Get embedding vector for prompt via SemanticDaemon.

    Returns np.ndarray (384-dim) on success, None on failure.
    """
    global _SEMANTIC_DISABLED

    client = _get_semantic_client(config)
    if client is None:
        return None

    try:
        result = client.query("compute_embedding", {"text": prompt}, timeout=0.35)
        emb_list = result.get("result", {}).get("embedding")
        if emb_list:
            return np.array(emb_list, dtype=np.float32)
    except Exception:
        _SEMANTIC_DISABLED = True
    return None


def _semantic_match(prompt: str, config: dict | None = None) -> str | None:
    """Check if prompt matches any FAP concept cluster via semantic similarity.

    Uses cosine similarity against pre-computed cluster centroids.
    Returns cluster name if best score >= _SEMANTIC_THRESHOLD, else None.
    Falls back to keyword matching if daemon unavailable.
    """
    global _CENTROIDS_COMPUTED, _SEMANTIC_THRESHOLD, _CLUSTER_CENTROIDS

    if not _semantic_globally_enabled(config):
        return None

    # Lazy centroid computation
    if not _CENTROIDS_COMPUTED:
        if config:
            try:
                _SEMANTIC_THRESHOLD = float(
                    config.get("fap_similarity_threshold", _SEMANTIC_THRESHOLD)
                )
            except Exception:
                pass
        _compute_cluster_centroids(config)

    # If centroids still empty (daemon unavailable), skip semantic path
    if not _CLUSTER_CENTROIDS:
        return None

    emb = _get_embedding(prompt, config)
    if emb is None:
        return None  # fallback to keyword

    best_cluster: str | None = None
    best_score: float = -1.0
    for cluster_name, centroid in _CLUSTER_CENTROIDS.items():
        score = cosine_similarity(emb, centroid)
        if score > best_score:
            best_cluster, best_score = cluster_name, score

    if best_score >= _SEMANTIC_THRESHOLD:
        return best_cluster
    return None


# ---------------------------------------------------------------------------
# FAP Layer Stats - tracks regex vs semantic hit rates
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
        _FAP_STATS_FILE.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    except Exception:
        pass  # Never fail the hook for stats


def _should_inject_fap(prompt: str, config: dict | None = None) -> bool:
    """Two-layer FAP trigger. Returns True if FAP injection should fire."""
    config = config or _load_config()
    if not prompt or len(prompt.strip()) < 15:
        return False

    # Layer 1: Regex fast path
    if (
        _RCA_PATTERN.search(prompt)
        or _META_PRINCIPLE_PATTERN.search(prompt)
        or _CORRECTION_PATTERN.search(prompt)
    ):
        _bump_fap_stat("layer1_regex_hit")
        return True

    # Layer 2: semantic / concept matching, behind one config gate.
    if config.get("fap_semantic_enabled", True):
        if _semantic_match(prompt, config) is not None:
            _bump_fap_stat("layer2_semantic_hit")
            return True
        if _concept_cluster_match(prompt):
            _bump_fap_stat("layer2_keyword_fallback")
            return True
    return False


# ---------------------------------------------------------------------------
# FAP Injection
# ---------------------------------------------------------------------------

_FAP_INJECTION = (
    "**Failure Analysis Protocol active.**\n"
    "Before diagnosing: (1) lock scope to the specific instance, (2) confirm you "
    "have the artifact (don't proceed on descriptions), (3) build a 3-hop causal chain, "
    "(4) generalization scan — name ≥1 other system sharing this failure class, "
    "(5) classify fixes S/D/R, (6) design the failure path (degradation marker), "
    "(7) codification gate — fix is incomplete without a test invariant.\n"
    "Full protocol: P:/docs/failure-analysis-protocol.md"
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
