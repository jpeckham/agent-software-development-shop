import json

from typer.testing import CliRunner

from asd_shop.cli import app


def test_run_command_executes_cycle(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "ready_for_approval" in result.stdout


def test_run_command_resumes_most_recent_failed_run_by_default(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runs_dir = tmp_path / "runs"
    run_dir = runs_dir / "2026-03-15T00-00-00Z"
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "run_id": "2026-03-15T00-00-00Z",
                "workspace": str(tmp_path),
                "run_dir": str(run_dir),
                "status": "failed",
                "current_stage": "developer",
                "failed_stage": "developer",
                "created_at": "2026-03-15T00:00:00Z",
                "updated_at": "2026-03-15T00:00:00Z",
            }
        )
    )
    runner = CliRunner()
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "2026-03-15T00-00-00Z" in result.stdout


def test_run_command_new_run_ignores_failed_resume(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runs_dir = tmp_path / "runs"
    run_dir = runs_dir / "2026-03-15T00-00-00Z"
    run_dir.mkdir(parents=True)
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "run_id": "2026-03-15T00-00-00Z",
                "workspace": str(tmp_path),
                "run_dir": str(run_dir),
                "status": "failed",
                "current_stage": "developer",
                "failed_stage": "developer",
                "created_at": "2026-03-15T00:00:00Z",
                "updated_at": "2026-03-15T00:00:00Z",
            }
        )
    )
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--new-run"])
    assert result.exit_code == 0
    assert "2026-03-15T00-00-00Z" not in result.stdout
