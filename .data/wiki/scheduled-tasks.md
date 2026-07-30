# Scheduled Tasks

Tasks that re-verify wiki content freshness. Checked by /todo, /maintain, /close.

| Task | Due Date | Frequency | Action | Last Done | Status |
|------|----------|-----------|--------|-----------|--------|
| Re-verify GLM-5.2 Tau2 score | 2026-10-29 | quarterly | Fetch benchlm.ai/models/glm-5-2, update model-role-assignment concept | 2026-07-29 | done |
| Re-run deep-reasoning benchmark | 2026-08-29 | monthly | Run benchmark.py --tier deep-reasoning, verify pool members still pass | 2026-07-29 | done |
| Re-run code-exec benchmark | 2026-08-29 | monthly | Run benchmark.py --tier code-exec, verify coding pool | 2026-07-29 | done |
| Check OpenCode Zen free promotion | 2026-08-15 | one-time | Check if zen-deepseek-v4-flash-free still $0, update reasoning-model-pool | 2026-07-29 | done |
| Verify go-kimi-k2-7-code recovered | 2026-08-05 | one-time | Test via direct API, update coding pool if working | | pending |
| Re-check dead NIM models | 2026-09-29 | quarterly | Probe 18 dead NIM models, re-add any that came back | 2026-07-29 | done |
