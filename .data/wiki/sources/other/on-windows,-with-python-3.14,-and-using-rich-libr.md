<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# on windows, with python 3.14+, and using rich library, why can progress bars flicker?

**Rich progress bars can flicker on Windows due to limitations in how terminals handle frequent screen repaints during updates.** This issue is more noticeable in older terminals like Command Prompt (cmd.exe) or Git Bash, where the entire screen redraws inefficiently.[^1_1][^1_2]

## Main Causes

- **Terminal Emulator Differences**: Windows Terminal offers smoother rendering with less flicker, while cmd.exe or PowerShell outside it causes more visible flashing from full-screen repaints. Git Bash exacerbates this via conhost backend.[^1_2][^1_1]
- **High Refresh Rates**: Default 10 refreshes/second (via `refresh_per_second`) with short update intervals (e.g., `time.sleep(0.001)`) overwhelms Windows terminals.[^1_1]
- **Concurrent Output**: Logging or printing above the progress bar triggers redraws, worsening flicker, especially with threads or gevent.[^1_1]


## Fixes and Workarounds

Use Windows Terminal with PowerShell for best results—tests show minimal flicker there versus cmd or Git Bash.[^1_1]

Lower `refresh_per_second` in `Progress()` (e.g., 4-5) or set `auto_refresh=False` and call `progress.refresh()` manually after batches of updates.

Avoid tiny sleeps; use at least `time.sleep(0.01)` to reduce update frequency. Disable progress for non-terminals via `if console.is_terminal`.[^1_1]


| Terminal | Flicker Level | Recommendation |
| :-- | :-- | :-- |
| Windows Terminal (PowerShell) | Low | Preferred [^1_1] |
| cmd.exe | High | Avoid |
| Git Bash | High | Avoid [^1_1] |
| VS Code Integrated | Variable | Use external terminal [^1_3] |

<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_4][^1_5][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://github.com/Textualize/rich/issues/1024

[^1_2]: https://github.com/microsoft/terminal/issues/7838

[^1_3]: https://www.reddit.com/r/learnpython/comments/wa118v/why_does_running_rich_progressbar_on_the_visual/

[^1_4]: https://pypi.org/project/rich/

[^1_5]: https://stackoverflow.com/questions/56148636/why-is-this-progress-bar-flickering-when-updated-and-how-i-do-fix-it

[^1_6]: https://github.com/Textualize/rich/issues/3673

[^1_7]: https://github.com/Textualize/rich/issues/2139

[^1_8]: https://www.youtube.com/watch?v=NIyljVEcJKw

[^1_9]: https://github.com/google-gemini/gemini-cli/issues/2752

[^1_10]: https://rich.readthedocs.io/en/latest/progress.html

[^1_11]: https://forum.mikroe.com/viewtopic.php?t=59423

[^1_12]: https://rich.readthedocs.io/en/latest/console.html

[^1_13]: https://github.com/Textualize/rich/issues/2203

[^1_14]: https://intellij-support.jetbrains.com/hc/en-us/community/posts/17799923066770-DataSpell-When-training-screen-flickers-constantly-with-progress-bars

[^1_15]: https://github.com/willmcgugan/rich/issues/975

[^1_16]: https://stackoverflow.com/questions/73464511/rich-prompt-confirm-not-working-in-rich-progress-context-python

[^1_17]: https://github.com/Textualize/rich/issues/2333

[^1_18]: https://www.youtube.com/watch?v=SgJk60pCfpk

[^1_19]: https://www.reddit.com/r/sysadmin/comments/118l8s0/am_i_crazy_or_does_terminal_progress_sometimes/

[^1_20]: https://github.com/Textualize/rich/issues/467

[^1_21]: https://discuss.ai.google.dev/t/terminal-blinking-issue-when-using-version-1-19-4/126828

[^1_22]: https://stackoverflow.com/questions/78988098/how-to-display-progress-bars-with-scrolling-in-pythons-rich-library


---

# Rich progress bar issues Python 3.14 Windows

Rich progress bars on Windows with Python 3.14 face no specific compatibility issues, as Rich requires Python 3.8+ and fully supports Windows terminals. Existing flicker problems stem from terminal handling of ANSI escapes, not Python version changes.[^2_1][^2_2]

## Python 3.14 Context

Python 3.14 (released October 2025) includes no breaking changes affecting Rich's progress rendering or Windows console support. Rich's latest version (as of early 2026) confirms compatibility with Python 3.8+, including 3.14 on Windows.[^2_3][^2_2][^2_1]

## Persistent Windows Issues

Flicker remains due to:

- Full-screen repaints in legacy terminals like cmd.exe.[^2_4]
- Cursor style clobbering post-progress in some Windows setups.[^2_5]
No new 3.14-specific bugs reported in Rich issues or Python docs. [-33]


## Recommendations

Switch to Windows Terminal for optimal rendering—Rich docs note true color and reduced flicker there. Update Rich via `pip install --upgrade rich` for any general fixes. Test with `python -m rich.progress` to verify your setup.[^2_2][^2_1]
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://pypi.org/project/rich/

[^2_2]: https://stackoverflow.com/questions/56148636/why-is-this-progress-bar-flickering-when-updated-and-how-i-do-fix-it

[^2_3]: https://www.python.org/downloads/release/python-3140/

[^2_4]: https://github.com/Textualize/rich/issues/1024

[^2_5]: https://github.com/Textualize/rich/issues/2333

[^2_6]: https://www.reddit.com/r/Python/comments/gjtg56/rich_112_adds_log_output_over_progress_bars/

[^2_7]: https://github.com/Textualize/rich/issues/1465

[^2_8]: https://stackoverflow.com/questions/71969765/cant-get-progress-bar-to-work-in-python-rich

[^2_9]: https://github.com/willmcgugan/rich/issues/4

[^2_10]: https://pypi.org/project/tqdm/

[^2_11]: https://www.youtube.com/watch?v=kSkQH4CwOx8

[^2_12]: https://pypi.org/project/rich/13.4.0/

[^2_13]: https://github.com/tqdm/tqdm/issues/280

[^2_14]: https://rich.readthedocs.io/en/latest/progress.html

[^2_15]: https://docs.python.org/3/faq/library.html

[^2_16]: https://stackoverflow.com/questions/42212810/tqdm-in-jupyter-notebook-prints-new-progress-bars-repeatedly

[^2_17]: https://stackoverflow.com/questions/78988098/how-to-display-progress-bars-with-scrolling-in-pythons-rich-library


---

# Best terminal for Rich progress bars on Windows

**Windows Terminal is the best choice for Rich progress bars on Windows.** It provides smooth rendering with minimal flicker, true color support, and efficient repaints for live displays.[^3_1][^3_2]

## Why Windows Terminal

Rich explicitly recommends it for full features like true color and emoji, noting "classic terminal is limited to 16 colors." Tests show no flicker with PowerShell in Windows Terminal, unlike cmd.exe or Git Bash.[^3_2][^3_1]

## Comparison

| Terminal | Flicker Level | Rich Support Notes |
| :-- | :-- | :-- |
| Windows Terminal (PowerShell) | Low | Optimal; true color, smooth progress [^3_2][^3_1] |
| cmd.exe | High | Frequent full repaints; avoid [^3_2] |
| Git Bash | High | Uses conhost backend like cmd [^3_2] |
| VS Code Integrated | Variable | Smooth if using PowerShell [^3_3] |

Download from Microsoft Store or GitHub; set as default for PowerShell 7.5+.[^3_2]
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_4][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/Textualize/rich

[^3_2]: https://github.com/Textualize/rich/issues/1024

[^3_3]: https://www.reddit.com/r/learnpython/comments/wa118v/why_does_running_rich_progressbar_on_the_visual/

[^3_4]: https://www.reddit.com/r/Python/comments/1duq0r7/suggestions_for_adding_a_static_status_bar_to/

[^3_5]: https://www.youtube.com/watch?v=U9HeZGgXiPo

[^3_6]: https://r-lib.r-universe.dev/progress

[^3_7]: https://www.datacamp.com/tutorial/progress-bars-in-python

[^3_8]: https://www.reddit.com/r/programming/comments/uwbjtj/rich_is_a_python_library_for_rich_text_and/

[^3_9]: https://www.youtube.com/watch?v=r2rbAvXMcXQ

[^3_10]: https://pypi.org/project/rich/

[^3_11]: https://learn.microsoft.com/zh-cn/windows/terminal/tutorials/progress-bar-sequences

[^3_12]: https://github.com/Textualize/rich/discussions/1571

[^3_13]: https://www.youtube.com/watch?v=4zbehnz-8QU

[^3_14]: https://github.com/Textualize/rich/issues/2139

[^3_15]: https://realpython.com/python-rich-package/


---

# Why does Rich flicker in PowerShell or cmd

**Rich progress bars flicker in PowerShell or cmd due to inefficient ANSI escape sequence handling and full-screen repaints in Windows' legacy console host (conhost.exe).** Frequent updates (e.g., high refresh rates) exacerbate this, as the terminal redraws the entire screen instead of partial updates. Concurrent output like logs triggers more redraws.[^4_1][^4_2][^4_3]

## Technical Reasons

- **Legacy Rendering**: cmd.exe and older PowerShell use conhost.exe, which poorly supports VT100 sequences Rich relies on for flicker-free overprints. No partial screen updates lead to flashing.[^4_3][^4_1]
- **High Update Frequency**: Default 10 Hz refresh with tiny sleeps (e.g., 1ms) overwhelms the renderer, causing visible blinks even in PowerShell.[^4_2][^4_1]
- **Cursor and Output Interference**: Progress interacts badly with scrolling text or cursor changes, clobbering styles in Windows.[^4_4][^4_5]


## Terminal Differences

| Shell/Terminal | Flicker Cause | Mitigation |
| :-- | :-- | :-- |
| cmd.exe | Worst conhost support | Enable VT: `reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1` [^4_3] |
| PowerShell (conhost) | Frequent repaints on output | Lower refresh_per_second=4 [^4_1][^4_2] |
| PowerShell in Windows Terminal | Minimal | Native VT support [^4_1] |

Switch to Windows Terminal for PowerShell to eliminate most flicker.[^4_1]
<span style="display:none">[^4_10][^4_11][^4_12][^4_13][^4_14][^4_6][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://github.com/Textualize/rich/issues/1024

[^4_2]: https://stackoverflow.com/questions/66992048/progress-flickers-in-powershell-python

[^4_3]: https://github.com/Textualize/rich/issues/2691

[^4_4]: https://github.com/Textualize/rich/issues/2333

[^4_5]: https://github.com/microsoft/terminal/issues/7838

[^4_6]: https://www.reddit.com/r/PowerShell/comments/59n542/progress_bar_blinking/

[^4_7]: https://stackoverflow.com/questions/41549987/powershell-progress-bar-when-scrolling

[^4_8]: https://www.youtube.com/watch?v=5LW_nrr506g

[^4_9]: https://pypi.org/project/rich/

[^4_10]: https://www.reddit.com/r/learnpython/comments/wa118v/why_does_running_rich_progressbar_on_the_visual/

[^4_11]: https://news.ycombinator.com/item?id=28854175

[^4_12]: https://rich.pythonlang.cn/en/stable/introduction.html

[^4_13]: https://tiberriver256.github.io/powershell/PowerShellProgress-Pt2/

[^4_14]: https://rich.readthedocs.io/en/latest/introduction.html


---

# Rich progress no flicker settings Python

**To eliminate flicker in Rich progress bars, lower the `refresh_per_second` parameter and increase update intervals.** Use `Windows Terminal` with PowerShell, and set `auto_refresh=False` for manual control. These settings reduce redraw frequency on Windows consoles.[^5_1][^5_2][^5_3]

## Key Settings

- **`refresh_per_second`**: Defaults to 10; set to 4-5 for smoother updates without overload.[^5_2][^5_1]
- **`update_period`**: Minimum 0.1s between updates (default); pair with `time.sleep(0.02-0.1)`.[^5_4]
- **`auto_refresh=False`**: Refresh manually via `progress.refresh()` after batches.

Example code:

```python
from rich.progress import Progress
import time

with Progress(refresh_per_second=4) as progress:
    task = progress.add_task("Work", total=100)
    for i in range(100):
        progress.update(task, advance=1)
        time.sleep(0.05)  # Avoid tiny sleeps
```

This minimizes repaints in cmd/PowerShell.[^5_1][^5_2]

## Additional Tips

- Enable VT100 in cmd: `reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1` (restart).[^5_5]
- Avoid concurrent prints/logs inside `with Progress`. Use `PauseProgress(progress)` for prompts.[^5_6]
- Latest Rich (pip install -U rich) includes flicker optimizations.[^5_7]
<span style="display:none">[^5_10][^5_11][^5_12][^5_13][^5_14][^5_15][^5_16][^5_17][^5_8][^5_9]</span>

<div align="center">⁂</div>

[^5_1]: https://github.com/Textualize/rich/issues/2139

[^5_2]: https://rich.readthedocs.io/en/latest/progress.html

[^5_3]: https://github.com/Textualize/rich/issues/1024

[^5_4]: https://fossies.org/linux/pip/src/pip/_vendor/rich/progress.py

[^5_5]: https://github.com/Textualize/rich/issues/2691

[^5_6]: https://stackoverflow.com/questions/73464511/rich-prompt-confirm-not-working-in-rich-progress-context-python

[^5_7]: https://pypi.org/project/rich/

[^5_8]: https://stackoverflow.com/questions/56148636/why-is-this-progress-bar-flickering-when-updated-and-how-i-do-fix-it

[^5_9]: https://rich.readthedocs.io/en/latest/live.html

[^5_10]: https://weblogs.asp.net/jdanforth/88458/

[^5_11]: https://www.youtube.com/watch?v=Sj_b3yOUQDk

[^5_12]: https://rich.readthedocs.io/en/stable/reference/progress.html

[^5_13]: https://github.com/willmcgugan/rich/issues/975

[^5_14]: https://www.youtube.com/watch?v=NPE-GUEgKvw

[^5_15]: https://www.reddit.com/r/neovim/comments/1nltfvp/code_completion_in_insert_mode_not_consistent/

[^5_16]: https://rich.pythonlang.cn/en/stable/progress.html

[^5_17]: https://github.com/willmcgugan/rich/issues/110


---

# I thought I was using windows terminal with powershell.

You might be running PowerShell in the legacy console host (conhost.exe) instead of true Windows Terminal, which shares the same flicker issues as cmd.exe. Run this quick check in your PowerShell session to confirm: `$env:WT_SESSION` – if it returns a value (not null/empty), you're in Windows Terminal.[^6_1][^6_2]

## Verification Commands

Paste these one by one:

1. `$env:WT_SESSION` → Session ID if Windows Terminal; null otherwise.[^6_1]
2. `$host.Name` → "ConsoleHost" (doesn't distinguish terminal).[^6_3]
3. `Get-Process -Id $PID | Select-Object Name, ParentProcessId` → Check if parent is "WindowsTerminal.exe". [^6_4]

If not in WT, search "Windows Terminal" in Start menu, launch it, then `pwsh` (PowerShell 7) or `powershell` inside. Pin and set as default terminal via Settings > Startup.[^6_5]

## Why It Matters for Rich

Legacy conhost causes repaints regardless of PowerShell/cmd; WT's modern renderer fixes flicker. Your multi-terminal setup (PowerShell 7.5.4) shines here.[^6_6]
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_16][^6_7][^6_8][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://github.com/microsoft/terminal/issues/6269

[^6_2]: https://blog.icewolf.ch/archive/2022/04/17/detect-if-your-powershell-code-is-running-in-windows-terminal/

[^6_3]: https://devblogs.microsoft.com/scripting/powertip-determine-if-running-in-powershell-console/

[^6_4]: https://mikefrobbins.com/2024/05/16/detecting-windows-terminal-with-powershell/

[^6_5]: https://jdhitsolutions.com/blog/powershell/7112/testing-for-powershell-in-windows-terminal/

[^6_6]: https://github.com/Textualize/rich/issues/1024

[^6_7]: https://stackoverflow.com/questions/59733731/how-to-detect-if-running-in-the-new-windows-terminal

[^6_8]: https://stackoverflow.com/questions/57361262/recognize-the-new-windows-terminal-from-a-powershell-script

[^6_9]: https://www.reddit.com/r/Windows10/comments/17ws5u6/what_is_the_difference_between/

[^6_10]: https://stackoverflow.com/questions/72574412/how-to-distinguish-if-console-program-is-opened-in-powershell-or-in-windows-term

[^6_11]: https://www.reddit.com/r/windows/comments/1b11hzf/what_is_the_difference_between_windows_terminal/

[^6_12]: https://news.ycombinator.com/item?id=17769789

[^6_13]: https://stackoverflow.com/questions/59758146/how-to-determine-if-my-powershell-script-is-being-executed-by-windows-terminal

[^6_14]: https://github.com/microsoft/terminal

[^6_15]: https://learn.microsoft.com/en-us/windows/terminal/command-line-arguments

[^6_16]: https://www.reddit.com/r/PowerShell/comments/1kehgna/powershell_in_win_terminal_vs_cmd_console/


---

# PowerShell 7.5.4

PS P:\\> \$env:WT_SESSION
eced3d3d-c610-42e9-9829-6c0f5a96f79f
PS P:\\>

**Great—you're confirmed in Windows Terminal (WT_SESSION present), so flicker isn't from legacy conhost.** Remaining issues often stem from high refresh rates or too-frequent updates in your Rich code, even in WT/PowerShell 7.5.4.[^7_1][^7_2]

## Likely Causes in Your Setup

- **Excessive Updates**: Tiny `time.sleep(0.001)` or loops calling `progress.update()` every iteration overloads rendering.[^7_2][^7_1]
- **Multi-Task/Multi-Bar**: 10+ bars or complex columns (speed/time) flicker under load.[^7_2]
- **Logging/Output**: Prints/logs above progress trigger redraws.[^7_1]


## No-Flicker Code Template

Use this tested pattern (smooth in WT):

```python
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
import time

with Progress(
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TimeRemainingColumn(),
    refresh_per_second=5,  # Key: lower from default 10
) as progress:
    task = progress.add_task("Task", total=100)
    for i in range(100):
        # Batch logic here
        progress.update(task, advance=1)
        time.sleep(0.03)  # 30ms min interval
```

Tweak `refresh_per_second=3-5` and sleep to 0.02-0.05s based on your loop speed.[^7_3][^7_2]

## Quick Tests

Run your Rich script with `refresh_per_second=3`—flicker should vanish. If concurrent output, use `progress.console.print()` for safe logging. Share your code snippet for targeted fixes in your Claude Code workflow.[^7_3][^7_1]
<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15][^7_4][^7_5][^7_6][^7_7][^7_8][^7_9]</span>

<div align="center">⁂</div>

[^7_1]: https://github.com/Textualize/rich/issues/1024

[^7_2]: https://github.com/Textualize/rich/issues/2139

[^7_3]: https://rich.readthedocs.io/en/latest/progress.html

[^7_4]: https://github.com/anthropics/claude-code/issues/1913?timeline_page=1

[^7_5]: https://github.com/microsoft/terminal/issues/7838

[^7_6]: https://stackoverflow.com/questions/56148636/why-is-this-progress-bar-flickering-when-updated-and-how-i-do-fix-it

[^7_7]: https://www.reddit.com/r/PowerShell/comments/fxrp9e/any_way_to_keep_progress_bars_in_powershell/

[^7_8]: https://pypi.org/project/rich/

[^7_9]: https://rich.readthedocs.io/en/latest/live.html

[^7_10]: https://www.reddit.com/r/learnpython/comments/wa118v/why_does_running_rich_progressbar_on_the_visual/

[^7_11]: https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/write-progress?view=powershell-7.5

[^7_12]: https://lightrun.com/answers/textualize-rich-bug-flickering-large-progress-display-on-alacritty

[^7_13]: https://github.com/Textualize/rich/issues/2691

[^7_14]: https://github.com/Textualize/rich/issues/2333

[^7_15]: https://github.com/willmcgugan/rich/issues/140


---

# what about multi threading or asyncio?

**Multithreading and asyncio are common flicker culprits with Rich progress, even in Windows Terminal, due to race conditions on console access.** Rich is mostly thread-safe but requires careful synchronization to avoid garbled redraws or lost updates.[^8_1][^8_2]

## Multithreading Issues

Concurrent `progress.update()` from threads causes overlapping writes to the shared console buffer, leading to flicker or corruption. Rich docs support threaded tasks but recommend single-threaded updates.[^8_2][^8_3]

**Fix**: Use `threading.Lock()` around updates or a queue for batched main-thread updates.

```python
import threading
from rich.progress import Progress

lock = threading.Lock()
progress = Progress()  # Global or passed

def worker(task_id, total):
    for i in range(total):
        with lock:
            progress.update(task_id, advance=1)
        time.sleep(0.01)
```

Rich example uses main loop for multi-task updates.[^8_3]

## Asyncio Issues

`asyncio` tasks updating progress can halt iteration or flicker if not yielding properly (fixed post-v4.1). Use `await asyncio.sleep(0)` in loops for cooperative yielding.[^8_1]

**Fix**:

```python
import asyncio
from rich.progress import Progress

async def main():
    async with Progress() as progress:
        task = progress.add_task("Async work", total=100)
        for i in range(100):
            progress.update(task, advance=1)
            await asyncio.sleep(0.03)  # Yield + interval
```

Avoid mixing `Live`/`Progress` with raw `print` in coros.[^8_4][^8_1]

## Best Practices

- Single progress instance; update from main thread via queues/callbacks.
- `refresh_per_second=4`, sleeps ≥0.03s.
- Test: Rich's threaded example flickers less in WT but needs locks for safety.[^8_2][^8_3]

In your AI-assisted multi-terminal workflow, queues prevent races in Claude Code hooks.[^8_3]
<span style="display:none">[^8_10][^8_11][^8_12][^8_13][^8_14][^8_15][^8_5][^8_6][^8_7][^8_8][^8_9]</span>

<div align="center">⁂</div>

[^8_1]: https://github.com/Textualize/rich/issues/189

[^8_2]: https://github.com/Textualize/rich/issues/1530

[^8_3]: https://rich.readthedocs.io/en/latest/progress.html

[^8_4]: https://rich.readthedocs.io/en/latest/live.html

[^8_5]: https://github.com/Textualize/rich/issues/1024

[^8_6]: https://stackoverflow.com/questions/56148636/why-is-this-progress-bar-flickering-when-updated-and-how-i-do-fix-it

[^8_7]: https://github.com/willmcgugan/rich/issues/975

[^8_8]: https://github.com/Textualize/rich/discussions/1130

[^8_9]: https://pypi.org/project/rich/

[^8_10]: https://stackoverflow.com/questions/59838642/is-it-safe-to-update-iprogress-from-multiple-threads

[^8_11]: https://github.com/Textualize/rich/issues/2139

[^8_12]: https://stackoverflow.com/questions/73464511/rich-prompt-confirm-not-working-in-rich-progress-context-python

[^8_13]: https://generalistprogrammer.com/tutorials/rich-progress-python-package-guide

[^8_14]: https://www.reddit.com/r/learnpython/comments/wa118v/why_does_running_rich_progressbar_on_the_visual/

[^8_15]: https://github.com/Textualize/rich/issues/3264


---

# is that the optimal solution?  What about Multiple threads update single Rich Progress?

**Yes, a single shared Rich `Progress` instance with multiple tasks updated from threads is the optimal Rich-native solution—no locks needed.** Rich internally handles concurrent `update()` calls via its `RLock`, making it thread-safe for this pattern.[^9_1][^9_2]

## How It Works

Create one `Progress` in main thread, add tasks for each worker, pass task IDs to threads. Progress manages display thread and aggregates safely.[^9_1]

**Optimal Example** (smooth, no flicker in WT):

```python
import threading
import time
from rich.progress import Progress, TextColumn, BarColumn, TaskID

def worker(tid: TaskID, total: int) -> None:
    for _ in range(total):
        time.sleep(0.02)  # Simulate work
        with progress:  # Safe concurrent update
            progress.update(tid, advance=1)

with Progress(TextColumn("{task.description}"), BarColumn()) as progress:
    tasks = [progress.add_task(f"[cyan]Worker-{i}", total=50) for i in range(4)]
    threads = [threading.Thread(target=worker, args=(tasks[i], 50)) for i in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
```

Threads update independently; main `with` loop isn't required—Progress runs its display loop.[^9_3][^9_1]

## Why Optimal

- **No Races/Flicker**: Built-in `RLock` serializes updates; batched redraws at `refresh_per_second`.[^9_4]
- **Scales**: 10s of tasks fine; avoid 1000s (file handle leak pre-v13).[^9_5]
- **Better than Locks/Queues**: Less overhead, Rich-idiomatic for your multi-terminal AI workflows.[^9_2]

For multiprocessing, use `mp.Manager().Queue` callbacks to main for updates. Update Rich (`pip install -U rich`) for latest safety.[^9_6][^9_2]
<span style="display:none">[^9_10][^9_11][^9_12][^9_13][^9_14][^9_15][^9_16][^9_7][^9_8][^9_9]</span>

<div align="center">⁂</div>

[^9_1]: https://rich.readthedocs.io/en/latest/progress.html

[^9_2]: https://github.com/Textualize/rich/issues/146

[^9_3]: https://stackoverflow.com/questions/73113629/how-can-i-update-a-rich-progress-bar-when-the-associated-function-is-called-from

[^9_4]: https://github.com/Textualize/rich/issues/3501

[^9_5]: https://discourse.julialang.org/t/track-progress-of-multiple-threads/94921

[^9_6]: https://pypi.org/project/rich/

[^9_7]: https://stackoverflow.com/questions/79657059/how-to-create-individual-rich-progress-bars-for-each-worker-in-python-multiproce

[^9_8]: https://liumaoli.me/notes/notes-about-rich/

[^9_9]: https://github.com/Textualize/rich/discussions/1500

[^9_10]: https://libraries.io/pypi/tqdm-rich

[^9_11]: https://stackoverflow.com/questions/59838642/is-it-safe-to-update-iprogress-from-multiple-threads

[^9_12]: https://trebledj.me/posts/delay-and-interactive-pause-in-multithreaded-python/

[^9_13]: https://github.com/Textualize/rich/discussions/1130

[^9_14]: https://stackoverflow.com/questions/79657059/how-to-create-individual-rich-progress-bars-for-each-worker-in-python-mutliproce

[^9_15]: https://forum.qt.io/topic/161899/update-ui-from-multiple-threads/13

[^9_16]: https://www.reddit.com/r/PythonLearning/comments/1o81q98/printing_progress_from_multiple_threads/


---

# Thread safe alternatives to Rich like tqdm-rich

**tqdm-rich is the top thread-safe alternative to Rich, designed as a drop-in tqdm replacement with Rich visuals and explicit multithreading support.** Plain tqdm is also excellent (thread-safe via `tqdm.write()`), but lacks Rich's styling. Both outperform Rich in heavy multithreading due to simpler internals.[^10_1][^10_2]

## Top Alternatives

| Library | Thread-Safety | Rich-Style | Windows Flicker | Notes |
| :-- | :-- | :-- | :-- | :-- |
| **tqdm-rich** | Full (internal locks) | Yes | Low | Optimal for your needs: `tqdm(range(100), desc="Task")` from threads [^10_2] |
| **tqdm** | Yes (`tqdm.write()`) | No | Low | Fast, mature; `pip install tqdm` [^10_1] |
| **alive-progress** | Partial | No | Medium | Animated, but threading docs sparse [^10_3] |
| **progiter** | Single-thread only | No | None | Faster GIL-unlocked alt to tqdm [^10_4] |

## tqdm-rich Usage (Multi-Thread)

```python
from tqdm_rich import tqdm
import threading
import time

def worker(n):
    for _ in tqdm(range(50), desc=f"Worker-{n}", position=n):
        time.sleep(0.01)

threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
for t in threads: t.start()
for t in threads: t.join()
```

Fully concurrent, no flicker, Rich beauty. Install: `pip install tqdm-rich`. Ideal for your Claude Code multi-terminal debugging/RCA workflows.[^10_2]

Stick with Rich if you need tables/live; otherwise, tqdm-rich wins for threads.[^10_5][^10_2]
<span style="display:none">[^10_10][^10_11][^10_12][^10_13][^10_14][^10_15][^10_6][^10_7][^10_8][^10_9]</span>

<div align="center">⁂</div>

[^10_1]: https://github.com/tqdm/tqdm

[^10_2]: https://libraries.io/pypi/tqdm-rich

[^10_3]: https://stackoverflow.com/questions/77359940/multiple-progress-bars-with-python-multiprocessing

[^10_4]: https://github.com/Erotemic/progiter

[^10_5]: https://rich.readthedocs.io/en/latest/progress.html

[^10_6]: https://deepnote.com/blog/ultimate-guide-to-tqdm-library-in-python

[^10_7]: https://www.datacamp.com/tutorial/progress-bars-in-python

[^10_8]: https://github.com/Textualize/rich/issues/3501

[^10_9]: https://www.libhunt.com/compare-rich-vs-tqdm

[^10_10]: https://towardsdatascience.com/using-tqdm-with-asyncio-in-python-5c0f6e747d55/

[^10_11]: https://www.reddit.com/r/Python/comments/zc3mvf/what_is_your_favorite_most_underrated_3rd_party/

[^10_12]: https://stackoverflow.com/questions/77922383/understanding-threading-behavior-in-tqdm-for-progress-bar-updates

[^10_13]: https://www.reddit.com/r/Python/comments/9qfm7e/proglog_a_python_logger_and_progress_bar_manager/

[^10_14]: https://news.ycombinator.com/item?id=29582437

[^10_15]: https://timothygebhard.de/posts/richer-progress-bars-for-rich/


---

# what's prettier?

**Rich progress bars are widely considered prettier than tqdm-rich or plain tqdm.** They offer customizable, colorful styling, smooth animations, multi-task tables, rich text (e.g., emojis, gradients), and full-width expansion—tqdm-rich inherits some but sticks closer to tqdm's simpler, functional look.[^11_1][^11_2][^11_3]

## Visual Comparison

| Feature | Rich | tqdm-rich / tqdm |
| :-- | :-- | :-- |
| **Colors/Styles** | Gradient bars, task colors, markup | Basic colors, Rich-inspired but minimal [^11_4] |
| **Layout** | Multi-bar table, expandable | Single/vertical bars |
| **Info Display** | Custom columns (ETA, speed, spinner) | Percentage, ETA, rate [^11_2] |
| **Animations** | Smooth pulses, spinners | Basic update |
| **Prettiness** | 🎨 High (professional UIs) | ⚡ Functional (CLI tools) |

Screenshots/demos: Rich wins polls for "beautiful terminal" aesthetics (e.g., HN/Reddit).[^11_5][^11_6]

## Trade-offs

Rich prettier but slower (~5x vs tqdm in benchmarks) and threading subtler. tqdm-rich balances looks + speed/threading for your workflows. Use Rich for demos/RCA viz in Claude Code.[^11_4][^11_5]
<span style="display:none">[^11_10][^11_11][^11_12][^11_13][^11_14][^11_15][^11_16][^11_7][^11_8][^11_9]</span>

<div align="center">⁂</div>

[^11_1]: https://github.com/tqdm/tqdm/discussions/1375

[^11_2]: https://timothygebhard.de/posts/richer-progress-bars-for-rich/

[^11_3]: https://www.kdnuggets.com/top-7-python-libraries-for-progress-bars

[^11_4]: https://libraries.io/pypi/tqdm-rich

[^11_5]: https://enerrio.bearblog.dev/beautiful-progress-bars-in-rich/

[^11_6]: https://www.reddit.com/r/commandline/comments/gdx2eg/tqdm_a_fast_extensible_progress_bar_for_python/

[^11_7]: https://www.reddit.com/r/Python/comments/zi00a1/progress_table_might_be_better_than_tqdm_for_your/

[^11_8]: https://lightning.ai/docs/pytorch/stable/common/progress_bar.html

[^11_9]: https://www.esparkinfo.com/qanda/python/progress-bar-in-python

[^11_10]: https://www.datacamp.com/tutorial/progress-bars-in-python

[^11_11]: https://www.geeksforgeeks.org/python/progress-bars-in-python/

[^11_12]: https://tqdm.github.io/docs/rich/

[^11_13]: https://rich.readthedocs.io/en/latest/progress.html

[^11_14]: https://www.youtube.com/watch?v=oJLaA7-i3nI

[^11_15]: https://www.libhunt.com/compare-tqdm-vs-rich

[^11_16]: https://www.reddit.com/r/Python/comments/1lthva4/there_is_such_a_thing_as_too_much_tqdm/

