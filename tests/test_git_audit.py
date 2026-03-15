from asd_shop.git_audit import diff_summary


def test_diff_summary_reports_no_changes_for_clean_repo(tmp_path) -> None:
    summary = diff_summary(tmp_path)
    assert summary.changed_files == []
