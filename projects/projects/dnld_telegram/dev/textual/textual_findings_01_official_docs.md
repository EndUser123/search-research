# Textual Official Documentation - Progress Bar Widget

**Source**: https://github.com/textualize/textual/blob/main/docs/widgets/progress_bar.md
**Date**: 2025-01-31

## Key Features for Our Use Case

### ✅ Perfect for Asyncio Applications
- **Non-blocking**: Progress bars are reactive widgets that don't block the event loop
- **Reactive attributes**: `progress`, `total`, `percentage` update automatically
- **Three states**: Indeterminate, in-progress, completed

### 🎯 Core Components
1. **Bar** (`#bar`) - Visual progress representation
2. **PercentageStatus** (`#percentage`) - Shows completion percentage
3. **ETAStatus** (`#eta`) - Shows estimated time to completion

### 📊 Reactive Attributes
- `progress` (float) - Current progress steps
- `total` (float) - Total steps to complete
- `percentage` (float, read-only) - Auto-calculated percentage

### 🎨 Styling Options
- **Gradient support** - Smooth gradient bars instead of solid
- **Custom CSS** - Full styling control via .tcss files
- **Component-level styling** - Style bar, percentage, ETA independently

## Key Insights for Telegram Downloader

1. **ETA Support**: Built-in ETA calculation - perfect for file downloads
2. **Indeterminate State**: Can start without knowing total files
3. **Reactive Updates**: Just update `progress` value, UI updates automatically
4. **No Blocking**: Designed for long-running async operations

## Example Structure (from docs)
```python
# Simple progress bar creation
progress_bar = ProgressBar(total=100, show_eta=True)

# Update progress (non-blocking)
progress_bar.progress = current_files_downloaded

# Auto-calculates percentage and ETA
```

## Next Steps
- Get actual code examples from the documentation
- Look for async/download-specific examples
- Find real-world implementations
