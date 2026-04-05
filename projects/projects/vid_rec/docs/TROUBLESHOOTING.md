# Vid_ReC Troubleshooting Guide

This guide provides solutions to common problems you might encounter while using the application.

### Common Errors

---

**Error:** `FileNotFoundError: Missing config file: config.toml`
- **Cause:** The application cannot find the `config.toml` file in its root directory.
- **Solution:** Ensure you are running the application from the project's root directory. If the file is missing, create one based on the `config.example.toml` template.

---

**Error:** `ffmpeg: command not found` or `ffmpeg-normalize: command not found`
- **Cause:** The `ffmpeg` tool, which is a critical dependency, is not installed or not available in your system's PATH.
- **Solution:**
  1.  Install FFmpeg using your system's package manager (e.g., `choco install ffmpeg` on Windows, `brew install ffmpeg` on macOS, `sudo apt-get install ffmpeg` on Debian/Ubuntu).
  2.  Ensure the location of the `ffmpeg.exe` (or `ffmpeg`) executable is included in your system's `PATH` environment variable.

---

**Error:** `TypeError: RichHandler.__init__() got an unexpected keyword argument...`
- **Cause:** This typically indicates an issue with installed dependencies, possibly an outdated version of the `rich` library.
- **Solution:** Ensure your Python environment is set up correctly and all dependencies are installed with the versions specified in `pyproject.toml`. Run `pip install --upgrade -e .` from the project root.

---

**Error:** Application freezes or the progress bar display prints many repeated lines.
- **Cause:** This is often a rendering issue between the `rich` library and your specific terminal application (e.g., the default Windows command prompt, some IDE-integrated terminals).
- **Solution:** Try running the application in a more modern terminal, such as Windows Terminal, PowerShell 7+, or standard terminals on macOS and Linux.

---

### Frequently Asked Questions (FAQ)

---

**Q: A job failed. How do I find out why?**
**A:** Check the log files in the `logs/` directory.
- `vid_rec.txt`: Contains the main log from the application.
- `vid_rec_worker_*.txt`: Contains detailed logs from each worker process, which is often where specific `ffmpeg` errors will be recorded.

---

**Q: Why is the "Subtitle Generation" phase slow and only using one core?**
**A:** Subtitle generation is a GPU-intensive task. To maximize performance and avoid memory conflicts on a single GPU, this phase is intentionally run sequentially (one file at a time).

---

**Q: The application detects the wrong language for my video file.**
**A:** The AI model for language detection is very accurate but not perfect, and it can sometimes make mistakes. You can manually override the language detection for a specific run using the `--language` flag. For example, to force the application to treat the source video(s) as Japanese, you would run:
```bash
# For a whole directory
python -m src.main_processor --language ja

# Or for a single file
python -m src.main_processor --source "/path/to/your/video.mp4" --language ja
```
You can find a list of valid two-letter language codes (like `en`, `ja`, `ko`, `zh`) from the Whisper documentation.

---

**Q: Why is the initial "Evaluating file states..." phase slow?**
**A:** During this phase, the application is calculating a SHA256 hash for every video file to check for changes since the last run. If your video library is large and stored on a network drive or a slow hard drive, this I/O-intensive operation can take some time.

---

**Q: How do I use the new interactive controls introduced in version 2.2?**
**A:** Version 2.2 introduces interactive controls to enhance user experience during processing. These controls are enabled by the `pynput` library, which must be installed. If `pynput` is not found, the application will run without interactive controls, and a warning will be logged. The available controls are:
- **Dashboard View (Press 'd')**: Toggles a detailed dashboard view showing individual worker progress during CPU processing phases.
- **Pause/Resume (Press 'p')**: Pauses or resumes the processing. When paused, the application will wait for your input to resume.
- **Quit (Press 'q')**: Requests a graceful shutdown of the application, stopping all processing tasks.

If you encounter issues with these controls, ensure `pynput` is installed correctly (`pip install pynput`), and check for any keyboard input conflicts with your terminal or environment.
