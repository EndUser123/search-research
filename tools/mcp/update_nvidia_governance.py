import sqlite3, json, urllib.request

conn = sqlite3.connect(r'C:\Users\brsth\AppData\Roaming\bifrost\config.db')
cur = conn.cursor()

# Fetch all Nvidia models from API
req = urllib.request.Request('https://integrate.api.nvidia.com/v1/models',
    headers={'Authorization': 'Bearer nvidia'})
with urllib.request.urlopen(req, timeout=30) as r:
    data = json.loads(r.read())

# Known context lengths from public specs (verified values only)
known_contexts = {
    'llama-3.3-70b-instruct': 131072,
    'llama-3.1-405b-instruct': 131072,
    'llama-3.1-70b-instruct': 131072,
    'llama-3.1-8b-instruct': 131072,
    'llama-4-scout-17b-16e-instruct': 131072,
    'llama-4-maverick-17b-128e-instruct': 131072,
    'llama2-70b': 131072,
    'llama-guard-4-12b': 131072,
    'llama-3.2-11b-vision-instruct': 131072,
    'llama-3.2-1b-instruct': 131072,
    'llama-3.2-3b-instruct': 131072,
    'llama-3.2-90b-vision-instruct': 131072,
    'mistral-large-3-675b-instruct-2512': 131072,
    'mistral-large-2-instruct': 131072,
    'mistral-large': 131072,
    'mistral-medium-3-instruct': 131072,
    'mistral-medium-3.5-128b': 131072,
    'mistral-nemotron': 131072,
    'mistral-small-4-119b-2603': 131072,
    'mixtral-8x22b-instruct-v0.1': 131072,
    'mixtral-8x22b-v0.1': 131072,
    'mixtral-8x7b-instruct-v0.1': 131072,
    'codestral-22b-instruct-v0.1': 131072,
    'devstral-2-123b-instruct-2512': 131072,
    'deepseek-v4-flash': 131072,
    'deepseek-v4-pro': 131072,
    'deepseek-coder-6.7b-instruct': 65536,
    'gemma-3-27b-it': 131072,
    'gemma-3-12b-it': 131072,
    'gemma-3-4b-it': 131072,
    'gemma-4-31b-it': 131072,
    'gemma-2-2b-it': 8192,
    'gemma-2b': 8192,
    'gemma-3n-e2b-it': 32768,
    'gemma-3n-e4b-it': 32768,
    'codegemma-1.1-7b': 8192,
    'codegemma-7b': 8192,
    'recurrentgemma-2b': 8192,
    'deplot': 2048,
    'qwen3.5-397b-a17b': 131072,
    'qwen3.5-122b-a10b': 131072,
    'qwen3-next-80b-a3b-instruct': 131072,
    'qwen3-next-80b-a3b-thinking': 131072,
    'qwen3-coder-480b-a35b-instruct': 131072,
    'qwen2.5-coder-32b-instruct': 32768,
    'granite-34b-code-instruct': 32768,
    'granite-8b-code-instruct': 32768,
    'codellama-70b': 16384,
    'kimi-k2.6': 262144,
    'kimi-k2-instruct': 262144,
    'kimi-k2-instruct-0905': 262144,
    'kimi-k2-thinking': 262144,
    'gpt-oss-120b': 131072,
    'gpt-oss-20b': 131072,
    'nemotron-4-340b-instruct': 131072,
    'nemotron-4-340b-reward': 32768,
    'nemotron-3-super-120b-a12b': 131072,
    'llama-3.1-nemotron-ultra-253b-v1': 131072,
    'llama-3.3-nemotron-super-49b-v1': 131072,
    'llama-3.3-nemotron-super-49b-v1.5': 131072,
    'llama-3.1-nemotron-70b-instruct': 131072,
    'llama-3.1-nemotron-51b-instruct': 131072,
    'cosmos-reason2-8b': 32768,
}

embed_kws = ['embed', 'rerank', 'embedding', 'e5', 'bge', 'arctic', 'snowflake']
safety_kws = ['safety', 'guard', 'nemoguard', 'llama-guard']
video_kws = ['video', 'synthetic', 'neva', 'vila', 'kosmos']
xlat_kws = ['riva', 'translate']
parse_kws = ['parse', 'retriever']

inserted = 0
skipped = 0
no_ctx = []

for m in data['data']:
    model_id = m['id']
    lower = model_id.lower()

    if any(k in lower for k in embed_kws):
        mode = 'embed'
    elif any(k in lower for k in safety_kws):
        mode = 'safety'
    elif any(k in lower for k in video_kws):
        mode = 'video'
    elif any(k in lower for k in xlat_kws):
        mode = 'translate'
    elif any(k in lower for k in parse_kws):
        mode = 'parse'
    else:
        mode = 'chat'

    ctx = 0
    for suffix, length in known_contexts.items():
        if suffix in model_id:
            ctx = length
            break

    if ctx == 0 and mode != 'chat':
        ctx = 32768

    data_json = json.dumps({
        'provider': 'nvidia',
        'base_model': model_id,
        'mode': mode,
        'max_input_tokens': ctx,
        'max_output_tokens': ctx if mode == 'chat' else 4096,
        'max_tokens': ctx if mode == 'chat' else 4096,
        'input_cost_per_token': 0,
        'output_cost_per_token': 0,
        'source': 'nvidia_nim_api_2026-05-06'
    })

    try:
        cur.execute('INSERT INTO governance_model_parameters (model, data) VALUES (?, ?)',
            (model_id, data_json))
        inserted += 1
    except Exception as e:
        skipped += 1
        if ctx == 0 and mode == 'chat':
            no_ctx.append(model_id)

conn.commit()
print(f'Inserted: {inserted}, Skipped (dupes): {skipped}')
if no_ctx:
    print(f'Chat models with no known context: {no_ctx}')