#!/usr/bin/env python3
"""
Fix input validation gaps for video URLs and file paths
"""

import re


def fix_input_validation_gaps():
    """Fix input validation gaps with comprehensive security measures"""

    file_path = "C:/_Python/_Projects/ai_studio/src/ai_studio/video_processor.py"

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Add comprehensive input validation function if it doesn't exist
    if "_validate_video_source" not in content:
        # Find a good insertion point after the imports and before the class
        insert_point = "class VideoProcessor:"

        validation_function = '''def _validate_video_source(source: str) -> dict:
    """Comprehensive validation of video sources with security checks.

    Args:
        source: Video source (URL or file path)

    Returns:
        dict: {'valid': bool, 'type': str, 'sanitized': str, 'error': str}
    """
    if not source or not isinstance(source, str):
        return {'valid': False, 'type': 'invalid', 'sanitized': '', 'error': 'Empty or invalid source'}

    source = source.strip()
    if not source:
        return {'valid': False, 'type': 'invalid', 'sanitized': '', 'error': 'Empty source after stripping'}

    # Check for YouTube URLs
    youtube_patterns = [
        r'^https?://(?:www\\.)?youtube\\.com/watch\\?v=[\\w-]{11}',
        r'^https?://(?:www\\.)?youtube\\.com/embed/[\\w-]{11}',
        r'^https?://(?:www\\.)?youtu\\.be/[\\w-]{11}',
        r'^https?://(?:www\\.)?youtube\\.com/shorts/[\\w-]{11}'
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, source, re.IGNORECASE):
            # Additional YouTube URL validation
            try:
                parsed = urlparse(source)
                if parsed.netloc.lower() not in ['youtube.com', 'www.youtube.com', 'youtu.be']:
                    return {'valid': False, 'type': 'url', 'sanitized': source, 'error': 'Invalid YouTube domain'}

                # Extract video ID for additional validation
                if 'v=' in source:
                    video_id = parse_qs(parsed.query).get('v', [''])[0]
                    if not re.match(r'^[\\w-]{11}$', video_id):
                        return {'valid': False, 'type': 'url', 'sanitized': source, 'error': 'Invalid YouTube video ID'}

                return {'valid': True, 'type': 'youtube', 'sanitized': source, 'error': ''}
            except Exception as e:
                return {'valid': False, 'type': 'url', 'sanitized': source, 'error': f'URL parsing error: {e}'}

    # Check for other video URLs (general validation)
    if source.startswith(('http://', 'https://')):
        try:
            parsed = urlparse(source)
            if not parsed.netloc:
                return {'valid': False, 'type': 'url', 'sanitized': source, 'error': 'Invalid URL format'}

            # Basic security checks for non-YouTube URLs
            if any(char in source for char in ['|', '&', ';', '`', '$', '(', ')', '{', '}', '<', '>']):
                return {'valid': False, 'type': 'url', 'sanitized': source, 'error': 'Potentially malicious characters in URL'}

            return {'valid': True, 'type': 'url', 'sanitized': source, 'error': ''}
        except Exception as e:
            return {'valid': False, 'type': 'url', 'sanitized': source, 'error': f'URL validation error: {e}'}

    # File path validation
    try:
        # Prevent path traversal attacks
        if '..' in source or source.startswith(('/', '\\\\')):
            return {'valid': False, 'type': 'path', 'sanitized': source, 'error': 'Potential path traversal attack'}

        # Check for suspicious characters in file paths
        suspicious_chars = ['|', '&', ';', '`', '$', '>', '<', '?', '*']
        if any(char in source for char in suspicious_chars):
            return {'valid': False, 'type': 'path', 'sanitized': source, 'error': 'Suspicious characters in file path'}

        # Validate file extension
        path_obj = Path(source)
        if path_obj.suffix.lower() not in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.webm', '.wmv']:
            return {'valid': False, 'type': 'path', 'sanitized': source, 'error': 'Unsupported video file format'}

        # Check if file exists (for local files)
        if path_obj.exists():
            if not path_obj.is_file():
                return {'valid': False, 'type': 'path', 'sanitized': source, 'error': 'Path is not a file'}

            # Basic file size check (prevent processing extremely large files)
            try:
                file_size = path_obj.stat().st_size
                if file_size > 10 * 1024 * 1024 * 1024:  # 10GB limit
                    return {'valid': False, 'type': 'path', 'sanitized': source, 'error': 'File too large (max 10GB)'}
                if file_size == 0:
                    return {'valid': False, 'type': 'path', 'sanitized': source, 'error': 'File is empty'}
            except OSError:
                return {'valid': False, 'type': 'path', 'sanitized': source, 'error': 'Cannot access file'}

        return {'valid': True, 'type': 'file', 'sanitized': str(path_obj), 'error': ''}

    except Exception as e:
        return {'valid': False, 'type': 'path', 'sanitized': source, 'error': f'Path validation error: {e}'}


'''

        new_content = content.replace(insert_point, validation_function + insert_point)

        if new_content != content:
            content = new_content
            print("✅ Added comprehensive input validation function")
        else:
            print("⚠️ Could not insert validation function")
    else:
        print("ℹ️ Input validation function already exists")

    # Enhance the process_video method to use validation
    process_video_pattern = r"def process_video\\(\\s*self,\\s*source: str,"
    process_video_replacement = '''def process_video(
        self,
        source: str,
        worker_statuses: dict,
        worker_statuses_lock: threading.Lock,
        download_only: bool,
        prompt_hash: str,
        shutdown_handler=None,
    ) -> dict:
        """The main pipeline for a single video, including triage.

        Enhanced with comprehensive input validation.
        """

        # CRITICAL FIX: Validate input source before processing
        validation_result = _validate_video_source(source)
        if not validation_result['valid']:
            logger.error(f"Input validation failed for {source}: {validation_result['error']}")
            return {"source": source, "status": "failure", "error": f"Invalid input: {validation_result['error']}"}

        logger.info(f"Input validation passed for {validation_result['type']}: {source}")

'''

    new_content = re.sub(
        process_video_pattern, process_video_replacement, content, flags=re.MULTILINE
    )

    if new_content != content:
        content = new_content
        print("✅ Enhanced process_video method with input validation")
    else:
        print("ℹ️ process_video method pattern not found or already enhanced")

    # Also add validation to the YouTube processing section
    youtube_validation_pattern = r"# Check if source is a YouTube URL\\s*if 'youtube\\.com' in source\\.lower\\(\\) or 'youtu\\.be' in source\\.lower\\(\\):"
    youtube_validation_replacement = """# Check if source is a YouTube URL (already validated above)
        if validation_result['type'] == 'youtube':"""

    new_content = re.sub(
        youtube_validation_pattern,
        youtube_validation_replacement,
        content,
        flags=re.MULTILINE,
    )

    if new_content != content:
        content = new_content
        print("✅ Enhanced YouTube URL detection with validation results")
    else:
        print("ℹ️ YouTube validation pattern not found or already enhanced")

    # Add validation for file paths in the downloader section
    file_validation_pattern = r"# Check video file exists before attempting extraction\\s*video_path = Path\\(video_info\\[\"local_path\"\\]\\)\\s*if not video_path\\.exists\\(\\):"
    file_validation_replacement = """# CRITICAL FIX: Enhanced file validation before processing
        video_path = Path(video_info["local_path"])

        # Re-validate the file path before processing
        file_validation = _validate_video_source(str(video_path))
        if not file_validation['valid']:
            logger.error(f"File validation failed for {video_path}: {file_validation['error']}")
            raise FileNotFoundError(f"Invalid file: {file_validation['error']}")

        if not video_path.exists():
            raise FileNotFoundError(f"Source video file not found: {video_path}")"""

    new_content = re.sub(
        file_validation_pattern,
        file_validation_replacement,
        content,
        flags=re.MULTILINE | re.DOTALL,
    )

    if new_content != content:
        content = new_content
        print("✅ Enhanced file validation in downloader section")
    else:
        print("ℹ️ File validation pattern not found or already enhanced")

    # Write the improved content back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Input validation gaps fixed successfully")
    return True


if __name__ == "__main__":
    fix_input_validation_gaps()
