import sys
from pathlib import Path

content = Path('setup-ralph-loop.py').read_text()

# Check if assessment is already there
if 'assess_task_fit' in content:
    print('File already has assessment function')
    sys.exit(0)

# Add typing import
content = content.replace('from pathlib import Path', 'from pathlib import Path\nfrom typing import Optional, Tuple')

# Add pattern dictionaries after docstring
patterns = '''
# Task-fit assessment patterns
RALPH_POOR_FIT_PATTERNS = {
    "research": {
        "keywords": ["research", "investigate", "explore", "learn about"],
        "reason": "Research is exploratory, not iterative",
        "alternative": "Use /research or direct investigation",
    },
}

RALPH_GOOD_FIT_PATTERNS = {
    "refactor": {"keywords": ["refactor", "migrate"], "suggested_iterations": 10, "auto_promise": "REFACTORING_COMPLETE"},
    "bug_fix": {"keywords": ["fix the", "fix bug", "debug"], "suggested_iterations": 8, "auto_promise": "BUG_FIXED"},
}

def assess_task_fit(prompt: str):
    prompt_lower = prompt.lower()
    for cat, pat in RALPH_POOR_FIT_PATTERNS.items():
        if any(kw in prompt_lower for kw in pat["keywords"]):
            return False, pat["reason"], pat["alternative"], None, None
    for cat, pat in RALPH_GOOD_FIT_PATTERNS.items():
        if any(kw in prompt_lower for kw in pat["keywords"]):
            return True, None, None, pat["suggested_iterations"], pat["auto_promise"]
    return True, None, None, 5, "TASK_COMPLETE"

'''

content = content.replace('"""', '""", 1)
content = content.replace('"""\n\nimport', '"""' + patterns + '\nimport')

Path('setup-ralph-loop.py').write_text(content)
print('File enhanced with task-fit assessment')
