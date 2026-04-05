#!/bin/bash
set -e
REPO_DIR="/c/Users/brsth/AppData/Local/Temp/gitingest_mbzuai-oryx_Video-LLaVA"  # pragma: allowlist secret
NOTEBOOKLM_DIR="$REPO_DIR/notebooklm"
OUT="$NOTEBOOKLM_DIR/repo-index-part-1.md"

cat > "$OUT" << 'HEADER'
# Video-LLaVA — Repository Index

Video-LLaVA is an instruction-tuned audio-visual language model for video understanding, extending LLaVA architecture to process video frames and audio jointly.

## Architecture

- **video_chatgpt/chat.py** — Core ChatGPT-style conversation interface for video understanding
- **video_chatgpt/train/train.py** — Training pipeline with LLaMA flash attention monkey-patching
- **video_chatgpt/inference.py** — Inference engine for video-based question answering
- **video_chatgpt/model/video_chatgpt.py** — Main VideoChATGPT model class with multimodal projector

## Evaluation

- **grounding_evaluation/** — Spatial-temporal video grounding benchmarks (HC-STVG, VidSTG datasets)
- **quantitative_evaluation/** — ActivityNet QA, MSVD QA, MSRVTT QA, TGIF-QA benchmark runners
- **eval/run_inference_*.py** — Per-benchmark inference scripts for general, consistency, and QA metrics

## Documentation

- **README.md** — Project overview and quick-start guide
- **docs/1-CLI_DEMO.md** — Command-line interface usage demonstration
- **docs/2-Training.md** — Training configuration and procedure documentation

## Key Utilities

- **grounding_evaluation/util/** — Box operations, distributed training helpers, image transforms
- **video_chatgpt/audio_transcript/** — Audio transcription for video understanding
- **video_chatgpt/model/multimodal_projector/** — LLaVA-style multimodal projector builder
HEADER

echo "" >> "$OUT"
echo "Full file inventory (61 source files total):" >> "$OUT"
echo "" >> "$OUT"

cd "$REPO_DIR"
git ls-files | grep -vE '(\.png$|\.jpg$|\.lock$|\.bin$|\.pyc$|__pycache__|\.pytest_cache|node_modules)' | sort >> "$OUT"

echo "" >> "$OUT"
echo "---" >> "$OUT"
echo "Slice generated from Video-LLaVA (mbzuai-oryx/Video-LLaVA) | 61 files" >> "$OUT"

echo "Done: $OUT ($(wc -l < $OUT) lines)"
