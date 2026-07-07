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
from datetime import datetime, timezone


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


# NOTE: resolve_list/safe_regex_match ported from hooks/model_router.py (dead code,
# unregistered in settings.json). Original loaded config but never consumed patterns —
# classify hook hardcoded defaults instead. Porting here makes config-driven pattern
# lists actually functional (extend/replace/remove modes per tier in claude-model-router.json).
def resolve_list(config, tier, field, defaults):
    """Resolve final keyword/pattern list for a tier based on mode."""
    tier_config = config.get(tier, {})
    mode = tier_config.get("mode", "extend")
    if mode == "replace":
        return tier_config.get(field, [])
    result = list(defaults)
    result.extend(tier_config.get(field, []))
    remove_key = f"remove_{field}"
    for item in tier_config.get(remove_key, []):
        if item in result:
            result.remove(item)
    return result


def safe_regex_match(patterns, text):
    """Test if any pattern matches text, silently skipping invalid regexes."""
    for p in patterns:
        try:
            if re.search(p, text):
                return True
        except re.error:
            pass
    return False


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

    opus_keywords = resolve_list(config, 'opus', 'keywords', default_opus_keywords)
    haiku_patterns = resolve_list(config, 'haiku', 'patterns', default_haiku_patterns)
    sonnet_patterns = resolve_list(config, 'sonnet', 'patterns', default_sonnet_patterns)

    has_opus_keyword = any(kw in prompt_lower for kw in opus_keywords)

    # Opus: complexity keyword + length (not bare word count alone)
    # 200+ words with a complexity keyword → opus
    # 100+ words with '?' + complexity keyword → opus
    # Bare long prompt without complexity keywords → stays on current model
    has_opus_signal = has_opus_keyword and (word_count > opus_word_count or (word_count > opus_question_word_count and '?' in prompt))

    if has_opus_signal:
        return 'opus'

    # Local: mechanical edits + trivial interactions — prefer over haiku
    # when both match, local saves paid API cost.
    # PRECEDENCE: local_patterns is checked BEFORE haiku_patterns. The two lists
    # overlap (e.g. rename/format/lint appear in both), so ordering is load-bearing
    # — do not reorder these blocks. local_patterns is also gated by word_count<=12,
    # which narrows the overlap to short single-file operations.
    local_patterns = [
        r'^(yes|no|ok|okay|sure|yep|nope|y|n)$',
        r'^(thanks|thank you|thx|ty)$',
        r'^(continue|go on|next|done|stop|quit|exit)$',
        r'^(show|print|list|tell me about|what is|where is)\s+\w{0,20}$',
        r'^(format|lint|check)\s+\w+$',
        r'^~\s+\w{0,20}$',
        # Mechanical edits — short, single-file operations, all anchored
        r'^(rename|move|copy|delete|remove|insert|replace|add)\s+\w+$',
        r'^(extract|inline|convert|wrap|unwrap)\s+\w+$',
        r'^(update|change|set)\s+(the\s+)?\w+\s+(to|in|on)\s+\w+$',
        r'^(sort|reorder|alphabetize)\s+\w+$',
        r'^(strip|trim|clean|dedupe|dedup)\s+\w+$',
    ]
    is_local_task = word_count <= 12 and any(
        re.search(p, prompt_lower) for p in local_patterns
    )
    if is_local_task:
        return 'local'

    # Haiku: routine operations (git, lint, format, version bump)
    # Only when word count is short — local takes priority for trivial tasks
    is_haiku_task = word_count < haiku_max_word_count and any(
        re.search(p, prompt_lower) for p in haiku_patterns
    )
    if is_haiku_task:
        return 'haiku'

    if any(re.search(p, prompt_lower) for p in sonnet_patterns):
        return 'sonnet'

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
        'written_at': datetime.now(timezone.utc).isoformat(),
        'turn_counter': data.get('turn_counter', 0),
        'consumed': False,
    }
    write_recommendation(state_path, rec_data)

    # Write a task-type hint for ccr-custom-router.js (per-request routing authority).
    # Maps classify tier -> router taskType. Best-effort: on any failure the router
    # falls back to its own inferTaskType() heuristic, so this never blocks routing.
    try:
        hooks_dir = pathlib.Path(__file__).resolve().parent.parent
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))
        from write_routing_hint import write_hint  # type: ignore[import-not-found]
        TIER_TO_TASK_TYPE = {
            'opus': 'reasoning',
            'sonnet': 'coding',
            'haiku': 'background',
            'local': 'local-coding',
        }
        task_type = TIER_TO_TASK_TYPE.get(recommendation)
        if task_type:
            write_hint(task_type, session_id)
    except Exception:
        pass

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
