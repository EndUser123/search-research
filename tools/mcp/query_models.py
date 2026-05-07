import sqlite3, json
DB_PATH = r'C:\Users\brsth\AppData\Roaming\bifrost\config.db'
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

print('='*70)
print('FREE-KEY PROVIDERS (Cerebras, Groq, Mistral, Nvidia)')
print('All chat mode >= 128k context qualify regardless of cost')
print('='*70)

for p in ['cerebras', 'groq', 'mistral', 'nvidia']:
    cur.execute('''
        SELECT model, json_extract(data, "$.max_input_tokens"),
               json_extract(data, "$.input_cost_per_token"),
               json_extract(data, "$.output_cost_per_token")
        FROM governance_model_parameters
        WHERE json_extract(data, "$.bifrost_provider") = ?
          AND json_extract(data, "$.mode") = "chat"
          AND json_extract(data, "$.max_input_tokens") >= 131072
        ORDER BY model
    ''', (p,))
    rows = cur.fetchall()
    print(f'\n[{p}] {len(rows)} models')
    for r in rows:
        cost_in = '${:.2f}/M'.format(r[2]*1e6) if r[2] > 0 else 'free'
        cost_out = '${:.2f}/M'.format(r[3]*1e6) if r[3] > 0 else 'free'
        print(f'  {r[0]} (ctx={r[1]:,}, in={cost_in}, out={cost_out})')

print()
print('='*70)
print('SUBSCRIPTION PROVIDERS (MiniMax, Z.AI) - free via subscription')
print('='*70)
for p in ['minimax', 'z.ai']:
    cur.execute('''
        SELECT model, json_extract(data, "$.max_input_tokens"),
               json_extract(data, "$.input_cost_per_token"),
               json_extract(data, "$.output_cost_per_token")
        FROM governance_model_parameters
        WHERE json_extract(data, "$.bifrost_provider") = ?
          AND json_extract(data, "$.mode") = "chat"
          AND json_extract(data, "$.max_input_tokens") >= 131072
        ORDER BY model
    ''', (p,))
    rows = cur.fetchall()
    print(f'\n[{p}] {len(rows)} models')
    for r in rows:
        cost_in = '${:.2f}/M'.format(r[2]*1e6) if r[2] > 0 else 'free'
        cost_out = '${:.2f}/M'.format(r[3]*1e6) if r[3] > 0 else 'free'
        print(f'  {r[0]} (ctx={r[1]:,}, in={cost_in}, out={cost_out})')

print()
print('='*70)
print('OPENROUTER (cost = 0, excludes moonshotai/minimax/z.ai/bytedance)')
print('='*70)
cur.execute('''
    SELECT model, json_extract(data, "$.vendor"),
           json_extract(data, "$.max_input_tokens")
    FROM governance_model_parameters
    WHERE json_extract(data, "$.bifrost_provider") = "openrouter"
      AND json_extract(data, "$.mode") = "chat"
      AND json_extract(data, "$.max_input_tokens") >= 131072
      AND json_extract(data, "$.input_cost_per_token") = 0
      AND json_extract(data, "$.output_cost_per_token") = 0
      AND json_extract(data, "$.vendor") NOT IN ("moonshotai", "minimax", "z.ai", "bytedance")
    ORDER BY json_extract(data, "$.vendor"), model
''')
rows = cur.fetchall()
by_vendor = {}
for r in rows:
    vendor = r[1]
    if vendor not in by_vendor:
        by_vendor[vendor] = []
    by_vendor[vendor].append((r[0], r[2]))

print(f'Total: {len(rows)} free models from {len(by_vendor)} vendors')
for vendor, models in sorted(by_vendor.items()):
    print(f'\n[{vendor}] {len(models)} models')
    for m, ctx in models[:8]:
        print(f'  {m} (ctx={ctx:,})')
    if len(models) > 8:
        print(f'  ... and {len(models)-8} more')
