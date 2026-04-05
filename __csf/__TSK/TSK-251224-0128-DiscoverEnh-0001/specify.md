# Specification: Discover Enhancements

**TSK-ID**: TSK-251224-0128-DiscoverEnh-0001
**Created**: 2025-12-24
**Status**: Implementation Complete

## Overview

Enhance the `/discover` command by integrating the CodeIntelligenceExplorer with the explorer_spec.py HardwareAcceleratedExplorer, fixing ast-grep pattern matching issues, and ensuring discover is included in the CWO12 workflow.

## Problem Statement

The `/discover` command has three main issues:

1. **Disconnected Integration**: CodeIntelligenceExplorer exists but is not integrated with explorer_spec.py
2. **Broken Pattern Matching**: ast-grep patterns use YAML rule syntax ($VAR, $$ARGS) instead of CLI-compatible patterns
3. **Missing CWO12 Inclusion**: Discover enhancements are not tracked in the CWO12 workflow

## Proposed Solution

1. Integrate CodeIntelligenceExplorer into HardwareAcceleratedExplorer class
2. Convert all ast-grep patterns from YAML rule syntax to CLI-compatible patterns
3. Document discover enhancements within CWO12 workflow

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| CodeIntelligenceExplorer Integration | ✅ Complete | Added to explorer_spec.py with graceful fallback |
| ast-grep Pattern Fixes | ✅ Complete | Converted ~60 patterns across Python, TS/JS, Go, Rust |
| CWO12 Documentation | ✅ In Progress | This specification |

## Success Criteria

- [x] CodeIntelligenceExplorer initialized in explorer_spec.py
- [x] ast-grep patterns return matches (tested with "except:", "raise", "exec(")
- [x] Patterns use CLI-compatible syntax (not YAML rule syntax)
- [x] No "ERROR node" warnings from ast-grep CLI
- [ ] CWO12 workflow updated to include discover

## Files Modified

- `P:/__csf.nip/src/modules/discover/explorer_spec.py` - Added CodeIntelligenceExplorer integration
- `P:/__csf.nip/src/code_intelligence/ast_grep/client.py` - Fixed pattern syntax

## Related Artifacts

- Code Intelligence Integration: `P:/__csf.nip/src/code_intelligence/integration/discover_integration.py`
- Pattern Library: `P:/__csf.nip/src/code_intelligence/ast_grep/client.py` (lines 99-440)
