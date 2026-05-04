import sqlite3, urllib.request, json, re, sys

db_path = r"C:\Users\brsth\AppData\Roaming\bifrost\config.db"
bifrost_url = "http://localhost:8080"
new_only = "--new-only" in sys.argv

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

def extract_model(cel):
    m = re.search(r'model\s*==\s*"([^"]+)"', cel)
    return m.group(1) if m else None

if not new_only:
    print("=== CONFIGURED ROUTES ===")
    for rule in rules:
        mn = extract_model(rule["cel"]) or rule["cel"]
        tgt = f"{rule['provider']}/{rule['model']}" if rule["provider"] and rule["model"] else "NO TARGET"
        print(f"  {mn} -> {tgt}  [priority={rule['priority']}]")

    if not rules:
        print("  [no routing rules found in DB]")
        sys.exit(0)

    print()
    print("=== RUNTIME PROBE ===")

    for rule in rules:
        mn = extract_model(rule["cel"])
        if not mn:
            print(f"  [skip {rule['id']} - no model in CEL]")
            continue
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
                lat = extra.get("latency", 0)
                req_model = extra.get("model_requested", "")
                status = "OK" if prov == rule["provider"] else "MISMATCH"
                print(f"  {mn}: provider={prov} latency={lat}ms model_requested={req_model} [{status}]")
        except Exception as e:
            print(f"  {mn}: ERROR {e}")
else:
    # --new-only: sweep /models from each configured provider, diff against routed models
    print("=== PROVIDER CATALOG SWEEP ===")

    # Get providers from config.json
    import pathlib
    cfg_path = pathlib.Path(db_path).parent / "config.json"
    with open(cfg_path) as f:
        cfg = json.load(f)

    routed_models = set(extract_model(r["cel"]) or "" for r in rules)

    for prov_name, prov_data in cfg.get("providers", {}).items():
        base = prov_data.get("network_config", {}).get("base_url")
        if not base:
            continue
        # Use the list_models path (respect overrides via custom_provider_config)
        overrides = prov_data.get("custom_provider_config", {}).get("request_path_overrides", {})
        list_path = overrides.get("list_models", "/v1/models")
        url = f"{base.rstrip('/')}{list_path}"

        prov_key = prov_data.get("keys", [{}])[0].get("value", "")
        if not prov_key:
            continue

        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {prov_key}"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                models = body.get("data", []) if isinstance(body, dict) else body
                for m in models:
                    mid = m.get("id", "")
                    if mid and mid not in routed_models:
                        print(f"  [{prov_name}] {mid}  -- no routing rule")
        except Exception as e:
            print(f"  [{prov_name}] ERROR: {e}")