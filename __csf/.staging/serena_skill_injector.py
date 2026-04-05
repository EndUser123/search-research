"""
UserPromptSubmit hook to inject serena-api skill for code analysis queries.
Detects semantic code analysis patterns and ensures skill is loaded.
"""
import re
import sys
from pathlib import Path

# Code analysis trigger patterns
CODE_ANALYSIS_PATTERNS = [
    r'\bfind\s+(all\s+)?(classes|functions|methods|symbols|references)\b',
    r'\bwhat\s+(references|uses|calls)\b',
    r'\banalyze\s+(code|class|hierarchy|structure)\b',
    r'\bsearch\s+(for\s+)?(functions|classes|symbols|methods)\b',
    r'\bunderstand\s+(code|codebase|structure|dependencies)\b',
    r'\bsymbol\s+(search|lookup|find|analysis)\b',
    r'\bcode\s+(intelligence|navigation|exploration)\b',
    r'\b(refactor|extract|inline)\s+\w+\b',
    r'\b(class\s+)?hierarchy\b',
    r'\binheritance\s+(chain|tree|structure)\b',
]

def detect_code_analysis(prompt: str) -> bool:
    """Check if prompt is asking for semantic code analysis."""
    prompt_lower = prompt.lower()
    for pattern in CODE_ANALYSIS_PATTERNS:
        if re.search(pattern, prompt_lower):
            return True
    return False

def main():
    prompt = sys.argv[-1] if len(sys.argv) > 1 else ""
    
    if detect_code_analysis(prompt):
        # Inject skill loading instruction
        skill_path = Path.cwd() / ".claude" / "skills" / "serena-api" / "SKILL.md"
        if skill_path.exists():
            print(f"\n[SKILL_INJECT] Loading serena-api skill for code analysis task")
            print(f"[SKILL_INJECT] Skill path: {skill_path}")
            # The skill will be loaded automatically by Claude's skill system
            # This just makes the intent explicit
            return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())
