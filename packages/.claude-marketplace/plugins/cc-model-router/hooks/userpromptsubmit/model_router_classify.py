#!/usr/bin/env python3
"""UserPromptSubmit hook: hierarchical prompt classification with semantic scoring.

Pipeline: deterministic overrides → TF-IDF semantic scoring → hierarchical decision
(background vs active → reasoning vs coding) → confidence-based fallback.

Writes: recommendation.json (apply.py compat), ccr-routing-hint.json (router),
classify_log.jsonl (observability).
"""
import hashlib
import json
import sys
import os
import pathlib
from datetime import datetime, timezone

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(PLUGIN_ROOT / "__lib") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "__lib"))

HINT_FILE = pathlib.Path("P:/.claude/state/ccr-routing-hint.json")
CLASSIFY_LOG = pathlib.Path("P:/.claude/state/model-router/classify_log.jsonl")

TASK_TYPE_TO_TIER = {"background": "haiku", "coding": "sonnet", "reasoning": "opus", "local-coding": "local"}
TIER_TO_MODEL = {"haiku": "claude-haiku-4-5-20251001", "sonnet": "claude-sonnet-5", "opus": "claude-opus-4-8", "local": "claude-local-ornith"}


def get_state_path(terminal_id, session_id):
    return pathlib.Path(os.environ.get("CSF_STATE_DIR") or str(pathlib.Path("P:/") / ".claude" / "state")) / 'model-router' / terminal_id / session_id


def load_session_config(state_path):
    config_path = state_path / 'config.json'
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def write_recommendation(state_path, data):
    state_path.mkdir(parents=True, exist_ok=True)
    tmp = state_path / 'recommendation.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    tmp.replace(state_path / 'recommendation.json')


def read_prev_hint():
    try:
        if HINT_FILE.exists():
            return json.loads(HINT_FILE.read_text())
    except Exception:
        pass
    return None


def write_enriched_hint(task_type, session_id, result=None):
    HINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    hint = {"taskType": task_type, "sessionId": session_id, "ts": datetime.now(timezone.utc).isoformat()}
    if result:
        hint.update({"confidence": round(result.confidence, 4), "top_2": result.top_2,
                      "margin": round(result.margin, 4), "lowConfidence": result.low_confidence,
                      "backend": result.backend, "source": result.source})
    HINT_FILE.write_text(json.dumps(hint, indent=2), encoding="utf-8")


def write_observability(result, prompt, session_id, terminal_id, prev_context):
    try:
        CLASSIFY_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {"ts": datetime.now(timezone.utc).isoformat(), "session_id": session_id,
                 "terminal_id": terminal_id, "prompt_hash": hashlib.sha256(prompt.encode()).hexdigest()[:16],
                 "word_count": len(prompt.split()), "char_count": len(prompt),
                 "override": result.override, "stage_a": result.stage_a, "stage_b": result.stage_b,
                 "stage_c": result.stage_c,
                 "class_scores": {k: round(v, 4) for k, v in result.class_scores.items()},
                 "top_2": result.top_2, "margin": round(result.margin, 4),
                 "final_taskType": result.task_type, "low_confidence": result.low_confidence,
                 "backend": result.backend, "source": result.source, "prev_hint_context": prev_context}
        with open(CLASSIFY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    prompt = data.get('prompt', '')
    if prompt.lstrip().startswith('<') or prompt.lstrip().startswith('~'):
        sys.exit(0)

    terminal_id = data.get('terminal_id', 'default')
    session_id = data.get('session_id', 'default')
    state_path = get_state_path(terminal_id, session_id)

    session_config = load_session_config(state_path)
    config = session_config.get('config', {})
    current_model = session_config.get('current_model', '')
    current_tier = session_config.get('current_tier', 'unknown')

    prev_hint = read_prev_hint()
    prev_task_type = prev_hint.get('taskType') if prev_hint else None

    try:
        from classifier.pipeline import classify_pipeline
        result = classify_pipeline(prompt, None, config)
    except Exception as e:
        print(f"[model-router-classify] pipeline failed: {e}", file=sys.stderr)
        sys.exit(0)

    task_type = result.task_type
    tier = TASK_TYPE_TO_TIER.get(task_type, "sonnet")
    recommended_model = TIER_TO_MODEL.get(tier, '')

    write_enriched_hint(task_type, session_id, result)
    write_observability(result, prompt, session_id, terminal_id, prev_task_type)

    if tier != current_tier and recommended_model and recommended_model != current_model:
        rec_data = {'recommended_model': recommended_model, 'recommended_tier': tier,
                    'current_model': current_model, 'current_tier': current_tier,
                    'written_at': datetime.now(timezone.utc).isoformat(),
                    'turn_counter': data.get('turn_counter', 0), 'consumed': False}
        write_recommendation(state_path, rec_data)
        base = recommended_model.split('[')[0]
        cur = current_model.split('[')[0]
        msg = f'[model-router] {task_type} → {base} | now: {cur} | advisory'
        print(json.dumps({'systemMessage': msg}))

    try:
        log_file = pathlib.Path.home() / '.claude' / 'logs' / 'model-router.ndjson'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        snippet = prompt[:50].replace('\n', ' ')
        entry = {'ts': datetime.now(timezone.utc).isoformat(), 'terminal_id': terminal_id,
                 'session_id': session_id, 'current_tier': current_tier, 'task_type': task_type,
                 'tier': tier, 'confidence': round(result.confidence, 4), 'backend': result.backend,
                 'source': result.source, 'low_confidence': result.low_confidence, 'prompt_snippet': snippet}
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass
    sys.exit(0)


if __name__ == '__main__':
    main()
