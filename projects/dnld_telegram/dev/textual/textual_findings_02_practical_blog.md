# Textual Practical Blog Post - Progress Bars Implementation

**Source**: https://github.com/textualize/textual/blob/main/docs/blog/posts/spinners-and-pbs-in-textual.md
**Date**: 2025-01-31

## 🎯 Key Insights for Our Telegram Downloader

### ✅ Perfect Pattern for Indeterminate Progress
This blog shows exactly how to create progress bars when you don't know the total upfront - perfect for our Telegram downloader that discovers files as it goes!

### 🔧 Working Implementation Pattern
```python
from rich.progress import Progress, BarColumn
from textual.app import App, ComposeResult
from textual.widgets import Static

class IndeterminateProgress(Static):
    def __init__(self):
        super().__init__("")
        self._bar = Progress(BarColumn())  # Just the bar, no extras
        self._bar.add_task("", total=None)  # total=None = indeterminate

    def on_mount(self) -> None:
        # Update 60 times per second for smooth animation
        self.update_render = self.set_interval(
            1 / 60, self.update_progress_bar
        )

    def update_progress_bar(self) -> None:
        self.update(self._bar)  # Rich renderable updates automatically
```

### 🚀 Why This Solves Our Rich Live Problem

1. **Non-blocking**: Uses `set_interval()` instead of Rich Live's blocking updates
2. **Asyncio-friendly**: Textual's `set_interval` works with asyncio event loop
3. **Self-updating**: Rich Progress object updates itself, no manual animation needed
4. **Signal-safe**: Textual handles signal management properly

### 📊 Key Technical Details

- **Update frequency**: 60 FPS for smooth animation
- **Rich integration**: Uses Rich Progress as a renderable inside Textual Static widget
- **Mounting pattern**: `on_mount()` starts the update cycle
- **Indeterminate mode**: `total=None` creates the spinning/pulsing effect

### 🔄 Evolution Path for Our Downloader

1. **Start indeterminate**: Begin with unknown total files
2. **Switch to determinate**: Once we know total files, update to show actual progress
3. **Multiple progress bars**: Could show per-file and overall progress

### 💡 Architecture Benefits

- **Separation of concerns**: Progress display separate from download logic
- **Reactive updates**: Just update the progress object, UI handles the rest
- **Rich ecosystem**: Full access to Rich's progress bar features
- **Textual integration**: Proper asyncio and signal handling

## Next Steps
- Find examples of switching from indeterminate to determinate
- Look for multi-progress bar examples
- Search for real download/file processing examples
