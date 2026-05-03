Target: P:/packages/.claude-marketplace/plugins/cc-skills-utils/skills/git/sync.py
Skill Type: code
Review: Commit loop in sync_single_repo() function (lines 852-896)
The loop commits uncommitted changes and pushes. It uses _has_uncommitted_worktree_changes(repo) to detect dirty state.

CODE UNDER REVIEW (sync_single_repo loop, lines 852-896):
"""
    max_iterations = 20
    while True:
        max_iterations -= 1
        add_result = run('git add -A', cwd=worktree, silent=True)
        if add_result.returncode != 0 and 'index.lock' in add_result.stderr:
            import time; time.sleep(0.5)
            add_result = run('git add -A', cwd=worktree, silent=True)

        if not _has_uncommitted_worktree_changes(repo):
            break

        commit_msg = generate_commit_message_for_repo(repo)
        commit_result = run(['git', 'commit', '-m', commit_msg], cwd=worktree, silent=True)

        if commit_result.returncode != 0:
            if 'nothing to commit' in commit_result.stderr.lower():
                break
            if 'index.lock' in commit_result.stderr:
                import time; time.sleep(0.5)
                continue
            print(f'  X Commit failed..., leaving dirty state')
            break

        did_commit = True
        if VERBOSE:
            print(f'  Committed: {commit_msg}')

        if max_iterations <= 0:
            print(f'  X Max iterations reached..., leaving dirty state')
            break
"""

HELPER FUNCTION (_has_uncommitted_worktree_changes, lines 899-930):
"""
def _has_uncommitted_worktree_changes(repo: RepoInfo) -> bool:
    status = run(['git', 'status', '--porcelain'], cwd=repo.path, silent=True)
    if status.returncode != 0:
        return False
    for line in status.stdout.splitlines():
        if not line:
            continue
        # XY filename format: X=index, Y=worktree
        col1, col2, _, filename = line, '', '', ''
        if len(line) >= 2:
            col1, col2 = line[0], line[1]
        if len(line) > 3:
            filename = line[3:]
        if line.startswith('??') or col2 != ' ':
            return True
    return False
"""
