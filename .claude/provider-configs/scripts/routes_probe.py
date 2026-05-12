"""Bifrost routing probe — verifies routes and sweeps provider catalogs.

Usage:
    python routes_probe.py                        # verify configured routes + runtime probe
    python routes_probe.py --only mistral         # show routed + unrouted for provider(s)
    python routes_probe.py --routes no            # sweep catalog, show unrouted candidates
    python routes_probe.py --routes no --only mistral  # unrouted only for provider
    python routes_probe.py --routes yes --only mistral # routed only for provider
    python routes_probe.py --providers            # list all available providers in catalog
"""

import sqlite3, urllib.request, json, re, sys, unicodedata

db_path     = r"C:\Users\brsth\AppData\Roaming\bifrost\config.db"
bifrost_url = "http://localhost:8080"
MIN_CONTEXT = 128_000   # tokens
FREE_OPENROUTER = True   # exclude paid OpenRouter models
LATENCY_DB  = r"C:\Users\brsth\AppData\Roaming\bifrost\latency_history.json"
LATENCY_TTL = 90         # days to keep latency records

# Known provider quotas (CEL model name -> quota string).
# Sources: user console (Mistral, Z.AI), official docs (MiniMax, Gemini),
# community/aggregator docs (Cerebras, Groq, Nvidia, OpenRouter).
MODEL_QUOTA: dict[str, str] = {
    # Cerebras — 1M tok/day free tier (source: pricepertoken.com)
    "C-Qwen-3-235b":         "1M/day",
    # Gemini — varies by model (source: aifreeapi.com)
    "Gemini-3.1-pro":        "100/day",
    "Gemini-3.1-flash-lite": "1K/day",
    "gemma-4-31b-it":        "1K/day",
    # Groq — ~14K RPD free tier (source: grizzlypeaksoftware.com)
    "Groq-GPT-OSS-120b":     "14K/day",
    # MiniMax — Plus plan (source: user account)
    "M27":                    "4500/5h",
    # Mistral — from user's console limits page
    "Mi-Devstral":           "4M/mo",
    "Mi-Magistral":          "1B/mo",
    "Mi-Mistral":            "unlimited",
    # Nvidia — 40 RPM, 1K credits (source: forums.developer.nvidia.com)
    "N-DSv4-flash":          "40RPM",
    "N-DSv4-Pro":            "40RPM",
    "N-Kimi-2.6":            "40RPM",
    "step-3.5-flash":        "40RPM",
    "N-Q3C-480b-a35b":       "40RPM",
    "N-N3S-120b-a12b":       "40RPM",
    # OpenRouter — paid account ($10+ credits): 1K/day free models (source: openrouter.ai/docs + reddit)
    "ring-2.6-1t":           "1K/day",
    "owl-alpha":             "1K/day",
    # Z.AI — Max plan (source: docs.z.ai + user confirmation)
    "GLM-5.1":               "1600/5h",
    "glm-4.7":               "1600/5h",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def extract_model(cel: str) -> str | None:
    m = re.search(r'model\s*==\s*"([^"]+)"', cel)
    return m.group(1) if m else None

def is_free_model(mid: str, pricing: dict | None = None) -> bool:
    """True for ':free' suffix or $0 pricing."""
    if ':free' in mid:
        return True
    if pricing:
        try:
            p = float(pricing.get('prompt', '1'))
            c = float(pricing.get('completion', '1'))
            return p == 0 and c == 0
        except (ValueError, TypeError):
            pass
    return False

def passes_filter(mid: str, ctx: int, prov: str, only_providers: list | None = None, pricing: dict | None = None) -> bool:
    """Apply context minimum and OpenRouter free-only rule."""
    if not only_providers and ctx == 0:
        return False
    if 0 < ctx < MIN_CONTEXT:
        return False
    if FREE_OPENROUTER and prov == 'openrouter' and not is_free_model(mid, pricing):
        return False
    return True

def parse_argv_flags() -> tuple[list[str], list[str], str | None]:
    """Parse --only, --exclude, --routes from sys.argv.
    Returns (only_providers, exclude_terms, routes_value).
    routes_value is 'yes', 'no', or None.
    """
    only_providers = []
    exclude_terms = []
    routes_value = None
    for i, a in enumerate(sys.argv):
        if a == "--only" and i + 1 < len(sys.argv):
            only_providers = [t.strip().lower() for t in sys.argv[i + 1].split(",") if t.strip()]
            if only_providers == ["all"]:
                only_providers = ["__all__"]
        if a == "--exclude" and i + 1 < len(sys.argv):
            exclude_terms = [t.strip().lower() for t in sys.argv[i + 1].split(",") if t.strip()]
        if a == "--routes" and i + 1 < len(sys.argv):
            val = sys.argv[i + 1].lower()
            if val in ("yes", "no"):
                routes_value = val
    return only_providers, exclude_terms, routes_value

def fetch_catalog() -> list[dict]:
    """Fetch all models from Bifrost catalog."""
    req = urllib.request.Request(
        f"{bifrost_url}/v1/models",
        headers={"Authorization": "Bearer dummy"},
    )
    print("  Fetching catalog (aggregates from all providers, may take up to 2min)...", end="", flush=True)
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        all_models = body.get("data", []) if isinstance(body, dict) else body
    print(f" done ({len(all_models)} models)")

    # Inject static models for providers whose APIs don't enumerate models
    all_models = inject_static_models(all_models)
    return all_models

STATIC_MODELS: dict[str, list[dict]] = {
    # MiniMax Token Plan: /v1/models returns null (GitHub issue #19)
    "MiniMax": [
        {"id": "MiniMax/MiniMax-M2.7",             "context_length": 204800},
        {"id": "MiniMax/MiniMax-M2.7-highspeed",    "context_length": 204800},
        {"id": "MiniMax/MiniMax-M2.5",              "context_length": 204800},
        {"id": "MiniMax/MiniMax-M2.1",              "context_length": 204800},
        {"id": "MiniMax/MiniMax-M2.1-highspeed",    "context_length": 204800},
        {"id": "MiniMax/MiniMax-M2",                "context_length": 204800},
        {"id": "MiniMax/MiniMax-M1",                "context_length": 80000},
    ],
}

def inject_static_models(all_models: list[dict]) -> list[dict]:
    """Add static models for providers configured in DB but absent from catalog."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT DISTINCT name FROM config_providers")
    db_providers = {row[0] for row in c.fetchall()}
    conn.close()

    catalog_providers = set()
    for m in all_models:
        mid = m.get("id", "")
        if "/" in mid:
            catalog_providers.add(mid.split("/", 1)[0])

    injected = 0
    for prov, models in STATIC_MODELS.items():
        if prov in db_providers and prov not in catalog_providers:
            all_models.extend(models)
            injected += len(models)
    if injected:
        print(f" (+{injected} static models for providers without catalog enumeration)")
    return all_models

def filter_candidates(all_models: list, routed: set, only_providers: list,
                      exclude_terms: list, include_routed: bool = False) -> list[dict]:
    """Filter catalog models by provider, context, keywords, and route status."""
    candidates = []
    for m in all_models:
        mid   = m.get("id", "")
        ctx   = m.get("context_length", 0) or 0
        if '/' not in mid:
            continue
        prov, model_id = mid.split('/', 1)
        if only_providers and "__all__" not in only_providers and prov.lower() not in only_providers:
            continue
        if not passes_filter(mid, ctx, prov, only_providers, m.get("pricing")):
            continue
        if not include_routed and (mid in routed or model_id in routed):
            continue
        if exclude_terms and any(t in mid.lower() for t in exclude_terms):
            continue
        non_chat = ['embed', 'parse', 'reward', 'detect', 'pii', 'translate',
                     'safety', 'guard', 'deplot', 'neva', 'nvclip', 'calibration',
                     'bge-', 'vila', 'cosmos', 'fuyu']
        if any(t in model_id.lower() for t in non_chat):
            continue
        label = "FREE" if is_free_model(mid, m.get("pricing")) else "PAID"
        has_tools = "tools" in (m.get("supported_parameters") or [])
        candidates.append({"id": mid, "ctx": ctx, "provider": prov, "label": label, "tools": has_tools})
    return candidates

def apply_latest_only(candidates: list[dict], only_providers: list | None = None) -> list[dict]:
    """Remove superseded models (keep only latest version per family).
    Default ON for provider-scoped queries (--only)."""
    if not candidates:
        return candidates
    if not only_providers and "--latest-only" not in sys.argv:
        return candidates
    import re as _re
    def model_version(mid: str) -> tuple[str, float]:
        name = mid.split("/", 1)[1] if "/" in mid else mid
        base = name.lower()
        score = 0.0
        base = _re.sub(r"[-:](latest|preview|free|beta|alpha)$", "", base)
        dm_ym = _re.search(r"[-](\d{2})[-](\d{4})$", base)
        dm_my = _re.search(r"[-](\d{2})(\d{2})$", base)
        if dm_ym:
            score = float(f"{dm_ym.group(2)}.{dm_ym.group(1)}")
            base = base[:dm_ym.start()]
        elif dm_my:
            score = float(f"20{dm_my.group(1)}.{dm_my.group(2)}")
            base = base[:dm_my.start()]
        else:
            vm = _re.search(r"[-.]v?(\d+)(?:[.](\d+))?", base)
            after = base[vm.end():] if vm else ""
            if vm and not after.lower().startswith("b"):
                major = int(vm.group(1))
                minor = int(vm.group(2)) if vm.group(2) else 0
                score = major + minor / 100.0
                base = base[:vm.start()]
        return base, score

    families: dict[str, list] = {}
    for c in candidates:
        fam, ver = model_version(c["id"])
        families.setdefault(fam, []).append((c, ver))
    kept = set()
    for fam, members in families.items():
        max_ver = max(v for _, v in members)
        for c, v in members:
            # -latest/-preview are pointers, not superseded versions
            is_alias = c["id"].lower().endswith(("-latest", "-preview"))
            if v == max_ver or is_alias:
                kept.add(c["id"])
    return [c for c in candidates if c["id"] in kept]

# ── latency history ───────────────────────────────────────────────────────────

def load_latency_history() -> dict[str, list[dict]]:
    """Load latency history from JSON. Keys are lowercase model names."""
    import time as _t
    try:
        with open(LATENCY_DB, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    cutoff = _t.time() - LATENCY_TTL * 86400
    pruned = {}
    for key, entries in data.items():
        kept = [e for e in entries if e.get("ts", 0) > cutoff]
        if kept:
            pruned[key.lower()] = kept
    return pruned

def save_latency_history(history: dict[str, list[dict]]) -> None:
    """Save latency history to JSON."""
    with open(LATENCY_DB, "w") as f:
        json.dump(history, f)

def record_latency(history: dict[str, list[dict]], model: str, latency_ms: float) -> float | None:
    """Record a latency sample and return the rolling average (ms), or None."""
    import time as _t
    key = model.lower()
    entries = history.setdefault(key, [])
    entries.append({"ts": _t.time(), "lat": latency_ms})
    if entries:
        return sum(e["lat"] for e in entries) / len(entries)
    return None

def avg_latency_str(history: dict[str, list[dict]], model: str) -> str:
    """Return formatted average latency string, or empty."""
    entries = history.get(model.lower(), [])
    if not entries:
        return ""
    avg = sum(e["lat"] for e in entries) / len(entries)
    n = len(entries)
    return f"{int(avg):,}({n})"

def display_width(s: str) -> int:
    """Column width accounting for wide chars (CJK, emoji)."""
    w = 0
    for ch in s:
        w += 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1
    return w

def pad_to(s: str, width: int) -> str:
    """Left-align s with padding calculated by display width."""
    return s + " " * (width - display_width(s))

def ansi_width(s: str) -> int:
    """Display width excluding ANSI escape sequences."""
    return display_width(re.sub(r'\033\[[0-9;]*m', '', s))

def pad_ansi(s: str, width: int) -> str:
    """Pad to display width, accounting for ANSI codes and wide chars."""
    return s + " " * max(0, width - ansi_width(s))

def short_error(err: str) -> str:
    """Shorten common HTTP errors for columnar display."""
    m = re.match(r'HTTP Error (\d+)', err)
    if m:
        reasons = {'429': 'Rate Limited', '404': 'Not Found', '400': 'Bad Request',
                   '500': 'Server Error', '504': 'Timeout'}
        return f"{m.group(1)} {reasons.get(m.group(1), '')}".strip()
    if 'timed out' in err.lower():
        return 'Timeout'
    return err[:20]

def active_filters(only_providers: list | None = None, exclude_terms: list | None = None) -> str:
    """Build a one-line summary of active filters for display."""
    parts = [f"ctx>={MIN_CONTEXT // 1000}K"]
    if FREE_OPENROUTER:
        parts.append("openrouter-free-only")
    parts.append("non-chat-excluded")
    if only_providers and "__all__" not in only_providers:
        parts.append(f"only={','.join(only_providers)}")
    if exclude_terms:
        parts.append(f"exclude={','.join(exclude_terms)}")
    if only_providers:
        parts.append("latest-only")
    return "  Filters: " + ", ".join(parts)

def print_unrouted(candidates: list[dict], only_providers: list | None = None, title: str = "UNROUTED") -> None:
    """Print unrouted candidates grouped by provider, stripped prefixes, aligned columns."""
    candidates = apply_latest_only(candidates, only_providers)
    by_provider: dict[str, list] = {}
    for c_model in candidates:
        p = c_model["provider"]
        by_provider.setdefault(p, []).append(c_model)

    all_names = [m["id"].split("/", 1)[1] if "/" in m["id"] else m["id"]
                 for models in by_provider.values() for m in models]
    max_name = max((display_width(n) for n in all_names), default=0)

    for prov in sorted(by_provider.keys()):
        models = sorted(by_provider[prov], key=lambda x: x["id"])
        print(f"\n  [{prov}]")
        for m in models:
            name = m["id"].split("/", 1)[1] if "/" in m["id"] else m["id"]
            ctx_k = m["ctx"] // 1000
            tools = "T" if m["tools"] else " "
            print(f"    {pad_to(name, max_name)}  {ctx_k:>5}K  {tools}  {m['label']}")

    if not candidates:
        print("  [no models meet the criteria]")

def print_routed(rules: list[dict], only_providers: list) -> None:
    """Print routed rules filtered by provider."""
    print("=== ROUTED ===")
    filtered = rules
    if only_providers and "__all__" not in only_providers:
        filtered = [r for r in rules if r["provider"] and r["provider"].lower() in only_providers]
    if not filtered:
        print("  [no matching routes found]")
        return
    model_names = [extract_model(r["cel"]) or r["cel"] for r in filtered]
    max_model = max((display_width(n) for n in model_names), default=22)
    max_model = max(max_model, 8)  # at least as wide as "Priority"
    header = f"  {pad_to('Priority', 8)} {pad_to('Model', max_model)} -> Target"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for rule in filtered:
        mn  = extract_model(rule["cel"]) or rule["cel"]
        tgt = f"{rule['provider']}/{rule['model']}" if rule["provider"] and rule["model"] else "NO TARGET"
        print(f"  {pad_to(str(rule['priority']), 8)} {pad_to(mn, max_model)} -> {tgt}")

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

# ── parse flags ──────────────────────────────────────────────────────────────

only_providers, exclude_terms, routes_value = parse_argv_flags()
has_provider_filter = bool(only_providers) or bool(exclude_terms)

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

elif has_provider_filter:
    # --only or --exclude present: show routed and/or unrouted filtered by provider
    routed = set(extract_model(r["cel"]) or "" for r in rules)

    if routes_value == "yes":
        # Routed only
        print_routed(rules, only_providers)

    elif routes_value == "no" or "--new-only" in sys.argv:
        # Unrouted only
        print("=== UNROUTED ===")
        try:
            all_models = fetch_catalog()
        except Exception as e:
            print(f"\n  ERROR fetching catalog: {e}")
            sys.exit(1)
        candidates = filter_candidates(all_models, routed, only_providers, exclude_terms)
        print(active_filters(only_providers, exclude_terms))
        print_unrouted(candidates, only_providers)

    else:
        # Default when --only/--exclude used without --routes: show both
        print_routed(rules, only_providers)
        print()
        print("=== UNROUTED ===")
        try:
            all_models = fetch_catalog()
        except Exception as e:
            print(f"\n  ERROR fetching catalog: {e}")
            sys.exit(1)
        candidates = filter_candidates(all_models, routed, only_providers, exclude_terms)
        print(active_filters(only_providers, exclude_terms))
        print_unrouted(candidates, only_providers)

elif routes_value == "no" or "--new-only" in sys.argv:
    # Legacy --new-only / --routes no without provider filter
    print("=== UNROUTED ===")
    try:
        all_models = fetch_catalog()
    except Exception as e:
        print(f"\n  ERROR fetching catalog: {e}")
        sys.exit(1)

    routed = set(extract_model(r["cel"]) or "" for r in rules)
    candidates = filter_candidates(all_models, routed, only_providers, exclude_terms)
    print(active_filters(only_providers, exclude_terms))
    print_unrouted(candidates, only_providers)

else:
    # Standard: show configured routes + runtime probe
    print("=== CONFIGURED ROUTES ===")
    model_names = [extract_model(r["cel"]) or r["cel"] for r in rules]
    max_model = max((display_width(n) for n in model_names), default=22)
    max_model = max(max_model, 8)
    header = f"  {pad_to('Priority', 8)} {pad_to('Model', max_model)} -> Target"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for rule in rules:
        mn  = extract_model(rule["cel"]) or rule["cel"]
        tgt = f"{rule['provider']}/{rule['model']}" if rule["provider"] and rule["model"] else "NO TARGET"
        print(f"  {pad_to(str(rule['priority']), 8)} {pad_to(mn, max_model)} -> {tgt}")

    if not rules:
        print("  [no routing rules found in DB]")
        sys.exit(0)

    print()
    print("=== RUNTIME PROBE ===")
    prov_w = 14
    quota_w = 9
    avg_w = 12
    header = f"   {pad_to('#', 3)} {pad_to('Model', max_model)} {pad_to('Provider', prov_w)} {'Latency':>9} {pad_to('Quota', quota_w)} {pad_to('Avg', avg_w)}"
    print(header)
    print("   " + "-" * ansi_width(header))

    lat_history = load_latency_history()

    ok_probe_count = 0
    err_probe_count = 0
    for i, rule in enumerate(rules, 1):
        mn = extract_model(rule["cel"])
        quota = MODEL_QUOTA.get(mn, "")
        if not mn:
            print(f"  {pad_to(str(i), 3)} {pad_to(rule['id'], max_model)} [no model in CEL]")
            continue
        payload = json.dumps({
            "model": mn,
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1,
        }).encode("utf-8")
        def probe_once():
            req2 = urllib.request.Request(
                f"{bifrost_url}/v1/chat/completions",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            return urllib.request.urlopen(req2, timeout=15)

        try:
            resp = probe_once()
        except Exception as e:
            err_raw = str(e).splitlines()[0]
            err_str = short_error(err_raw)
            if err_str in ("Timeout", "500 Server Error"):
                try:
                    resp = probe_once()
                except Exception as e2:
                    err_raw = str(e2).splitlines()[0]
                    err_str = short_error(err_raw)
                    err_col = f"\033[91m{err_str}\033[0m"
                    avg_str = avg_latency_str(lat_history, mn)
                    print(f"   {pad_to(str(i), 3)} {pad_to(mn, max_model)} {pad_ansi(err_col, prov_w)} {'':>9} {pad_to(quota, quota_w)} {pad_to(avg_str, avg_w)}")
                    err_probe_count += 1
                    continue
            else:
                err_col = f"\033[91m{err_str}\033[0m"
                avg_str = avg_latency_str(lat_history, mn)
                print(f"   {pad_to(str(i), 3)} {pad_to(mn, max_model)} {pad_ansi(err_col, prov_w)} {'':>9} {pad_to(quota, quota_w)} {pad_to(avg_str, avg_w)}")
                err_probe_count += 1
                continue
        body = json.loads(resp.read().decode("utf-8"))
        extra = body.get("extra_fields", {})
        prov = extra.get("provider", "UNKNOWN")
        lat  = extra.get("latency", 0)
        lat_str = f"{int(lat):,}ms"
        record_latency(lat_history, mn, lat)
        avg_str = avg_latency_str(lat_history, mn)
        prov_col = f"\033[92m{prov}\033[0m" if prov == rule["provider"] else f"\033[93m{prov}\033[0m"
        print(f"   {pad_to(str(i), 3)} {pad_to(mn, max_model)} {pad_ansi(prov_col, prov_w)} {lat_str:>9} {pad_to(quota, quota_w)} {pad_to(avg_str, avg_w)}")
        ok_probe_count += 1

    save_latency_history(lat_history)
    if err_probe_count == 0:
        print(f"\n  \033[92mAll {ok_probe_count} routes healthy\033[0m")
    else:
        print(f"\n  \033[92m{ok_probe_count} OK\033[0m, \033[91m{err_probe_count} ERROR\033[0m")
