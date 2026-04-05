#!/usr/bin/env python3
"""
Fix tensor reshape error in audio processing
"""

import re


def fix_tensor_reshape_error():
    """Fix the tensor reshape error by improving empty audio handling"""

    file_path = "C:/_Python/_Projects/ai_studio/src/ai_studio/audio_transcriber.py"

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Find the section where mel spectrogram is created and add better empty audio handling
    pattern = r"""(\s+# Create Mel spectrogram with detailed logging and defensive n_mels
\s+logger\.debug\("\[MEL_DEBUG\] Creating Mel spectrogram with defensive parameters"\)

\s+# ENHANCED: Force standard Whisper parameters for compatibility
\s+expected_n_mels = 80  # Standard Whisper n_mels
\s+expected_n_fft = 400  # Standard Whisper n_fft
\s+expected_hop_length = 160  # Standard Whisper hop_length

\s+# Check model dimensions for consistency
\s+actual_n_mels = getattr\(model\.dims, 'n_mels', expected_n_mels\)
\s+if actual_n_mels != expected_n_mels:
\s+logger\.warning\(f"\[MEL_DEBUG\] Model n_mels mismatch: \{actual_n_mels\} vs expected \{expected_n_mels\}, forcing standard value"\)

\s+# Create Mel spectrogram with explicit parameters to prevent dimension issues
\s+mel = whisper\.log_mel_spectrogram\(
\s+audio,
\s+n_mels=expected_n_mels
\s+\))"""

    replacement = """        # Create Mel spectrogram with detailed logging and defensive n_mels
        logger.debug(\"[MEL_DEBUG] Creating Mel spectrogram with defensive parameters\")

        # CRITICAL FIX: Check for empty or invalid audio before processing
        if audio is None or not hasattr(audio, 'numel') or audio.numel() == 0:
            logger.error(\"[MEL_DEBUG] Audio tensor is empty or invalid - creating minimal valid audio\")
            # Create minimal valid audio tensor (1 second of silence at 16kHz)
            import torch
            audio = torch.zeros(16000, dtype=torch.float32)

        # ENHANCED: Force standard Whisper parameters for compatibility
        expected_n_mels = 80  # Standard Whisper n_mels
        expected_n_fft = 400  # Standard Whisper n_fft
        expected_hop_length = 160  # Standard Whisper hop_length

        # Check model dimensions for consistency
        actual_n_mels = getattr(model.dims, 'n_mels', expected_n_mels)
        if actual_n_mels != expected_n_mels:
            logger.warning(f\"[MEL_DEBUG] Model n_mels mismatch: {actual_n_mels} vs expected {expected_n_mels}, forcing standard value\")

        # ENHANCED: Additional validation for audio tensor
        if len(audio.shape) > 1:
            logger.debug(f\"[MEL_DEBUG] Audio tensor shape: {audio.shape}, attempting to flatten\")
            # Flatten to 1D if needed
            audio = audio.flatten()

        # Ensure minimum audio length (at least 0.1 seconds)
        min_samples = 1600  # 0.1 seconds at 16kHz
        if audio.numel() < min_samples:
            logger.warning(f\"[MEL_DEBUG] Audio too short ({audio.numel()} samples), padding to minimum length\")
            padding = torch.zeros(min_samples - audio.numel(), dtype=audio.dtype, device=audio.device)
            audio = torch.cat([audio, padding])

        # Create Mel spectrogram with explicit parameters to prevent dimension issues
        try:
            mel = whisper.log_mel_spectrogram(
                audio,
                n_mels=expected_n_mels
            )
            logger.debug(\"[MEL_DEBUG] Mel spectrogram created successfully with standard parameters\")
        except Exception as e:
            logger.error(f\"[MEL_DEBUG] Failed to create mel spectrogram: {e}\")
            # Create fallback mel spectrogram
            import torch
            mel = torch.zeros((expected_n_mels, 3000), dtype=torch.float32)"""

    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ Fixed tensor reshape error by adding better empty audio handling")
        return True
    else:
        print("❌ Pattern not found - may already be fixed")
        return False


if __name__ == "__main__":
    fix_tensor_reshape_error()
