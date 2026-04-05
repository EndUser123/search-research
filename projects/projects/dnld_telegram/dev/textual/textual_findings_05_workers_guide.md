# Textual Workers Guide - Perfect for Async Downloads

**Source**: https://github.com/textualize/textual/blob/main/docs/guide/workers.md
**Date**: 2025-01-31

## 🎯 PERFECT SOLUTION FOR OUR TELEGRAM DOWNLOADER!

This documentation shows **exactly** how to solve our Rich Live + asyncio problem using Textual workers.

## 🚀 Key Insights for Our Use Case

### ✅ Solves Our Exact Problem
The weather app example demonstrates the **exact same issue** we have:
- Network requests (downloads) blocking the UI
- Need for responsive interface during long operations
- Concurrent operations without blocking the event loop

### 🔧 Implementation Pattern for Downloads

```python
from textual.work import work
from textual.app import App

class TelegramDownloaderApp(App):

    @work(exclusive=True)
    async def download_files(self, files_list):
        """Background worker for downloading files"""
        for i, file_info in enumerate(files_list):
            # Update progress display
            self.update_progress(i, len(files_list), file_info.name)

            # Download file (non-blocking for UI)
            await download_file(file_info)

        # Send completion message
        self.post_message(DownloadComplete())
```

### 🎯 Critical Features for Our Downloader

1. **`@work(exclusive=True)`**: Cancels previous downloads if user starts new ones
2. **Non-blocking UI**: Downloads happen in background, UI stays responsive
3. **Progress updates**: Can update progress display from worker
4. **Automatic cleanup**: Workers cancelled if app/widget is removed
5. **Error handling**: Built-in exception handling with `exit_on_error=False`

### 📊 Worker States Perfect for Download Tracking

```python
# Monitor download progress
def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
    if event.state == WorkerState.RUNNING:
        self.status = "Downloading..."
    elif event.state == WorkerState.SUCCESS:
        self.status = "Download complete!"
    elif event.state == WorkerState.ERROR:
        self.status = f"Download failed: {event.worker.error}"
    elif event.state == WorkerState.CANCELLED:
        self.status = "Download cancelled"
```

### 🔄 Thread vs Async Workers

**For our Telegram downloader**: Use **async workers** since:
- We're already using asyncio for downloads
- Can directly call async download functions
- Better integration with existing async code
- No need for `call_from_thread` complexity

### 🎨 UI Update Pattern

```python
@work(exclusive=True)
async def download_files(self, files_list):
    for i, file_info in enumerate(files_list):
        # Safe to update UI from async worker
        self.progress_bar.progress = i
        self.status_text.update(f"Downloading: {file_info.name}")

        await download_file(file_info)
```

## 🏗️ Architecture Benefits

1. **Solves Rich Live blocking**: Workers run in background
2. **Proper signal handling**: Textual manages this automatically
3. **Cancellation support**: Can cancel downloads cleanly
4. **Progress tracking**: Built-in state management
5. **Error resilience**: Graceful error handling

## 💡 Implementation Strategy

### Phase 1: Basic Worker Integration
```python
# Replace current Rich Live with Textual app + worker
class TelegramDownloader(App):
    def compose(self) -> ComposeResult:
        yield ProgressBar(id="download_progress")
        yield Static("Ready to download", id="status")

    @work(exclusive=True)
    async def start_download(self, channel_url):
        # All download logic moves here
        # UI updates are non-blocking
```

### Phase 2: Enhanced Progress Display
- Multiple progress bars (per-file + overall)
- Real-time download speed
- ETA calculations
- File-specific status

### Phase 3: Advanced Features
- Pause/resume downloads
- Download queue management
- Error recovery
- Download history

## 🎯 Why This Is THE Solution

1. **Addresses root cause**: Separates download logic from UI updates
2. **Async-native**: Built for asyncio applications
3. **Professional**: Much better than console.clear() workaround
4. **Scalable**: Can add more features easily
5. **Maintainable**: Clean separation of concerns

## 📝 Next Steps

1. **Get specific examples** of progress bar integration with workers
2. **Find download-specific implementations**
3. **Look for multi-progress patterns**
4. **Study error handling patterns**
