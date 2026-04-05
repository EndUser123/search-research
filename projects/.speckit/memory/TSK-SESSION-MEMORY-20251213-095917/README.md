# TSK: Session Memory Persistence System

**TSK ID**: TSK-SESSION-MEMORY-20251213-095917
**Created**: 2025-12-13
**Status**: Planning → Development
**Priority**: High

## Project Overview

Complete implementation of session memory persistence system for Claude Code to prevent context loss during compaction events. This project addresses the core problem where Claude Code "forgets what it's doing" after automatic or manual compaction.

## Architecture

The solution integrates three existing systems with a new Session Memory Bridge:

- **TaskMaster Database**: Session linkage and task continuity
- **Chat History RAG**: Conversation pattern preservation
- **Evidence Correlation**: Cross-session evidence trails
- **Session Memory Bridge**: Central coordination hub

## Implementation Plan

Location: `C:\Users\brsth\.claude\plans\rustling-rolling-taco.md`

## Key Tasks

1. **Implement Session Memory Bridge Core** (16h)
   - Build central SessionMemoryBridge class
   - Context preservation and restoration capabilities
   - API interface design

2. **Create Pre/Post Compaction Hooks** (6h)
   - Memory preservation before compaction
   - Context restoration after compaction
   - Integration with hook system

3. **Extend TaskMaster Database Schema** (4h)
   - Add session columns to task table
   - Migration script implementation
   - Session linkage functionality

## Success Criteria

- Task continuity: 95% of active tasks restored after compaction
- Context preservation: Semantic similarity >0.8 between pre/post-compaction
- Restoration time: <500ms for session recovery
- Zero critical data loss: No elements with criticality >0.4 lost

## Notes

- Self-contained implementation plan ready
- Builds on existing infrastructure
- Production-ready with comprehensive testing strategy