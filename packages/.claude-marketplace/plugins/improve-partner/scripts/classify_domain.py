#!/usr/bin/env python3
import sys, re, json
from pathlib import Path

DOMAIN_SIGNALS = {
    'prompt-review': [
        (r'system_prompt|SystemMessage|role.*system', 'system_prompt_pattern'),
        (r'SKILL\.md|frontmatter|anti-sycophancy|epistemic', 'skill_or_prompt_instruction'),
        (r'output_schema|response_format|FACT:|INFERENCE:|RISK:|ASSUMPTION:', 'structured_prompt_controls'),
    ],
    'code-workflow-review': [
        (r'def |class |import |from .* import', 'source_code'),
        (r'timeout|latency|budget|elapsed|ThreadPoolExecutor|asyncio|parallel', 'execution_or_timing'),
        (r'test_|pytest|assert |traceback|exception', 'tests_or_failures'),
    ],
    'hook-plugin-audit': [
        (r'PreToolUse|PostToolUse|Stop|SubagentStop|UserPromptSubmit', 'hook_lifecycle'),
        (r'plugin\.json|\.claude-plugin|\.claude/hooks/|\.claude/skills/', 'plugin_or_claude_structure'),
        (r'MCP|CCR|settings\.json|slash.?command|plugin', 'tooling_or_routing'),
    ],
}

def classify(text):
    votes={k:[] for k in DOMAIN_SIGNALS}
    for domain, patterns in DOMAIN_SIGNALS.items():
        for pattern, label in patterns:
            if re.search(pattern, text, re.I|re.M):
                votes[domain].append(label)
    scores={k:len(v) for k,v in votes.items()}
    ranked=sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top, top_score = ranked[0]
    second, second_score = ranked[1]
    if top_score >= 2 and second_score >= 2:
        return {'domain':'hybrid','confidence':'medium','rationale':f'strong signals in {top} and {second}','alternative':top,'scores':scores}
    if top_score >= 3:
        conf='high'
    elif top_score >= 2:
        conf='medium'
    else:
        conf='low'
    if top_score == 0:
        top='code-workflow-review'
    return {'domain':top,'confidence':conf,'rationale':f'{top_score} signal(s) for {top}','alternative':second if second_score else None,'scores':scores}

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] != '-':
        text=Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
    else:
        text=sys.stdin.read()
    print(json.dumps(classify(text), indent=2))
