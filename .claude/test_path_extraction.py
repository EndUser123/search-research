"""Test path extraction to understand P:\c garbling."""
import re

_PATTERN_MKDIR_WIN = re.compile(
    r'mkdir\s+(?:-p\s+)?["\']?([A-Za-z]:[\\/][^\s"\';&|]+)', re.IGNORECASE
)
_PATTERN_MKDIR_UNIX = re.compile(r'mkdir\s+(?:-p\s+)?["\']?(/[^\s"\';&|]+)', re.IGNORECASE)

BASH_PATH_PATTERNS = [
    _PATTERN_MKDIR_WIN,
    _PATTERN_MKDIR_UNIX,
]

def extract_paths_from_bash(command: str) -> list[str]:
    paths = []
    for pattern in BASH_PATH_PATTERNS:
        matches = pattern.findall(command)
        paths.extend(matches)
    return list(set(paths))

# Test commands
cmd1 = 'mkdir -p "C:/Users/brsth/.claude/plans/"'
cmd2 = 'mkdir -p /c/Users/brsth/.claude/plans/'
cmd3 = 'mkdir -p "C:/Users/brsth/.claude/plans/"  [C:/Users/brsth/.claude/plans/]'

print("Test 1:", repr(cmd1))
print("Paths:", extract_paths_from_bash(cmd1))
print()
print("Test 2:", repr(cmd2))
print("Paths:", extract_paths_from_bash(cmd2))
print()
print("Test 3:", repr(cmd3))
print("Paths:", extract_paths_from_bash(cmd3))
