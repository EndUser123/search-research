---
name: ai-pi-or-nemotron-free
description: Adversarial review via pi using Nemotron 3 Super 120B A12B (free tier) via openrouter
version: 1.0.0
triggers:
  - /ai-pi-or-nemotron-free
  - /pi-nemotron-free
---

# /ai-pi-or-nemotron-free

Adversarial review via pi using **Nemotron 3 Super 120B A12B** (free tier) via openrouter.

```bash
pi --mode json --provider openrouter --model nvidia/nemotron-3-super-120b-a12b:free "Review P:/path/to/file.py and return JSON"
```
