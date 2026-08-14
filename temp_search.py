import subprocess
result = subprocess.run(
    ["python", "-m", "search_research.cli",
     "--mode", "web",
     "--providers", "tavily",
     "Claude Code hooks command prompt agent type implementation"],
    cwd=r"P:\packages\.claude-marketplace\plugins\search-research",
    capture_output=True, text=True, timeout=120
)
print("STDOUT:", result.stdout[:3000] if result.stdout else "empty")
print("STDERR:", result.stderr[:1000] if result.stderr else "empty")
print("RC:", result.returncode)
