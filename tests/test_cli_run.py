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


def test_run_command_streams_stage_logs_when_requested(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(app, ["run", "--log-verbosity", "normal", "--no-color"])

    assert result.exit_code == 0
    assert "[coding-agent] [INFO]" in result.stdout
    assert "starting developer" in result.stdout
    assert "completed developer" in result.stdout


def test_demo_logs_command_simulates_multiple_agents() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["demo-logs", "--no-color"])

    assert result.exit_code == 0
    assert "[orchestrator] [INFO] task acquisition: coordinating workflow" in result.stdout
    assert "[coding-agent] [INFO] implementation: writing code" in result.stdout
    assert "[review-agent] [INFO] test execution: reviewing changes" in result.stdout


def test_run_command_backend_option_routes_all_stages_to_requested_backend(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    used_backends: list[str] = []

    def fake_get_backend(name: str):
        used_backends.append(name)
        return type(
            "Backend",
            (),
            {
                "run": lambda self, prompt, workspace, stage_name: __import__(
                    "asd_shop.shell_runner"
                ).shell_runner.CommandResult(
                    args=["fake"],
                    cwd=str(workspace),
                    exit_code=0,
                    stdout=(
                        f"`{__import__('asd_shop.roles').roles.ROLE_BY_NAME[stage_name].artifact_filename}` "
                        "has been written."
                    ),
                    stderr="",
                    duration_seconds=0.1,
                )
            },
        )()

    monkeypatch.setattr("asd_shop.stages.get_backend", fake_get_backend)
    runner = CliRunner()

    result = runner.invoke(app, ["run", "--backend", "codex", "--no-color"])

    assert result.exit_code == 0
    assert used_backends
    assert set(used_backends) == {"codex"}
