"""Bifrost database queries — machine-readable helper for PowerShell and scripts.

Usage:
    python bifrost_db.py --get-routes          -> JSON dict of routing rules
    python bifrost_db.py --get-rules           -> JSON list of all rules with targets
    python bifrost_db.py --status              -> JSON summary of daemon health
    python bifrost_db.py --enable-rules         -> enable all rules, print count
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path.home() / "AppData" / "Roaming" / "bifrost" / "config.db"


def get_routes() -> dict:
    """Return routing table as {model_name: {display, sonnet, opus, haiku}}."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT r.id, r.cel_expression, rt.provider, rt.model
        FROM routing_rules r
        LEFT JOIN routing_targets rt ON rt.rule_id = r.id
        WHERE r.cel_expression IS NOT NULL AND r.cel_expression != ''
        ORDER BY r.priority
    """)
    routes = {}
    for row in c.fetchall():
        cel, provider, model = row[1], row[2], row[3]
        if not provider or not model:
            continue
        import re
        m = re.search(r'model=="([^"]+)"', cel.replace(" ", ""))
        if m:
            model_name = m.group(1)
            routes[model_name] = {
                "display": f"{provider}/{model}",
                "sonnet": model_name,
                "opus": model_name,
                "haiku": model_name,
            }
    conn.close()
    return routes


def get_rules() -> list[dict]:
    """Return all rules with their targets as a list."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT r.id, r.name, r.cel_expression, r.scope, r.priority, rt.provider, rt.model, rt.weight
        FROM routing_rules r
        LEFT JOIN routing_targets rt ON rt.rule_id = r.id
        ORDER BY r.priority
    """)
    rules = []
    for row in c.fetchall():
        rules.append({
            "id": row[0],
            "name": row[1] or row[0],
            "cel_expression": row[2] or "",
            "scope": row[3] or "global",
            "priority": row[4],
            "targets": [] if (row[5] is None or row[6] is None)
                       else [{"provider": row[5], "model": row[6], "weight": row[7] or 1.0}],
        })
    conn.close()
    return {"rules": rules}


def get_status() -> dict:
    """Return daemon health summary as a dict."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*), SUM(CASE WHEN enabled=1 THEN 1 ELSE 0 END)
        FROM routing_rules
    """)
    total, enabled = c.fetchone()
    enabled = enabled or 0

    c.execute("""
        SELECT COUNT(DISTINCT r.id)
        FROM routing_rules r
        JOIN routing_targets rt ON rt.rule_id = r.id
        WHERE r.enabled = 1 AND rt.provider IS NOT NULL
    """)
    rules_with_targets = c.fetchone()[0] or 0

    c.execute("""
        SELECT DISTINCT rt.provider
        FROM routing_targets rt
        JOIN routing_rules r ON r.id = rt.rule_id
        WHERE r.enabled = 1 AND rt.provider IS NOT NULL
    """)
    providers_with_rules = sorted([row[0] for row in c.fetchall()])

    c.execute("""
        SELECT LOWER(provider) as p, substr(value, 1, 12)
        FROM config_keys GROUP BY LOWER(provider)
    """)
    all_keys = [[row[0], row[1]] for row in c.fetchall()]
    all_keys_lower = [k[0].lower() for k in all_keys]
    missing = [p for p in providers_with_rules if p.lower() not in all_keys_lower]

    conn.close()
    return {
        "total": total,
        "enabled": enabled,
        "rules_with_targets": rules_with_targets,
        "providers_with_rules": providers_with_rules,
        "all_keys": all_keys,
        "missing_keys": missing,
    }


def enable_rules() -> int:
    """Re-enable all routing rules. Returns count of updated rows."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE routing_rules SET enabled = 1")
    conn.commit()
    count = c.rowcount
    conn.close()
    return count


def main():
    parser = argparse.ArgumentParser(description="Bifrost DB queries")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--get-routes", action="store_true", help="Return routing table as JSON dict")
    group.add_argument("--get-rules", action="store_true", help="Return all rules with targets as JSON")
    group.add_argument("--status", action="store_true", help="Return daemon health summary as JSON")
    group.add_argument("--enable-rules", action="store_true", help="Enable all rules, print count")
    args = parser.parse_args()

    if args.get_routes:
        print(json.dumps(get_routes()))
    elif args.get_rules:
        print(json.dumps(get_rules()))
    elif args.status:
        print(json.dumps(get_status()))
    elif args.enable_rules:
        count = enable_rules()
        print(f"Enabled {count} rules")


if __name__ == "__main__":
    main()