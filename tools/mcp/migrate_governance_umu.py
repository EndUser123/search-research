#!/usr/bin/env python3
"""
Migrate governance_model_parameters to 5-field UMU schema.

Schema change:
  BEFORE: data = {provider, base_model, mode, max_input_tokens, ...}
  AFTER:  data = {
    bifrost_provider,  -- Bifrost configured provider (MiniMax, Nvidia, etc.)
    host,              -- API host (extracted from current provider, or mapped)
    vendor,            -- model creator/owner (extracted from model string)
    model_slug,        -- immutable model identifier
    base_model,        -- unchanged
    mode,              -- unchanged
    max_input_tokens,  -- unchanged
    ...
  }

UMU format: {host}://{vendor}/{model_slug}

Migration steps:
1. Compute new fields for each row
2. Update data JSON
3. Verify UMU regex for all rows
"""

from __future__ import annotations
import sqlite3, json, re

DB_PATH = r'C:\Users\brsth\AppData\Roaming\bifrost\config.db'

# ---------------------------------------------------------------------------
# Vendor extraction
# ---------------------------------------------------------------------------

# Registered vendor prefixes (authoritative list)
# Maps model string prefix → vendor name
VENDOR_PREFIX_MAP: dict[str, str] = {
    'openai/': 'openai',
    'anthropic/': 'anthropic',
    'meta/': 'meta',
    'mistralai/': 'mistralai',
    'mistral/': 'mistralai',
    'moonshotai/': 'moonshotai',
    'moonshot/': 'moonshotai',
    'deepseek/': 'deepseek',
    'google/': 'google',
    'googleai/': 'google',
    'cohere/': 'cohere',
    'ai21/': 'ai21',
    'jamba': 'ai21',           # ai21 jamba models (no leading slash)
    'aws/': 'amazon',
    'amazon/': 'amazon',
    'amazon-nova/': 'amazon',
    'bedrock/': 'amazon',
    'azure/': 'microsoft',
    'openrouter/': 'openrouter',
    'groq/': 'groq',
    'cerebras/': 'cerebras',
    'nvidia/': 'nvidia',
    'fireworks_ai/': 'fireworks',
    'fireworks/': 'fireworks',
    'together_ai/': 'together',
    'together/': 'together',
    'replicate/': 'replicate',
    'anyscale/': 'anyscale',
    'perplexity/': 'perplexity',
    'xai/': 'xai',
    'grok': 'xai',             # grok models without slash
    'anthropic-claude': 'anthropic',  # bedrock style
    'meta-llama': 'meta',
    'meta_llama': 'meta',
    'novita/': 'novita',
    'deepinfra/': 'deepinfra',
    'vertex_ai/': 'google',
    'vercel_ai_gateway/': 'vercel',
    'lambda_ai/': 'lambda',
    'sambanova/': 'sambanova',
    'snowflake/': 'snowflake',
    'watsonx/': 'ibm',
    'ibm-granite/': 'ibm',
    'ibm/': 'ibm',
    ' volcengine/': 'volcengine',
    ' volc/': 'volcengine',
    'ollama/': 'ollama',
    'local/': 'local',
    'ft:': 'openai',           # fine-tuned OpenAI models
    'huggingface/': 'huggingface',
    'hf/': 'huggingface',
    'codellama/': 'meta',
    'llama/': 'meta',
    'qwen/': 'qwen',
    'qwen2': 'qwen',
    'qwen3': 'qwen',
    'gemma': 'google',
    'phi3': 'microsoft',
    'phi4': 'microsoft',
    'phi': 'microsoft',
    'wizardcoder': 'wizard',
    'wizardlm': 'wizard',
    'codegemma': 'google',
    'starcoder': 'huggingface',
    'starchat': 'huggingface',
    'bakllama': 'huggingface',
    'open-orca': 'openorca',
    'openorca': 'openorca',
    ' dolphin': 'cognitivecomputations',
    'dolphin-mixtral': 'cognitivecomputations',
    'mixtral': 'mistralai',
    'nexusraven': 'nexus',
    'shieldgemma': 'google',
    'meditron': 'meditron',
    'sailor2': 'sailor',
    'sailor': 'sailor',
    'vicuna': 'vicuna',
    'llava': 'llava',
    'hermes3': 'nousresearch',
    'hermes': 'nousresearch',
    'stablelm2': 'stabilityai',
    'stablelm': 'stabilityai',
    'reader-lm': 'deepmind',
    'nexusraven': 'nexus',
    'yarn': 'yarn',
    'granite': 'ibm',
    'granite-code': 'ibm',
    'granite3': 'ibm',
    'bespoke-minicheck': 'bespoke',
    'smollm': 'huggingface',
    'phind': 'phind',
    'command-r': 'cohere',
    'commandr': 'cohere',
    'thedrummer': 'thedrummer',
    'sao10k': 'sao10k',
    'switchpoint': 'switchpoint',
    'poolside': 'poolside',
    'aion-labs': 'aionlabs',
    'aion': 'aionlabs',
    'bytedance': 'bytedance',
    'xiaomi': 'xiaomi',
    'stepfun': 'stepfun',
    'inception': 'inception',
    'apac': 'amazon',
    'eu.': 'amazon',  # bedrock region prefixes
    'us.': 'amazon',
    'global.': 'amazon',
    'jp.': 'amazon',
    'au.': 'amazon',
    'arcee-ai': 'arcee',
    'arceeai': 'arcee',
    'prime-intellect': 'primeintellect',
    'deepcogito': 'deepcogito',
    'kwaipilot': 'kwaipilot',
    'relace': 'relace',
    'nest': 'nest',
    'symmetrically': 'symmetrically',
    'solar': 'upstage',
    'tencent': 'tencent',
    'hunyuan': 'tencent',
    'nex-agi': 'nexagi',
    'nex': 'nexagi',
    'alibaba': 'alibaba',
    'tongyi': 'alibaba',
    'baidu': 'baidu',
    'ernie': 'baidu',
    'cobuddy': 'baidu',
    'replicateopenai': 'openai',
    'openrouter/': 'openrouter',
    'openai/': 'openai',
}

# Special case: model strings that are just a vendor name with no model-id
SINGLE_TOKEN_MODELS: set = {
    'command-r', 'command-r-plus', 'command-r-plus-08-2024',
    'llama2', 'llama3', 'llama3.1', 'llama3.2', 'llama3.3', 'llama4',
    'mistral', 'mistral-large', 'mistral-medium', 'mistral-nemo',
    'mixtral', 'mixtral-8x7b', 'mixtral-8x22b',
    'gpt-4', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo',
    'gemini', 'gemini-pro', 'gemini-flash',
    'claude', 'claude-2', 'claude-3', 'claude-3.5',
    'davinci', 'babbage', 'ada', 'curie',
}


def extract_vendor(model: str, current_host: str) -> str:
    """Extract vendor from model string."""
    model_lower = model.lower()

    # Handle fine-tune prefix
    if model_lower.startswith('ft:'):
        return 'openai'

    # Handle bedrock complex paths like bedrock/eu-central-1/6-month-commitment/anthropic.claude-v1:0
    if current_host == 'bedrock':
        # Extract vendor from path segment containing a dot (vendor.model format)
        parts = model.split('/')
        for part in parts:
            if '.' in part:
                # e.g. anthropic.claude-v1:0 or meta.llama3-8b-instruct-v1:0
                vendor_part = part.split('.')[0]
                return VENDOR_PREFIX_MAP.get(vendor_part, vendor_part)
        # Fallback: first part after bedrock region/commitment
        for part in parts[2:]:  # skip bedrock/region/commitment
            if part and '.' not in part and 'commitment' not in part:
                return VENDOR_PREFIX_MAP.get(part, part)
        return 'amazon'

    # Handle fireworks_ai long paths: fireworks_ai/accounts/fireworks/models/...
    if '/' in model and model.count('/') >= 3:
        # e.g. fireworks_ai/accounts/fireworks/models/cogito-v1-preview-llama-70b
        # vendor = 'fireworks'
        return 'fireworks'

    # Handle openrouter paths:
    # - openrouter/vendor/model (3+ segments): vendor is parts[1]
    # - vendor/model:free (2 segments, free tier): vendor is parts[0]
    if '/' in model and current_host == 'openrouter':
        parts = model.split('/')
        if len(parts) >= 3:
            return parts[1]  # host/vendor/model format
        elif len(parts) == 2:
            return parts[0]  # vendor/model:free format (first segment is vendor)
        return 'openrouter'

    # Standard case: first segment before / is the vendor prefix
    if '/' in model:
        first = model.split('/')[0].lower()
        if first in VENDOR_PREFIX_MAP:
            return VENDOR_PREFIX_MAP[first]
        return first

    # No slash: single token model
    if model_lower in SINGLE_TOKEN_MODELS:
        return VENDOR_PREFIX_MAP.get(model_lower, current_host)

    # Try prefix matching
    for prefix, vendor in VENDOR_PREFIX_MAP.items():
        if model_lower.startswith(prefix):
            return vendor
        # Also check without trailing slash for models like "mistral:7b..."
        if prefix.endswith('/') and model_lower.startswith(prefix[:-1]):
            return vendor

    # Fallback: use current_host as vendor
    return VENDOR_PREFIX_MAP.get(current_host, current_host)


def extract_model_slug(model: str, vendor: str) -> str:
    """Extract model slug from model string."""
    # Remove vendor prefix from model string to get slug
    model_lower = model.lower()

    # Handle ft: prefix
    if model_lower.startswith('ft:'):
        return model[3:]  # everything after 'ft:'

    # Handle bedrock complex paths
    if '/' in model:
        parts = model.split('/')
        slug = parts[-1]
        # Strip :free suffix for OpenRouter free tier models
        if slug.endswith(':free'):
            slug = slug[:-5]
        return slug

    # Handle :variant suffix (e.g., smollm:1.7b-base-v0.2-q5_1)
    if ':' in model and '/' not in model:
        return model  # return as-is

    return model

    # Otherwise last segment after /
    return model.split('/')[-1]


# ---------------------------------------------------------------------------
# Bifrost provider mapping
# ---------------------------------------------------------------------------

# Map governance hosts -> Bifrost configured providers
# Only for the 7 free/subscription providers; others map to themselves
HOST_TO_BIFROST_PROVIDER: dict[str, str] = {
    'nvidia': 'nvidia',
    'cerebras': 'cerebras',
    'groq': 'groq',
    'mistral': 'mistral',
    'minimax': 'minimax',
    'zai': 'z.ai',
}

# For all other hosts, bifrost_provider = host
def get_bifrost_provider(host: str) -> str:
    return HOST_TO_BIFROST_PROVIDER.get(host, host)


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

UMU_REGEX = re.compile(r'^[a-z0-9._-]+://[a-z0-9._:/-]+/[a-zA-Z0-9._:/\(\)-]+$')


def migrate_row(model: str, data: dict) -> dict | None:
    """Transform a row to the 5-field schema.

    Returns None if row is already migrated (has bifrost_provider).
    """
    # Idempotency: skip if already migrated
    if 'bifrost_provider' in data:
        return None

    host = data.get('provider', '')
    vendor = extract_vendor(model, host)
    slug = extract_model_slug(model, vendor)
    bifrost_provider = get_bifrost_provider(host)

    new_data = {
        'bifrost_provider': bifrost_provider,
        'host': host,
        'vendor': vendor,
        'model_slug': slug,
        # preserve all existing fields
        'base_model': data.get('base_model'),
        'mode': data.get('mode'),
        'max_input_tokens': data.get('max_input_tokens'),
        'max_output_tokens': data.get('max_output_tokens'),
        'max_tokens': data.get('max_tokens'),
        'input_cost_per_token': data.get('input_cost_per_token'),
        'output_cost_per_token': data.get('output_cost_per_token'),
        'source': data.get('source'),
    }

    return new_data


def sanitize_slug(slug: str) -> str:
    """Normalize model slug for UMU regex."""
    # Remove size annotations like (3B), (7B), etc.
    import re
    slug = re.sub(r'\s*\([^)]*\)\s*', '', slug).strip()
    # Replace @ versioning with -
    slug = slug.replace('@', '-')
    return slug


def build_umu(new_data: dict) -> str:
    return f"{new_data['host']}://{new_data['vendor']}/{sanitize_slug(new_data['model_slug'])}"


def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Validate UMU regex on a sample of NOT-YET-MIGRATED rows
    print("=== Pre-migration validation ===")
    cur.execute('''
        SELECT model, data FROM governance_model_parameters
        WHERE json_extract(data, '$.mode') = 'chat'
          AND json_extract(data, '$.bifrost_provider') IS NULL
        ORDER BY random()
        LIMIT 20
    ''')
    sample_rows = cur.fetchall()
    validated = 0
    failed = 0
    for r in sample_rows:
        d = json.loads(r[1])
        nd = migrate_row(r[0], d)
        if nd is None:
            continue  # already migrated, skip
        validated += 1
        umu = build_umu(nd)
        valid = bool(UMU_REGEX.match(umu))
        if not valid:
            failed += 1
            print(f"  INVALID: {umu} | {r[0]}")

    if failed:
        print(f"\n{failed}/{validated} validated sample rows have invalid UMUs — fix extraction before proceeding")
        return

    if validated == 0:
        print("All rows already migrated — nothing to do")
        return

    print(f"Sample valid ({validated} rows) — proceeding with full migration\n")

    print(f"Sample valid — proceeding with full migration\n")

    # Full migration
    cur.execute('SELECT model, data FROM governance_model_parameters')
    rows = cur.fetchall()

    updated = 0
    skipped = 0
    errors = 0
    umu_failures = []

    for r in rows:
        try:
            d = json.loads(r[1])
            nd = migrate_row(r[0], d)
            if nd is None:
                skipped += 1
                continue
            umu = build_umu(nd)

            if not UMU_REGEX.match(umu):
                umu_failures.append((r[0], umu))
                continue

            cur.execute(
                'UPDATE governance_model_parameters SET data = ? WHERE model = ?',
                (json.dumps(nd), r[0])
            )
            updated += 1
        except Exception as e:
            errors += 1
            print(f"Error on {r[0]}: {e}")

    conn.commit()

    print(f"Updated: {updated}")
    print(f"Skipped (already migrated): {skipped}")
    print(f"Errors: {errors}")
    print(f"UMU failures: {len(umu_failures)}")

    if umu_failures:
        print("\nUMU failures (first 10):")
        for m, u in umu_failures[:10]:
            print(f"  {m} -> {u}")


if __name__ == '__main__':
    run_migration()