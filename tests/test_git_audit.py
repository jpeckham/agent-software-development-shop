from asd_shop.git_audit import diff_summary


def test_diff_summary_reports_no_changes_for_clean_repo(tmp_path) -> None:
    summary = diff_summary(tmp_path)
    assert summary.changed_files == []


def test_diff_summary_normalizes_missing_subprocess_stdout(tmp_path, monkeypatch) -> None:
    (tmp_path / ".git").mkdir()
    results = iter(
        [
            type("Completed", (), {"stdout": None})(),
            type("Completed", (), {"stdout": None})(),
        ]
    )

    monkeypatch.setattr("asd_shop.git_audit.subprocess.run", lambda *args, **kwargs: next(results))

    summary = diff_summary(tmp_path)

    assert summary.changed_files == []
    assert summary.diff_text == ""
