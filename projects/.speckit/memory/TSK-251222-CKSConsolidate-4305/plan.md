# CKS Consolidation Implementation Plan

## Phase 1: Backup (5 minutes)

**Files to backup:**
- src/data/cks.db
- src/data/cks_hypergraph/
- data/cks_hypergraph/

**Command:**
```bash
python -c "import shutil; from datetime import datetime; stamp = datetime.now().strftime('%Y%m%d'); shutil.copytree('P:/__csf.nip/src/data', f'P:/__csf.nip/src/data_backup_{stamp}')"
```

**Validation:**
- [ ] Backups created successfully
- [ ] File counts match originals

---

## Phase 2: Create New CKS Module (30 minutes)

**File:** `P:/__csf.nip/src/cks/__init__.py`

**Components:**
1. CKS class with unified schema
2. ingest_memory() method
3. ingest_pattern() method
4. search() method
5. Migration helpers

**Validation:**
- [ ] data/cks.db created
- [ ] Schema matches specification
- [ ] CKS class instantiates correctly

---

## Phase 3: Migrate Data (1 hour)

### Step 3.1: Migrate Memories
- Source: src/data/cks.db (309 records)
- Target: entries table with type='memory'

### Step 3.2: Migrate Knowledge Nodes
- Source: src/data/cks_hypergraph/cks_hypergraph.db (40 records)
- Source: data/cks_hypergraph/cks_hypergraph.db (19 records)
- Target: entries table with type='knowledge' or 'pattern'

**Validation:**
- [ ] 368 records migrated total
- [ ] No duplicates
- [ ] Content integrity verified

---

## Phase 4: Compatibility Layer (15 minutes)

**Deprecation warnings for old imports:**
- src/cks/integration/commands/direct_knowledge_ingestion.py
- Routes to new CKS class
- User-friendly warnings

**Validation:**
- [ ] Old code still works
- [ ] Warnings displayed
- [ ] New interface works

---

## Phase 5: Testing (15 minutes)

**Test Cases:**
1. Ingest memory → search → verify
2. Ingest pattern → search → verify
3. Get statistics → verify counts

**Validation:**
- [ ] All tests pass
- [ ] No data loss
- [ ] Performance acceptable

---

## Phase 6: Documentation (10 minutes)

**Files:**
- src/cks/README.md
- Usage examples
- Migration notes

---

## Phase 7: Cleanup (deferred 1 week)

**After 1 week:**
- Archive old databases
- Update all code to use new interface
- Remove deprecation warnings
