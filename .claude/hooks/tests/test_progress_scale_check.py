"""
Tests for progress scale consistency validation.

RED phase: These tests fail because the hook doesn't exist yet.
"""



def test_detects_percentage_count_mismatch():
    """
    Should FAIL when progress.add_task(total=100) but progress.update(completed=345).

    This is the actual bug: total=100 means percentage scale (0-100),
    but completed=345 is a raw count. 345 > 100*2 signals units mismatch.
    """
    diff_output = '''
    progress.add_task("discover", total=100, stats="0")
    progress.update("discover", completed=345, description="yt-api: 345/345")
    '''

    from progress_scale_check import check_progress_scale_consistency

    violations = check_progress_scale_consistency(diff_output)

    assert len(violations) == 1
    assert "total=100" in violations[0]
    assert "completed=345" in violations[0]
    assert "percentage vs count" in violations[0]


def test_passes_consistent_scales():
    """
    Should PASS when total and completed use same scale.

    Example: both use count scale (total=345, completed=100)
    """
    diff_output = '''
    progress.add_task("discover", total=345, stats="0")
    progress.update("discover", completed=100, fields={"stats": "100/345"})
    '''

    from progress_scale_check import check_progress_scale_consistency

    violations = check_progress_scale_consistency(diff_output)

    assert len(violations) == 0


def test_detects_missing_fields_parameter():
    """
    Should FAIL when Progress has {task.fields[...]} column but update()
    doesn't include fields= parameter.

    This causes stale display values (the "0" that never updated).
    """
    diff_output = '''
    Progress(
        TextColumn("   ⎿ yt-api:"),
        TextColumn("{task.fields[stats]}"),  # <-- Has fields column
    )
    progress.add_task("discover", total=100, stats="0")
    progress.update("discover", completed=50)  # <-- Missing fields=
    '''

    from progress_scale_check import validate_progress_fields_update

    violations = validate_progress_fields_update(diff_output)

    assert len(violations) == 1
    assert "fields=" in violations[0]


def test_passes_with_fields_parameter():
    """
    Should PASS when update() includes fields= parameter.
    """
    diff_output = '''
    Progress(
        TextColumn("   ⎿ yt-api:"),
        TextColumn("{task.fields[stats]}"),
    )
    progress.add_task("discover", total=100, stats="0")
    progress.update("discover", completed=50, fields={"stats": "50/100"})
    '''

    from progress_scale_check import validate_progress_fields_update

    violations = validate_progress_fields_update(diff_output)

    assert len(violations) == 0


def test_allows_reasonable_completed_values():
    """
    Should PASS when completed is reasonably close to total.

    completed <= total * 2 is allowed (e.g., total=100, completed=150 is OK,
    might be legitimate progress beyond estimate).
    """
    diff_output = '''
    progress.add_task("discover", total=100, stats="0")
    progress.update("discover", completed=150)
    '''

    from progress_scale_check import check_progress_scale_consistency

    violations = check_progress_scale_consistency(diff_output)

    assert len(violations) == 0
