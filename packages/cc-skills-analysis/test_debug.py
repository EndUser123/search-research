import re

def snap_to_word(remainder: str) -> str:
    """Snap start AND end of remainder to word boundaries, capped at ~100 chars."""
    r = re.search(r'\w', remainder)
    start_offset = r.start() if r else 0
    end_offset = start_offset + 100

    if end_offset < len(remainder):
        pre_end = remainder[start_offset:end_offset]
        # Find all complete words in pre_end (word followed by non-word in pre_end).
        candidates = []
        for m in re.finditer(r'\w+', pre_end):
            word_end = m.end()
            if word_end < len(pre_end):
                following = pre_end[word_end]
                if not following.isalnum() and following != '_':
                    candidates.append((m.start(), word_end))
        if candidates:
            end_offset = start_offset + candidates[-1][1]
        else:
            # No complete word found in pre_end. The cut went through a word.
            # Find the last word that starts before or at the cut.
            last_match = None
            for m in re.finditer(r'\w+', pre_end):
                last_match = m
            if last_match:
                # The word ends AFTER the cut in the actual remainder.
                if last_match.start() > 0:
                    # Word doesn't start at beginning — snap to its start
                    end_offset = start_offset + last_match.start()
                else:
                    # Word starts at position 0 — can't snap back further.
                    # This means we're in the middle of the FIRST word.
                    # Snap to END of the window as a last resort.
                    pass  # keep end_offset = start_offset + 100

    return remainder[start_offset:end_offset]

# Test cases
tests = [
    (" diagnostic" + "sthatisnotaword" + "x" * 200, "sthatisnotaword", "endswith"),
    (" work on the hooks module.", "work on the hooks module.", "full"),
    (":diagnostics/P:/.claude/hooks", "diagnostics/P:/.claude/hooks", "startswith_d"),
    ("ostics/P:/.claude/hooks", "ostics/P:/.claude/hooks", "full_path"),
    ("", "", "empty"),
    ("work on the hooks module.", "work on the hooks module.", "startswith_work"),
    (".claude/hooks/SomeFile.py and continue.", "claude", "path_mid"),
]

for remainder, expected, case in tests:
    phrase = snap_to_word(remainder)
    if case == "endswith":
        ok = phrase.endswith(expected)
    elif case == "startswith_d":
        ok = phrase.startswith(expected)
    elif case == "full":
        ok = phrase == expected
    elif case == "empty":
        ok = phrase == ""
    elif case == "startswith_work":
        ok = phrase.startswith(expected)
    elif case == "full_path":
        ok = phrase == expected
    elif case == "path_mid":
        ok = phrase.startswith("claude") or phrase.startswith("SomeFile")
    print(f"{'PASS' if ok else 'FAIL'} [{case}]: {phrase!r} (expected: {expected!r})")