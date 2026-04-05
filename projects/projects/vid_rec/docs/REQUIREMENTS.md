# Requirements Management for Vid_ReC

This document explains how dependencies are managed in the Vid_ReC project, following the recommendations from `dev/CRR.md`.

## Overview

The project uses a **two-file approach** for dependency management:

- `requirements.in` - Source of truth for high-level dependencies
- `requirements.txt` - Fully pinned, compiled dependencies for production

This approach addresses the critical findings from CRR.md:
- ✅ **Reproducible builds** - All versions are pinned
- ✅ **Supply-chain security** - Enables vulnerability scanning
- ✅ **Dependency management** - Clear process for updates

## File Structure

```
requirements.in      # High-level dependencies (what we need)
requirements.txt     # Pinned dependencies (exact versions)
update_requirements.py  # Helper script for maintenance
```

## Workflow

### 1. Adding New Dependencies

1. Add the dependency to `requirements.in`:
   ```
   # Add to appropriate section
   new-package>=1.0.0
   ```

2. Regenerate `requirements.txt`:
   ```bash
   python update_requirements.py
   ```

3. Test and commit both files

### 2. Updating Dependencies

1. Modify version constraints in `requirements.in`
2. Run the update script:
   ```bash
   python update_requirements.py --check-security
   ```
3. Test thoroughly before committing

### 3. Security Audits

Run security checks regularly:
```bash
python update_requirements.py --check-security
```

## Dependency Categories

### Core Video Processing
- `ffmpeg-python` - Python FFmpeg wrapper
- `ffmpeg-normalize` - Audio normalization
- `ffmpeg-quality-metrics` - Video quality analysis

### AI/ML for Subtitle Generation
- `openai-whisper` - Speech recognition (pinned to stable version)
- `stable-ts` - Stable transcription timestamps
- `torch` & `torchaudio` - PyTorch ML framework

### Configuration Management
- `tomlkit` - TOML file parsing
- `pydantic` - Data validation and settings

### User Interface
- `rich` - Enhanced console output
- `tqdm` - Progress bars
- `colorama` - Cross-platform colored output

## Best Practices

1. **Always pin critical dependencies** (like openai-whisper)
2. **Use version ranges for stable libraries** (like rich>=13.0.0)
3. **Test after every dependency update**
4. **Run security audits before releases**
5. **Keep requirements.in minimal and well-commented**

## Troubleshooting

### Common Issues

**"pip-tools not found"**
```bash
pip install pip-tools
```

**"Dependency conflict"**
- Check for incompatible version constraints in `requirements.in`
- Use `pip-compile --upgrade` to get latest compatible versions

**"Security vulnerabilities found"**
- Review the pip-audit output
- Update affected packages in `requirements.in`
- Regenerate `requirements.txt`

## Integration with pyproject.toml

The project also maintains dependencies in `pyproject.toml` for modern Python packaging. The `requirements.txt` file is the authoritative source for production deployments, while `pyproject.toml` is used for development installation (`pip install -e .`).

## References

- [CRR.md](dev/CRR.md) - Codebase review recommendations
- [pip-tools documentation](https://pip-tools.readthedocs.io/)
- [pip-audit documentation](https://pypi.org/project/pip-audit/)
