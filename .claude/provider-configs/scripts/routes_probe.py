"""Bifrost routing probe — verifies routes and sweeps provider catalogs.

Usage:
    python routes_probe.py              # verify configured routes + runtime probe
    python routes_probe.py --new-only   # sweep provider catalogs, show unrouted candidates
    python routes_probe.py --providers  # list all available providers in catalog
"""

import sqlite3, urllib.request, json, re, sys

db_path     = r"C:\Users\brsth\AppData\Roaming\bifrost\config.db"
bifrost_url = "http://localhost:8080"
MIN_CONTEXT = 128_000   # tokens
FREE_OPENROUTER = True   # exclude paid OpenRouter models

# ── helpers ──────────────────────────────────────────────────────────────────

def extract_model(cel: str) -> str | None:
    m = re.search(r'model\s*==\s*"([^"]+)"', cel)
    return m.group(1) if m else None

def is_free_model(mid: str) -> bool:
    """True for ':free' suffixed models or models with $0 price."""
    return ':free' in mid

def passes_filter(mid: str, ctx: int, prov: str) -> bool:
    """Apply context minimum and OpenRouter free-only rule."""
    if ctx < MIN_CONTEXT:
        return False
    if FREE_OPENROUTER and prov == 'openrouter' and not is_free_model(mid):
        return False
    return True

# ── DB query ─────────────────────────────────────────────────────────────────

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("""
    SELECT r.id, r.name, r.cel_expression, r.priority, rt.provider, rt.model
    FROM routing_rules r
    LEFT JOIN routing_targets rt ON rt.rule_id = r.id
    WHERE r.enabled = 1
    ORDER BY r.priority
""")
rules = []
for row in c.fetchall():
    rules.append({
        "id": row[0], "name": row[1] or row[0], "cel": row[2] or "",
        "priority": row[3], "provider": row[4], "model": row[5]
    })
conn.close()

# ── main ─────────────────────────────────────────────────────────────────────

if "--providers" in sys.argv:
    print("=== PROVIDERS IN BIFROST CATALOG ===")
    req = urllib.request.Request(
        f"{bifrost_url}/v1/models",
        headers={"Authorization": "Bearer dummy"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            models = body.get("data", []) if isinstance(body, dict) else body
            providers = {}
            for m in models:
                mid = m.get("id", "")
                if '/' in mid:
                    p = mid.split('/')[0]
                    providers[p] = providers.get(p, 0) + 1
            for p, cnt in sorted(providers.items()):
                print(f"  {p}  ({cnt} models)")
    except Exception as e:
        print(f"  ERROR: {e}")

elif "--new-only" in sys.argv:
    print("=== PROVIDER CATALOG SWEEP (128K+ ctx, OpenRouter free-only) ===")

    # Get all models from Bifrost catalog (proxied via Bifrost so auth is handled)
    req = urllib.request.Request(
        f"{bifrost_url}/v1/models",
        headers={"Authorization": "Bearer dummy"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            all_models = body.get("data", []) if isinstance(body, dict) else body
    except Exception as e:
        print(f"  ERROR fetching catalog: {e}")
        sys.exit(1)

    # Build set of currently routed model names (from CEL expressions)
    routed = set(extract_model(r["cel"]) or "" for r in rules)

    candidates = []
    for m in all_models:
        mid   = m.get("id", "")
        ctx   = m.get("context_length", 0) or 0
        if '/' not in mid:
            continue
        prov, model_id = mid.split('/', 1)
        if not passes_filter(mid, ctx, prov):
            continue
        if mid in routed or model_id in routed:
            continue
        # Further filter to coding/architecture keywords
        kws = ['coder', 'code', 'think', 'reason', 'architect', 'prover', 'theorem',
               'llama', 'qwen', 'gemma', 'nemotron', 'mistral', 'deepseek', 'kimi',
               'glm', 'codestral', 'devstral']
        if any(k in model_id.lower() for k in kws):
            label = "FREE" if is_free_model(mid) else "PAID"
            candidates.append({
                "id": mid,
                "ctx": ctx,
                "provider": prov,
                "label": label
            })

    # Group by provider
    by_provider = {}
    for c_model in candidates:
        p = c_model["provider"]
        by_provider.setdefault(p, []).append(c_model)

    for prov in sorted(by_provider.keys()):
        models = sorted(by_provider[prov], key=lambda x: x["id"])
        print(f"\n  [{prov}]")
        for m in models:
            ctx_k = m["ctx"] // 1000
            print(f"    {m['id']} | {ctx_k}K | {m['label']}")

    if not candidates:
        print("  [no unrouted coding/architecture models meet the criteria]")

else:
    # Standard: show configured routes + runtime probe
    print("=== CONFIGURED ROUTES ===")
    header = f"  {'Priority':<8} {'Model':<22} -> Target"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for rule in rules:
        mn  = extract_model(rule["cel"]) or rule["cel"]
        tgt = f"{rule['provider']}/{rule['model']}" if rule["provider"] and rule["model"] else "NO TARGET"
        print(f"  {rule['priority']:<8} {mn:<22} -> {tgt}")

    if not rules:
        print("  [no routing rules found in DB]")
        sys.exit(0)

    print("=== RUNTIME PROBE ===")
    total = len(rules)
    header = f"  {'#':>2}  {'Model':<20} {'Provider':<14} {'Latency':>9}  Status"
    print(header)
    print("  " + "-" * (len(header) - 2))

    ok_probe_count = 0
    err_probe_count = 0
    for i, rule in enumerate(rules, 1):
        mn = extract_model(rule["cel"])
        if not mn:
            print(f"  {i:>2}  {rule['id']:<20} {'[no model in CEL]':<14}")
            continue
        mn_display = mn[:20]
        payload = json.dumps({
            "model": mn,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{bifrost_url}/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                extra = body.get("extra_fields", {})
                prov = extra.get("provider", "UNKNOWN")
                lat  = extra.get("latency", 0)
                status = f"\033[92m{prov}\033[0m" if prov == rule["provider"] else f"\033[93m{prov}\033[0m (MISMATCH)"
                print(f"  {i:>2}  {mn_display:<20} {status:<14} {lat:>7}ms")
                ok_probe_count += 1
        except Exception as e:
            err_str = str(e).splitlines()[0]
            err_col = f"\033[91m{err_str}\033[0m"
            print(f"  {i:>2}  {mn_display:<20} {err_col:<14}")
            err_probe_count += 1

    if err_probe_count == 0:
        print(f"\n  \033[92mAll {ok_probe_count} routes healthy\033[0m")
    else:
        print(f"\n  \033[92m{ok_probe_count} OK\033[0m, \033[91m{err_probe_count} ERROR\033[0m")