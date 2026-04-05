# Unified /analyze Command

**Goal**: Consolidate 13 analysis commands into one intelligent analysis engine.

## Current Status

| Component | Status |
|-----------|--------|
| Session-based scoping | ✅ Complete (WT_SESSION isolation) |
| PMGOA backend | ✅ Working |
| CLI argument parsing | ✅ Working |
| Quality backend | ✅ Fixed (created qual_gate.py bridge) |
| Intel backend | ⚠️ References ProductionDebateCouncil (needs testing) |
| Other focus lenses | ⚠️ Need verification |

## Remaining Work

1. ~~**Fix Quality backend**~~ ✅ Done (created qual_gate.py bridge)
2. **Test all focus lenses** - risk, quality, security, performance, architecture, cognitive
3. **Test all modes** - quick, standard, deep, council
4. **Test all output formats** - checklist, report, json, interactive
5. **End-to-end testing** - Verify full command works

## Commands Being Consolidated

- /pmgoa → /analyze --mode standard --focus risk
- /pmgoa-cs → /analyze --mode deep --focus cognitive
- /preview → /analyze
- /intel → /analyze --mode council --focus opportunities
- /asef → /analyze --mode deep --focus quality
- /quality → /analyze --focus quality
- /cq → /analyze --output json
- /code-review-v2 → /analyze --focus quality
- /zen-challenge → /analyze --focus cognitive --mode quick
- /dni → /analyze --focus architecture
- /analyze-code → /analyze --focus quality
- /ast-analyze → /analyze --focus architecture --output json
