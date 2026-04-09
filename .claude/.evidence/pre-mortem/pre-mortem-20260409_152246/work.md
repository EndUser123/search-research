PreCompact_handoff_capture.py fix for prior_transcript_path=N/A bug

CHANGES:
1. scripts/hooks/__lib/handoff_files.py: load_raw_handoff() now accepts optional exclude_session_id param
   - When provided, scans mtime-sorted handoff files and returns first whose source_session_id differs
   - This fixes the bug where load_raw_handoff() returned S_NEW's own handoff (newest by mtime) instead of S_OLD's
   
2. scripts/hooks/PreCompact_handoff_capture.py: passes exclude_session_id=input_data.get('session_id')
   - At PreCompact time, S_NEW's handoff is already written to disk
   - Without exclude, mtime-sort returns S_NEW; with exclude, we skip it and get S_OLD

TARGET FILES:
- P:/packages/handoff/scripts/hooks/__lib/handoff_files.py (load_raw_handoff method)
- P:/packages/handoff/scripts/hooks/PreCompact_handoff_capture.py (lines 751-765)

BUG: prior_transcript_path=N/A in all 83 handoff files because load_raw_handoff() returns newest by mtime
