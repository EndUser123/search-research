"""Integration test: /red-team:red-team command resolves to a real file.

Cheapest proxy for 'the slash command launches' (TEST-5). A true launch test
would invoke Claude Code itself and remains a manual Plugin Mutation Checklist
step 5. Catches the 'registered + cached but command file missing' class.
"""

from pathlib import Path

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_CACHE_ROOT = Path.home() / ".claude" / "plugins" / "cache" / "local" / "red-team"


def test_command_file_in_source():
    assert (_PLUGIN_ROOT / "commands" / "red-team.md").is_file()


def test_cache_dir_exists_with_command():
    caches = sorted(_CACHE_ROOT.glob("*/commands/red-team.md"))
    assert caches, f"no cached commands/red-team.md under {_CACHE_ROOT}"
