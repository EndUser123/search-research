---
title: "I'm using Rich with python 3.14 on Windows 11.  I think we have 5 workers.  Why am I getting this visual duplication?

"
date: "2025-12-22"
mode: "COPILOT"
uuid: "2f50a396-3c0a-47da-9b6c-5f4c67ccc94f"
entry_count: 1
---

## Human

I'm using Rich with python 3.14 on Windows 11.  I think we have 5 workers.  Why am I getting this visual duplication?



⬇️  Downloading channel: [https://www.youtube.com/@TwoMinutePapers](https://www.youtube.com/@TwoMinutePapers)
⠴ 📥 Downloading 5 channels                   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   0% 0:00:00
⠴ 📥 [https://www.youtube.com/@TwoMinutePapers](https://www.youtube.com/@TwoMinutePapers) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   0% 0:00:00
⠦ 📥 Downloading 5 channels                   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   0% 0:00:00
⠸ 📥 Downloading 5 channels                   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   0% 0:00:04
⠸ 📥 [https://www.youtube.com/@TwoMinutePapers](https://www.youtube.com/@TwoMinutePapers) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   0% 0:00:04
PS P:\projects\yt-fts>

## Assistant

## Root Cause Analysis: Rich Progress Bar Duplication with Concurrent Workers

The visual duplication you're experiencing is a **thread-safety race condition in Rich's Live display mechanism**—a known issue identified in Rich's GitHub repository. Here's precisely what's happening and how to fix it.[1]

### The Core Problem

Rich's `Progress` class (which uses `Live` internally) maintains separate locks for the console output and the live refresh thread. When multiple worker threads call `progress.update()` simultaneously while the auto-refresh thread renders to the terminal, these independent synchronization mechanisms create a race condition. The sequence unfolds like this:

1. Worker thread 1 calls `progress.update()` to change the task description with a URL
2. Before the complete frame renders, the refresh thread (running at 10 Hz by default) triggers and draws the terminal
3. The terminal displays an incomplete/partial render with both the old and new content visible
4. Worker thread 2 updates, refresh cycles again, creating overlapping visual artifacts

You're seeing the same progress bar line rendered twice because the terminal buffer contains state from both a mid-update and a refresh-thread render occurring microseconds apart.

### Why Windows Amplifies This

Windows console has fundamental architectural differences that make this visible:

- **Buffer Management**: Windows Console Host's ANSI escape sequence handling is slower than Windows Terminal, creating larger timing windows where the race condition manifests
- **Thread Scheduling**: Windows kernel thread scheduling can rapidly interleave worker threads and Rich's refresh thread more aggressively than Unix systems
- **Legacy Console Rendering**: Rich detects Windows and may use legacy rendering paths with less efficient synchronization[2]

This is why the issue is visible on Windows 11 PowerShell but might be less apparent on macOS/Linux terminals.

### Practical Solutions

**Immediate Fix (Minimal Code Changes):**

Replace direct worker-thread progress updates with a queue-based pattern that serializes all updates through the main thread:

```python
import queue
from concurrent.futures import ThreadPoolExecutor
from rich.progress import Progress

class ThreadSafeProgressCoordinator:
    """Coordinate progress from multiple workers via queue."""
    
    def __init__(self, total_tasks):
        self.update_queue = queue.Queue()
        self.total_tasks = total_tasks
        
    def worker_wrapper(self, task_id, work_func):
        """Workers push updates to queue instead of calling progress directly."""
        result = work_func(task_id)
        self.update_queue.put(('complete', task_id))
        return result
    
    def run(self, work_func, num_workers=5):
        """Main thread only updates progress—eliminates race condition."""
        with Progress() as progress:
            overall_task = progress.add_task(
                "[cyan]Downloading channels", 
                total=self.total_tasks
            )
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [
                    executor.submit(self.worker_wrapper, i, work_func)
                    for i in range(self.total_tasks)
                ]
                
                # Process queue updates in main thread only
                completed = 0
                while completed < self.total_tasks:
                    try:
                        msg_type, task_num = self.update_queue.get(timeout=0.1)
                        if msg_type == 'complete':
                            progress.update(overall_task, advance=1)
                            completed += 1
                    except queue.Empty:
                        continue
```

This pattern works because **all console writes happen on the main thread**—the queue serializes access, eliminating the race condition entirely. The `timeout=0.1` prevents blocking while remaining responsive.

**Quick Alternative (Single-Line Fix):**

If refactoring worker code isn't feasible, reduce the refresh rate to create fewer race condition windows:

```python
Progress(refresh_per_second=2)  # Default is 10 Hz
```

This trades responsiveness for stability—fewer refresh cycles mean fewer opportunities for the race condition to create visible artifacts.

**Environment-Level Fix:**

Run your code in **Windows Terminal** (not legacy Console Host):

```powershell
# In Windows Terminal with PowerShell 7+
python your_script.py
```

Windows Terminal renders ANSI escape sequences significantly faster, reducing the timing window where overlapping renders become visible. Rich's legacy Windows rendering path is automatically bypassed when modern terminal support is detected.

### Why This Matters for Your Use Case

With 5 concurrent workers and a default 10 Hz refresh rate, you have 50 potential update events per second competing with 10 refresh renders per second. On Windows, thread scheduling can make these collide frequently, creating the overlapping output you're observing. The queue approach guarantees that only one "update event" reaches the console at any given moment, making the problem impossible.
