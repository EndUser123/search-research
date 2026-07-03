#!/usr/bin/env python3
"""UserPromptSubmit hook: classify prompt complexity and write recommendation.

Reads state from config.json, classifies prompt, writes recommendation.json
to .claude/state/model-router/{terminal_id}/{session_id}/

warn mode: injects systemMessage, exits 0
autoswitch mode: writes recommendation, exits 0 (apply hook handles switching)
"""

import json
import sys
import re
import os
import pathlib
from datetime import datetime


def get_state_path(terminal_id, session_id):
    """Compute state directory path."""
    return pathlib.Path(os.environ.get("CSF_STATE_DIR") or str(pathlib.Path("P:/") / ".claude" / "state")) / 'model-router' / terminal_id / session_id


def load_session_config(state_path):
    """Load config from state file."""
    config_path = state_path / 'config.json'
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def write_recommendation(state_path, data):
    """Write recommendation state file atomically."""
    state_path.mkdir(parents=True, exist_ok=True)
    tmp = state_path / 'recommendation.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    tmp.replace(state_path / 'recommendation.json')


def classify_prompt(prompt, config):
    """Classify prompt complexity and return recommended tier."""
    prompt_lower = prompt.lower()
    word_count = len(prompt.split())

    thresholds = config.get('thresholds', {})
    opus_word_count = thresholds.get('opus_word_count', 200)
    opus_question_word_count = thresholds.get('opus_question_word_count', 100)
    haiku_max_word_count = thresholds.get('haiku_max_word_count', 60)

    default_opus_keywords = [
        'architect', 'architecture', 'evaluate', 'tradeoff', 'trade-off',
        'strategy', 'strategic', 'compare approaches', 'why does', 'deep dive',
        'redesign', 'across the codebase', 'investor', 'multi-system',
        'complex refactor', 'analyze', 'analysis', 'plan mode', 'rethink',
        'high-stakes', 'critical decision'
    ]
    default_haiku_patterns = [
        r'\bgit\s+(commit|push|pull|status|log|diff|add|stash|branch|merge|rebase|checkout)\b',
        r'\bcommit\b.*\b(change|push|all)\b', r'\bpush\s+(to|the|remote|origin)\b',
        r'\brename\b', r'\bre-?order\b', r'\bmove\s+file\b', r'\bdelete\s+file\b',
        r'\badd\s+(import|route|link)\b', r'\bformat\b', r'\blint\b',
        r'\bprettier\b', r'\beslint\b', r'\bremove\s+(unused|dead)\b',
        r'\bupdate\s+(version|package)\b'
    ]
    default_sonnet_patterns = [
        r'\bbuild\b', r'\bimplement\b', r'\bcreate\b', r'\bfix\b', r'\bdebug\b',
        r'\badd\s+feature\b', r'\bwrite\b', r'\bcomponent\b', r'\bservice\b',
        r'\bpage\b', r'\bdeploy\b', r'\btest\b', r'\bupdate\b', r'\brefactor\b',
        r'\bstyle\b', r'\bcss\b', r'\broute\b', r'\bapi\b', r'\bfunction\b'
    ]

    opus_keywords = default_opus_keywords
    haiku_patterns = default_haiku_patterns
    sonnet_patterns = default_sonnet_patterns

    has_opus_keyword = any(kw in prompt_lower for kw in opus_keywords)
    has_opus_signal = has_opus_keyword or (word_count > opus_question_word_count and '?' in prompt) or word_count > opus_word_count

    if has_opus_signal:
        return 'opus'

    is_haiku_task = word_count < haiku_max_word_count and any(
        re.search(p, prompt_lower) for p in haiku_patterns
    )
    if is_haiku_task:
        return 'haiku'

    if any(re.search(p, prompt_lower) for p in sonnet_patterns):
        return 'sonnet'

    # Local: very short prompts that don't match haiku patterns — safe for small model
    local_patterns = [
        r'^(yes|no|ok|okay|sure|yep|nope|y|n)$',
        r'^(thanks|thank you|thx|ty)$',
        r'^(continue|go on|next|done|stop|quit|exit)$',
        r'^(show|print|list|tell me about|what is|where is) \w{0,20}$',
        r'^(rename|move|copy|delete|remove) \w+ to \w+$',
        r'^(format|lint|check)\s+\w+$',
        r'^~\s+\w{0,20}$',
    ]
    is_local_task = word_count <= 8 and any(
        re.search(p, prompt_lower) for p in local_patterns
    )
    if is_local_task:
        return 'local'

    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    prompt = data.get('prompt', '')

    if prompt.lstrip().startswith('<'):
        sys.exit(0)

    if prompt.lstrip().startswith('~'):
        sys.exit(0)

    terminal_id = data.get('terminal_id', 'default')
    session_id = data.get('session_id', 'default')

    state_path = get_state_path(terminal_id, session_id)

    session_config = load_session_config(state_path)
    config = session_config.get('config', {})

    current_tier = session_config.get('current_tier', 'unknown')

    recommendation = classify_prompt(prompt, config)

    if not recommendation:
        sys.exit(0)

    TIER_TO_MODEL = {
        'haiku': 'claude-haiku-4-5-20251001',
        'sonnet': 'claude-sonnet-4-6',
        'opus': 'claude-opus-4-8',
        'local': 'claude-local-ornith',
    }

    new_model = None
    current_model = session_config.get('current_model', '')

    if recommendation == 'haiku' and current_tier in ('sonnet', 'opus'):
        new_model = TIER_TO_MODEL['haiku']
    elif recommendation == 'sonnet' and current_tier in ('haiku', 'opus'):
        suffix = re.search(r'(\[.+?\])$', current_model)
        new_model = TIER_TO_MODEL['sonnet'] + (suffix.group(1) if suffix else '')
    elif recommendation == 'opus' and current_tier in ('sonnet', 'haiku'):
        suffix = re.search(r'(\[.+?\])$', current_model)
        new_model = TIER_TO_MODEL['opus'] + (suffix.group(1) if suffix else '')

    action_mode = config.get('action', 'warn')

    rec_data = {
        'recommended_model': new_model or TIER_TO_MODEL.get(recommendation, recommendation),
        'recommended_tier': recommendation,
        'current_model': current_model,
        'current_tier': current_tier,
        'action_mode': action_mode,
        'written_at': datetime.now().isoformat(),
        'turn_counter': data.get('turn_counter', 0),
        'consumed': False,
    }
    write_recommendation(state_path, rec_data)

    try:
        log_file = pathlib.Path.home() / '.claude' / 'logs' / 'model-router.ndjson'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        snippet = prompt[:50].replace('\n', ' ')
        entry = {
            'ts': datetime.now().isoformat(),
            'terminal_id': terminal_id,
            'session_id': session_id,
            'current_tier': current_tier,
            'recommended_tier': recommendation,
            'action': action_mode,
            'prompt_snippet': snippet,
        }
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass

    if action_mode == 'warn' and new_model:
        base = new_model.split('[')[0]
        system_message = f'[model-router-hook] Recommended {base} for this task (current: {current_model}). Run /model {base} to switch, or prefix ~ to bypass.'
        print(json.dumps({'systemMessage': system_message}))

    sys.exit(0)


if __name__ == '__main__':
    main()
