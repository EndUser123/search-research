bf skill improvements — route management wiring
Target: P:/packages/.claude-marketplace/plugins/cc-skills-utils/skills/bf/
Files: SKILL.md, bf_agent.py

Changes made:
1. P1: Removed VALID_MODELS hardcoded set from bf_agent.py — Bifrost now validates at runtime
2. P2: Added list_catalog_models(), probe_model(), probe_routes() to bf_agent.py
3. P3: Added add_route(), delete_route(), list_routes() to bf_agent.py
4. SKILL.md workflow_steps: wired routes/list-routes/add/delete to Python (bf_agent) calls
5. SKILL.md documentation: all new functions documented, examples added
6. Tests: 9/9 pass
