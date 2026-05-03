# SIGNATURE TOC

## CLAUDE.md
```
# CLAUDE Constitution v8.0 (Reference)

**Purpose:** Context and lookup tables. Enforcement is structural (hooks).

---

## Philosophy

Solo developer environment. 75-85% reliability target.

**Hooks handle enforcement. This document provides context.**

Key principles (enforced structurally):
- Fail fast, surface problems immediately
- Truthfulness > agreement
- Evidence-first verification
- Investigation before diagnosis
- Subagent delegation for non-trivial work

---

## Bulk Refactoring Rule

**Core principle: Use atomic operations for directory restructuring.**

When restructuring directories (move, rename, split packages), the sqa incident showed that separate delete + create risks losing files.

### The Rule

1. **Always use `git mv`** — never separate delete + create
   - `git mv .claude/skills/foo packages/cc-skills-bar/skills/foo`
   - This preserves git history and ensures files aren't lost
2. **One logical operation per commit** — move first, then modify
3. **Verify before committing** — `git status` should show renames (R), not delete+add

### Anti-Patterns

| Pattern | Why it fails | Fix |
|---------|-------------|-----|
| `rm -rf dir/` + `mkdir new/` + copy files | Files lost if process interrupted | `git mv dir/ new/` |
| Delete in commit A, create in commit B | Files missing in commit A's tree | Single atomic commit |
| Mass delete (`git rm *`) without verification | Lost files (sqa incident) | `git mv` + check |

### Evidence

The sqa incident (commit d1d4d2a): `SKILL.md` and `orchestrator.py` were deleted from `.claude/skills/sqa/` but never copied to `packages/cc-skills-sdlc/skills/sqa/`. Recovery required `git show d1d4d2a^:path > file`.

---

## Terminal & Session Behavior

- **Terminal isolation**: Each terminal has isolated state
- **Stale data immunity**: State changes must propagate
- **UUID-named transcript files**: Stored in user home directory
- **Routing and contract policy**: See `.claude/rules/skill-routing-and-contracts.md`

### Session Recovery Rules

When a `<compact-restore>` block is present at session start:

1. **Frame goal as inference, not fact**: Say "Based on the session handoff, we were working on X" — never "The task was X." The captured goal reflects the last user message before compaction, which may be a rejected option or incomplete state.

2. **If corrected about session memory**: Respond directly: "You're right, I don't have reliable recall of what the exact task was." Never say "that was whatever you said" — that is passive-aggressive deflection, not an acknowledgment.

3. **When you don't know something, say so plainly**: "I don't know what the end-of-session task was" is a complete and professional answer. Filling the gap with a confident-sounding guess is worse than admitting uncertainty.

### Contract Discipline

Do not rely on implied producer/consumer contracts.

For any handoff between hooks, sessions, plans, skills, files, or agents, explicitly define and validate:

- input schema
- outpu
```
- class _DangerOp([]) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- class RepoType([]) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def _check_destructive_git(['cmd_list']) -> BinOp(left=Name(id='dict', ctx=Load()), op=BitOr(), right=Constant(value=None, kind=None)) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- class _BlockedResult(['__init__', 'check_returncode']) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def run(['cmd', 'cwd', 'silent']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def color(['text', 'status']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def header(['text']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def item(['text', 'status', 'detail']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- class RepoInfo([]) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def is_nested_repo(['repo', 'all_repos']) -> bool [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def find_all_git_repos([]) -> Subscript(value=Name(id='Tuple', ctx=Load()), slice=Tuple(elts=[Subscript(value=Name(...), slice=Name(...), ctx=Load(...)), Subscript(value=Name(...), slice=Name(...), ctx=Load(...))], ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def filter_repos(['repos', 'filter_type']) -> Subscript(value=Name(id='List', ctx=Load()), slice=Name(id='RepoInfo', ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def get_repo_status(['repo']) -> Subscript(value=Name(id='Tuple', ctx=Load()), slice=Tuple(elts=[Name(id='bool', ctx=Load(...)), ..., Name(id='int', ctx=Load(...))], ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def generate_commit_message_for_repo(['repo']) -> str [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def get_push_target(['repo_path']) -> Subscript(value=Name(id='Tuple', ctx=Load()), slice=Tuple(elts=[Subscript(value=Name(...), slice=Name(...), ctx=Load(...)), ..., Name(id='str', ctx=Load(...))], ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def push_repo(['repo', 'silent']) -> Subscript(value=Name(id='Tuple', ctx=Load()), slice=Tuple(elts=[Name(id='bool', ctx=Load(...)), Name(id='str', ctx=Load(...))], ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def parse_selection(['selection', 'max_idx']) -> Subscript(value=Name(id='List', ctx=Load()), slice=Name(id='int', ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def interactive_select_repos(['repos']) -> Subscript(value=Name(id='List', ctx=Load()), slice=Name(id='RepoInfo', ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def worktree_list([]) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def worktree_add(['name']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def worktree_remove(['name']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def worktree_prune([]) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def get_conflict_strategy(['file_path']) -> str [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def detect_conflicts(['repo']) -> Subscript(value=Name(id='List', ctx=Load()), slice=Name(id='str', ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def resolve_conflicts(['repo', 'conflicts']) -> Subscript(value=Name(id='Tuple', ctx=Load()), slice=Tuple(elts=[Name(id='int', ctx=Load(...)), ..., Subscript(value=Name(...), slice=Name(...), ctx=Load(...))], ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def ensure_diff3_config([]) -> Constant(value=None, kind=None) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def sync_single_repo(['repo', 'is_main']) -> Subscript(value=Name(id='Tuple', ctx=Load()), slice=Tuple(elts=[Name(id='bool', ctx=Load(...)), Name(id='bool', ctx=Load(...))], ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def _has_uncommitted_worktree_changes(['repo']) -> bool [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def repo_has_worktree_changes(['repo']) -> bool [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def _check_repo_health(['repo']) -> Subscript(value=Name(id='Tuple', ctx=Load()), slice=Tuple(elts=[Name(id='str', ctx=Load(...)), ..., Name(id='str', ctx=Load(...))], ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def _get_dirty_description(['repo']) -> str [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def __init__(['self']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def check_returncode(['self']) -> Constant(value=None, kind=None) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def detect_file_type(['path']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def detect_scope(['files']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def detect_commit_type(['data']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def generate_subject(['data']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def generate_commit_body(['data']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync.py]
- def _fallback_detect_file_type(['path']) -> str [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync_utils.py]
- def _fallback_detect_scope(['files']) -> Subscript(value=Name(id='List', ctx=Load()), slice=Name(id='str', ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync_utils.py]
- def _fallback_detect_commit_type(['data']) -> str [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync_utils.py]
- def run(['cmd', 'cwd', 'silent']) -> Attribute(value=Name(id='subprocess', ctx=Load()), attr='CompletedProcess', ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync_utils.py]
- def _infer_scope_from_path(['file_path']) -> Subscript(value=Name(id='Optional', ctx=Load()), slice=Name(id='str', ctx=Load()), ctx=Load()) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync_utils.py]
- def generate_commit_message(['repo_path']) -> str [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\sync_utils.py]
- class TestCheckDestructiveGit(['guard_function', 'test_blocks_git_reset_hard', 'test_blocks_git_reset_hard_with_commit', 'test_blocks_git_clean_full', 'test_blocks_git_stash_drop', 'test_blocks_git_stash_clear', 'test_allows_git_status', 'test_allows_git_add', 'test_allows_git_commit', 'test_allows_git_push', 'test_allows_git_pull', 'test_allows_git_reset_soft', 'test_allows_git_reset_mixed', 'test_allows_git_clean_without_flags', 'test_allows_git_stash_pop', 'test_allows_git_stash_push', 'test_returns_none_for_empty_list', 'test_returns_none_for_non_git_command', 'test_returns_none_for_partial_git', 'test_returns_correct_command_string']) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- class TestDestructiveGitRun(['run_function', 'test_run_blocks_reset_hard', 'test_run_blocks_git_clean_fd', 'test_run_blocks_git_stash_drop', 'test_run_allows_safe_commands']) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def guard_function(['self']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_blocks_git_reset_hard(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_blocks_git_reset_hard_with_commit(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_blocks_git_clean_full(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_blocks_git_stash_drop(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_blocks_git_stash_clear(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_allows_git_status(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_allows_git_add(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_allows_git_commit(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_allows_git_push(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_allows_git_pull(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_allows_git_reset_soft(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_allows_git_reset_mixed(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_allows_git_clean_without_flags(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_allows_git_stash_pop(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_allows_git_stash_push(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_returns_none_for_empty_list(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_returns_none_for_non_git_command(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_returns_none_for_partial_git(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_returns_correct_command_string(['self', 'guard_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def run_function(['self']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_run_blocks_reset_hard(['self', 'run_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_run_blocks_git_clean_fd(['self', 'run_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_run_blocks_git_stash_drop(['self', 'run_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- def test_run_allows_safe_commands(['self', 'run_function']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_destructive_git_guard.py]
- class TestSemanticCommitMessageGeneration(['sync_module', 'test_generate_commit_message_function_exists', 'test_generate_commit_message_extracts_changed_files', 'test_generate_commit_message_produces_semantic_format', 'test_generate_commit_message_not_generic_wip', 'test_generate_commit_message_infers_type_from_files', 'test_generate_commit_message_with_python_files']) [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_sync_semantic_commits.py]
- def sync_module(['self']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_sync_semantic_commits.py]
- def test_generate_commit_message_function_exists(['self', 'sync_module']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_sync_semantic_commits.py]
- def test_generate_commit_message_extracts_changed_files(['self', 'sync_module']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_sync_semantic_commits.py]
- def test_generate_commit_message_produces_semantic_format(['self', 'sync_module']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_sync_semantic_commits.py]
- def test_generate_commit_message_not_generic_wip(['self', 'sync_module']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_sync_semantic_commits.py]
- def test_generate_commit_message_infers_type_from_files(['self', 'sync_module']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_sync_semantic_commits.py]
- def test_generate_commit_message_with_python_files(['self', 'sync_module']) -> None [P:\packages\.claude-marketplace\plugins\cc-skills-utils\skills\git\tests\test_sync_semantic_commits.py]
