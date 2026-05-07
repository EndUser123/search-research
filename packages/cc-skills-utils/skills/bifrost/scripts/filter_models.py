#!/usr/bin/env python3
"""Query and filter model catalog database (local shadow DB + Bifrost fallback)."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
PACKAGE_DIR = SCRIPT_DIR.parent.parent.parent          # cc-skills-utils root
CATALOG_DB = PACKAGE_DIR / "skills" / "catalog.db"   # local shadow DB
BIFROST_DB = Path(r"C:\Users\brsth\AppData\Roaming\bifrost\config.db")

# ── Provider taxonomy ───────────────────────────────────────────────────────────

FREE_KEY_PROVIDERS = {"cerebras", "groq", "mistral", "nvidia"}
OPENROUTER_PROVIDER = "openrouter"
SUBSCRIPTION_PROVIDERS = {"minimax", "z.ai"}
DEFAULT_EXCLUDED_VENDORS = {"moonshotai", "minimax", "z.ai", "bytedance"}

# ── DB connections ─────────────────────────────────────────────────────────────

def connect_local() -> sqlite3.Connection:
    if not CATALOG_DB.exists():
        sys.exit(f"Catalog DB not found at {CATALOG_DB}. Run sync_catalog.py first.")
    conn = sqlite3.connect(CATALOG_DB)
    conn.row_factory = sqlite3.Row
    return conn


def connect_bifrost() -> sqlite3.Connection:
    if not BIFROST_DB.exists():
        sys.exit(f"Bifrost DB not found at {BIFROST_DB}.")
    return sqlite3.connect(BIFROST_DB)


# ── Row adapters ────────────────────────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ── Query builders ─────────────────────────────────────────────────────────────

def build_query_local(args: argparse.Namespace) -> tuple[str, list]:
    """Build SQL query for local catalog DB."""
    wheres = []
    params = []

    if args.mode:
        wheres.append("mode = ?")
        params.append(args.mode)

    # Context minimum: free-key providers (API key covers all) are excluded from this filter
    # Others: require min_context. Uses CASE so a single SQL clause handles both paths.
    if getattr(args, 'min_context', None):
        free_key_case = " OR ".join(f"bifrost_provider = '{p}'" for p in FREE_KEY_PROVIDERS)
        wheres.append(f"(CASE WHEN {free_key_case} THEN 1 ELSE max_input_tokens >= ? END)")
        params.append(args.min_context)

    if args.provider:
        wheres.append("bifrost_provider = ?")
        params.append(args.provider)

    if args.vendor:
        wheres.append("vendor = ?")
        params.append(args.vendor)

    where_clause = " AND ".join(wheres) if wheres else "1=1"
    return (
        f"SELECT model, umu, bifrost_provider, host, vendor, model_slug, mode, "
        f"max_input_tokens, max_output_tokens, input_cost_per_token, output_cost_per_token "
        f"FROM models WHERE {where_clause} ORDER BY bifrost_provider, model",
        params,
    )


def build_query_bifrost(args: argparse.Namespace) -> tuple[str, list]:
    """Build SQL query for Bifrost governance DB (JSON blob)."""
    wheres = ["json_extract(data, '$.bifrost_provider') IS NOT NULL"]
    params = []

    if args.mode:
        wheres.append("json_extract(data, '$.mode') = ?")
        params.append(args.mode)

    if args.min_context:
        wheres.append("json_extract(data, '$.max_input_tokens') >= ?")
        params.append(args.min_context)

    if args.provider:
        wheres.append("json_extract(data, '$.bifrost_provider') = ?")
        params.append(args.provider)

    if args.vendor:
        wheres.append("json_extract(data, '$.vendor') = ?")
        params.append(args.vendor)

    where_clause = " AND ".join(wheres)
    return (
        f"SELECT model, data FROM governance_model_parameters WHERE {where_clause}",
        params,
    )


# ── Free/subscription filter ───────────────────────────────────────────────────

# Priority tiers: higher tier wins on slug collision.
# TIER 3 (highest): subscription providers — paid, authoritative
# TIER 2: free-key providers — API key covers all, authoritative
# TIER 1 (lowest): openrouter — fallback, used only if slug absent elsewhere
_TIER: dict[str, int] = {p: 3 for p in SUBSCRIPTION_PROVIDERS}
_TIER.update({p: 2 for p in FREE_KEY_PROVIDERS})
_TIER[OPENROUTER_PROVIDER] = 1

def apply_free_above_subscription(rows: list, excluded_vendors: set) -> list:
    """Filter rows based on provider taxonomy rules, then deduplicate on model_slug.

    Priority tiers (highest wins on collision):
      TIER 3 — minimax, z.ai  (subscription, authoritative)
      TIER 2 — cerebras, groq, mistral, nvidia  (free-key, authoritative)
      TIER 1 — openrouter  (fallback — used only if slug absent elsewhere)

    Duplicate detection is by model_slug so that identical models across
    providers (e.g. a model available via OpenRouter AND via minimax) are
    collapsed to the higher-priority source.  OpenRouter rows that collide
    with a TIER-2 or TIER-3 row are dropped from output but remain in the DB.
    """
    # Pass 1: taxonomy filtering
    candidates: list[tuple[int, dict]] = []
    for row in rows:
        data = row if isinstance(row, dict) else _row_to_dict(row)
        bp = data.get("bifrost_provider", "")
        vendor = data.get("vendor", "")
        in_cost = float(data.get("input_cost_per_token", 0) or 0)
        out_cost = float(data.get("output_cost_per_token", 0) or 0)

        if bp in FREE_KEY_PROVIDERS:
            candidates.append((_TIER[bp], data))
            continue

        if bp in SUBSCRIPTION_PROVIDERS:
            candidates.append((_TIER[bp], data))
            continue

        if bp == OPENROUTER_PROVIDER:
            if in_cost == 0 and out_cost == 0 and vendor not in excluded_vendors:
                candidates.append((_TIER[bp], data))
            continue

    # Pass 2: dedupe by model_slug, keeping highest-tier row
    seen: dict[str, int] = {}       # slug -> tier
    best:  dict[str, dict] = {}     # slug -> row
    for tier, data in candidates:
        slug = data.get("model_slug", "")
        if not slug:
            continue
        if slug not in seen or tier > seen[slug]:
            seen[slug] = tier
            best[slug] = data

    return list(best.values())


# ── Output formatters ──────────────────────────────────────────────────────────

def _format_row(model: str, data: dict, include_costs: bool) -> str:
    bp = data.get("bifrost_provider", "?")
    ctx = data.get("max_input_tokens", 0) or 0
    in_cost = data.get("input_cost_per_token", 0) or 0
    out_cost = data.get("output_cost_per_token", 0) or 0

    in_str = "free" if in_cost == 0 else f"${in_cost*1e6:.2f}/M"
    out_str = "free" if out_cost == 0 else f"${out_cost*1e6:.2f}/M"

    if include_costs:
        return f"{bp:<15} {model:<50} {ctx:>10,} {in_str:>8} {out_str:>8}"
    return f"{bp:<15} {model:<65} {ctx:>10,}"


def format_table(rows: list, include_costs: bool = True) -> str:
    if not rows:
        return "No models found."

    lines = []
    if include_costs:
        lines.append(f"{'Provider':<15} {'Model':<50} {'Ctx':>10} {'In':>8} {'Out':>8}")
        lines.append("-" * 93)
    else:
        lines.append(f"{'Provider':<15} {'Model':<65} {'Ctx':>10}")
        lines.append("-" * 90)

    for row in rows:
        data = row if isinstance(row, dict) else _row_to_dict(row)
        model = data.get("model", "")
        lines.append(_format_row(model, data, include_costs))

    lines.append(f"\nTotal: {len(rows)} models")
    return "\n".join(lines)


def format_json(rows: list) -> str:
    models = []
    for row in rows:
        data = row if isinstance(row, dict) else _row_to_dict(row)
        models.append({
            "provider": data.get("bifrost_provider"),
            "host": data.get("host"),
            "vendor": data.get("vendor"),
            "model": data.get("model"),
            "model_slug": data.get("model_slug"),
            "mode": data.get("mode"),
            "max_input_tokens": data.get("max_input_tokens"),
            "max_output_tokens": data.get("max_output_tokens"),
            "input_cost_per_token": data.get("input_cost_per_token"),
            "output_cost_per_token": data.get("output_cost_per_token"),
        })
    return json.dumps(models, indent=2)


# ── List providers ──────────────────────────────────────────────────────────────

def list_providers_local() -> None:
    conn = connect_local()
    cur = conn.execute("""
        SELECT bifrost_provider, COUNT(*) as cnt
        FROM models GROUP BY bifrost_provider ORDER BY cnt DESC
    """)
    rows = cur.fetchall()
    conn.close()

    print(f"{'Provider':<30} {'Count':>8}")
    print("-" * 40)
    for bp, cnt in rows:
        tag = ""
        if bp in FREE_KEY_PROVIDERS:
            tag = " [FREE-KEY]"
        elif bp in SUBSCRIPTION_PROVIDERS:
            tag = " [SUBSCRIPTION]"
        elif bp == OPENROUTER_PROVIDER:
            tag = " [OPENROUTER]"
        print(f"{bp:<30} {cnt:>8}{tag}")


def list_providers_bifrost() -> None:
    conn = connect_bifrost()
    cur = conn.execute("""
        SELECT json_extract(data, '$.bifrost_provider'), COUNT(*)
        FROM governance_model_parameters
        WHERE json_extract(data, '$.bifrost_provider') IS NOT NULL
        GROUP BY json_extract(data, '$.bifrost_provider')
        ORDER BY COUNT(*) DESC
    """)
    rows = cur.fetchall()
    conn.close()

    print(f"{'Provider':<30} {'Count':>8}")
    print("-" * 40)
    for bp, cnt in rows:
        tag = ""
        if bp in FREE_KEY_PROVIDERS:
            tag = " [FREE-KEY]"
        elif bp in SUBSCRIPTION_PROVIDERS:
            tag = " [SUBSCRIPTION]"
        elif bp == OPENROUTER_PROVIDER:
            tag = " [OPENROUTER]"
        print(f"{bp:<30} {cnt:>8}{tag}")


# ── List all ──────────────────────────────────────────────────────────────────

def list_all_local(args: argparse.Namespace) -> None:
    conn = connect_local()
    query, params = build_query_local(args)
    cur = conn.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    if args.format == "json":
        print(format_json(rows))
    else:
        print(format_table(rows, include_costs=True))


def list_all_bifrost(args: argparse.Namespace) -> None:
    conn = connect_bifrost()
    query, params = build_query_bifrost(args)
    cur = conn.execute(query, params)
    rows = [(r[0], json.loads(r[1])) for r in cur.fetchall()]
    conn.close()

    if args.format == "json":
        print(format_json(rows))
    else:
        print(format_table(rows, include_costs=True))


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query model catalog (local shadow DB or Bifrost governance DB)"
    )
    parser.add_argument(
        "--source", choices=["local", "bifrost"], default="local",
        help="local = shadow DB (default), bifrost = governance DB"
    )
    parser.add_argument("--mode", choices=["chat", "embed", "safety", "video", "translate", "parse"])
    parser.add_argument("--min-context", type=int, default=131072)
    parser.add_argument("--provider")
    parser.add_argument("--vendor")
    parser.add_argument("--free-only", action="store_true")
    parser.add_argument(
        "--free-above-subscription", action="store_true", default=True,
        help="Apply free/subscription rules (default: True)"
    )
    parser.add_argument("--exclude-vendors", default="moonshotai,minimax,z.ai,bytedance")
    parser.add_argument("--list-providers", action="store_true")
    parser.add_argument("--list-all", action="store_true")
    parser.add_argument("--format", choices=["table", "json", "count"], default="table")
    args = parser.parse_args()

    # ── list-providers ──────────────────────────────────────────────────────
    if args.list_providers:
        if args.source == "local":
            list_providers_local()
        else:
            list_providers_bifrost()
        return

    # ── list-all ────────────────────────────────────────────────────────────
    if args.list_all:
        if args.source == "local":
            list_all_local(args)
        else:
            list_all_bifrost(args)
        return

    # ── filtered query ──────────────────────────────────────────────────────
    if args.source == "local":
        conn = connect_local()
        query, params = build_query_local(args)
        cur = conn.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
    else:
        conn = connect_bifrost()
        query, params = build_query_bifrost(args)
        cur = conn.execute(query, params)
        rows = [(r[0], json.loads(r[1])) for r in cur.fetchall()]
        conn.close()

    # ── apply taxonomy filter ───────────────────────────────────────────────
    if args.free_above_subscription:
        excluded = set(args.exclude_vendors.split(",")) if args.exclude_vendors else DEFAULT_EXCLUDED_VENDORS
        rows = apply_free_above_subscription(rows, excluded)
    elif args.free_only:
        rows = [
            r for r in rows
            if float((r if isinstance(r, dict) else dict(r)).get("input_cost_per_token", 0) or 0) == 0
            and float((r if isinstance(r, dict) else dict(r)).get("output_cost_per_token", 0) or 0) == 0
        ]

    if args.format == "count":
        print(len(rows))
        return
    elif args.format == "json":
        print(format_json(rows))
    else:
        print(format_table(rows))


if __name__ == "__main__":
    main()
