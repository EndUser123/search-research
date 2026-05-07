#!/usr/bin/env python3
"""Sync model catalog from NVIDIA NIM and OpenRouter APIs."""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Load .env if present
_ENV = Path(__file__).resolve().parents[5] / ".env"  # P:/.env
if _ENV.exists():
    for line in _ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        if k:
            os.environ[k] = v

CATALOG_DB = Path(__file__).parent.parent.parent / "catalog.db"
SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "model_catalog.sql"

# ── Provider definitions ──────────────────────────────────────────────────────

PROVIDERS = [
    {
        "bifrost_name": "nvidia",
        "display_name": "NVIDIA NIM",
        "access_model": "free_key",
        "api_base": "https://integrate.api.nvidia.com/v1",
        "notes": "NIM subscription — all models effectively free",
    },
    {
        "bifrost_name": "openrouter",
        "display_name": "OpenRouter",
        "access_model": "openrouter",
        "api_base": "https://openrouter.ai/api/v1",
        "notes": "Cost-aware filtering required",
    },
    {
        "bifrost_name": "cerebras",
        "display_name": "Cerebras",
        "access_model": "free_key",
        "api_base": None,
        "notes": "API key covers access",
    },
    {
        "bifrost_name": "groq",
        "display_name": "Groq",
        "access_model": "free_key",
        "api_base": None,
        "notes": "API key covers access",
    },
    {
        "bifrost_name": "mistral",
        "display_name": "Mistral",
        "access_model": "free_key",
        "api_base": None,
        "notes": "API key covers access",
    },
    {
        "bifrost_name": "minimax",
        "display_name": "MiniMax",
        "access_model": "subscription",
        "api_base": None,
        "notes": "MiniMax subscription",
    },
    {
        "bifrost_name": "z.ai",
        "display_name": "Z.AI",
        "access_model": "subscription",
        "api_base": None,
        "notes": "Z.AI subscription",
    },
]


# ── Schema init ───────────────────────────────────────────────────────────────

def init_db() -> sqlite3.Connection:
    CATALOG_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(CATALOG_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    schema = SCHEMA_PATH.read_text()
    conn.executescript(schema)
    # Seed providers
    for p in PROVIDERS:
        conn.execute("""
            INSERT OR IGNORE INTO providers (bifrost_name, display_name, access_model, api_base, notes)
            VALUES (:bifrost_name, :display_name, :access_model, :api_base, :notes)
        """, p)
    conn.commit()
    return conn


# ── NIM sync ──────────────────────────────────────────────────────────────────

def fetch_nim_models() -> list[dict]:
    """Fetch all models from NVIDIA NIM API."""
    api_key = os.environ.get("NVIDIA_NIM_API_KEY") or os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        print("NVIDIA_NIM_API_KEY not set — skipping NIM sync")
        return []

    url = "https://integrate.api.nvidia.com/v1/models"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    models = data.get("data", [])
    results = []
    now = datetime.now(timezone.utc).isoformat()

    for m in models:
        mid = m.get("id", "")
        # Skip non-chat models (embeddings, safety, etc.) for now
        # NIM models often have context in special fields
        context_len = (
            m.get("context_length")
            or m.get("max_tokens")
            or 0
        )

        # Determine mode from model ID / name
        name_lower = mid.lower()
        if any(x in name_lower for x in ["embed", "embedding", "rerank"]):
            mode = "embed"
        elif any(x in name_lower for x in ["safety", "guard", "shield"]):
            mode = "safety"
        elif any(x in name_lower for x in ["translate", "translation"]):
            mode = "translate"
        elif any(x in name_lower for x in ["vision", "vlm", "vision-language"]):
            mode = "video"
        else:
            mode = "chat"

        # Derive host/vendor/slug from model ID
        # NIM model IDs are "provider/model-slug" (e.g. "meta/llama-3.3-70b-instruct")
        # Vendor is the provider prefix (parts[0]), slug is everything after
        parts = mid.split("/")
        if len(parts) >= 2:
            host = "nvidia"        # NIM is always accessed via nvidia host in UMU
            vendor = parts[0]       # provider prefix is the vendor (meta, moonshotai, nvidia, etc.)
            slug = "/".join(parts[1:])
        else:
            host = "nvidia"
            vendor = "nvidia"
            slug = mid

        umu = f"{host}://{vendor}/{slug}"

        pricing = m.get("pricing", {}) or {}
        input_cost = float(pricing.get("input", 0) or 0)
        output_cost = float(pricing.get("output", 0) or 0)

        results.append({
            "model": mid,
            "umu": umu,
            "bifrost_provider": "nvidia",
            "host": host,
            "vendor": vendor,
            "model_slug": slug,
            "base_model": mid,
            "mode": mode,
            "max_input_tokens": context_len,
            "max_output_tokens": None,
            "input_cost_per_token": input_cost,
            "output_cost_per_token": output_cost,
            "source": "nvidia_nim",
            "fetched_at": now,
        })

    return results


# ── OpenRouter sync ───────────────────────────────────────────────────────────

# Known free vendors to exclude (have their own subscription paths)
OPENROUTER_EXCLUDED_VENDORS = {"moonshotai", "minimax", "z.ai", "bytedance"}


def fetch_openrouter_models() -> list[dict]:
    """Fetch all models from OpenRouter API."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set — skipping OpenRouter sync")
        return []

    url = "https://openrouter.ai/api/v1/models"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())

    models = data.get("data", [])
    results = []
    now = datetime.now(timezone.utc).isoformat()

    for m in models:
        mid = m.get("id", "")
        if not mid:
            continue

        # Determine mode
        name_lower = mid.lower()
        modalities = m.get("supported_parameters", []) or []
        if "embed" in modalities or "embeddings" in modalities:
            mode = "embed"
        elif "image" in modalities or "vision" in modalities:
            mode = "video"
        else:
            mode = "chat"

        # OpenRouter format: "provider/model" or "provider/model:variant"
        # Keep full model string (including :variant) as slug — UMU must be unique
        parts = mid.split("/")
        if len(parts) >= 2:
            vendor = parts[0].lower()
            slug = "/".join(parts[1:])   # preserve full variant suffix (e.g. :free, :aa2897)
        else:
            vendor = parts[0].lower()
            slug = parts[0]

        host = "openrouter"
        umu = f"{host}://{vendor}/{slug}"

        ctx = m.get("context_length", 0) or 0
        pricing = m.get("pricing", {}) or {}
        input_cost = float(pricing.get("input", 0) or 0)
        output_cost = float(pricing.get("output", 0) or 0)

        # Skip excluded vendors for free models (they have subscription paths)
        excluded = OPENROUTER_EXCLUDED_VENDORS
        is_free = input_cost == 0 and output_cost == 0
        skip_reason = None
        if vendor in excluded and is_free:
            skip_reason = f"vendor {vendor} excluded (subscription path)"
        elif vendor not in excluded and not is_free:
            skip_reason = f"vendor {vendor}, non-zero cost"

        results.append({
            "model": mid,
            "umu": umu,
            "bifrost_provider": "openrouter",
            "host": host,
            "vendor": vendor,
            "model_slug": slug,
            "base_model": mid,
            "mode": mode,
            "max_input_tokens": ctx,
            "max_output_tokens": m.get("max_output_tokens"),
            "input_cost_per_token": input_cost,
            "output_cost_per_token": output_cost,
            "source": "openrouter",
            "fetched_at": now,
            "_skip_reason": skip_reason,
        })

    return results


# ── DB upsert ────────────────────────────────────────────────────────────────

MODEL_COLS = [
    "model", "umu", "bifrost_provider", "host", "vendor", "model_slug",
    "base_model", "mode", "max_input_tokens", "max_output_tokens",
    "input_cost_per_token", "output_cost_per_token", "source", "fetched_at",
]


def upsert_models(conn: sqlite3.Connection, rows: list[dict]) -> int:
    upserted = 0
    skipped = 0
    for r in rows:
        skip = r.pop("_skip_reason", None)
        if skip:
            skipped += 1
            continue

        cols = {k: r[k] for k in MODEL_COLS if k in r}
        cols["updated_at"] = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            INSERT INTO models VALUES (NULL, :model, :umu, :bifrost_provider,
                :host, :vendor, :model_slug, :base_model, :mode,
                :max_input_tokens, :max_output_tokens,
                :input_cost_per_token, :output_cost_per_token, :source, :fetched_at,
                datetime('now'), datetime('now'))
            ON CONFLICT(model) DO UPDATE SET
                umu                = excluded.umu,
                bifrost_provider   = excluded.bifrost_provider,
                host              = excluded.host,
                vendor            = excluded.vendor,
                model_slug        = excluded.model_slug,
                mode              = excluded.mode,
                max_input_tokens  = excluded.max_input_tokens,
                max_output_tokens = excluded.max_output_tokens,
                input_cost_per_token   = excluded.input_cost_per_token,
                output_cost_per_token  = excluded.output_cost_per_token,
                source            = excluded.source,
                fetched_at        = excluded.fetched_at,
                updated_at        = datetime('now')
        """, cols)
        upserted += 1

    conn.commit()
    return upserted, skipped


# ── OpenAI-compatible fetch helper ───────────────────────────────────────────

def _fetch_openai_compatible_models(
    provider: str,
    api_base: str,
    env_key: str,
    api_key: str | None = None,
) -> list[dict]:
    """Fetch models from any OpenAI-compatible /models endpoint (requests-based)."""
    import requests as _req

    key = api_key or os.environ.get(env_key)
    if not key:
        print(f"{env_key} not set — skipping {provider} sync")
        return []

    url = f"{api_base.rstrip('/')}/models"
    try:
        resp = _req.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  {provider} fetch failed: {e}")
        return []

    models = data.get("data", []) or data.get("models", []) or []
    results = []
    now = datetime.now(timezone.utc).isoformat()

    for m in models:
        mid = m.get("id", "")
        if not mid:
            continue

        name_lower = mid.lower()
        if any(x in name_lower for x in ["embed", "embedding"]):
            mode = "embed"
        elif any(x in name_lower for x in ["safety", "guard", "shield"]):
            mode = "safety"
        elif any(x in name_lower for x in ["vision", "vlm"]):
            mode = "video"
        elif any(x in name_lower for x in ["translate"]):
            mode = "translate"
        else:
            mode = "chat"

        parts = mid.split("/")
        if len(parts) >= 2:
            vendor = parts[0].lower()
            slug = "/".join(parts[1:])
        else:
            vendor = provider
            slug = mid

        ctx = m.get("context_length", 0) or 0
        if not ctx:
            ctx = m.get("max_tokens", 0) or 0

        pricing = m.get("pricing", {}) or {}
        input_cost = float(pricing.get("input", 0) or 0)
        output_cost = float(pricing.get("output", 0) or 0)

        results.append({
            "model": mid,
            "umu": f"{provider}://{vendor}/{slug}",
            "bifrost_provider": provider,
            "host": provider,
            "vendor": vendor,
            "model_slug": slug,
            "base_model": mid,
            "mode": mode,
            "max_input_tokens": ctx,
            "max_output_tokens": m.get("max_output_tokens"),
            "input_cost_per_token": input_cost,
            "output_cost_per_token": output_cost,
            "source": f"{provider}_api",
            "fetched_at": now,
        })

    return results


# ── Provider-specific fetchers ─────────────────────────────────────────────────

def fetch_cerebras_models() -> list[dict]:
    return _fetch_openai_compatible_models(
        "cerebras", "https://api.cerebras.ai/v1", "CEREBRAS_API_KEY"
    )


def fetch_groq_models() -> list[dict]:
    return _fetch_openai_compatible_models(
        "groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY"
    )


def fetch_mistral_models() -> list[dict]:
    return _fetch_openai_compatible_models(
        "mistral", "https://api.mistral.ai/v1", "MISTRAL_API_KEY"
    )


# ── Subscription providers (no public /v1/models endpoint known) ─────────────

# Seeded from bifrost governance DB records — no live API refresh available
MINIMAX_KNOWN_MODELS = [
    {"model": "minimax/minimax-m2.7", "ctx": 196608},
    {"model": "minimax/minimax-m2.5", "ctx": 196608},
    {"model": "minimax/minimax-m2.5:free", "ctx": 196608},
]

ZAI_KNOWN_MODELS = [
    {"model": "zai/glm-5", "ctx": 200000},
    {"model": "zai/glm-5-turbo", "ctx": 200000},
    {"model": "zai/glm-5.1", "ctx": 200000},
]


def fetch_minimax_models() -> list[dict]:
    """Seed from known records — no public /v1/models endpoint."""
    if not os.environ.get("MINIMAX_API_KEY"):
        print("MINIMAX_API_KEY not set — skipping minimax sync")
        return []
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "model": m["model"],
            "umu": f"minimax://minimax/{m['model'].split('/')[1]}",
            "bifrost_provider": "minimax",
            "host": "minimax",
            "vendor": "minimax",
            "model_slug": m["model"].split("/", 1)[1],
            "base_model": m["model"],
            "mode": "chat",
            "max_input_tokens": m["ctx"],
            "max_output_tokens": m["ctx"],
            "input_cost_per_token": 0,
            "output_cost_per_token": 0,
            "source": "minimax_seed",
            "fetched_at": now,
        }
        for m in MINIMAX_KNOWN_MODELS
    ]


def fetch_zai_models() -> list[dict]:
    """Seed from known records — no public /v1/models endpoint."""
    if not os.environ.get("ZAI_API_KEY"):
        print("ZAI_API_KEY not set — skipping z.ai sync")
        return []
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "model": m["model"],
            "umu": f"zai://zai/{m['model'].split('/')[1]}",
            "bifrost_provider": "z.ai",
            "host": "zai",
            "vendor": "zai",
            "model_slug": m["model"].split("/", 1)[1],
            "base_model": m["model"],
            "mode": "chat",
            "max_input_tokens": m["ctx"],
            "max_output_tokens": m["ctx"],
            "input_cost_per_token": 0,
            "output_cost_per_token": 0,
            "source": "zai_seed",
            "fetched_at": now,
        }
        for m in ZAI_KNOWN_MODELS
    ]


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Sync model catalog from provider APIs")
    parser.add_argument("--source", choices=["nim", "openrouter", "cerebras", "groq", "mistral", "minimax", "zai", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = init_db()

    total_upserted = 0
    total_skipped = 0

    if args.source in ("nim", "all"):
        print("Fetching NVIDIA NIM models...")
        try:
            rows = fetch_nim_models()
            upserted, skipped = upsert_models(conn, rows)
            print(f"  NIM: {upserted} upserted, {skipped} skipped")
            total_upserted += upserted
            total_skipped += skipped
        except Exception as e:
            print(f"  NIM fetch failed: {e}")

    if args.source in ("openrouter", "all"):
        print("Fetching OpenRouter models...")
        try:
            rows = fetch_openrouter_models()
            upserted, skipped = upsert_models(conn, rows)
            print(f"  OpenRouter: {upserted} upserted, {skipped} skipped")
            total_upserted += upserted
            total_skipped += skipped
        except Exception as e:
            print(f"  OpenRouter fetch failed: {e}")

    if args.source in ("cerebras", "all"):
        print("Fetching Cerebras models...")
        try:
            rows = fetch_cerebras_models()
            upserted, skipped = upsert_models(conn, rows)
            print(f"  Cerebras: {upserted} upserted, {skipped} skipped")
            total_upserted += upserted
            total_skipped += skipped
        except Exception as e:
            print(f"  Cerebras fetch failed: {e}")

    if args.source in ("groq", "all"):
        print("Fetching Groq models...")
        try:
            rows = fetch_groq_models()
            upserted, skipped = upsert_models(conn, rows)
            print(f"  Groq: {upserted} upserted, {skipped} skipped")
            total_upserted += upserted
            total_skipped += skipped
        except Exception as e:
            print(f"  Groq fetch failed: {e}")

    if args.source in ("mistral", "all"):
        print("Fetching Mistral models...")
        try:
            rows = fetch_mistral_models()
            upserted, skipped = upsert_models(conn, rows)
            print(f"  Mistral: {upserted} upserted, {skipped} skipped")
            total_upserted += upserted
            total_skipped += skipped
        except Exception as e:
            print(f"  Mistral fetch failed: {e}")

    if args.source in ("minimax", "all"):
        print("Fetching MiniMax models...")
        try:
            rows = fetch_minimax_models()
            upserted, skipped = upsert_models(conn, rows)
            print(f"  MiniMax: {upserted} upserted, {skipped} skipped")
            total_upserted += upserted
            total_skipped += skipped
        except Exception as e:
            print(f"  MiniMax fetch failed: {e}")

    if args.source in ("zai", "all"):
        print("Fetching Z.AI models...")
        try:
            rows = fetch_zai_models()
            upserted, skipped = upsert_models(conn, rows)
            print(f"  Z.AI: {upserted} upserted, {skipped} skipped")
            total_upserted += upserted
            total_skipped += skipped
        except Exception as e:
            print(f"  Z.AI fetch failed: {e}")

    # Summary
    cur = conn.execute("SELECT COUNT(*), COUNT(DISTINCT bifrost_provider) FROM models")
    count, n_providers = cur.fetchone()
    print(f"\nCatalog: {count} models from {n_providers} providers")
    print(f"Total upserted: {total_upserted}, skipped: {total_skipped}")

    if args.dry_run:
        print("[DRY RUN — no changes committed]")
        conn.rollback()

    conn.close()


if __name__ == "__main__":
    main()
