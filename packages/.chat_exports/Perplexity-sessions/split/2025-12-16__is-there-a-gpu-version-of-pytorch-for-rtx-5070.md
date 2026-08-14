---
title: "Is there a gpu version of pytorch for rtx 5070?"
date: "2025-12-16"
mode: "COPILOT"
uuid: "fc082883-fca2-4a8b-a6d7-95e316d3f27d"
entry_count: 1
---

## Human

Is there a gpu version of pytorch for rtx 5070?

## Assistant

## GPU Support for PyTorch with RTX 5070

Yes, there is GPU support for PyTorch with RTX 5070, but **stable PyTorch builds currently do not support it**. The RTX 5070 is part of NVIDIA's Blackwell architecture (compute capability `sm_120`), which is newer than what stable PyTorch versions officially support.[1][2]

### Current Support Status

**Stable PyTorch versions** (e.g., 2.7.0 and earlier) support CUDA compute capabilities up to `sm_90`, which means RTX 5070 cards are not officially supported in standard builds. You'll see compatibility warnings when attempting to use the GPU.[3][4]

### Working Solutions

To use PyTorch with RTX 5070, you have several options:

**1. Use PyTorch Nightly Builds (Recommended)**

Install PyTorch nightly builds built with CUDA 12.8 or later, which include support for the Blackwell architecture (`sm_120`):[4][1]

```bash
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
```

This requires **CUDA 12.8 or newer** to be installed on your system.[1][4]

**2. Compile from Source**

Build PyTorch from source with explicit support for Blackwell architecture. Set the appropriate environment variables and build with your CUDA toolkit.[5]

### Key Requirements

To successfully use PyTorch with RTX 5070, ensure you have:[5][1]

- **CUDA Toolkit 12.8 or higher** installed
- **Python 3.11 or 3.12** (avoid the latest Python versions as they may have compatibility issues)
- **nightly PyTorch builds** or a custom-compiled PyTorch binary

The nightly build option is generally the most straightforward path for users with RTX 5070 cards.[4][5]
