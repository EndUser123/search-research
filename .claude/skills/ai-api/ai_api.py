#!/usr/bin/env python3
"""
LLM API - Multi-Provider LLM Access with Dynamic Discovery

Implements:
- Dynamic model discovery via litellm
- Task-based routing to appropriate models
- Domain-based routing using dynamic model router (quality-first)
- Performance tracking for curation
- Four modes: chill (fast), mid (standard), chad (comprehensive), adaptive (auto-stops at convergence)
"""

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add proxy litellm venv to path for litellm package
PROXY_DIR = Path(__file__).parent / "proxy" / "litellm_venv" / "Lib" / "site-packages"
sys.path.insert(0, str(PROXY_DIR))

# Add CSF src to path for dynamic model router
CSF_SRC = Path(__file__).parent.parent.parent.parent / "__csf" / "src"
if CSF_SRC.exists():
    sys.path.insert(0, str(CSF_SRC))

try:
    from litellm import acompletion
except ImportError:
    print("ERROR: litellm not installed. Run: pip install litellm")
    sys.exit(1)

# Import dynamic model router for domain-based routing
try:
    from src.csf.llm_providers.dynamic_model_router import Domain, get_router

    DYNAMIC_ROUTER_AVAILABLE = True
except ImportError:
    DYNAMIC_ROUTER_AVAILABLE = False
    print("[WARNING] Dynamic router not available, using default model selection")


# ============================================================================
# Configuration
# ============================================================================

MODELS_CACHE_PATH = Path.home() / ".claude" / "llm-api-models.json"
PERFORMANCE_LOG_PATH = Path.home() / ".claude" / "llm-api-performance.jsonl"
MODEL_HEALTH_PATH = Path.home() / ".claude" / "llm-api-health.json"
CACHE_EXPIRY_HOURS = 24


# ============================================================================
# Task Classification
# ============================================================================


@dataclass
class TaskClassification:
    task_type: str
    confidence: float
    matched_keywords: list[str]


def classify_task(query: str) -> TaskClassification:
    """Classify query into task type for routing."""
    query_lower = query.lower()

    TASK_PATTERNS = {
        "code_review": ["review", "audit", "analyze", "inspect", "examine"],
        "debug": ["debug", "fix", "error", "bug", "issue"],
        "implement": ["implement", "create", "write", "build", "add"],
        "refactor": ["refactor", "improve", "optimize", "clean"],
        "explain": ["explain", "describe", "how", "what", "why"],
        "plan": ["plan", "design", "architecture", "strategy"],
        "test": ["test", "verify", "validate", "check"],
    }

    matched = {}
    for task_type, keywords in TASK_PATTERNS.items():
        matches = [kw for kw in keywords if kw in query_lower]
        if matches:
            matched[task_type] = len(matches)

    if not matched:
        return TaskClassification(task_type="general", confidence=0.0, matched_keywords=[])

    # Return task type with most keyword matches
    best_task = max(matched, key=matched.get)
    confidence = min(1.0, matched[best_task] * 0.2)
    matched_keywords = [kw for kw in TASK_PATTERNS[best_task] if kw in query_lower]

    return TaskClassification(
        task_type=best_task, confidence=confidence, matched_keywords=matched_keywords
    )


# ============================================================================
# Model Catalog
# ============================================================================


@dataclass
class ModelInfo:
    provider: str
    model_name: str
    context_window: int
    input_price: float  # per 1M tokens
    output_price: float  # per 1M tokens
    categories: list[str]
    tier: int  # 1=Proven, 2=Promising, 3=Experimental
    api_base: str = ""  # For custom API endpoints (e.g., Chutes)
    custom_llm_provider: str = ""  # For custom providers (e.g., "openai" for Chutes)


# ============================================================================
# Model Health Tracking
# ============================================================================


class ModelHealthTracker:
    """Track model health to avoid repeatedly failing models."""

    # Provider priority for fallback (higher = more preferred)
    PROVIDER_PRIORITY = {
        "groq": 100,
        "chutes": 80,
        "openrouter": 50,
        "openai": 90,
        "anthropic": 90,
        "google": 85,
    }

    def __init__(self, health_path: Path = MODEL_HEALTH_PATH):
        self.health_path = health_path
        self.unhealthy_models: dict[str, dict] = {}  # model_id -> {reason, last_failed, fail_count}
        self._load_health()

    def _load_health(self):
        """Load health status from disk."""
        if not self.health_path.exists():
            return

        try:
            with open(self.health_path) as f:
                data = json.load(f)
                self.unhealthy_models = data.get("unhealthy", {})
            print(f"[ModelHealth] Loaded {len(self.unhealthy_models)} unhealthy models")
        except Exception as e:
            print(f"[ModelHealth] Failed to load health data: {e}")

    def _save_health(self):
        """Save health status to disk."""
        try:
            self.health_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.health_path, "w") as f:
                json.dump({"unhealthy": self.unhealthy_models}, f, indent=2)
        except Exception as e:
            print(f"[ModelHealth] Failed to save health data: {e}")

    def mark_success(self, model_id: str):
        """Mark model as healthy (remove from unhealthy list if present)."""
        if model_id in self.unhealthy_models:
            del self.unhealthy_models[model_id]
            self._save_health()
            print(f"[ModelHealth] ✓ {model_id} recovered (removed from unhealthy list)")

    def mark_failure(self, model_id: str, reason: str, permanent: bool = False):
        """Mark model as unhealthy.

        Args:
            model_id: Model that failed
            reason: Error message
            permanent: If True, model won't be auto-retried (e.g., decommissioned)
        """
        self.unhealthy_models[model_id] = {
            "reason": reason,
            "last_failed": datetime.now().isoformat(),
            "fail_count": self.unhealthy_models.get(model_id, {}).get("fail_count", 0) + 1,
            "permanent": permanent,
        }
        self._save_health()
        status = "PERMANENT" if permanent else "temporary"
        print(f"[ModelHealth] ✗ {model_id} marked unhealthy ({status}): {reason[:80]}")

    def is_healthy(self, model_id: str) -> bool:
        """Check if model is healthy."""
        if model_id not in self.unhealthy_models:
            return True

        # Auto-retry temporary failures after 24 hours
        health_data = self.unhealthy_models[model_id]
        if not health_data.get("permanent", False):
            last_failed = datetime.fromisoformat(health_data["last_failed"])
            if datetime.now() - last_failed > timedelta(hours=24):
                print(f"[ModelHealth] Retrying {model_id} after 24h cooldown")
                del self.unhealthy_models[model_id]
                self._save_health()
                return True

        return False

    def get_provider_priority(self, model_id: str) -> int:
        """Get priority score for model's provider."""
        # Extract provider from model_id
        for provider, priority in self.PROVIDER_PRIORITY.items():
            if provider in model_id.lower():
                return priority
        return 10  # Default low priority for unknown providers


# Global health tracker instance
_health_tracker: ModelHealthTracker | None = None


def get_health_tracker() -> ModelHealthTracker:
    """Get singleton health tracker instance."""
    global _health_tracker
    if _health_tracker is None:
        _health_tracker = ModelHealthTracker()
    return _health_tracker


# ============================================================================
# Model Catalog
# ============================================================================


class ModelCatalog:
    """Dynamic model catalog with caching."""

    def __init__(self, cache_path: Path = MODELS_CACHE_PATH):
        self.cache_path = cache_path
        self.models: dict[str, ModelInfo] = {}
        self.health = get_health_tracker()
        self._load_cache()

    def _load_cache(self):
        """Load cached model list if fresh."""
        if not self.cache_path.exists():
            return

        try:
            cache_age = datetime.now() - datetime.fromtimestamp(self.cache_path.stat().st_mtime)
            if cache_age < timedelta(hours=CACHE_EXPIRY_HOURS):
                with open(self.cache_path) as f:
                    data = json.load(f)
                    for model_id, model_data in data.items():
                        self.models[model_id] = ModelInfo(**model_data)
                print(
                    f"[ModelCatalog] Loaded {len(self.models)} models from cache ({cache_age.seconds // 60} minutes old)"
                )
        except Exception as e:
            print(f"[ModelCatalog] Failed to load cache: {e}")

    def _save_cache(self):
        """Save model catalog to cache."""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_path, "w") as f:
                json.dump(
                    {model_id: asdict(model_info) for model_id, model_info in self.models.items()},
                    f,
                    indent=2,
                )
        except Exception as e:
            print(f"[ModelCatalog] Failed to save cache: {e}")

    async def discover_models(self, refresh: bool = False) -> int:
        """Discover available models from providers."""
        if self.models and not refresh:
            return len(self.models)

        print("[ModelCatalog] Discovering models from providers...")

        # Try to load models from litellm config
        models_from_config = self._load_models_from_litellm_config()

        if models_from_config:
            self.models = models_from_config
        else:
            # Fallback to curated list based on litellm supported providers
            curated_models = {
                # Tier 1: Proven models
                "openai/gpt-4o": ModelInfo(
                    provider="openai",
                    model_name="gpt-4o",
                    context_window=128000,
                    input_price=2.5,
                    output_price=10.0,
                    categories=["code_review", "implement", "debug", "explain"],
                    tier=1,
                ),
                "anthropic/claude-sonnet-4-20250514": ModelInfo(
                    provider="anthropic",
                    model_name="claude-sonnet-4-20250514",
                    context_window=200000,
                    input_price=3.0,
                    output_price=15.0,
                    categories=["code_review", "plan", "explain", "refactor"],
                    tier=1,
                ),
                # Tier 2: Promising models
                "deepseek/deepseek-chat": ModelInfo(
                    provider="deepseek",
                    model_name="deepseek-chat",
                    context_window=128000,
                    input_price=0.14,
                    output_price=0.28,
                    categories=["implement", "debug", "explain"],
                    tier=2,
                ),
                "google/gemini-2.0-flash-exp": ModelInfo(
                    provider="google",
                    model_name="gemini-2.0-flash-exp",
                    context_window=1000000,
                    input_price=0.0,
                    output_price=0.0,
                    categories=["explain", "plan", "large_context"],
                    tier=2,
                ),
                "groq/llama-3.3-70b-versatile": ModelInfo(
                    provider="groq",
                    model_name="llama-3.3-70b-versatile",
                    context_window=128000,
                    input_price=0.0,
                    output_price=0.0,
                    categories=["code_review", "debug", "implement", "explain"],
                    tier=2,
                ),
                "groq/mixtral-8x7b-32768": ModelInfo(
                    provider="groq",
                    model_name="mixtral-8x7b-32768",
                    context_window=32768,
                    input_price=0.0,
                    output_price=0.0,
                    categories=["code_review", "debug"],
                    tier=2,
                ),
            }
            self.models = curated_models

        self._save_cache()
        print(f"[ModelCatalog] Discovered {len(self.models)} models")
        return len(self.models)

    def _load_models_from_litellm_config(self) -> dict[str, ModelInfo] | None:
        """Load models from litellm config YAML file."""
        import yaml

        # Try multiple path options (config now in skill-local proxy directory)
        config_paths = [
            Path(__file__).parent / "proxy" / "START_litellm_config.yaml",
            Path.home() / ".claude" / "skills" / "ai-api" / "proxy" / "START_litellm_config.yaml",
            Path("P:/").resolve()
            / ".claude"
            / "skills"
            / "ai-api"
            / "proxy"
            / "START_litellm_config.yaml",
        ]

        config_path = None
        for p in config_paths:
            if p.exists():
                config_path = p
                break

        if not config_path:
            print("[ModelCatalog] litellm config not found at any expected location")
            return None

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)

            if not config or "model_list" not in config:
                return None

            models = {}
            for model_config in config["model_list"]:
                model_name = model_config.get("model_name", "")
                litellm_params = model_config.get("litellm_params", {})
                litellm_model = litellm_params.get("model", "")
                api_base = litellm_params.get("api_base", "")

                # Use litellm_model as the model_id since it has the provider prefix
                model_id = litellm_model if litellm_model else model_name

                # Determine provider and tier
                if "openrouter" in litellm_model.lower():
                    provider = "openrouter"
                    tier = 2
                elif "chutes" in api_base.lower() or api_base.endswith("chutes.ai/v1"):
                    provider = "chutes"
                    tier = 2
                elif "groq" in litellm_model.lower():
                    provider = "groq"
                    tier = 2
                else:
                    provider = "unknown"
                    tier = 3

                # Map model to categories based on name patterns
                categories = ["general"]
                model_lower = model_name.lower()
                if any(x in model_lower for x in ["coder", "code", "dev", "kimi", "deepseek"]):
                    categories.extend(["implement", "debug", "code_review"])
                if any(x in model_lower for x in ["chat", "instruct", "nova"]):
                    categories.append("explain")

                models[model_id] = ModelInfo(
                    provider=provider,
                    model_name=model_id,  # Use the full litellm model name
                    context_window=128000,  # Default assumption
                    input_price=0.0,  # Will be updated from pricing data
                    output_price=0.0,
                    categories=categories,
                    tier=tier,
                    api_base=api_base,
                    custom_llm_provider=litellm_params.get("custom_llm_provider", ""),
                )

            return models

        except Exception as e:
            print(f"[ModelCatalog] Failed to load litellm config: {e}")
            return None

    def select_models(self, task_type: str, mode: str, max_models: int = 3) -> list[str]:
        """Select appropriate models for task and mode."""
        # Mode determines how many models
        mode_limits = {"chill": 1, "mid": 2, "chad": 3}
        limit = min(max_models, mode_limits.get(mode, 2))

        # Filter by task type AND health
        candidates = [
            (model_id, model_info)
            for model_id, model_info in self.models.items()
            if (task_type in model_info.categories or "general" in model_info.categories)
            and self.health.is_healthy(model_id)  # Exclude unhealthy models
        ]

        # Sort by: provider priority (reliable first), then tier, then cost
        candidates.sort(
            key=lambda x: (
                -self.health.get_provider_priority(x[0]),  # Higher priority first
                x[1].tier,  # Lower tier number first (T1 > T2 > T3)
                x[1].input_price,  # Lower cost first
            )
        )

        selected = [model_id for model_id, _ in candidates[:limit]]
        if not selected:
            print(f"[ModelCatalog] WARNING: No healthy models available for {task_type}/{mode}")
            print(
                f"[ModelCatalog] Total models: {len(self.models)}, Unhealthy: {len(self.health.unhealthy_models)}"
            )
        else:
            print(
                f"[ModelCatalog] Selected {len(selected)} models for {task_type}/{mode}: {selected}"
            )
        return selected


# ============================================================================
# Performance Tracking
# ============================================================================


@dataclass
class PerformanceRecord:
    model_id: str
    task_type: str
    query_preview: str
    duration_seconds: float
    outcome: str  # success, timeout, error, empty_output
    output_length: int
    timestamp: str
    error_message: str | None = None
    unique_finding_count: int = 0
    dedup_ratio: float = 0.0


class PerformanceTracker:
    """Track model performance for curation."""

    def __init__(self, log_path: Path = PERFORMANCE_LOG_PATH):
        self.log_path = log_path
        self.records: list[PerformanceRecord] = []
        self._load_records()

    def _load_records(self):
        """Load existing performance records."""
        if not self.log_path.exists():
            return

        try:
            with open(self.log_path) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.records.append(PerformanceRecord(**data))
        except Exception as e:
            print(f"[PerformanceTracker] Failed to load records: {e}")

    def log_execution(
        self,
        model_id: str,
        task_type: str,
        query: str,
        duration: float,
        outcome: str,
        output_length: int,
        error: str | None = None,
        unique_finding_count: int = 0,
        dedup_ratio: float = 0.0,
    ):
        """Log a model execution."""
        record = PerformanceRecord(
            model_id=model_id,
            task_type=task_type,
            query_preview=query[:100],
            duration_seconds=duration,
            outcome=outcome,
            output_length=output_length,
            timestamp=datetime.now().isoformat(),
            error_message=error,
            unique_finding_count=unique_finding_count,
            dedup_ratio=dedup_ratio,
        )

        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a") as f:
                f.write(json.dumps(asdict(record)) + "\n")
            self.records.append(record)
        except Exception as e:
            print(f"[PerformanceTracker] Failed to log execution: {e}")

    def get_model_stats(self, model_id: str, task_type: str) -> dict[str, Any]:
        """Get performance stats for a model."""
        model_records = [
            r for r in self.records if r.model_id == model_id and r.task_type == task_type
        ]

        if not model_records:
            return {"total_executions": 0}

        successful = [r for r in model_records if r.outcome == "success"]
        return {
            "total_executions": len(model_records),
            "success_rate": len(successful) / len(model_records),
            "avg_duration": sum(r.duration_seconds for r in successful) / len(successful)
            if successful
            else 0,
            "avg_output_length": sum(r.output_length for r in successful) / len(successful)
            if successful
            else 0,
        }


# ============================================================================
# Rule-Based Routing (from llm-route)
# ============================================================================


@dataclass
class RoutingRule:
    """Routing rule for task type to provider mapping."""

    task_type: str
    keywords: list[str]
    preferred_provider: str
    description: str


# Routing rules from llm-route (manually defined, not learned)
ROUTING_RULES = [
    RoutingRule(
        task_type="coding",
        keywords=["api", "function", "code", "implement", "refactor"],
        preferred_provider="openrouter",
        description="OpenRouter DeepSeek R1T2 Chimera",
    ),
    RoutingRule(
        task_type="planning",
        keywords=["plan", "strategy", "roadmap", "architecture"],
        preferred_provider="chutes",
        description="Chutes Hermes 4 70B",
    ),
    RoutingRule(
        task_type="creative",
        keywords=["story", "write", "content", "creative"],
        preferred_provider="chutes",
        description="Chutes Hermes 4 70B",
    ),
    RoutingRule(
        task_type="analysis",
        keywords=["analyze", "compare", "evaluate"],
        preferred_provider="chutes",
        description="Chutes Qwen3 235B",
    ),
    RoutingRule(
        task_type="large_context",
        keywords=["whole codebase", "entire project", "all files", "large context"],
        preferred_provider="gemini-cli",
        description="Google Gemini CLI (1M+ tokens)",
    ),
]


def route_by_rules(query: str, available_models: dict[str, ModelInfo]) -> list[str]:
    """Route query to appropriate models using rule-based keyword matching.

    This is the routing logic from llm-route - simple keyword pattern matching
    without learning or telemetry. Used as alternative to smart selection.

    Args:
        query: User query text
        available_models: Dictionary of model_id -> ModelInfo

    Returns:
        List of model IDs that match the routing rules (empty if no match)
    """
    query_lower = query.lower()

    # Find matching routing rules
    matched_rules = []
    for rule in ROUTING_RULES:
        if any(keyword in query_lower for keyword in rule.keywords):
            matched_rules.append(rule)

    if not matched_rules:
        return []

    # For each matched rule, find models from the preferred provider
    selected_models = []
    for rule in matched_rules[:2]:  # Limit to top 2 matching rules
        provider = rule.preferred_provider

        # Find models from this provider
        provider_models = [
            model_id
            for model_id, model_info in available_models.items()
            if model_info.provider == provider
        ]

        # Select up to 2 models from this provider
        # Prefer tier 1 (proven), then tier 2, then tier 3
        provider_models.sort(key=lambda mid: available_models[mid].tier)

        selected_models.extend(provider_models[:2])

        print(f"[Route] Rule '{rule.task_type}' → {provider} ({rule.description})")

    return selected_models[:3]  # Limit to 3 total models


# ============================================================================
# Main API
# ============================================================================


async def run_llm_review(
    query: str,
    context: str | None = None,
    mode: str = "mid",
    domain: str | None = None,
    refresh_benchmarks: bool = False,
) -> dict[str, Any]:
    """Run LLM review across selected models.

    Modes:
    - chill: 1 model (fastest)
    - mid: 2 models (standard)
    - chad: 3 models (comprehensive)
    - adaptive: 2-6 models with auto-stopping at finding convergence
    - route: Rule-based routing using keyword patterns (from llm-route)

    Domain (optional): Use dynamic model router for quality-first model selection
    - code_generation: Best models for writing code
    - code_review: Best models for analyzing code
    - architecture: Best models for design decisions
    - testing: Best models for generating tests
    - documentation: Best models for writing docs
    - debugging: Best models for finding bugs
    """

    # Classify task
    classification = classify_task(query)
    print(
        f"\n[LLM-API] Task: {classification.task_type} (confidence: {classification.confidence:.0%})"
    )

    # Domain-based routing using dynamic router
    if domain and DYNAMIC_ROUTER_AVAILABLE:
        return await _run_domain_review(domain, query, context, mode, refresh_benchmarks)

    # Discover models
    catalog = ModelCatalog()
    await catalog.discover_models(refresh=False)

    # Build prompt
    prompt = query
    if context:
        prompt = f"--- Context ---\n{context}\n\n--- Question ---\n{query}"

    # Route mode: use rule-based routing
    if mode == "route":
        return await _run_route_review(catalog, prompt, query)
    # Adaptive mode: run models iteratively until convergence
    elif mode == "adaptive":
        return await _run_adaptive_review(catalog, classification.task_type, prompt, query)
    else:
        return await _run_fixed_review(catalog, classification.task_type, mode, prompt, query)


async def _run_domain_review(
    domain: str, query: str, context: str | None, _mode: str, refresh_benchmarks: bool = False
) -> dict[str, Any]:
    """Run review using dynamic model router for domain-based model selection.

    Uses quality-first routing from actual provider data instead of hardcoded models.
    """
    import os

    from dotenv import load_dotenv

    # Load API keys
    load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / "__csf" / ".env")

    # Map domain string to Domain enum
    domain_map = {
        "code_generation": Domain.CODE_GENERATION,
        "code_review": Domain.CODE_REVIEW,
        "architecture": Domain.ARCHITECTURE,
        "testing": Domain.TESTING,
        "documentation": Domain.DOCUMENTATION,
        "debugging": Domain.DEBUGGING,
    }

    if domain not in domain_map:
        return {"error": f"Unknown domain: {domain}", "findings": [], "mode": "domain"}

    domain_enum = domain_map[domain]

    print(f"\n[Domain Router] Using dynamic router for domain: {domain}")
    print("[Domain Router] Fetching current models from providers...")

    try:
        # Get router with fresh data
        router = await get_router(
            groq_key=os.getenv("GROQ_API_KEY"),
            chutes_key=os.getenv("CHUTES_API_KEY"),
            openrouter_key=os.getenv("OpenRouterKey"),
            refresh_benchmarks=refresh_benchmarks,
        )

        # Get best model for domain
        model_info = router.get_best_model(domain_enum, preference="primary")

        if not model_info:
            return {
                "error": f"No models available for domain: {domain}",
                "findings": [],
                "mode": "domain",
            }

        # Display model selection with both benchmark and local data
        router.display_model_selection_with_both_sources(domain_enum, query)

        # Ask for user confirmation
        print()
        response = input("Continue with recommended model? (Y/n): ").strip().lower()
        if response and response != "y":
            return {
                "error": "User cancelled",
                "findings": [],
                "mode": "domain",
                "domain": domain,
                "cancelled": True,
            }

        print()  # Spacing before execution output

        # Build prompt
        prompt = query
        if context:
            prompt = f"--- Context ---\n{context}\n\n--- Question ---\n{query}"

        # Run with selected model
        tracker = PerformanceTracker()

        import time

        start_time = time.time()

        # Execute model
        result = await execute_model(
            model_info.id,
            prompt,
            domain,  # Use domain as task_type
            tracker,
        )

        duration = time.time() - start_time

        # Process result
        if isinstance(result, Exception):
            tracker.log_execution(model_info.id, domain, query, 0, "error", 0, str(result))
            return {
                "error": str(result),
                "findings": [],
                "mode": "domain",
                "domain": domain,
                "model": model_info.id,
            }

        findings = [
            {
                "model": model_info.id,
                "content": result["content"],
                "duration": result["duration"],
                "outcome": result["outcome"],
            }
        ]

        # Log performance
        if result["outcome"] == "success":
            tracker.log_execution(
                model_info.id, domain, query, result["duration"], "success", len(result["content"])
            )
        else:
            tracker.log_execution(
                model_info.id,
                domain,
                query,
                result["duration"],
                result["outcome"],
                len(result.get("content", "")),
                result.get("error"),
            )

        return {
            "findings": findings,
            "mode": "domain",
            "domain": domain,
            "task_type": domain,
            "model_used": model_info.id,
            "model_provider": model_info.provider,
            "duration": duration,
            "total_requested": 1,
            "total_completed": 1 if result["outcome"] == "success" else 0,
        }

    except Exception as e:
        return {
            "error": f"Domain routing failed: {e}",
            "findings": [],
            "mode": "domain",
            "domain": domain,
        }


async def _run_route_review(catalog: ModelCatalog, prompt: str, query: str) -> dict[str, Any]:
    """Run review using rule-based routing (from llm-route)."""

    print("\n[Route] Using rule-based routing...")

    # Get available models
    available_models = catalog.models

    # Route using keyword rules
    routed_models = route_by_rules(query, available_models)

    if not routed_models:
        print("[Route] No routing rules matched, falling back to default selection")
        # Fallback to smart selection
        classification = classify_task(query)
        routed_models = catalog.select_models(classification.task_type, "mid")

    if not routed_models:
        return {"error": "No models available for routing", "findings": [], "mode": "route"}

    # Run selected models
    tracker = PerformanceTracker()
    task_type = classify_task(query).task_type

    tasks = [
        execute_model(model_id, prompt, task_type, tracker)
        for model_id in routed_models[:3]  # Limit to 3 models
    ]

    import time

    start_time = time.time()
    completed = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start_time

    # Process results
    findings = []
    for model_id, result in zip(routed_models, completed, strict=True):
        if isinstance(result, Exception):
            print(f"[LLM-API] {model_id} error: {result}")
            tracker.log_execution(model_id, task_type, query, 0, "error", 0, str(result))
        else:
            findings.append(
                {
                    "model": model_id,
                    "content": result["content"],
                    "duration": result["duration"],
                    "outcome": result["outcome"],
                }
            )

    # Deduplicate and track metrics
    all_findings, dedup_metrics = _deduplicate_findings(findings)

    for finding in findings:
        if finding["outcome"] == "success":
            tracker.log_execution(
                finding["model"],
                task_type,
                query,
                finding["duration"],
                "success",
                len(finding["content"]),
                unique_finding_count=dedup_metrics["unique_findings"],
            )

    return {
        "findings": all_findings,
        "dedup_metrics": dedup_metrics,
        "mode": "route",
        "task_type": task_type,
        "models_routed": routed_models[:3],
        "duration": duration,
        "total_requested": len(routed_models[:3]),
        "total_completed": len([f for f in findings if f["outcome"] == "success"]),
    }


async def _run_fixed_review(
    catalog: ModelCatalog, task_type: str, mode: str, prompt: str, query: str
) -> dict[str, Any]:
    """Run review with fixed number of models (chill/mid/chad modes)."""

    # Select models
    model_ids = catalog.select_models(task_type, mode)
    if not model_ids:
        return {"error": "No models available", "findings": [], "mode": mode}

    # Run models in parallel
    tracker = PerformanceTracker()

    tasks = [execute_model(model_id, prompt, task_type, tracker) for model_id in model_ids]

    import time

    start_time = time.time()
    completed = await asyncio.gather(*tasks, return_exceptions=True)
    duration = time.time() - start_time

    # Process results
    findings = []
    for model_id, result in zip(model_ids, completed, strict=True):
        if isinstance(result, Exception):
            print(f"[LLM-API] {model_id} error: {result}")
            tracker.log_execution(model_id, task_type, query, 0, "error", 0, str(result))
        else:
            findings.append(
                {
                    "model": model_id,
                    "content": result["content"],
                    "duration": result["duration"],
                    "outcome": result["outcome"],
                }
            )

    # Deduplicate and track metrics
    all_findings, dedup_metrics = _deduplicate_findings(findings)

    # Log dedup metrics for each model
    for finding in findings:
        if finding["outcome"] == "success":
            tracker.log_execution(
                finding["model"],
                task_type,
                query,
                finding["duration"],
                "success",
                len(finding["content"]),
                unique_finding_count=dedup_metrics["unique_findings"],
                dedup_ratio=dedup_metrics["dedup_ratio"],
            )

    # Sort by priority (P0 > P1 > P2 > P3)
    all_findings.sort(key=lambda f: _extract_priority(f["content"]))

    return {
        "task_type": task_type,
        "mode": mode,
        "models_tested": len(model_ids),
        "findings": all_findings,
        "total_duration": duration,
        "dedup_metrics": dedup_metrics,
    }


async def _run_adaptive_review(
    catalog: ModelCatalog, task_type: str, prompt: str, query: str
) -> dict[str, Any]:
    """Run adaptive review with iterative model addition based on finding convergence."""

    # Convergence thresholds
    MIN_MODELS = 2  # Start with 2 models
    MAX_MODELS = 6  # Safety cap
    CONVERGENCE_THRESHOLD = 0.20  # Stop if last 2 models each added < 20% unique findings

    tracker = PerformanceTracker()
    import time

    start_time = time.time()

    # Get all available models for this task (sorted by tier/cost)
    all_candidates = [
        (model_id, model_info)
        for model_id, model_info in catalog.models.items()
        if task_type in model_info.categories or "general" in model_info.categories
    ]
    all_candidates.sort(key=lambda x: (x[1].tier, x[1].input_price))

    if not all_candidates:
        return {"error": "No models available", "findings": [], "mode": "adaptive"}

    all_model_ids = [model_id for model_id, _ in all_candidates]

    # Start with MIN_MODELS
    models_to_test = min(MIN_MODELS, len(all_model_ids))
    findings_so_far = []
    models_tested = []
    unique_counts_history = []  # Track unique finding count per iteration

    iteration = 0
    converged = False

    while models_to_test <= len(all_model_ids) and len(models_tested) < MAX_MODELS:
        iteration += 1
        iteration_models = all_model_ids[len(models_tested) : models_to_test]

        print(
            f"[Adaptive Mode] Iteration {iteration}: Testing {len(iteration_models)} models: {iteration_models}"
        )

        # Run this iteration's models
        tasks = [
            execute_model(model_id, prompt, task_type, tracker) for model_id in iteration_models
        ]

        completed = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        iteration_findings = []
        for model_id, result in zip(iteration_models, completed, strict=True):
            models_tested.append(model_id)

            if isinstance(result, Exception):
                print(f"[LLM-API] {model_id} error: {result}")
                tracker.log_execution(model_id, task_type, query, 0, "error", 0, str(result))
            else:
                iteration_findings.append(
                    {
                        "model": model_id,
                        "content": result["content"],
                        "duration": result["duration"],
                        "outcome": result["outcome"],
                    }
                )

        findings_so_far.extend(iteration_findings)

        # Deduplicate all findings so far
        all_findings, dedup_metrics = _deduplicate_findings(findings_so_far)
        unique_count = dedup_metrics["unique_findings"]
        unique_counts_history.append(unique_count)

        # Log metrics for successful models
        for finding in iteration_findings:
            if finding["outcome"] == "success":
                tracker.log_execution(
                    finding["model"],
                    task_type,
                    query,
                    finding["duration"],
                    "success",
                    len(finding["content"]),
                    unique_finding_count=unique_count,
                    dedup_ratio=dedup_metrics["dedup_ratio"],
                )

        print(
            f"[Adaptive Mode] Iteration {iteration} complete: {unique_count} unique findings "
            f"(dedup ratio: {dedup_metrics['dedup_ratio']:.0%})"
        )

        # Check convergence (need at least 2 iterations)
        if len(unique_counts_history) >= 2:
            # Calculate how many NEW unique findings this iteration added
            prev_unique = unique_counts_history[-2]
            curr_unique = unique_counts_history[-1]
            new_unique_ratio = (curr_unique - prev_unique) / max(prev_unique, 1)

            print(
                f"[Adaptive Mode] New unique findings this iteration: {curr_unique - prev_unique} "
                f"({new_unique_ratio:.0%} increase)"
            )

            # Check if last iteration added enough value
            if new_unique_ratio < CONVERGENCE_THRESHOLD:
                print(
                    f"[Adaptive Mode] Convergence detected: only {new_unique_ratio:.0%} new unique findings"
                )
                converged = True
                break

        # Add another model for next iteration
        models_to_test += 1

    duration = time.time() - start_time

    # Sort by priority (P0 > P1 > P2 > P3)
    all_findings.sort(key=lambda f: _extract_priority(f["content"]))

    return {
        "task_type": task_type,
        "mode": "adaptive",
        "models_tested": len(models_tested),
        "findings": all_findings,
        "total_duration": duration,
        "dedup_metrics": dedup_metrics,
        "converged": converged,
        "iterations": iteration,
    }


async def execute_model(
    model_id: str, prompt: str, task_type: str, tracker: PerformanceTracker
) -> dict[str, Any]:
    """Execute a single model."""
    import time

    start = time.time()

    # Get model info and health tracker
    catalog = ModelCatalog()
    health = get_health_tracker()
    if catalog.models and model_id in catalog.models:
        model_info = catalog.models[model_id]
    else:
        model_info = None

    try:
        # Prepare acompletion parameters
        acompletion_params = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "timeout": 30.0,
        }

        # Add Chutes-specific parameters if needed
        if model_info and model_info.api_base:
            acompletion_params["api_base"] = model_info.api_base
        if model_info and model_info.custom_llm_provider:
            acompletion_params["custom_llm_provider"] = model_info.custom_llm_provider

        response = await acompletion(**acompletion_params)

        duration = time.time() - start
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        if not content:
            tracker.log_execution(model_id, task_type, prompt, duration, "empty_output", 0)
            health.mark_failure(model_id, "Empty response", permanent=False)
            return {"model": model_id, "content": "", "duration": duration, "outcome": "empty"}

        tracker.log_execution(model_id, task_type, prompt, duration, "success", len(content))
        health.mark_success(model_id)  # Mark model as healthy on success

        return {"model": model_id, "content": content, "duration": duration, "outcome": "success"}

    except TimeoutError:
        duration = time.time() - start
        tracker.log_execution(model_id, task_type, prompt, duration, "timeout", 0)
        health.mark_failure(model_id, "Timeout after 30s", permanent=False)
        return {"model": model_id, "content": "", "duration": duration, "outcome": "timeout"}

    except Exception as e:
        duration = time.time() - start
        error_str = str(e)
        tracker.log_execution(model_id, task_type, prompt, duration, "error", 0, error_str)

        # Detect permanent failures
        is_permanent = any(
            x in error_str.lower()
            for x in [
                "decommissioned",
                "no longer supported",
                "has been removed",
                "not found",
                "404",
            ]
        )
        health.mark_failure(model_id, error_str, permanent=is_permanent)
        raise


def _extract_priority(content: str) -> int:
    """Extract priority from finding content."""
    lines = content.split("\n")
    for line in lines[:10]:  # Check first 10 lines
        if "P0" in line or "Critical" in line:
            return 0
        elif "P1" in line or "High" in line:
            return 1
        elif "P2" in line or "Medium" in line:
            return 2
    return 3  # Default to P3


def _extract_finding_signature(content: str) -> str:
    """Extract a unique signature from a finding for deduplication.

    A finding signature is based on:
    - File paths mentioned (e.g., "src/main.py")
    - Line numbers if specified
    - Issue type keywords (e.g., "SQL injection", "null pointer")
    - Function/class names if mentioned

    Returns a normalized signature string for comparison.
    """
    import re

    # Extract file paths (common patterns: src/file.py, /path/to/file, etc.)
    file_patterns = re.findall(r"[\w/]+\.(?:py|js|ts|java|go|rs|cpp|c|h|md)[:\d]*", content)
    files = sorted(set(file_patterns))

    # Extract issue type keywords
    issue_keywords = [
        "sql injection",
        "xss",
        "csrf",
        "buffer overflow",
        "null pointer",
        "memory leak",
        "race condition",
        "deadlock",
        "infinite loop",
        "type error",
        "value error",
        "index error",
        "key error",
        "missing import",
        "unused variable",
        "undefined variable",
        "security",
        "vulnerability",
        "bug",
        "error",
        "warning",
    ]

    content_lower = content.lower()
    found_issues = sorted({kw for kw in issue_keywords if kw in content_lower})

    # Extract function/class names (common patterns: def foo, class Bar, etc.)
    code_patterns = re.findall(r"(?:def|class|function|interface)\s+(\w+)", content)
    code_refs = sorted(set(code_patterns))

    # Build signature
    signature_parts = []
    if files:
        signature_parts.append(f"files:{','.join(files[:3])}")  # Limit to 3 files
    if found_issues:
        signature_parts.append(f"issues:{','.join(found_issues[:2])}")  # Limit to 2 issues
    if code_refs:
        signature_parts.append(f"refs:{','.join(code_refs[:2])}")  # Limit to 2 refs

    if not signature_parts:
        # Fallback: use first 100 chars of content hashed
        import hashlib

        return hashlib.md5(content[:100].encode()).hexdigest()[:16]

    return "|".join(signature_parts)


def _deduplicate_findings(
    all_findings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Deduplicate findings across models and compute uniqueness metrics.

    Args:
        all_findings: List of finding dicts with 'model', 'content', 'duration', 'outcome'

    Returns:
        Tuple of (deduplicated_findings, dedup_metrics)
        where dedup_metrics includes:
        - total_findings: total count before dedup
        - unique_findings: count after dedup
        - dedup_ratio: unique/total ratio
        - duplicates_removed: count removed
    """
    if not all_findings:
        return [], {
            "total_findings": 0,
            "unique_findings": 0,
            "dedup_ratio": 0.0,
            "duplicates_removed": 0,
        }

    seen_signatures = {}
    unique_findings = []

    for finding in all_findings:
        signature = _extract_finding_signature(finding["content"])

        if signature not in seen_signatures:
            # First occurrence of this finding
            seen_signatures[signature] = finding
            finding["signature"] = signature
            finding["is_duplicate"] = False
            unique_findings.append(finding)
        else:
            # Duplicate finding - mark it but track which model also found it
            finding["signature"] = signature
            finding["is_duplicate"] = True
            finding["duplicate_of"] = seen_signatures[signature]["model"]
            # Keep duplicate for tracking, but mark it
            unique_findings.append(finding)

    # Separate truly unique from duplicates
    truly_unique = [f for f in unique_findings if not f["is_duplicate"]]
    duplicates = [f for f in unique_findings if f["is_duplicate"]]

    metrics = {
        "total_findings": len(all_findings),
        "unique_findings": len(truly_unique),
        "duplicates_found": len(duplicates),
        "dedup_ratio": len(truly_unique) / len(all_findings) if all_findings else 0.0,
        "signatures_seen": len(seen_signatures),
    }

    return unique_findings, metrics


# ============================================================================
# CLI Interface
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="LLM API - Multi-Provider LLM Access with Dynamic Discovery"
    )
    parser.add_argument("path", help="Path to analyze")
    parser.add_argument(
        "--mode",
        choices=["chill", "mid", "chad", "adaptive"],
        default="mid",
        help="Analysis mode (default: mid, adaptive auto-stops at finding convergence)",
    )
    parser.add_argument("--refresh-models", action="store_true", help="Refresh model catalog")
    parser.add_argument(
        "--domain",
        choices=[
            "code_generation",
            "code_review",
            "architecture",
            "testing",
            "documentation",
            "debugging",
        ],
        help="Use domain-based routing with dynamic model router (quality-first)",
    )
    parser.add_argument(
        "--refresh-benchmarks",
        action="store_true",
        help="Force refresh benchmark data from internet before routing",
    )

    args = parser.parse_args()

    # Use @file syntax for token efficiency (matches llm-cli approach)
    # This is ~99.96% more token-efficient than embedding file contents
    try:
        file_path = Path(args.path)
        if not file_path.exists():
            # Try relative path from current directory
            file_path = Path.cwd() / args.path

        if not file_path.exists():
            print(f"ERROR: File not found: {args.path}")
            sys.exit(1)

        # Use forward slashes for @file syntax (cross-platform compatibility)
        context = f"@{file_path.as_posix()}"
    except Exception as e:
        print(f"ERROR: Failed to process {args.path}: {e}")
        sys.exit(1)

    query = "Review this code for issues, security vulnerabilities, and improvements."

    # Run analysis
    result = asyncio.run(
        run_llm_review(
            query=query,
            context=context,
            mode=args.mode,
            domain=args.domain,
            refresh_benchmarks=args.refresh_benchmarks,
        )
    )

    # Display results
    print("\n" + "=" * 80)
    print(f"RESULTS ({result['task_type']}/{result['mode']})")
    print("=" * 80)

    # Show dedup metrics if available
    if "dedup_metrics" in result and result["dedup_metrics"]:
        m = result["dedup_metrics"]
        print("\n[DEDUPLICATION METRICS]")
        print(f"  Total findings: {m.get('total_findings', 0)}")
        print(f"  Unique findings: {m.get('unique_findings', 0)}")
        print(f"  Duplicates found: {m.get('duplicates_found', 0)}")
        print(f"  Dedup ratio: {m.get('dedup_ratio', 0.0):.0%} (higher is better)")

    # Show adaptive mode specific info
    if result["mode"] == "adaptive" and "converged" in result:
        print("\n[ADAPTIVE MODE]")
        print(f"  Converged: {result['converged']}")
        print(f"  Iterations: {result.get('iterations', 'N/A')}")

    for i, finding in enumerate(result["findings"], 1):
        print(f"\n[{'─' * 76}")
        print(f"Finding {i}/{len(result['findings'])} - {finding['model']}")
        print(f"[{'─' * 76}")
        print(finding["content"][:1000])  # Truncate long outputs
        if len(finding["content"]) > 1000:
            print("... (truncated)")

    print(f"\n{'=' * 80}")
    print(f"Total duration: {result['total_duration']:.1f}s")
    print(f"Models tested: {result['models_tested']}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
