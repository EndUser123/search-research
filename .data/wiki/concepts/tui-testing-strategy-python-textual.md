---
title: "TUI Testing Strategy — Python Textual Apps"
created: 2026-07-22
source: session-2026-07-22
tags: [testing, tui, textual, python, mutation-testing, property-based, hypothesis, pytest]
summary: >
  Four-layer testing stack for Textual TUI apps: pure-function unit tests,
  Hypothesis property-based tests for edge cases, Textual's run_test() for
  integration/UI behavior, and mutmut for test-quality verification. Each
  layer catches a different bug class that the others miss.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
---

## Summary

Testing a Textual TUI app requires four layers, each catching a different
class of bug. Coverage alone (tier 1) misses logic errors. Property-based
testing (Hypothesis) generates edge cases you didn't think of. Textual's
built-in `run_test()` drives the actual UI headlessly. Mutation testing
(mutmut) verifies your tests actually catch bugs by mutating the source.

## The four layers

### Layer 1: Pure-function unit tests (coverage + behavior)

Test functions that have no UI dependency: `format_size`, `scan_videos`,
`get_duration`, `list_drives`. These are testable with plain pytest.

```python
def test_format_size_gb():
    assert format_size(1_500_000_000) == "1.50 GB"

def test_scan_videos_finds_all_extensions(tmp_path):
    (tmp_path / "test.mp4").write_bytes(b"x" * 100)
    result = scan_videos(str(tmp_path))
    assert len(result) == 1
```

**Catches:** import errors, basic wiring, dead code, extension filtering.

**Misses:** UI interactions, threading, widget state, keybinding conflicts.

### Layer 2: Property-based tests (Hypothesis)

Generate thousands of inputs automatically. Instead of manually thinking
"what about negative numbers? empty folders? duplicate names?", Hypothesis
explores the input space and finds edge cases you missed.

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0))
def test_format_size_never_crashes(n):
    result = format_size(n)
    assert isinstance(result, str)
    assert "MB" in result or "GB" in result or "KB" in result

@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
def test_scan_videos_basenames(names):
    # Property: all found entries have valid video extensions
    result = scan_videos(test_folder)
    for basename, (path, size) in result.items():
        assert os.path.exists(path)
        assert size >= 0
```

**Catches:** edge cases you didn't think of (negative sizes, empty strings,
unicode paths, very large numbers, duplicate filenames).

**Misses:** UI behavior, widget interactions, threading.

**Key insight from research:** Property-based testing explores an infinite
input space — you never know if you're "done." Mutation testing enumerates
a finite problem space — you know when all mutants are killed. They are
complementary, not substitutes.
[source: Anders Hovmöller, "Mutation vs Property Based Testing", 2019, authority=2, evidence=3]

### Layer 3: Textual integration tests (run_test + snapshot)

Textual's `App.run_test()` runs the app headlessly and returns a `Pilot`
object for simulating keyboard/mouse interaction. This is the layer that
catches runtime bugs that static reading cannot.

```python
async def test_folder_browser_drills_into_drives():
    app = KeepSmallerCopyApp()
    async with app.run_test() as pilot:
        await pilot.click("#source-browse")
        await pilot.pause()
        # Click first drive in the tree
        tree = app.screen.query_one("#browser-tree", Tree)
        first_drive = tree.root.children[0]
        # Simulate selecting it
        tree.select_node(first_drive)
        await pilot.pause()
        # Should show drive CONTENTS, not the drive list again
        assert len(tree.root.children) > 0
        assert first_drive.data not in list_drives() or len(tree.root.children) != len(list_drives())
```

**Also: snapshot testing** via `pytest-textual-snapshot` — takes an SVG
screenshot, compares against baseline. Catches visual regressions.
[source: textual.textualize.io/guide/testing, authority=3, recency=3]
[source: github.com/Textualize/pytest-textual-snapshot]

**Catches:** keybinding conflicts (typing `m` in Input triggers Move),
focus management issues, screen transition bugs, folder browser navigation
broken, button state desync, DataTable rendering errors.

**Misses:** code paths that require real filesystem I/O timing, cross-drive
move behavior, ffprobe subprocess behavior.

### Layer 4: Mutation testing (mutmut)

Mutates the source code (changes `<` to `>`, removes lines, swaps `+`/`-`)
and checks if tests still pass. If a mutant survives, your tests don't
actually verify that code path.

```bash
pip install mutmut
mutmut run
```

**Catches:** tests that pass without actually testing anything (fake tests,
circular tests, tests that assert trivially-true properties).

**Key insight from research:** Mutation testing finds "pathological case"
bugs — hardcoded special cases that bypass logic but pass example-based
tests. Example: `if l == list(range(100)): return -1` passes all example
tests but mutmut catches it immediately.
[source: Anders Hovmöller, "Mutation vs Property Based Testing", 2019]

## What each layer catches for this specific app

| Bug class | Layer 1 | Layer 2 | Layer 3 | Layer 4 |
|---|---|---|---|---|
| `format_size` edge cases | ❌ | ✅ | — | ✅ |
| `scan_videos` duplicate basenames | ❌ | ✅ | — | ✅ |
| Folder browser drive navigation | — | — | ✅ | — |
| Keybinding hijacks Input typing | — | — | ✅ | — |
| Delete mode inverts logic | ❌ | ❌ | ✅ | ✅ |
| Move verification missing | ❌ | ❌ | ✅ | ✅ |
| Stop button doesn't interrupt | — | — | ✅ | — |
| Column labels misleading | — | — | ✅ | — |
| Tests that don't actually test | — | — | — | ✅ |

## Integration vs end-to-end for TUI apps

From Waleed Khan's research on TUI testing:

- **Integration testing** (Textual's `run_test`): hooks into the app's event
  loop, injects synthetic events, takes virtual screenshots. More direct,
  less flaky. Can mock filesystem and subprocess calls.
- **End-to-end testing** (PTY-based): simulates real terminal via PTY,
  sends keystrokes, reads screen output via terminal emulation (pyte).
  More realistic but flakier. Can't wait on internal operations.
[source: blog.waleedkhan.name/testing-tui-apps, authority=2, evidence=2]

**Recommendation:** integration testing (Textual's `run_test`) for this app.
It's already async, event-driven, and structured for testing. E2E/PTY is
overkill for a personal utility.

## Sources

- https://textual.textualize.io/guide/testing/ — official Textual testing docs (authority=3, recency=3)
- https://github.com/Textualize/pytest-textual-snapshot — snapshot testing plugin
- https://medium.com/@boxed/mutation-vs-property-based-testing-4c788b06f665 — mutation vs property comparison (authority=2, evidence=3)
- https://blog.waleedkhan.name/testing-tui-apps/ — TUI testing patterns (authority=2, evidence=2)
- https://increment.com/testing/in-praise-of-property-based-testing/ — Hypothesis author on PBT
- https://docs.pytest.org/ — pytest framework
- https://hypothesis.readthedocs.io/ — Hypothesis property-based testing

## Related

- [[testing-methodology-both-outcomes-informative]]@related
- [[tui-frameworks-for-personal-scripts]]@related
