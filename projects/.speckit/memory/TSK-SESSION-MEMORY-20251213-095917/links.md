# TSK Links and References

## Implementation Plan
- **Main Plan**: `C:\Users\brsth\.claude\plans\rustling-rolling-taco.md`
- **Database**: `P:\.speckit\taskmaster\tasks.db`

## Key Files
- **TaskMaster DAL**: `P:\.speckit\taskmaster\db.py`
- **Session Memory Bridge (planned)**: `P:\__csf.nip\src\core\session_memory\session_memory_bridge.py`
- **Pre-Compaction Hook (planned)**: `P:\.claude\hooks\pre_compaction_memory_preserve.py`
- **Post-Compaction Hook (planned)**: `P:\.claude\hooks\post_compaction_memory_restore.py`

## Integration Points
- **TaskMaster Database**: Session linkage and task continuity
- **Chat History RAG**: `P:\__csf.nip\src\cks\integration\clients\chat_history_client.py`
- **Evidence Correlation**: `P:\__csf.nip\src\core\evidence_correlation\`

## Related Research
- Session Management Research (stored in CKS)
- Intentional Compaction Patterns (40% threshold)
- Subagent Auto-Compaction Strategies (35% threshold)

## Commands
- Activate TSK: `/task tsk set TSK-SESSION-MEMORY-20251213-095917`
- View tasks: `/task list`
- Update task: `/task update <task_id> status:in-progress`