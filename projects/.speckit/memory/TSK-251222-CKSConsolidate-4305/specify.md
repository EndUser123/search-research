# CKS System Consolidation - Specification

## Problem Statement
Current CKS (Constitutional Knowledge System) has uncontrolled database sprawl:
- 53 database files with "cks" or "knowledge" in the name
- 3+ incompatible schemas across active databases
- 9 MB of scattered data
- Path confusion causing data loss during ingestion attempts
- High maintenance overhead for solo developer

## Success Criteria
1. Single unified CKS database: P:/__csf.nip/data/cks.db
2. Unified schema supporting all entry types (memories, patterns, code, knowledge)
3. All existing data migrated without loss
4. Backward compatibility layer with deprecation warnings
5. Clear, simple interface: from src.cks import CKS
6. Total database size < 2 MB (from 9 MB)
7. Zero data loss during migration

## Out of Scope
- Vector embedding search (defer to future optimization)
- Multi-tenancy (not needed for solo dev)
- Distributed CKS (violates constitutional principles)

## Failure Conditions
- Any data loss during migration
- Breaking existing code without compatibility layer
- No rollback plan if migration fails

## Time Estimate
2-3 hours total
- Backup: 5 min
- Schema design: 15 min
- Migration: 1-2 hours
- Code updates: 30 min
- Testing: 30 min
